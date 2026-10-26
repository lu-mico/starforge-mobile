# Towers — sprite set (6 static images)

| 项 | 值 |
|---|---|
| 画布 | 40x60，透明背景 |
| 数量 | 6（玩家塔 / 敌方塔 / 王塔 × 完好 / 受击） |
| 调色板 | 14 色（见 `towers_frames.json`） |
| 抗锯齿 | 无（alpha 只含 0/255） |
| 来源 | **确定性代码绘制**，非 AI 生成、非真人委托 |

## 清单

| # | 文件 | 状态 | 尺寸 |
|---|---|---|---|
| 0 | `player_tower_intact.png` | player_tower_intact | 40x60 |
| 1 | `player_tower_damaged.png` | player_tower_damaged | 40x60 |
| 2 | `enemy_tower_intact.png` | enemy_tower_intact | 40x60 |
| 3 | `enemy_tower_damaged.png` | enemy_tower_damaged | 40x60 |
| 4 | `king_tower_intact.png` | king_tower_intact | 40x60 |
| 5 | `king_tower_damaged.png` | king_tower_damaged | 40x60 |

## 验收对照（brief §3）

- [x] 像素网格对齐，无抗锯齿、无半透明羽化边
- [x] 透明背景 PNG-32
- [x] 命名规范 `<subject>_<state>.png` + 清单
- [x] **三处导出像素一致**（单张 == strip 格 == grid 格）由 `verify_exports()` 硬校验
- [x] Godot 4.6 导入测试通过 —— `tools/accept_static_sprites.gd` **24/24 PASS**（4.6.stable.official.89cea1439）
- [x] 声明「非 AI 生成」（确定性代码绘制）→ 商店审核披露最简

## 重生成

```bash
python3 tools/tower_sprite_generator.py
```
