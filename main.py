# main.py — news-image-20261119 v3 (ditulis baru dari nol, PIL saja, tanpa network)
# Template: masthead + tanggal raksasa + strip angka + timeline + 3 lead + 10 kartu
# + peta titik-titik + ALSO 30 + DATE CHECK + HOW SURE ARE WE? + footer.
# Deterministik: tanpa waktu acak / tanpa random; build 2x harus byte-identical.
from PIL import Image, ImageDraw, ImageFont
import math, sys

W, H = 1024, 1024
OUT = "entry.png"

F_SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_SANS_B  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SANS    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NAVY  = (14, 42, 74)
NAVY2 = (10, 32, 58)
GOLD  = (201, 162, 39)
GOLD_BG = (245, 214, 110)
RED   = (178, 34, 34)
INK   = (22, 22, 22)
GREY  = (96, 96, 96)
PAPER = (250, 248, 240)
CREAM = (248, 244, 232)

def F(path, size):
    return ImageFont.truetype(path, size)

OVERFLOW = []
def note_overflow(msg):
    OVERFLOW.append(msg)

def grad(d, box, c1, c2):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    for i in range(h):
        t = i / h
        c = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)

def wrap(text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def block(d, x, y, text, f, fill, width, max_lines, lh=None, align="left"):
    """Draw wrapped text; FAIL LOUDLY (record overflow) if it exceeds max_lines."""
    lh = lh or int(f.size * 1.25)
    lines = wrap(text, f, width)
    if len(lines) > max_lines:
        note_overflow(f"'{text[:40]}...' needs {len(lines)} lines, max {max_lines}")
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        xx = x
        if align == "center":
            xx = x + (width - f.getlength(ln)) / 2
        d.text((xx, y + i * lh), ln, font=f, fill=fill)
    return y + len(lines) * lh

def fit_one_line(d, x, y, text, f, fill, width, candidates=None):
    """Draw text on one line; if too wide, try shorter candidates. Returns text used."""
    cands = [text] + (candidates or [])
    for c in cands:
        if f.getlength(c) <= width:
            d.text((x, y), c, font=f, fill=fill)
            return c
    note_overflow(f"one-line text too wide even after shortening: '{text[:50]}'")
    d.text((x, y), cands[-1][:60], font=f, fill=fill)
    return cands[-1]

# ---------------------------------------------------------------- data
NUMBERS = [
    ("$81.3bn", "Anthropic IPO, largest ever"),
    ("99", "GTA VI on Metacritic"),
    ("551,864", "sit the Suneung in Korea"),
    ("72,000", "evacuated from Akvan"),
    ("730,000", "Rohingya fled in 2017"),
    ("$120bn", "COP31 adaptation goal, draft"),
]

TIMELINE_FULL = ("THE DAY BY HOURS (UTC) — 00:00 GTA VI unlocks in NZ · Morning Trilateral opens · "
                 "10:00 ICJ reads judgment · 14:30 First ANT trades · Evening COP31 takes over")
TIMELINE_SHORT = ("THE DAY BY HOURS (UTC) — 00:00 GTA VI unlocks in NZ · Morning Trilateral opens · "
                  "10:00 ICJ reads judgment · 14:30 First ANT trades")
TIMELINE_SHORTER = ("THE DAY BY HOURS (UTC) — 00:00 GTA VI unlocks NZ · Morning Trilateral opens · "
                    "10:00 ICJ judgment · 14:30 First ANT trades · Evening COP31")

LEADS = [
    dict(kicker="ASIA · DIPLOMACY", headline="THREE LEADERS, ONE ROOM",
         deck="Trump, Xi and Putin meet trilaterally for the first time in Shenzhen. "
              "No breakthrough; a four-point statement; Ukraine not mentioned.",
         scene="trilateral", caption="KYLIN VILLA · SHENZHEN"),
    dict(kicker="WORLD · GAMES", headline="VICE CITY OPENS AT MIDNIGHT",
         deck="GTA VI unlocks at midnight, region by region, from New Zealand. "
              "PS5 and Xbox only — no PC, no online at launch. Reviews: 99 on Metacritic.",
         scene="gta", caption="MIDNIGHT · NEW ZEALAND"),
    dict(kicker="N. AMERICA · MARKETS", headline="THE $81 BILLION DEBUT",
         deck="Anthropic prices at $83 — above its $70–$78 range — and starts trading on the "
              "Nasdaq today as ANT. The biggest IPO on record; ~$1.5tn valuation.",
         scene="anthropic", caption="NASDAQ · NEW YORK"),
]

CARDS = [
    dict(kicker="EUROPE · LAW", headline="MYANMAR GUILTY OF GENOCIDE",
         deck="World Court rules 9–6: Myanmar committed genocide — the first state ever held.",
         scene="icj"),
    dict(kicker="WORLD · CLIMATE", headline="COP31: 21 POINTS LEFT, 48 HOURS TO GO",
         deck="Ministers take over in Antalya. Draft proposes $120bn a year for adaptation — a goal.",
         scene="cop31"),
    dict(kicker="ASIA · WEATHER", headline="AKVAN BEARS DOWN ON INDIA'S EAST COAST",
         deck="Odisha moves 72,000 to 7,900 shelters; Akvan nears landfall Friday, winds 90–100 km/h.",
         scene="akvan"),
    dict(kicker="EUROPE · WAR", headline="KERCH BRIDGE HIT A THIRD TIME IN A WEEK",
         deck="Drones strike the Crimea bridge overnight; rail halted. Third attack in four days.",
         scene="kerch"),
    dict(kicker="MIDEAST · WAR", headline="TANKS CROSS THE YELLOW LINE",
         deck="Israeli armour pushes deeper into Gaza. Ground move came Wednesday; fighting continues.",
         scene="gaza"),
    dict(kicker="ASIA · DIPLOMACY", headline="APEC ADOPTS THE 'SHENZHEN VISION'",
         deck="APEC leaders close in Shenzhen with the 2026 Declaration — a roadmap for 21 economies.",
         scene="apec"),
    dict(kicker="ASIA · EDUCATION", headline="551,864 SIT THE SUNEUNG",
         deck="South Korea's college exam runs 08:40–17:45, 1,312 sites. Flights halt for listening.",
         scene="suneung"),
    dict(kicker="EUROPE · WAR", headline="BERLIN RALLIES FOR KYIV — LONDON SENDS MISSILES",
         deck="36 nations meet in Berlin on Ukraine guarantees. Britain pledges 1,000 missiles, £260m.",
         scene="berlin"),
    dict(kicker="N. AMERICA · WEATHER", headline="FLORIDA UNDER WATER FOR A SECOND DAY",
         deck="Broward and Miami-Dade schools shut Thursday as the St. Johns River hits record level.",
         scene="florida"),
    dict(kicker="ASIA · MARKETS", headline="ALIBABA BEATS ON SALES, AI CLOUD +53%",
         deck="Revenue 271.52bn yuan, up 10%. Adjusted EPS 8.10 yuan vs 11.16 expected.",
         scene="alibaba"),
]

ALSO = [
    (14, "MIDEAST", "Houthi missile downed over Riyadh; debris damages capital."),
    (15, "WORLD", "IEA: data-centre power doubles to ~1,000 TWh by 2030."),
    (16, "AFRICA", "Amnesty: RSF drone strikes kill 37 near El Obeid, Sudan."),
    (17, "AFRICA", "Migrant boat capsizes off Senegal; ~100 aboard, dozens missing."),
    (18, "AFRICA", "Uganda landslide survivors take climate case to UN."),
    (19, "MIDEAST", "Five Israeli opposition leaders unite to oust Netanyahu."),
    (20, "ASIA", "Xi pledges $20m for APEC cooperation, new research centre."),
    (21, "ASIA", "Trump and Xi meet one-on-one: 'special relationship'."),
    (22, "ASIA", "Trump greets Putin as 'my friend' in ~40-minute talks."),
    (23, "ASIA", "India and Japan hold 2+2 defence dialogue in Tokyo."),
    (24, "OCEANIA", "Australia jobless rate jumps to 4.9%, a five-year high."),
    (25, "S. AMERICA", "Colombia unions strike nationwide over tax bill."),
    (26, "N. AMERICA", "Banxico minutes: split 3–2 cut to 6.25% (5 Nov)."),
    (27, "N. AMERICA", "Fed minutes point to more hikes; gold falls 3.18%."),
    (28, "N. AMERICA", "Dow −561 to 50,198 Wednesday; S&P falls fifth day."),
    (29, "N. AMERICA", "Nvidia falls 2.9% to $150.96 despite record revenue."),
    (30, "N. AMERICA", "UnitedHealth plunges 10.21% on Medicare audit plan."),
    (31, "N. AMERICA", "Take-Two up ~6% to $216.61 on eve of GTA VI launch."),
    (32, "WORLD", "Sensor Tower: ~17.07m GTA VI copies sold (ESTIMATE)."),
    (33, "WORLD", "Bitcoin slips below $63,000, down 15.1% in a week."),
    (34, "AFRICA", "South Africa win first Test by nine wickets; top of WTC."),
    (35, "N. AMERICA", "Utah stuns Lakers 109–97, ends nine-game streak."),
    (36, "N. AMERICA", "76ers rally from 17 down to beat Orlando 121–116."),
    (37, "S. AMERICA", "Corinthians thrash Botafogo 4–0; Kaio Cesar hat-trick."),
    (38, "N. AMERICA", "Ella Langley sweeps six CMA Awards, incl. Entertainer."),
    (39, "N. AMERICA", "Taylor Swift wins HMMA for 'I Knew It, I Knew You'."),
    (40, "EUROPE", "France's Greens open door to backing Mélenchon."),
    (41, "N. AMERICA", "NASA sets 29 Nov for next cargo launch to ISS."),
    (42, "WORLD", "mRNA vaccine protects all hamsters vs Nipah, Hendra."),
    (43, "N. AMERICA", "CAR T cells linked to gut side-effects, MD Anderson finds."),
]

DATE_CHECK = ("FIRST REPORTED WED 18 NOV, SO NOT HERE: Voyager 1 light-day · Van Gogh $190.4m · "
              "EU €45bn loan · Pew projection · Peltola win · Modi–William/Kate · Anthropic pricing "
              "($83) · Iran drone interceptions · Qeshm strikes · COP31 draft · Jeffries 251–11 · "
              "Odesa strike. ALSO NOT TODAY: Nature 'missing billion years' (4 Nov).")

HOW_SURE = ("REPORTED — named wire or official source · CLAIM — one side's account, attributed · "
            "FORECAST — expected, not yet happened.")

FOOTER = ("Every story here happened, or was first reported, on Thursday 19 November 2026. "
          "Sources: Reuters, AP, AFP, BBC, ICJ, IMD, KICE, UN, Nature, NASA, SEC EDGAR, Metacritic.")

# ---------------------------------------------------------------- map data
# Rough world landmass polygons in (lon, lat), hand-approximated.
LAND = [
    # North America
    [(-168,66),(-150,70),(-135,69),(-125,71),(-110,73),(-95,80),(-85,76),(-75,72),(-65,60),
     (-60,55),(-55,47),(-60,44),(-70,42),(-74,39),(-76,35),(-80,32),(-81,26),(-84,30),
     (-90,21),(-94,17),(-97,16),(-102,18),(-105,20),(-110,23),(-114,28),(-120,34),
     (-124,40),(-124,48),(-130,55),(-145,60),(-155,58),(-162,55),(-168,66)],
    # Greenland
    [(-58,64),(-45,68),(-32,70),(-22,76),(-30,80),(-45,81),(-58,79),(-68,76),(-62,70),(-58,64)],
    # South America
    [(-80,10),(-72,11),(-62,9),(-55,6),(-50,0),(-44,-3),(-35,-8),(-38,-15),(-40,-22),
     (-48,-27),(-52,-32),(-58,-38),(-62,-41),(-65,-45),(-68,-50),(-70,-54),(-73,-50),
     (-73,-40),(-72,-30),(-70,-20),(-77,-12),(-80,-4),(-80,10)],
    # Europe
    [(-10,36),(-9,38),(-9,43),(-2,44),(-1,46),(-4,48),(-1,49),(2,51),(4,53),(8,54),
     (8,57),(10,59),(12,56),(18,56),(21,55),(24,58),(26,59),(30,60),(28,62),(25,66),
     (22,70),(28,71),(32,70),(38,68),(42,66),(44,62),(40,58),(38,54),(36,50),(34,46),
     (30,46),(28,44),(26,42),(23,40),(22,37),(19,40),(16,38),(12,38),(8,39),(3,38),
     (0,38),(-2,37),(-6,36),(-10,36)],
    # Africa
    [(-17,15),(-17,21),(-15,27),(-10,31),(-6,34),(-2,35),(5,37),(10,37),(15,32),(20,32),
     (25,32),(30,31),(32,31),(34,28),(36,24),(38,20),(39,16),(43,12),(48,11),(51,11),
     (51,5),(48,0),(44,-4),(40,-10),(38,-15),(35,-20),(33,-25),(31,-29),(28,-33),
     (24,-34),(19,-35),(17,-32),(15,-27),(13,-22),(12,-17),(13,-12),(12,-6),(9,0),
     (9,4),(4,6),(-3,5),(-8,4),(-13,8),(-16,12),(-17,15)],
    # Asia (mainland)
    [(38,45),(40,48),(42,52),(44,56),(46,60),(44,64),(42,68),(46,70),(52,71),(58,72),
     (66,72),(72,73),(80,73),(88,75),(96,76),(104,77),(112,76),(120,73),(128,72),
     (136,71),(144,70),(152,69),(158,66),(162,62),(170,60),(178,65),(178,66),(170,62),
     (162,58),(158,52),(156,50),(150,46),(144,42),(141,39),(139,35),(136,33),(132,33),
     (130,32),(128,34),(126,38),(124,40),(121,38),(120,32),(119,28),(117,24),(112,22),
     (109,18),(106,10),(104,8),(101,7),(99,10),(97,15),(95,16),(93,20),(90,22),(88,22),
     (86,20),(83,17),(80,14),(77,8),(76,10),(74,14),(72,20),(69,22),(66,25),(62,25),
     (58,26),(55,27),(52,28),(50,29),(48,30),(46,31),(44,33),(42,36),(40,38),(38,42),(38,45)],
    # Australia
    [(113,-22),(114,-28),(115,-33),(118,-35),(124,-33),(129,-32),(132,-32),(135,-35),
     (138,-35),(140,-38),(144,-38),(147,-39),(150,-37),(153,-32),(153,-27),(151,-24),
     (149,-20),(146,-19),(143,-15),(142,-11),(140,-13),(137,-12),(135,-12),(132,-12),
     (130,-13),(127,-14),(124,-16),(121,-19),(117,-20),(113,-22)],
    # United Kingdom
    [(-5,50),(-3,51),(-1,51),(0,53),(-1,55),(-2,57),(-4,58),(-6,57),(-6,54),(-5,52),(-5,50)],
]
# Small island dots (lon, lat): Japan, Indonesia, New Zealand, Sri Lanka, Taiwan, Philippines
ISLANDS = [(139,36),(141,39),(140,38),(130,33),(95,2),(100,-2),(105,-5),(110,-7),(115,-8),
           (120,-9),(125,-8),(130,-3),(135,-4),(140,-4),(167,-45),(174,-41),(80,7),
           (121,25),(120,22),(122,14),(124,10)]

def inside(px, py, poly):
    ins = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            ins = not ins
        j = i
    return ins

def is_land(lon, lat):
    for poly in LAND:
        if inside(lon, lat, poly):
            return True
    for (ilon, ilat) in ISLANDS:
        if abs(lon - ilon) < 1.6 and abs(lat - ilat) < 1.6:
            return True
    return False

# Featured pins 1-13: (number label, lon, lat, label offset dx,dy in map px)
PINS = [
    ("1·9", 114.0, 22.5, -30, -18),   # Shenzhen: trilateral + APEC share one pin
    ("2", 174.0, -41.0, 8, -4),       # New Zealand (GTA unlock)
    ("3", -74.0, 40.7, -6, -18),      # New York (ANT)
    ("4", 4.3, 52.0, -20, -16),       # The Hague (ICJ)
    ("5", 30.7, 36.9, 12, 10),         # Antalya (COP31)
    ("6", 86.0, 19.8, 4, 12),         # Odisha coast (Akvan)
    ("7", 36.5, 45.3, 2, -20),        # Kerch
    ("8", 34.5, 31.5, -14, 10),       # Gaza
    ("10", 127.0, 37.5, 12, -14),     # Seoul (Suneung)
    ("11", 13.4, 52.5, 16, -16),      # Berlin
    ("12", -80.2, 25.8, 0, 12),       # Miami (Florida)
    ("13", 120.2, 30.3, 12, 2),       # Hangzhou (Alibaba)
]
# Grey dots for ALSO stories (lon, lat) — distinct locations only
ALSO_DOTS = [
    (47.0, 24.6), (2.3, 48.8), (30.2, 13.2), (-17.0, 14.7), (32.6, 0.3),
    (35.2, 31.8), (37.6, 55.7), (139.7, 35.7), (149.0, -35.3), (-74.0, 4.7),
    (-99.0, 19.4), (-77.0, 38.9), (28.0, -26.2), (-118.0, 34.0), (-81.0, 28.5),
    (-46.6, -23.5), (-86.8, 36.2), (-80.6, 28.4), (-95.4, 29.8), (-17.0, 32.6),
]

# ---------------------------------------------------------------- scenes
# Each scene(d, box) draws inside box=(x0,y0,x1,y1), scaled by box size.

def flag_us(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=(150, 150, 150))
    for i in range(7):
        d.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7], fill=(178, 34, 34))
    d.rectangle([x, y, x + w * 0.4, y + h * 0.55], fill=(30, 50, 110))
    for r in range(3):
        for c in range(3):
            d.ellipse([x + 2 + c * w * 0.12, y + 2 + r * h * 0.16,
                       x + 5 + c * w * 0.12, y + 5 + r * h * 0.16], fill=(255, 255, 255))

def flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    cx, cy, s = x + w * 0.22, y + h * 0.30, max(2, int(h * 0.16))
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        px, py = cx + math.cos(a) * s, cy + math.sin(a) * s
        d.polygon([(px, py - s * 0.55), (px + s * 0.18, py - s * 0.18),
                   (px + s * 0.55, py), (px + s * 0.18, py + s * 0.18),
                   (px, py + s * 0.55), (px - s * 0.18, py + s * 0.18),
                   (px - s * 0.55, py), (px - s * 0.18, py - s * 0.18)],
                  fill=(255, 222, 0))

def flag_ru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h / 3], fill=(255, 255, 255))
    d.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
    d.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))
    d.rectangle([x, y, x + w, y + h], outline=(150, 150, 150))

def scene_trilateral(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (58, 32, 86), (214, 118, 60))
    # dusk stars
    for (sx, sy) in [(0.08, 0.12), (0.22, 0.06), (0.5, 0.10), (0.68, 0.05), (0.85, 0.14), (0.95, 0.07)]:
        d.ellipse([x0 + sx * w - 1, y0 + sy * h - 1, x0 + sx * w + 1, y0 + sy * h + 1], fill=(255, 240, 200))
    # skyline silhouettes with lit windows
    base = y1 - h * 0.28
    for (bx, bw, bh) in [(0.02, 0.16, 0.42), (0.20, 0.12, 0.55), (0.34, 0.18, 0.38),
                         (0.54, 0.12, 0.48), (0.68, 0.16, 0.60), (0.86, 0.12, 0.44)]:
        d.rectangle([x0 + bx * w, base - bh * h, x0 + (bx + bw) * w, y1], fill=(18, 20, 44))
        for r in range(3):
            for c in range(int(bw * w / 9)):
                if (r * 3 + c) % 2 == 0:
                    d.rectangle([x0 + bx * w + 3 + c * 9, base - bh * h + 5 + r * 8,
                                 x0 + bx * w + 6 + c * 9, base - bh * h + 8 + r * 8],
                                fill=(255, 210, 90))
    # three flags on poles
    fw, fh = w * 0.13, h * 0.26
    for (fx, fn) in [(0.10, flag_us), (0.44, flag_cn), (0.78, flag_ru)]:
        px = x0 + fx * w
        d.line([(px, y0 + h * 0.18), (px, y1 - h * 0.28)], fill=(220, 220, 220), width=2)
        fn(d, px + 2, y0 + h * 0.18, fw, fh)
    d.rectangle([x0, y1 - h * 0.10, x1, y1], fill=(12, 14, 30))

