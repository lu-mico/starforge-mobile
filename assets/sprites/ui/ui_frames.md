# UI batch — sprite set (10 static images)

| 项 | 值 |
|---|---|
| 画布 | 单张各自尺寸（图标 64x64 / 卡框 48x64 / 矿 32+16 / 角标 12x12） |
| 数量 | 10（卡牌图标 4 + 九宫格卡框 1 + 矿图标 2 + 角标 3） |
| 调色板 | 全局 16 色（见 `ui_frames.json`） |
| 抗锯齿 | 无（alpha 只含 0/255） |
| 来源 | **确定性代码绘制**，非 AI 生成、非真人委托 |
| 九宫格 | `card_frame.png` 48x64，patch_margin 四边 10px → 中心拉伸区 28x44 |

## 清单

| # | 文件 | 尺寸 | 实测 body bbox | 边距 L/T/R/B |
|---|---|---|---|---|
| 0 | `icon_marine.png` | 64x64 | (14,12)-(50,52) | 14/12/14/12 |
| 1 | `icon_marauder.png` | 64x64 | (11,12)-(53,52) | 11/12/11/12 |
| 2 | `icon_hellion.png` | 64x64 | (9,12)-(55,52) | 9/12/9/12 |
| 3 | `icon_siege_tank.png` | 64x64 | (6,12)-(58,52) | 6/12/6/12 |
| 4 | `card_frame.png` | 48x64 | (0,0)-(48,64) | - |
| 5 | `icon_mineral_32.png` | 32x32 | (5,1)-(27,32) | - |
| 6 | `icon_mineral_16.png` | 16x16 | (1,1)-(15,15) | - |
| 7 | `card_badge_cost.png` | 12x12 | (0,0)-(12,12) | - |
| 8 | `card_badge_count.png` | 12x12 | (0,0)-(12,12) | - |
| 9 | `card_badge_frame.png` | 12x12 | (0,0)-(12,12) | - |

## 图标主体高度（4 张必须一致且 ≤40px）

| 图标 | 主体高 |
|---|---|
| `icon_marine` | 40 |
| `icon_marauder` | 40 |
| `icon_hellion` | 40 |
| `icon_siege_tank` | 40 |

## 三处导出一致性

- 横向 strip：`ui_sheet_strip.png`（388x64，第 i 帧 x = 累计宽度）
- 审阅网格：`ui_sheet_grid.png`（259x194，4x3，1px 透明沟，单元格 64x64，资产居中）
- 硬校验：单张 == strip 格 == grid 格（逐字节），由 `verify_consistency()` 执行

## 验收对照（brief §3 / ASSET_UI_SPEC §3）

- [x] 像素网格对齐，无抗锯齿、无半透明羽化边
- [x] 透明背景 PNG-32（角标底板全不透明）
- [x] 命名规范 + 帧表（json + 本 md）
- [x] 九宫格 patch_margin=10 拉伸 3 种尺寸无接缝
- [x] 卡框中心纯色，左右边仅水平渐变，上下边仅垂直渐变，四角铅钉
- [x] 4 张卡牌图标主体高度一致且 ≤40px
- [x] 每个图标四周留白 ≥2px（坦克 ≥6px），不贴画布边
- [x] 16px 矿图标为手工简化版（非 32px 缩放），≤3 色
- [x] 背景 720x1280 不透明、严格 2x 网格、无噪点、**不含阵营蓝/橙**

## 重生成

```bash
python3 tools/ui_sprite_generator.py
```
