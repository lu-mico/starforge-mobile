#!/usr/bin/env python3
"""
Starforge-mobile — battlefield background (720x1280, 1 lane).

docs/ASSET_UI_SPEC.md §4 + the engine's real geometry:
  * viewport is 720x1280 with stretch mode canvas_items -> engine pixels ==
    background pixels, no extra 2x scaling
  * the lane band is the battle row of the PORTRAIT screen and sits on its
    vertical centre: lane_y = 640 (main.tscn "Lane" rect 620..660, every unit's
    feet land on lane_y, both tower bases sit on the same row)
    => the ground line in this image MUST be y=640
  * §4 asks for the battle zone to be the central vertical 40% of the screen
    (rows 384..896). With the lane at 620..659 the battle zone IS inside that
    band; with the lane at 340..380 it would sit in the top quarter and the
    central band would be empty ground
  * exact 2x pixel grid: every colour-block boundary lands on an even coord
  * no dither / no single-pixel noise: 4x4 rule blocks only
  * large neutral-grey areas, 3-4 brightness levels, no unit colours
  * one lane: horizontal band + boundary lines
  * clear flat ground at the far left/right for the tower bases
  * EXACTLY mirrored top/bottom about the image centre (639.5): the lane band
    (620..659), the ground line (638..641), the tower pads (580..699) and the
    approach marks are all self-mirroring pairs, so the whole 720x1280 image
    satisfies row y == row 1279-y with ZERO differing pixels
  * the central x strip (144..576) carries no terrain texture, so units on the
    lane always read against plain ground
  * fully opaque

The background is drawn with PIL rectangle fills (integer coords) rather than
the polygon rasteriser used for sprites: 720x1280 is 4.6M pixels and the
per-pixel polygon test would take minutes. Integer rects still give hard
edges and an exact 2x grid.
"""
from PIL import Image, ImageDraw

W, H = 720, 1280
GROUND_Y = 640            # engine lane_y - every unit's feet land here
LANE_TOP, LANE_BOT = 620, 659   # lane surface; 620+659 == 1279 -> self-mirrored
CENTER_CLEAN = (144, 576)        # central x strip: no terrain texture
PAD_TOP, PAD_BOT = 580, 699      # tower-base clearing; 580+699 == 1279
MARK_TOP_A, MARK_TOP_B = 592, 615   # approach marks above the lane
MARK_BOT_A, MARK_BOT_B = 664, 687   # exact mirror of the pair above
PAD_PLAYER = (50, 149)         # player tower sprite is centred on x=100
PAD_ENEMY = (570, 669)         # enemy tower sprite is centred on x=620

# neutral greys only (blue/orange stay for units and towers)
FIELD = (107, 114, 128)    # G - base terrain
LANE = (170, 179, 194)     # T - lane surface
DARK = (16, 24, 32)       # S - dark terrain blocks / ground line
LIGHT = (200, 212, 228)   # R - light terrain blocks
INK = (11, 13, 26)        # K - lane boundary lines / pad rims


def _mirror_y(y, size):
    """Mirror the terrain about the image centre (top half == bottom half)."""
    return H - y - size


# Terrain blocks live in the upper half only; each one is mirrored below the
# centre. They stay out of the central x strip (CENTER_CLEAN) so the battle
# row always reads against plain ground.
BLOCKS = [
    (16, 32, 24, DARK), (88, 16, 16, LIGHT), (24, 112, 16, DARK),
    (16, 176, 32, LIGHT), (96, 208, 24, DARK), (40, 256, 32, LIGHT),
    (112, 296, 16, DARK), (16, 352, 24, DARK), (72, 392, 32, LIGHT),
    (24, 448, 16, LIGHT), (104, 504, 24, DARK), (48, 552, 16, DARK),
    (584, 48, 24, LIGHT), (648, 80, 32, DARK), (576, 144, 16, DARK),
    (600, 208, 32, LIGHT), (656, 272, 24, DARK), (584, 320, 16, LIGHT),
    (640, 368, 24, DARK), (576, 432, 32, LIGHT), (616, 496, 16, DARK),
    (656, 544, 24, LIGHT),
]


