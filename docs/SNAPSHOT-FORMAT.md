# Snapshot file format

**Status:** draft 2, 2026-10-01. Design only; nothing is built.

- **Draft 2 makes the format generic for any device profile** (CONTROLLER-BUILDER §4), following the owner's words there: "this process needs to be abstract for every synth".
- What is specific to one device comes from its profile. The Jupiter-Xm, the first profile, is the running example; its specifics are marked "Jupiter-Xm".

The owner chose this as the next piece of work (2026-10-01, verbatim):

> snapshot files are more important

This file makes DEVICE-MODEL §4.2 exact enough to build against, for any device: every field, the content hash byte for byte, and what a reader does with a file. What a snapshot holds, and how capture and recall work, stay in DEVICE-MODEL §4.1 and §4.3–§4.4.

**Scope:**

- One JSON text file per snapshot, shared by mazika and the plugin (DEVICE-MODEL §4.2, §9 item 4).
- The `.syx` export (§8).
- **Not here:** Roland's own formats (`.SVD`, `.SVZ`, the editor's librarian files). Whether to support them later is still the owner's open question (README, open questions).

**Words:** the file is a *snapshot* in this repository and in the plugin, and a *sound* inside mazika (DEVICE-MODEL §3.2). The format is the same.

---

## 1. The file

- **Name:** `<name>.<profile id>.json`, for example `Night Brass.roland.jupiter-xm.json`.
  - `<name>` is the snapshot's name with `/ \ : * ? " < > |` and control characters replaced by `-`, trimmed, at most 100 characters.
  - On a clash in the same folder, ` 2`, ` 3`… is added before the extension.
  - The file name is a convenience. The name inside the file is the real one.
- **Text:** UTF-8 without a BOM, LF line endings, a final newline.
- **JSON form,** so the same snapshot always writes the same text and diffs stay small:
  - keys sorted;
  - two-space indent;
  - whole numbers only, no floats;
  - hex in lowercase.
- **Size** depends on the device. A Jupiter-Xm snapshot is about 25 KB of raw bytes at most (DEVICE-MODEL §4.1), so about 55–70 KB as a file with its decoded values.

## 2. Top level

```json
{
  "format": "synthctrlr.snapshot",
  "formatVersion": 1,
  "profile": { "id": "roland.jupiter-xm", "version": "0.1.0" },
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
| `format` | yes | Always `synthctrlr.snapshot`. A reader refuses any other value. |
| `formatVersion` | yes | `1`. A reader refuses a higher version, saying which version it can read. |
| `profile` | yes | The device profile's `id` and `version` (CONTROLLER-BUILDER §2). A reader without that profile can list the file but not open it for editing or recall. |
| `meta` | yes | Name, time, tags, notes (§3.1). Outside the hash. |
| `source` | yes | Where and how it was captured (§3.2). Outside the hash. |
| `parts` | yes | One entry per part the profile defines (five on the Jupiter-Xm): its sound reference, engine, model (§3.3). |
| `dependencies` | yes | What the sound needs installed on the device, in lists the profile names (§3.4). May be empty. |
| `macros` | yes | Performance-view macro assignments (§3.5). May be empty. |
| `blocks` | yes | The captured bytes: the authoritative sound wherever the device can be read (§4). Empty for a send-only device. |
| `omitted` | yes | Blocks left out of a light snapshot because they equal a reference (§4.2). May be empty. |
| `missing` | yes | Blocks that never answered during capture (§4.3). May be empty. |
| `system` | yes | The optional global context, or `null` (§5). Outside `contentHash`. |
| `values` | yes | Values by parameter id (§6). Decoded copies of the blocks, outside the hash, except for send-only parameters, where they are the sound and inside the hash. |
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
  "origin": "xxxxxx",
  "capturedBy": "synthctrlr-plugin 0.1.0"
}
```

- `identityReply`: the raw Universal Identity reply, as hex (DEVICE-MODEL §2.6), or `null` for a device that does not answer. Its revision bytes are kept as received, since they do not map reliably to a firmware version.
- `firmwareConfirmed`: the version the person confirmed (on the Jupiter-Xm, from MENU › INFORMATION), or `null` if they skipped it.
- `deviceId`: the SysEx device ID used, or `null` for a device without SysEx. Jupiter-Xm: 16–31 (`10`–`1F`).
- `origin`: optional bytes, named by the profile, that say which stored memory the edit buffer came from. Read only; never recalled. Jupiter-Xm: the 3 bytes of the Setup block (`00 10 00 00`).
- `capturedBy`: the program and its version.

