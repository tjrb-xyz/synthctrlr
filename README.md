# synthctrlr

A synth controller. Its first model is an editor for the owner's Roland JUPITER-Xm, driven over USB MIDI and SysEx, with its UI built on aui (tjrb-xyz/aui).

**Status:** design notes only. Nothing is built. Hardware checks, any probe tool and any build are frozen until the owner is at their computer with the synth.

The owner's words that started this repository (2026-10-01):

> I’ve outsourced the jupiter xm controller into a new repo, which has to have a new session and use “aui”. The new name is “tjrb-xyz/synthctrlr”. Can you open a new session as well as pose the requirements you have to “aui” in the documents you’ve been writing thus far.

| File | What it holds |
|---|---|
| `docs/README.md` | Purpose, the owner's decisions verbatim, the process model, the roadmap, open questions |
| `docs/DEVICE-MODEL.md` | The synth as seen over SysEx, Scene snapshots, plugin mode, views, the pack, what mazika must change, checks on the synth |
| `docs/SNAPSHOT-FORMAT.md` | The snapshot file `.jupiter-xm.json`: every field, the content hash, what a reader does |
| `docs/VALUE-DISPLAY.md` | Showing values as the synth shows them, 1:1: the sweep of the MI, converters, adjusting on the interface |
| `docs/AUI-REQUIREMENTS.md` | What synthctrlr needs from aui (SC-01…SC-30) |
| `tools/mi-sweep/` | Reads your own copy of the MI and classifies every parameter's conversion |

The notes come from tjrb-xyz/aui, branch `jupiter-xm`, `examples/jupiter-xm/`, where they were written.

**Rules:**

- Roland's MIDI Implementation is cited, never copied. Roland's editor database is used for structure only, never copied or shipped.
- No dependence on aui code until its licence and package name are settled.
