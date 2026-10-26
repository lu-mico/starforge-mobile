#!/usr/bin/env python3
"""
Starforge-mobile — battlefield background (720x1280, 1 lane).

docs/ASSET_UI_SPEC.md §4:
  * exact 2x pixel grid (every colour-block boundary lands on an even coord)
  * no dither/noise: 2x2 or 4x4 rule blocks only
  * large neutral-grey areas, 3-4 brightness levels
  * no unit colours (blue/orange stay for units and towers)
  * one lane: a horizontal main band + boundary lines top and bottom
  * a clear flat area at the left and right for the tower bases
  * top/bottom mirrored (enemy side / player side)
  * the central vertical 40% must stay clean (no high-contrast texture)
  * fully opaque (alpha = 255)

The background is drawn with PIL's rectangle fill (integer coords) rather than
the polygon rasteriser used for the sprites: 720x1280 is 4.6M pixels, and the
per-pixel polygon test would take minutes. Integer rects still give hard
edges and an exact 2x grid.
"""
from PIL import Image, ImageDraw

W, H = 720, 1280
GRID = 2                      # 2x pixel grid
LANE_TOP, LANE_BOT = 440, 840  # the main lane band (both even)
CENTER_CLEAN = (144, 576)     # central vertical 40% stays texture-free

# neutral greys only (no unit colours)
FIELD = (107, 114, 128)        # G - base terrain
LANE = (170, 179, 194)         # T - lane surface
DARK = (16, 24, 32)           # S - dark terrain blocks
LIGHT = (200, 212, 228)       # R - light terrain blocks
INK = (11, 13, 26)            # K - lane boundary lines
SHADE = (42, 63, 102)         # C - tower-base ground (neutral-blue-grey)


def _terrain(draw, y0, y1):
    """Mirrored 4x4 terrain blocks, skipping the central clean strip."""
    # (x, y, size, colour) pattern in the upper half, mirrored below
    blocks = [
        (16, 96, 24, DARK), (88, 64, 16, LIGHT), (176, 128, 32, DARK),
        (264, 48, 16, DARK), (352, 160, 24, LIGHT), (440, 96, 16, DARK),
        (560, 176, 32, DARK), (648, 80, 24, LIGHT), (24, 232, 16, DARK),
        (120, 296, 24, LIGHT), (232, 264, 16, DARK), (320, 224, 16, DARK),
        (416, 288, 24, LIGHT), (520, 240, 16, DARK), (600, 312, 24, DARK),
        (664, 264, 16, LIGHT),
    ]
    for x, y, s, col in blocks:
        if CENTER_CLEAN[0] - s <= x <= CENTER_CLEAN[1]:
            continue
        draw.rectangle([x, y, x + s - 1, y + s - 1], fill=col)
        # mirror below the centre line
        my = H - 1 - (y + s - 1)
        draw.rectangle([x, my, x + s - 1, my + s - 1], fill=col)


def build_background():
    img = Image.new("RGBA", (W, H), FIELD + (255,))
    d = ImageDraw.Draw(img)

    # lane band + boundary lines (every boundary on an even coordinate)
    d.rectangle([0, LANE_TOP, W - 1, LANE_BOT - 4], fill=LANE)
    d.rectangle([0, LANE_TOP - 4, W - 1, LANE_TOP - 1], fill=INK)
    d.rectangle([0, LANE_BOT, W - 1, LANE_BOT + 3], fill=INK)
    d.rectangle([0, LANE_BOT - 4, W - 1, LANE_BOT - 1], fill=DARK)

    # tower-base clearings: flat, marked, outside the lane surface
    # x1 must be odd so the edge lands on an even coordinate (2x grid)
    for x0, x1 in ((0, 131), (W - 132, W - 1)):
        d.rectangle([x0, 520, x1, 759], fill=SHADE)
        d.rectangle([x0, 520, x1, 523], fill=INK)
        d.rectangle([x0, 756, x1, 759], fill=INK)

    # mirrored terrain texture
    _terrain(d, 0, H)

    # lane approach marks (symmetric, subtle, outside the clean centre)
    for x in (24, 64, 640, 680):   # kept outside the central clean strip
        d.rectangle([x, LANE_TOP - 28, x + 3, LANE_TOP - 5], fill=DARK)
        d.rectangle([x, LANE_BOT + 8, x + 3, LANE_BOT + 31], fill=DARK)

    assert img.mode == "RGBA"
    return img


def build_image():
    return build_background()