def scene_gta(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (96, 40, 128), (255, 140, 60))
    # sun with glow
    cx, cy, r = x0 + w * 0.68, y0 + h * 0.42, h * 0.30
    for rr, col in [(r * 1.5, (255, 170, 90)), (r * 1.2, (255, 190, 110))]:
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 214, 90))
    # neon skyline
    base = y1 - h * 0.22
    for (bx, bw, bh) in [(0.02, 0.14, 0.30), (0.18, 0.10, 0.44), (0.30, 0.16, 0.34),
                         (0.48, 0.10, 0.40), (0.60, 0.14, 0.28), (0.76, 0.12, 0.38), (0.90, 0.09, 0.30)]:
        d.rectangle([x0 + bx * w, base - bh * h, x0 + (bx + bw) * w, base], fill=(24, 10, 44))
        for r in range(2):
            for c in range(int(bw * w / 8)):
                col = (255, 80, 180) if (r + c) % 2 else (60, 220, 255)
                d.rectangle([x0 + bx * w + 2 + c * 8, base - bh * h + 4 + r * 7,
                             x0 + bx * w + 5 + c * 8, base - bh * h + 7 + r * 7], fill=col)
    # palms
    for (tx, lean) in [(0.06, -1), (0.94, 1)]:
        px = x0 + tx * w
        d.line([(px, base), (px + lean * w * 0.03, base - h * 0.30)], fill=(20, 12, 30), width=3)
        for a in range(-50, 60, 25):
            ang = math.radians(a + (180 if lean < 0 else 0))
            ex = px + lean * w * 0.03 + math.cos(ang) * w * 0.06
            ey = base - h * 0.30 + abs(math.sin(ang)) * h * 0.10
            ex = max(x0 + 1, min(x1 - 1, ex))  # clamp fronds inside the band
            d.line([(px + lean * w * 0.03, base - h * 0.30), (ex, ey)], fill=(20, 12, 30), width=2)
    # water with reflections
    d.rectangle([x0, base, x1, y1], fill=(30, 20, 70))
    for i in range(4):
        yy = base + 4 + i * 5
        d.line([(x0 + w * 0.15, yy), (x0 + w * 0.85, yy)], fill=(255, 150, 90), width=1)

