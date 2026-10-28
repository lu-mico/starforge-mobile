# Starforge Mobile — Project Plan

**Codename:** Starforge Mobile
**Owner:** Luminary (CEO) / Nagi (Project Lead) / Mico (COO, advisor)
**Target launch:** v1.0 in ~10 weeks from 2026-08-29
**Re-baselined:** 2026-10-25 — original 9/12 -> 11/07 chain was blown (see "Schedule Re-baseline" below)

---

## Milestones

### v0.1 — "Playable Loop" (target **2026-11-15**, re-baselined from 2026-09-12)

**Scope decision (2026-10-29):** v0.1 ships **1 lane, 1 tower per side** (player + enemy).
3 lanes + side towers + king tower move to **v0.3**. This is a deliberate MVP cut — the
win/lose loop needed exactly two towers on one lane to be reachable at all.

- ✅ Godot 4 project scaffold + GitHub repo
- ✅ 1 arena, 2 towers (player + enemy), 1 lane — `Tower.gd`: 1200 HP each, `take_damage()`, 2-state art (intact/damaged), hit flash + shake, and the `towers` group so units can acquire them via `Unit._acquire_tower_target()`. **3 lanes + 2 side towers + king tower → v0.3**
- ✅ 4 units (Marine / Marauder / Hellion / Siege Tank) walk + attack + die — all 4 have script + scene + full 13-frame idle/walk/attack/death sets
- ✅ Card hand (4 cards) + tap-to-deploy — `CardBar` + `UnitCard`: tap card → tap lane, deploys at the tapped x. ⚠️ **Deviation from GDD §5**: the GDD says "tap card → drag to lane → release"; v0.1 ships tap-to-tap and drag is **not** implemented. Keyboard `1`–`4` still spawn at the fixed point.
- ✅ Minerals HUD + regen (5 start / 10 max / 1 per 2.0s) — verified by `tests/smoke_test.tscn`
- ✅ Basic AI opponent (scripted deployment) — `AiOpponent`: first unit at 18s, then one every 9s, rotation hellion → marine → marauder → hellion, team 1, walks left toward the player tower, spends no minerals
- ✅ Win/Lose screen — `ResultOverlay`: VICTORY / DEFEAT + RESTART. Enemy tower falls → VICTORY, player tower falls → DEFEAT; the match pauses and the overlay stays interactive
- ✅ Sound — `Sfx` autoload (`SfxBank.gd`) + 5 events (deploy / hit / death / mineral / win), engine-side gain, 8-voice pool
- ✅ Art — 74 runtime assets delivered (69 PNG + 5 WAV), 0 cost (procedurally synthesised locally, no paid API). King-tower art exists but no `KingTower` node yet → v0.3
- ✅ APK rebuilt + installed + launched on Android emulator — 2026-10-29 08:28, 28.2 MB (`build/starforge.apk`, sha256 `d3a2214…`), contains AI opponent + result screen + SFX
- ✅ **Tap-to-deploy verified on device** — card select → lane deploy → unit on the lane, minerals 10 → 7 (Marine = 3). Found and fixed a real bug doing this, see below.
- ✅ Full loop reachable both ways — measured headless: idle player loses in 32.6s, active player wins in 28.6s
- ⚠️ **Match length is ~30s, not the 3 minutes the deliverable names** — measured, not estimated. Tower HP and AI cadence are tuned for a quick loop, not a 3-minute match. The deliverable is therefore **met in substance** (a complete match vs AI on your phone, both outcomes reachable) but **not met in the "3-minute" wording**. Retuning HP/cadence vs restating the target is a call for Luminary; v0.3 owns pacing.
- **Deliverable:** finish a match vs the AI on your phone — **met, with the "3-minute" wording flagged above**

**Status 2026-10-29:** 9/10 done, 1 wording mismatch (match length). Every gate green:
SFX wiring 25, match result 24, UI 118, tower feedback 40, tap input 8, smoke test 14/14.

