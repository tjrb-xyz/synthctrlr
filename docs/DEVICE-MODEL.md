> **Source:** copied from tjrb-xyz/aui, branch `jupiter-xm` (PR #1), `examples/jupiter-xm/DEVICE-MODEL.md`, commit `6426a67`, on 2026-10-01, then extended in this repository (see its history). In the text below, "this example" now means synthctrlr. The owner's quoted words are kept verbatim.

# Device model: Roland JUPITER-Xm editor

**Status:** draft 2.2, 2026-10-01. Design only; nothing is built.

**Since 2026-10-01 synthctrlr is generic** (`CONTROLLER-BUILDER.md`). This file is now the design notes for the first device profile, `roland.jupiter-xm`. The descriptor of §2.5 is generalised in CONTROLLER-BUILDER §2.4, and the snapshot file in `SNAPSHOT-FORMAT.md` (draft 2).

- Draft 2 was reviewed against Roland's MIDI Implementation, the research, mazika's spec and the owner's decisions. Draft 2.1 applies the 72 confirmed findings.
- Draft 2.2 records the owner's answers to four open questions (§11): recall confirmation, engines by reference, mazika's browser core first, and the first pack as an unbranded homage.
- The owner's decisions are quoted in full in `README.md`.

**What this is:**

- a device model for an editor that drives the owner's real JUPITER-Xm over USB MIDI and SysEx;
- its views, built from aui parts;
- the external pack that styles them.

**What it is not:**

- **It makes no sound.** The sound comes off the Jupiter-Xm.
- **It is not yet the synth controller device.** That device, with the Jupiter-Xm as one of its models, follows once dsper is wired (`README.md`, roadmap).

Inside mazika this is M1.2, "the Jupiter-Xm synth manager" (mazika@36bde22:docs/HANDOFF.md §4).

**Evidence labels:**

- **MI:** read directly in Roland's *JUPITER-X/Xm MIDI Implementation* Version 1.06 (dated Apr 19, 2022, 90 pages), the newest edition found.
  - Roland's site was unreachable from the research network. The PDF was read from a public mirror (github.com/matchalunatic/jupiter-xm-midi-controller, `midi-spec.pdf`).
  - It is Roland's document. This repo cites it and never copies it.
- **editor DB:** seen only in the parameter database of Roland's own JUPITER-X Editor, as decoded by github.com/DrKnackerator/RolandZenDecodeXML and DrKnackeratorStrikesAgain/Roland-Zen-Decode-XML.
  - Used for structure only; never copied or shipped.
  - Where it disagrees with the MI, the MI wins.
- **snippet:** seen only in search-engine snippets of Roland's support pages or the press.
- **UNVERIFIED:** no source. It must be measured on the owner's synth (§10).

---

## 1. What the editor fixes

**The owner's priorities, in order (2026-10-01):**

1. **See the whole Scene:** the Scene overview (§6.1).
2. **Edit its parts:** the part editor (§6.2).
   - The analog models and the JUPITER-X model come first.
   - Complete support of every engine is the goal, within what the synth's public SysEx allows (§2.2).
3. **Save to the computer and reload with every parameter of every part:** Scene snapshots (§4).
   - Every engine the public SysEx reaches is restored exactly. Drum kits, the vocoder and expansion Tones are restored by reference (§2.2).
   - Writing to the synth's own memory is secondary.

**Complaints and answers** (snippets from Sweetwater, gearnews and Gearspace, plus the owner's words):

| Complaint | This model's answer |
|---|---|
| The whole Scene is hard to see at once | A Scene overview: 5 part strips side by side, like a mixer (§6.1) |
| Menu diving on a tiny LCD; confusing edit modes | Every parameter of the selected part on one screen, sectioned like a panel (§6.2) |
| Saving and reloading an edited Scene is awkward | Snapshots on the computer. Every part the public SysEx reaches is restored exactly and verified by reading back; the rest is restored by reference (§4, §2.2) |
| Roland's JUPITER-X Editor UI is oversized and needs constant scrolling | Pages fit the screen and never scroll (mazika ux-spec §6.4.4 "**No page scrolls.**"); compact and performance views |
| Roland's editor crashes while rearranging; its librarian lagged behind firmware 3.0 | Our own librarian of snapshot files (§6.7); no dependence on Roland Cloud Manager |
| Two-way SysEx is unreliable | A transfer layer with size-aware timeouts, strict reply matching, retries, read-back after every recall, and a visible state per control (§3, §4) |

**Prior art to beat:**

- **Roland's free JUPITER-X Editor** (May 2021, standalone, via Roland Cloud Manager; snippet). It has a librarian with "save to file", a Scene Builder and a Part Editor.
- **Sound Quest MIDI Quest** sells a Jupiter-X editor/librarian, including as AU/VST3/AAX plugins (snippet).

---

## 2. The synth as seen over SysEx

### 2.1 Structure

- **A Scene does not contain its Tones; it refers to them** (MI).
  - Each Scene Part stores its Tone's bank MSB, bank LSB and program number, at Scene Part offsets `00 02`–`00 04`.
  - The Tone's data lives in a per-part **temporary Tone area**, one per engine (§2.3).
  - Roland's support says writing a Scene does not save edited Tones (snippet).
- **The temporary Scene** (MI: 36 blocks, 12,490 data bytes):
  - **Scene Common.**
  - **5 Scene Parts**, each with:
    - part switch, mute, level, pan, tune;
    - mono/poly, legato, bend and portamento (each with a "TONE" option);
    - the Tone reference;
    - output assign;
    - the sound-control offsets set by CC 71–78;
    - MIDI settings.
  - **Per part:** Part EQ, MFX and Zone.
  - **Shared effects:** Chorus, Delay, Reverb and Drive.
  - **Arpeggio:** settings per part, including Arp Mode (I-ARP / ARP / STEP), Step Seq Mode and Probability. These arrived in firmware 3.00 (snippet).
  - **Five user arpeggio/step patterns,** 2,112 bytes each. These are 10,560 of the 12,490 bytes.
- **Parts 1–4 are synth parts; part 5 is the drum part.**
- **Only in System, not in a Scene** (MI):
  - Master EQ and Master Comp;
  - mic noise suppressor, compressor and sends;
  - the System chorus, delay and reverb;
  - the SCENE/SYS source switches, which decide whether chorus, delay, reverb, tempo and controllers come from the Scene or from System.
  - System Common also holds settings unrelated to the sound: master tune, key shift, receive PC/bank, local switch and USB audio settings.
- **Unreachable over SysEx** (the editor DB marks them not SysEx-addressable):
  - mic input gain, master level;
  - Rx Exclusive, Tx Edit;
  - device ID.
  
  The editor labels these "set on the synth".
- **Storage counts** (MI): 512 user Scenes and 512 user Tones on firmware 3.00+.
  - Using slots 257–512 may need a factory reset after updating to 3.00 (snippet).
  - Whether the owner's unit answers in the `60 …` area is a check (§10).

### 2.2 Engines

| Engine | Models / content | Temporary area (per part) | Size per part | Public SysEx? |
|---|---|---|---|---|
| Analog model (`SynMdl`) | JUPITER-8, JX-8P, JUNO-106, SH-101 (MI `Model` 1–4; 0 is `---`) | `02 10 00 00` + part (parts 1–4) | 334 bytes, 3 blocks (parameters, MFX, Tone common) | **Yes (MI).** First priority. |
| JUPITER-X model (`MdlJPX`, firmware 3.00+) | Jupiter-8-inspired: 4 oscillators, 7 waveforms, osc pan and delay | `02 50 00 00` + part | 436 bytes, 3 blocks | **Yes (MI).** First priority. |
| ZEN-Core (`ZCore`) | PCM / XV-5080 / VA / SuperSAW tones with 4 partials | `02 00 00 00` + part | 2,124 bytes, 33 blocks | **Yes (MI)** |
| RD Piano | Piano tones | `02 20 00 00` (part 1 only) | 20 bytes, 2 blocks | **Yes (MI)** |
| Vocoder | 2 preset tones (bank 71/70) | no temporary area found | — | **No:** captured by reference only |
| Drum kit (part 5) | Preset kits: PR-A DRUM (86/64) and CMN DRUM (86/65) | none in the MI. The editor DB names one, but its address is unknown | ~4,969 bytes (editor DB) | **No:** captured by reference, plus the Scene-level part settings |
| JD-800 (paid expansion) | JD-800 model | `02 30 00 00` + part (editor DB) | 566 bytes (editor DB) | **Experimental** until measured |
| Vocal Designer (expansion) | Vocal Designer | `02 40 00 00` (editor DB) | 178 bytes (editor DB) | **Experimental** until measured |

**JUNO-60 is not documented for this synth.**

- The MI's analog `Model` field stops at SH-101, and the MI's bank table has no JUNO-60 bank.
- The editor DB adds `JUNO60` as model 5.
- It is supported only if the owner's synth shows it (§10).

**"Complete support of every engine" has a public-SysEx limit:**

- The analog, JUPITER-X, ZEN-Core and RD Piano engines are fully readable and writable from the MI.
- The drum kits, vocoder and expansions are not documented. They are captured by reference (bank and program) and restored with their Scene-level settings.
- **Settled by the owner (2026-10-01): by reference is enough for now.** Measuring the undocumented areas (§10 item 10) is deferred. If it happens later, it means measuring on the owner's synth, never copying Roland's editor files.

**Engine detection per part:**

1. **Read the part's Tone reference** (Scene Part `00 02`–`00 04`).
2. **Preset Tones:** the engine follows from the bank (MI bank table):
   - 97/64 JUPITER-8, 97/66 JUNO-106, 97/68 JX-8P, 97/70 SH-101 → analog model;
   - 97/81–82 → JUPITER-X model;
   - 87/xx (PR-A…D, XV-5080, COMMON) → ZEN-Core;
   - 71/69 → RD Piano;
   - 71/70 → vocoder;
   - 86/64 PR-A DRUM and 86/65 CMN DRUM → drum kit;
   - 71/67 PR-X → engine unknown. The MI groups it with the ZEN-Core banks, but this is confirmed only by probing on the synth.
3. **User Tones** (71/3–6) and PR-X do not reveal their engine. In order of preference:
   - read the editor DB's "Temporary Tone Type" or the editor area's part info, once their addresses are measured (§10);
   - otherwise, probe each candidate engine's temporary area.
     - Silence counts as "inactive" only after retries.
     - If more than one area answers (an inactive area may hold stale data from an earlier Tone; UNVERIFIED), the editor asks the person rather than guessing.
4. **Analog models:** the analog block's `Model` value says which of the four it is. It is a 2-nibble group at offset `00 00`–`00 01`; 1–4 = JP8, JX8P, JUNO106, SH101.

### 2.3 Address map (MI)

| Address | Area |
|---|---|
| `00 00 00 00` | System: Common, Control, chorus/delay/reverb, Master EQ/Comp, mic, Model Bank Assign, and Button Color Set (unused on the Xm) |
| `00 10 00 00` | Setup (3 bytes: the current Scene's bank and program) |
| `01 00 00 00` | Temporary Scene |
| `02 00 00 00` – `02 03 00 00` | Temporary Tone, ZEN-Core, parts 1–4 |
| `02 10 00 00` – `02 13 00 00` | Temporary Tone, analog model, parts 1–4 |
| `02 20 00 00` | Temporary Tone, RD Piano (part 1) |
| `02 50 00 00` – `02 53 00 00` | Temporary Tone, JUPITER-X model, parts 1–4 (firmware 3.00+) |
| `40 00 00 00` – `49 7B 00 00` | User Scenes 1–256, one every `00 05 00 00` |
| `50 00 00 00` – `57 7E 00 00` | User Tones 1–512, one every `00 02 00 00`. These are opaque data blocks, not named parameters. |
| `60 00 00 00` – `69 7B 00 00` | User Scenes 257–512 (firmware 3.00+) |
| `7F 00 00 00` | "Editor". Undocumented in the MI. The editor DB names, all UNVERIFIED: <br>• a version request <br>• Scene, Tone and wave lists <br>• "Notify Scene Load" (`7F 00 42 00`) and "Notify Tone Load" (`7F 00 41 00`) <br>• Edit State <br>• a Write Message (`7F 00 70 00`) <br>• Editor Mode and Edit Tx switches (`7F 00 7F 00`–`01`) |

Addresses and sizes are 4 bytes of 7 bits each, so offsets carry at 128.

**What the editor touches:**

- **Capture and recall** read and write only:
  - `00 00 00 00` (System context, opt-in);
  - `00 10 00 00` (Setup, read only);
  - `01 …`;
  - `02 …`.
- **Experimental, only after measuring (§10 items 7–8):**
  - listening for the editor-area notifications;
  - writing the Editor Mode / Edit Tx switches.
- **Only "Save to synth…"** (§3.3) writes the storage areas `40 …`, `50 …` and `60 …` or sends the Write Message `7F 00 70 00`.

### 2.4 Message format and encoding (MI)

- **DT1 (data set):** `F0 41 <dev> 00 00 00 65 12 <a a a a> <data…> <sum> F7`.
- **RQ1 (request):** `F0 41 <dev> 00 00 00 65 11 <a a a a> <s s s s> <sum> F7`.
  - The model ID is `00 00 00 65`. The MI's reception tables misprint the last byte as `52`; ignore that.
  - The device ID is `10`–`1F` (default `10`); `7F` is also accepted.
- **Checksum:** `(128 − (sum of address and data or size bytes) mod 128) & 0x7F`.
  - The MI's example `F0 41 10 00 00 00 65 12 01 00 00 10 4A 25 F7` (temporary Scene level = 74) checks out.
- **Requests:**
  - An RQ1 must use a block start address and size from the map.
  - A wrong request gets **silence, not an error**.
- **Packets:**
  - Data over 256 bytes travels in packets of 256 bytes or less, about 20 ms apart. This holds both ways.
  - A long reply arrives as several DT1 messages, each with its own address and checksum (matching rules: §4.3).
- **Values:**
  - A plain value is one 7-bit byte.
  - A value marked `#` is split into 4-bit nibbles, high nibble first. Groups are 2 bytes (8-bit values) or 4 bytes (16-bit values), never 3.
  - **The address of a `#` value is its group's first byte.**
- **Signed values are stored with an offset,** for example:
  - `FILTER KEY FOLLOW 824–1224` means −200…+200;
  - `FILTER ENV DEPTH 1–2047` means −1023…+1023.
  
  A few fields' signed encodings are unclear and need measuring (§10).
- **Active Sensing:** filter `FE` on input, and never send it.

**Not from the MI:** third-party tooling configs show the synth exposing a second USB MIDI port ("… DAW CTRL"), and the editor uses the main port for SysEx. Port names, and which port carries SysEx, are UNVERIFIED (§10 item 13).

### 2.5 A parameter descriptor

Every editable value is data. This needs a v2 of mazika's synth-profile format (§9). The example is the analog model's filter frequency, from the MI's `[MDLSYN0]` table:

```json
{
  "id": "analog.filter.freq",
  "label": "Cutoff",
  "group": "Filter",
  "engine": "analog",
  "models": ["JP8", "JX8P", "JUNO106", "SH101"],
  "area": "temp.tone.analog",
  "offset": "00 00 4F",
  "encoding": "nibble4",
  "raw": [0, 1023],
  "display": { "kind": "number", "min": 0, "max": 1023 },
  "hero": true
}
```

- **`area`** names a base that depends on the part: `temp.tone.analog` for part *n* is `02 1(n−1) 00 00`. One table holds every base. The address is base + offset, with 7-bit carry.
- **`encoding`** is one of `byte7`, `nibble2` or `nibble4`. **`raw`** is the wire range, and **`display`** maps it to what the person sees, including signed offsets.
  - The `display` converters, their 1:1 rule and where each comes from are in `VALUE-DISPLAY.md` §3. The MI gives no display for this example's parameter, so the `number` 0–1023 shown above is an assumption until measured (VALUE-DISPLAY §2).
- **`models`** lists the analog models that use the parameter. The panel shows only those parameters.
  - This is the device model deciding what exists, not a skin hiding controls. It follows mazika's DJ design §4.6 rule that a skin may never "add a control or hide one", and aui's one DOM per theme (AUI-182).
- **No `cc` here.**
  - The synth's sound-control CCs 71–78 set the Scene Part's offset parameters (Scene Part `00 0F`–`00 16`; `40H` means no offset). These shift the Tone's cutoff, resonance, envelope and vibrato. They are performance offsets on the part, not ways to set Tone parameters (MI).
  - CCs can also be assigned as MFX or Scene/System control sources, which modulate rather than set values.
- **The full table is generated from the MI** (a parser over the MI's text, as the RoMi project does), not typed by hand, and then checked on the synth.

### 2.6 Firmware and identity

**Versions:**

- **3.03** (March 2025) is the newest found (snippet).
  - Its known change: the Auto Off default becomes 20 minutes.
  - Its page also mentions editor-connection fixes, probably carried over from 3.01.
  - The full note was not readable, so any other change is unknown.
- **3.02** (October 2022) reduced popping noise. **3.01** (May 2022) fixed problems connecting to Roland's editor (snippet).
- **3.00** (April 2022) is the last release *reported* to change parameters, engines or storage (snippet):
  - the JUPITER-X model;
  - 512 Scenes and Tones, with the new Scene block at `60 …`;
  - I-ARP raised from 55 to 65 types and from 44 to 65 rhythms;
  - per-part arp/step mode and Probability.
- **The MI v1.06 is dated Apr 19, 2022** (MI), the same week as 3.00 (snippet). No later MI edition is indexed.
- **The owner runs 3.02 and plans 3.03.** One schema (MI v1.06) is expected to cover both, but 3.01–3.03 postdate the MI. Block sizes are measured on 3.02 and again on 3.03 (§10 items 1–2).

**Identity** (MI):

- The Universal Identity Request `F0 7E 7F 06 01 F7` is answered with `F0 7E <dev> 06 02 41 65 03 00 00 <rev ×4> F7`.
- The family `65 03 / 00 00` identifies a JUPITER-X or Xm.
- The MI is inconsistent about the revision bytes (`01 01 00 05` vs `00 01 00 05`). They do not map reliably to "3.02" or "3.03", and may or may not tell X from Xm.
- So the editor:
  - stores the raw reply;
  - asks the person once per synth to confirm the version shown under MENU › INFORMATION (location: snippet);
  - records both in every snapshot.

**Auto Off** (the 3.03 default is 20 minutes) means an idle synth can switch itself off. Port loss is handled as in §4.3 and §4.4.

---

## 3. Talking to the synth

### 3.1 Who talks to the synth

The owner's rule (2026-10-01): **"The web view should be separate from the main thread which should handle midi."**

- **The main side owns the conversation with the synth.** That covers:
  - the MIDI port;
  - SysEx framing, checksums and pacing;
  - reply matching, timeouts and retries;
  - the echo guard;
  - the decoded device state;
  - snapshot capture and recall (§4);
  - the snapshot store.
  
  It runs whether or not a view is open.
- **Which process is the main side:**
  - **mazika:** the core that owns the synth.
    - **Today** that is mazika's browser core page, which uses Web MIDI with the permission granted in the core's own window. mazika's rule is "**A client never calls `requestMIDIAccess`.**" (ux-spec §6.6.2).
    - **Settled by the owner (2026-10-01): the first version starts there.** It moves to mazikad later without changing the views.
    - **Later** it is the native daemon mazikad, which has no MIDI design yet (§9).
  - **A DAW plugin:** the plugin's native, non-audio thread, which opens the synth's USB MIDI port itself (§5). It never uses the audio thread, the host's MIDI path or the editor's web view.
- **One specification, two builds.** There is one protocol, one pacing and reply-matching design, and one parameter table generated from the MI. They are implemented once, as a Rust crate with a transport and storage adapter, built two ways:
  - **native**, with a C interface, for the plugin shell and mazikad;
  - **WebAssembly**, for mazika's browser core, matching mazika's plan to build its core three ways (brief §1a).
  
  Until the WebAssembly build exists, mazika's TypeScript browser core implements the same contract over Web MIDI.
- **The web view is a client.** It renders aui, holds a replica of the state and proposes edits. It never opens a MIDI port or a file.
- **The research supports this:**
  - WebKit has no Web MIDI, so neither does WKWebView (macOS and iOS hosts) nor WebKitGTK (Linux). This is confirmed in the WebKit source tree and browser-compat data.
  - WebView2 (Windows) has Web MIDI only behind a SysEx permission.
  - A web view that owned MIDI would fail on two of three desktop systems and would lose the synth whenever the editor window closed.

### 3.2 Messages

**The contract is mazika's synth session messages** (ux-spec §10.5 and §6.4.6), extended where needed:

- **Client → main side:**
  - `synth.set {profileId, param, value}`: one edit.
  - `synth.do {profileId, action, soundId?, name?}`, with mazika's existing actions:
    - `save-sound`: capture a snapshot;
    - `send-sound {soundId}`: recall it. The snapshot stays in the owning main side's store; the client sends only its id;
    - `send-whole`, `rename`, `delete`.
  - New actions for this profile (§9):
    - `read-sound` (read everything from the synth);
    - `import`, `export`;
    - `save-to-synth {slot}` (behind its confirmation).
  - The confirmation is shown in the client where the action was chosen; the main side confirms nothing itself (mazika §10.5).
- **Main side → client:**
  - `synth.state`, sent as changes per area rather than whole value lists;
  - progress and results for long actions;
  - structured errors (timeout, checksum, partial reply, port lost, another program talking to the synth).
- **Ownership:** `synth.claim`, `synth.claimed`, `synth.refused` and `synth.released`, within one mazika session (§5.3).

**Words per host:**

- **In mazika:**
  - a saved snapshot is a **sound** (mazika's glossary word);
  - the actions are `Save sound as…` and `Send`;
  - "scene", "capture" and "recall" stay with mazika's jam scenes and audio logging.
  - "Scene" appears only when naming the Jupiter's own concept.
- **In the plugin:** `Save snapshot` and `Restore` may be used.
- **In this document:** "capture" and "recall" are internal terms.

### 3.3 Rules

**Carried over from mazika** (HANDOFF M1.2; ux-spec §6.4.5, §6.4.6):

- **Edit buffer only.** Editing and recall write only the temporary areas (`01 …`, `02 …`).
  - **One exception: the System area** (`00 00 00 00`) is not a temporary area. Whether DT1 changes there survive a power cycle is UNVERIFIED (§10 item 12).
  - Until it is measured, every System write is confirmed as "affects every Scene, may be permanent".
- **Writing the synth's memory needs the "Save to synth…" confirmation.**
- **Editor → synth:**
  - at most one message per control per 10 ms;
  - the latest value wins;
  - the final value is always sent.
- **Control states**, each shown on the control:
  - Heard;
  - Not heard;
  - Pending send;
  - Turned on the synth.
  
  mazika's fifth state, "Not modelled", belongs to its S-1 stand-in and is not used here.
- **Not in undo.** Synth edits stay out of the console's undo history.

**New here:**

- **"Save to synth…":**
  - it names the slot it overwrites;
  - it offers to back up the slot's old contents to a snapshot first;
  - it reminds the person that edited Tones must be saved as well as the Scene, since a Scene only refers to its Tones (Roland support, snippet). Roland's "Scene & Tone" write option is unconfirmed (snippet).
- **Control state "Set on the synth":** for settings SysEx cannot reach (§2.1).
- **Synth → editor (Tx Edit):**
  - With **Tx Edit** on, panel moves arrive as DT1 messages (snippet).
  - What a panel move sends (address, length, whole or partial nibble groups) is UNVERIFIED (§10 item 7).
  - The parser accepts any DT1 inside a known block. A partial nibble group never updates the mirror by itself; it triggers a short, debounced re-read of its block.
  - Tx Edit cannot be set over documented SysEx. The editor asks the person to set System › MIDI TX › Tx Edit = ON. It uses the editor-area switch only if measuring shows it works.
  - With Tx Edit off, the editor warns that panel moves on the synth are not seen and are not saved.
- **Echo guard:**
  - It is kept per address and compares whole nibble groups.
  - Each DT1 the editor sends adds an expected echo to a first-in, first-out queue for its group address. The entry expires after about 2 s, extended while a transfer is in flight.
  - An incoming value matching the head of that queue is an echo.
  - If measuring shows the synth never echoes host DT1 (§10 item 7), the guard is off.
- **Transfers are exclusive.** A capture or recall is one transaction on the main side.
  - `synth.set` from clients waits until it ends.
  - Tx Edit messages arriving during it are logged by address (§4.3, §4.4).
- **Setup checked and explained on first connect:**
  - USB MIDI port found (on Windows, Roland's VENDOR driver mode where needed);
  - System › MIDI RX › **Rx Exclusive = ON** (without it every RQ1 and DT1 is ignored);
  - **Tx Edit = ON** for a live mirror;
  - the device ID, if not the default;
  - the firmware confirmation (§2.6).
- **Bluetooth MIDI** (the Xm has BLE-MIDI): whether it carries RQ1/DT1 at all is UNVERIFIED (§10 item 13).
  - Until checked, a Bluetooth connection is shown as "notes and controllers only".
  - It offers no capture or recall.

---

## 4. Scene snapshots (save to the computer)

The owner's third priority: "saving it, not necessarily on synth memory but computer memory and being able to reload the save with all the parameters and parts we’ve edited."

### 4.1 What a snapshot holds

**Always:**

- **The temporary Scene:** all 36 blocks (MI), including the 5 user patterns (10,560 bytes).
  - A "light" snapshot may leave the patterns out only when they equal a *reference pattern*: the bytes of an initialised Scene, measured once on the synth and stored in the profile (§10).
  - Recalling a light snapshot writes the reference pattern, so the result is the same as a full one.
- **For each of parts 1–4,** the temporary Tone blocks of its *active engine* (§2.2):
  - 334 bytes for an analog model;
  - 436 bytes for the JUPITER-X model;
  - 2,124 bytes for ZEN-Core;
  - 20 bytes for RD Piano.
- **For each part:**
  - its Tone reference (bank, program, name);
  - its engine;
  - for an analog Tone, its model.
- **Part 5 (drums), the vocoder and expansion Tones:** the reference and every Scene-level setting (part, EQ, MFX, zone, arpeggio, pattern).
  - Their inner data is not in the public SysEx (§2.2).
  - JD-800 and Vocal Designer data are captured as *experimental* blocks once measuring confirms their areas.
- **Dependencies:**
  - the expansions the snapshot needs (JD-800, Vocal Designer);
  - the wave expansions its ZEN-Core partials use (from each partial's wave group).
- **Macro assignments** for the performance view (§6.5), as parameter ids.
- **Metadata:**
  - the identity reply;
  - the firmware the person confirmed;
  - the MI edition the schema follows (v1.06);
  - the profile and schema versions;
  - the Setup block (which stored Scene it came from);
  - name, time, tags, notes.

**Optional, as "System context":**

- System Common's sound-related fields (mic processing, the SCENE/SYS switches);
- the SCENE/SYS fields in System Control;
- System Chorus, Delay and Reverb;
- Master EQ and Master Comp.

These come to 7 blocks and about 0.37 KB. They affect every Scene, so they are saved for reference and **restored only when the person ticks "Also restore System settings"**. Restoring writes those fields one by one, as whole nibble groups, and never the whole System Common block, which also holds unrelated settings (§2.1).

**Size:**

- **Raw data:** about 12.5 KB for the Scene, plus up to 4 × 2.1 KB for Tones, plus about 0.4 KB of System context. That is about 21 KB at most, or about 2 KB plus Tones for a light snapshot.
- **As a file:** the bytes are stored as hex, so roughly double, plus the decoded values (§4.2).

### 4.2 File format

The exact format is specified in `SNAPSHOT-FORMAT.md` (draft 1, 2026-10-01). Where the two differ, that file wins.

- **One JSON text file per snapshot:** `<name>.jupiter-xm.json`. It is also mazika's sound export format for this profile (§9), so mazika and the plugin share one file.
- **`blocks`** is the authoritative part: a list of `{address, size, bytes}`, sorted by address.
  - Each size is the size that answered on the synth it was captured from. Sizes come from a per-firmware table in the profile, settled by measuring (§10 item 2).
  - Recall replays exactly what was captured.
- **`values`** holds decoded values by name for the profile's known parameters, *except* the user-pattern steps. For example: `"part1.analog.filter.freq": 812`.
  - They serve reading, comparing and editing in a text editor.
  - On load, a value that differs from its bytes is re-encoded into the block, and each such change is listed before sending.
  - Blocks the profile cannot decode stay opaque and round-trip unchanged.
- **`contentHash`** is SHA-256 over the sound only:
  - the blocks sorted by address, each serialised as address ‖ size ‖ bytes;
  - computed after any edited `values` are re-encoded into the blocks;
  - omitted light-snapshot patterns count as the reference pattern bytes.
  
  Names, tags, notes, metadata and `values` are outside it. So renaming a sound never changes its hash, and the same sound captured twice has the same hash.
- **JSON form:** sorted keys, lowercase hex, whole numbers only. The hash does not depend on the JSON text.
- **`.syx` export:** for backup and other librarians.
  - It is written in recall order: Tone selections, then Tone data, then the rest of the Scene, with Scene Part blocks split (§4.4).
  - It is labelled "Tone edits may be lost if replayed without pauses". The minimum pause after the Tone selections is stated once it is measured (§10 item 5).
- **Roland's own formats** (`.SVD` backups and Scene exports, `.SVZ` Tones, the editor's librarian files) are undocumented. They are not written or read in this version.

### 4.3 Capture

**Steps:**

1. Read Setup (`00 10 00 00`) and the temporary Scene, one RQ1 per block at the MI's start and size.
2. For each part, find its engine (§2.2) and read that engine's temporary Tone blocks.
3. Read System context.
4. **Re-read Setup and the five Scene Part references at the end.** If any changed during the capture (someone changed Scene or Tone on the panel), redo the parts affected.
5. Tx Edit messages received during the capture that fall inside an already-captured range are applied to the captured bytes, or that block is re-read.

**Reading one block** (the reply matching rules):

- **While an RQ1 is outstanding,** only DT1 messages at the block's start + k × 256 (with 7-bit carry) whose length is min(256, remaining) count as reply packets. Every other DT1 goes to the Tx Edit path.
  - This keeps a panel move or another program's reply from corrupting the block.
- **A block is complete** when the bytes received equal the requested size.
- **The timeout scales with the size:** a base plus about 30 ms × ceil(size / 256). It resets on each packet.
  - The editor never re-requests while packets are still arriving.
  - A bad checksum discards the block, which is then re-read whole.
- **On silence,** it retries once. Then, as a diagnostic, it tries the editor DB's alternative size if one exists and records which size answered.
- **A block that never answers is reported by name.** A snapshot is never saved silently partial:
  - the person retries;
  - or saves it marked "N blocks missing". mazika's equivalent is "Saved with N not heard".

**Size of the job:**

- 1 (Setup) + 36 (Scene) + 7 (System context) = 44 reads.
- Each part adds 3 (analog or JUPITER-X), 2 (RD Piano) or 33 (ZEN-Core) reads, plus any User Tone engine probes.
- So a full capture is about 56 reads with four analog parts, and up to about 176 with four ZEN-Core parts. There are fewer if one RQ1 can read a whole area (§10 item 4).
- Wall-clock time is UNVERIFIED (§10 item 9). Progress is shown throughout.

**If the port is lost mid-capture,** the received blocks are kept. After reconnecting, the capture resumes if Setup and the Scene Part references are unchanged; otherwise it starts again.

### 4.4 Recall

**Steps:**

1. **Check the snapshot's model and firmware against the connected synth.** A mismatch warns, then allows recall.
   - The confirmation also lists the expansions and wave expansions the snapshot depends on. It says the editor cannot verify they are installed until the editor-area lists are measured (§10).
2. **For each part, select its Tone** by bank and program, then wait until the Tone has loaded.
   - The wait uses "Notify Tone Load" once measuring confirms it; otherwise it is a measured delay (§10 item 5).
   - Before writing, the editor checks the part's engine (§2.2).
3. **Write that part's temporary Tone blocks.**
   - **If a referenced *user* Tone slot has changed** (the editor selects the slot and compares its loaded name and engine with the snapshot's), it uses a *carrier*:
     - it selects a factory Tone of the same engine and model, then writes the saved Tone data over it;
     - the result records the substitution, for example "Part 2 restored on carrier JP-8 001 (user Tone 0123 has changed)";
     - the read-back expects the carrier's reference for that part;
     - "Save to synth…" for such a Scene offers to save the Tone to a chosen user slot as well.
4. **Write the remaining Scene blocks.**
   - Scene Part blocks are split, so the Tone selection is not sent again after the Tone data. Re-sending it would reload the Tone and wipe the edit (UNVERIFIED behaviour; §10 item 5).
   - User patterns travel as 9 packets each.
5. **Restore System context only if ticked** (§4.1).
6. **Read everything back and compare.**
   - It shows "Restored · all parts match", or lists each mismatch with a retry.
   - Mismatches at addresses the synth reported through Tx Edit *during* the recall read "changed on the synth during recall". They are never retried automatically.
   - Reference mismatches are never retried automatically either, since a retry would reload a Tone.
7. **Nothing is written to the synth's memory.** Keeping the Scene on the synth is "Save to synth…".

**Partial snapshots and interruptions:**

- **Recall of a snapshot saved with missing blocks** skips those blocks. It says so in the confirmation and the result, and excludes them from the compare.
- **If the port is lost mid-recall,** the synth is marked "partly restored", and the recall restarts from the beginning after reconnecting.

**Size of the job:** about 76 write messages for the Scene (31 blocks plus 45 pattern packets), plus up to about 132 for four ZEN-Core Tones. With about 20 ms between packets, a tone-load wait per part and the read-back, a full recall is on the order of 10 seconds (UNVERIFIED; §10 item 9). It runs on the main side as one exclusive transaction (§3.3), so the UI stays live and shows progress.

### 4.5 Confirming a recall

mazika confirms every send of a sound ("… Send · Cancel", ux-spec §6.4.6), in the client where the action was chosen.

**Settled by the owner (2026-10-01): ask every time, as mazika does.** A recall asks once, saying what it replaces:

- *"Replace the synth's current sound with 'Night Brass'? Unsaved edits on the synth will be lost. Send · Cancel"*;
- "Save current first" is offered when the edit buffer has unsaved changes.

The same rule applies to:

- stepping through sounds with `Shift+,` / `Shift+.` (mazika §6.4.6);
- "Try", which sends a sound from the library without saving anything (§6.7).

**The plugin exception (settled with the same answer):** in a DAW, "recall on project load" is a per-project option (§5.2), and choosing it is the consent.

- The recall then runs without a prompt, even with the editor closed. An open editor shows progress with Cancel.
- A person who wants a prompt there too picks "manual" or "on first play" (§5.2).

### 4.6 Where snapshots live

**In the store of whichever main side owns the synth, never in a client.**

- **mazika:** the spec already keeps sounds in the owning core's store `sounds`, "kept across core restarts, kiosk restarts and new participant ids" (ux-spec §10.8).
  - The code does not have that store yet; today `src/persistence` holds only console and takes.
  - §10.8 does not name the database; the SDK design's core-scoped `mazika-device` is one candidate.
- **A DAW plugin:**
  - the project's snapshot is the plugin's saved state, inside the DAW project (§5.2);
  - its library of other snapshots lives in the portable per-user folder:
    - macOS: `~/Library/Application Support/<vendor>/`
    - Windows: `%APPDATA%\<vendor>\`
    - Linux: `$XDG_DATA_HOME/<vendor>/`
- **Moving snapshots between computers or hosts** is export and import of the same `.jupiter-xm.json` file.

---

## 5. Running in other DAWs (plugin mode)

### 5.1 How the plugin reaches the synth

**Never through the DAW.** The plugin's native main side opens the synth's USB MIDI port directly. The research found host routing of plugin SysEx too unreliable:

- **Formats:** VST3, CLAP and AU can all carry SysEx in principle.
- **Hosts** (snippets and source, 2026):
  - Bitwig strips SysEx at the track and device level;
  - Live passes it only through Max for Live;
  - Logic's External Instrument does not pass it;
  - developers reported VST3 SysEx output failing in Cubase 12 and REAPER (a JUCE framing bug fixed in 2023; current hosts are untested).
- **clap-wrapper 0.16.0** forwards outgoing SysEx to AUv2 and AUv3 but drops it in its VST3 adapter (confirmed in its source).
- **Commercial editors with total recall do the same** (snippet): MIDI Quest, Soundtower and Ctrlr open their own MIDI ports.

**Opening the port alongside the DAW:**

- **macOS:** CoreMIDI is multi-client.
- **Linux:** use the ALSA sequencer (multi-client), never rawmidi (exclusive).
  - If the DAW opens the synth's rawmidi device itself, the port may be unavailable to the plugin (UNVERIFIED). The editor detects this and shows the same fix as on Windows.
- **Windows:**
  - Windows MIDI Services makes ports multi-client by default and routes the older WinMM and WinRT APIs through itself (Microsoft's docs, 2026).
  - Ports are exclusive again in its "Legacy" mode, on Windows 10, and on unupdated systems. There the editor detects the mode and shows the known fix: disable the synth's port in the DAW.
  - Whether Roland's VENDOR driver joins the multi-client service is UNVERIFIED.

### 5.2 Total recall

- **The plugin's saved state** (CLAP state, VST3 `getState`, AU `fullState`) **is the project's Scene snapshot**, plus an instance id.
- **Saving (`getState`)** is called often (autosave, undo) and must return at once, so it never captures. It returns:
  - the last verified device state, if the synth has been read or restored this session;
  - otherwise, the snapshot it was loaded with, unchanged and marked "unverified".
  
  A reconnect after Auto Off never replaces the project's snapshot with the synth's power-on state.
- **Edits mark the project as changed** (CLAP: a state-changed notice; VST3: dirty; AU: a state-change notification), so the DAW saves them.
- **Loading (`setState`):**
  - skips the recall when the snapshot's `contentHash` equals the synth's current state;
  - debounces repeated calls, and cancels any recall in flight;
  - otherwise schedules a paced recall and read-back on the main side, waiting until the synth's port appears.
- **Duplicates:**
  - In CLAP hosts that implement state-context, a duplicated track is told apart from a project load and does not resend.
  - In VST3 and AU hosts it cannot be told apart. So a second live instance carrying the same instance id is treated as a duplicate: it takes a new id, acts as a client and does not recall.
  - Duplicate behaviour per host is a check (§10).
- **One instance per synth per project holds the total-recall state;** others save only a reference to it. If two owner states conflict at load, the editor asks.
- **Recall options**, as MIDI Quest offers:
  - on project load (default);
  - on first play, which warns that playback before the recall finishes is not yet restored;
  - manual.
- **A recall started during playback** finishes in the background and says so. It never touches the audio thread.

### 5.3 One owner per synth

**Within one mazika session:** mazika's rule holds. Cores claim the synth, and the first claim wins (`synth.claim`).

**Between plugin instances and processes** (for example, Bitwig's per-plugin sandboxes):

- An OS lock keyed by the synth's port name, taken before any traffic and released when the process dies (`flock` or a named mutex), picks one owner.
- The others show "Managed by …" and act as clients.

**mazika and a DAW at once:**

- When a mazika core holds the synth, the plugin joins mazika's session as a paired client, the way mazika's Max for Live device already does, instead of opening the port.
- mazika's browser core cannot take an OS lock, so until mazikad exists a collision between it and a plugin cannot be prevented, only detected (UNVERIFIED). The owner accepted this for the first version (§11).

**Programs outside any of this** (a DAW track, Roland's editor) cannot be excluded on multi-client ports. The editor detects them heuristically (DT1 replies it did not request) and shows "Another program is talking to the synth".

### 5.4 Build

- **CLAP first,** wrapped to VST3 and AUv2 with clap-wrapper. Its VST3 SysEx gap does not matter, since SysEx bypasses the host.
- **AUv2 before AUv3,** until an AUv3 sandbox is shown to reach CoreMIDI hardware ports.
- **The Jupiter core** is the native build of the Rust crate (§3.1), with a C interface for the C++ plugin shell.
- **The editor UI is aui in the plugin's web view,** bridged to the core with the toolkit's native calls (choc's `bind`, JUCE's native functions, or equivalent).
  - The web view follows aui's older-WKWebView rules: no `light-dark()` (AUI-073), and precomputed colours (AUI-040, AUI-179).
- **Pro Tools (AAX)** is left out at first by default, because of its signing barrier. This awaits the owner's answer to the Pro Tools question (IDEAS 2026-09-30; §11).

### 5.5 Echo and thru loops

With multi-client ports, a DAW track listening to the synth also receives:

- the synth's Tx Edit SysEx;
- the Bank Select and Program Change the synth may send when the editor selects a Tone.

The editor's setup notes tell the person to turn off MIDI thru, not only SysEx thru, from the synth's port on that track.

---

## 6. Views

**All views are built from aui parts and generated from the device model.**

- A firmware change that adds parameters needs a profile update, not new screens.
- The pack (§7) styles the views where packs apply. It cannot add, hide or move behaviour.

**Inside mazika, pages follow mazika's layout rules:**

- no scrolling;
- a 56 px unit;
- a 1024×576 reference size, 800×480 minimum.

### 6.1 Scene overview (the default page)

- **5 part strips side by side, like mixer channels.** Each strip shows:
  - part number;
  - engine and model (e.g. `Analog · JP-8`, `Drums · by reference`);
  - Tone name;
  - level, pan, mute/solo;
  - key range bar, octave;
  - arp/step mode;
  - MFX name;
  - output assign (THRU or DRIVE);
  - sends to chorus, delay and reverb;
  - a note-activity LED.
- **Above the strips:**
  - Scene name and picker;
  - DUAL / SPLIT;
  - the save and send actions: `Save sound as…` and `Send` in mazika, `Save snapshot` and `Restore` in the plugin;
  - the firmware and connection badge.
- **The SCENE/SYS switches** for chorus, delay, reverb, tempo and controllers sit next to the shared effects, so the person sees which settings actually apply.
- **Click a strip** to open its part editor.
- **At 800×480** the strips compress to name, engine, level and mute. Details are one tap away.

### 6.2 Part editor (the front panel)

- **Analog model:**
  - sections for OSC, Mod (sync, ring, x-mod), Mixer, HPF, Filter, Amp, ENV 1, ENV 2, LFO, and Voice (key mode, portamento, drift);
  - envelopes drawn as curves from their values; the LFO shows its wave;
  - switching the model (JP-8 → SH-101) re-forms the panel to that model's parameters.
  - Whether writing the `Model` value (both nibbles) switches the model, or only selecting a Tone from that model's bank does, is UNVERIFIED (§10).
- **JUPITER-X model:** its four oscillators, waveforms, osc pan and delay, plus filter, amp, envelope and LFO sections.
- **ZEN-Core:**
  - Common and Matrix Control;
  - 4 partial tabs, plus a "compare all 4" table;
  - per partial: Osc, Filter, Amp, three envelope curves, 2 LFOs with step patterns, EQ.
- **RD Piano:** its few parameters.
- **Drums, vocoder, expansions:**
  - the Scene-level part settings (level, pan, EQ, MFX, zone, arp) are editable;
  - the inner data shows "Not in the synth's public SysEx: saved by reference".
- **Every part also has** its MFX (type and parameters) and Part EQ.

### 6.3 Effects and routing

- **The signal flow** (MI):
  - parts → MFX → Part EQ → output assign: THRU, or DRIVE → Drive;
  - → sends to Chorus / Delay / Reverb (each part's own send levels, or Drive's send levels for parts routed through Drive);
  - → Master EQ / Comp → out.
- **Mic in** → noise suppressor → compressor → vocoder.
- **Settings that live in System** are marked "System · affects every Scene".
- **Settings SysEx cannot reach** are marked "Set on the synth".
- **In aui terms,** this is the synth's internal bus view (IDEAS 2026-09-29). Its routing is fixed; output assign, sends, levels and switches are editable.

### 6.4 Arpeggio and step sequencer

- **Per part:** Arp Mode (I-ARP / ARP / STEP), type, rhythm, motif and Step Seq Mode.
- **The step pattern** is a row of step keys with Probability, using aui's parameter-button painting gesture (AUI-147).

### 6.5 Performance view (phone, tablet, on stage)

- Scene picker, large.
- 4–8 macro knobs. The owner picks the parameters, saved in the snapshot (§4.1), not on the synth.
- Keys and wheels.
- Part mutes.
- Arp on/off.

### 6.6 Compact view and back panel

- **Compact tile:** Scene name, 5 part LEDs, connection (USB / Bluetooth "notes only" / off / "Managed by …"), and 4 macros.
- **Back panel:** generated from the synth's declared I/O:
  - USB (audio + MIDI);
  - MIDI in/out;
  - L/R out, phones;
  - mic in, pedal jacks;
  - Bluetooth.
  
  The exact jack list and USB MIDI ports are UNVERIFIED (§10).
- **Getting the synth's audio into mazika** (ux-spec §6.6.3):
  - USB audio needs Roland's VENDOR driver (snippet), and whether it is class-compliant is unverified (mazika's check U17).
  - The analog outputs into an interface are the fallback, and the only path on the Linux box unless U17 passes.

### 6.7 Librarian

- **Snapshots are the library's unit.** The library offers:
  - search by name, tag, engine and model;
  - marking favourites (mazika's `Star` in mazika);
  - A/B compare;
  - **Try**, which sends a sound without saving, under the confirmation rule of §4.5;
  - a diff between two snapshots, by part and parameter, from their decoded values.
- **A full backup** reads every user Scene and every user Tone into a folder of files.
  - User Tones in synth memory are opaque blocks (§2.3), so a full backup restores bit-exact but is not editable parameter by parameter. Editing a stored user Tone means loading it into a part first.
  - Timeouts in the `60 …` area are recorded as "slots 257–512 not enabled" (§2.1).
- **Writing to the synth** always goes through "Save to synth…".

---

## 7. The pack (the look)

- **The pack styles faces only:**
  - panel colours and materials;
  - knob caps, section legends, LED colour;
  - the LCD window (glass, as on real gear).
- **Two layers stay apart:**
  - **The device profile** (§2) is device data that ships with the editor, because it *is* the editor's function.
  - **The skin pack** is the external, text-editable look: JSON and SVG, with bitmaps allowed (IDEAS 2026-09-29). It is versioned separately from the editor (IDEAS 2026-09-30).
- **Where the pack applies:**
  - **In the plugin and any standalone host:** yes.
  - **Inside mazika:** mazika's synth pages follow its rule "**Sticker Deck only.** Nothing imitates the synth's own panel artwork." (ux-spec §6.4.4 rule 9). Until that rule changes (§9), the editor in mazika uses mazika's themes and the pack does not apply.
  - **Either way,** mazika brief §1a applies to mazika's own skins: never "others' logos, panel graphics or trade dress".
- **Replica or homage:**
  - The owner put replica homages in external, editable packs, never in the app (IDEAS 2026-09-30), and said the team makes the first pack.
  - **Settled by the owner (2026-10-01): the first-party pack is an unbranded homage with its own name.** It captures the panel's layout, colours and feel, with no Roland logos, product names or copied panel graphics.
  - Naming "JUPITER-Xm" to say which synth the editor drives is fine (mazika brief §1a).
- **No plugin sound.** The sound is the real synth.
  - The later synth controller device (README, roadmap) can reuse the same faces and the same descriptor shape.

---

## 8. aui parts this needs

- **In aui's requirements already:**
  - Knob, Fader, Toggle, Segmented;
  - ParamButton (painting);
  - Keys, Meter;
  - InfoView.
- **New:**
  - envelope curve (ADSR and multi-stage, drawn from values);
  - LFO shape indicator;
  - step-pattern row (with probability);
  - part strip;
  - key-range bar;
  - pad grid;
  - signal-flow diagram;
  - LCD/display window (glass material);
  - librarian list with tags and diff;
  - control-state marks (heard, not heard, pending, turned on the synth, set on the synth);
  - a progress-and-verify panel for long transfers;
  - "by reference" and "Managed by …" badges.

---

## 9. What mazika needs to change

The research read mazika@36bde22. These are changes for mazika's session to make. They are listed here so nothing is lost.

1. **M1.2's target.** HANDOFF names the Jupiter-Xm, but ux-spec §6.7 and the research still build M1.2 around the Roland S-1. The spec needs the Jupiter-Xm profile.
2. **First-party, not an extension.** The extension SDK forbids SysEx (`midi.send` is 3 bytes), has no MIDI input, and caps storage. So the editor's main side is mazika core code (`src/synth/`), with a sound-design client view.
3. **Synth profile v2.** v1 (`mazika/synth-profile/v1`) assumes:
   - one channel;
   - CCs per parameter;
   - a flat list, with unknown keys refused.
   
   v2 needs:
   - SysEx areas with bases per part, offsets and encodings;
   - per-firmware block sizes;
   - device ID and checksum rules;
   - 4 synth parts and a drum part with their own channels;
   - parameters that depend on the engine and model;
   - raw blocks outside the page-mapped list;
   - the reference user pattern (§4.1).
4. **The sound's shape.** A sound is a flat `values` array in profile order today. A Jupiter-Xm sound is the snapshot of §4: addressed blocks plus decoded values, with a `contentHash`. That is about 21 KB of data, roughly double as JSON text.
5. **Takes keep their sound as an immutable object.**
   - A Sound record is device-local and never replicated, and it can be deleted. So a take must not point to it.
   - Instead, the snapshot is stored as an immutable, content-addressed object in the take store (like take segments, e.g. `objects/<h>/<sha256>.json`, shared the same way).
   - `Take.synthSound` then holds that object's hash, plus `soundName` and `changedDuring`.
   - This keeps mazika's "Use this take's sound" working on every participant (ux-spec §10.4–§10.5).
6. **`synth.do` gains actions.** `save-sound`, `send-sound`, `send-whole`, `rename` and `delete` stay. Added:
   - `read-sound`;
   - `import`, `export`;
   - `save-to-synth {slot}`.
   
   `send-sound` gains the paced SysEx recall and read-back for this profile.
7. **`synth.state` sends changes per area,** not whole value lists at 20 per second.
8. **The `sounds` store in code.** The spec already has it (ux-spec §10.8); the code does not. §10.8 should also name its database.
9. **MIDI in mazikad.**
   - No design yet says how the native daemon owns MIDI and SysEx on macOS, Windows and Linux.
   - Until it does, the Jupiter core runs in mazika's browser core with Web MIDI.
   - Whether a headless core gets Web MIDI at all is UNVERIFIED (ux-spec §13.2). Until it is, the Jupiter core in mazika needs the core open in its own window.
10. **Synth-page artwork.** ux-spec §6.4.4 rule 9 ("Sticker Deck only") must change if the owner wants packs on mazika's synth pages (IDEAS 2026-10-01). Brief §1a's trade-dress rule still applies.
11. **Words:**
    - "sound", never patch, program or preset;
    - "scene", "capture" and "recall" stay with jam scenes and audio logging;
    - "audition" stays mazika's word for a take, so the library's send-without-saving is "Try";
    - favourites use `Star`;
    - no "Record" labels.
12. **A generic device profile** (added 2026-10-01). synthctrlr's device profile format (CONTROLLER-BUILDER §2) covers any synth or MIDI device: CC, NRPN and SysEx addressing, parts, engines, converters and a snapshot recipe. It is a candidate for mazika's synth profile v2 (item 3), so mazika and synthctrlr share one format.

---

## 10. Checks on the owner's synth

These belong on mazika's M1.2 hardware checklist ("Jupiter-Xm: its checklist comes with M1.2"). Most take minutes with a SysEx monitor.

1. **Identity reply** on 3.02, and again after the upgrade to 3.03. Record the four revision bytes.
2. **Block sizes that answer on 3.02 and 3.03,** against MI v1.06, especially:
   - Arpeggio Part (61 vs 59);
   - System Common (48 vs 47);
   - the JUPITER-X model block;
   - the 2,112-byte user pattern.
3. **What an RQ1 to an inactive engine's temporary area returns** (silence, stale data or defaults).
   - Also, where the editor DB's "Temporary Tone Type", part info and drum kit areas live.
4. **Whether one RQ1 can read a whole area,** and how many requests can be in flight at once.
5. **Recall order:**
   - how long after a Tone selection the temporary Tone can be written;
   - whether re-sending a Scene Part reloads the Tone and wipes edits;
   - whether writing Setup loads a Scene;
   - whether a Tone selected by DT1 makes the synth send Bank Select / Program Change.
6. **Whether writing the analog `Model` value switches the model.**
7. **Tx Edit:**
   - what a panel move sends, per engine (address, length, whole or partial nibble groups);
   - whether the synth echoes host DT1;
   - whether the `7F 00 7F 00`–`01` switches work.
8. **Whether the synth sends "Notify Scene Load" / "Notify Tone Load"** when the panel changes Scene or Tone, and whether that needs Editor Mode.
9. **Pacing:**
   - the sustained rate of single DT1 edits without drops or audio glitches;
   - the real time of a full capture and a full recall.
10. **Undocumented engines** (only if the owner wants them):
    - the drum kit;
    - the vocoder;
    - JD-800 at `02 30 …` and Vocal Designer at `02 40 …` (needs the expansions installed);
    - whether a JUNO-60 model exists on this unit;
    - the editor-area wave and expansion lists.
11. **Signed-value encodings** the MI leaves ambiguous (e.g. AMP MOD −100…100 in two nibbles).
12. **Whether System-area changes** (Master EQ/Comp, mic) persist across power cycles without a write.
13. **Ports and connection:**
    - USB MIDI port names per OS and driver mode, and which port carries SysEx;
    - the device ID set on the synth;
    - the rear jack list;
    - whether Bluetooth MIDI carries RQ1/DT1, and at what rate.
14. **What the synth shows when DT1 data arrives:** the "EDITED" mark, and names on the display.
15. **Whether selecting another Scene on the panel discards edits without asking,** and what it sends.
16. **Whether the `60 …` area (User Scenes 257–512) answers** on the owner's unit.
17. **The reference user pattern** of an initialised Scene (§4.1).
18. **Plugin hosts:**
    - duplicate-track behaviour per host (§5.2);
    - whether a Linux DAW holding rawmidi blocks the plugin (§5.1).
19. **What the screen shows** (VALUE-DISPLAY §7):
    - the 55 analog and JUPITER-X parameters the MI gives no display for;
    - names for the unlabelled lists;
    - sign, decimals and units;
    - release-time steps;
    - which OSC WAVE FORM positions each analog model uses;
    - anywhere the screen is coarser than the wire;
    - effect slots per type, if no public list is found.

---

## 11. Open questions for the owner

**Answered (2026-10-01; see `README.md`):**

- the whole Scene, its parts and saving to the computer come first;
- all engines, with the analog models first;
- runs in mazika and potentially other DAWs;
- firmware 3.02, with 3.03 planned;
- MIDI on the main side, the web view separate;
- **recall asks every time** ("Send · Cancel"), as mazika does. In a DAW, "recall on project load" runs without a prompt, because choosing that option is the consent (§4.5);
- **drum kits, the vocoder and the expansions by reference are enough for now.** Measuring their hidden areas is deferred (§2.2);
- **mazika's browser core first.** The Jupiter core starts in mazika's browser core page with Web MIDI and moves to mazikad later (§3.1, §5.3);
- **the first-party pack is an unbranded homage** with its own name (§7).

**Still open:**

1. **Snapshot files:** one JSON file per Scene with raw blocks plus readable values, shared by mazika and the plugin. Is that right, or do you also want Roland-compatible files later?
2. **Pro Tools (AAX):** left out at first by default (signing barrier). Do you need it early?
3. **Your synth:** do you own JD-800 or Vocal Designer, and does it show any JUNO-60 tones? This only matters once the deferred measuring happens.
