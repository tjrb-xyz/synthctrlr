> **Source:** copied unchanged from tjrb-xyz/aui, branch `jupiter-xm` (PR #1), `examples/jupiter-xm/AUI-REQUIREMENTS.md`, commit `6426a67`, on 2026-10-01. In the text below, "this example" now means synthctrlr. The owner's quoted words are kept verbatim.

# What synthctrlr needs from aui

**Status:** draft 1, 2026-10-01.

- The Jupiter-Xm controller is outsourced to its own repository, **tjrb-xyz/synthctrlr**, which builds on aui.
- This file lists what that consumer needs from aui. It is written from this example's notes (`README.md`, `DEVICE-MODEL.md`) and from the ideas logged in `aui-docs/IDEAS.md` (branch `owner-ideas`).
- Ids `AUI-NNN` refer to aui's requirements (`aui-docs/REQUIREMENTS.md`, rev 2, branch `claude/happy-pasteur-7y8qeh`). New needs get ids `SC-NN`.

**The owner's words (2026-10-01):**

> I’ve outsourced the jupiter xm controller into a new repo, which has to have a new session and use “aui”. The new name is “tjrb-xyz/synthctrlr”. Can you open a new session as well as pose the requirements you have to “aui” in the documents you’ve been writing thus far.

**Split of responsibilities:**

| aui provides | synthctrlr keeps |
|---|---|
| Presentation: controls, parts, layout, theming, packs, accessibility | The Jupiter-Xm device profile (parameters, SysEx addresses, encodings) |
| A parameter model the views bind to | The SysEx core: framing, pacing, reply matching, echo guard, device state |
| Pack format, validation and loading | Scene snapshots, the librarian's storage, the plugin shell, MIDI ownership |
| Neutral default theme | The first-party Jupiter pack (an unbranded homage), shipped outside the app |

---

## 1. Kit contracts

| Id | Need | aui requirement |
|---|---|---|
| SC-01 | **Presentation only.** aui never opens MIDI, storage or audio. synthctrlr's main side owns MIDI, and aui's views are clients that render state and propose edits. | AUI-115 (carried) |
| SC-02 | **Declared-stable exports with exact versions,** so synthctrlr depends only on what aui promises. | AUI-122 (carried) |
| SC-03 | **Runs inside plugin web views:** <br>• WKWebView, including older hosts: no `light-dark()`, the dark block written twice <br>• WebView2 <br>• WebKitGTK <br>Colours are precomputed hex. | AUI-073, AUI-040, AUI-179, AUI-215 (carried) |
| SC-04 | **Loads nothing from elsewhere:** fonts and images are bundled, and it works under COOP/COEP `require-corp`. | AUI-162, AUI-163 (carried) |
| SC-05 | **Works without mazika:** a neutral default theme, and no mazika policy words in kit code. | AUI-028, AUI-014 |
| SC-06 | **A parameter model that a device descriptor maps into.** It must express: <br>• raw and display ranges, including signed offsets (e.g. 824–1224 shown as −200…+200) <br>• enums with labels <br>• units and value text <br>• a long name and info text <br>• which parameters exist for the selected engine and model | AUI-265 (open): synthctrlr's descriptor (DEVICE-MODEL §2.5) is one input to that decision |
| SC-07 | **Control states supplied by the app,** shown on any control: heard, not heard, pending send, turned on the synth, set on the synth. aui supplies the shapes; the app supplies the words, as with Tag. | New; same pattern as AUI-242 |
| SC-08 | **Fast external updates.** A ZEN-Core part has about 1,200 parameters, and the synth can stream panel moves. Views must update from outside without re-rendering everything. | AUI-135 (feed path), AUI-286 (open) |
| SC-09 | **Accessible by default:** <br>• every control has its role, name and value text <br>• confirmations are modal and keyboard-safe <br>• long transfers announce progress politely <br>• step rows and part strips are reachable by keyboard | aui §5 (mazika spec §9.8) |

## 2. Existing aui parts synthctrlr uses

These are all in aui's requirements already:

- **Knob,** including `knob-xl`.
- **Fader.**
- **ParamButton,** with the painting gesture for step rows (AUI-147). Painting semantics are still open (AUI-204).
- **Toggle, Segmented.**
- **Keys.**
- **Meter.**
- **InfoView.**
- **Tag** ("by reference", "SIM", firmware).
- **Banner, Toast.**
- **Sheet,** for the "Send · Cancel" recall confirmation and "Save to synth…".
- **Popover, Menu.**
- **Error parts:** structured timeout, checksum, partial-reply and port-lost errors.
- **The ADSR graph variant** (four handles, each a `role=slider`).

## 3. New parts synthctrlr needs

Ordered by the owner's priorities: see the whole Scene, edit its parts, save and reload.

| Id | Part | Used for | Priority |
|---|---|---|---|
| SC-10 | **Part strip:** a vertical channel with name, engine badge, level, pan, mute/solo, sends, a mode chip and an activity LED | Scene overview (DEVICE-MODEL §6.1) | 1 |
| SC-11 | **Key-range bar:** a small keyboard strip showing a part's low and high keys | Scene overview | 1 |
| SC-12 | **Section panel layout:** groups of controls laid out from descriptors, fitting a page with no scrolling (reference 1024×576, minimum 800×480), with a "hero" control per section | Part editor (§6.2) | 2 |
| SC-13 | **Envelope curve,** multi-stage beyond ADSR (pitch, filter and amp envelopes), drawn from values; editable through its own sliders | Part editor | 2 |
| SC-14 | **LFO shape indicator:** wave shape and rate, drawn from values | Part editor | 2 |
| SC-15 | **Display window:** an LCD-style readout behind a glass material | Part editor, compact tile | 2 |
| SC-16 | **Progress-and-verify panel:** a long transfer with per-block progress, cancel, and a result list ("all parts match", or mismatches with reasons) | Save and reload (§4) | 3 |
| SC-17 | **Librarian list:** search, tags, favourites (`Star` in mazika), A/B, and a diff between two items by group and parameter | Librarian (§6.7) | 3 |
| SC-18 | **Step-pattern row:** step keys with per-step probability, painted with ParamButton's gesture | Arpeggio and step sequencer (§6.4) | 4 |
| SC-19 | **Signal-flow diagram:** fixed routing with editable sends, levels and switches, marking which settings are System-wide | Effects (§6.3) | 4 |
| SC-20 | **Pad grid:** a note-keyed grid of pads | Drum part (by reference for now) | 5 |
| SC-21 | **Badges:** "by reference", "managed by …", "set on the synth", connection | Throughout | 1 |
| SC-22 | **Compact device tile and generated back panel** (jacks from declared I/O) | Compact view, back panel (§6.6; IDEAS 2026-09-29) | 5 |

## 4. Theming and packs

| Id | Need | Source |
|---|---|---|
| SC-23 | **Themes as data, skins by others, one DOM per theme;** schemas refuse unknown keys with a reason; contrast is checked | AUI-024, AUI-026, AUI-182, AUI-210, AUI-214 |
| SC-24 | **A public skin-pack format:** <br>• external and text-editable: JSON and SVG, bitmaps allowed <br>• versioned separately from the app <br>• validated before it is applied <br>• loaded locally from the person's files, never hot-linked <br>• it never changes behaviour | IDEAS 2026-09-29, 2026-09-30 |
| SC-25 | **Material tokens:** `glass.*` for windows and LCDs, `panel.*` for faceplates | IDEAS 2026-09-29 (glass is the enclosure, analog is the instrument) |
| SC-26 | **A headless pack API:** schema, `validate`, `apply` / `unapply`, `diff`, contrast check, live reload. Plus an inspect mode that shows a part's id and the tokens that style it. | IDEAS 2026-09-30 |
| SC-27 | **Image-based controls**, if a pack wants bitmap knobs. The first pack is an unbranded homage and prefers SVG, so this can wait. | AUI-138 (open) |

**Inside mazika,** synth pages follow mazika's "Sticker Deck only" rule (ux-spec §6.4.4 rule 9). The pack applies in synthctrlr's plugin and standalone hosts unless mazika changes that rule (DEVICE-MODEL §7, §9).

## 5. Gates

- **Licence (AUI-016, AUI-185; aui Q-01).**
  - aui's component code waits for the owner's licence choice.
  - synthctrlr ships plugins for other DAWs that bundle aui, so that choice decides what synthctrlr may ship and under what terms.
- **Package name and scope (aui Q-02).** synthctrlr imports aui by its published name, so that name is needed before synthctrlr can depend on a release.
- **Until both are settled,** synthctrlr designs against these needs and does not depend on aui code.
