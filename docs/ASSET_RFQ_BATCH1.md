# Pixel Art Outsourcing — Request for Quotes (Batch 1)

> **Status:** DRAFT — not yet sent. Needs a send channel + Luminary's go on budget ceiling before outreach goes out.
> **Owner:** Mico (sourcing + acceptance) · Nagi (technical spec + engine import)
> **Source spec:** `docs/ASSET_OUTSOURCING_BRIEF.md` §2–§4
> **Deadline target:** quotes in by **2026-10-29** → sample piece by **11-05** → full delivery by **11-12** → v0.1 by **11-15**

---

## 1. Short version

We're looking for a **pixel artist** to produce the art for **Starforge Mobile** — a mobile lane-battler RTS (Android, F2P), inspired by StarCraft unit design and Clash Royale pacing. This is **Batch 1 only**: the v0.1 vertical-slice art set.

We start small on purpose: **one paid sample piece** (full Marine animation set) before committing to the full batch. Worst case we spend the sample fee only.

---

## 2. What we're asking for

### 2.1 Deliverable A — Marine (full set, **trial piece**)

| Item | Spec |
|---|---|
| Canvas | **32×32 px** |
| Animation | **13 frames** — idle ×2, walk ×4, attack ×3, death ×4 |
| Direction | **Right-facing only** (engine flips left via `flip_h`) — this halves the frame count, please don't draw both directions |
| Format | Transparent **PNG**, pixel-perfect grid, no anti-aliasing, no feathered semi-transparent edges (except deliberate soft FX) |
| Source | **`.aseprite` (or `.psd`) source files included** — we need to re-export and tweak |
| Naming | `marine_<state>_<index>.png`, e.g. `marine_idle_00.png` |
| Padding | ≤2 px between frames in the sheet |

### 2.2 Deliverable B — full Batch 1 (only after the sample passes)

| Group | Count | Notes |
|---|---|---|
| Unit animations | **4 units × 13 frames = 52 frames** | Marine, Hellion, **Marauder**, **Siege Tank** — Marauder & Siege Tank are **not implemented in-game yet**; specs below |
| Marauder | 13 frames | 32×32 — medium-range artillery unit |
| Siege Tank | 13 frames | **48×48** — slow, high-HP siege unit |
| Buildings | **6 images** | player tower, enemy tower, king tower ×2 states each (intact / damaged) — 40×60 canvas |
| UI | **8 items** | mineral icon (16×16 + 32×32), 4 card icons (64×64: Marine / Marauder / Hellion / Siege Tank), 1 nine-slice card frame, 1 single-lane battlefield background (720×1280, simple terrain texture, non-scrolling) |
| SFX | **5 files** | deploy whoosh, hit thud, unit-death zap, mineral pickup +1, match-win sting — `.wav`/`.ogg`, ≤2 s each |

**Palette direction (rough, not final):** StarCraft-flavoured — **player = blue HUD tones, enemy = orange**, terrain = neutral grey. We'll share the exact palette on request.

---

## 3. Hard requirements

1. **Godot 4.6 import must work** — we'll test in-engine on receipt. Deliverables must drop straight into `AnimatedSprite2D` + `SpriteFrames`.
2. **Full commercial buyout**, including source files. No work-for-hire ambiguity, no exclusivity beyond this asset set, no portfolio restrictions on showing the work.
3. **AI generation disclosure** — please state whether the art is hand-made or AI-generated, and confirm commercial rights either way. (We're building a store release, so this matters for store review.)
4. **Consistent proportions across a unit's frames** — a Marine must not visibly shrink between idle and death.
5. **Naming exactly as specified.** We'll check mechanically on delivery.

---

## 4. Trial piece first — please quote both ways

| Quote | What it covers |
|---|---|
| **A. Trial only** | Marine full set (13 frames + source) |
| **B. Trial + full Batch 1** | Trial + remaining 39 unit frames + 6 buildings + 8 UI + 5 SFX |

Quote the **trial** separately from the **rest**, so we can award the trial on its own.

---

## 5. Trial acceptance checklist

We'll check these line by line before awarding the batch.

- [ ] Canvas exactly 32×32; frame grid aligned, no off-by-one
- [ ] No anti-aliasing / no semi-transparent feathered edges
- [ ] 13 frames present and in the specified order (idle 2, walk 4, attack 3, death 4)
- [ ] Proportions consistent idle → death (no shrinking)
- [ ] Transparent background; PNG-8 or PNG-32 both acceptable
- [ ] Sheet spacing ≤2 px
- [ ] Naming exactly `marine_<state>_<index>.png`
- [ ] `.aseprite`/`.psd` source included and opens cleanly
- [ ] Imports in Godot 4.6 with correct `SpriteFrames` (our check, on receipt)

---

## 6. Payment & schedule

- Trial piece: **~1 week** from brief acceptance
- Full batch: **~1 week** after trial acceptance
- Payment: **milestone-based** — trial paid on delivery+acceptance, balance on full delivery+acceptance
- We'll share the full brief, palette, and engine import setup before you quote

**To quote, reply with:** rate per unit set (or per frame), trial-piece cost, total for Batch 1, source-file inclusion, AI disclosure, and your earliest start date + turnaround.

---

## 7. Contact

Reply to this post directly, or reach **Mico** (this account).

---

*Spec source: `docs/ASSET_OUTSOURCING_BRIEF.md` (v1). Technical contact for import questions: Nagi.*
