# darken_images.py (SuperScience Blue, tools)
# Created: 2026-09-29 16:33 | Last change: 2026-09-29 16:36 — white handled per image; in images with white glyphs, light anti-aliased edge pixels are kept too (no dark specks).
# SPDX-License-Identifier: GPL-3.0-or-later
"""Derive the dark variant's images from the light theme's images.
Every pixel gets the same color rule darken.py applies to the stylesheet
(greys inverted into a dark range; blues, status colors, pure white and
near-black kept), and its alpha is left unchanged, so checkboxes, radio
buttons, switches and border images match the dark stylesheet.
Pure white depends on the image: the checkmarks and dots of checked/mixed
states stay white (with their light anti-aliased edges), the fill of unchecked checkboxes and radio buttons
becomes the dark view color, and the knobs of switches that are off become a soft light grey.
Usage: darken_images.py light_dir dark_dir  (PNG files, one level deep)"""
import colorsys
import os
import sys
from PIL import Image
from darken import dark_rgb


KNOB_GREY = (200, 204, 212)


def white_for(name):
    """What pure white becomes in the image called name."""
    if name.startswith("switch") and "-active" not in name:
        return KNOB_GREY
    if name.startswith(("checkbox", "radio")) and "-checked" not in name and "-mixed" not in name:
        return dark_rgb(254, 254, 254)
    return (255, 255, 255)


def darken_png(src, dst):
    img = Image.open(src).convert("RGBA")
    white = white_for(os.path.basename(src))
    cache = {}
    out = []
    for r, g, b, a in img.get_flattened_data():
        if a == 0:
            out.append((r, g, b, a))
            continue
        key = (r, g, b)
        if key not in cache:
            if key == (255, 255, 255):
                cache[key] = white
            elif white == (255, 255, 255) and colorsys.rgb_to_hls(r / 255, g / 255, b / 255)[1] > 0.75:
                cache[key] = key          # edge of a white glyph: keep it light
            else:
                cache[key] = dark_rgb(r, g, b)
        out.append(cache[key] + (a,))
    img.putdata(out)
    img.save(dst)


def main():
    src_dir, dst_dir = sys.argv[1], sys.argv[2]
    os.makedirs(dst_dir, exist_ok=True)
    count = 0
    for name in sorted(os.listdir(src_dir)):
        if name.lower().endswith(".png"):
            darken_png(os.path.join(src_dir, name), os.path.join(dst_dir, name))
            count += 1
    print(f"{count} images -> {dst_dir}")


if __name__ == "__main__":
    main()
