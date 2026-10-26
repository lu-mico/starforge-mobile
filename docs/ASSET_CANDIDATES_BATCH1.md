# Batch 1 — 候选供应商清单（2026-10-26 摸底）

> 配套文件：`docs/ASSET_RFQ_BATCH1.md`（询价帖正文）· 需求源头 `docs/ASSET_OUTSOURCING_BRIEF.md`
> 目标：10/29 拿到 ≥3 份报价 → 11/05 试片 → 11/12 全交 → 11/15 v0.1

## ⚠️ 关于价格的诚实说明

下面的价格**全部是公开挂牌价 / 社区公开帖报价**，不是我谈下来的，也没有替你承诺任何报价。
**「Fiverr 评价 ≥4.8」这条我没能核验** —— Fiverr 评分在页面 JS 里，抓取被挡；itch.io 的社区帖大多不公开评分。
→ 所以下面的候选**还没有一家是经过验证的 4.8+**。真要发出去之前，需要人工开页面看一眼评分和近期差评。

---

## 一、独立像素画师（brief §4 档 B · 建议路线）

| # | 候选 | 公开报价 | 作品集 | 匹配度 | 风险 |
|---|---|---|---|---|---|
| 1 | [Versatile Pixel Artist（itch.io）](https://itch.io/t/6523503/for-hire-versatile-pixel-artist-characters-sprites-game-assets-starts-at-15) | **起价 $15** | 帖内 | 🟢 交付物直指我们要的：**透明 PNG + upscaled sheet + 源文件 .aseprite/.psd**；**明确 50% 预付 / 50% 交付**（= 里程碑制，与我们 RFQ 一致） | 评分未核；起价 $15 可能只覆盖单张 |
| 2 | [Pixel Artist & Animator（itch.io）](https://itch.io/t/4455928/for-hire-pixelart-and-animator-looking-for-paid-projectworkcommission) | **$10/h** 或 单件：角色+动画 **$20–70+**，加动画 **$10+** | 帖内 | 🟢 报价结构清晰，$10/h 适合按小时谈整套 52 帧 | 🔴 **帖内未见「交付源文件」与「商用买断」承诺** → 须在询价时逐条确认；报价为 2025-01 发布，可能已变 |
| 3 | [Character Sprites 专精（itch.io）](https://itch.io/t/7175915/for-hire-pixel-artist-pixel-artist-specialized-in-character-sprites-and-animation-also-knowledgeable-on-environments-and-character-illustrations) | 动画 idle **起 $80**；RPG Maker 整表 **起 $200** | 帖内 | 🟡 专精角色 sprite + 动画，正对口 | 🔴 **偏贵** —— 单角色 idle 就 $80，13 帧全套大概率超预算 |
| 4 | [像素画委托站（pixelartcommissions.com）](https://pixelartcommissions.com/) | 按件报价 | 站内 | 🟡 明示「按件定价含修改，报价即实付」 | 🔴 **站点抓取失败**，无法核价；需人工看 |

> **1 是首选**：唯一同时明示「交 .aseprite/.psd 源文件」+「50/50 里程碑付款」+「透明 PNG 交付」的候选，与 brief §3 验收项逐条对得上。
> **2 是备选**：报价结构最好谈，但源文件/商用授权需在询价时逐条问清 —— RFQ §3 的硬性要求就是为此写的。

## 二、Fiverr 散单（brief §4 档 A · 低价但风险高）

| # | 候选 | 公开报价 | 匹配度 | 风险 |
|---|---|---|---|---|
| 5 | [Pixesprite](https://www.fiverr.com/pixesprite/create-pixel-art-character-animation-2d-pixel-art-animation-rpg-sprite-sheet) | **$15** | 🟢 明确写 **16/32/48/64×64 全尺寸** + **Godot / Unity 引擎就绪导出** | 🔴 $15 档几乎不可能覆盖 52 帧 + 源文件；风格一致性靠运气 |
| 6 | [Taralabs](https://www.fiverr.com/taralabs/design-pixel-art-characters-and-sprite-sheet-animation-for-your-game) | **$10** | 🔴 基础档，几乎只有单张 | 🔴 同上 |

> **Fiverr 两家只适合当「试片」渠道**，不适合整套。

## 三、社区池（brief §4 档 B · 备选投放位）

这些是**我们发询价帖的落点**，不是供应商：

| 渠道 | 链接 | 说明 |
|---|---|---|
| r/PixelArt（招聘贴专用版块） | https://www.reddit.com/r/PixelArt/comments/t6ua9w/pixel_art_jobs_hire_a_pixel_artist_post_your_jobs/ | 像素画师的求职/招聘专用帖，**历史帖里全是 32×32 / 16×16 单需求 → 说明这就是常规作业规模** |
| r/gameDevClassifieds | https://www.reddit.com/r/gameDevClassifieds/ | 有活跃的 [FOR HIRE] 像素画师帖 |
| itch.io Help Wanted | https://itch.io/t/ | 像素画师挂出来的接单帖密度最高 |
| ArtStation | https://www.artstation.com/ | 搜 "pixel art" + 标 available for freelance |
| Discord 像素艺术社区 | — | brief 里点名的渠道，但**具体服务器我没核**（不编名字） |

## 四、已核到的市场价（做还价锚点用）

| 报价点 | 来源 | 含义 |
|---|---|---|
| **$5/帧** | 社区公开帖（[itch.io](https://itch.io/t/6833182/art-seeking-someone-to-make-pixel-sprites-for-project)） | ⚠️ **按帧报的**。52 帧 = $260；这正好落在 brief 档 B 的 $250–500 区间内 |
| $4 小尺寸 sprite sheet / $7 大尺寸 | 社区公开帖 | 低档报价锚点 |
| $20–70+ / 角色含动画 | 独立画师 | 单角色全套，13 帧量级可参考 |
| $10/h | 独立画师 | 计时制，适合需求不明时谈 |
| $80 起 / idle 动画 | 专精角色 sprite 画师 | 高档锚点 |
| $200 起 / 整套 sheet | 同上 | 高档锚点 |

> 🔴 **注意成本放大效应**：按 $5/帧 算，52 帧 = $260；但档 B 若走「$250–500 整套」，**含 6 张塔 + 8 项 UI + 720×1280 背景 + 5 个 SFX**。
> → **背景那张 720×1280 可能比全部 52 帧还贵**，且它规格最模糊（"简易地形纹理，不滚动"）。**RFQ 里要把它单独列一行报价。**

## 五、下一步（需要 Luminary 的两项，其余我能自己做完）

1. **预算上限**（brief 建议 $300 封顶）→ 决定只发 RFQ 单，还是同时能预留试片费 $30–60
2. **付款方式与付款人**（我无支付权限）→ 定了才能真正下单

拿到后我能做：
- 把 RFQ 帖发到 r/PixelArt + r/gameDevClassifieds + itch.io（需确认用哪个 bot 身份，避免用 Luminary 本人号发）
- 10/29 回收报价 → 出一张比价表（总价 / 工期 / 源文件 / 商用授权 / 评价）

---

*所有链接与价格均为 2026-10-26 公开检索所得，未经私下沟通。未经 Luminary 确认预算与付款方式前，**不发出任何询价帖**。*
