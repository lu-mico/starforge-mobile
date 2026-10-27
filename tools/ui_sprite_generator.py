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
  assets/sprites/ui/ui_sheet_review.png    256x128 review sheet
  assets/sprites/ui/ui_frames.json         manifest (same shape as towers)
  assets/sprites/background/battlefield_720x1280.png

Then runs the batch gate.  EVERY gate measures the EXPORTED PNG that was just
written to disk (never the generator's own constants), so a gate can actually
fail on a broken export:

  G0  hygiene        alpha {0,255}, <= 16 opaque colours, expected canvas size
  G1  9-slice        patch_margin stretched to 3 sizes without a seam
  G2  background     exact 2x pixel grid, opaque, no faction hue, central 40%
                     texture free
  G3  icon height    icon body height measured, identical across the 4 icons
  G4  background     EXACT vertical mirror: row y == row 1279-y, 0 differing px
  G5  icon geometry  bbox rows 12..51, widths 36/42/46/52, centred with
                     >= 6px margin, transparent canvas border, complete ink ring
  G6  mineral_16     <= 3 opaque colours, no 1px feature rows/cols, >= 1px
                     margin, complete ink ring, still differs from a NEAREST
                     32->16 downscale in >= 20% of the pixels
  G7  badges         all 144 px opaque, every border px is ink, the three
                     badges stay > 20 differing pixels apart

Exits 1 if any gate fails.
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

INK = (11, 13, 26)          # palette 'K' - the ink outline colour

# ---- G5 targets: the EXPORTED (post-ink-ring) opaque bbox of every card icon
ICON_TARGET_W = {
    "icon_marine": 36,
    "icon_marauder": 42,
    "icon_hellion": 46,
    "icon_siege_tank": 52,
}
ICON_ROW_TOP = 12
ICON_ROW_BOT = 51
ICON_MIN_MARGIN = 6

# ---- G6 targets
MINERAL16_MAX_COLOURS = 3
MINERAL16_MIN_MARGIN = 1
MINERAL16_MIN_DIFF = 0.20      # vs a NEAREST 32->16 downscale

# ---- G7 targets
BADGE_MIN_PAIR_DIFF = 20

# Saturated faction hues (blue + orange).  The background must not contain any
# of them: spec §4 reserves blue/orange for units and towers, so a "neutral
# blue-grey" tower base is still a unit colour.
FACTION_HUES = {
    (42, 63, 102), (47, 74, 122), (79, 124, 192), (143, 184, 232),
    (255, 138, 31), (255, 196, 77), (255, 224, 138),
}

# ---- manifest strip layout (a real horizontal strip, no overlapping frames)
STRIP_LAYOUT = [
    ("icon_marine", 0, 64, 64),
    ("icon_marauder", 64, 64, 64),
    ("icon_hellion", 128, 64, 64),
    ("icon_siege_tank", 192, 64, 64),
    ("card_frame", 256, 48, 64),
    ("icon_mineral_32", 304, 32, 32),
    ("icon_mineral_16", 336, 16, 16),
    ("card_badge_cost", 352, 12, 12),
    ("card_badge_count", 364, 12, 12),
    ("card_badge_frame", 376, 12, 12),
]


# ---------------------------------------------------------------- helpers

def alpha_and_colours(img):
    px = list(img.convert("RGBA").getdata())
    alphas = {p[3] for p in px}
    colours = len({p for p in px if p[3] == 255})
    return alphas, colours


def body_box(img):
    p = img.convert("RGBA").getbbox()
    return p


def opaque_bbox(img):
    """Inclusive (x0, y0, x1, y1) of the opaque pixels, or None when empty."""
    px = img.load()
    w, h = img.size
    x0 = y0 = None
    x1 = y1 = None
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 255:
                if x0 is None or x < x0:
                    x0 = x
                if x1 is None or x > x1:
                    x1 = x
                if y0 is None or y < y0:
                    y0 = y
                if y1 is None or y > y1:
                    y1 = y
    if x0 is None:
        return None
    return (x0, y0, x1, y1)


def border_pixels(img):
    """Every pixel that sits on the canvas border (corners counted twice)."""
    px = img.load()
    w, h = img.size
    out = []
    for x in range(w):
        out.append((x, 0, px[x, 0]))
        out.append((x, h - 1, px[x, h - 1]))
    for y in range(h):
        out.append((0, y, px[0, y]))
        out.append((w - 1, y, px[w - 1, y]))
    return out


def ink_ring_violations(img):
    """Opaque pixels that touch a transparent pixel without being ink."""
    px = img.load()
    w, h = img.size
    bad = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 255:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    continue                       # outside the canvas
                if px[nx, ny][3] == 0:
                    if px[x, y][:3] != INK:
                        bad.append((x, y))
                    break
    return bad


def runs(bools):
    """Lengths of the maximal True runs in a list of booleans."""
    out = []
    n = 0
    for b in bools:
        if b:
            n += 1
        elif n:
            out.append(n)
            n = 0
    if n:
        out.append(n)
    return out


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
    right = src.crop((sw - margin, margin, sw - margin, sh - margin)).resize((margin, h - 2 * margin), Image.NEAREST)
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
    hue = {px[x, y][:3] for x in range(0, w, 7) for y in range(0, h, 7)}
    leaked = hue & FACTION_HUES
    if leaked:
        problems.append(f"background contains unit faction hues: {sorted(leaked)}")
    bad = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c0 = px[x, y]
            if c0 != px[x + 1, y] or c0 != px[x, y + 1] or c0 != px[x + 1, y + 1]:
                bad += 1
    if bad:
        problems.append(f"{bad} 2x2 blocks are not on the pixel grid")
    # the engine's lane band must be lane surface, with the ground line on lane_y
    for y in (LANE_TOP, LANE_BOT):
        if px[360, y][:3] != LANE_SURFACE:
            problems.append(f"lane surface missing at y={y}")
    if px[360, LANE_GROUND_Y][:3] != LANE_GROUND:
        problems.append(f"ground line is not on lane_y={LANE_GROUND_Y}")
    # central 40% must not carry high-contrast terrain texture
    # the lane band is the battle area and belongs there; the clean rule
    # applies to the terrain above and below it
    field = {px[x, y][:3] for y in list(range(0, LANE_TOP - 4, 9)) + list(range(LANE_BOT + 5, h, 9))
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


# engine-pinned lane geometry (must match tools/background_sprite_sheet.py
# and the engine's main.tscn lane_y)
LANE_TOP, LANE_BOT = 620, 659
LANE_GROUND_Y = 640
LANE_SURFACE = (170, 179, 194)
LANE_GROUND = (16, 24, 32)


# ---------------------------------------------------------------- gate 4: mirror

def check_background_mirror(img):
    """EXACT vertical mirror: row y must equal row h-1-y for EVERY pixel.

    No exclusions. The lane band, the ground line, the tower pads and the
    approach marks are all self-mirroring pairs about the image centre, so
    the whole 720x1280 image satisfies this with 0 differing pixels.
    """
    problems = []
    w, h = img.size
    px = img.load()
    diff = 0
    first = None
    for y in range(h // 2):
        my = h - 1 - y
        for x in range(w):
            if px[x, y] != px[x, my]:
                diff += 1
                if first is None:
                    first = (x, y)
    if diff:
        problems.append(
            f"{diff} px differ between row y and row {h - 1}-y (first at {first})")
    return problems, diff


# ---------------------------------------------------------------- gate 5: geometry

def check_icon_geometry(images):
    problems = []
    for name in ICON_TARGET_W:
        img = images[name]
        w, h = img.size
        box = opaque_bbox(img)
        if box is None:
            problems.append(f"{name}: is empty")
            continue
        x0, y0, x1, y1 = box
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if (y0, y1) != (ICON_ROW_TOP, ICON_ROW_BOT):
            problems.append(
                f"{name}: body rows {y0}..{y1} != {ICON_ROW_TOP}..{ICON_ROW_BOT}")
        if bh != ICON_BODY_MAX:
            problems.append(f"{name}: body height {bh} != {ICON_BODY_MAX}")
        if bw != ICON_TARGET_W[name]:
            problems.append(f"{name}: body width {bw} != {ICON_TARGET_W[name]}")
        left, right = x0, w - 1 - x1
        if left != right:
            problems.append(f"{name}: not horizontally centred (left {left} / right {right})")
        if min(left, right) < ICON_MIN_MARGIN:
            problems.append(
                f"{name}: margin {min(left, right)} < {ICON_MIN_MARGIN}px")
        clipped = [b for b in border_pixels(img) if b[2][3] == 255]
        if clipped:
            problems.append(
                f"{name}: {len(clipped)} opaque px on the canvas border (clipped art)")
        bad = ink_ring_violations(img)
        if bad:
            problems.append(
                f"{name}: {len(bad)} px touch transparency without an ink outline")
    return problems


# ---------------------------------------------------------------- gate 6: mineral 16

def check_mineral16(img16, img32):
    problems = []
    w, h = img16.size
    px = img16.load()
    opaque = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 255]
    if not opaque:
        return ["icon_mineral_16: is empty"], 0
    colours = {px[x, y][:3] for x, y in opaque}
    if len(colours) > MINERAL16_MAX_COLOURS:
        problems.append(
            f"icon_mineral_16: {len(colours)} opaque colours > {MINERAL16_MAX_COLOURS}")
    xs = [p[0] for p in opaque]
    ys = [p[1] for p in opaque]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    margins = (x0, y0, w - 1 - x1, h - 1 - y1)
    if min(margins) < MINERAL16_MIN_MARGIN:
        problems.append(
            f"icon_mineral_16: margins L/T/R/B {margins} < {MINERAL16_MIN_MARGIN}px")
    # no 1px-wide / 1px-tall feature runs
    for y in range(y0, y1 + 1):
        if 1 in runs([px[x, y][3] == 255 for x in range(x0, x1 + 1)]):
            problems.append(f"icon_mineral_16: row {y} has a 1px-wide opaque run")
    for x in range(x0, x1 + 1):
        if 1 in runs([px[x, y][3] == 255 for y in range(y0, y1 + 1)]):
            problems.append(f"icon_mineral_16: column {x} has a 1px-tall opaque run")
    bad = ink_ring_violations(img16)
    if bad:
        problems.append(
            f"icon_mineral_16: {len(bad)} px touch transparency without an ink outline")
    # must still be a hand-drawn crystal, not a rescaled 32
    down = img32.convert("RGBA").resize((w, h), Image.NEAREST)
    dp = down.load()
    diff = sum(1 for y in range(h) for x in range(w) if dp[x, y] != px[x, y])
    pct = diff / float(w * h)
    if pct < MINERAL16_MIN_DIFF:
        problems.append(
            f"icon_mineral_16: only {pct * 100:.1f}% differs from the 32->16 downscale")
    return problems, diff


# ---------------------------------------------------------------- gate 7: badges

def check_badges(images):
    problems = []
    for name, img in images.items():
        w, h = img.size
        px = img.load()
        soft = sum(1 for y in range(h) for x in range(w) if px[x, y][3] != 255)
        if soft:
            problems.append(f"{name}: {soft} px are not fully opaque")
        border = border_pixels(img)
        nonink = [b for b in border if b[2][:3] != INK]
        if nonink:
            problems.append(
                f"{name}: {len(nonink)} border px are not ink (no contour)")
    names = sorted(images)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = images[names[i]].convert("RGBA")
            b = images[names[j]].convert("RGBA")
            w, h = a.size
            ap, bp = a.load(), b.load()
            d = sum(1 for y in range(h) for x in range(w) if ap[x, y] != bp[x, y])
            if d <= BADGE_MIN_PAIR_DIFF:
                problems.append(
                    f"{names[i]} vs {names[j]}: only {d} differing px "
                    f"(> {BADGE_MIN_PAIR_DIFF} required)")
    return problems


# ---------------------------------------------------------------- main

def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    ui_dir = os.path.join(repo, "assets", "sprites", "ui")
    bg_dir = os.path.join(repo, "assets", "sprites", "background")
    os.makedirs(ui_dir, exist_ok=True)
    os.makedirs(bg_dir, exist_ok=True)

    built = U.build_images()
    by_name = {name: img for name, img, _w, _h in built}
    sizes = {name: (w, h) for name, _img, w, h in built}

    for name, img, w, h in built:
        img.save(os.path.join(ui_dir, name + ".png"))

    # review sheet: 4 icons on top, the rest below (256x128)
    sheet = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    for i, name in enumerate(("icon_marine", "icon_marauder",
                              "icon_hellion", "icon_siege_tank")):
        sheet.alpha_composite(by_name[name], (i * 64, 0))
    sheet.alpha_composite(by_name["card_frame"], (0, 64))
    sheet.alpha_composite(by_name["icon_mineral_32"], (48, 64))
    sheet.alpha_composite(by_name["icon_mineral_16"], (80, 64))
    sheet.alpha_composite(by_name["card_badge_cost"], (96, 64))
    sheet.alpha_composite(by_name["card_badge_count"], (108, 64))
    sheet.alpha_composite(by_name["card_badge_frame"], (120, 64))
    sheet.save(os.path.join(ui_dir, "ui_sheet_review.png"))

    # manifest: a real horizontal strip, 4 icons at a 64px pitch, then the
    # remaining sprites at their own widths.
    frames = []
    for i, (name, x, w, h) in enumerate(STRIP_LAYOUT):
        assert sizes[name] == (w, h), (name, sizes[name], (w, h))
        frames.append({"index": i, "name": name, "state": name, "state_index": i,
                       "x": x, "y": 0, "w": w, "h": h, "fps": 0, "loop": False})

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

    # ------------------------------------------------------------------
    # Gates.  Every gate re-opens the EXPORTED PNG from disk, so a broken
    # export is caught even if the generator's own constants look fine.
    # ------------------------------------------------------------------
    exported = {}
    for name, _img, w, h in built:
        exported[name] = Image.open(os.path.join(ui_dir, name + ".png")).convert("RGBA")
    bg_exported = Image.open(bg_path).convert("RGBA")

    icons = {n: exported[n] for n in ICON_TARGET_W}
    badges = {n: exported[n] for n in
              ("card_badge_cost", "card_badge_count", "card_badge_frame")}

    gates = []          # (id, label, problems)

    # G0 - hygiene: alpha {0,255}, <=16 colours, canvas size
    probs = []
    for name, _img, w, h in built:
        img = exported[name]
        alphas, colours = alpha_and_colours(img)
        if not alphas <= {0, 255}:
            probs.append(f"{name}: alpha {sorted(alphas)} (soft pixels)")
        if colours > 16:
            probs.append(f"{name}: {colours} colours")
        if img.size != (w, h):
            probs.append(f"{name}: size {img.size} != {(w, h)}")
    gates.append(("G0", "hygiene (alpha/16 colours/size)", probs))

    # G1 - 9-slice stretch
    gates.append(("G1", "9-slice stretch at 3 sizes",
                  check_nine_slice(exported["card_frame"])))

    # G2 - background 2x grid
    gates.append(("G2", "background 2x grid / opaque / no faction hue",
                  check_background(bg_exported)))

    # G3 - icon body heights
    probs, heights = check_icons(icons)
    gates.append(("G3", "icon body heights equal and <= %d" % ICON_BODY_MAX, probs))

    # G4 - exact vertical mirror of the background
    probs, mirror_diff = check_background_mirror(bg_exported)
    gates.append(("G4", "background EXACT vertical mirror", probs))

    # G5 - icon geometry integrity
    gates.append(("G5", "icon geometry (bbox/width/margin/ink ring)",
                  check_icon_geometry(icons)))

    # G6 - mineral 16
    probs, m16_diff = check_mineral16(exported["icon_mineral_16"],
                                      exported["icon_mineral_32"])
    gates.append(("G6", "mineral_16 (colours/1px runs/ink ring/downscale)", probs))

    # G7 - badges
    gates.append(("G7", "badges (opaque/ink border/pairwise)",
                  check_badges(badges)))

    failed = 0
    for gid, label, probs in gates:
        if probs:
            failed += 1
            print("GATE %-3s %-46s FAIL" % (gid, label))
            for p_ in probs:
                print("        - %s" % p_)
        else:
            print("GATE %-3s %-46s PASS" % (gid, label))

    print("mirror diff px: %d | mineral_16 vs 32->16 downscale: %d px | "
          "icon body heights: %s" % (mirror_diff, m16_diff, heights))

    if failed:
        print("BATCH GATE FAIL: %d gate(s) failed" % failed)
        raise SystemExit(1)
    print("ui batch: %d sprites + background exported; all %d gates PASS"
          % (len(built), len(gates)))


if __name__ == "__main__":
    main()
