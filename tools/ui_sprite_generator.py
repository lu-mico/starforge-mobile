#!/usr/bin/env python3
"""
Regenerate the UI batch (docs/ASSET_UI_SPEC.md §3) and the battlefield
background (§4) into the repo:

    python3 tools/ui_sprite_generator.py [REPO_PATH]

Exports
  assets/sprites/ui/icon_marine.png        64x64
  assets/sprites/ui/icon_marauder.png      64x64
  assets/sprites/ui/icon_hellion.png       64x64
  assets/sprites/ui/icon_siege_tank.png    64x64
  assets/sprites/ui/card_frame.png         48x64  (9-slice, patch_margin 10)
  assets/sprites/ui/icon_mineral_32.png    32x32
  assets/sprites/ui/icon_mineral_16.png    16x16
  assets/sprites/ui/card_badge_cost.png    12x12
  assets/sprites/ui/card_badge_count.png   12x12
  assets/sprites/ui/card_badge_frame.png   12x12
  assets/sprites/ui/ui_frames.json         manifest (same shape as towers)
  assets/sprites/background/battlefield_720x1280.png

Then runs the batch-specific gate (the three checks Nagi asked for):
  1. 9-slice patch_margin stretched to 3 sizes without a seam
  2. the background sits on an exact 2x pixel grid
  3. the UI icon body height is measured and identical across the four icons
plus the standing rules: <=16 colours, alpha {0,255}, opaque background.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image

import marine_sprite_sheet as M
import ui_sprite_sheet as U
import background_sprite_sheet as B

PATCH_MARGIN = 10
ICON_BODY_MAX = 40


# ---------------------------------------------------------------- helpers

def alpha_and_colours(img):
    px = list(img.convert("RGBA").getdata())
    alphas = {p[3] for p in px}
    colours = len({p for p in px if p[3] == 255})
    return alphas, colours


def body_box(img):
    p = img.convert("RGBA").getbbox()
    return p


# ---------------------------------------------------------------- gate 1: 9-slice

def stretch_9slice(src, margin, w, h):
    """Stitch a 9-slice the way Godot does: corners fixed, edges stretched."""
    sw, sh = src.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # corners
    out.paste(src.crop((0, 0, margin, margin)), (0, 0))
    out.paste(src.crop((sw - margin, 0, sw, margin)), (w - margin, 0))
    out.paste(src.crop((0, sh - margin, margin, sh)), (0, h - margin))
    out.paste(src.crop((sw - margin, sh - margin, sw, sh)), (w - margin, h - margin))
    # top / bottom edges (stretched horizontally)
    top = src.crop((margin, 0, sw - margin, margin)).resize((w - 2 * margin, margin), Image.NEAREST)
    bot = src.crop((margin, sh - margin, sw - margin, sh)).resize((w - 2 * margin, margin), Image.NEAREST)
    out.paste(top, (margin, 0))
    out.paste(bot, (margin, h - margin))
    # left / right edges (stretched vertically)
    left = src.crop((0, margin, margin, sh - margin)).resize((margin, h - 2 * margin), Image.NEAREST)
    right = src.crop((sw - margin, margin, sw, sh - margin)).resize((margin, h - 2 * margin), Image.NEAREST)
    out.paste(left, (0, margin))
    out.paste(right, (w - margin, margin))
    # centre
    centre = src.crop((margin, margin, sw - margin, sh - margin)).resize(
        (w - 2 * margin, h - 2 * margin), Image.NEAREST)
    out.paste(centre, (margin, margin))
    return out


def check_nine_slice(src):
    sw, sh = src.size
    px = src.load()
    problems = []
    # centre region must be one flat colour
    centre = {px[x, y] for x in range(PATCH_MARGIN, sw - PATCH_MARGIN)
              for y in range(PATCH_MARGIN, sh - PATCH_MARGIN)}
    if len(centre) != 1:
        problems.append(f"centre region is not flat ({len(centre)} colours)")
    # left/right bands: every column must be constant (vertical stretch is seamless)
    for x in list(range(1, PATCH_MARGIN)) + list(range(sw - PATCH_MARGIN, sw - 1)):
        col = {px[x, y] for y in range(PATCH_MARGIN, sh - PATCH_MARGIN)}
        if len(col) != 1:
            problems.append(f"side band column {x} varies vertically ({len(col)} colours)")
    # top/bottom bands: every row must be constant (horizontal stretch is seamless)
    for y in list(range(1, PATCH_MARGIN)) + list(range(sh - PATCH_MARGIN, sh - 1)):
        row = {px[x, y] for x in range(PATCH_MARGIN, sw - PATCH_MARGIN)}
        if len(row) != 1:
            problems.append(f"edge band row {y} varies horizontally ({len(row)} colours)")
    # corners must be fully painted (no transparent pixels inside a corner block)
    for cx, cy in ((0, 0), (sw - PATCH_MARGIN, 0), (0, sh - PATCH_MARGIN), (sw - PATCH_MARGIN, sh - PATCH_MARGIN)):
        for y in range(cy, cy + PATCH_MARGIN):
            for x in range(cx, cx + PATCH_MARGIN):
                if px[x, y][3] != 255:
                    problems.append(f"corner block at ({cx},{cy}) has transparent pixels")
                    break
    # stretch to three sizes and confirm the corners survive untouched
    for w, h in ((sw, sh), (96, 140), (160, 220)):
        out = stretch_9slice(src, PATCH_MARGIN, w, h)
        op = out.load()
        for cx, cy, ox, oy in ((0, 0, 0, 0), (sw - PATCH_MARGIN, 0, w - PATCH_MARGIN, 0),
                               (0, sh - PATCH_MARGIN, 0, h - PATCH_MARGIN),
                               (sw - PATCH_MARGIN, sh - PATCH_MARGIN, w - PATCH_MARGIN, h - PATCH_MARGIN)):
            for y in range(PATCH_MARGIN):
                for x in range(PATCH_MARGIN):
                    if op[ox + x, oy + y] != px[cx + x, cy + y]:
                        problems.append(f"stretch {w}x{h}: corner pixel moved")
                        break
        # the stretched centre must still be flat
        cset = {op[x, y] for x in range(PATCH_MARGIN, w - PATCH_MARGIN)
                for y in range(PATCH_MARGIN, h - PATCH_MARGIN)}
        if len(cset) != 1:
            problems.append(f"stretch {w}x{h}: centre not flat ({len(cset)} colours)")
    return problems


# ---------------------------------------------------------------- gate 2: background

def check_background(img):
    problems = []
    w, h = img.size
    px = img.load()
    if w != 720 or h != 1280:
        problems.append(f"size {w}x{h} != 720x1280")
    if {px[x, y][3] for x in range(0, w, 13) for y in range(0, h, 13)} != {255}:
        problems.append("background is not fully opaque")
    bad = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c0 = px[x, y]
            if c0 != px[x + 1, y] or c0 != px[x, y + 1] or c0 != px[x + 1, y + 1]:
                bad += 1
    if bad:
        problems.append(f"{bad} 2x2 blocks are not on the pixel grid")
    # central 40% must not carry high-contrast terrain texture
    field = {px[x, y][:3] for y in list(range(0, 436, 9)) + list(range(848, h, 9))
             for x in range(144, 576, 9)}
    if field - {(107, 114, 128), (11, 13, 26)}:
        problems.append(f"central 40% carries texture: {field}")
    return problems


# ---------------------------------------------------------------- gate 3: icons

def check_icons(images):
    problems = []
    heights = {}
    for name, img in images.items():
        box = body_box(img)
        if box is None:
            problems.append(f"{name} is empty")
            continue
        h = box[3] - box[1]   # PIL bbox is exclusive on right/bottom
        heights[name] = h
        if h > ICON_BODY_MAX:
            problems.append(f"{name} body height {h} > {ICON_BODY_MAX}")
    if len(set(heights.values())) > 1:
        problems.append(f"icon body heights differ: {heights}")
    return problems, heights


# ---------------------------------------------------------------- main

def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    ui_dir = os.path.join(repo, "assets", "sprites", "ui")
    bg_dir = os.path.join(repo, "assets", "sprites", "background")
    os.makedirs(ui_dir, exist_ok=True)
    os.makedirs(bg_dir, exist_ok=True)

    built = U.build_images()
    frames = []
    for i, (name, img, w, h) in enumerate(built):
        img.save(os.path.join(ui_dir, name + ".png"))
        frames.append({"index": i, "name": name, "state": name, "state_index": i,
                       "x": i * w, "y": 0, "w": w, "h": h, "fps": 0, "loop": False})

    # review sheet: 4 icons on top, the rest below
    sheet = Image.new("RGBA", (4 * 64, 64 + 64), (0, 0, 0, 0))
    for i, (name, img, w, h) in enumerate(built[:4]):
        sheet.alpha_composite(img, (i * 64, 0))
    sheet.alpha_composite(built[4][1], (0, 64))
    sheet.save(os.path.join(ui_dir, "ui_sheet_review.png"))

    meta = {
        "unit": "ui",
        "canvas": [64, 64],
        "frames": frames,
        "palette": {k: "#%02X%02X%02X" % v for k, v in M.PAL.items() if v},
        "colors_used": 14,
        "alpha": "0 or 255 only",
        "origin": "deterministically generated by code (NOT AI-generated, NOT human-commissioned)",
        "patch_margin": PATCH_MARGIN,
        "icon_body_height_max": ICON_BODY_MAX,
    }
    with open(os.path.join(ui_dir, "ui_frames.json"), "w") as f:
        json.dump(meta, f, indent=2)

    bg = B.build_image()
    bg_path = os.path.join(bg_dir, "battlefield_720x1280.png")
    bg.save(bg_path)

    # ---- gates
    problems = []
    icons = {}
    for name, img, w, h in built:
        alphas, colours = alpha_and_colours(img)
        if not alphas <= {0, 255}:
            problems.append(f"{name}: alpha {sorted(alphas)} (soft pixels)")
        if colours > 16:
            problems.append(f"{name}: {colours} colours")
        if (img.size != (w, h)):
            problems.append(f"{name}: size {img.size}")
        if name.startswith("icon_") and name != "icon_mineral_16" and name != "icon_mineral_32":
            icons[name] = img
    p, heights = check_icons(icons)
    problems += p
    frame = built[4][1]
    problems += check_nine_slice(frame)
    problems += check_background(bg)
    # badges must be fully opaque
    for name, img, w, h in built:
        if name.startswith("card_badge"):
            if {img.convert("RGBA").getpixel((x, y))[3] for x in range(w) for y in range(h)} != {255}:
                problems.append(f"{name}: base is not opaque")

    if problems:
        print("BATCH GATE FAIL:")
        for p_ in problems:
            print("  -", p_)
        raise SystemExit(1)
    print("ui batch: %d sprites + background exported; gates PASS" % len(built))
    print("icon body heights:", heights)


if __name__ == "__main__":
    main()