def _terrain(draw):
    """4x4-rule terrain blocks, mirrored about the image centre."""
    for x, y, s, col in BLOCKS:
        if x + s > CENTER_CLEAN[0] and x < CENTER_CLEAN[1]:
            continue
        draw.rectangle([x, y, x + s - 1, y + s - 1], fill=col)
        my = _mirror_y(y, s)
        draw.rectangle([x, my, x + s - 1, my + s - 1], fill=col)


def build_background():
    img = Image.new("RGBA", (W, H), FIELD + (255,))
    d = ImageDraw.Draw(img)

    # mirrored terrain texture
    _terrain(d)

    # tower-base clearings: flat marked ground at the lane level, both ends
    for x0, x1 in (PAD_PLAYER, PAD_ENEMY):
        d.rectangle([x0, PAD_TOP, x1, PAD_BOT], fill=FIELD)
        d.rectangle([x0, PAD_TOP, x1, PAD_TOP + 3], fill=INK)
        d.rectangle([x0, PAD_BOT - 3, x1, PAD_BOT], fill=INK)

    # lane band + boundary lines (every boundary on an even coordinate)
    d.rectangle([0, LANE_TOP, W - 1, LANE_BOT], fill=LANE)
    d.rectangle([0, LANE_TOP - 4, W - 1, LANE_TOP - 1], fill=INK)
    d.rectangle([0, LANE_BOT + 1, W - 1, LANE_BOT + 4], fill=INK)
    # ground line: exactly where the units' feet land (lane_y = 640)
    d.rectangle([0, GROUND_Y - 2, W - 1, GROUND_Y + 1], fill=DARK)

    # lane approach marks (an exact mirror pair about the image centre)
    for x in (24, 64, 640, 680):
        d.rectangle([x, MARK_TOP_A, x + 3, MARK_TOP_B], fill=DARK)
        d.rectangle([x, MARK_BOT_A, x + 3, MARK_BOT_B], fill=DARK)

    return img


def build_image():
    return build_background()


def self_check(img):
    """Lane alignment + grid + opacity + exact mirror. Returns problem list."""
    px = img.load()
    problems = []
    if img.size != (W, H):
        problems.append(f"size {img.size} != {(W, H)}")
    if {px[x, y][3] for x in range(0, W, 13) for y in range(0, H, 13)} != {255}:
        problems.append("background is not fully opaque")
    # the engine's lane band must be lane surface
    for y in (LANE_TOP, LANE_BOT):
        if px[360, y][:3] != LANE:
            problems.append(f"lane surface missing at y={y}")
    # the ground line must sit on lane_y
    if px[360, GROUND_Y][:3] != DARK:
        problems.append(f"ground line is not on lane_y={GROUND_Y}")
    bad = 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            c0 = px[x, y]
            if c0 != px[x + 1, y] or c0 != px[x, y + 1] or c0 != px[x + 1, y + 1]:
                bad += 1
    if bad:
        problems.append(f"{bad} 2x2 blocks are not on the pixel grid")
    # EXACT vertical mirror, no exclusions
    diff = 0
    for y in range(H // 2):
        my = H - 1 - y
        for x in range(W):
            if px[x, y] != px[x, my]:
                diff += 1
    if diff:
        problems.append(f"{diff} px differ between row y and row {H - 1}-y")
    # central x strip free of terrain texture
    field = {px[x, y][:3] for y in list(range(0, LANE_TOP - 4, 9)) + list(range(LANE_BOT + 5, H, 9))
             for x in range(144, 576, 9)}
    if field - {FIELD, INK, DARK}:
        problems.append(f"central strip carries texture: {field}")
    return problems
