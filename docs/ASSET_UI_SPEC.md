# Starforge Mobile — 美术规格：塔楼 / UI / 背景 / SFX

> **Owner:** Nagi（技术规格 + 引擎导入）｜Mico（制作 + 验收）
> **Status:** 塔楼（`59be7cd`）、UI+背景（`551bfde`→`0844158`）已交付并验收；SFX 已交付（`3cfe546`）；
> 引擎侧接线已落地（背景 TextureRect + 卡牌栏 + 点选部署）。§6 三项已拍板。
> **上游:** `docs/ASSET_OUTSOURCING_BRIEF.md` §2.2–§2.4（画布尺寸/数量）+ §3（DoD）
> **相关:** `docs/STARFORGE_GDD.md` §4（塔/车道）、§5（卡牌）、§3（矿）

---

## 0. 通用规则（沿用单位批次，不改）

| 项 | 规则 |
|---|---|
| 调色板 | **全局 16 色**（与 5 个单位共用同一张 palette），非每个素材各自 16 色 |
| 采样 | Nearest（`project.godot` 已设 `textures/canvas_textures/default_texture_filter=0`） |
| alpha | 只允许 `{0, 255}`（无 AA、无羽化边） |
| 尺寸 | **像素包含**语义：`rect(x0,y0,x1,y1)` 含两端（`ea4359d` 起的栅格化器契约） |
| 命名 | `<subject>_<state>_<index>.png`，index **0-based** |
| 交付 | 单帧 PNG + 帧表 md/json +（动画类）strip + 4×4 审阅图 |
| 硬断言 | 真实 bbox ≤ 画布（**重渲染到大画布量**，不能只看成品 PNG） |
| 三处一致 | 单帧 / strip 格 / grid 格 必须**字节一致** |

---

## 1. 塔楼（6 张，40×60）— 已交付，实测数据

`59be7cd` 交付，Godot 4.6 独立复跑 **24/24 PASS**（`tools/accept_static_sprites.gd`），
`tools/sprite_qa.py` 裁切 0px / 三处导出字节一致 / alpha{0,255} / ≤16 色 全 PASS。

### 1.1 实测几何（引擎侧据此对位）

| 素材 | bbox | 有效高 | 宽 | 基线 | 顶留白 | 左/右边距 | 部件数 |
|---|---|---|---|---|---|---|---|
| player_tower_intact | (4,15)-(36,59) | 45 | 33 | y=59 ✓ | 15 | 4 / 3 | 1 |
| player_tower_damaged | (4,15)-(36,59) | 45 | 33 | y=59 ✓ | 15 | 4 / 3 | 1 |
| enemy_tower_intact | (4,15)-(36,59) | 45 | 33 | y=59 ✓ | 15 | 4 / 3 | 1 |
| enemy_tower_damaged | (4,15)-(36,59) | 45 | 33 | y=59 ✓ | 15 | 4 / 3 | 1 |
| king_tower_intact | (1,8)-(38,59) | 52 | 38 | y=59 ✓ | 8 | 1 / 1 | 1 |
| king_tower_damaged | (1,8)-(38,59) | 52 | 38 | y=59 ✓ | 8 | 1 / 1 | 1 |

- ✅ **基线全部贴 y=59**（画布底边），无 1px 悬空
- ✅ 有效高 45/52 ≤ 56，顶饰留白充足（15 / 8px）
- ⚠️ **侧塔左右各留 3–4px**，王塔仅 **1px**（王塔 38px 宽几乎占满 40px 画布）
- ✅ 阵营配色分离干净：玩家塔 4 个蓝系色 / 0 橙；敌方塔 3 个橙系色 / 1 蓝
- ✅ 单一连通部件（无碎片）

### 1.2 两个待定项（不阻塞 v0.1）

**(a) 受击态是「改色」不是「缺口」**
实测：玩家/敌方塔受击态**轮廓未减任何像素**（removed=0，added=10），只有 91 px 改色；
王塔 removed=0 / added=2 / 改色 114 px。即受击态 = 污渍 + 底座碎块，**没有轮廓缺口**。

后果量化：塔在 720px 宽视口里只有 40px 宽（**屏宽 5.6%**），受击痕迹约 8×9px（**屏宽 ~1%**）。
1x 显示时改色型受击态**接近不可辨**。

→ **已拍板（§6-3）：塔楼受击只做 2 态（intact / damaged），不改剪影。**
可辨性靠**引擎侧受击反馈**补：HP<50% 切 damaged 贴图 + 轻微屏幕抖动/闪白，
不指望 1px 级的贴图差异承担全部信息量。
次选方案（受击态去掉 ≥3px 深的一块轮廓角，需重出 2 张）**不做** —— 会改塔的剪影，
而塔在 v0.1 场景里只有 40px 宽，剪影变化比改色更值得留到 3 车道时统一处理。

