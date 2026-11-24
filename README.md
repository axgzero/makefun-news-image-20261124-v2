# makefun-news-image-20261124-v2

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/axgzero/makefun-news-image-20261124-v2/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/axgzero/makefun-news-image-20261124-v2/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A single picture of Tuesday 24 November 2026's world news, drawn as
a newspaper front page: the COP31 collapse in Antalya, Jensen Huang's
return to Nvidia, Moscow's "open war" warning to Estonia, the
Democrats' biggest House majority since 1992, India's $1.62 billion
aid package for Nepal, and Tajikistan starting to leave the ICC —
plus Puigdemont's return, Denmark's "ghetto law" ruling, the Gaza
strike that killed an UNRWA worker, and the CAS ruling on Senegal's
AFCON title in the footer. `main.py` paints `entry.png` (1024×1024,
18,264 bytes) from the stories written into it, with nothing but the
Python standard library, so any run produces the same bytes. Each
story was checked against mainstream reporting in the 24 November
2026 morning editions; `SOURCES.md` has the evidence, story by story.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

And for a quick look at what the picture says:

```sh
python3 main.py --list      # print the six headline stories
python3 main.py --check     # verify entry.png matches a fresh render
```

Python 3.13, standard library only — nothing to install.

---

<sub>Entered on [make.fun](https://make.fun/?ref=cefc1nk2&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
