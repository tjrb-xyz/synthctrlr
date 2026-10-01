# Device values: showing what the synth shows

**Status:** draft 1, 2026-10-01. Design only; nothing is built.

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

**Findings:**

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

## 4. Where a conversion comes from

| `source` | Meaning | Shown on the control |
|---|---|---|
| `mi` | Read from the MI by the sweep | no mark |
| `measured` | Checked on the owner's synth | no mark |
| `convention` | The MI is silent; common practice assumed | "assumed" mark |
| `adjusted` | Set by the person on the interface (§6) | "adjusted" mark |
| `none` | Nothing known; the wire value is shown | "not known" mark |

The InfoView of every control always names the source.

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

- The 55 analog and JUPITER-X parameters with no display: what the screen shows at wire 0, 1, the middle, max − 1 and max.
- Names for the unlabelled lists (analog FILTER TYPE, MIXER DYNAMICS…).
- Sign, decimals and units on a sample of `offset` and `scale` parameters.
- Release-time steps: even, or a table.
- The arpeggio's Original Type No. and Original Rhythm No.
- Which OSC WAVE FORM positions each analog model uses.
- Anywhere the screen is coarser than the wire.
- Effect slots per type, if no public list is found.

## 8. What aui needs

Added to AUI-REQUIREMENTS as SC-28 to SC-30:

- **SC-28, value text from the app both ways:** a control shows text from an app-supplied format function and reads typed entry with an app-supplied parse function. A rejected entry shows the app's reason.
- **SC-29, source marks:** "assumed", "adjusted" and "not known" marks on any control, with the words supplied by the app, as with SC-07.
- **SC-30, editable list:** a short table of rows (wire value → text) with add, remove and reorder, reachable by keyboard. It is used for `labels`, `lookup` and the "Match the synth" pairs.

## 9. Choices to confirm

Each has a default this draft already uses:

1. **No mark on values from the MI;** marks only on assumed, adjusted and unknown values (§4).
2. **An adjustment applies to the whole definition by default:** all parts and all repeats (§6).
3. **Adjustments live in the user's folder,** outside snapshots and the profile, and can be shared back to this repository (§6).
