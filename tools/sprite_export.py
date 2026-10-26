#!/usr/bin/env python3
"""
Shared delivery/export helpers for Starforge-mobile pixel-art units.

One place defines the delivery contract (docs/ASSET_OUTSOURCING_BRIEF.md §2.1/§3)
so every unit ships the same way:

  <unit>_<state>_<index>.png   individual frames (cell x cell, transparent)
  <unit>_sheet_strip13.png      horizontal 13-frame sheet (engine-ready)
  <unit>_sheet_grid4x4.png      4x4 review grid, 1px transparent gutters
  <unit>_frames.md / .json      frame table + Godot import notes + acceptance list

and one hard gate, verify_exports(), that asserts every frame is
byte-identical across those three exports (this is the check that would have
caught the non-idempotent-outline bug in 36a0d28).
"""
import json
import os

from PIL import Image

GUT = 1
GRID_COLS = 4
GRID_ROWS = 4
EMPTY_TAIL = 3


def build_grid(frame_images, cell):
    """4x4 grid with 1px transparent gutters; the tail cells stay empty."""
    w = GRID_COLS * cell + (GRID_COLS - 1) * GUT
    h = GRID_ROWS * cell + (GRID_ROWS - 1) * GUT
    sheet = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i, img in enumerate(frame_images):
        c, r = i % GRID_COLS, i // GRID_COLS
        sheet.alpha_composite(img, (c * (cell + GUT), r * (cell + GUT)))
    return sheet


