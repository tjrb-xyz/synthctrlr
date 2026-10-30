"""Sweep Roland's JUPITER-X/Xm MIDI Implementation for value conversions.

Reads the text of your own copy of the MI (v1.06), made with
`pdftotext -layout midi-spec.pdf mi.txt`, and classifies every parameter by how
its wire value turns into what the synth shows (docs/VALUE-DISPLAY.md §2). It
then builds each parameter's converter (§3), applies the initial values for the
parameters the MI is silent on (§10), and checks every converter 1:1 (§1).

    python3 sweep.py mi.txt                      summary, counts and the flagged parameters
    python3 sweep.py mi.txt --initial FILE       the same, with initial values applied
    python3 sweep.py mi.txt [--initial FILE] --json
                                                 every parameter with its converter, for building the profile

FILE is a profile's initial-display.json, e.g.
../../profiles/roland.jupiter-xm/initial-display.json. The exit status is 1 if
an initial value does not fit the MI or any converter fails the 1:1 check.

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
# The parameter that picks each typed table's type, and how many slots it has.
TYPE_PARAM = {"MFX": "Type (* appendix 1)", "Chorus": "Chorus Type", "Reverb": "Reverb Type"}
# Unit tags the MI writes in brackets, as the synth writes them.
UNITS = {"EQFREQ": "Hz", "EQGAIN": "dB", "EQQ": "", "ASCII": ""}
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

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


def appendix1(path):
    """Return the MFX type names by value, from the MI's appendix 1, or [] if any is missing."""
    text = open(path, encoding="utf-8", errors="replace").read()
    page = next(p for p in text.split("\f") if re.search(r"^\* appendix 1", p, re.M))
    names = {}
    for name, value in re.findall(r"\|\s*([^|\s][^|]*?)\s*\|\s*(\d{1,2})\s*\|", page):
        if re.search(r"[A-Za-z]", name):
            names[int(value)] = name
    # The first rows of the table are split over several lines, so their names
    # stand alone in the Type column. Fill the missing values with them, in order.
    head = page[page.index("| Category"):]
    loose = [m.group(1) for m in re.finditer(r"^ {10,}\| (\S[^|]*?)\s*$", head[:head.index("|    ")], re.M)]
    for value in sorted(set(range(max(names) + 1)) - set(names)):
        if not loose:
            break
        names[value] = loose.pop(0)
    out = [names.get(v) for v in range(max(names) + 1)]
    return out if None not in out and len(set(out)) == len(out) else []


def unit_of(tag):
    if not tag:
        return ""
    tag = tag.strip("[]")
    return UNITS.get(tag, tag)


def decimals(s):
    return len(s.split(".")[1]) if "." in s else 0


def converter(p, mfx_types):
    """Return the parameter's converter (VALUE-DISPLAY §3) as the MI gives it."""
    lo, hi = p["raw"]
    shown, kind = p["display"], p["kind"]
    if kind == "typed":
        return {"kind": "typed", "by": TYPE_PARAM[p["table"]], "table": p["table"], "source": "mi"}
    if kind in ("identity", "offset", "scale", "pan", "text"):
        m = NUMRANGE.match(shown)
        a, b, unit = m.group(1), m.group(2), unit_of(m.group(3))
        if kind == "identity":
            return {"kind": "identity", "unit": unit, "source": "mi"}
        if kind in ("pan", "text"):
            return {"kind": kind, "source": "mi"}
        x, y = number(a), number(b)
        if kind == "offset":
            return {"kind": "offset", "offset": int(x - lo), "plus": x < 0, "unit": unit, "source": "mi"}
        step = (y - x) / (hi - lo)
        off = x / step - lo  # a fraction only when the MI's range cannot be exact; the 1:1 check says so
        return {"kind": "scale", "offset": int(off) if off.denominator == 1 else str(off),
                "num": step.numerator, "den": step.denominator,
                "decimals": max(decimals(a), decimals(b)), "plus": x < 0, "unit": unit, "source": "mi"}
    if kind in ("labels", "lookup"):
        items = [i.strip() for i in re.split(r",\s*", shown) if i.strip()]
        if kind == "labels":
            return {"kind": "labels", "labels": items, "source": "mi"}
        unit = unit_of(NUMBER.fullmatch(items[-1]).group(1))
        return {"kind": "lookup", "values": [re.sub(r"\[[^\]]*\]$", "", i) for i in items], "unit": unit,
                "source": "mi"}
    if p["table"] == "MFX" and "appendix 1" in p["name"] and len(mfx_types) == hi - lo + 1:
        return {"kind": "labels", "labels": mfx_types, "source": "mi"}
    return {"kind": "raw", "source": "none"}


