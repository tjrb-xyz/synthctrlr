# mi-sweep

Sweeps Roland's JUPITER-X/Xm MIDI Implementation (v1.06) for how each parameter's wire value turns into what the synth shows. It builds each parameter's converter, applies the initial values for what the MI leaves out, and checks every converter 1:1. The results and what they mean are in `docs/VALUE-DISPLAY.md` §2 and §10.

```sh
pdftotext -layout midi-spec.pdf mi.txt   # your own copy of the MI
python3 sweep.py mi.txt                  # counts, flagged parameters, the 1:1 check
python3 sweep.py mi.txt --initial ../../profiles/roland.jupiter-xm/initial-display.json
python3 sweep.py mi.txt --initial ../../profiles/roland.jupiter-xm/initial-display.json --json
                                         # every parameter with its converter, for building the profile
```

- The exit status is 1 if an initial value names no MI parameter or any converter fails the 1:1 check. On the MI alone, eight fail (VALUE-DISPLAY §10.2).
- Python 3, standard library only. `pdftotext` comes with poppler.
- The MI is Roland's document. It is cited, never copied: neither the MI nor this tool's output is committed. `initial-display.json` is committed: it holds facts only, each with its page.
- It talks to no synth and is not part of the editor.
