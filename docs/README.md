> **Source:** copied unchanged from tjrb-xyz/aui, branch `jupiter-xm` (PR #1), `examples/jupiter-xm/README.md`, commit `6426a67`, on 2026-10-01. In the text below, "this example" now means synthctrlr. The owner's quoted words are kept verbatim.

# Example: jupiter-xm

An editor for the owner's Roland JUPITER-Xm. It drives the real synth over USB MIDI and SysEx, and its UI is built with aui.

**Status:** design notes only. Nothing here is built.

**Outsourced (2026-10-01).** The Jupiter-Xm controller is outsourced to its own repository, **tjrb-xyz/synthctrlr**, which has its own session and builds on aui. The owner's words:

> I’ve outsourced the jupiter xm controller into a new repo, which has to have a new session and use “aui”. The new name is “tjrb-xyz/synthctrlr”. Can you open a new session as well as pose the requirements you have to “aui” in the documents you’ve been writing thus far.

- synthctrlr's session takes these notes as its starting point. synthctrlr replaces the "synth-modeller" repository named in the roadmap below.
- `AUI-REQUIREMENTS.md` lists what synthctrlr needs from aui.

**Frozen (2026-10-01).** Work on this example pauses until the owner is at their computer with the synth. That covers the hardware checks (DEVICE-MODEL §10), the probe tool and any build. The owner's words:

> I am not running on Mac yet so let’s keep these frozen for now until when I am on my computer

**To resume:**
- run the §10 checks on the owner's Jupiter-Xm (3.02, then 3.03);
- answer the last two open questions (snapshot file format, Pro Tools).

| File | What it holds |
|---|---|
| `README.md` | Purpose, the owner's decisions verbatim, the process model, the roadmap, open questions |
| `AUI-REQUIREMENTS.md` | What synthctrlr needs from aui: kit contracts, existing and new parts, theming and packs, gates |
| `DEVICE-MODEL.md` | The device model (draft 2): the synth as seen over SysEx, the address map, Scene snapshots, plugin mode, views, the pack, what mazika must change, checks on the synth |

---

## Purpose

- **Fix what makes the current tools annoying.** The owner's priorities, in order:
  1. see the whole Scene;
  2. edit its parts;
  3. save to the computer and reload it with every parameter of every part.
- **Support the analog models (JP-8, JX-8P, JUNO-106, SH-101) and the JUPITER-X model first**, with complete support of every engine as the goal, within what the synth's public SysEx allows (DEVICE-MODEL §2.2).
  - JUNO-60 is not in Roland's document for this synth. It is supported only if the owner's synth shows it (DEVICE-MODEL §10).
- **Run inside mazika, and potentially as a plugin in other DAWs.**
- **The sound comes off the Jupiter-Xm itself.** This example makes no sound of its own.
- **Prove aui's parts** (knobs, faders, envelope curves, part strips, the glass display window, the librarian) on a real device.

## The owner's decisions (verbatim)

**2026-10-01, modelling request:**

> Yes, I want you to model one for the Juliter XM. As It’s current editor and tooling is very annoying.

**2026-10-01, priorities, engines and hosts:**

> 1. It’s mainly about seeing the whole scene, editing its parts, and saving it, not necessarily on synth memory but computer memory and being able to reload the save with all the parameters and parts we’ve edited.
> 2. All engines are used but the analog models are the primary models to support here yet a complete support is desired
> 3. would love if this runs as part of mazika and potentially other daws as well
> 4. My jupiter is running the latest firmware

**2026-10-01, this PR, threads, the roadmap:**

> this should be its own PR. call it “jupiter-xm” and place under an example. The web view should be separate from the main thread which should handle midi. the sounds now come off the jupiter xm, and later on once dsper is wired and works properly we can build a synth controller device which will contain jupiter xm as model. let’s keep all of these notes in the jupiter-xm PR for now. Later on we can create a synth-modeller repo once we have the necessary UI elements here.

**2026-10-01, firmware:**

> I have version 3.02 but planning to upgrade to 3.03

**2026-10-01, four open questions (the owner picked from offered options; the chosen option is quoted):**

- Reload confirmation: "Ask every time (Recommended)".
- Drum kits, vocoder and expansions saved by reference: "Enough for now (Recommended)".
- mazika before native MIDI: "Yes, start there (Recommended)".
- The first skin pack: "Unbranded homage (Recommended)".

The earlier ideas behind this example are logged with dates in `aui-docs/IDEAS.md` on the `owner-ideas` branch:
- the synth as the first pack;
- the pack sitting beside its plugin;
- packs editable as text;
- replica homages live in external, editable packs, never in the app.

## Process model

The owner's rule: **the web view is separate from the main thread, and the main thread handles MIDI.**

```
 ┌──────────────────── main side ─────────────────┐        ┌──────── web view ────────┐
 │ MIDI port (USB)                                 │        │ aui views                │
 │ SysEx framing, checksum, packet pacing          │ ─────▶ │ replica of device state  │
 │ echo guard, Edit Tx parsing                     │ state  │ proposes edits           │
 │ device state: the current Scene                 │ ◀───── │ never touches MIDI       │
 │ snapshot capture and recall, snapshot store     │ edits  │                          │
 └─────────────────────────────────────────────────┘        └──────────────────────────┘
```

- **The main side owns everything that talks to the synth or the disk:**
  - the MIDI port;
  - SysEx encoding and pacing;
  - the device state;
  - the Scene snapshot store.
  
  It is one specification built two ways: native for the plugin and mazikad, and WebAssembly for mazika's browser core (DEVICE-MODEL §3.1).
  
  Which process this is depends on the host:
  - **mazika:** the core that owns the synth.
    - Today that is mazika's browser core page, using Web MIDI.
    - Later it is the native daemon, mazikad.
    - mazika already says "**A client never calls `requestMIDIAccess`.**" (mazika@36bde22:docs/ux-spec.md §6.6.2).
  - **A DAW plugin:** the plugin's own non-audio thread, which opens the synth's MIDI port itself rather than going through the DAW (DEVICE-MODEL §5). It is never the audio thread, and never the editor's web view.
- **The web view is a client.**
  - It holds a replica of the device state and proposes edits as messages (`synth.set {profileId, param, value}`, mazika's message).
  - It receives state updates (`synth.state`).
  - It can close, reload or crash without losing the synth's state.
- **Why:**
  - **Total recall works with the editor window closed:** a DAW project reload restores the synth from the main side. Every engine the public SysEx reaches is restored exactly; drum kits, the vocoder and expansion Tones are restored by reference (DEVICE-MODEL §2.2).
  - **No dependence on Web MIDI inside a host's web view.** WebKit has none, so WKWebView (macOS, iOS) and WebKitGTK (Linux) cannot reach MIDI. WebView2 (Windows) needs a SysEx permission (DEVICE-MODEL §3.1).
  - **Slow SysEx dumps never stall the UI.**

## Roadmap

1. **Now: a hardware editor.**
   - The Jupiter-Xm makes the sound. Its audio reaches mazika as a source:
     - through USB audio, which needs Roland's VENDOR driver and is not yet verified as class-compliant;
     - or through its analog outputs into an interface (DEVICE-MODEL §6.6).
   - aui supplies the views. The device model and the snapshot format live in this example.
2. **Later: a synth controller device.** Once dsper (tjrb-xyz/dsper) is wired and works properly, build a generic synth controller device that holds *models*; the Jupiter-Xm becomes its first model.
3. **A separate repository: `tjrb-xyz/synthctrlr`** (named "synth-modeller" at first). The owner created it on 2026-10-01, before aui has the UI elements this example needs (DEVICE-MODEL §8; `AUI-REQUIREMENTS.md`). synthctrlr's session builds on these notes.

## Open questions

The full list is in DEVICE-MODEL §11.

**Answered:**

- **Firmware:** 3.02, with 3.03 planned.
  - Roland's newest MIDI Implementation (v1.06) dates from 3.00, and the research found no reported parameter or SysEx changes in 3.01–3.03 (DEVICE-MODEL §2.6).
  - **Before upgrading,** take Roland's own backup as well.
- **Recall:** asks "Send · Cancel" every time. In a DAW, "recall on project load" is its own consent (DEVICE-MODEL §4.5).
- **Drum kits, vocoder, expansions:** saved by reference for now.
- **mazika:** starts in mazika's browser core, moves to mazikad later.
- **First pack:** an unbranded homage with its own name.

**Still open:**

1. **Snapshot files:** one JSON file per Scene (raw blocks plus readable values), or also Roland-compatible files later?
2. **Pro Tools (AAX):** left out at first by default. Needed early?
3. **Expansions and JUNO-60** on the owner's synth: only matters once the deferred measuring happens.
