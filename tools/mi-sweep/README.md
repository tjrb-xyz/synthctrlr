# mi-sweep

Sweeps Roland's JUPITER-X/Xm MIDI Implementation (v1.06) for how each parameter's wire value turns into what the synth shows. The results and what they mean are in `docs/VALUE-DISPLAY.md` §2.

```sh
pdftotext -layout midi-spec.pdf mi.txt   # your own copy of the MI
python3 sweep.py mi.txt                  # counts and flagged parameters
python3 sweep.py mi.txt --json           # every parameter, for building the profile
```

- Python 3, standard library only. `pdftotext` comes with poppler.
- The MI is Roland's document. It is cited, never copied: neither the MI nor this tool's output is committed.
- It talks to no synth and is not part of the editor.