def scene_anthropic(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (10, 28, 58), (16, 52, 96))
    # grid
    for i in range(1, 5):
        yy = y0 + i * h / 5
        d.line([(x0, yy), (x1, yy)], fill=(40, 80, 130), width=1)
    # rising bars
    vals = [0.18, 0.26, 0.34, 0.44, 0.55, 0.68, 0.85]
    bw = w * 0.10
    base = y1 - h * 0.12
    for i, v in enumerate(vals):
        bx = x0 + w * 0.06 + i * w * 0.125
        bh = v * h * 0.75
        col = (46, 160, 90) if i < 6 else (255, 190, 60)
        d.rectangle([bx, base - bh, bx + bw, base], fill=col)
    # gold trend line
    pts = []
    for i, v in enumerate(vals):
        pts.append((x0 + w * 0.06 + i * w * 0.125 + bw / 2, base - v * h * 0.75 - 4))
    d.line(pts, fill=(255, 200, 60), width=3)
    # $83 tag
    f = F(F_SANS_B, max(11, int(h * 0.30)))
    tag = "$83"
    tw = f.getlength(tag)
    tx = x1 - tw - 8
    ty = y0 + 4
    d.rounded_rectangle([tx - 4, ty - 2, tx + tw + 4, ty + f.size + 4], radius=4, fill=(213, 0, 50))
    d.text((tx, ty), tag, font=f, fill=(255, 255, 255))

def scene_icj(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (16, 44, 88), (40, 90, 150))
    # floor
    d.rectangle([x0, y1 - h * 0.14, x1, y1], fill=(30, 30, 34))
    # courthouse columns
    for i in range(3):
        cx = x0 + w * (0.22 + i * 0.28)
        cw = w * 0.09
        d.rectangle([cx - cw / 2, y0 + h * 0.10, cx + cw / 2, y1 - h * 0.14], fill=(228, 222, 200))
        d.rectangle([cx - cw / 2 - 3, y0 + h * 0.06, cx + cw / 2 + 3, y0 + h * 0.10], fill=(240, 236, 220))
        d.rectangle([cx - cw / 2 - 3, y1 - h * 0.18, cx + cw / 2 + 3, y1 - h * 0.14], fill=(240, 236, 220))
    # scales of justice (gold, centre)
    cx, top = x0 + w * 0.50, y0 + h * 0.30
    d.line([(cx, top), (cx, y1 - h * 0.16)], fill=(255, 200, 60), width=3)
    d.line([(cx - w * 0.16, top + h * 0.06), (cx + w * 0.16, top + h * 0.06)], fill=(255, 200, 60), width=3)
    for s in (-1, 1):
        px = cx + s * w * 0.16
        d.line([(px, top + h * 0.06), (px, top + h * 0.20)], fill=(255, 200, 60), width=2)
        d.pieslice([px - w * 0.07, top + h * 0.18, px + w * 0.07, top + h * 0.30], 0, 180, fill=(255, 200, 60))
    d.ellipse([cx - 3, top - 5, cx + 3, top + 1], fill=(255, 200, 60))