def fmt(c, v, lo):
    """Return the text the synth shows for wire value v. Raises ValueError if inexact."""
    kind, unit, pad = c["kind"], c.get("unit", ""), c.get("pad", 0)
    if kind == "identity":
        return f"{v:0{pad}d}{unit}"
    if kind == "offset":
        x = v + c["offset"]
        return f"{'+' if c['plus'] and x > 0 else ''}{x:0{pad}d}{unit}"
    if kind == "scale":
        x = (v + Fraction(c["offset"])) * c["num"] / c["den"]
        q = x * 10 ** c["decimals"]
        if q.denominator != 1:
            raise ValueError(f"wire {v} gives {float(x)}, not {c['decimals']} decimals")
        sign = "-" if q < 0 else ("+" if c["plus"] and q > 0 else "")
        digits = str(abs(q.numerator)).rjust(c["decimals"] + 1, "0")
        whole, frac = digits[: len(digits) - c["decimals"]], digits[len(digits) - c["decimals"]:]
        return f"{sign}{whole}{'.' + frac if c['decimals'] else ''}{unit}"
    if kind == "labels":
        return c["labels"][v - lo]
    if kind == "lookup":
        return c["values"][v - lo] + unit
    if kind == "pan":
        x = v - 64
        return f"L{-x}" if x < 0 else (f"{x}R" if x > 0 else "0")
    if kind == "note":
        return f"{NOTE_NAMES[v % 12]}{v // 12 - 1}"
    if kind == "text":
        return chr(v)
    return str(v)


def check(c, values, lo, hi):
    """Return the 1:1 problems of converter c over the wire values (§1)."""
    if c["kind"] in ("raw", "typed"):
        return []
    if c["kind"] in ("labels", "lookup"):
        n = len(c["labels"] if c["kind"] == "labels" else c["values"])
        if n != hi - lo + 1:
            return [f"{n} entries for {hi - lo + 1} wire values"]
    seen, problems = {}, []
    for v in values:
        try:
            text = fmt(c, v, lo)
        except ValueError as e:
            return [str(e)]
        if text in seen:
            problems.append(f"wire {seen[text]} and {v} both show {text!r}")
        seen.setdefault(text, v)
    return problems[:3]


def pattern(name):
    return re.sub(r"\d+", "#", name)


def apply_initial(params, path):
    """Apply a profile's initial values to the MI's parameters. Return the errors."""
    doc = json.load(open(path, encoding="utf-8"))
    errors = []
    by_key = collections.defaultdict(list)
    for p in params:
        by_key[(p["table"], pattern(p["name"]), tuple(p["raw"]))].append(p)
    seen = set()
    for e in doc["entries"]:
        key = (e["table"], pattern(e["name"]), tuple(e["raw"]))
        where = f"{e['table']} / {e['name']}"
        if key in seen:
            errors.append(f"{where}: listed twice")
        seen.add(key)
        rows = by_key.get(key)
        if not rows:
            errors.append(f"{where} {e['raw']}: no such parameter in the MI")
            continue
        if "display" in e:
            if e.get("replaces") == "mi":
                if not e.get("conflict"):
                    errors.append(f"{where}: replaces the MI's conversion without saying why (conflict)")
                targets = rows
            else:
                targets = [p for p in rows if p["converter"]["source"] == "none"]
                if not targets:
                    errors.append(f"{where}: the MI already converts it; say replaces and why")
            for p in targets:
                p["converter"] = e["display"]
        lo, hi = e["raw"]
        for model, m in e.get("models", {}).items():
            a, b = m["raw"]
            if not lo <= a <= b <= hi:
                errors.append(f"{where}: {model}'s range {m['raw']} is outside {e['raw']}")
        for model, subset in e.get("subsets", {}).items():
            if not all(lo <= v <= hi for v in subset):
                errors.append(f"{where}: {model}'s subset is outside {e['raw']}")
        for p in rows:
            for k in ("models", "subsets", "blocks", "checks", "conflict", "evidence", "why"):
                if k in e:
                    p[k] = e[k]
    for name, table in doc.get("typed", {}).items():
        mi_table = table.get("layout", name)
        slots = sum(1 for p in params if p["table"] == mi_table and p["kind"] == "typed") // max(
            1, sum(1 for p in params if p["table"] == mi_table and p["name"] == TYPE_PARAM[mi_table]))
        for t in table["types"]:
            labels = [s["label"] for s in t["slots"]]
            if len(t["slots"]) > slots:
                errors.append(f"{name} type {t['type']}: {len(t['slots'])} slots, the block has {slots}")
            if len(set(labels)) != len(labels):
                errors.append(f"{name} type {t['type']}: two slots share a label")
            for s in t["slots"]:
                c = s["display"]
                if c["kind"] in ("labels",):
                    n = len(c["labels"]) - 1
                    bad = check(c, range(0, n + 1), 0, n)
                elif c["kind"] in ("identity", "offset"):
                    a, b = (int(x) for x in re.findall(r"[-+]?\d+", s["printed"])[:2])
                    bad = check(c, range(a, b + 1), a, b)
                else:
                    bad = []
                errors += [f"{name} type {t['type']} slot {s['slot']} {s['label']}: {x}" for x in bad]
    return doc, errors


