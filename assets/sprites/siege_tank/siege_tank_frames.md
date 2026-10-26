# Siege Tank — sprite sheet (13 frames)

| 项 | 值 |
|---|---|
| 单元 | siege_tank（朝右 +X，左向由引擎 flip_h） |
| 帧数 | 13 = idle 2 + walk 4 + attack 3 + death 4 |
| 单帧画布 | 48×48，透明背景 |
| 横向 sheet | `siege_tank_sheet_strip13.png`（624×48，无间距，帧 i 的 x = i×48） |
| 4×4 审阅图 | `siege_tank_sheet_grid4x4.png`（195×195，1px 透明沟） |
| 单帧 | `siege_tank_<state>_<index>.png` ×13 |
| 调色板 | 14 色（见 `siege_tank_frames.json`） |
| 抗锯齿 | 无（alpha 只含 0/255） |
| 来源 | **确定性代码绘制**，非 AI 生成、非真人委托 |

## 帧表（横向 sheet 顺序）

| # | 文件 | 状态 | x | y | fps | loop |
|---|---|---|---|---|---|---|
| 0 | `siege_tank_idle_1.png` | idle 1 | 0 | 0 | 2 | yes |
| 1 | `siege_tank_idle_2.png` | idle 2 | 48 | 0 | 2 | yes |
| 2 | `siege_tank_walk_1.png` | walk 1 | 96 | 0 | 6 | yes |
| 3 | `siege_tank_walk_2.png` | walk 2 | 144 | 0 | 6 | yes |
| 4 | `siege_tank_walk_3.png` | walk 3 | 192 | 0 | 6 | yes |
| 5 | `siege_tank_walk_4.png` | walk 4 | 240 | 0 | 6 | yes |
| 6 | `siege_tank_attack_1.png` | attack 1 | 288 | 0 | 8 | no |
| 7 | `siege_tank_attack_2.png` | attack 2 | 336 | 0 | 8 | no |
| 8 | `siege_tank_attack_3.png` | attack 3 | 384 | 0 | 8 | no |
| 9 | `siege_tank_death_1.png` | death 1 | 432 | 0 | 4 | no |
| 10 | `siege_tank_death_2.png` | death 2 | 480 | 0 | 4 | no |
| 11 | `siege_tank_death_3.png` | death 3 | 528 | 0 | 4 | no |
| 12 | `siege_tank_death_4.png` | death 4 | 576 | 0 | 4 | no |

## Godot 4.6 导入提示

- 用 `AnimatedSprite2D` + `SpriteFrames`；贴图 `siege_tank_sheet_strip13.png`，
  `hframes = 13`，`vframes = 1`，第 i 帧对应上表 x = i×48。
- 建议用 `SpriteFrames` 分段：idle = 帧 0-1，walk = 2-5，attack = 6-8，death = 9-12。
- 项目已设 `default_texture_filter = 0`（Nearest），移动端 2x 放大请用整数倍。

## 备注

- 48×48 画布（brief §2.1：Siege Tank 扩到 48×48）
- 与 Marine 共用同一套调色板与 `verify_exports()` 硬校验
- 单位代码本身尚未实现（brief §2.1 注），素材先行

## 验收对照（brief §3）

- [x] 像素网格对齐，无抗锯齿、无半透明羽化边
- [x] 各帧轮廓比例一致（idle→death 不缩水）
- [x] 透明背景 PNG-32，帧间距 0px（≤2px）
- [x] 命名规范 `<unit>_<state>_<index>.png` + 帧表
- [x] **三处导出像素一致**（单帧 == strip 格 == grid 格）由 `verify_exports()` 硬校验
- [x] Godot 4.6 导入测试通过 —— Nagi 实测 **20/20 全过**（4.6.stable.official.89cea1439：48×48 strip 导入 / SpriteFrames 4 段动画 / region 映射 / AnimatedSprite2D 播放 / fps 生效 / flip_h / hframes=13 / Nearest 采样 / .import 齐全）—— 复跑：`godot --headless --script tools/accept_sprite_import.gd -- res://assets/sprites/siege_tank/siege_tank_frames.json`
- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简

## 重生成

```bash
python3 tools/siege_tank_sprite_generator.py
```