def scene_cop31(d, box):
    # POLISHED v3: sun + rays, clouds, 3 layered hills, 3 turbines, birds
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (168, 214, 238), (250, 238, 196))
    # sun with rays
    sx, sy, sr = x0 + w * 0.84, y0 + h * 0.22, h * 0.16
    for k in range(8):
        a = k * math.pi / 4
        d.line([(sx + math.cos(a) * (sr + 2), sy + math.sin(a) * (sr + 2)),
                (sx + math.cos(a) * (sr + 8), sy + math.sin(a) * (sr + 8))],
               fill=(255, 200, 60), width=2)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 90))
    # clouds
    for (cx, cy, cw) in [(0.18, 0.16, 0.22), (0.48, 0.10, 0.18)]:
        for (ox, oy, r) in [(0, 0, 0.05), (0.06, 0.01, 0.06), (0.12, 0, 0.05)]:
            d.ellipse([x0 + (cx + ox) * w - r * w, y0 + (cy + oy) * h - r * h * 0.5,
                       x0 + (cx + ox) * w + r * w, y0 + (cy + oy) * h + r * h * 0.5],
                      fill=(255, 255, 255))
    # birds
    for (bx, by) in [(0.62, 0.18), (0.68, 0.14), (0.74, 0.20)]:
        d.arc([x0 + bx * w - 5, y0 + by * h - 3, x0 + bx * w, y0 + by * h + 3], 200, 340, fill=(60, 60, 60), width=1)
        d.arc([x0 + bx * w, y0 + by * h - 3, x0 + bx * w + 5, y0 + by * h + 3], 200, 340, fill=(60, 60, 60), width=1)
    # layered hills
    d.pieslice([x0 - w * 0.20, y1 - h * 0.55, x0 + w * 0.55, y1 + h * 0.25], 180, 360, fill=(120, 180, 110))
    d.pieslice([x0 + w * 0.35, y1 - h * 0.62, x0 + w * 1.15, y1 + h * 0.20], 180, 360, fill=(80, 155, 90))
    d.pieslice([x0 + w * 0.10, y1 - h * 0.40, x0 + w * 0.90, y1 + h * 0.30], 180, 360, fill=(46, 125, 70))
    # three turbines on the hills
    for (tx, th, ang) in [(0.18, 0.52, 20), (0.55, 0.62, 140), (0.85, 0.48, 260)]:
        px, py = x0 + tx * w, y1 - h * 0.08
        d.line([(px, py), (px, py - th * h)], fill=(245, 245, 245), width=2)
        hub = (px, py - th * h)
        for k in range(3):
            a = math.radians(ang + k * 120)
            ex = hub[0] + math.cos(a) * w * 0.055
            ey = hub[1] + math.sin(a) * h * 0.22
            d.line([hub, (ex, ey)], fill=(255, 255, 255), width=2)
        d.ellipse([hub[0] - 2, hub[1] - 2, hub[0] + 2, hub[1] + 2], fill=(255, 255, 255))

def scene_akvan(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (10, 90, 110), (24, 150, 158))
    # coastline (tan) bottom-right
    d.pieslice([x0 + w * 0.55, y1 - h * 0.42, x0 + w * 1.35, y1 + h * 0.30], 180, 270, fill=(222, 196, 140))
    d.rectangle([x0 + w * 0.55, y1 - h * 0.14, x1, y1], fill=(222, 196, 140))
    # cyclone spiral: concentric arcs
    cx, cy = x0 + w * 0.42, y0 + h * 0.52
    for k in range(5):
        r = h * (0.10 + k * 0.09)
        d.arc([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], 200 + k * 40, 200 + k * 40 + 220,
              fill=(255, 255, 255), width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 255, 255))
    # rain streaks
    for i in range(6):
        rx = x0 + w * (0.08 + i * 0.14)
        d.line([(rx, y0 + h * 0.08), (rx - 4, y0 + h * 0.24)], fill=(200, 230, 240), width=1)
    # landfall marker
    mx, my = x0 + w * 0.78, y1 - h * 0.30
    d.ellipse([mx - 4, my - 4, mx + 4, my + 4], fill=(213, 0, 50))
    d.ellipse([mx - 7, my - 7, mx + 7, my + 7], outline=(255, 255, 255), width=1)
    f = F(F_SANS_B, max(8, int(h * 0.20)))
    d.text((mx + 8, my - 5), "FRI", font=f, fill=(255, 255, 255))

def scene_kerch(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (58, 58, 92), (198, 118, 70))
    # water
    d.rectangle([x0, y1 - h * 0.30, x1, y1], fill=(24, 48, 84))
    for i in range(3):
        yy = y1 - h * 0.24 + i * 5
        d.line([(x0 + w * 0.1, yy), (x0 + w * 0.9, yy)], fill=(90, 130, 180), width=1)
    # bridge: left span intact, right span dropped
    deck_y = y0 + h * 0.42
    d.line([(x0, deck_y), (x0 + w * 0.55, deck_y)], fill=(220, 220, 220), width=3)
    d.line([(x0 + w * 0.55, deck_y), (x0 + w * 0.72, deck_y + h * 0.16)], fill=(220, 220, 220), width=3)
    for px in (0.12, 0.30, 0.48):
        d.line([(x0 + px * w, deck_y), (x0 + px * w, y1 - h * 0.30)], fill=(180, 180, 180), width=2)
    d.line([(x0 + w * 0.68, deck_y + h * 0.14), (x0 + w * 0.68, y1 - h * 0.30)], fill=(180, 180, 180), width=2)
    # arch
    d.arc([x0 + w * 0.30, deck_y - h * 0.30, x0 + w * 0.55, deck_y + h * 0.05], 180, 360,
          fill=(200, 200, 200), width=2)
    # smoke plumes
    for (sx, sy, sr) in [(0.62, 0.30, 0.09), (0.66, 0.22, 0.07), (0.70, 0.16, 0.05)]:
        d.ellipse([x0 + sx * w - sr * w, y0 + sy * h - sr * h, x0 + sx * w + sr * w, y0 + sy * h + sr * h],
                  fill=(120, 120, 130))
    # drone silhouette
    dx, dy = x0 + w * 0.82, y0 + h * 0.18
    d.line([(dx - 6, dy), (dx + 6, dy)], fill=(20, 20, 20), width=2)
    d.line([(dx, dy - 3), (dx, dy + 3)], fill=(20, 20, 20), width=2)

