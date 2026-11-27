[![make.fun](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/c/news-image-20261127)
[![Rank](https://make.fun/badge/news-image-20261127/AfrizalSek/news-image-20261127/rank.svg)](https://make.fun/c/news-image-20261127)
[![Reward](https://make.fun/badge/news-image-20261127/reward.svg)](https://make.fun/c/news-image-20261127)

# THE WORLD — Friday 27 November 2026

Make.fun entry for [news-image-20261127](https://make.fun/c/news-image-20261127):
sum up 27 November's world news in one image.

A single-page newspaper drawn entirely by hand in code — no photos,
no external assets. 42 stories across 10 regions, with a
numbers strip on top, three illustrated lead stories with
"WHY IT MATTERS", a world map pinned by story number, a "THE DAY IN
UTC" strip, a DATE CHECK footer listing stories from other days that
were deliberately left out, and a HOW SURE legend. All type is set
in Liberation Serif (Times-style), rendered by a minimal TrueType
rasterizer written in pure standard-library Python.

## How to run

```sh
python3 main.py
```

Writes `entry.png` (1024x1024, under 1 MiB) to `$MAKEFUN_OUTPUT_DIR`
or `/output` by default. Python 3 standard library only; the build is
fully deterministic — two runs produce byte-identical PNGs.

## Fonts

The typefaces are bundled in `fonts/` so the build reproduces anywhere:
Liberation Serif Regular and Bold, Copyright (c) 2012 Red Hat, Inc.,
licensed under the SIL Open Font License 1.1 (see `fonts/OFL.txt`).
`main.py` loads them by relative path; no system fonts are used.

## Contents

- `main.py` — the whole paper: Liberation Serif rasterizer, 15
  hand-drawn scenes, layout, and PNG writer
- `fonts/` — Liberation Serif Regular + Bold (SIL OFL 1.1) + `OFL.txt`
- `entry.png` — the finished front page
- `SOURCES.md` — the named source for every story and number
- `LICENSE` — MIT
