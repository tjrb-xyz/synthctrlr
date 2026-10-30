# Controllers for any device: profiles, the wizard and MCP

**Status:** draft 1.1, 2026-10-30. Design only; nothing is built.

- **Draft 1.1 records the owner's answers to §8** and adds initial values from a maker's documents (§3.6).

The owner's words (2026-10-01, verbatim):

> 3. sure
> 4. ok
> this process needs to be abstract for every synth through a wizard configured manually or via mcp
> we need an mcp ability to create controller of different synths or midi devices

"3" and "4" answer SNAPSHOT-FORMAT §11 choices 3 (bytes in 32-byte lines) and 4 (unknown keys refused, `x-` keys kept).

**So:**

- **synthctrlr is a controller for any synth or MIDI device.** The Jupiter-Xm is its first *device profile*, not special code.
- **A device profile is data.** One builder makes profiles, with two front ends:
  - **a wizard** a person fills in by hand;
  - **an MCP server** an AI client drives.
  
  Both call the same builder operations, so anything one can do, the other can.
- **This is the roadmap's "synth controller device that holds models"** (README, roadmap), arriving earlier and without sound of its own.

---

## 1. Generic or per device

| synthctrlr code (generic) | Device profile (data, per device) |
|---|---|
| MIDI ports, pacing, reply matching, echo guard | Identity, port names, channels and parts |
| SysEx dialects: a small, tested set (§2.3) | Which dialect, and its settings |
| Value converters (VALUE-DISPLAY §3) | Each parameter's address, encoding, range and converter |
| Snapshot capture and recall | Readable blocks and their sizes per firmware; the capture and recall recipe |
| Engine and model conditions | The device's engines and models, and how to detect them |
| Views generated from profiles (aui) | Pages, sections and hero controls |
| The builder, the wizard, the MCP server | The list of checks to run on the device, and their results |
| Schema and 1:1 checks | Sources the profile was built from, cited |

**Profiles are data only, never code.** A profile picks from what synthctrlr implements and sets its numbers. It cannot add behaviour.

- This keeps profiles safe to share, and safe to accept from an AI client.
- A device that needs something new, such as another SysEx dialect or converter kind, needs a change to synthctrlr, reviewed as code.

## 2. The device profile

### 2.1 File

- **Name:** `<id>.profile.json`, for example `roland.jupiter-xm.profile.json`.
- **JSON form:** as for snapshots (SNAPSHOT-FORMAT §1): sorted keys, two-space indent. Unknown keys are refused, except `x-` keys, which are kept.

### 2.2 Top level

```json
{
  "format": "synthctrlr.device-profile",
  "formatVersion": 1,
  "id": "roland.jupiter-xm",
  "version": "0.1.0",
  "status": "draft",
  "device": { "maker": "Roland", "model": "JUPITER-Xm", "kind": "synth" },
  "sources": [],
  "identify": {},
  "ports": {},
  "transport": {},
  "parts": [],
  "areas": {},
  "blocks": [],
  "engines": [],
  "parameters": [],
  "snapshot": {},
  "layout": {},
  "checks": []
}
```

| Key | What it holds |
|---|---|
| `id` | `<maker>.<model>`: lowercase letters, digits and `-`. It never changes once published. |
| `version` | Semantic version. Snapshots record it. |
| `status` | `draft`, `checked` or `published` (§3.3). |
| `device.kind` | `synth`, `drum-machine`, `effects`, `controller` or `other`. |
| `sources` | What the profile was built from, cited, e.g. `{ "kind": "spec", "title": "JUPITER-X/Xm MIDI Implementation", "edition": "1.06", "date": "2022-04-19" }`. A source can also be a dataset (§3.4), measurements, or adjustments. Only facts are taken from a source, never its text. |
| `identify` | The identity request and a reply pattern with `??` wildcards, and whether to ask the person to confirm the firmware (DEVICE-MODEL §2.6). Optional, since many devices do not answer. |
| `ports` | Port-name patterns per OS, and which port carries SysEx. |
| `transport` | The SysEx dialect and its settings (§2.3); pacing (largest packet, gap); the fastest edit rate per control; whether the device echoes what it receives. |
| `parts` | The device's parts (5 on the Jupiter-Xm, 1 on a mono synth). Each has an id, a kind (`synth`, `drum`…) and a MIDI channel, either fixed or set by a parameter. |
| `areas`, `blocks` | Named bases with per-part strides, and readable blocks with sizes per firmware (DEVICE-MODEL §2.3). Empty for a device that cannot be read. |
| `engines` | Engines and models, and the rules that detect the active one: a bank in a set, a parameter's value, or probing (DEVICE-MODEL §2.2). |
| `parameters` | Parameter descriptors (§2.4). |
| `snapshot` | The capture and recall recipe (§4). |
| `layout` | Pages, sections, hero controls, and which parameters each section shows. This feeds aui's section layout (SC-12). |
| `checks` | What to verify on the device, with results, firmware and date (DEVICE-MODEL §10, generalised). The wizard's check step fills them in. |

