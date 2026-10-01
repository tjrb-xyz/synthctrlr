# Snapshot file format: `.jupiter-xm.json`

**Status:** draft 1, 2026-10-01. Design only; nothing is built.

The owner chose this as the next piece of work (2026-10-01, verbatim):

> snapshot files are more important

This file makes DEVICE-MODEL §4.2 exact enough to build against: every field, the content hash byte for byte, and what a reader does with a file. What a snapshot holds, and how capture and recall work, stay in DEVICE-MODEL §4.1 and §4.3–§4.4.

**Scope:**

- One JSON text file per snapshot, shared by mazika and the plugin (DEVICE-MODEL §4.2, §9 item 4).
- The `.syx` export (§8).
- **Not here:** Roland's own formats (`.SVD`, `.SVZ`, the editor's librarian files). Whether to support them later is still the owner's open question (README, open questions).

**Words:** the file is a *snapshot* in this repository and in the plugin, and a *sound* inside mazika (DEVICE-MODEL §3.2). The format is the same.

---

## 1. The file

- **Name:** `<name>.jupiter-xm.json`.
  - `<name>` is the snapshot's name with `/ \ : * ? " < > |` and control characters replaced by `-`, trimmed, at most 100 characters.
  - On a clash in the same folder, ` 2`, ` 3`… is added before the extension.
  - The file name is a convenience. The name inside the file is the real one.
- **Text:** UTF-8 without a BOM, LF line endings, a final newline.
- **JSON form,** so the same snapshot always writes the same text and diffs stay small:
  - keys sorted;
  - two-space indent;
  - whole numbers only, no floats;
  - hex in lowercase.
- **Size:** about 25 KB of raw bytes at most (DEVICE-MODEL §4.1), so about 55–70 KB as a file with its decoded values.

## 2. Top level

```json
{
  "format": "synthctrlr.jupiter-xm.snapshot",
  "formatVersion": 1,
  "meta": { },
  "source": { },
  "parts": [ ],
  "dependencies": { },
  "macros": [ ],
  "blocks": [ ],
  "omitted": [ ],
  "missing": [ ],
  "system": null,
  "values": { },
  "contentHash": "sha256:…"
}
```

| Key | Required | What it holds |
|---|---|---|
| `format` | yes | Always `synthctrlr.jupiter-xm.snapshot`. A reader refuses any other value. |
| `formatVersion` | yes | `1`. A reader refuses a higher version, saying which version it can read. |
| `meta` | yes | Name, time, tags, notes (§3.1). Outside the hash. |
| `source` | yes | Where and how it was captured (§3.2). Outside the hash. |
| `parts` | yes | One entry per part 1–5: Tone reference, engine, model (§3.3). |
| `dependencies` | yes | Expansions and wave expansions the sound needs (§3.4). May be empty lists. |
| `macros` | yes | Performance-view macro assignments (§3.5). May be empty. |
| `blocks` | yes | The captured bytes: the authoritative sound (§4). |
| `omitted` | yes | Blocks left out of a light snapshot because they equal a reference (§4.2). May be empty. |
| `missing` | yes | Blocks that never answered during capture (§4.3). May be empty. |
| `system` | yes | The optional System context, or `null` (§5). Outside `contentHash`. |
| `values` | yes | Decoded values by parameter id, for reading, comparing and hand editing (§6). Outside the hash. |
| `contentHash` | yes | SHA-256 over the sound (§7). |

**Unknown keys:**

- Keys starting with `x-` (at the top level or inside `meta`) are kept and written back unchanged. They are for other tools.
- Any other unknown key makes the reader refuse the file and name the key. This follows aui's rule that schemas refuse unknown keys with a reason (AUI-REQUIREMENTS SC-23).

## 3. Description fields

### 3.1 `meta`

```json
"meta": {
  "name": "Night Brass",
  "createdAt": "2026-10-01T18:42:07Z",
  "modifiedAt": "2026-10-01T18:42:07Z",
  "tags": ["brass", "pad"],
  "notes": "",
  "starred": false
}
```