def check_all(distinct):
    """Run the 1:1 check on every distinct definition. Return the errors."""
    errors = []
    for p in distinct.values():
        c, (lo, hi) = p["converter"], p["raw"]
        where = f"{p['table']} {p['offset']} {p['name']}"
        if "subsets" in p:
            for model, subset in p["subsets"].items():
                errors += [f"{where} ({model}): {b}" for b in check(c, subset, lo, hi)]
            continue
        errors += [f"{where}: {b}" for b in check(c, range(lo, hi + 1), lo, hi)]
        for block, alt in p.get("blocks", {}).items():
            a, b = alt["raw"]
            errors += [f"{where} ({block}): {x}" for x in check(alt["display"], range(a, b + 1), a, b)]
    return errors


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    params = parse(argv[1])
    mfx_types = appendix1(argv[1])
    for p in params:
        p["kind"], p["notes"] = classify(p)
        p["converter"] = converter(p, mfx_types)
    errors, doc = [], None
    if "--initial" in argv:
        doc, errors = apply_initial(params, argv[argv.index("--initial") + 1])

    def key(p):
        return (p["table"], pattern(p["name"]), tuple(p["raw"]), p["display"])

    distinct = {}
    for p in params:
        distinct.setdefault(key(p), p)
    errors += check_all(distinct)
    if "--json" in argv:
        json.dump(params, sys.stdout, indent=1, ensure_ascii=False)
        print()
        sys.exit(1 if errors else 0)

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
    used = [p for p in distinct.values() if p["kind"] != "reserved"]
    sources = collections.Counter(p["converter"]["source"] for p in used)
    label = f" after {argv[argv.index('--initial') + 1]}" if doc else ""
    print(f"converter sources{label}, {len(used)} definitions in use:")
    for k in ("mi", "guide", "measured", "convention", "adjusted", "none"):
        if sources[k]:
            print(f"  {k:10} {sources[k]:5}")
    print()
    if doc:
        unknown = [p for p in used if p["converter"]["source"] == "none" and p["kind"] != "typed"]
        print(f"still not known: {len(unknown)}")
        for p in unknown:
            print(f"  {p['table']:22} {p['offset']}  {p['name']:36} {p['raw'][0]}..{p['raw'][1]}")
        print()
        conflicts = [p for p in distinct.values() if "conflict" in p]
        print(f"the MI and the guide disagree: {len(conflicts)}")
        for p in conflicts:
            print(f"  {p['table']:22} {p['name']:36} {p['conflict']}")
        print()
        checks = sum(len(p.get("checks", [])) for p in distinct.values())
        print(f"checks on the synth: {checks}")
        print()
        print("typed tables:")
        for name, table in doc.get("typed", {}).items():
            mi_table = table.get("layout", name)
            n = next(p["raw"][1] for p in params if p["table"] == mi_table and p["name"] == TYPE_PARAM[mi_table])
            if name == "Scene Delay":  # the guide's own type list; its Type has the chorus's range
                n = table["types"][-1]["type"]
            print(f"  {name:12} {len(table['types']):3} of {n} types (type 0 has no slots)")
        print()
    print(f"validation (initial values and the 1:1 check): {'ok' if not errors else str(len(errors)) + ' problems'}")
    for e in errors:
        print(f"  {e}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv)
