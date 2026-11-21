#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws, entirely in code, an open passport spread for the invented
Republic of Zaldria — a fog-bound North Atlantic island nation — as a
single PNG: a data page (portrait + machine-readable zone) on the left
and a stamps page (four stamps from neighbouring invented countries,
all dated inside the passport's validity) on the right.

Deterministic: no network, no randomness, no timestamps. Two runs
produce byte-identical output.

Usage:  python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png  (default: out/entry.png)
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- facts
COUNTRY = "REPUBLIC OF ZALDRIA"
COUNTRY_Z = "RÍKI ZALDRIA"          # Zaldrian for the same
CAPITAL = "MIRENPORT"
MOTTO = "HAV \u00b7 STEIN \u00b7 STILLLE"   # Sea \u00b7 Stone \u00b7 Silence

HOLDER = {
    "surname": "SELVIG",
    "given": "MARA",
    "nationality": "ZALDRIAN",
    "dob": "14 MAR 1994",
    "pob": "MIRENPORT",
    "sex": "F",
    "height": "172 CM",
    "eyes": "GREY-BLUE",
    "number": "ZL 482 917",
    "number_mrz": "ZL482917",
    "issued": "12 JUN 2023",
    "expiry": "12 JUN 2033",
    "authority": "PASSPORT OFFICE \u2014 MIRENPORT",
}

# Stamps: every date sits after the 12 JUN 2023 issue and before the
# 12 JUN 2033 expiry. Neighbours are invented too.
STAMPS = [
    {"country": "NORVEST", "kind": "ARRIVAL", "port": "HARBOURGATE",
     "date": "04 SEP 2023", "no": "0417", "ink": (31, 58, 120), "rot": -4,
     "icon": "anchor"},
    {"country": "DRAKKEN ISLES", "kind": "DEPARTURE", "port": "SKERRVIK",
     "date": "19 NOV 2023", "no": "0902", "ink": (122, 32, 48), "rot": 3,
     "icon": "wave"},
    {"country": "OSTERFELL", "kind": "ARRIVAL", "port": "PORT HALVAR",
     "date": "02 MAR 2024", "no": "1188", "ink": (28, 96, 62), "rot": -2,
     "icon": "fish"},
    {"country": "NORVEST", "kind": "DEPARTURE", "port": "HARBOURGATE",
     "date": "27 JUL 2024", "no": "0771", "ink": (31, 58, 120), "rot": 5,
     "icon": "lighthouse"},
]

# ---------------------------------------------------------------- canvas
W, H = 1024, 720
PAPER = (244, 239, 228)
PAPER_DARK = (232, 226, 210)
INK = (28, 32, 44)
GREY = (110, 108, 96)
NAVY = (24, 46, 88)
GOLD = (146, 112, 52)
RED = (158, 32, 32)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


SERIF = "DejaVuSerif.ttf"
SERIF_B = "DejaVuSerif-Bold.ttf"
SERIF_I = "DejaVuSerif-Italic.ttf"  # not shipped; resolved below
SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
MONO = "DejaVuSansMono.ttf"
MONO_B = "DejaVuSansMono-Bold.ttf"
LIB_DIR = "/usr/share/fonts/truetype/liberation"


def F(name, size):
    for base in (FONT_DIR, LIB_DIR):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # fallbacks for the italic faces DejaVu does not ship
    if name == SERIF_I:
        return ImageFont.truetype(
            os.path.join(LIB_DIR, "LiberationSerif-Italic.ttf"), size)
    raise FileNotFoundError(name)


# ------------------------------------------------------------------- MRZ
def mrz_check(s):
    """ICAO 9303 check digit: weights 7,3,1; A=10 .. Z=35, '<'=0."""
    total = 0
    for i, ch in enumerate(s):
        if ch.isdigit():
            v = int(ch)
        elif ch == "<":
            v = 0
        else:
            v = ord(ch) - 55
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<ZLD" + "SELVIG<<MARA"
    line1 = line1 + "<" * (44 - len(line1))
    doc = HOLDER["number_mrz"] + "<"
    dob = "940314"
    exp = "330612"
    personal = "<" * 14
    line2 = (doc + mrz_check(doc) + "ZLD" + dob + mrz_check(dob) + "F"
             + exp + mrz_check(exp) + personal + mrz_check(personal))
    line2 = line2 + mrz_check(line2)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# -------------------------------------------------------------- drawing
def draw_lighthouse(draw, cx, cy, r, colour, beams=True):
    """Small lighthouse emblem inside a circle."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=colour, width=2)
    # tower
    tw = r * 0.34
    draw.polygon([(cx - tw, cy + r * 0.72), (cx - tw * 0.7, cy - r * 0.28),
                  (cx + tw * 0.7, cy - r * 0.28), (cx + tw, cy + r * 0.72)],
                 fill=colour)
    draw.rectangle([cx - tw * 0.95, cy - r * 0.42, cx + tw * 0.95,
                    cy - r * 0.28], fill=colour)
    draw.polygon([(cx - tw, cy - r * 0.42), (cx, cy - r * 0.78),
                  (cx + tw, cy - r * 0.42)], fill=colour)
    if beams:
        draw.polygon([(cx - tw * 0.7, cy - r * 0.35), (cx - r * 0.95, cy - r * 0.62),
                      (cx - r * 0.95, cy - r * 0.18)], fill=colour)
        draw.polygon([(cx + tw * 0.7, cy - r * 0.35), (cx + r * 0.95, cy - r * 0.62),
                      (cx + r * 0.95, cy - r * 0.18)], fill=colour)
    # sea
    draw.arc([cx - r * 0.8, cy + r * 0.42, cx + r * 0.8, cy + r * 0.95],
             0, 180, fill=colour, width=2)


def guilloche(base, box, colour, alpha=16, step=9):
    """Faint wavy security lines across a page."""
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = box
    y = y0
    while y < y1:
        pts = [(x, y + 3 * math.sin((x - x0) / 26.0 + y / 40.0))
               for x in range(x0, x1, 4)]
        d.line(pts, fill=colour + (alpha,), width=1)
        y += step
    base.alpha_composite(ov)


def draw_stamp(stamp):
    """One entry/exit stamp, drawn on its own layer and rotated."""
    w, h = 200, 128
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = stamp["ink"]
    x0, y0, x1, y1 = 20, 20, 20 + w, 20 + h
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=ink, width=3)
    d.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=7,
                        outline=ink, width=1)
    cx = (x0 + x1) // 2
    d.text((cx, y0 + 12), stamp["country"], font=F(SANS_B, 15), fill=ink,
           anchor="ma")
    d.text((cx, y0 + 32), stamp["kind"], font=F(SANS_B, 12), fill=ink,
           anchor="ma")
    d.line([x0 + 22, y0 + 52, x1 - 22, y0 + 52], fill=ink, width=1)
    d.text((cx, y0 + 58), stamp["port"], font=F(SANS, 11), fill=ink,
           anchor="ma")
    d.text((cx, y0 + 76), stamp["date"], font=F(SANS_B, 16), fill=ink,
           anchor="ma")
    d.text((x1 - 10, y1 - 18), "No. " + stamp["no"], font=F(SANS, 8),
           fill=ink, anchor="ra")
    # tiny icon, bottom-left
    ix, iy = x0 + 12, y1 - 26
    if stamp["icon"] == "anchor":
        d.line([ix + 8, iy, ix + 8, iy + 18], fill=ink, width=2)
        d.arc([ix, iy, ix + 16, iy + 12], 180, 360, fill=ink, width=2)
        d.line([ix, iy + 13, ix + 16, iy + 13], fill=ink, width=2)
        d.arc([ix + 1, iy + 8, ix + 15, iy + 20], 0, 180, fill=ink, width=2)
    elif stamp["icon"] == "wave":
        for k in range(3):
            d.arc([ix, iy + k * 6, ix + 18, iy + 8 + k * 6], 180, 360,
                  fill=ink, width=2)
    elif stamp["icon"] == "fish":
        d.ellipse([ix, iy + 4, ix + 16, iy + 14], outline=ink, width=2)
        d.polygon([(ix + 15, iy + 9), (ix + 22, iy + 3), (ix + 22, iy + 15)],
                  outline=ink)
        d.point([ix + 4, iy + 8], fill=ink)
    else:  # lighthouse
        d.polygon([(ix + 5, iy + 18), (ix + 7, iy + 2), (ix + 11, iy + 2),
                   (ix + 13, iy + 18)], fill=ink)
        d.line([ix, iy + 18, ix + 18, iy + 18], fill=ink, width=2)
    return layer.rotate(stamp["rot"], resample=Image.BICUBIC, expand=False)


def round_fee_stamp():
    """Circular red 'LIGHT DUES PAID' fee stamp."""
    s = 150
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = s // 2
    d.ellipse([4, 4, s - 4, s - 4], outline=RED, width=3)
    d.ellipse([14, 14, s - 14, s - 14], outline=RED, width=1)
    d.text((c, c - 34), "LIGHT DUES", font=F(SANS_B, 13), fill=RED,
           anchor="ma")
    d.text((c, c - 16), "40 KR", font=F(SANS_B, 20), fill=RED, anchor="ma")
    d.text((c, c + 8), "PAID", font=F(SANS_B, 15), fill=RED, anchor="ma")
    d.text((c, c + 30), "MIRENPORT", font=F(SANS, 10), fill=RED, anchor="ma")
    return layer.rotate(-8, resample=Image.BICUBIC)


def field_compact(draw, x, y, label, label_z, value):
    """Label + Zaldrian label on one line (measured gap), value below."""
    draw.text((x, y), label, font=F(SANS, 9), fill=GREY)
    w = draw.textlength(label, font=F(SANS, 9))
    draw.text((x + w + 8, y), label_z, font=F(SANS, 9), fill=GREY)
    draw.text((x, y + 12), value, font=F(SERIF_B, 15), fill=INK)


def field(draw, x, y, label, label_z, value, value_size=15):
    draw.text((x, y), label, font=F(SANS, 9), fill=GREY)
    draw.text((x + 132, y), label_z, font=F(SANS, 9), fill=GREY)
    draw.text((x, y + 12), value, font=F(SERIF_B, value_size), fill=INK)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    img = Image.new("RGBA", (W, H), (46, 52, 64, 255))
    draw = ImageDraw.Draw(img)

    # desk shadow + pages
    for (px, py) in ((28, 36), (524, 36)):
        draw.rectangle([px + 5, py + 6, px + 472 + 5, py + 648 + 6],
                       fill=(20, 23, 30, 255))
    left = Image.new("RGBA", (472, 648), PAPER + (255,))
    right = Image.new("RGBA", (472, 648), PAPER + (255,))
    guilloche(left, (8, 8, 464, 640), NAVY)
    guilloche(right, (8, 8, 464, 640), NAVY)

    # ============================== LEFT PAGE: data page
    d = ImageDraw.Draw(left)
    draw_lighthouse(d, 44, 44, 22, NAVY)
    d.text((76, 22), COUNTRY, font=F(SERIF_B, 19), fill=NAVY)
    d.text((76, 46), "PASSPORT  \u00b7  VEGABR\u00c9F", font=F(SANS, 11),
           fill=GREY)
    d.line([20, 74, 452, 74], fill=GOLD, width=2)
    d.line([20, 78, 452, 78], fill=GOLD, width=1)
    d.text((452, 46), MOTTO, font=F(SERIF_I, 10), fill=GREY, anchor="ra")

    # portrait
    portrait = Image.open("assets/portrait.webp").convert("RGB")
    pw, ph = portrait.size
    target_ratio = 148 / 186
    crop_h = int(pw / target_ratio)
    y0 = 80
    portrait = portrait.crop((0, y0, pw, y0 + crop_h))
    portrait = portrait.resize((148, 186), Image.LANCZOS)
    left.paste(portrait, (24, 104))
    d.rectangle([24, 104, 24 + 148, 104 + 186], outline=NAVY, width=2)
    d.rectangle([28, 108, 24 + 144, 104 + 182], outline=NAVY, width=1)

    # holder fields, right of the photo
    fx, fy = 192, 104
    field(d, fx, fy, "SURNAME", "\u00c6TTARNAMN", HOLDER["surname"])
    field(d, fx, fy + 42, "GIVEN NAMES", "FORNAMN", HOLDER["given"])
    field(d, fx, fy + 84, "NATIONALITY", "R\u00cdKISFANG",
          HOLDER["nationality"])
    field(d, fx, fy + 126, "DATE OF BIRTH", "F\u00d8DD", HOLDER["dob"])
    field(d, fx, fy + 168, "PLACE OF BIRTH", "F\u00d8\u00d0ESTAD",
          HOLDER["pob"])
    # second row under photo: sex / height / eyes
    field_compact(d, 24, 316, "SEX", "KJ\u00d8NN", HOLDER["sex"])
    field_compact(d, 120, 316, "HEIGHT", "H\u00c6\u00d0", HOLDER["height"])
    field_compact(d, 230, 316, "EYES", "AUGU", HOLDER["eyes"])
    # signature
    d.text((452, 318), "Mara Selvig", font=F(SERIF_I, 15), fill=INK,
           anchor="ra")
    d.line([360, 340, 452, 340], fill=INK, width=1)
    d.text((452, 344), "HOLDER'S SIGNATURE / UNDIRSKRIFT",
           font=F(SANS, 8), fill=GREY, anchor="ra")

    d.line([20, 378, 452, 378], fill=GOLD, width=1)
    # document details
    d.text((24, 392), "PASSPORT No.", font=F(SANS, 9), fill=GREY)
    d.text((24, 405), HOLDER["number"], font=F(SERIF_B, 16), fill=INK)
    d.text((180, 392), "TYPE", font=F(SANS, 9), fill=GREY)
    d.text((180, 405), "P", font=F(SERIF_B, 16), fill=INK)
    d.text((240, 392), "CODE", font=F(SANS, 9), fill=GREY)
    d.text((240, 405), "ZLD", font=F(SERIF_B, 16), fill=INK)
    d.text((330, 392), "DATE OF ISSUE", font=F(SANS, 9), fill=GREY)
    d.text((330, 405), HOLDER["issued"], font=F(SERIF_B, 14), fill=INK)
    d.text((24, 448), "DATE OF EXPIRY", font=F(SANS, 9), fill=GREY)
    d.text((24, 461), HOLDER["expiry"], font=F(SERIF_B, 14), fill=INK)
    d.text((180, 448), "AUTHORITY", font=F(SANS, 9), fill=GREY)
    d.text((180, 461), HOLDER["authority"], font=F(SERIF_B, 12), fill=INK)

    # MRZ
    d.line([20, 516, 452, 516], fill=GOLD, width=1)
    line1, line2 = mrz_lines()
    d.rectangle([20, 524, 452, 566], fill=(255, 255, 255, 255))
    d.text((24, 528), line1, font=F(MONO, 14), fill=INK)
    d.text((24, 546), line2, font=F(MONO, 14), fill=INK)
    d.text((452, 578), "12", font=F(SANS, 9), fill=GREY, anchor="ra")

    # ============================== RIGHT PAGE: stamps
    d = ImageDraw.Draw(right)
    d.text((24, 22), "VISAS", font=F(SERIF_B, 19), fill=NAVY)
    d.text((24, 46), "STAMPS  \u00b7  STIMPLAR", font=F(SANS, 11), fill=GREY)
    d.line([20, 74, 452, 74], fill=GOLD, width=2)
    d.line([20, 78, 452, 78], fill=GOLD, width=1)

    positions = [(28, 96), (240, 104), (28, 258), (240, 266)]
    for stamp, (sx, sy) in zip(STAMPS, positions):
        layer = draw_stamp(stamp)
        right.alpha_composite(layer, (sx - 20, sy - 20))

    # endorsement — the telling detail of paperwork
    d.rectangle([24, 424, 448, 516], outline=NAVY, width=2)
    d.text((36, 434), "ENDORSEMENT", font=F(SANS_B, 11), fill=NAVY)
    d.text((36, 452),
           "HOLDER IS A KEEPER OF THE NORTH LIGHT.",
           font=F(SERIF_B, 13), fill=INK)
    d.text((36, 472),
           "MAY LAND AT ANY HARBOUR IN FOG.",
           font=F(SERIF, 12), fill=INK)
    d.text((36, 492),
           "NO PAID WORK. FISHING LICENCE REQUIRED AFTER 30 DAYS.",
           font=F(SANS, 10), fill=INK)

    fee = round_fee_stamp()
    right.alpha_composite(fee, (290, 495))
    d.text((24, 612),
           "This passport remains the property of the Republic of Zaldria.",
           font=F(SERIF_I, 10), fill=GREY)
    d.text((452, 636), "13", font=F(SANS, 9), fill=GREY, anchor="ra")

    # compose spread
    img.alpha_composite(left, (28, 36))
    img.alpha_composite(right, (524, 36))
    # centre gutter shadow
    gutter = Image.new("RGBA", (10, 648), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gutter)
    for i in range(10):
        gd.line([(i, 0), (i, 648)], fill=(0, 0, 0, 26 - abs(i - 5) * 4))
    img.alpha_composite(gutter, (495, 36))

    rgb = img.convert("RGB")
    rgb.save(out_path, format="PNG", optimize=True)
    print("wrote", out_path, rgb.size,
          os.path.getsize(out_path), "bytes")


if __name__ == "__main__":
    main()