- `name`: any Unicode text, 1–100 characters. It is not the Scene name stored on the synth, which lives in the Scene Common block and is limited by the synth.
- `createdAt`, `modifiedAt`: RFC 3339, UTC, whole seconds.
- `starred`: mazika's `Star`.

### 3.2 `source`

```json
"source": {
  "identityReply": "f07e1006024165030000xxxxxxxxf7",
  "firmwareConfirmed": "3.02",
  "deviceId": 16,
  "port": "JUPITER-Xm",
  "miEdition": "1.06",
  "profile": { "id": "roland.jupiter-xm", "version": "1.0.0" },
  "setup": "xxxxxx",
  "capturedBy": "synthctrlr-plugin 0.1.0"
}
```

- `identityReply`: the raw Universal Identity reply, as hex (DEVICE-MODEL §2.6). Its revision bytes are kept as received, since they do not map reliably to a firmware version.
- `firmwareConfirmed`: the version the person confirmed from MENU › INFORMATION, or `null` if they skipped it.
- `deviceId`: the device ID used, 16–31 (`10`–`1F`).
- `setup`: the 3 bytes of the Setup block (`00 10 00 00`): which stored Scene the edit buffer came from. Read only; never recalled.
- `capturedBy`: the program and its version.

### 3.3 `parts`

Exactly five entries, in part order.

```json
"parts": [
  {
    "part": 1,
    "engine": "analog",
    "model": "JP8",
    "tone": { "msb": 97, "lsb": 64, "pc": 0, "name": "…" },
    "byReference": false
  }
]
```

- `engine`: `analog`, `jupiterx`, `zencore`, `rdpiano`, `vocoder`, `drums`, `jd800`, `vocaldesigner` or `unknown` (DEVICE-MODEL §2.2).
- `model`: for `analog` only, `JP8`, `JX8P`, `JUNO106` or `SH101`; otherwise `null`. `JUNO60` is allowed only once the owner's synth shows it (DEVICE-MODEL §10 item 10).
- `tone`: the Tone reference read from the Scene Part (offsets `00 02`–`00 04`), plus the Tone's name as read.
- `byReference`: `true` when the Tone's inner data is not in the public SysEx, so only the reference is saved: drums, vocoder, and the expansions until they are measured.
- Carrier substitutions (DEVICE-MODEL §4.4 step 3) are reported in the recall result, never written into the file.
- The engine and model here are a summary for the librarian. The blocks are what recall writes.

### 3.4 `dependencies`

```json
"dependencies": { "expansions": ["JD-800"], "waveExpansions": [] }
```

Read from the parts' engines and from each ZEN-Core partial's wave group. Shown in the recall confirmation (DEVICE-MODEL §4.4 step 1).

### 3.5 `macros`

```json
"macros": [ { "slot": 1, "param": "part1.analog.filter.freq" } ]
```

Up to 8 slots, each naming a parameter id from `values` (DEVICE-MODEL §6.5).

## 4. Blocks

### 4.1 `blocks`

```json
"blocks": [
  {
    "address": "01000000",
    "size": 80,
    "bytes": [
      "0000000000000000000000000000000000000000000000000000000000000000",
      "…"
    ]
  }
]
```

- `address`: the block's start address, as its 4 wire bytes in hex (8 characters). Each byte is 0–127 (DEVICE-MODEL §2.3).
- `size`: the number of data bytes, as a plain whole number. It is the size that answered on the synth it was captured from (DEVICE-MODEL §4.2), so it can differ between firmware versions.
- `bytes`: the data as hex, split into lines of 32 bytes (64 characters); the last line may be shorter. Splitting keeps text diffs of two snapshots readable. Every byte is 0–127.
- The list is sorted by address and holds no address twice.
- **Which blocks:** Setup is *not* a block (it is in `source`). The blocks are the temporary Scene's 36 blocks (DEVICE-MODEL §4.1) and, for each of parts 1–4, the temporary Tone blocks of its active engine. The profile's block table, per firmware, gives the expected addresses and sizes (DEVICE-MODEL §10 item 2).
- **Blocks the profile cannot decode** (for example the experimental JD-800 blocks) are stored the same way and round-trip unchanged.