def scene_gaza(d, box):
    # POLISHED v3: brighter dusk, clear sun, crisp tank + yellow line, distant blocks
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (232, 176, 96), (146, 84, 44))
    # sun
    sx, sy, sr = x0 + w * 0.82, y0 + h * 0.26, h * 0.17
    d.ellipse([sx - sr * 1.5, sy - sr * 1.5, sx + sr * 1.5, sy + sr * 1.5], fill=(255, 220, 150))
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 238, 180))
    # distant building blocks
    for (bx, bw, bh) in [(0.58, 0.10, 0.30), (0.70, 0.08, 0.38), (0.80, 0.12, 0.26)]:
        d.rectangle([x0 + bx * w, y1 - h * 0.34 - bh * h, x0 + (bx + bw) * w, y1 - h * 0.34],
                    fill=(110, 70, 40))
    # ground
    d.rectangle([x0, y1 - h * 0.34, x1, y1], fill=(96, 62, 34))
    # Yellow Line across the ground band
    ly = y1 - h * 0.20
    d.line([(x0, ly), (x1, ly)], fill=(255, 214, 40), width=3)
    # tank silhouette (dark olive), left of centre
    tx, ty = x0 + w * 0.16, y1 - h * 0.34
    d.rectangle([tx, ty - h * 0.13, tx + w * 0.30, ty], fill=(52, 52, 38))
    d.rectangle([tx + w * 0.07, ty - h * 0.22, tx + w * 0.20, ty - h * 0.13], fill=(52, 52, 38))
    d.line([(tx + w * 0.20, ty - h * 0.19), (tx + w * 0.34, ty - h * 0.19)], fill=(52, 52, 38), width=3)
    for i in range(4):
        d.ellipse([tx + 2 + i * 9, ty - 4, tx + 9 + i * 9, ty + 3], fill=(30, 30, 22))
    # smoke columns
    for (sx2, sy2, sr2) in [(0.60, 0.30, 0.08), (0.64, 0.22, 0.06), (0.68, 0.15, 0.045)]:
        d.ellipse([x0 + sx2 * w - sr2 * w, y0 + sy2 * h - sr2 * h,
                   x0 + sx2 * w + sr2 * w, y0 + sy2 * h + sr2 * h], fill=(90, 80, 70))

def scene_apec(d, box):
    # POLISHED v3: glowing globe, taller tower, flag row, stars
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (14, 36, 76), (30, 74, 140))
    # stars
    for (sx, sy) in [(0.06, 0.10), (0.16, 0.06), (0.30, 0.12), (0.55, 0.08), (0.90, 0.10), (0.96, 0.05)]:
        d.ellipse([x0 + sx * w - 1, y0 + sy * h - 1, x0 + sx * w + 1, y0 + sy * h + 1], fill=(255, 255, 255))
    # globe with glow
    cx, cy, r = x0 + w * 0.30, y0 + h * 0.48, h * 0.34
    d.ellipse([cx - r * 1.25, cy - r * 1.25, cx + r * 1.25, cy + r * 1.25], fill=(50, 110, 190))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 140, 210))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 230, 255), width=2)
    for k in (-2, -1, 0, 1, 2):
        d.ellipse([cx - r * 0.45 + k * r * 0.22, cy - r, cx + r * 0.45 + k * r * 0.22, cy + r],
                  outline=(180, 215, 245), width=1)
    for k in (-1, 0, 1):
        d.arc([cx - r, cy - r + k * r * 0.55, cx + r, cy + r + k * r * 0.55], 0, 180,
              fill=(180, 215, 245), width=1)
    # Shenzhen tower silhouette
    tx = x0 + w * 0.72
    d.polygon([(tx - w * 0.05, y1), (tx - w * 0.02, y0 + h * 0.12), (tx + w * 0.02, y0 + h * 0.12),
               (tx + w * 0.05, y1)], fill=(12, 18, 40))
    d.line([(tx, y0 + h * 0.12), (tx, y0 + h * 0.02)], fill=(255, 220, 100), width=2)
    for i in range(4):
        yy = y0 + h * (0.25 + i * 0.16)
        d.line([(tx - w * 0.035, yy), (tx + w * 0.035, yy)], fill=(255, 210, 90), width=1)
    # flag row at bottom
    for i, col in enumerate([(178, 34, 34), (255, 255, 255), (0, 90, 160), (220, 41, 16), (255, 200, 60)]):
        fx = x0 + w * (0.62 + i * 0.07)
        d.line([(fx, y1 - h * 0.18), (fx, y1 - h * 0.02)], fill=(220, 220, 220), width=1)
        d.rectangle([fx + 1, y1 - h * 0.18, fx + w * 0.05, y1 - h * 0.10], fill=col)

def scene_suneung(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (250, 240, 214), (236, 214, 170))
    # clock face (08:40 — hour hand 260 deg, minute hand 240 deg)
    cx, cy, r = x0 + w * 0.30, y0 + h * 0.50, h * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=(30, 30, 30), width=2)
    for k in range(12):
        a = math.radians(k * 30)
        d.line([(cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85),
                (cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95)], fill=(30, 30, 30), width=1)
    ha = math.radians(260 - 90)
    d.line([(cx, cy), (cx + math.cos(ha) * r * 0.55, cy + math.sin(ha) * r * 0.55)], fill=(30, 30, 30), width=3)
    ma = math.radians(240 - 90)
    d.line([(cx, cy), (cx + math.cos(ma) * r * 0.80, cy + math.sin(ma) * r * 0.80)], fill=(178, 34, 34), width=2)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(30, 30, 30))
    # pencil diagonal
    px, py = x0 + w * 0.62, y0 + h * 0.30
    d.line([(px, py), (px + w * 0.30, py + h * 0.45)], fill=(255, 190, 40), width=5)
    d.line([(px + w * 0.30, py + h * 0.45), (px + w * 0.34, py + h * 0.52)], fill=(40, 40, 40), width=3)
    # taegeuk
    tx, ty, tr = x0 + w * 0.86, y0 + h * 0.24, h * 0.13
    d.pieslice([tx - tr, ty - tr, tx + tr, ty + tr], 90, 270, fill=(213, 0, 50))
    d.pieslice([tx - tr, ty - tr, tx + tr, ty + tr], 270, 90, fill=(0, 70, 160))
    d.ellipse([tx - tr, ty - tr / 2, tx, ty + tr / 2], fill=(213, 0, 50))
    d.ellipse([tx, ty - tr / 2, tx + tr, ty + tr / 2], fill=(0, 70, 160))

def scene_berlin(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (72, 92, 142), (222, 182, 122))
    # EU stars arc
    for k in range(7):
        a = math.radians(200 + k * 20)
        sx = x0 + w * 0.30 + math.cos(a) * w * 0.22
        sy = y0 + h * 0.42 + math.sin(a) * h * 0.30
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 214, 60))
    # Brandenburg Gate
    gx, gy = x0 + w * 0.10, y1 - h * 0.10
    gw, gh = w * 0.42, h * 0.55
    d.rectangle([gx, gy - gh, gx + gw, gy - gh + h * 0.08], fill=(228, 222, 200))
    for i in range(4):
        cx = gx + gw * (0.12 + i * 0.25)
        d.rectangle([cx - 2, gy - gh + h * 0.08, cx + 2, gy], fill=(228, 222, 200))
    # quadriga silhouette on top
    d.rectangle([gx + gw * 0.40, gy - gh - h * 0.08, gx + gw * 0.60, gy - gh], fill=(60, 60, 60))
    # rising missile with trail
    mx, my = x0 + w * 0.82, y1 - h * 0.30
    d.line([(mx + 10, my + h * 0.28), (mx, my)], fill=(255, 255, 255), width=2)
    d.line([(mx, my), (mx - 6, my - h * 0.28)], fill=(240, 240, 240), width=3)
    d.polygon([(mx - 9, my - h * 0.28), (mx - 3, my - h * 0.28), (mx - 6, my - h * 0.38)], fill=(240, 240, 240))
    d.ellipse([mx - 10, my - 2, mx - 2, my + 6], fill=(255, 160, 40))

