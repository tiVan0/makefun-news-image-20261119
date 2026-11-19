# Thursday 19 November 2026 in 43 stories

![news-image-20261119](https://make.fun/badge/news-image-20261119.svg)
![rank](https://make.fun/badge/news-image-20261119/tiVan0/makefun-news-image-20261119/rank.svg)
![reward](https://make.fun/badge/news-image-20261119/tiVan0/makefun-news-image-20261119/reward.svg)

A one-page newspaper front page for Thursday 19 November 2026: 3 lead
stories (the first Trump–Xi–Putin trilateral in Shenzhen, GTA VI's midnight
unlock, Anthropic's $81.3 billion IPO debut), 10 cards, 30 more stories, a
dotted world map with every story pinned, and a BY THE NUMBERS strip. 43
stories, 6 continents, one day.

## Run

```sh
python3 main.py
```

Writes `entry.png` (1024 x 1024, under 1 MiB). Deterministic: every run
produces byte-identical output.

## How it is drawn

Everything is drawn in code with PIL only: the scenes are compositions of
shapes and gradients (trilateral skyline, GTA sunset, IPO chart, court
scales, wind turbines, cyclone spiral, broken bridge, tank, globe, exam
clock, Brandenburg Gate, flood street, cloud), the world map is a
hand-authored dotted land grid, and the text uses embedded bitmap fonts
(DejaVu, generated from the font tables). No photos, no AI images, no
network access at render time. Python 3 standard library + Pillow only.

## Sources

Every story was reported on Thursday 19 November 2026 or in the overnight
bulletins that opened the day. Disputed claims are attributed: the ICJ
ruling 9–6; Akvan evacuations to the Odisha government (72,000); GTA VI
pre-orders as a Sensor Tower estimate. Sources: AP, Reuters, AFP, BBC,
ICJ, IMD, KICE, UN, Nature, NASA, SEC EDGAR, Metacritic and others.
