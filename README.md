# synthctrlr

A controller for any synth or MIDI device, built from a data profile by a wizard or over MCP. Its first profile is an editor for the owner's Roland JUPITER-Xm, driven over USB MIDI and SysEx. Its UI is built on aui (tjrb-xyz/aui).

**Status:** design notes only. Nothing is built. Hardware checks, any probe tool and any build are frozen until the owner is at their computer with the synth.

The owner's words that started this repository (2026-10-01):

> I’ve outsourced the jupiter xm controller into a new repo, which has to have a new session and use “aui”. The new name is “tjrb-xyz/synthctrlr”. Can you open a new session as well as pose the requirements you have to “aui” in the documents you’ve been writing thus far.

| File | What it holds |
|---|---|
| `docs/README.md` | Purpose, the owner's decisions verbatim, the process model, the roadmap, open questions |
| `docs/DEVICE-MODEL.md` | The Jupiter-Xm profile's design notes: the synth as seen over SysEx, Scene snapshots, plugin mode, views, the pack, what mazika must change, checks on the synth |
| `docs/CONTROLLER-BUILDER.md` | Controllers for any device: the device profile, the wizard, the MCP server |
| `docs/SNAPSHOT-FORMAT.md` | The snapshot file, for any device: every field, the content hash, what a reader does |
| `docs/VALUE-DISPLAY.md` | Showing values as the synth shows them, 1:1: the sweep of the MI, converters, adjusting on the interface |
| `docs/AUI-REQUIREMENTS.md` | What synthctrlr needs from aui (SC-01…SC-33) |
| `tools/mi-sweep/` | Reads your own copy of the MI, builds every parameter's converter, applies the initial values and checks them 1:1 |
| `profiles/roland.jupiter-xm/initial-display.json` | Initial display values for what the MI leaves out, from Roland's Parameter Guide, each with its page |

The notes come from tjrb-xyz/aui, branch `jupiter-xm`, `examples/jupiter-xm/`, where they were written.

**Rules:**

- Roland's documents (the MIDI Implementation, the Parameter Guide) are cited, never copied. A profile takes facts from them (names, ranges, value lists) with the page, never their text. Roland's editor database is used for structure only, never copied or shipped.
- No dependence on aui code until its licence and package name are settled.
- Device profiles are data only, never code. MCP builds drafts; a person publishes, and only a person writes a device's memory.