✅ **已落地（2026-10-27）**：引擎侧受击反馈实现在 `src/buildings/Tower.gd`
（+ 门禁 `tools/accept_tower_feedback.gd` 40/40 PASS）。规则：
- **hp < 50%** → 切 `<kind>_tower_damaged.png`（**严格小于**：正好 50% 仍显示 intact）
- **每次受击** → 0.12s 受击染色 + 0.18s 横向抖动（衰减正弦，幅度 3px）
- **hp = 0** → 塔被摧毁：碰撞关闭、退出 `towers` 组、单位不再打它、贴图压暗
- 补了**伤害通路**：`Unit._acquire_tower_target()` —— 无敌方单位时，单位会走向并射击敌方塔
  （否则 v0.1 里没有东西能打塔，damaged 贴图永远不会出现）

**(b) 王塔蓝色顶晶，但王塔是「双方共用」的同一张图**
brief §2.2 = 6 张 = 玩家塔/敌方塔/**王塔** × 2 状态 ⇒ 王塔只有一张设计，
但 GDD §4 说**双方各有一个王塔**。当前王塔顶晶是蓝色（3 个蓝系色），
放到敌方半场会读成「玩家蓝」。

→ 三个选项：
1. **王塔顶晶改中性银白**（改 2 张，阵营靠位置+周边色区分）—— 最省
2. 王塔出 2 个阵营版本（总数 6 → 8 张，超 brief 的 6）
3. 引擎侧用 `modulate` 给敌方王塔换色（会染到整张图，不推荐）

**✅ 已拍板并落地（§6-1）＝选项 1（中性银白）**：`tools/tower_sprite_sheet.py` 的
`ACCENT["king"]` 由 `("B","L","R")`（蓝）改为 `("T","R","X")`（中性银白 + 白高光）。
重出 2 张王塔贴图后实测：**7 色、无阵营蓝**（旧版 3 个蓝系色），
`accept_static_sprites.gd` 对塔楼清单全 PASS。阵营靠位置 + 周边侧塔色区分。

### 1.3 塔楼交付格式小缺口 — ✅ 已补（`375ad0a` 加 `towers_frames.md`）
单位批次每个都有 `<unit>_frames.md`（人读帧表 + 验收对照表），**塔楼只有 `towers_frames.json`**。
建议补一份 `towers_frames.md`（含「Godot 4.6 导入测试通过」勾选 + 上面 §1.1 的几何表），
与单位批次保持同一交付口径。

---

## 2. 引擎侧对位表（我方落地用，单位素材已具备但场景还没接）

> **✅ 引擎侧已接线**（单位/塔贴图已进场景）。接线时**必须**按下表对齐，否则单位脚底会错位。

**脚底对齐公式**（`Sprite2D` / `AnimatedSprite2D` centered=true）
```
offset_y = H/2 - g - 1        H = 画布高, g = idle 帧最底一行(ground row)
```
目标：所有单位/塔的**脚底**落在同一条线 **`lane_y = 640`**
（`Unit._physics_process` 锁定 position.y = lane_y）。

> **为什么是 640 不是 360**：lane_y 是竖屏 720×1280 的**垂直中线**，不是随手取的数。
> §4 要求战斗区落在中央纵向 40%（rows 384..896）—— 车道在 340..380 时它挤在顶部四分之一，
> 中央那条带是空地；挪到 **620..659** 后战斗区正好就是中央那条带，
> 且整张背景能做成**上下精确镜像**（row y == row 1279-y，0 像素差）。
> 背景与引擎必须同步改，**引擎才是位置的权威**（Mico 09:45 那版按 360 做的已作废）。

| 素材 | 画布 H | idle ground row g | **offset_y** | 说明 |
|---|---|---|---|---|
| marine | 32 | 30 | **-15** | |
| marauder | 32 | 30 | **-15** | 与 Marine 同基线 |
| hellion | 32 | 28 | **-13** | 悬浮单位，比 Marine 高 2px（视觉悬空，正确） |
| siege_tank | 48 | 46 | **-23** | 48×48 大画布，必须单独算，否则比 Marine 低 8px |
| tower（侧/王） | 60 | 59 | **-30** | 基线在画布底边 |

⚠️ **最易错的一条**：`siege_tank` 是 48×48，跟 32×32 走同一套居中逻辑的话脚底会低 8px。
⚠️ **lane 带是 y=620..660**（背景地面线 638..641 压 `lane_y=640`），塔底若压到 660 以下会出带外。
⚠️ `main.tscn` 的 `Lane` ColorRect 是**调试占位**，正式背景贴图自带车道，**不要再叠一层**。

**单位 SpriteFrames 建议**：直接用 `AnimatedSprite2D` + 由 `<unit>_frames.json` 生成的
`.tres`（4 段动画 idle/walk/attack/death，帧数 2/4/3/4）。转换里已知要点：
Godot 4 的 `SpriteFrames.add_frame()` **不接受 Rect2 region**，必须包 `AtlasTexture`
（`atlas` + `region` + `filter_clip`），且 `SpriteFrames.new()` 自带一个空 `default` 动画。

---

## 3. UI / 卡牌（✅ 10 项，已交付）

### 3.1 卡牌图标（4 张，64×64）
`icon_marine.png` / `icon_marauder.png` / `icon_hellion.png` / `icon_siege_tank.png`

- **主体高度 ≤40px**，4 张**必须一致**（否则卡牌栏高低不齐）
- 统一朝右；背景**透明**，不自带卡框
- Tank 原 48×48 塞进 64×64 要**留白 ≥6px**（否则比另外三个小一号）
- 宽度差异靠造型（Marauder 宽 / Marine 中 / Hellion 宽扁 / Tank 最宽），不靠缩放

### 3.2 九宫格卡框（1 张，48×64）
- `patch_margin` 左/上/右/下 = **10px** → 中心拉伸区 28×44
- 4 角必须完整造型；**中心区必须纯色**（渐变/纹理会露馅）
- 左右边只能水平渐变或纯色（禁竖向渐变 → 拉伸出斜纹）
- **框内高 44 ⇒ 图标主体必须 ≤40px**（上下各留 2px）

### 3.3 水晶矿图标（2 张）
`icon_mineral_16.png`(16×16) / `icon_mineral_32.png`(32×32)
- 16 版必须是 32 版的**手工简化版**（缩放会糊）；16px 下不画 1px 细节，只留 2–3 色
- 晶体造型（多面菱形），不要金币/圆球

### 3.4 卡牌角标（3 张，12×12）— 引擎侧刚需
`card_badge_cost.png` / `card_badge_count.png` / `card_badge_frame.png`
- 画在卡牌**右上角**，锚点 = 右上角；底板必须**不透明**（否则和卡框叠一起花）
- 12×12 在 720×1280 上按 2x = 24×24 实际像素，够读
- ⇒ **UI 项数 8 → 10**（见 §6 拍板项 2）—— ✅ **已拍板并交付（2026-10-27）：按 10 项做**。
  角标 3 张已交付（`551bfde`）并已进引擎（卡面右上角 = 角标贴图 + 引擎画的数字 Label）。

### 3.5 GDD 里的卡牌事实（引擎侧要接的）
GDD §5：手牌 **4 张**常驻底部，牌库 8 张，**点击卡牌 → 拖到车道 → 松手部署**。
卡牌费用：Marine 3 / Marauder 4 / Hellion 4 / Siege Tank **7**（`UnitSpawner` 现在只硬编码了
Marine 3 / Hellion 4，且只有 KEY_1/KEY_2）。角标要显示的就是这 4 个数字。

---

## 4. 战场背景（1 张，720×1280）

- **精确 2x 像素网格**（色块边界对齐偶数坐标；720/1280 天然偶数）
- **禁噪点/dither**，用 2×2 或 4×4 规则色块（16 色下单像素噪点极明显）
- 大面积中性灰，3–4 个明度层级；**不画单位色**（蓝/橙留给单位和塔）
- 1 lane：一条主道横向带 + 两侧边界线
- 左右塔基各留明确空地（背景不画塔，塔是独立贴图）
- 上下对称（敌方侧/玩家侧镜像）
- **中央纵向 40% 必须干净**（战斗区，不能有高对比纹理干扰单位识别）
- 不透明（alpha=255，底层 ColorRect 兜底）；预计 <60KB
- 引擎侧：`TextureRect` + `STRETCH_KEEP_ASPECT_COVERED` + NEAREST，`canvas_items` stretch

---

## 5. SFX（5 条）

| 文件 | 时长 | 规格 |
|---|---|---|
| `sfx_deploy.wav` | ≤0.6s | 谁osh —— 落场，短促下扫 + 落点冲击 |
| `sfx_hit.wav` | ≤0.4s | 命中 thud —— 低频冲击，短衰减 |
| `sfx_death.wav` | ≤0.8s | 死亡 zap —— 噪声 + 下滑音 |
| `sfx_mineral.wav` | ≤0.5s | 采矿 +1 —— **清脆上行**，混战里要听得见 |
| `sfx_win.wav` | ≤2.0s | 胜负 sting —— 上行和弦，1.5–2s |

> **交付为 WAV**（brief §2.4 允许 wav/ogg）：本机 ffmpeg 无 libvorbis、homebrew 的 libvorbis 状态损坏（装了但没有二进制），
> 所以这轮先交 WAV；生成器 `tools/sfx_generator.py --ogg` 走 oggenc，**修好 `brew reinstall libvorbis` 后一条命令即可转 Ogg**。
> 导入用 `compress/mode=0`（未压缩 PCM，共约 500KB，引擎侧才能直接量峰值）；要省内存可改 QOA。

技术：Ogg Vorbis｜44100Hz 单声道（sting 可双声道）｜峰值 **−6 dBFS**（音效会重叠，防削波）｜
无直流偏移｜结尾 **≤30ms 淡出**（防爆音）｜走 `AudioStreamPlayer`（非 bus），引擎侧统一 `volume_db`。

**程序合成路线 Mico 已认领**（零成本、可商用）—— 同意，走这条。约束同上（≤2s、-6dBFS、淡出）。
✅ **已交付 5 条**（`tools/sfx_generator.py` 程序合成，零成本无授权风险），引擎侧验收 `tools/accept_sfx.gd` **全绿**：
44100Hz / 单声道（sting 双声道）/ 时长合规 / 峰值 −6.00 dBFS / 结尾 30ms 淡出到 0（无爆音）/ 无直流偏移。

---

## 6. 需 Luminary 拍板 3 项

1. **王塔顶晶配色**（§1.2b）：改中性银白（省）/ 出 2 个阵营版本（6→8 张）/ 引擎染色（不推荐）。
   建议 1。v0.1 单线场景无王塔，可推迟到 3 车道，但**加 3 车道时必须一并处理**。
2. **UI 项数 8 → 10**（卡牌角标 3 张）。建议做 —— 否则卡牌栏只有一张脸，没有费用信息。
3. **塔楼受击 2 态还是 3 态**？brief 写 2 态 ⇒ 建议就 2 态，**伤害反馈靠引擎**（切贴图 + 闪白/抖动），
   不靠第三张图。前提是 §1.2a 的贴图可辨性问题用引擎手段补。

### 6.1 拍板记录（2026-10-27，Nagi）

| 项 | 决定 | 依据 | 落地 |
|---|---|---|---|
| §6-1 王塔顶晶 | **中性银白**（选项 1） | 阵营靠位置 + 周边色区分；省 2 张 | `40812bf`（已） |
| §6-2 UI 项数 | **8 → 10（做）** | 卡牌栏没有费用数字 = 一张脸；角标是引擎刚需 | 美术 `551bfde`（已）· 引擎接线 `86ec446`（已） |
| §6-3 塔楼受击 | **2 态 + 引擎反馈** | 3 态要改 40px 宽的剪影，收益低、多 3 张图；差异型受击态实测屏宽 ~1% 基本不可读 | `src/buildings/Tower.gd` + 门禁 `tools/accept_tower_feedback.gd`（本轮） |

**§6-2 的 spec 正式口径**：UI = **10 项**（图标 4 + 卡框 1 + 矿图标 2 + 角标 3），
§3.4 的「8 → 10」不再是待定项。

**§6-3 的 spec 正式口径**：塔 = **2 态**（intact / damaged），
受击可辨性**由引擎承担**（见 §1.2a 的四条规则），美术侧不再出第 3 态。

---

## 7. 交付顺序（每批走同一套门禁）

B1 塔楼（✅ 已交付）→ B2 卡牌图标4+卡框1（框与图标必须同批定，框内高44锁死图标≤40）
→ B3 矿图标2+角标3 → B4 背景720×1280（单独一批，2x网格+无噪点单独好验）→ B5 SFX5。

门禁：`tools/sprite_qa.py`（像素）+ `tools/accept_sprite_import.gd`（动画单位）+
`tools/accept_static_sprites.gd`（静态：塔/图标/框/背景）+ **新增 3 条本批专属测**：
九宫格 patch_margin 拉伸 3 种尺寸不出缝 / 背景 2x 网格对齐 / UI 图标主体高度实测。

---

---

## 8. 2026-10-28 复验记录（R30）

补 R29 遗留的**引擎侧复验**（上一轮只改了 manifest 帧位，没跑门禁）：

| 门禁 | 命令 | 结果 |
|---|---|---|
| UI 静态贴图（10 项） | `godot --headless --script tools/accept_static_sprites.gd -- res://assets/sprites/ui/ui_frames.json` | **PASS**（10/10 项：尺寸/alpha 二值/≤16 色/.import 齐全） |
| 像素门禁 G0–G8 | `python3 tools/ui_sprite_generator.py` | **全 PASS**（G0 hygiene … G8 strip/grid 字节一致） |
| 塔楼受击反馈 | `godot --headless --script tools/accept_tower_feedback.gd` | **PASS**（40 checks, 0 failed） |
| UI 交互（选卡/点车道/部署） | `godot --headless --script tools/accept_ui.gd` | **PASS**（118 checks, 0 failed） |
| SFX 5 条 | `godot --headless --script tools/accept_sfx.gd -- res://assets/audio/sfx` | **PASS**（44100Hz/单声道/峰值 ≤−6dBFS/淡出到 0） |

**顺带修的门禁顺序 bug**（`65ccca1`）：G8（strip/grid 字节一致）虽然编号在 G7 之后，
但代码里跑在 G7 之前，打印顺序和文档对不上。已改成 G7 → G8，并在模块 docstring 里补上 G8 说明。

**真机侧（模拟器）**：用 Medium_Phone_API_36.1 装新导出的 debug APK 并启动，
战场背景、卡牌栏 4 张卡（带角标位）、王塔贴图均正常渲染，无崩溃。
APK：`~/Agent-Outputs/Nagi/starforge-mobile/starforge_v0.1.0-alpha.1-debug_2026-10-28.apk`
（sha256 `49385e618ed1b31129c8ebf3aa95aefb7eb38e33f047ce3380ed45663662206f`）。
⚠️ 模拟器上手动点选卡 + 点车道，**未能从截图确认单位落地**（点选高亮也不明显）——
部署链路目前只有 headless 门禁（118 checks）背书，真机视觉确认还欠一次。

*最后更新：2026-10-28 20:20 JST by Nagi*


---

## 8. 引擎侧接线（✅ 已落地）

**背景**：`main.tscn` 的 `Background` = `TextureRect`，720×1280，
`stretch_mode = STRETCH_KEEP_ASPECT_COVERED`、`texture_filter = NEAREST`。
原 `Lane` ColorRect 已删（背景自带车道，叠两层会打架）。

**卡牌栏**（`src/ui/CardBar.gd` + `src/ui/UnitCard.gd`）：
- 4 张卡 = `UnitRoster.CARDS`（**费用/场景/图标唯一真源**，`UnitSpawner` 与卡牌栏共用）
- 卡面 = 九宫格 `NinePatchRect`（patch_margin 四边 10）+ 64×64 图标（**按 body bbox 居中**，
  不按画布居中 —— 图标留白不对称，按画布居中会歪）+ 3 张角标
- 卡框画在 80×64 源空间再整体 2x 上屏（**最近邻，不重采样**）
- 角标上**没有数字**，费用数字由引擎画（`Label` 叠在角标上），否则只有一张脸没有费用信息
- 卡栏底边贴屏底，4 张 160×128 + 16px 间距 = 688px，720 宽居中

**部署**：点卡选中（`card_badge_frame` 亮起作选中角标）→ 点车道该 x 处生成。
`UnitSpawner` 把单位挂在**自己父节点（arena）**，不是 `get_tree().current_scene`
（后者在 `--script` 驱动时为 null，且 arena 才是正确的宿主）。
键盘 1–4 仍可在固定出生点生成。

**验收脚本自指**：headless 下 root 视口只有 64×64，content-scale 会把输入坐标全部扭曲，
所以 `accept_ui.gd` 先 `content_scale_mode = DISABLED` + `root.size = 720×1280`，
让画布变换成为单位阵（与真机一致），GUI 命中测试与 `_unhandled_input` 才落在正确位置。

**塔楼受击反馈（§6-3 落地）**：`src/buildings/Tower.gd` + `main.tscn` 的 `EnemyTower`
- 贴图按 `tower_kind` 自动取（player / enemy / king 各 2 张），脚本是唯一真源
- `hp < 50%` → 切 damaged 贴图；每次受击 → 染色 + 抖动；`hp = 0` → 摧毁
- 单位会在没有敌方单位时走向并射击敌方塔（`Unit._acquire_tower_target()`），
  否则 v0.1 里没有任何东西能打塔，damaged 贴图永远不出现
- 门禁：`godot --headless --script tools/accept_tower_feedback.gd`（40/40 PASS）
