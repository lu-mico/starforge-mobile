# Hellion — sprite sheet (13 frames)

| 项 | 值 |
|---|---|
| 单元 | hellion（朝右 +X，左向由引擎 flip_h） |
| 帧数 | 13 = idle 2 + walk 4 + attack 3 + death 4 |
| 单帧画布 | 32×32，透明背景 |
| 横向 sheet | `hellion_sheet_strip13.png`（416×32，无间距，帧 i 的 x = i×32） |
| 4×4 审阅图 | `hellion_sheet_grid4x4.png`（131×131，1px 透明沟） |
| 单帧 | `hellion_<state>_<index>.png` ×13 |
| 调色板 | 14 色（见 `hellion_frames.json`） |
| 抗锯齿 | 无（alpha 只含 0/255） |
| 来源 | **确定性代码绘制**，非 AI 生成、非真人委托 |

## 帧表（横向 sheet 顺序）

| # | 文件 | 状态 | x | y | fps | loop |
|---|---|---|---|---|---|---|
| 0 | `hellion_idle_1.png` | idle 1 | 0 | 0 | 2 | yes |
| 1 | `hellion_idle_2.png` | idle 2 | 32 | 0 | 2 | yes |
| 2 | `hellion_walk_1.png` | walk 1 | 64 | 0 | 6 | yes |
| 3 | `hellion_walk_2.png` | walk 2 | 96 | 0 | 6 | yes |
| 4 | `hellion_walk_3.png` | walk 3 | 128 | 0 | 6 | yes |
| 5 | `hellion_walk_4.png` | walk 4 | 160 | 0 | 6 | yes |
| 6 | `hellion_attack_1.png` | attack 1 | 192 | 0 | 8 | no |
| 7 | `hellion_attack_2.png` | attack 2 | 224 | 0 | 8 | no |
| 8 | `hellion_attack_3.png` | attack 3 | 256 | 0 | 8 | no |
| 9 | `hellion_death_1.png` | death 1 | 288 | 0 | 4 | no |
| 10 | `hellion_death_2.png` | death 2 | 320 | 0 | 4 | no |
| 11 | `hellion_death_3.png` | death 3 | 352 | 0 | 4 | no |
| 12 | `hellion_death_4.png` | death 4 | 384 | 0 | 4 | no |

## Godot 4.6 导入提示

- 用 `AnimatedSprite2D` + `SpriteFrames`；贴图 `hellion_sheet_strip13.png`，
  `hframes = 13`，`vframes = 1`，第 i 帧对应上表 x = i×32。
- 建议用 `SpriteFrames` 分段：idle = 帧 0-1，walk = 2-5，attack = 6-8，death = 9-12。
- 项目已设 `default_texture_filter = 0`（Nearest），移动端 2x 放大请用整数倍。

## 备注

- 快速悬浮侦察车：开放座舱 + 车手（橙色面罩）+ 下挂机枪 + 两组悬浮推进器
- 「走路」= 推进器脉冲 + 车身起伏（悬浮单位无履带）
- 与其他单位共用同一套调色板（全局 ≤16 色）与 `verify_exports()` 硬校验

## 验收对照（brief §3）

- [x] 像素网格对齐，无抗锯齿、无半透明羽化边
- [x] 各帧轮廓比例一致（idle→death 不缩水）
- [x] 透明背景 PNG-32，帧间距 0px（≤2px）
- [x] 命名规范 `<unit>_<state>_<index>.png` + 帧表
- [x] **三处导出像素一致**（单帧 == strip 格 == grid 格）由 `verify_exports()` 硬校验
- [ ] Godot 4.6 导入测试 —— **待实跑确认**（用 tools/accept_sprite_import.gd 一键复现）
- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简

## 重生成

```bash
python3 tools/hellion_sprite_generator.py
```