def scene_florida(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (62, 74, 96), (128, 140, 158))
    # storm clouds
    for (cx, cy, cw) in [(0.20, 0.14, 0.30), (0.55, 0.08, 0.34), (0.85, 0.16, 0.26)]:
        for (ox, oy, r) in [(0, 0, 0.07), (0.08, 0.02, 0.08), (0.16, 0, 0.07)]:
            d.ellipse([x0 + (cx + ox) * w - r * w, y0 + (cy + oy) * h - r * h * 0.5,
                       x0 + (cx + ox) * w + r * w, y0 + (cy + oy) * h + r * h * 0.5],
                      fill=(48, 56, 72))
    # rain streaks
    for i in range(10):
        rx = x0 + w * (0.04 + i * 0.10)
        d.line([(rx, y0 + h * 0.30), (rx - 5, y0 + h * 0.52)], fill=(190, 205, 220), width=1)
    # flooded road
    d.rectangle([x0, y1 - h * 0.34, x1, y1], fill=(36, 52, 74))
    for i in range(3):
        yy = y1 - h * 0.28 + i * 6
        d.line([(x0 + w * 0.08, yy), (x0 + w * 0.55, yy)], fill=(150, 175, 200), width=1)
    # bent palm
    px = x0 + w * 0.80
    d.line([(px, y1 - h * 0.34), (px + w * 0.04, y1 - h * 0.62)], fill=(30, 40, 26), width=3)
    for a in range(-40, 70, 28):
        ang = math.radians(a)
        ex = px + w * 0.04 + math.cos(ang) * w * 0.07
        ey = y1 - h * 0.62 + abs(math.sin(ang)) * h * 0.08
        d.line([(px + w * 0.04, y1 - h * 0.62), (ex, ey)], fill=(30, 40, 26), width=2)

def scene_alibaba(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad(d, box, (238, 118, 40), (250, 182, 82))
    # cloud with AI
    cx, cy = x0 + w * 0.34, y0 + h * 0.42
    for (ox, oy, r) in [(-0.10, 0.02, 0.10), (0.0, -0.04, 0.13), (0.11, 0.02, 0.10)]:
        d.ellipse([cx + ox * w - r * w, cy + oy * h - r * h, cx + ox * w + r * w, cy + oy * h + r * h],
                  fill=(255, 255, 255))
    f = F(F_SANS_B, max(11, int(h * 0.30)))
    d.text((cx - f.getlength("AI") / 2, cy - f.size / 2 - 1), "AI", font=f, fill=(14, 42, 74))
    # green arrow up
    ax, ay = x0 + w * 0.68, y1 - h * 0.20
    d.line([(ax, ay), (ax + w * 0.16, ay - h * 0.45)], fill=(20, 140, 70), width=4)
    d.polygon([(ax + w * 0.16, ay - h * 0.45), (ax + w * 0.11, ay - h * 0.38),
               (ax + w * 0.21, ay - h * 0.38)], fill=(20, 140, 70))
    # mini bars + 53% tag
    for i, v in enumerate([0.25, 0.45, 0.70]):
        bx = x0 + w * (0.60 + i * 0.09)
        d.rectangle([bx, y1 - h * 0.10 - v * h * 0.28, bx + w * 0.05, y1 - h * 0.10], fill=(255, 255, 255))
    f2 = F(F_SANS_B, max(9, int(h * 0.22)))
    d.text((x0 + w * 0.86, y0 + h * 0.08), "+53%", font=f2, fill=(255, 255, 255))

SCENES = {
    "trilateral": scene_trilateral, "gta": scene_gta, "anthropic": scene_anthropic,
    "icj": scene_icj, "cop31": scene_cop31, "akvan": scene_akvan, "kerch": scene_kerch,
    "gaza": scene_gaza, "apec": scene_apec, "suneung": scene_suneung,
    "berlin": scene_berlin, "florida": scene_florida, "alibaba": scene_alibaba,
}

# ---------------------------------------------------------------- map
def draw_map(d, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cols, rows = 78, 24
    def to_px(lon, lat):
        return (x0 + (lon + 170) / 360 * w, y0 + (78 - lat) / 140 * h)
    # land dots
    for r in range(rows):
        for c in range(cols):
            lon = -170 + (c + 0.5) / cols * 360
            lat = 78 - (r + 0.5) / rows * 140
            if is_land(lon, lat):
                px, py = to_px(lon, lat)
                d.ellipse([px - 1.6, py - 1.6, px + 1.6, py + 1.6], fill=(90, 110, 140))
    # ALSO grey dots
    for (lon, lat) in ALSO_DOTS:
        px, py = to_px(lon, lat)
        d.ellipse([px - 1.8, py - 1.8, px + 1.8, py + 1.8], fill=(150, 150, 150))
    # featured pins with leader-line labels
    fnum = F(F_SANS_B, 8)
    for (label, lon, lat, dx, dy) in PINS:
        px, py = to_px(lon, lat)
        lx, ly = px + dx, py + dy
        d.line([(px, py), (lx, ly)], fill=RED, width=1)
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED)
        r = 7 if len(label) <= 2 else 9
        d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=(255, 255, 255), outline=RED, width=1)
        tw = fnum.getlength(label)
        d.text((lx - tw / 2, ly - 4), label, font=fnum, fill=RED)

