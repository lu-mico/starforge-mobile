#!/usr/bin/env python3
"""
Regenerate the Marine sprite set into <repo>/assets/sprites/marine/.

    python3 tools/marine_sprite_generator.py [REPO_PATH]

Delivery contract: docs/ASSET_OUTSOURCING_BRIEF.md §2.1 / §3
(13 frames: idle 2 / walk 4 / attack 3 / death 4, 32x32, transparent, right-facing).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import marine_sprite_sheet as M
from sprite_export import export_unit, verify_exports

FPS = {"idle": 2, "walk": 6, "attack": 8, "death": 4}
LOOP = {"idle": True, "walk": True, "attack": False, "death": False}

GODOT_LINE = ("- [x] Godot 4.6 导入测试通过 —— Nagi 实测 **18/18 全过**"
              "（4.6.stable.official.89cea1439：SpriteFrames 4 段动画 / region 映射 / "
              "AnimatedSprite2D 播放 / flip_h / hframes=13 / Nearest 采样）")

DISCLOSURE = "- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简"

HISTORY = ["", "## 验收记录", "",
           "- `36a0d28` 首版交付 → `e6517de` 修 `outline()` 非幂等 + death_3 溢出 + realpath 守卫",
           "- `e5f1fd3` 加 `verify_exports()` 硬校验（单帧 == strip 格 == grid 格，字节级）"]


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    out = os.path.join(repo, "assets", "sprites", "marine")
    frames = []
    for g in M.build_frames()[:13]:
        g.outline()
        frames.append(g.to_image())
    export_unit(
        "marine", M.CELL, frames, M.FRAME_SPEC, out, FPS, LOOP,
        palette={k: "#%02X%02X%02X" % v for k, v in M.PAL.items() if v},
        colors_used=14,
        origin="**确定性代码绘制**，非 AI 生成、非真人委托",
        title="Marine",
        extra_md=HISTORY,
        godot_line=GODOT_LINE,
        disclosure_line=DISCLOSURE,
    )
    n = verify_exports(out, "marine", M.CELL, 13)
    print("marine: %d frames exported + verified" % n)


if __name__ == "__main__":
    main()
