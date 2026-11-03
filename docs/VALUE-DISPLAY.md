# Device values: showing what the synth shows

**Status:** draft 2, 2026-10-30. Design only; nothing of the editor is built.

- **Draft 2 adds initial values from Roland's Parameter Guide** (§10), the owner's answer to the open choices. The sweep now builds every converter and runs the 1:1 check (§1) over all of them.

**Generic since 2026-10-01** (`CONTROLLER-BUILDER.md`): the converters, the 1:1 check and "Adjust display…" apply to every device profile. "Match the synth" is "Match the device". The Jupiter-Xm and its MI are the first case, and `tools/mi-sweep` is the first version of the `roland-mi` importer.

The owner's words (2026-10-01, verbatim), answering SNAPSHOT-FORMAT §11 choices 1 and 2:

> 1. yes
> 2.  sure can we have a converter built in to device actual values to be able to have 1:1 mapping? you can sweep the specs and allow adjustments on the interface itself.

So:

- **Snapshot files keep wire values** (SNAPSHOT-FORMAT §6). System context stays outside the content hash (SNAPSHOT-FORMAT §5).
- **The editor has a converter built in.** It shows every value as the synth's own screen shows it, and turns what the person types back into the exact wire value.
- **The conversions come from a sweep of Roland's MIDI Implementation** (§2).
- **Where the MI says nothing, or is wrong, the person can adjust the conversion on the interface** (§6).

---

## 1. What 1:1 means

- **Each wire value shows as exactly one text:** the text the synth's screen shows for it, with its sign, decimals and unit.
- **Each text the editor shows turns back into exactly one wire value.**
- **Nothing is rounded on the way.** Conversions use whole numbers and exact fractions, never floating point.
- **It is checked, not assumed.** When a profile loads, every wire value of every parameter is converted to text and back:
  - it must come back unchanged;
  - no two wire values may give the same text.
  
  The largest range is 65,536 values, so checking the whole profile takes well under a second. A profile that fails does not load, and the error names the parameter.
- **Typing is forgiving; showing is strict.** For a gain shown as `+24.0dB`, typing `24`, `+24` or `24 dB` is accepted. The editor always shows the synth's form.
- **If the synth's screen turns out coarser than the wire,** with two wire values showing the same text (found only by measuring, §7), the screen cannot be matched 1:1. The editor then shows the synth's text and adds the wire value in small type, for example `64 · 515`. Nothing is hidden, and the snapshot keeps the exact value.

## 2. The sweep of the MI

**Method:** `tools/mi-sweep/sweep.py` reads the text of your own copy of the MI v1.06 (`pdftotext -layout`) and walks the Parameter Address Map.

- The pages are two columns, and a table can continue from one page's right column to the next page's left. The tool reads them in that order.
- For each parameter row, it takes the wire range and the line under it that says what the value means.
- Its output is not committed, since it comes from Roland's document. It can be re-run when Roland publishes a new MI.

**Results.** The MI's tables have 2,330 parameter rows. Repeats (OSC1–3, four partials, 16 patterns × 64 steps…) collapse to 623 distinct definitions.

| Kind | Distinct | Rows | What the MI gives | Example |
|---|---|---|---|---|
| `labels` | 231 | 1,398 | one name per value | analog FILTER SLOPE: −12, −18, −24 dB |
| `offset` | 148 | 239 | shown = wire + a constant | analog FILTER KEY FOLLOW: wire 824–1224 shows −200…+200 |
| `identity` | 100 | 206 | shown = wire, sometimes with a unit | Partial EQ frequency 20–16000 |
| `none` | 96 | 281 | **nothing** | analog FILTER FREQ, wire 0–1023 |
| `scale` | 17 | 17 | shown = (wire + a constant) × a step | tempo: wire 2000–30000 shows 20.00–300.00 |
| `reserved` | 10 | 46 | unused | |
| `lookup` | 9 | 11 | one number per value | EQ Q: 0.5, 1.0, 2.0, 4.0, 8.0, 16.0 |
| `pan` | 6 | 12 | L64…63R | Part Pan |
| `text` | 3 | 48 | name characters | Scene and Tone names |
| `typed` | 3 | 72 | generic effect slots | MFX Parameter 1–32 |

**So the MI gives a conversion for 514 of the 613 definitions in use (84%).** The rest is below.