# ---------------------------------------------------------------- build
def main():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    M = 16                      # margin
    CW = W - 2 * M              # content width 992

    # --- masthead (0-50)
    d.rectangle([0, 0, W, 50], fill=NAVY)
    f_mast = F(F_SERIF_B, 36)
    t = "THE WORLD TODAY"
    d.text(((W - f_mast.getlength(t)) / 2, 6), t, font=f_mast, fill=(255, 255, 255))

    # --- date row (50-90)
    f_date = F(F_SANS_B, 32)
    d.text((M, 56), "THURSDAY 19 NOVEMBER 2026", font=f_date, fill=NAVY)
    f_badge = F(F_SANS_B, 13)
    badge = "43 STORIES · 6 CONTINENTS · ONE DAY"
    d.text((W - M - f_badge.getlength(badge), 66), badge, font=f_badge, fill=(176, 132, 20))

    # --- gold rule
    d.rectangle([0, 90, W, 93], fill=GOLD)

    # --- numbers strip (93-133)
    f_num = F(F_SANS_B, 23)
    f_lab = F(F_SANS, 9)
    cell = CW / 6
    for i, (num, lab) in enumerate(NUMBERS):
        cx = M + i * cell
        d.text((cx + 4, 98), num, font=f_num, fill=NAVY)
        d.text((cx + 4, 124), lab, font=f_lab, fill=GREY)
        if i:
            d.line([(cx, 98), (cx, 132)], fill=(210, 210, 210), width=1)

    # --- timeline strip (133-150), 11.5px, text shortened until it fits
    d.rectangle([0, 133, W, 150], fill=GOLD_BG)
    f_tl = F(F_SANS_B, 11.5)
    used = None
    for cand in (TIMELINE_FULL, TIMELINE_SHORT, TIMELINE_SHORTER):
        if f_tl.getlength(cand) <= CW - 8:
            used = cand
            break
    if used is None:
        note_overflow("timeline does not fit even shortened")
        used = TIMELINE_SHORTER
    d.text((M, 137), used, font=f_tl, fill=NAVY)

    # --- leads (153-361)
    col_w = (CW - 16) / 3
    f_kick = F(F_SANS_B, 9)
    f_hlead = F(F_SANS_B, 25)
    f_dlead = F(F_SANS, 12)
    for i, L in enumerate(LEADS):
        x = M + i * (col_w + 8)
        # scene band 153-237
        SCENES[L["scene"]](d, (int(x), 153, int(x + col_w), 237))
        # location caption chip inside band, bottom-left
        f_cap = F(F_SANS_B, 9)
        cap = L["caption"]
        cw = f_cap.getlength(cap) + 10
        d.rectangle([x + 4, 237 - 16, x + 4 + cw, 237 - 4], fill=(10, 20, 36))
        d.text((x + 9, 237 - 14), cap, font=f_cap, fill=(255, 255, 255))
        # kicker / headline / deck
        d.text((x, 241), L["kicker"], font=f_kick, fill=RED)
        block(d, x, 255, L["headline"], f_hlead, INK, col_w, 2, lh=27)
        block(d, x, 311, L["deck"], f_dlead, INK, col_w, 4, lh=14)

    # --- cards, 2 rows x 5 cols
    ccol = (CW - 4 * 8) / 5
    f_kick2 = F(F_SANS_B, 9)
    f_hcard = F(F_SANS_B, 15)
    f_dcard = F(F_SANS, 11)
    for row in range(2):
        y_scene = 365 + row * 154
        for col in range(5):
            C = CARDS[row * 5 + col]
            x = M + col * (ccol + 8)
            SCENES[C["scene"]](d, (int(x), y_scene, int(x + ccol), y_scene + 40))
            d.text((x, y_scene + 43), C["kicker"], font=f_kick2, fill=RED)
            block(d, x, y_scene + 55, C["headline"], f_hcard, INK, ccol, 3, lh=18)
            block(d, x, y_scene + 111, C["deck"], f_dcard, INK, ccol, 3, lh=13)

    # --- map zone (673-797)
    y_map = 673
    f_mapt = F(F_SANS_B, 12)
    d.text((M, y_map), "WHERE IT HAPPENED", font=f_mapt, fill=NAVY)
    f_mapl = F(F_SANS, 9)
    d.text((M + 150, y_map + 2), "red pins 1–13 featured, grey dots ALSO", font=f_mapl, fill=GREY)
    draw_map(d, (M, y_map + 16, M + 540, y_map + 124))
    # DATE CHECK box (right)
    bx0, bx1 = M + 556, W - M
    f_dct = F(F_SANS_B, 10)
    f_dcb = F(F_SANS, 9)
    d.rectangle([bx0, y_map + 16, bx1, y_map + 82], outline=RED, width=1)
    d.text((bx0 + 6, y_map + 19), "DATE CHECK — WHAT WE LEFT OUT ON PURPOSE", font=f_dct, fill=RED)
    block(d, bx0 + 6, y_map + 33, DATE_CHECK, f_dcb, INK, bx1 - bx0 - 12, 4, lh=11)
    # HOW SURE ARE WE? box (right, below)
    d.rectangle([bx0, y_map + 86, bx1, y_map + 124], outline=NAVY, width=1)
    d.text((bx0 + 6, y_map + 89), "HOW SURE ARE WE?", font=f_dct, fill=NAVY)
    block(d, bx0 + 6, y_map + 103, HOW_SURE, f_dcb, INK, bx1 - bx0 - 12, 2, lh=11)

    # --- ALSO (801-996)
    y_also = 801
    f_at = F(F_SANS_B, 13)
    d.text((M, y_also), "ALSO ON THURSDAY — 30 MORE STORIES", font=f_at, fill=NAVY)
    d.rectangle([0, y_also + 17, W, y_also + 19], fill=GOLD)
    f_anum = F(F_SANS_B, 11)
    f_atag = F(F_SANS_B, 11)
    f_atext = F(F_SANS, 11)
    col2_x = M + CW / 2 + 8
    col_w2 = CW / 2 - 8
    for idx, (num, tag, text) in enumerate(ALSO):
        col = 0 if idx < 15 else 1
        r = idx % 15
        x = M if col == 0 else col2_x
        y = y_also + 22 + r * 12
        d.text((x, y), f"{num}", font=f_anum, fill=RED)
        d.text((x + 26, y), tag, font=f_atag, fill=NAVY)
        tx = x + 26 + f_atag.getlength(tag) + 6
        line = text
        if f_atext.getlength(line) > (x + col_w2 - tx):
            note_overflow(f"ALSO #{num} too wide: '{line}'")
        d.text((tx, y), line, font=f_atext, fill=INK)

    # --- footer
    f_foot = F(F_SANS, 9)
    fw = f_foot.getlength(FOOTER)
    d.text(((W - fw) / 2, 1002), FOOTER, font=f_foot, fill=GREY)

    # --- checks
    assert len(LEADS) == 3 and len(CARDS) == 10 and len(ALSO) == 30, "story count wrong"
    if OVERFLOW:
        print("OVERFLOW:", file=sys.stderr)
        for o in OVERFLOW:
            print(" -", o, file=sys.stderr)
        sys.exit(1)
    im.save(OUT)
    print(f"wrote {OUT} {W}x{H}")
    print(f"checks: 0 overflow; stories: 3 lead + 10 cards + 30 ALSO = 43")

if __name__ == "__main__":
    main()
