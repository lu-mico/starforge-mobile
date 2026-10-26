# Marine — sprite sheet (13 frames)

| 项 | 值 |
|---|---|
| 单位 | Marine（朝右 +X，左向由引擎 flip_h） |
| 帧数 | 13 = idle 2 / walk 4 / attack 3 / death 4 |
| 单帧画布 | 32×32，透明背景 |
| 横向 sheet | `marine_sheet_strip13.png`（416×32，无间距，帧 i 的 x = i×32） |
| 4×4 审阅图 | `marine_sheet_grid4x4.png`（131×131，1px 透明沟） |
| 单帧 | `marine_<state>_<index>.png` ×13 |
| 调色板 | 14 色（见 `marine_frames.json`） |
| 抗锯齿 | 无（alpha 只含 0/255） |
| 来源 | **确定性代码绘制**，非 AI 生成、非真人委托 |

## 帧表（横向 sheet 顺序）

| # | 文件 | 状态 | x | y | fps | loop |
|---|---|---|---|---|---|---|
| 0 | `marine_idle_1.png` | idle 1 | 0 | 0 | 2 | yes |
| 1 | `marine_idle_2.png` | idle 2 | 32 | 0 | 2 | yes |
| 2 | `marine_walk_1.png` | walk 1 | 64 | 0 | 6 | yes |
| 3 | `marine_walk_2.png` | walk 2 | 96 | 0 | 6 | yes |
| 4 | `marine_walk_3.png` | walk 3 | 128 | 0 | 6 | yes |
| 5 | `marine_walk_4.png` | walk 4 | 160 | 0 | 6 | yes |
| 6 | `marine_attack_1.png` | attack 1 | 192 | 0 | 8 | no |
| 7 | `marine_attack_2.png` | attack 2 | 224 | 0 | 8 | no |
| 8 | `marine_attack_3.png` | attack 3 | 256 | 0 | 8 | no |
| 9 | `marine_death_1.png` | death 1 | 288 | 0 | 4 | no |
| 10 | `marine_death_2.png` | death 2 | 320 | 0 | 4 | no |
| 11 | `marine_death_3.png` | death 3 | 352 | 0 | 4 | no |
| 12 | `marine_death_4.png` | death 4 | 384 | 0 | 4 | no |

## Godot 4.6 导入提示

- 用 `AnimatedSprite2D` + `SpriteFrames`；贴图 `marine_sheet_strip13.png`，
  `hframes = 13`，`vframes = 1`，第 i 帧对应上表 x = i×32。
- 建议用 `SpriteFrames` 分段：idle = 帧 0-1，walk = 2-5，attack = 6-8，death = 9-12。
- 项目已设 `default_texture_filter = 0`（Nearest），移动端 2x 放大请用整数倍。

## 验收对照（brief §3）

- [x] 像素网格对齐，无抗锯齿、无半透明羽化边
- [x] 13 帧轮廓比例一致（idle→death 不缩水）
- [x] 透明背景 PNG-32，帧间距 0px（≤2px）
- [x] 命名规范 `<unit>_<state>_<index>.png` + 帧表
- [ ] Godot 4.6 导入测试通过 —— **待 Nagi 实跑确认**
- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简
- [x] 源文件：生成器 `tools/marine_sprite_generator.py`（可改色/改姿势重跑）

## 重生成

```bash
python3 tools/marine_sprite_generator.py
```
