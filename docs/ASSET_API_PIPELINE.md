# Asset Pipeline — API Generation (not local, not human vendor)

> **Decision (Luminary, 2026-10-26 09:14 JST):** "外包的意思是用 API 而不是本地跑"
> → **Outsource = generate assets through paid third-party APIs.**
> ❌ Not local ComfyUI/SD (rejected 2026-10-25)
> ❌ Not commissioning a human pixel artist (RFQ path superseded by this file)
> ✅ Paid image/sprite generation APIs with commercial-use rights

---

## 1. What this supersedes

| Doc | Status |
|---|---|
| `docs/ASSET_RFQ_BATCH1.md` | ⛔ **Do not send.** Human-vendor RFQ, wrong path now. Kept for spec reference only. |
| `docs/ASSET_CANDIDATES_BATCH1.md` | ⛔ Vendor candidate list — not needed. Market price anchors still useful as cost ceiling comparison. |
| `docs/ASSET_OUTSOURCING_BRIEF.md` | ✅ **Still authoritative for the art spec** (canvas sizes, frame counts, naming, Godot import requirements). Channel changes; spec does not. |

---

## 2. API routes evaluated

| Route | Fit for 32×32 animated sprites | Commercial rights | Cost | Status |
|---|---|---|---|---|
| **PixelLab API** (`pixellab.ai/pixellab-api`) | ✅ purpose-built: pixel sprites, character-state animation, 8-dir rotation, tilesets | ✅ included on paid plans | from **$12/mo** (2,000 generations) | **recommended primary** — needs key |
| Google Gemini image (`gemini-3.1-flash-image-preview`) | 🟡 good style, not pixel-exact; needs palette quantize + downscale | ✅ per Google terms | existing key | configured ✅ — use for **backgrounds / card art / UI** |
| OpenAI `gpt-image-1.5` | 🟡 same caveat; transparent BG supported | ✅ | existing key | ⚠️ 2026-10-26 test call failed (Codex route model error) → needs a working key before use |
| fal.ai / Replicate (SDXL + pixel LoRA) | 🟡 viable, more tuning work | ✅ | per-call, cents | not configured |
| Local ComfyUI | ❌ rejected by Luminary | — | — | not used |

**Rule:** any route used must grant **commercial use + store distribution**. Check the licence on the tier we pay for, and screenshot the terms into `docs/licences/` when we buy.

---

## 3. Pipeline (target)

```
spec (ASSET_OUTSOURCING_BRIEF §2)
   │
   ├─ units/sprites ──→ PixelLab API ──→ frames (32×32 / 48×48, right-facing)
   ├─ buildings/UI ───→ Gemini image API ──→ downscale + palette quantize
   └─ SFX ────────────→ (TBD: audio API, e.g. ElevenLabs SFX)
   │
   ▼
post-process (local, CPU only — Pillow: crop to grid, quantize to 16-colour palette,
               strip anti-aliasing, verify frame count + naming)
   │
   ▼
Godot 4.6 import check (AnimatedSprite2D + SpriteFrames) → Nagi
```

Post-processing locally with Pillow is **not** "running a model locally" — it's image cleanup, no GPU inference.

## 4. Acceptance stays identical

The checklist in `ASSET_RFQ_BATCH1.md` §5 still applies verbatim (canvas size, frame count, no AA, naming, Godot import). It was written vendor-agnostic on purpose.

## 5. Open decisions (Luminary)

1. **Budget ceiling** for API spend — recommendation: **$30/mo** cap (PixelLab $12 + headroom for image calls). Compare: human artist trial was going to be $80–150.
2. **Who pays / which card** — I have no payment authority.
3. Confirmation that API-generated art is acceptable for **store review** (Google Play requires AI disclosure; we will disclose).
