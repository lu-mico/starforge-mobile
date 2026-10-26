#!/usr/bin/env python3
"""
Regenerate the Marauder sprite set into <repo>/assets/sprites/marauder/.

    python3 tools/marauder_sprite_generator.py [REPO_PATH]

13 frames (idle 2 / walk 4 / attack 3 / death 4) on a 32x32 canvas, right-facing,
transparent background, hard edges, shared palette with the Marine sheet.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import marine_sprite_sheet as M
import marauder_sprite_sheet as T
from sprite_export import export_unit, verify_exports

FPS = {"idle": 2, "walk": 6, "attack": 8, "death": 4}
LOOP = {"idle": True, "walk": True, "attack": False, "death": False}

GODOT_LINE = "- [ ] Godot 4.6 导入测试 —— **待实跑确认**（用 tools/accept_sprite_import.gd 一键复现）"
DISCLOSURE = "- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简"


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    out = os.path.join(repo, "assets", "sprites", "marauder")
    frames = []
    for g in T.build_frames()[:13]:
        g.outline()
        frames.append(g.to_image())
    export_unit(
        "marauder", T.CELL, frames, T.FRAME_SPEC, out, FPS, LOOP,
        palette={k: "#%02X%02X%02X" % v for k, v in M.PAL.items() if v},
        colors_used=14,
        origin="**确定性代码绘制**，非 AI 生成、非真人委托",
        title="Marauder",
        extra_md=["", "## 备注", "",
                  "- 重甲变体：钢灰装甲 + 肩扛炮（Marine 是蓝甲 + 步枪），剪影更宽更矮壮",
                  "- 与 Marine 共用同一套调色板（全局 ≤16 色）与 `verify_exports()` 硬校验"],
        godot_line=GODOT_LINE,
        disclosure_line=DISCLOSURE,
    )
    n = verify_exports(out, "marauder", T.CELL, 13)
    print("marauder: %d frames exported + verified" % n)


if __name__ == "__main__":
    main()
