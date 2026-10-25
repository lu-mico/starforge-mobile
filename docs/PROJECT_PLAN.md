# Starforge Mobile — Project Plan

**Codename:** Starforge Mobile
**Owner:** Luminary (CEO) / Nagi (Project Lead) / Mico (COO, advisor)
**Target launch:** v1.0 in ~10 weeks from 2026-08-29
**Re-baselined:** 2026-10-25 — original 9/12 -> 11/07 chain was blown (see "Schedule Re-baseline" below)

---

## Milestones

### v0.1 — "Playable Loop" (target **2026-11-15**, re-baselined from 2026-09-12)
- ✅ Godot 4 project scaffold + GitHub repo
- [ ] 1 arena, 3 lanes with side + king towers — **partial**: arena + 1 lane only; `EnemyTower` is a scriptless `StaticBody2D` (no HP, not in the `units` group, so units cannot target it)
- [ ] 4 units (Marine / Marauder / Hellion / Siege Tank) walk + attack + die — **partial**: 2 of 4 (Marine, Hellion); Marauder + Siege Tank missing. walk/attack/die all verified
- [ ] Card hand (4 cards), drag-to-lane deploy — **not started**: keyboard `1`/`2` spawn only
- ✅ Minerals HUD + regen (5 start / 10 max / 1 per 2.0s) — verified by `tests/smoke_test.tscn`
- [ ] Basic AI opponent (scripted deployment) — **not started**: no enemy spawner exists
- [ ] Win/Lose screen — **not started**
- ✅ APK builds + launches on Android emulator — verified 2026-10-25 (27.5 MB, installed + launched on `Medium_Phone_API_36.1`, no crash)
- **Deliverable:** 3-min match you can finish vs AI on your phone — **not yet met** (no AI opponent, no win/lose screen)

**Status 2026-10-25:** 3/8 done, 2 partial, 3 not started. Skeleton + economy + combat
+ APK pipeline all verified green. See "Schedule Re-baseline" below.

### v0.3 — "Pacing Pass" (target **2026-12-06**, re-baselined from 2026-09-26)
- [ ] Match timer + sudden death
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
- **2026-10-29** — towers with HP + target priority + Marauder/Siege Tank stats
- **2026-11-05** — card hand + drag-to-lane deploy + enemy spawner
- **2026-11-12** — win/lose screen + full-loop playtest + asset pass

### Known risks to v0.1

| Risk | Impact | Mitigation |
|---|---|---|
| `assets/` is **empty** (0 files) — every visual is a `ColorRect` placeholder | No shippable art; 4 cards x 8 sprites = 32-64 sprites needed | ComfyUI batch pass; ComfyUI was **down** during this audit (port 8188 refused) |
| No AI opponent exists yet | The "3-min match vs AI" deliverable is blocked on it | Scripted phase AI (early passive / mid balanced / late aggressive) per GDD |
| `EnemyTower` has no HP script and is not in the `units` group | Units can never damage it; no win condition is reachable | Towers become `Unit`-like with `take_damage()` + group membership |

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
- [x] APK builds cleanly (verified 2026-10-25: `build/starforge.apk` 27.5 MB, installs + launches on Android emulator)
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
- **ComfyUI / gemini-image** for sprite assets

---

## Open Questions for Mico

1. Should Starforge be **public or private** repo on GitHub during dev?
   (Default: public, matching suika-game-android convention. Flag for Mico.)
2. **Cross-project resource sharing:** can Starlight Jump / Suika tooling (Java17 path, Gradle configs) be lifted into a shared `_tools/` repo?
3. **Telemetry:** which analytics SDK? (Firebase / Sentry / custom / none)
4. **PvP for v1.5:** do we self-host or use PlayFab/Photon?