### 2.3 How a parameter is reached

Each parameter has one or more addresses:

| `via` | Fields | Can it be read back? |
|---|---|---|
| `sysex` | `area`, `offset`, `encoding` (`byte7`, `nibble2`, `nibble4`…) | Yes, if its block is readable |
| `cc` | `number`, optional `lsb` for a 14-bit pair, `channel` (the part's or fixed) | No: the editor remembers what it sent and what arrived |
| `nrpn`, `rpn` | `msb`, `lsb`, 7- or 14-bit value | No |
| `pc` | program change, with an optional bank-select pair | No |

A parameter with more than one address can, for example, be sent by CC for speed and read by SysEx.

**SysEx dialects** are code in synthctrlr. A profile chooses one and sets it:

- **`roland`:** DT1 and RQ1, the model id's length, 3- or 4-byte addresses, Roland's checksum. The Jupiter-Xm uses model id `00 00 00 65` and 4-byte addresses (DEVICE-MODEL §2.4).
- **`template`:** a fixed message with fields `{dev}`, `{addr}`, `{value}` and `{sum}`, and a checksum picked from a list: Roland, 7-bit sum, XOR, or none. This covers many simple parameter-change formats.
- **More dialects** (Yamaha, Korg…) are added as devices need them, each with tests.

### 2.4 Parameter descriptor

This generalises DEVICE-MODEL §2.5:

```json
{
  "id": "analog.filter.freq",
  "label": "Cutoff",
  "group": "Filter",
  "scope": "part:synth",
  "when": { "engine": "analog", "model": ["JP8", "JX8P", "JUNO106", "SH101"] },
  "address": [{ "via": "sysex", "area": "temp.tone.analog", "offset": "00 00 4F", "encoding": "nibble4" }],
  "raw": [0, 1023],
  "display": { "kind": "raw", "source": "none" },
  "hero": true,
  "info": ""
}
```

- **`scope`:** `device`, `scene`, or `part:<kind>`. A part-scoped parameter is repeated per part of that kind, as `part1.analog.filter.freq`.
- **`when`:** conditions under which the parameter exists. The panel shows it only when they hold. This is the device model deciding what exists, not a skin hiding controls (DEVICE-MODEL §2.5).
- **`display`:** a converter from VALUE-DISPLAY §3. Converters are generic.
- **`info`:** help text in the profile's own words, never copied from a manual.
- **`evidence`:** where a converter came from, when not from the device's MIDI document: the document, the page, and the value as printed (§3.6).
- **`models`, `subsets`, `blocks`:** a narrower range or set of values per model, and another block's own values (VALUE-DISPLAY §3).

## 3. The builder, the wizard and MCP

### 3.1 One builder

The main side holds a **profile builder**. It offers operations on a draft profile:

- create;
- set fields;
- add, change or remove parameters;
- import from a source (§3.4);
- validate;
- run checks on the device;
- preview the generated views;
- publish.

Every operation is validated and recorded in the draft's history, so it can be undone. **The wizard and the MCP server are two front ends over these same operations.**

### 3.2 The wizard (by hand)

It has seven steps. After step 1 they can be done in any order. The draft is saved after every step, so the work can stop and resume.

1. **Device:** maker, model, kind; pick its port. If it answers an identity request, `identify` is filled in.
2. **How it talks:** CC/NRPN, SysEx (pick a dialect and its settings), or both; channels; parts.
3. **Parameters:**
   - import them (§3.4), and/or type them into a table (SC-32);
   - **Learn:** move a control on the device, and the wizard catches the CC, NRPN or SysEx it sends and fills in the address. This needs the device.
4. **Values:** ranges and display converters (VALUE-DISPLAY), with "Match the device" (VALUE-DISPLAY §6).
5. **Reading and snapshots:** if the device can be read, its blocks and the capture and recall recipe; if not, it is send-only (§4).
6. **Layout:** pages, sections, hero controls, with a live preview of the generated views (SC-33).
7. **Check and save:**
   - validation: schema, the 1:1 check, overlapping addresses, every parameter either in a readable block or send-only, every parameter placed in the layout;
   - the device checks;
   - save, and publish when ready.

### 3.3 Draft, checked, published

- **`draft`:** being built. Usable by whoever is building it; views show a "draft" mark.
- **`checked`:** the device checks passed on a real unit. The firmware and date are recorded.
- **`published`:** exported as a file to share. **A person always confirms publishing;** MCP never publishes alone.
- **Profiles shipped with synthctrlr** are reviewed in this repository. A profile loaded from elsewhere is validated and shows its sources before use.

### 3.4 Importers

Importers produce draft parameters marked with their source. Nothing imported is trusted until checked.

- **`roland-mi`:** reads your own copy of a Roland MIDI Implementation. `tools/mi-sweep` is its first version. Other Roland MIs may share the same table layout; that is still to check.
- **`midi-guide`:** the open MIDI CC & NRPN dataset by Pencil Research (midi.guide; github.com/pencilresearch/midi).
  - It has 465 device files as CSV, one row per parameter: section, name, description, CC and NRPN numbers, ranges, default, notes. One of them is "Jupiter-X (Jupiter-Xm)".
  - Its licence is CC BY-SA 4.0. **A profile built from it may ship with synthctrlr** (the owner's answer, §8). It credits midi.guide in `sources` and is shared under CC BY-SA 4.0. Importing on a person's own computer works too.
- **`roland-guide`** (planned): reads your own copy of a Roland Parameter Guide, the manual of what the screen shows, as `roland-mi` reads the MI. Its first use is the Jupiter-Xm guide's pages that the web reader could not reach (VALUE-DISPLAY §10.3).
- **`csv`:** a plain sheet in synthctrlr's own columns, for typing in a manual's table.
- **By hand,** in the wizard.

### 3.5 MCP server

synthctrlr runs an MCP (Model Context Protocol) server, so an AI client (Claude Code, Claude Desktop or another MCP client) can build and test controllers on the person's computer.

**Where it runs:**

- The MCP server is part of the main side, because the main side owns MIDI and storage (README, process model).
- It runs first in the standalone app and as `synthctrlr mcp` over stdio (the owner's answer, §8). In mazika, it waits for mazikad.
- DAW plugins do not host it.

**Two modes:**

- **Offline** needs no device and offers only the profile tools.
- **Device tools** appear only while a device is connected *and* the person has turned them on for the session in the app.

**Tools:**

| Tool | What it does | Needs a device |
|---|---|---|
| `profiles.list`, `profiles.get` | List and read profiles | no |
| `profiles.create` | Start a draft: maker, model, kind | no |
| `profiles.update` | Change a draft's fields (a JSON patch, validated) | no |
| `parameters.upsert`, `parameters.remove` | Add, change or remove parameters | no |
| `profiles.import` | Run an importer (§3.4) on a file the person names | no |
| `profiles.validate` | The wizard's step 7 validation, as a report | no |
| `profiles.preview` | Render a generated view with sample values, as an image | no |
| `profiles.publish` | Ask the person to publish. It returns "waiting for the person". | no |
| `devices.list` | MIDI ports, and which profile matches each | yes |
| `devices.identify` | Send the identity request; return the reply and the matching profiles | yes |
| `devices.learn` | Listen for a few seconds while the person moves a control; report what arrived | yes |
| `devices.read` | Read one block named by the profile | yes |
| `devices.send` | Set one parameter in the edit buffer | yes |
| `devices.match` | Start "Match the device" for a parameter. The person types what the screen shows. | yes |

- **Resources:** the profile schema, the converter kinds, the dialect list, profiles, and these docs.
- **Prompts:** `new-controller`, which walks through the wizard's steps.

**Safety rules:**

1. **Data only.** MCP changes profiles only through builder operations. It cannot add code or touch files outside synthctrlr's folders, and importers read only files the person names.
2. **Drafts only.** MCP never publishes, and never changes a checked or published profile in place. Changing one makes a new draft version.
3. **Consent for the device.** Device tools stay off until the person turns them on in the app for that session. Every send shows in the app as it happens, in an activity list with Stop.
4. **Edit buffer only.** No MCP tool writes the device's memory: "Save to synth…" stays a person's action. System-area writes need the app's confirmation. A recall needs the "Send · Cancel" confirmation shown to the person (DEVICE-MODEL §4.5).
5. **Paced.** MCP sends go through the same pacing and exclusivity as any edit (DEVICE-MODEL §3.3).
6. **Logged.** Every MCP operation is in the draft's history, marked "via MCP".

### 3.6 Initial values from a maker's documents

The owner asked for initial values from the maker's PDF or the web, through MCP (the owner's answer 4, §8). So an AI client can fill a draft's values before anyone measures them.

- **The AI client reads.** It reads a PDF the person names, with `profiles.import` or its own tools, or searches the web. synthctrlr's MCP server fetches nothing itself.
- **It proposes through the builder.** Values arrive with `parameters.upsert`, like any edit to a draft.
- **Rules:**
  - Facts only: names, ranges, value lists and units, never a document's text.
  - Every value carries `evidence`: the document, the page, and the value as printed.
  - The maker's own documents give `source: "guide"`, shown with no mark. Anything else, or anything inferred, is `convention`, shown as "assumed".
  - Where a document disagrees with the device's MIDI document, the disagreement is recorded, never settled silently.
  - The 1:1 check (VALUE-DISPLAY §1) runs on every value. "Match the device" confirms them later.
- **The first case is the Jupiter-Xm** (VALUE-DISPLAY §10). Its result is `profiles/roland.jupiter-xm/initial-display.json`, which the sweep applies.

## 4. Snapshots for any device

SNAPSHOT-FORMAT becomes generic (draft 2). The changes:

- **Format and file:**
  - the format id becomes `synthctrlr.snapshot`;
  - a top-level `profile` holds `{id, version}`;
  - the file is `<name>.<profile id>.json`, for example `Night Brass.roland.jupiter-xm.json`.
- **Three kinds of device:**
  - **Readable** (SysEx dumps): `blocks` are authoritative, as now.
  - **Send-only** (CC, NRPN, program change; nothing can be read):
    - `values` are authoritative;
    - capture saves what the editor last sent and what arrived from the device, and says "not read from the device";
    - recall sends every value in the profile's order;
    - there is no read-back compare: the result says "sent, not verified".
  - **Mixed:** blocks where readable, values for the rest.
- **Profile-defined fields:** parts, engines and models take their names from the profile.
- **The hash covers both:** `contentHash` covers blocks and authoritative values, and its domain includes the profile id (SNAPSHOT-FORMAT §7).
- **`system` becomes the profile's *global context*:** settings that affect everything, saved for reference and restored only when ticked.
- **The Jupiter-Xm's specifics become its profile's recipe:** its 36 Scene blocks, light snapshots with the reference pattern, and its System context.

## 5. What changes in the other docs

- **DEVICE-MODEL** becomes the design notes for the Jupiter-Xm profile. Its §2.5 descriptor is generalised in §2.4 here. Its §9 gains a note for mazika: this profile format is a candidate for mazika's synth profile v2.
- **SNAPSHOT-FORMAT** goes to draft 2, generic (§4).
- **VALUE-DISPLAY:** its converters are generic, and "Match the synth" is "Match the device".
- **AUI-REQUIREMENTS** gains SC-31 to SC-33 (§6).
- **`tools/mi-sweep`** is the first version of the `roland-mi` importer.

## 6. What aui needs

- **SC-31, wizard:** steps with a state each (done, needs attention, waiting for the device), resumable and keyboard-reachable.
- **SC-32, large editable table:** hundreds of rows (the Jupiter-Xm has about 600 parameter definitions), only visible rows rendered, filter and sort, inline editing with validation messages, keyboard-reachable. SC-30's editable list is its small case.
- **SC-33, views without a device:** render a generated view from a profile and sample values, for the wizard's preview and MCP's `profiles.preview` (as an image). Related to SC-26 (headless pack API).

## 7. Order of work

**Now (design, no hardware):**

1. The profile schema, as a JSON Schema in this repository.
2. The Jupiter-Xm profile's skeleton: device, transport, areas and the parameters the sweep can fill, with the initial values of VALUE-DISPLAY §10. It is generated from your own copy of the MI. It may be committed and shipped, since it holds facts only, cited (the owner's answer 3, §8).
3. The builder operations: inputs, outputs and errors, shared by the wizard and MCP.
4. The MCP tools' input and output schemas.

**When the owner is at their computer:**

1. The core and the MCP server in offline mode (profiles only).
2. Then the device tools and the checks on the Jupiter-Xm.
3. Then the wizard's interface, once aui can be used (its licence and package name, AUI-REQUIREMENTS §5).

## 8. The owner's answers

The questions were:

1. May synthctrlr ship profiles built from the midi.guide dataset (CC BY-SA 4.0), with credit and under the same licence, or only import them locally?
2. Where MCP runs first: the standalone app, plus `synthctrlr mcp` over stdio, with mazika waiting for mazikad?
3. May profiles built from a maker's MIDI document (facts only, cited) be committed to this repository and shipped?
4. The value-display choices still open (VALUE-DISPLAY §9).

The owner's words (2026-10-01, verbatim):

> 1. sure whatever works
> 2.yes
> 3.yes
> 4. please read the pdf via the mcp or use the mcp to search the web and figure initial values

So:

1. **midi.guide profiles may ship,** credited and under CC BY-SA 4.0. Importing locally works too (§3.4).
2. **MCP runs first in the standalone app and as `synthctrlr mcp`** (§3.5).
3. **Profiles built from a maker's documents are committed and shipped,** facts only, cited (§7).
4. **Initial values come from the maker's documents and the web,** through an AI client over MCP (§3.6). The Jupiter-Xm's are in VALUE-DISPLAY §10. The three display choices of VALUE-DISPLAY §9 were not changed and stay the defaults.