**Bug found and fixed 2026-10-29 (tap-to-deploy was dead on a real device):**
On Android one physical tap reaches Godot **twice** — the real `InputEventScreenTouch`
**and** the mouse event Godot emulates from it (`emulate_mouse_from_touch` is on by
default). The card handler treated both as presses, so one tap selected the card and
immediately deselected it: the card hand did **nothing** on a real phone. Every headless
gate was green, because the harness pushes one synthetic event and never sees the pair.
Fix: `src/core/TapInput.gd` — one place that decides what counts as a real press, used by
both `UnitCard` and `Arena`. New gate `tools/accept_tap_input.gd` (8 checks) replays the
real Android event pair and asserts one tap does exactly one thing.

### v0.3 — "Pacing Pass" (target **2026-12-06**, re-baselined from 2026-09-26)
- [ ] 3 lanes + 2 side towers + king tower (pulled forward from v0.1)
- [ ] Match timer + sudden death
- [ ] Match length retune (v0.1 matches run ~30s; GDD target is 5-8 min)
- [ ] Tutorial (3 screens)
- [ ] Settings menu (audio, controls)
- [ ] Save/load (player prefs)
- [ ] Sound + music pass
- [ ] 1 internal playtest + fix critical bugs
- **Deliverable:** Smooth 5-min match, tutorial explains the game in 30s

### v0.5 — "Engagement Test" (target **2026-12-20**, re-baselined from 2026-10-10)
- [ ] Expand to 8 cards (add Reaper, Medic, Stim, Medivac)
- [ ] Battle Pass (7-day, 2 tiers)
- [ ] Daily login + daily missions
- [ ] Card pack rewards
- [ ] Rewarded ads integration
- [ ] Internal beta (10 testers)
- **Deliverable:** Closed beta build on TestFlight-equivalent Android track

### v0.8 — "Soft Launch" (target **2027-01-17**, re-baselined from 2026-10-24)
- [ ] TapTap China soft launch
- [ ] Balance pass based on telemetry
- [ ] Bug bash + crash rate <1%
- [ ] 12-card roster
- [ ] Visual polish pass (VFX, juice)
- **Deliverable:** Live on TapTap with 1000 DAU

### v1.0 — "Launch" (target **2027-02-07**, re-baselined from 2026-11-07)
- [ ] Google Play worldwide launch
- [ ] F2P economy live
- [ ] Cosmetics shop (3 sets)
- [ ] First paid Battle Pass
- [ ] Discord community + bug report channel
- **Deliverable:** Public Android launch, marketing push

### v1.5 — "PvP & Social" (Post-launch, target 2027-03-21)
- [ ] 1v1 async PvP (climb ladder)
- [ ] Clan system
- [ ] Leaderboards
- [ ] 1 more arena (different terrain)

---

## Schedule Re-baseline (2026-10-25)

Original chain assumed a 10-week run from 2026-08-29. Actual: the `7356a27`
skeleton landed 2026-10-16 (**34 days** after the 9/12 v0.1 target), and every
downstream milestone date had already passed unaddressed. Re-baselining the
whole chain from today rather than only v0.1:

| Milestone | Original | Re-baselined | Slip |
|---|---|---|---|
| v0.1 Playable Loop | 2026-09-12 | **2026-11-15** | +64d |
| v0.3 Pacing Pass | 2026-09-26 | 2026-12-06 | +71d |
| v0.5 Engagement Test | 2026-10-10 | 2026-12-20 | +71d |
| v0.8 Soft Launch | 2026-10-24 | 2027-01-17 | +85d |
| v1.0 Google Play Launch | 2026-11-07 | 2027-02-07 | +92d |