### 4.2 `omitted` (light snapshots)

```json
"omitted": [ { "address": "…", "size": 2112, "reference": "init-pattern" } ]
```

- A block may be omitted only when its bytes equal a reference the profile stores, measured once on the synth (DEVICE-MODEL §4.1, §10 item 17). Today the only reference is `init-pattern`, the user pattern of an initialised Scene.
- Recall writes the reference bytes in its place, so a light snapshot recalls the same as a full one.
- A reader whose profile lacks the named reference refuses to recall the snapshot, naming the reference. It can still show and export the rest.
- An omitted block counts in `contentHash` as its reference bytes (§7), so a light and a full snapshot of the same sound have the same hash.

### 4.3 `missing`

```json
"missing": [ { "address": "…", "size": 61, "reason": "timeout" } ]
```

- Blocks that never answered during capture, saved only when the person chose "save with N blocks missing" (DEVICE-MODEL §4.3).
- `reason`: `timeout`, `checksum` or `partial`.
- Recall skips them, says so in the confirmation and the result, and leaves them out of the read-back compare (DEVICE-MODEL §4.4).
- A snapshot with missing blocks can never have the same hash as a complete one (§7).

## 5. System context

```json
"system": {
  "blocks": [ { "address": "00000000", "bytes": ["…"], "size": 0 } ],
  "fields": ["…"],
  "systemHash": "sha256:…"
}
```

- `null` when System context was not captured.
- `blocks`: the captured System blocks, in the same form as §4.1 (about 7 blocks, 0.37 KB; DEVICE-MODEL §4.1).
- `fields`: the parameter ids that "Also restore System settings" writes, one by one as whole nibble groups. Recall never writes a whole System block (DEVICE-MODEL §4.1).
- `systemHash`: computed as in §7, over `system.blocks` only.
- **System context is outside `contentHash`.** It affects every Scene, so the same Scene captured with and without it is still the same sound. This settles a point DEVICE-MODEL §4.2 left open.

## 6. Values

```json
"values": {
  "part1.analog.filter.freq": 812,
  "scene.common.tempo": 1200
}
```

- Keys are the profile's parameter ids, prefixed with `part1.`…`part5.` for part parameters and `scene.` for Scene-wide ones. User-pattern steps are left out (DEVICE-MODEL §4.2).
- **Each value is the raw wire value,** a whole number in the parameter's `raw` range (DEVICE-MODEL §2.5). The display form (for example −200…+200) comes from the profile, so the file never holds a rounded or unit-dependent number.
- Values exist only for parameters inside `blocks`; none for `omitted`, `missing` or opaque blocks.
- **On load,** each value is compared with its bytes:
  - **equal:** nothing happens;
  - **different and in range:** it is re-encoded into its block, and the change is listed before anything is sent ("part 1 Cutoff: 790 → 812");
  - **out of range or the wrong type:** the file is refused, naming the parameter;
  - **an id the profile does not know:** ignored and listed as a note (it may come from a newer profile). The blocks still carry the sound.
- **On save,** `values` is rewritten from the blocks, so it always matches them.

## 7. `contentHash`

`contentHash` is `sha256:` followed by the lowercase hex SHA-256 of this byte sequence:

1. The ASCII text `synthctrlr.jupiter-xm.sound/1` followed by one LF byte (`0a`).
2. For each block of the sound, in ascending address order, one record:
   - its 4 address bytes;
   - its size as 4 bytes, big-endian;
   - a kind byte:
     - `00`, then `size` data bytes, for a block in `blocks`, or in `omitted` with its reference bytes put in;
     - `01`, with nothing after it, for a block in `missing`.

**Details:**

