#!/usr/bin/env python3
"""
Starforge sprite pipeline QA — reusable for EVERY unit
(Marine / Hellion / Marauder / Siege Tank).

Art-source agnostic: works on any generator that follows the
"<module>.py drawing module + generator" pattern.

Checks
  1. rasterizer self-test  — Ops.rect(x0,y0,x1,y1) must land exactly on pixels
                             x0..x1, y0..y1. A half-pixel convention mismatch in
                             fill_poly silently shifts every shape by 1px and
                             pushes the silhouette off the cell.
  2. crop report           — per frame: pixels the 32x32 cell cannot hold.
                             Re-renders the pose into a padded canvas and diffs
                             against the real 32x32 output, so art that is drawn
                             off-canvas is REPORTED, not silently cropped.
  3. export consistency    — single PNG == strip cell == grid cell, byte for byte.
  4. colour/alpha hygiene  — alpha in {0,255}, <= 16 opaque colours.

Usage
  python3 tools/sprite_qa.py tools/marine_sprite_sheet.py assets/sprites/marine

Exit code 0 = all hard checks pass, 1 = FAIL.
"""
import importlib.util
import json
import os
import sys

from PIL import Image

OFF = 8          # pad used when re-rendering to reveal off-canvas art
MAX_COLOURS = 16


