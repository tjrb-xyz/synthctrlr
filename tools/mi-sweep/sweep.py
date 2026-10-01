"""Sweep Roland's JUPITER-X/Xm MIDI Implementation for value conversions.

Reads the text of your own copy of the MI (v1.06), made with
`pdftotext -layout midi-spec.pdf mi.txt`, and classifies every parameter by how
its wire value turns into what the synth shows (docs/VALUE-DISPLAY.md §2).

    python3 sweep.py mi.txt            summary, counts and the flagged parameters
    python3 sweep.py mi.txt --json     every parameter, for building the profile

The MI is Roland's document. Neither it nor this tool's output is committed.
Standard library only.
"""

import collections
import json
import re
import sys
from fractions import Fraction

CELL = re.compile(r"\|(#?)\s*((?:[0-9A-F]{2} ){1,3}[0-9A-F]{2})?\s*\|\s*([0a-d]{4} [0a-d]{4})?\s*\|([^|]*)\|")
HEAD = re.compile(r"\* \[([^\]]+)\]")
PARAM = re.compile(r"^(.*?)\s*\((-?\d+)\s*-\s*(-?\d+)\)\s*$")
NUMRANGE = re.compile(r"^(L?[-+]?[\d.]+R?)\s*-\s*(L?[-+]?[\d.]+R?)\s*(\[[^\]]*\])?$")
NUMBER = re.compile(r"[-+]?[\d.]+(\[[^\]]*\])?")
TYPED_TABLES = ("MFX", "Chorus", "Reverb")

# The pages are two columns side by side. Anything starting at or after this
# character position belongs to the right column.
SPLIT = 70

# Cells that are not parameter rows. They are blanked (same width) before
# matching, so their bars cannot pair up with a neighbouring cell's.
NOISE = [
    re.compile(r"\|\s*Offset\s*\|[^|]*\|"),
    re.compile(r"\|\s*Address\s*\|[^|]*\|"),
    re.compile(r"\|-+\+-+\|"),
    re.compile(r"\|\s*(?:[0-9A-F]{2} ){3}[0-9A-F]{2}\s*\|\s*Total Size\s*\|"),
    re.compile(r"\|\s*(?:[0-9A-F]{2} ){2,3}[0-9A-F]{2}\s*\|[^|]*\[[^\]]+\]\s*\|"),
    re.compile(r"\|\s*:\s*\|[^|]*\|"),
]


def blank(line):
    for rx in NOISE:
        line = rx.sub(lambda m: " " * len(m.group(0)), line)
    return line


def column(pos):
    return 1 if pos >= SPLIT else 0


def parse(path):
    """Return one dict per parameter row of the Parameter Address Map."""
    text = open(path, encoding="utf-8", errors="replace").read()
    # Collect events per page, then replay them in reading order: the left
    # column, then the right. A table that starts in the right column carries
    # on in the next page's left column.
    events = []
    in_map = False
    for page in text.split("\f"):
        cols = [[], []]
        for line in page.split("\n"):
            if "3. Parameter Address Map" in line:
                in_map = True
            if "4. Supplementary Material" in line:
                in_map = False
            if not in_map:
                continue
            for m in HEAD.finditer(line):
                cols[column(m.start())].append(("head", m.group(1)))
            for m in re.finditer(r"Total Size|\+-{5,}", line):
                cols[column(m.start())].append(("end", None))
            for m in CELL.finditer(blank(line)):
                cols[column(m.start())].append(("cell", m.groups()))
        events.extend(cols[0])
        events.extend(cols[1])

    table, current, params = "?", None, []
    for kind, data in events:
        if kind == "head":
            table, current = data, None
        elif kind == "end":
            current = None
        else:
            _, offset, bits, desc = data
            desc = desc.strip()
            pm = PARAM.match(desc) if desc else None
            if offset and bits and pm:
                current = {
                    "table": table,
                    "offset": offset,
                    "bits": bits,
                    "name": pm.group(1).strip(),
                    "raw": [int(pm.group(2)), int(pm.group(3))],
                    "display": [],
                }
                params.append(current)
            elif offset and bits:
                if desc:
                    current = None
            elif not offset and not bits and desc and current is not None:
                current["display"].append(desc)
    for p in params:
        p["display"] = " ".join(p["display"]).strip()
    return params


def number(s):
    return Fraction(s.replace("+", ""))


def classify(p):
    """Return (kind, notes) for one parameter. Kinds match VALUE-DISPLAY.md §3."""
    lo, hi = p["raw"]
    shown = p["display"]
    notes = []
    if lo < 0:
        notes.append("negative-raw")
    if p["table"] in TYPED_TABLES and re.search(r"Parameter \d+$", p["name"]):
        return "typed", notes
    if p["name"].lower() == "reserved":
        return "reserved", notes
    if not shown:
        return "none", notes
    m = NUMRANGE.match(shown)
    if m and "," not in shown:
        a, b, unit = m.group(1), m.group(2), m.group(3)
        if a.startswith("L") or b.endswith("R"):
            return "pan", notes
        if unit == "[ASCII]":
            return "text", notes
        x, y = number(a), number(b)
        if (x, y) == (lo, hi):
            return "identity", notes
        if hi == lo:
            return "other", notes
        step = (y - x) / (hi - lo)
        if step == 1:
            return "offset", notes
        # A step that is not a whole number or a whole fraction of one is
        # unlikely to be linear on the synth.
        if step.denominator not in (1, 2, 4, 5, 10, 20, 100) and step.numerator != 1:
            notes.append("suspect-scale")
        return "scale", notes
    items = [i.strip() for i in re.split(r",\s*", shown) if i.strip()]
    if len(items) == hi - lo + 1:
        if len(set(items)) != len(items):
            notes.append("duplicate-labels")
        if all(NUMBER.fullmatch(i) for i in items):
            return "lookup", notes
        return "labels", notes
    return "other", notes + ["count-mismatch"]


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    params = parse(argv[1])
    for p in params:
        p["kind"], p["notes"] = classify(p)
    if "--json" in argv:
        json.dump(params, sys.stdout, indent=1)
        print()
        return

    def key(p):
        return (p["table"], re.sub(r"\d+", "#", p["name"]), tuple(p["raw"]), p["display"])

    distinct = {}
    for p in params:
        distinct.setdefault(key(p), p)
    rows = collections.Counter(p["kind"] for p in params)
    kinds = collections.Counter(p["kind"] for p in distinct.values())
    print(f"parameter rows {len(params)}, distinct definitions {len(distinct)}")
    for k in sorted(kinds, key=lambda k: -kinds[k]):
        print(f"  {k:10} {kinds[k]:5} distinct  {rows[k]:5} rows")
    print()
    for flag in ("none", "typed", "negative-raw", "duplicate-labels", "suspect-scale", "count-mismatch"):
        hits = [p for p in distinct.values() if p["kind"] == flag or flag in p["notes"]]
        print(f"{flag}: {len(hits)}")
        for p in hits:
            print(f"  {p['table']:22} {p['offset']}  {p['name']:36} {p['raw'][0]}..{p['raw'][1]}  {p['display'][:40]}")
        print()


if __name__ == "__main__":
    main(sys.argv)