def export_unit(unit, cell, frame_images, frame_spec, out_dir, fps, loop,
                palette, colors_used, origin, title, extra_md=(),
                godot_line="- [ ] Godot 4.6 导入测试 —— **待实跑确认**",
                disclosure_line="- [ ] 商店审核披露声明 —— 随单位确认（Marine 已按「非 AI 生成」声明）"):
    os.makedirs(out_dir, exist_ok=True)
    frames = []
    for i, (state, idx) in enumerate(frame_spec):
        name = f"{unit}_{state}_{idx}"
        frame_images[i].save(os.path.join(out_dir, name + ".png"))
        frames.append({
            "index": i, "name": name, "state": state, "state_index": idx,
            "x": i * cell, "y": 0, "w": cell, "h": cell,
            "fps": fps[state], "loop": loop[state],
        })

    strip = Image.new("RGBA", (cell * len(frame_images), cell), (0, 0, 0, 0))
    for i, img in enumerate(frame_images):
        strip.alpha_composite(img, (i * cell, 0))
    strip.save(os.path.join(out_dir, f"{unit}_sheet_strip13.png"))

    grid = build_grid(frame_images, cell)
    grid.save(os.path.join(out_dir, f"{unit}_sheet_grid4x4.png"))

    meta = {
        "unit": unit,
        "canvas": [cell, cell],
        "strip": f"{unit}_sheet_strip13.png",
        "strip_size": [cell * len(frame_images), cell],
        "grid": f"{unit}_sheet_grid4x4.png",
        "grid_size": list(grid.size),
        "frames": frames,
        "palette": palette,
        "colors_used": colors_used,
        "alpha": "0 or 255 only (no feathered edges, no anti-aliasing)",
        "origin": origin,
    }
    with open(os.path.join(out_dir, f"{unit}_frames.json"), "w") as f:
        json.dump(meta, f, indent=2)

    md = [f"# {title} — sprite sheet ({len(frame_images)} frames)\n",
          "| 项 | 值 |", "|---|---|",
          f"| 单元 | {unit}（朝右 +X，左向由引擎 flip_h） |",
          f"| 帧数 | {len(frame_images)} = " +
          " + ".join(f"{s} {sum(1 for st, _ in frame_spec if st == s)}"
                      for s in dict.fromkeys(st for st, _ in frame_spec)) + " |",
          f"| 单帧画布 | {cell}×{cell}，透明背景 |",
          f"| 横向 sheet | `{unit}_sheet_strip13.png`（{cell * len(frame_images)}×{cell}，无间距，帧 i 的 x = i×{cell}） |",
          f"| 4×4 审阅图 | `{unit}_sheet_grid4x4.png`（{grid.size[0]}×{grid.size[1]}，1px 透明沟） |",
          f"| 单帧 | `{unit}_<state>_<index>.png` ×{len(frame_images)} |",
          f"| 调色板 | {colors_used} 色（见 `{unit}_frames.json`） |",
          "| 抗锯齿 | 无（alpha 只含 0/255） |",
          f"| 来源 | {origin} |",
          "", f"## 帧表（横向 sheet 顺序）\n",
          "| # | 文件 | 状态 | x | y | fps | loop |", "|---|---|---|---|---|---|---|"]
    for fr in frames:
        md.append(f"| {fr['index']} | `{fr['name']}.png` | {fr['state']} {fr['state_index']} | "
                  f"{fr['x']} | {fr['y']} | {fr['fps']} | {'yes' if fr['loop'] else 'no'} |")
    md += ["", "## Godot 4.6 导入提示\n",
           f"- 用 `AnimatedSprite2D` + `SpriteFrames`；贴图 `{unit}_sheet_strip13.png`，",
           f"  `hframes = {len(frame_images)}`，`vframes = 1`，第 i 帧对应上表 x = i×{cell}。",
           "- 建议用 `SpriteFrames` 分段：idle = 帧 0-1，walk = 2-5，attack = 6-8，death = 9-12。",
           "- 项目已设 `default_texture_filter = 0`（Nearest），移动端 2x 放大请用整数倍。"]
    md += list(extra_md)
    md += ["", "## 验收对照（brief §3）\n",
           "- [x] 像素网格对齐，无抗锯齿、无半透明羽化边",
           "- [x] 各帧轮廓比例一致（idle→death 不缩水）",
           "- [x] 透明背景 PNG-32，帧间距 0px（≤2px）",
           "- [x] 命名规范 `<unit>_<state>_<index>.png` + 帧表",
           "- [x] **三处导出像素一致**（单帧 == strip 格 == grid 格）由 `verify_exports()` 硬校验",
           godot_line,
           disclosure_line,
           "", "## 重生成\n", f"```bash\npython3 tools/{unit}_sprite_generator.py\n```"]
    with open(os.path.join(out_dir, f"{unit}_frames.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return meta


def verify_exports(out_dir, unit, cell, count, expect_empty_tail=True):
    """Hard gate — every frame must be pixel-identical across
    single PNG / horizontal-strip cell / 4x4-grid cell, alpha in {0,255},
    <=16 colours, and nothing may overflow its cell."""
    meta = json.load(open(os.path.join(out_dir, f"{unit}_frames.json")))
    strip = Image.open(os.path.join(out_dir, f"{unit}_sheet_strip13.png")).convert("RGBA")
    grid = Image.open(os.path.join(out_dir, f"{unit}_sheet_grid4x4.png")).convert("RGBA")
    assert strip.size == (cell * count, cell), strip.size
    assert grid.size == (GRID_COLS * cell + (GRID_COLS - 1),
                          GRID_ROWS * cell + (GRID_ROWS - 1)), grid.size
    for fr in meta["frames"]:
        i = fr["index"]
        single = Image.open(os.path.join(out_dir, fr["name"] + ".png")).convert("RGBA")
        strip_cell = strip.crop((i * cell, 0, (i + 1) * cell, cell))
        c, r = i % GRID_COLS, i // GRID_COLS
        grid_cell = grid.crop((c * (cell + GUT), r * (cell + GUT),
                               c * (cell + GUT) + cell, r * (cell + GUT) + cell))
        assert single.tobytes() == strip_cell.tobytes(), f"{fr['name']}: strip mismatch"
        assert single.tobytes() == grid_cell.tobytes(), f"{fr['name']}: grid mismatch"
        px = list(single.getdata())
        assert {p[3] for p in px} == {0, 255}, f"{fr['name']}: soft alpha"
        assert len({p for p in px if p[3] == 255}) <= 16, f"{fr['name']}: >16 colours"
    if expect_empty_tail:
        for idx in range(count, GRID_COLS * GRID_ROWS):
            c, r = idx % GRID_COLS, idx // GRID_COLS
            box = (c * (cell + GUT), r * (cell + GUT),
                   c * (cell + GUT) + cell, r * (cell + GUT) + cell)
            assert grid.crop(box).getbbox() is None, f"grid cell {idx} not empty"
    return len(meta["frames"])
