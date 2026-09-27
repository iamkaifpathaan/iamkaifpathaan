"""Text -> SVG path outlines.

GitHub renders README SVGs as sandboxed <img>s, so web fonts never load.
Every glyph in the profile artwork is therefore converted to a vector path
here, shaped with HarfBuzz (real kerning) using the same families as the
banner: Space Grotesk (display), Inter (body), JetBrains Mono (labels).
"""
import os
import re
import subprocess
import urllib.request
from functools import lru_cache

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.path.dirname(__file__), ".fonts")
FAMILIES = {
    "grotesk": ("Space Grotesk", "SpaceGrotesk"),
    "inter": ("Inter", "Inter"),
    "mono": ("JetBrains Mono", "JetBrainsMono"),
}


def _ensure(key, weight):
    family, stem = FAMILIES[key]
    path = os.path.join(FONT_DIR, f"{stem}-{weight}.ttf")
    if not os.path.exists(path):
        os.makedirs(FONT_DIR, exist_ok=True)
        css_url = ("https://fonts.googleapis.com/css2?family="
                   + family.replace(" ", "+") + f":wght@{weight}")
        # An old user agent makes Google Fonts serve plain TrueType files.
        req = urllib.request.Request(css_url, headers={"User-Agent": "Mozilla/4.0"})
        css = urllib.request.urlopen(req).read().decode()
        url = re.search(r"url\(([^)]+)\)", css).group(1)
        urllib.request.urlretrieve(url, path)
    return path


@lru_cache(maxsize=None)
def _font(key, weight):
    path = _ensure(key, weight)
    blob = hb.Blob.from_file_path(path)
    return TTFont(path), hb.Font(hb.Face(blob))


def measure(s, key="inter", weight=400, size=16, tracking=0.0):
    return text(s, 0, 0, key, weight, size, tracking)[1]


def text(s, x, y, key="inter", weight=400, size=16, tracking=0.0, anchor="start"):
    """Return (path_d, advance_width). (x, y) is the baseline origin.

    tracking is extra letter spacing in em units (0.2 == 0.2em).
    """
    tt, hbfont = _font(key, weight)
    upm = tt["head"].unitsPerEm
    scale = size / upm
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True, "liga": True})
    order = tt.getGlyphOrder()
    gs = tt.getGlyphSet()
    extra = tracking * upm
    total = sum(p.x_advance for p in buf.glyph_positions) + extra * max(len(buf.glyph_infos) - 1, 0)
    width = total * scale
    ox = x - (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
    pen_x = 0
    parts = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        sp = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        tx = ox + (pen_x + pos.x_offset) * scale
        ty = y - pos.y_offset * scale
        gs[name].draw(TransformPen(sp, (scale, 0, 0, -scale, tx, ty)))
        d = sp.getCommands()
        if d:
            parts.append(d)
        pen_x += pos.x_advance + extra
    return " ".join(parts), width