- The set of blocks is `blocks` ∪ `omitted` ∪ `missing`. `system`, `source`, `meta`, `parts`, `dependencies`, `macros` and `values` are outside it.
- It is computed after any edited `values` have been re-encoded into the blocks (§6).
- Data bytes are always 0–127, so the kind byte and the sizes keep records unambiguous.
- **Consequences:**
  - renaming, tagging or re-noting a snapshot never changes its hash;
  - the same sound captured twice has the same hash;
  - a full and a light snapshot of the same sound have the same hash;
  - a snapshot with missing blocks never matches a complete one.
- **On load,** the reader recomputes the hash. If it differs from the stored one, it says "blocks changed outside synthctrlr" and uses the recomputed hash.
- **The plugin's skip-recall test** (DEVICE-MODEL §5.2) compares the snapshot's hash with the hash of the synth's current state over the same set of addresses. A snapshot with missing blocks is never skipped.

## 8. `.syx` export

- For backup and other librarians. It is written from the snapshot, never read back into one in this version.
- **Order:** the recall order of DEVICE-MODEL §4.4:
  1. each part's Tone selection;
  2. each part's Tone data;
  3. the rest of the Scene, with Scene Part blocks split so the Tone selection is not sent again.
- Each block is one or more DT1 messages of at most 256 data bytes, at the snapshot's device ID, each with its checksum (DEVICE-MODEL §2.4). Omitted blocks are written as their reference bytes. Missing blocks are left out.
- System context is left out unless the person ticks "Include System settings".
- The export is labelled "Tone edits may be lost if replayed without pauses". The pause needed after Tone selections is stated once measured (DEVICE-MODEL §10 item 5).

## 9. Where the files live

- **One file per snapshot is the source of truth.** A library index (search, tags, stars) is a cache rebuilt from the files, so copying a folder of files moves a library.
- **Plugin:** the per-user folder of DEVICE-MODEL §4.6. The project's own snapshot sits inside the DAW project as the plugin's state, in this same JSON.
- **mazika:** the owning core's `sounds` store holds the same JSON. Import and export are this file (DEVICE-MODEL §9 item 4).

## 10. Example

A complete file, shortened only in the block list and values; the bytes shown are placeholders, not real synth data.

```json
{
  "blocks": [
    {
      "address": "01000000",
      "bytes": ["…"],
      "size": 80
    }
  ],
  "contentHash": "sha256:…",
  "dependencies": { "expansions": [], "waveExpansions": [] },
  "format": "synthctrlr.jupiter-xm.snapshot",
  "formatVersion": 1,
  "macros": [],
  "meta": {
    "createdAt": "2026-10-01T18:42:07Z",
    "modifiedAt": "2026-10-01T18:42:07Z",
    "name": "Night Brass",
    "notes": "",
    "starred": false,
    "tags": ["brass"]
  },
  "missing": [],
  "omitted": [],
  "parts": [
    { "byReference": false, "engine": "analog", "model": "JP8", "part": 1, "tone": { "lsb": 64, "msb": 97, "name": "…", "pc": 0 } }
  ],
  "source": {
    "capturedBy": "synthctrlr-plugin 0.1.0",
    "deviceId": 16,
    "firmwareConfirmed": "3.02",
    "identityReply": "…",
    "miEdition": "1.06",
    "port": "…",
    "profile": { "id": "roland.jupiter-xm", "version": "1.0.0" },
    "setup": "…"
  },
  "system": null,
  "values": { "part1.analog.filter.freq": 812 }
}
```

The real block table and a real example wait for the checks on the owner's synth (DEVICE-MODEL §10 items 1, 2 and 17).

## 11. Choices to confirm

These are new in this draft. Each has a default the format already uses:

1. **System context outside `contentHash`,** with its own `systemHash` (§5).
2. **Raw wire values in `values`,** not display values (§6).
3. **Bytes split into 32-byte hex lines** for readable diffs (§4.1).
4. **Unknown keys refused,** except `x-` keys, which are kept (§2).
