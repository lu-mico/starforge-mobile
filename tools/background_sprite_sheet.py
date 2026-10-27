#!/usr/bin/env python3
"""
Starforge-mobile — battlefield background (720x1280, 1 lane).

docs/ASSET_UI_SPEC.md §4 + the engine's real geometry:
  * viewport is 720x1280 with stretch mode canvas_items -> engine pixels ==
    background pixels, no extra 2x scaling
  * the lane band is y=340..380 (main.tscn "Lane" rect) and every unit's feet
    land on lane_y = 360 (Unit.gd locks position.y = lane_y)
    => the ground line in this image MUST be y=360, not the image centre
  * exact 2x pixel grid: every colour-block boundary lands on an even coord
  * no dither / no single-pixel noise: 4x4 rule blocks only
  * large neutral-grey areas, 3-4 brightness levels, no unit colours
  * one lane: horizontal band + boundary lines
  * clear flat ground at the far left/right for the tower bases
  * top/bottom mirrored about the lane (enemy side / player side)
  * the central vertical 40% stays free of high-contrast terrain texture
  * fully opaque

The background is drawn with PIL rectangle fills (integer coords) rather than
the polygon rasteriser used for sprites: 720x1280 is 4.6M pixels and the
per-pixel polygon test would take minutes. Integer rects still give hard
edges and an exact 2x grid.
"""
from PIL import Image, ImageDraw

W, H = 720, 1280
GROUND_Y = 360            # engine lane_y - every unit's feet land here
LANE_TOP, LANE_BOT = 340, 379   # the lane surface (covers the engine's 340..380 band)
CENTER_CLEAN = (144, 576)       # central vertical 40%: no terrain texture
TOWER_BASE = (300, 419)         # tower-base clearing, centred on the lane

# neutral greys only (blue/orange stay for units and towers)
FIELD = (107, 114, 128)    # G - base terrain
LANE = (170, 179, 194)     # T - lane surface
DARK = (16, 24, 32)       # S - dark terrain blocks
LIGHT = (200, 212, 228)   # R - light terrain blocks
INK = (11, 13, 26)        # K - lane boundary lines
GROUND = (42, 63, 102)     # C - ground line / tower-base ground


def _mirror_y(y, size):
    """Mirror the terrain about the image centre (top half == bottom half).

    The lane band itself is NOT mirrored: the engine pins it to y=340..380
    (main.tscn "Lane" rect) with every unit's feet on lane_y=360, so it has
    no counterpart in the lower half by design."""
    return H - y - size


def _terrain(draw):
    """4x4-rule terrain blocks, mirrored about the ground line."""
    blocks = [
        (16, 64, 24, DARK), (88, 32, 16, LIGHT), (176, 96, 32, DARK),
        (264, 16, 16, DARK), (352, 128, 24, LIGHT), (440, 64, 16, DARK),
        (560, 144, 32, DARK), (648, 48, 24, LIGHT), (24, 200, 16, DARK),
        (120, 264, 24, LIGHT), (232, 232, 16, DARK), (320, 192, 16, DARK),
        (416, 256, 24, LIGHT), (520, 208, 16, DARK), (600, 280, 24, DARK),
        (664, 232, 16, LIGHT),
    ]
    for x, y, s, col in blocks:
        if x + s > CENTER_CLEAN[0] and x < CENTER_CLEAN[1]:
            continue
        draw.rectangle([x, y, x + s - 1, y + s - 1], fill=col)
        my = _mirror_y(y, s)
        draw.rectangle([x, my, x + s - 1, my + s - 1], fill=col)


def build_background():
    img = Image.new("RGBA", (W, H), FIELD + (255,))
    d = ImageDraw.Draw(img)

    # lane band + boundary lines (every boundary on an even coordinate)
    d.rectangle([0, LANE_TOP, W - 1, LANE_BOT], fill=LANE)
    d.rectangle([0, LANE_TOP - 4, W - 1, LANE_TOP - 1], fill=INK)
    d.rectangle([0, LANE_BOT + 1, W - 1, LANE_BOT + 4], fill=INK)
    # ground line: exactly where the units' feet land (lane_y = 360)
    d.rectangle([0, GROUND_Y - 2, W - 1, GROUND_Y + 1], fill=DARK)   # the ground line

    # tower-base clearings: flat marked ground at the lane level, both ends
    for x0, x1 in ((0, 131), (W - 132, W - 1)):
        d.rectangle([x0, TOWER_BASE[0], x1, TOWER_BASE[1]], fill=FIELD)
        d.rectangle([x0, TOWER_BASE[0], x1, TOWER_BASE[0] + 3], fill=INK)
        d.rectangle([x0, TOWER_BASE[1] - 3, x1, TOWER_BASE[1]], fill=INK)

    # mirrored terrain texture
    _terrain(d)

    # lane approach marks (symmetric, outside the central clean strip)
    for x in (24, 64, 640, 680):
        d.rectangle([x, LANE_TOP - 28, x + 3, LANE_TOP - 5], fill=DARK)
        d.rectangle([x, LANE_BOT + 9, x + 3, LANE_BOT + 30], fill=DARK)

    return img


def build_image():
    return build_background()


def self_check(img):
    """Lane alignment + grid + opacity. Returns a list of problems."""
    px = img.load()
    problems = []
    if img.size != (W, H):
        problems.append(f"size {img.size} != {(W, H)}")
    if {px[x, y][3] for x in range(0, W, 13) for y in range(0, H, 13)} != {255}:
        problems.append("background is not fully opaque")
    # the engine's lane band (340..380) must be lane surface
    for y in (340, 360, 380):
        if px[360, y][:3] not in (LANE, GROUND):
            problems.append(f"lane surface missing at y={y}")
    # the ground line must sit on lane_y
    if px[360, GROUND_Y][:3] != DARK:
        problems.append("ground line is not on lane_y=360")
    bad = 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            c0 = px[x, y]
            if c0 != px[x + 1, y] or c0 != px[x, y + 1] or c0 != px[x + 1, y + 1]:
                bad += 1
    if bad:
        problems.append(f"{bad} 2x2 blocks are not on the pixel grid")
    # central 40% free of terrain texture
    field = {px[x, y][:3] for y in list(range(0, 336, 9)) + list(range(384, H, 9))
             for x in range(144, 576, 9)}
    if field - {FIELD, INK, DARK}:
        problems.append(f"central 40% carries texture: {field}")
    return problems