### 3.3 `parts`

One entry per part the profile defines, in part order. The fields below are the Jupiter-Xm's; another profile names its own engines and models, and its own way of referring to a stored sound.

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

The lists are named by the profile. Jupiter-Xm: read from the parts' engines and from each ZEN-Core partial's wave group. Shown in the recall confirmation (DEVICE-MODEL §4.4 step 1).

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

- `address`: the block's start address, as its wire bytes in hex. The number of bytes is fixed by the profile's SysEx dialect (4 on the Jupiter-Xm, so 8 characters). Each byte is 0–127 (DEVICE-MODEL §2.3).
- `size`: the number of data bytes, as a plain whole number. It is the size that answered on the device it was captured from (DEVICE-MODEL §4.2), so it can differ between firmware versions.
- `bytes`: the data as hex, split into lines of 32 bytes (64 characters); the last line may be shorter. Splitting keeps text diffs of two snapshots readable. Every byte is 0–127.
- The list is sorted by address and holds no address twice.
- **Which blocks** comes from the profile's capture recipe (CONTROLLER-BUILDER §2.2). Jupiter-Xm: Setup is *not* a block (it is `source.origin`). The blocks are the temporary Scene's 36 blocks (DEVICE-MODEL §4.1) and, for each of parts 1–4, the temporary Tone blocks of its active engine. The profile's block table, per firmware, gives the expected addresses and sizes (DEVICE-MODEL §10 item 2).
- **Blocks the profile cannot decode** (for example the experimental JD-800 blocks) are stored the same way and round-trip unchanged.

### 4.2 `omitted` (light snapshots)

```json
"omitted": [ { "address": "…", "size": 2112, "reference": "init-pattern" } ]
```

- A block may be omitted only when its bytes equal a reference the profile stores, measured once on the device. Jupiter-Xm: the only reference is `init-pattern`, the user pattern of an initialised Scene (DEVICE-MODEL §4.1, §10 item 17).
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

## 5. Global context (`system`)

Settings that affect everything on the device, not only this sound. The profile says which (Jupiter-Xm: its System context).

```json
"system": {
  "blocks": [ { "address": "00000000", "bytes": ["…"], "size": 0 } ],
  "fields": ["…"],
  "systemHash": "sha256:…"
}
```

- `null` when the global context was not captured.
- `blocks`: the captured blocks, in the same form as §4.1. Jupiter-Xm: about 7 blocks, 0.37 KB (DEVICE-MODEL §4.1). A send-only device's global context is a `values` map instead.
- `fields`: the parameter ids that "Also restore System settings" writes, one by one. Jupiter-Xm: as whole nibble groups, never a whole System block (DEVICE-MODEL §4.1).
- `systemHash`: computed as in §7, over the global context only.
- **The global context is outside `contentHash`.** It affects every sound, so the same sound captured with and without it is still the same sound. Confirmed by the owner (§11).

## 6. Values

```json
"values": {
  "part1.analog.filter.freq": 812,
  "scene.common.tempo": 1200
}
```