**Findings** (§10 answers most of them from Roland's Parameter Guide):

1. **The MI is silent on 96 definitions, and 55 of them are the analog and JUPITER-X models' main controls.** These are the first-priority engines.
   - With no display given: cutoff, resonance, HPF, envelope times and levels, LFO rate and delay, oscillator and noise levels, pulse width, portamento time, pitch drift, bend depth, cross-mod depth. The wire ranges are 0–1023, 0–255 or 0–127. Whether the screen shows 0–1023, 0–255, 0–127 or something else is not in the MI.
   - With no labels given: analog FILTER TYPE, FILTER HPF STEP, MIXER DYNAMICS, DYNAMICS PITCH / FILTER / AMP, AMP MOD STEP and ENV KEY FOLLOW STEP. They are lists of 4 or 7 values without names.
   - The other 41 follow common practice and get a converter marked "assumed" (§4): levels and sends 0–127, bank select and program change, key ranges as note names, velocity ranges.
2. **The effects slots depend on the effect type.**
   - MFX (32 slots), chorus (20) and reverb (20) carry −20000…+20000 on the wire. The delay uses the chorus block's layout, so it has the same 20 slots.
   - What each slot means, its range and its text depend on the selected type. The MI lists the MFX type names (its appendix 1) but not their parameters.
   - Until each type's table is filled in, a slot shows as "Parameter n" with its wire value. Where the per-type tables come from is open: Roland's other public documents for this synth are a candidate to check (cited, never copied); otherwise measuring (§7).
   - The Drive block's own parameters are in the MI.
3. **Five parameters have negative wire ranges inside nibble groups:** Mic Noise Suppressor Threshold, the arpeggio's Grid Offset, Offset Velocity and Probability Grid Offset, and analog AMP MOD. How a negative number is written on the wire is unclear (DEVICE-MODEL §10 item 11). This is an encoding question, not a display one, and is settled by measuring.
4. **Repeated labels:** the analog OSC1 and OSC3 WAVE FORM lists have 28 names with repeats, because each analog model uses its own part of the list. For 1:1, the editor shows only the current model's part. Which positions belong to which model is checked on the synth.
5. **Two ranges in the MI cannot be right:** the arpeggio's Original Type No. and Original Rhythm No. are wire 0–65 but shown as 0–255. They are treated as `identity` until measured.
6. **Assumed even steps:** Mic Comp and Master Comp release times (wire 0–99, shown 10–1000 ms). The MI gives only the ends, so the steps between are checked. Attack times come as full lists.
7. **Signs:** the MI writes the same kind of range as `-63 - +63` in one table and `-63 - 63` in another. Whether the screen shows a `+` is checked. Until then, signed values show a `+` (the converter's `plus` setting).

## 3. Converter kinds

The `display` field of a parameter descriptor (DEVICE-MODEL §2.5) holds one of these:

| Kind | Fields | Shown text |
|---|---|---|
| `identity` | `unit` | the wire value |
| `offset` | `offset`, `plus`, `unit` | wire + `offset` |
| `scale` | `offset`, `num`, `den`, `decimals`, `plus`, `unit` | (wire + `offset`) × `num` / `den`, with `decimals` places |
| `labels` | `labels`, optional `subsets` per model | `labels[wire − min]` |
| `lookup` | `values` (strings, as shown), `unit` | `values[wire − min]` |
| `pan` | — | `L64` … `0` … `63R` |
| `note` | `lowest` (default `C-1`) | note names: 0 = C-1, 60 = C4, 127 = G9 |
| `text` | — | the bytes as characters 32–127 |
| `typed` | `by` (the type parameter), `table` | the converter for the selected type's slot, from a per-type table |
| `raw` | — | the wire value, marked "not known" |

`identity` and `offset` also take `pad`: the fewest digits shown, with leading zeros. The arpeggio's types show as `00`–`65` (§10).

**Every converter also carries:**

- `source`: where it came from (§4);
- `unit`: the text after the value, as the synth writes it (`dB`, `ms`, `cent`…), or empty.

**Examples:**

```json
{ "kind": "offset", "offset": -1024, "plus": true, "unit": "", "source": "mi" }
{ "kind": "scale", "offset": -1024, "num": 1, "den": 10, "decimals": 1, "plus": true, "unit": "dB", "source": "mi" }
{ "kind": "labels", "labels": ["-12dB", "-18dB", "-24dB"], "source": "mi" }
{ "kind": "raw", "source": "none" }
```

**Rules:**

- For `scale`, every wire value must land exactly on `decimals` places. The loader checks this, so `num` / `den` can never cause rounding.
- For `labels` and `lookup`, the list length must equal the wire range, and no two entries may be equal (within a model's subset, for `subsets`).
- **`typed` tables** have one entry per effect type: `{ "type": 3, "slots": [ { "slot": 1, "label": "…", "display": { … } } ] }`. A slot missing from its type's table shows as `raw`.
- **A model can show less than the wire range.** A descriptor's `models` gives a model a narrower range, for example `"JP8": { "raw": [1024, 1224] }`, and `subsets` gives it a set of wire values, for `labels`. The panel offers only those values for that model.
- **A block can reuse another's layout with its own values.** The Scene Delay uses the Chorus block's layout but has its own six types. A descriptor's `blocks` gives such a block its own range and converter.

## 4. Where a conversion comes from

| `source` | Meaning | Shown on the control |
|---|---|---|
| `mi` | Read from the MI by the sweep | no mark |
| `guide` | Read from the maker's own manual of what the screen shows: for the Jupiter-Xm, Roland's Parameter Guide (§10) | no mark |
| `measured` | Checked on the owner's synth | no mark |
| `convention` | The MI is silent; common practice assumed | "assumed" mark |
| `adjusted` | Set by the person on the interface (§6) | "adjusted" mark |
| `none` | Nothing known; the wire value is shown | "not known" mark |

The InfoView of every control always names the source, and for `guide` and `convention` its evidence: the document, the page and the value as printed.

## 5. Where the converter runs

- **The descriptors are data in the profile.** The main side (the Rust core, and mazika's TypeScript browser core until then) uses them for typed entry, the librarian's diff, and anything that reads a snapshot for a person.
- **The web view formats on its own,** because panel moves arrive faster than a round trip to the main side should take. It receives the descriptors with the profile and formats them with a small formatter.
- **Both formatters run the same test vectors:** every wire value of every parameter with its expected text, generated once from the profile. They cannot drift apart.
- **aui shows the text; it never converts** (SC-28).
- **Snapshot files hold wire values only.** Display text is never stored in them, so changing a conversion never changes a snapshot or its hash.

## 6. Adjusting on the interface

**Every control has "Adjust display…"** in its context menu and in its InfoView. It opens a sheet that shows:

- the wire range, the current converter and its source;
- a preview: the first, last, current and a few middle values, wire → shown;
- fields to change the converter: its kind, offset, step, decimals, unit and sign, or the list for `labels` and `lookup`.

**"Match the synth":**

1. The editor sends a few wire values to the synth one at a time, or reads the current one.
2. The person types what the synth's screen shows for each.
3. The editor proposes the converter that fits every pair (offset, scale, or a lookup list) and lists any pair it cannot fit.
4. The original value is sent back afterwards.

These sends are ordinary edits to the edit buffer, so they need the synth connected. They wait, like all hardware work, until the owner is at their computer.

**Saving:**

- **Saving runs the 1:1 check** (§1). If two wire values would show the same text, it refuses and names them.
- **By default an adjustment applies to the whole definition:** every part, and every repeat such as OSC1–3 or ENV1–2. It can be narrowed to one parameter.
- **An adjustment changes only what is shown and how typing is read.** It never changes a wire value, anything sent to the synth, or a snapshot.
- **Reset** works per parameter or for all.

**Where adjustments live:** `display-adjustments.json` in the per-user folder (DEVICE-MODEL §4.6). In mazika, the same JSON lives in the owning core's store, and the sheet is shown in the client.

```json
{
  "format": "synthctrlr.display-adjustments",
  "formatVersion": 1,
  "profile": "roland.jupiter-xm",
  "adjustments": {
    "analog.filter.freq": {
      "display": { "kind": "scale", "offset": 0, "num": 1, "den": 4, "decimals": 0, "unit": "", "source": "adjusted" },
      "pairs": [[0, "0"], [1023, "255"]],
      "firmware": "3.02",
      "at": "2026-10-01T18:42:07Z"
    }
  }
}
```

The converter in this example is made up, to show the shape. It also shows why "Match the synth" lists pairs it cannot fit: a ÷4 scale would show 1023 as 255.75, which the `scale` rule (§3) refuses, so this case would need a `lookup` or a measured rule.

- **`pairs`** records what the person saw, so the adjustment can be checked later.
- **When a newer profile ships its own converter** for an adjusted parameter, the adjustment stays in effect. The editor says the profile now has one and offers to drop the adjustment.
- **Adjustments can be shared back.** The file can be sent to this repository, so the profile gains them as `measured` and everyone gets them.

## 7. Checks on the synth

Added to DEVICE-MODEL §10 as item 19. Most of them are "Match the synth" itself, so the measuring tool and the adjusting sheet are the same flow, and their results become profile data.

Since §10, most of these start from the Parameter Guide and only need confirming. Each entry in `initial-display.json` lists its own checks.

- A sample of the analog values from the guide, for example cutoff at wire 0, 512 and 1023.
- The JUPITER-X model's 27 values, assumed by analogy (§10): what the screen shows at wire 0, 1, the middle, max − 1 and max.
- Which wire value of the analog FILTER TYPE is JP, R, M and S.
- The arpeggio's I-Arp Style and Probability Style, where the MI and the guide disagree.
- Sign, decimals and units on a sample of `offset` and `scale` parameters.
- Release-time steps: even, or a table.
- Which OSC WAVE FORM positions each analog model uses (assumed in §10).
- Anywhere the screen is coarser than the wire.
- Effect slots: their order and the wire value of a few, per type (§10). The MFX slots, once their pages are read.

## 8. What aui needs

Added to AUI-REQUIREMENTS as SC-28 to SC-30:

- **SC-28, value text from the app both ways:** a control shows text from an app-supplied format function and reads typed entry with an app-supplied parse function. A rejected entry shows the app's reason.
- **SC-29, source marks:** "assumed", "adjusted" and "not known" marks on any control, with the words supplied by the app, as with SC-07.
- **SC-30, editable list:** a short table of rows (wire value → text) with add, remove and reorder, reachable by keyboard. It is used for `labels`, `lookup` and the "Match the synth" pairs.

## 9. Choices to confirm

The owner's answer (§10) asked for initial values from the documents and did not change these three. They stay the defaults:

1. **No mark on values from the MI;** marks only on assumed, adjusted and unknown values (§4).
2. **An adjustment applies to the whole definition by default:** all parts and all repeats (§6).
3. **Adjustments live in the user's folder,** outside snapshots and the profile, and can be shared back to this repository (§6).

## 10. Initial values from Roland's documents

The owner's words (2026-10-01, verbatim), answering CONTROLLER-BUILDER §8 (1–3) and §9 here (4):

> 1. sure whatever works
> 2.yes
> 3.yes
> 4. please read the pdf via the mcp or use the mcp to search the web and figure initial values

So the values the MI leaves out start from Roland's own public documents, not only from measuring. Reading a maker's documents is also something an AI client does for any device over MCP (CONTROLLER-BUILDER §3.6). This section is the first case: an AI read Roland's PDFs on the web and wrote the results as profile data.

**Where it lives:** `profiles/roland.jupiter-xm/initial-display.json`. It is committed (the owner's answer 3).

- Facts only: names, ranges and value lists as printed, with the page. No description text is copied.
- Each entry names an MI parameter and gives its converter (§3), its evidence (document, page, the model or section, the value as printed), why, its checks on the synth, and any disagreement with the MI.
- `tools/mi-sweep/sweep.py mi.txt --initial …/initial-display.json` applies it. It fails if an entry names no MI parameter, or if any converter fails the 1:1 check.

### 10.1 What was read

| Id | Document | Pages read |
|---|---|---|
| `pg06` | JUPITER-X/Xm Parameter Guide, edition 06 (Ver. 3.0 and later) | 3–20 |
| `pg03` | JUPITER-X/Xm Parameter Guide, edition 03 | 14–20 (the JX-8P) |
| `pgxm01` | JUPITER-Xm Parameter Guide, edition 01 | 17–18 (the SH-101) |
| `rm07` | JUPITER-X Reference Manual, edition 07 (Ver. 3.0 and later) | 2–32 |

- **The web reader stops about 20 pages into each PDF.** The guide's pages 21–75 could not be read this way. They hold the JUPITER-X model, the System parameters and the MFX.
- **The reader answers questions about a PDF; it does not hand over its text.** A misread is possible. Every value cites its page, so it can be checked, and "Match the device" corrects it.
- The SH-101 and the second half of the JX-8P come from older editions, because they fall past page 20 in edition 06. Version 3 may have changed them.

### 10.2 Results

Of the 96 definitions the MI is silent on:

| Now | Count | What |
|---|---|---|
| `guide` | 48 | 26 analog model controls; scene, part and zone levels, sends, key ranges and velocities; the arpeggio's key range; drive; voice reserve; reverb type; chorus type, level and send; MFX switch |
| `mi` | 2 | MFX type names, from the MI's own appendix 1, which the sweep now reads; NAME 1, as NAME 2–16 |
| `convention` | 42 | the JUPITER-X model's 27, by analogy; analog AMP MOD; bank select and program change; the USB levels and aftertouch sense; reverb level; piano resonance; expansion and user-data numbers |
| still `none` | 4 | analog FILTER TYPE, I-Arp Style, Probability Style, MFX CtrlAsgn |

Two more replace the MI's own conversion: the arpeggio's Original Type No. and Original Rhythm No. The MI shows wire 0–65 as 0–255, which cannot be 1:1. The guide shows `00`–`65`.

**With the initial values, every converter passes the 1:1 check.** On the MI alone, eight fail: those two arpeggio numbers, and the OSC WAVE FORM lists' repeated names.

**Findings:**

1. **The screen shows the wire value.** Every analog model's cutoff, resonance, HPF, envelope stages, LFO rate and delay, and portamento time show 0–1023, the same as the wire. Levels show 0–255, cross mod 0–10800, pitch drift 0–255. The Reference Manual's example screen shows 1023 (`rm07` p. 6). So 1:1 is exact for these.
2. **Each analog model shows only part of some shared ranges.**
   - FLT KEY FOLLOW shows 0–200 on all four. By the MI's −200…+200 conversion that is wire 1024–1224.
   - BEND PITCH shows 0–1200 on the JUPITER-8 and JUNO-106, and 0–1500 on the SH-101, of the wire's 0–4800. The JX-8P uses its own step list (2, 3, 4, 7).
   - The JUPITER-8 offers two filter slopes, −12dB and −24dB, of the MI's three.
   
   These become `models` ranges and `subsets` (§3). The panel offers only those values.
3. **The OSC WAVE FORM list is in runs, one per model:** wire 0–5 for the SH-101, 6–9 for the JUNO-106, 10–15 for the JUPITER-8, 16–19 for the JX-8P. The runs match the guide's per-model wave lists. Wire 20–27 match none of the four. This answers §2 finding 4, assumed until checked.
4. **Most "unlabelled" lists are plain numbers.** MIXER DYNAMICS, DYNAMICS PITCH, FILTER and AMP, FILTER HPF STEP and AMP MOD STEP show 0–3. Only FILTER TYPE has names: JP, M and S on the JUPITER-8; R, M and S on the others. Which wire value is which is not documented.
5. **The JUPITER-X model** has the same kinds of controls on the same ranges as the analog models. Its 27 are assumed to show the wire value too, marked "assumed", until its pages are read or measured.
6. **The arpeggio:** Type and Rhythm show `00`–`65` (§2 finding 5). I-Arp Style and Probability Style disagree with the MI (wire 0–65 against a printed 000–111; wire 0–255 against OFF and 1–64), so they stay "not known".
7. **Effects:** every chorus type (10), delay type (5) and reverb type (8) is listed with each slot's name and printed range (`pg06` pp. 7–10).
   - Assumed: the slots follow the guide's order, and a slot's value is the shown number or the list position from 0.
   - Slots shown with decimals (rates in Hz, times in seconds) stay "not known", since their step on the wire is not documented.
   - The Scene Delay has its own six types although it uses the chorus block's layout. Whether they are wire 0–5 is a check.
   - The 93 MFX types' slots wait for pages 40–75.

### 10.3 To finish

- **Pages 21–75 of the guide:** the JUPITER-X model, the System and the MFX slots. With the PDF itself, a `roland-guide` importer can read its text exactly, as `mi-sweep` reads the MI, instead of through a web reader. Two ways:
  - the owner adds the Parameter Guide PDF to the project;
  - or the owner allows `static.roland.com` in the cloud environment's network settings.
- **The checks on the synth** listed with each entry, when the owner is at their computer.