def load_module(path):
    spec = importlib.util.spec_from_file_location("sheet_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 1. self-test

def rasterizer_self_test(mod):
    """Ops.rect(x0,y0,x1,y1) is documented as pixel-inclusive (x0..x1, y0..y1).
    If fill_poly samples at the wrong half-pixel, the whole sheet drifts."""
    grid = mod.Grid()
    ops = mod.Ops()
    ops.rect(5, 5, 7, 7, 'B')
    _, (pts, color) = ops.items[0]
    mod.fill_poly(grid, pts, color)
    got = sorted(grid.px.keys())
    want = sorted((x, y) for x in range(5, 8) for y in range(5, 8))
    return got == want, got, want


# ---------------------------------------------------------------- 2. crop report

def _render_frames(mod, padded, cell=32):
    """Render every frame. padded=True re-renders into a bigger canvas with the
    drawing shifted, so pixels that fall outside the cell become visible
    instead of being silently dropped.

    The shift is applied AFTER the frame transform (so rotated poses are not
    re-rotated about a shifted pivot) and the canvas grows by 2*OFF."""
    orig_render = mod.render
    if padded:
        def padded_render(ops, tf=None, w=None, h=None):
            ident = getattr(mod, 'T_identity', None)
            base_tf = tf if tf is not None else (ident() if ident else (lambda x, y: (x, y)))
            def shifted_tf(x, y):
                sx, sy = base_tf(x, y)
                return (sx + OFF, sy + OFF)
            return orig_render(ops, shifted_tf, cell + 2 * OFF, cell + 2 * OFF)
        mod.render = padded_render
    try:
        frames = mod.build_frames()
    finally:
        mod.render = orig_render
    return frames


def crop_report(mod, cell=32):
    """-> list of (frame_name, [(x, y), ...]) for art the cell cannot hold."""
    real = _render_frames(mod, padded=False, cell=cell)
    padded = _render_frames(mod, padded=True, cell=cell)
    spec = getattr(mod, "FRAME_SPEC", [])
    report = []
    for i, (state, idx) in enumerate(spec):
        if i >= len(real) or i >= len(padded):
            break
        g_real, g_pad = real[i], padded[i]
        if g_real is None or g_pad is None:
            continue
        real_px = set(g_real.px.keys())
        lost = []
        for (x, y) in g_pad.px:
            ox, oy = x - OFF, y - OFF
            if not (0 <= ox < cell and 0 <= oy < cell):
                lost.append((ox, oy))
            elif (ox, oy) not in real_px:
                lost.append((ox, oy))
        report.append((f"{state}_{idx}", sorted(lost)))
    return report


# ---------------------------------------------------------------- 3./4. exports

def export_checks(out_dir, meta):
    meta_path = os.path.join(out_dir, meta)
    with open(meta_path) as fh:
        data = json.load(fh)
    frames = data["frames"]
    strip = Image.open(os.path.join(out_dir, data["strip"])).convert("RGBA")
    grid = None
    if data.get("grid"):
        grid = Image.open(os.path.join(out_dir, data["grid"])).convert("RGBA")

    consistency, hygiene = [], []
    for fr in frames:
        name = fr["name"]
        single = Image.open(os.path.join(out_dir, name + ".png")).convert("RGBA")
        strip_cell = strip.crop((fr["x"], fr["y"], fr["x"] + fr["w"], fr["y"] + fr["h"]))
        if single.tobytes() != strip_cell.tobytes():
            consistency.append(f"{name}: strip mismatch")
        if grid is not None:
            # the review grid is always 4 columns wide; derive the column
            # count from the GRID width (the strip is a different length).
            cols = max(1, round((grid.width + 1) / (fr["w"] + 1)))
            r = fr["index"] // cols
            c = fr["index"] % cols
            gx, gy = c * (fr["w"] + 1), r * (fr["h"] + 1)
            grid_cell = grid.crop((gx, gy, gx + fr["w"], gy + fr["h"]))
            if single.tobytes() != grid_cell.tobytes():
                consistency.append(f"{name}: grid mismatch")
        px = list(single.getdata())
        alphas = {p[3] for p in px}
        if not alphas <= {0, 255}:
            hygiene.append(f"{name}: soft alpha {sorted(alphas)}")
        colours = len({p for p in px if p[3] == 255})
        if colours > MAX_COLOURS:
            hygiene.append(f"{name}: {colours} colours > {MAX_COLOURS}")
    return consistency, hygiene


# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    module_path, out_dir = sys.argv[1], sys.argv[2]
    unit = os.path.basename(os.path.abspath(out_dir))
    meta = sys.argv[3] if len(sys.argv) > 3 else f"{unit}_frames.json"
    mod = load_module(module_path)
    cell = 32
    try:
        with open(os.path.join(out_dir, meta)) as fh:
            cell = json.load(fh)["canvas"][0]
    except Exception:
        pass

    hard_fail = False

    print("1. rasterizer self-test")
    ok, got, want = rasterizer_self_test(mod)
    if ok:
        print("   PASS  Ops.rect(5,5,7,7) rasterizes to exactly (5..7, 5..7)")
    else:
        hard_fail = True
        print("   FAIL  Ops.rect(5,5,7,7) rasterizes to "
              f"{sorted({p[0] for p in got})}, {sorted({p[1] for p in got})}")
        print("         expected (5..7, 5..7) — fill_poly samples at the wrong")
        print("         half-pixel, so every shape is drawn 1px off its declared")
        print("         rect and the silhouette hangs off the 32x32 cell.")

    print(f"\n2. crop report (art the {cell}x{cell} cell cannot hold)")
    report = crop_report(mod, cell)
    total = 0
    for name, lost in report:
        if lost:
            total += len(lost)
            rows = sorted({y for _, y in lost})
            cols = sorted({x for x, _ in lost})
            print(f"   {name:<10} {len(lost):>3} px cropped  rows {rows}  cols {cols}")
    print(f"   TOTAL cropped pixels: {total}")

    print("\n3. export consistency")
    consistency, hygiene = export_checks(out_dir, meta)
    if consistency:
        hard_fail = True
        for line in consistency:
            print("   FAIL  " + line)
    else:
        print("   PASS  single PNG == strip cell == grid cell, byte for byte")

    print("\n4. colour / alpha hygiene")
    if hygiene:
        hard_fail = True
        for line in hygiene:
            print("   FAIL  " + line)
    else:
        print("   PASS  alpha in {0,255}, <= 16 opaque colours")

    print("\n=> " + ("FAIL" if hard_fail else "PASS"))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