- Keys are the profile's parameter ids, prefixed by their scope (CONTROLLER-BUILDER §2.4): `part1.`, `part2.`… for part parameters, `scene.` for Scene-wide ones. Jupiter-Xm: user-pattern steps are left out (DEVICE-MODEL §4.2).
- **Each value is the raw wire value,** a whole number in the parameter's `raw` range (DEVICE-MODEL §2.5). The display form (for example −200…+200) comes from the profile's converters (`VALUE-DISPLAY.md`), so the file never holds a rounded or unit-dependent number.
- **Two roles:**
  - **Inside a block:** the value is a decoded copy. Values exist only for parameters inside `blocks`; none for `omitted`, `missing` or opaque blocks.
  - **Send-only** (the parameter's addresses are all CC, NRPN, RPN or program change; CONTROLLER-BUILDER §2.3): the value *is* the sound. It is what the editor last sent or saw arrive from the device. Recall sends it, and the result says "sent, not verified", since it cannot be read back.
- **On load,** each value inside a block is compared with its bytes:
  - **equal:** nothing happens;
  - **different and in range:** it is re-encoded into its block, and the change is listed before anything is sent ("part 1 Cutoff: 790 → 812");
  - **out of range or the wrong type:** the file is refused, naming the parameter;
  - **an id the profile does not know:** ignored and listed as a note (it may come from a newer profile). The blocks still carry the sound.
- **On save,** values inside blocks are rewritten from the blocks, so they always match them.

## 7. `contentHash`

`contentHash` is `sha256:` followed by the lowercase hex SHA-256 of this byte sequence:

1. The ASCII text `synthctrlr.sound/2`, an LF byte (`0a`), the profile id in ASCII, and another LF.
2. For each block of the sound, in ascending address order, one record:
   - a kind byte: `00` for a block in `blocks`, or in `omitted` with its reference bytes put in; `01` for a block in `missing`;
   - its address bytes (as many as the profile's dialect uses);
   - its size as 4 bytes, big-endian;
   - for kind `00` only, its `size` data bytes.
3. Then, for each send-only value, in ascending order of parameter id (compared as UTF-8 bytes), one record:
   - the kind byte `02`;
   - the parameter id in UTF-8, then a `00` byte;
   - the value as 4 bytes, big-endian, two's complement.

**Details:**

- **Changed in draft 2:** the domain names the profile, and the kind byte comes first so block and value records cannot be confused. `/2` marks the change.
- The set of blocks is `blocks` ∪ `omitted` ∪ `missing`; the values are the send-only ones. `system`, `source`, `meta`, `parts`, `dependencies`, `macros` and the decoded copies in `values` are outside it.
- It is computed after any edited `values` have been re-encoded into the blocks (§6).
- The kind byte, the fixed address length, the sizes and the `00` after each id keep records unambiguous. Parameter ids never contain a `00` byte.
- **Consequences:**
  - renaming, tagging or re-noting a snapshot never changes its hash;
  - the same sound captured twice has the same hash;
  - a full and a light snapshot of the same sound have the same hash;
  - a snapshot with missing blocks never matches a complete one.
- **On load,** the reader recomputes the hash. If it differs from the stored one, it says "blocks changed outside synthctrlr" and uses the recomputed hash.
- **The plugin's skip-recall test** (DEVICE-MODEL §5.2) compares the snapshot's hash with the hash of the device's current state over the same set of addresses. A snapshot with missing blocks, or with send-only values (which cannot be read back), is never skipped.

## 8. `.syx` export

- For devices with SysEx, for backup and other librarians. The order and message form come from the profile; the Jupiter-Xm's are below. It is written from the snapshot, never read back into one in this version.
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
  "format": "synthctrlr.snapshot",
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
  "profile": { "id": "roland.jupiter-xm", "version": "0.1.0" },
  "source": {
    "capturedBy": "synthctrlr-plugin 0.1.0",
    "deviceId": 16,
    "firmwareConfirmed": "3.02",
    "identityReply": "…",
    "origin": "…",
    "port": "…"
  },
  "system": null,
  "values": { "part1.analog.filter.freq": 812 }
}
```

The real block table and a real example wait for the checks on the owner's synth (DEVICE-MODEL §10 items 1, 2 and 17).

## 11. Choices to confirm

These are new in this draft. Each has a default the format already uses. The owner's answers (2026-10-01, verbatim):

> 1. yes
> 2.  sure can we have a converter built in to device actual values to be able to have 1:1 mapping? you can sweep the specs and allow adjustments on the interface itself.

1. **System context outside `contentHash`,** with its own `systemHash` (§5). **Confirmed by the owner (2026-10-01).**
2. **Raw wire values in `values`,** not display values (§6). **Confirmed by the owner (2026-10-01),** who asked for a converter built in so the editor shows the synth's own values 1:1 (`VALUE-DISPLAY.md`).
3. **Bytes split into 32-byte hex lines** for readable diffs (§4.1). **Confirmed by the owner (2026-10-01).**
4. **Unknown keys refused,** except `x-` keys, which are kept (§2). **Confirmed by the owner (2026-10-01).**

The owner's answers to 3 and 4 (2026-10-01, verbatim), followed by the request that made this format generic (CONTROLLER-BUILDER):

> 3. sure
> 4. ok
> this process needs to be abstract for every synth through a wizard configured manually or via mcp
> we need an mcp ability to create controller of different synths or midi devices
