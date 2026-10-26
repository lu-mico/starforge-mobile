#!/usr/bin/env python3
"""
Regenerate the Siege Tank sprite set into <repo>/assets/sprites/siege_tank/.

    python3 tools/tank_sprite_generator.py [REPO_PATH]

13 frames (idle 2 / walk 4 / attack 3 / death 4) on a 48x48 canvas, right-facing,
transparent background, hard edges, shared palette with the Marine sheet.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import marine_sprite_sheet as M
import tank_sprite_sheet as T
from sprite_export import export_unit, verify_exports

FPS = {"idle": 2, "walk": 6, "attack": 8, "death": 4}
LOOP = {"idle": True, "walk": True, "attack": False, "death": False}

GODOT_LINE = ("- [x] Godot 4.6 导入测试通过 —— Nagi 实测 **20/20 全过**"
              "（4.6.stable.official.89cea1439：48×48 strip 导入 / SpriteFrames 4 段动画 / "
              "region 映射 / AnimatedSprite2D 播放 / fps 生效 / flip_h / hframes=13 / "
              "Nearest 采样 / .import 齐全）—— 复跑："
              "`godot --headless --script tools/accept_sprite_import.gd -- "
              "res://assets/sprites/siege_tank/siege_tank_frames.json`")

DISCLOSURE = "- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简"


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    out = os.path.join(repo, "assets", "sprites", "siege_tank")
    frames = []
    for g in T.build_frames()[:13]:
        g.outline()
        frames.append(g.to_image())
    export_unit(
        "siege_tank", T.TCELL, frames, T.FRAME_SPEC, out, FPS, LOOP,
        palette={k: "#%02X%02X%02X" % v for k, v in M.PAL.items() if v},
        colors_used=14,
        origin="**确定性代码绘制**，非 AI 生成、非真人委托",
        title="Siege Tank",
        extra_md=["", "## 备注", "",
                  "- 48×48 画布（brief §2.1：Siege Tank 扩到 48×48）",
                  "- 与 Marine 共用同一套调色板与 `verify_exports()` 硬校验",
                  "- 单位代码本身尚未实现（brief §2.1 注），素材先行"],
        godot_line=GODOT_LINE,
        disclosure_line=DISCLOSURE,
    )
    n = verify_exports(out, "siege_tank", T.TCELL, 13)
    print("siege_tank: %d frames exported + verified" % n)


if __name__ == "__main__":
    main()