**Checkpoint discipline** (the actual lesson from the 34-day miss — no milestone
was reported as missed until it was long gone):
- **2026-10-29** — towers with HP + target priority + Marauder/Siege Tank stats — ✅ landed 10-27 (`c5e1ccd`)
- **2026-11-05** — card hand + deploy + enemy spawner — ✅ landed 10-28 (`86ec446`, `037f012`)
- **2026-11-12** — win/lose screen + asset pass — ✅ landed 10-28 (`037f012`); playtest still open
- **2026-10-29** — device playthrough of the v0.1 loop — ✅ done, and it caught the tap-to-deploy bug
- **2026-11-05** — Luminary call on the match-length target (retune vs restate)

### Known risks to v0.1

| Risk | Impact | Mitigation |
|---|---|---|
| Headless gates pass while the device is broken (the tap bug lived here for 3 days) | Green gates gave false confidence; the real feature was dead on the only surface the user touches | Gates now replay the **real Android event pair** (`tools/accept_tap_input.gd`); every v0.1 change is also verified by installing the APK and driving the actual UI |
| Match length ~30s vs the 3-minute deliverable | The headline deliverable reads as unmet, or worse, gets reported as met | Measure, don't estimate (`tools/measure_match.gd`); retune HP/cadence or restate the target — Luminary's call, v0.3 owns pacing |
| v0.1 ships 1 lane / 2 towers vs the GDD's 3 lanes + king tower | v0.1 does not exercise side-tower → king-tower activation or multi-lane targeting | Explicitly cut, tracked in v0.3 with its own checklist item |

## Roles

| Role | Who | Focus |
|---|---|---|
| CEO / Direction | Luminary | Big calls, monetization, marketing |
| Project Lead | **Nagi (me)** | Day-to-day, scope, scheduling, blockers |
| COO / Advisor | Mico | Daily patrol, cross-project alignment |
| (Future) Engineer | TBD | Once budget allows |
| (Future) Artist | TBD | Once budget allows |

For v0.1-v0.5: Nagi is sole executor using godogen pipeline + ComfyUI assets.

---

## Risks

| Risk | Mitigation |
|---|---|
| Godot 4.6 mobile performance (Android low-end) | Test on entry-level device weekly; GL Compatibility renderer; pixel-art = cheap |
| AI opponent too easy / too hard | Scripted phases (early = passive, mid = balanced, late = aggressive); tune by week 3 |
| Art pipeline bottleneck | ComfyUI batch generation upfront; 4 cards × 8 sprites (idle/walk/attack/death × 2 directions) = 64 sprites, doable in 1 day |
| Luminary shifts priority again | OK — park in `paused/` branch, resume when reprioritized |

---

## Definition of Done (per milestone)

- [ ] All milestone features shipped
- [x] APK builds cleanly (verified 2026-10-29: `build/starforge.apk` 28.2 MB, sha256 `d3a2214…`, installs + launches on Android emulator, AI opponent + result screen + SFX present)
- [x] Deploy flow verified **on device**, not only in headless gates (2026-10-29)
- [ ] No P0 bugs open
- [ ] Internal playtest (Nagi + Mico) passes
- [ ] Luminary notified with build link + test path

---

## Tooling

- **Godot 4.6** (`/opt/homebrew/bin/godot`)
- **JDK 17** (`/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`)
- **Gradle 8.6** (in android/ template)
- **gh CLI** for repo operations
- **godogen pipeline** for code generation
- **Local Python + PIL** for sprite assets (`tools/*_sprite_generator.py`) and local `wave` synthesis for SFX — 0 cost, no API keys

---

## Open Questions for Mico

1. Should Starforge be **public or private** repo on GitHub during dev?
   (Default: public, matching suika-game-android convention. Flag for Mico.)
2. **Cross-project resource sharing:** can Starlight Jump / Suika tooling (Java17 path, Gradle configs) be lifted into a shared `_tools/` repo?
3. **Telemetry:** which analytics SDK? (Firebase / Sentry / custom / none)
4. **PvP for v1.5:** do we self-host or use PlayFab/Photon?
