# makefun-news-image-20261124-v2

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/axgzero/makefun-news-image-20261124-v2/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/axgzero/makefun-news-image-20261124-v2/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

One image summing up the world news of Tuesday 24 November 2026: COP31 collapses in Antalya, Nvidia brings back Jensen Huang as CEO, Moscow warns Estonia of "open war" over its border closure, the Democrats take their biggest House majority since 1992, Nepal gets a $1.62 billion aid package from India, and Tajikistan starts leaving the ICC — with Puigdemont's return, Denmark's "ghetto law" ruling, the Gaza strike that killed an UNRWA worker, and the CAS ruling on Senegal's AFCON title in the footer. `main.py` draws `entry.png` (1024×1024, 18,264 bytes) from the stories it encodes, using only the Python standard library, so every run produces identical bytes. Every story was checked against mainstream reporting in the 24 November 2026 morning editions — see `SOURCES.md` for the story-by-story breakdown and sources.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Other useful commands:

```sh
python3 main.py --list      # print the six headline stories
python3 main.py --check     # verify entry.png matches a fresh render
```

No dependencies beyond Python 3.13 (standard library only).

---

<sub>Entered on [make.fun](https://make.fun/?ref=cefc1nk2&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
