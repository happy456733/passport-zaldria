#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws, entirely in code, an open passport spread for the invented
Republic of Zaldria — a fog-bound North Atlantic island nation — as a
single PNG: a data page (portrait + machine-readable zone) on the left
and a stamps page (four stamps from neighbouring invented countries,
all dated inside the passport's validity) on the right.

STDLIB ONLY. The grader's pinned python3.13 image ships no third-party
packages (no Pillow, no fonts on disk), runs the entry as
`python3 -P -s /bot/main.py` with the repo read-only and the working
directory outside the repo, so this file:
  * imports nothing beyond the standard library,
  * rasterises with its own tiny canvas (RGBA bytearray) and its own
    PNG encoder (zlib) and decoder,
  * draws text with a hand-built stroke font (no font files needed),
  * resolves the portrait asset relative to this file, never the cwd,
  * writes only to $MAKEFUN_OUTPUT_DIR (default: out/entry.png).

Deterministic: no network, no randomness, no timestamps. Two runs
produce byte-identical output.

Usage:  python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png  (default: out/entry.png)
"""

import math
import os
import struct
import zlib

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _rgba(color):
    if len(color) == 3:
        return (color[0], color[1], color[2], 255)
    return color


# ------------------------------------------------------------ PNG codec
def png_decode(path):
    """Decode an 8-bit, non-interlaced PNG (colour types 0/2/3/4/6)
    to (width, height, RGBA bytearray). Stdlib only."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: " + path)
    pos = 8
    idat = bytearray()
    plte = None
    trns = None
    width = height = None
    bitdepth = ctype = interlace = None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            width, height, bitdepth, ctype, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk)
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"PLTE":
            plte = chunk
        elif typ == b"tRNS":
            trns = chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bitdepth != 8 or interlace != 0:
        raise ValueError("unsupported PNG (bitdepth/interlace): " + path)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        f = raw[p]
        p += 1
        row = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:  # Sub
            for i in range(channels, stride):
                row[i] = (row[i] + row[i - channels]) & 0xFF
        elif f == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif f == 3:  # Average
            for i in range(stride):
                a = row[i - channels] if i >= channels else 0
                row[i] = (row[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:  # Paeth
            for i in range(stride):
                a = row[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        elif f != 0:
            raise ValueError("bad PNG filter %d" % f)
        o = y * width * 4
        if ctype == 2:
            for x in range(width):
                i = x * 3
                out[o:o + 4] = bytes((row[i], row[i + 1], row[i + 2], 255))
                o += 4
        elif ctype == 6:
            out[y * width * 4:(y + 1) * width * 4] = row
        elif ctype == 0:
            for x in range(width):
                g = row[x]
                out[o:o + 4] = bytes((g, g, g, 255))
                o += 4
        elif ctype == 4:
            for x in range(width):
                g, a = row[x * 2], row[x * 2 + 1]
                out[o:o + 4] = bytes((g, g, g, a))
                o += 4
        elif ctype == 3:
            for x in range(width):
                idx = row[x] * 3
                r, g, b = plte[idx], plte[idx + 1], plte[idx + 2]
                a = trns[idx] if trns and idx < len(trns) else 255
                out[o:o + 4] = bytes((r, g, b, a))
                o += 4
        prev = row
    return width, height, out


def png_encode_rgb(path, w, h, rgb):
    """Write RGB bytes (3 bytes/px, row-major) as a PNG. Filter 0 rows,
    zlib level 9 — the spread is mostly flat paper, so this stays well
    under the 1 MiB cap."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, payload):
        out = struct.pack(">I", len(payload)) + typ + payload
        return out + struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ------------------------------------------------------------ stroke font
# Hand-built single-stroke sans font. Each glyph is a list of strokes;
# each stroke a polyline of (x, y) points on a 10-wide grid, cap height
# 14 (y 0..14, baseline 14, descenders to 18). One advance (10 units)
# for every glyph, so text is naturally monospace-ish and measurable.
GLYPHS = {
    "A": (((1, 14), (5, 0), (9, 14)), ((3, 9), (7, 9))),
    "B": (((1, 0), (1, 14)), ((1, 0), (6, 0), (8, 2), (8, 5), (6, 7), (1, 7)),
          ((1, 7), (6, 7), (8, 9), (8, 12), (6, 14), (1, 14))),
    "C": (((9, 3), (7, 0), (3, 0), (1, 3), (1, 11), (3, 14), (7, 14), (9, 11)),),
    "D": (((1, 0), (1, 14)), ((1, 0), (6, 0), (9, 3), (9, 11), (6, 14), (1, 14))),
    "E": (((1, 0), (1, 14)), ((1, 0), (8, 0)), ((1, 7), (6, 7)), ((1, 14), (8, 14))),
    "F": (((1, 0), (1, 14)), ((1, 0), (8, 0)), ((1, 7), (6, 7))),
    "G": (((9, 3), (7, 0), (3, 0), (1, 3), (1, 11), (3, 14), (7, 14), (9, 11),
           (9, 7), (5, 7)),),
    "H": (((1, 0), (1, 14)), ((9, 0), (9, 14)), ((1, 7), (9, 7))),
    "I": (((5, 0), (5, 14)), ((2, 0), (8, 0)), ((2, 14), (8, 14))),
    "J": (((8, 0), (8, 11), (6, 14), (3, 14), (1, 12)),),
    "K": (((1, 0), (1, 14)), ((9, 0), (2, 7)), ((4, 5), (9, 14))),
    "L": (((1, 0), (1, 14)), ((1, 14), (8, 14))),
    "M": (((1, 14), (1, 0), (5, 8), (9, 0), (9, 14)),),
    "N": (((1, 14), (1, 0), (9, 14), (9, 0)),),
    "O": (((3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11), (1, 3),
           (3, 0)),),
    "P": (((1, 0), (1, 14)), ((1, 0), (6, 0), (8, 2), (8, 5), (6, 7), (1, 7))),
    "Q": (((3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11), (1, 3),
           (3, 0)), ((6, 10), (9, 14))),
    "R": (((1, 0), (1, 14)), ((1, 0), (6, 0), (8, 2), (8, 5), (6, 7), (1, 7)),
          ((5, 7), (9, 14))),
    "S": (((8, 2), (6, 0), (3, 0), (1, 2), (1, 5), (3, 7), (7, 7), (9, 9),
           (9, 12), (7, 14), (4, 14), (2, 12)),),
    "T": (((1, 0), (9, 0)), ((5, 0), (5, 14))),
    "U": (((1, 0), (1, 11), (3, 14), (7, 14), (9, 11), (9, 0)),),
    "V": (((1, 0), (5, 14), (9, 0)),),
    "W": (((1, 0), (2, 14), (5, 7), (8, 14), (9, 0)),),
    "X": (((1, 0), (9, 14)), ((9, 0), (1, 14))),
    "Y": (((1, 0), (5, 7), (9, 0)), ((5, 7), (5, 14))),
    "Z": (((1, 0), (9, 0), (1, 14), (9, 14)),),
    "Æ": (((1, 14), (4, 0), (7, 14)), ((3, 8), (6, 8)), ((7, 0), (7, 14)),
          ((7, 0), (9, 0)), ((7, 14), (9, 14))),
    "Ø": (((3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11), (1, 3),
           (3, 0)), ((2, 12), (8, 2))),
    "Ð": (((1, 0), (1, 14)), ((1, 0), (6, 0), (9, 3), (9, 11), (6, 14), (1, 14)),
          ((0, 7), (10, 7))),
    "É": (((1, 0), (1, 14)), ((1, 0), (8, 0)), ((1, 7), (6, 7)), ((1, 14), (8, 14)),
          ((7, -4), (9, -1))),
    "Í": (((5, 0), (5, 14)), ((2, 0), (8, 0)), ((2, 14), (8, 14)),
          ((6, -4), (8, -1))),
    "a": (((3, 5), (7, 5), (9, 7), (9, 12), (7, 14), (3, 14), (1, 12), (1, 7),
           (3, 5)), ((9, 5), (9, 14))),
    "b": (((1, 0), (1, 14)), ((1, 7), (5, 5), (8, 7), (8, 12), (5, 14), (1, 14))),
    "c": (((8, 7), (6, 5), (3, 5), (1, 7), (1, 12), (3, 14), (6, 14), (8, 12)),),
    "d": (((9, 0), (9, 14)), ((9, 7), (6, 5), (3, 5), (1, 7), (1, 12), (3, 14),
           (6, 14), (9, 12))),
    "e": (((8, 6), (6, 5), (3, 5), (1, 7), (1, 12), (3, 14), (7, 14), (9, 11)),
          ((1, 9), (8, 9))),
    "f": (((7, 2), (7, 14)), ((7, 2), (5, 0), (3, 1)), ((3, 6), (8, 6))),
    "g": (((3, 5), (7, 5), (9, 7), (9, 12), (7, 14), (3, 14), (1, 12), (1, 7),
           (3, 5)), ((9, 5), (9, 17), (6, 18), (3, 18))),
    "h": (((1, 0), (1, 14)), ((1, 9), (4, 5), (7, 5), (9, 7), (9, 14))),
    "i": (((5, 5), (5, 14)), ((5, 1), (5, 2))),
    "j": (((7, 5), (7, 17), (5, 18), (3, 18)), ((7, 1), (7, 2))),
    "k": (((1, 0), (1, 14)), ((8, 5), (2, 9)), ((4, 8), (8, 14))),
    "l": (((5, 0), (5, 14)),),
    "m": (((1, 5), (1, 14)), ((1, 9), (3, 5), (5, 7), (5, 14)),
          ((5, 9), (7, 5), (9, 7), (9, 14))),
    "n": (((1, 5), (1, 14)), ((1, 9), (4, 5), (7, 5), (9, 7), (9, 14))),
    "o": (((3, 5), (7, 5), (9, 7), (9, 12), (7, 14), (3, 14), (1, 12), (1, 7),
           (3, 5)),),
    "p": (((1, 5), (1, 18)), ((1, 7), (4, 5), (7, 5), (9, 7), (9, 12), (7, 14),
           (4, 14), (1, 12))),
    "q": (((9, 5), (9, 18)), ((9, 7), (6, 5), (3, 5), (1, 7), (1, 12), (3, 14),
           (6, 14), (9, 12))),
    "r": (((1, 5), (1, 14)), ((1, 9), (4, 5), (7, 5), (8, 7))),
    "s": (((8, 7), (6, 5), (3, 5), (1, 7), (1, 9), (3, 11), (7, 11), (9, 12),
           (9, 13), (7, 14), (4, 14), (2, 13)),),
    "t": (((5, 1), (5, 14)), ((2, 6), (8, 6)), ((5, 14), (7, 14), (8, 13))),
    "u": (((1, 5), (1, 12), (3, 14), (7, 14), (9, 12), (9, 5)),),
    "v": (((1, 5), (5, 14), (9, 5)),),
    "w": (((1, 5), (2, 14), (5, 9), (8, 14), (9, 5)),),
    "x": (((1, 5), (9, 14)), ((9, 5), (1, 14))),
    "y": (((1, 5), (5, 13), (9, 5)), ((5, 13), (5, 18), (3, 18))),
    "z": (((1, 5), (9, 5), (1, 14), (9, 14)),),
    "0": (((3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11), (1, 3),
           (3, 0)),),
    "1": (((2, 3), (5, 0), (5, 14)), ((2, 14), (8, 14))),
    "2": (((2, 2), (4, 0), (7, 0), (9, 2), (9, 5), (8, 7), (1, 14), (9, 14)),),
    "3": (((1, 2), (3, 0), (7, 0), (9, 2), (9, 6), (7, 7), (5, 7)),
          ((5, 7), (7, 7), (9, 9), (9, 12), (7, 14), (3, 14), (1, 12))),
    "4": (((8, 0), (8, 14)), ((1, 10), (8, 10)), ((7, 0), (1, 10))),
    "5": (((8, 0), (1, 0), (1, 6), (6, 6), (8, 8), (8, 12), (6, 14), (1, 14)),),
    "6": (((8, 2), (6, 0), (3, 0), (1, 3), (1, 11), (3, 14), (7, 14), (9, 11),
           (9, 8), (7, 6), (3, 6), (1, 8)),),
    "7": (((1, 0), (9, 0), (5, 14)),),
    "8": (((3, 0), (7, 0), (9, 2), (9, 5), (7, 7), (3, 7), (1, 5), (1, 2), (3, 0)),
          ((3, 7), (7, 7), (9, 9), (9, 12), (7, 14), (3, 14), (1, 12), (1, 9),
           (3, 7))),
    "9": (((3, 0), (7, 0), (9, 3), (9, 8), (7, 10), (3, 10), (1, 8), (1, 3),
           (3, 0)), ((9, 3), (9, 11), (7, 14), (4, 14), (2, 12))),
    " ": (),
    ".": (((5, 13), (5, 14)),),
    ",": (((5, 12), (5, 14)), ((5, 14), (3, 17))),
    "'": (((5, 0), (4, 4)),),
    "/": (((2, 14), (8, 0)),),
    "-": (((1, 7), (9, 7)),),
    "\u2014": (((0, 7), (10, 7)),),
    "\u00b7": (((5, 6), (5, 7)),),
    ":": (((5, 4), (5, 5)), ((5, 10), (5, 11))),
    "<": (((8, 0), (2, 7), (8, 14)),),
    ">": (((2, 0), (8, 7), (2, 14)),),
    "(": (((6, 0), (3, 3), (3, 11), (6, 14)),),
    ")": (((4, 0), (7, 3), (7, 11), (4, 14)),),
}

_FONT_CACHE = {}


def _glyph_lines(ch, size, bold, italic):
    """Scaled polylines for one glyph, in pixels relative to the
    glyph origin (top-left of the cap box). Cached."""
    key = (ch, size, bold, italic)
    got = _FONT_CACHE.get(key)
    if got is not None:
        return got
    scale = size / 14.0
    width = size * (0.20 if bold else 0.11)
    lines = []
    for stroke in GLYPHS.get(ch, ()):
        pts = []
        for (gx, gy) in stroke:
            x = gx + (0.22 * (14 - gy) if italic else 0.0)
            pts.append((x * scale, gy * scale))
        lines.append((pts, width))
    _FONT_CACHE[key] = lines
    return lines


def text_width(s, size, advance=10.0):
    return len(s) * advance * size / 14.0


# ------------------------------------------------------------------ canvas
class Canvas(object):
    """RGBA raster canvas, pixels stored as a flat bytearray."""

    def __init__(self, w, h, color=(0, 0, 0, 0)):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(_rgba(color)) * (w * h))

    # -- low level ------------------------------------------------------
    def _span(self, x0, x1, y, color):
        """Fill horizontal span [x0, x1] on row y (clipped)."""
        if y < 0 or y >= self.h or x1 < x0:
            return
        x0 = max(x0, 0)
        x1 = min(x1, self.w - 1)
        if x1 < x0:
            return
        r, g, b, a = _rgba(color)
        base = (y * self.w + x0) * 4
        n = x1 - x0 + 1
        if a == 255:
            self.px[base:base + 4 * n] = bytes((r, g, b, 255)) * n
        elif a:
            px = self.px
            ia = 255 - a
            for i in range(n):
                o = base + 4 * i
                px[o] = (r * a + px[o] * ia) // 255
                px[o + 1] = (g * a + px[o + 1] * ia) // 255
                px[o + 2] = (b * a + px[o + 2] * ia) // 255
                px[o + 3] = min(255, a + (px[o + 3] * ia) // 255)

    def pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self._span(x, x, y, color)

    def _disc(self, cx, cy, rw, color):
        """Filled disc of radius rw (float) centred on (cx, cy)."""
        r = int(rw)
        for dy in range(-r, r + 1):
            hw = int((rw * rw - dy * dy) ** 0.5)
            self._span(cx - hw, cx + hw, cy + dy, color)

    # -- shapes ---------------------------------------------------------
    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self._span(x0, x1, y, color)

    def rect_outline(self, x0, y0, x1, y1, color, width=1):
        for i in range(width):
            self.fill_rect(x0 + i, y0 + i, x1 - i, y0 + i, color)
            self.fill_rect(x0 + i, y1 - i, x1 - i, y1 - i, color)
            self.fill_rect(x0 + i, y0 + i, x0 + i, y1 - i, color)
            self.fill_rect(x1 - i, y0 + i, x1 - i, y1 - i, color)

    def rounded_rect_outline(self, x0, y0, x1, y1, radius, color, width=1):
        self.line(x0 + radius, y0, x1 - radius, y0, color, width)
        self.line(x0 + radius, y1, x1 - radius, y1, color, width)
        self.line(x0, y0 + radius, x0, y1 - radius, color, width)
        self.line(x1, y0 + radius, x1, y1 - radius, color, width)
        for (cx, cy, a0) in ((x0 + radius, y0 + radius, 180),
                             (x1 - radius, y0 + radius, 270),
                             (x1 - radius, y1 - radius, 0),
                             (x0 + radius, y1 - radius, 90)):
            self.arc(cx, cy, radius, radius, a0, a0 + 90, color, width)

    def line(self, x0, y0, x1, y1, color, width=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = int(max(abs(dx), abs(dy))) + 1
        rw = width / 2.0
        for i in range(steps + 1):
            t = i / steps if steps else 0.0
            self._disc(int(round(x0 + dx * t)), int(round(y0 + dy * t)),
                       rw, color)

    def ellipse_outline(self, cx, cy, rx, ry, color, width=1):
        self.arc(cx, cy, rx, ry, 0, 360, color, width)

    def ellipse_fill(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / float(ry) if ry else 0.0
            if abs(t) > 1:
                continue
            hw = int(rx * (1 - t * t) ** 0.5)
            self._span(cx - hw, cx + hw, y, color)

    def arc(self, cx, cy, rx, ry, a0, a1, color, width=1):
        n = max(8, int(2 * math.pi * max(rx, ry) / 3))
        prev = None
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pt = (int(round(cx + rx * math.cos(a))),
                  int(round(cy + ry * math.sin(a))))
            if prev is not None:
                self.line(prev[0], prev[1], pt[0], pt[1], color, width)
            prev = pt

    def polygon_fill(self, pts, color):
        ys = [p[1] for p in pts]
        ymin, ymax = int(min(ys)), int(max(ys))
        n = len(pts)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / float(y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self._span(int(math.ceil(xs[i])), int(math.floor(xs[i + 1])),
                           y, color)

    # -- compositing ----------------------------------------------------
    def blit(self, src, dx, dy):
        """Paste src canvas over this one, honouring src alpha."""
        sw, sh = src.w, src.h
        x0 = max(0, -dx)
        y0 = max(0, -dy)
        x1 = min(sw, self.w - dx)
        y1 = min(sh, self.h - dy)
        spx, dpx = src.px, self.px
        for y in range(y0, y1):
            srow = y * sw * 4
            drow = ((dy + y) * self.w + dx + x0) * 4
            # fast path: a whole source row that is fully opaque
            if spx[srow + 3 + x0 * 4:srow + sw * 4:4] == b"\xff" * (x1 - x0):
                n = x1 - x0
                dpx[drow:drow + 4 * n] = spx[srow + x0 * 4:srow + x0 * 4 + 4 * n]
                continue
            for x in range(x0, x1):
                so = srow + x * 4
                a = spx[so + 3]
                if not a:
                    continue
                do = drow + (x - x0) * 4
                if a == 255:
                    dpx[do:do + 4] = spx[so:so + 4]
                else:
                    ia = 255 - a
                    dpx[do] = (spx[so] * a + dpx[do] * ia) // 255
                    dpx[do + 1] = (spx[so + 1] * a + dpx[do + 1] * ia) // 255
                    dpx[do + 2] = (spx[so + 2] * a + dpx[do + 2] * ia) // 255
                    dpx[do + 3] = min(255, a + (dpx[do + 3] * ia) // 255)

    def rotate(self, angle_deg):
        """Rotate counter-clockwise (PIL convention) about the centre,
        same size, transparent where nothing lands. Nearest sampling."""
        out = Canvas(self.w, self.h)
        a = math.radians(angle_deg)
        ca, sa = math.cos(a), math.sin(a)
        cx, cy = (self.w - 1) / 2.0, (self.h - 1) / 2.0
        spx, dpx = self.px, out.px
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = x - cx, y - cy
                sx = int(round(cx + dx * ca + dy * sa))
                sy = int(round(cy - dx * sa + dy * ca))
                if 0 <= sx < self.w and 0 <= sy < self.h:
                    so = (sy * self.w + sx) * 4
                    if spx[so + 3]:
                        do = (y * self.w + x) * 4
                        dpx[do:do + 4] = spx[so:so + 4]
        return out

    def to_rgb(self):
        rgb = bytearray(self.w * self.h * 3)
        px = self.px
        for i in range(self.w * self.h):
            rgb[3 * i:3 * i + 3] = px[4 * i:4 * i + 3]
        return bytes(rgb)

    # -- text -----------------------------------------------------------
    def text(self, x, y, s, size, color, anchor="la", bold=False,
             italic=False, advance=10.0):
        """Draw text; (x, y) is the top of the cap box. anchor: la
        (left), ma (middle), ra (right)."""
        if anchor != "la":
            w = text_width(s, size, advance)
            if anchor == "ma":
                x = x - w / 2.0
            elif anchor == "ra":
                x = x - w
        step = advance * size / 14.0
        cx = x
        for ch in s:
            for pts, width in _glyph_lines(ch, size, bold, italic):
                prev = None
                for (gx, gy) in pts:
                    pt = (int(round(cx + gx)), int(round(y + gy)))
                    if prev is not None:
                        self.line(prev[0], prev[1], pt[0], pt[1], color,
                                  max(1, int(round(width))))
                    prev = pt
            cx += step


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
def draw_lighthouse(d, cx, cy, r, colour, beams=True):
    """Small lighthouse emblem inside a circle."""
    d.ellipse_outline(cx, cy, r, r, colour, 2)
    # tower
    tw = r * 0.34
    d.polygon_fill([(cx - tw, cy + r * 0.72), (cx - tw * 0.7, cy - r * 0.28),
                    (cx + tw * 0.7, cy - r * 0.28), (cx + tw, cy + r * 0.72)],
                   colour)
    d.fill_rect(int(cx - tw * 0.95), int(cy - r * 0.42),
                int(cx + tw * 0.95), int(cy - r * 0.28), colour)
    d.polygon_fill([(cx - tw, cy - r * 0.42), (cx, cy - r * 0.78),
                    (cx + tw, cy - r * 0.42)], colour)
    if beams:
        d.polygon_fill([(cx - tw * 0.7, cy - r * 0.35),
                        (cx - r * 0.95, cy - r * 0.62),
                        (cx - r * 0.95, cy - r * 0.18)], colour)
        d.polygon_fill([(cx + tw * 0.7, cy - r * 0.35),
                        (cx + r * 0.95, cy - r * 0.62),
                        (cx + r * 0.95, cy - r * 0.18)], colour)
    # sea
    d.arc(cx, cy, int(r * 0.8), int(r * 0.8), 0, 180, colour, 2)
    # NOTE: arc above draws a full lower half; the original drew the arc
    # over the lower half of the circle only (0..180 in PIL's y-down
    # coords is the lower half). Kept as-is.


def guilloche(page, box, colour, alpha=16, step=9):
    """Faint wavy security lines across a page."""
    x0, y0, x1, y1 = box
    y = y0
    while y < y1:
        prev = None
        for x in range(x0, x1, 4):
            pt = (x, int(y + 3 * math.sin((x - x0) / 26.0 + y / 40.0)))
            if prev is not None:
                page.line(prev[0], prev[1], pt[0], pt[1],
                          colour + (alpha,), 1)
            prev = pt
        y += step


def draw_stamp(stamp):
    """One entry/exit stamp, drawn on its own layer and rotated."""
    w, h = 200, 128
    layer = Canvas(w + 40, h + 40)
    ink = stamp["ink"]
    x0, y0, x1, y1 = 20, 20, 20 + w, 20 + h
    layer.rounded_rect_outline(x0, y0, x1, y1, 10, ink, 3)
    layer.rounded_rect_outline(x0 + 5, y0 + 5, x1 - 5, y1 - 5, 7, ink, 1)
    cx = (x0 + x1) // 2
    layer.text(cx, y0 + 12, stamp["country"], 15, ink, anchor="ma", bold=True)
    layer.text(cx, y0 + 32, stamp["kind"], 12, ink, anchor="ma", bold=True)
    layer.line(x0 + 22, y0 + 52, x1 - 22, y0 + 52, ink, 1)
    layer.text(cx, y0 + 58, stamp["port"], 11, ink, anchor="ma")
    layer.text(cx, y0 + 76, stamp["date"], 16, ink, anchor="ma", bold=True)
    layer.text(x1 - 10, y1 - 18, "No. " + stamp["no"], 8, ink, anchor="ra")
    # tiny icon, bottom-left
    ix, iy = x0 + 12, y1 - 26
    if stamp["icon"] == "anchor":
        layer.line(ix + 8, iy, ix + 8, iy + 18, ink, 2)
        layer.arc(ix + 8, iy + 6, 8, 6, 180, 360, ink, 2)
        layer.line(ix, iy + 13, ix + 16, iy + 13, ink, 2)
        layer.arc(ix + 8, iy + 14, 7, 6, 0, 180, ink, 2)
    elif stamp["icon"] == "wave":
        for k in range(3):
            layer.arc(ix + 9, iy + 4 + k * 6, 9, 4, 180, 360, ink, 2)
    elif stamp["icon"] == "fish":
        layer.ellipse_outline(ix + 8, iy + 9, 8, 5, ink, 2)
        layer.polygon_fill([(ix + 15, iy + 9), (ix + 22, iy + 3),
                            (ix + 22, iy + 15)], ink)
        layer.pixel(ix + 4, iy + 8, ink)
    else:  # lighthouse
        layer.polygon_fill([(ix + 5, iy + 18), (ix + 7, iy + 2),
                            (ix + 11, iy + 2), (ix + 13, iy + 18)], ink)
        layer.line(ix, iy + 18, ix + 18, iy + 18, ink, 2)
    return layer.rotate(stamp["rot"])


def round_fee_stamp():
    """Circular red 'LIGHT DUES PAID' fee stamp. Sized 140 so that,
    blitted at (309, 508), its top arc clears the endorsement's last
    line and its MIRENPORT line clears the footer line."""
    s = 140
    layer = Canvas(s, s)
    c = s // 2
    layer.ellipse_outline(c, c, s // 2 - 4, s // 2 - 4, RED, 3)
    layer.ellipse_outline(c, c, s // 2 - 14, s // 2 - 14, RED, 1)
    layer.text(c, c - 34, "LIGHT DUES", 13, RED, anchor="ma", bold=True)
    layer.text(c, c - 16, "40 KR", 20, RED, anchor="ma", bold=True)
    layer.text(c, c + 8, "PAID", 15, RED, anchor="ma", bold=True)
    layer.text(c, c + 30, "MIRENPORT", 9, RED, anchor="ma")
    return layer.rotate(-8)


def field_compact(d, x, y, label, label_z, value):
    """Label + Zaldrian label on one line (measured gap), value below."""
    d.text(x, y, label, 9, GREY)
    w = text_width(label, 9)
    d.text(x + w + 8, y, label_z, 9, GREY)
    d.text(x, y + 12, value, 15, INK, bold=True)


def field(d, x, y, label, label_z, value, value_size=15):
    d.text(x, y, label, 9, GREY)
    d.text(x + 132, y, label_z, 9, GREY)
    d.text(x, y + 12, value, value_size, INK, bold=True)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    img = Canvas(W, H, (46, 52, 64, 255))

    # desk shadow + pages
    for (px, py) in ((28, 36), (524, 36)):
        img.fill_rect(px + 5, py + 6, px + 472 + 5, py + 648 + 6,
                      (20, 23, 30, 255))
    left = Canvas(472, 648, PAPER + (255,))
    right = Canvas(472, 648, PAPER + (255,))
    guilloche(left, (8, 8, 464, 640), NAVY)
    guilloche(right, (8, 8, 464, 640), NAVY)

    # ============================== LEFT PAGE: data page
    d = left
    draw_lighthouse(d, 44, 44, 22, NAVY)
    d.text(76, 22, COUNTRY, 19, NAVY, bold=True)
    d.text(76, 46, "PASSPORT  \u00b7  VEGABR\u00c9F", 11, GREY)
    d.line(20, 74, 452, 74, GOLD, 2)
    d.line(20, 78, 452, 78, GOLD, 1)
    d.text(452, 46, MOTTO, 10, GREY, anchor="ra", italic=True)

    # portrait — pre-scaled 148x186 PNG (same crop + LANCZOS resize the
    # Pillow build used), decoded by the stdlib PNG reader. Path is
    # resolved against this file, never the working directory.
    portrait_path = os.path.join(BASE_DIR, "assets", "portrait_small.png")
    try:
        pw, ph, px = png_decode(portrait_path)
    except Exception:
        pw, ph, px = png_decode(os.path.join(BASE_DIR, "assets",
                                             "portrait.png"))
    portrait = Canvas(pw, ph)
    portrait.px = px
    # paste 1:1 at the photo box (148x186); if the fallback full-size
    # portrait was loaded, it is cropped/resized by plain sampling
    if (pw, ph) != (148, 186):
        small = Canvas(148, 186)
        crop_h = int(pw / (148 / 186))
        y0 = 80
        for y in range(186):
            sy = y0 + int(y * crop_h / 186)
            for x in range(148):
                sx = int(x * pw / 148)
                so = (sy * pw + sx) * 4
                do = (y * 148 + x) * 4
                small.px[do:do + 4] = portrait.px[so:so + 4]
        portrait = small
    left.blit(portrait, 24, 104)
    d.rect_outline(24, 104, 24 + 148, 104 + 186, NAVY, 2)
    d.rect_outline(28, 108, 24 + 144, 104 + 182, NAVY, 1)

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
    d.text(452, 318, "Mara Selvig", 15, INK, anchor="ra", italic=True)
    d.line(360, 340, 452, 340, INK, 1)
    d.text(452, 344, "HOLDER'S SIGNATURE / UNDIRSKRIFT", 8, GREY,
           anchor="ra")

    d.line(20, 378, 452, 378, GOLD, 1)
    # document details
    d.text(24, 392, "PASSPORT No.", 9, GREY)
    d.text(24, 405, HOLDER["number"], 16, INK, bold=True)
    d.text(180, 392, "TYPE", 9, GREY)
    d.text(180, 405, "P", 16, INK, bold=True)
    d.text(240, 392, "CODE", 9, GREY)
    d.text(240, 405, "ZLD", 16, INK, bold=True)
    d.text(330, 392, "DATE OF ISSUE", 9, GREY)
    d.text(330, 405, HOLDER["issued"], 14, INK, bold=True)
    d.text(24, 448, "DATE OF EXPIRY", 9, GREY)
    d.text(24, 461, HOLDER["expiry"], 14, INK, bold=True)
    d.text(180, 448, "AUTHORITY", 9, GREY)
    d.text(180, 461, HOLDER["authority"], 12, INK, bold=True)

    # MRZ
    d.line(20, 516, 452, 516, GOLD, 1)
    line1, line2 = mrz_lines()
    d.fill_rect(20, 524, 452, 566, (255, 255, 255, 255))
    d.text(24, 528, line1, 14, INK, advance=9.5)
    d.text(24, 546, line2, 14, INK, advance=9.5)
    d.text(452, 578, "12", 9, GREY, anchor="ra")

    # ============================== RIGHT PAGE: stamps
    d = right
    d.text(24, 22, "VISAS", 19, NAVY, bold=True)
    d.text(24, 46, "STAMPS  \u00b7  STIMPLAR", 11, GREY)
    d.line(20, 74, 452, 74, GOLD, 2)
    d.line(20, 78, 452, 78, GOLD, 1)

    positions = [(28, 96), (240, 104), (28, 258), (240, 266)]
    for stamp, (sx, sy) in zip(STAMPS, positions):
        layer = draw_stamp(stamp)
        right.blit(layer, sx - 20, sy - 20)

    # endorsement — the telling detail of paperwork
    d.rect_outline(24, 424, 448, 516, NAVY, 2)
    d.text(36, 434, "ENDORSEMENT", 11, NAVY, bold=True)
    d.text(36, 452, "HOLDER IS A KEEPER OF THE NORTH LIGHT.", 13, INK,
           bold=True)
    d.text(36, 472, "MAY LAND AT ANY HARBOUR IN FOG.", 12, INK)
    d.text(36, 492, "NO PAID WORK. FISHING LICENCE REQUIRED AFTER 30 DAYS.",
           10, INK)

    fee = round_fee_stamp()
    right.blit(fee, 309, 508)
    d.text(24, 612,
           "This passport remains the property of the Republic of Zaldria.",
           6, GREY, italic=True)
    d.text(452, 636, "13", 9, GREY, anchor="ra")

    # compose spread
    img.blit(left, 28, 36)
    img.blit(right, 524, 36)
    # centre gutter shadow
    for i in range(10):
        img.fill_rect(495 + i, 36, 495 + i, 36 + 648,
                      (0, 0, 0, 26 - abs(i - 5) * 4))

    rgb = img.to_rgb()
    png_encode_rgb(out_path, W, H, rgb)
    print("wrote", out_path, (W, H), os.path.getsize(out_path), "bytes")


if __name__ == "__main__":
    main()
