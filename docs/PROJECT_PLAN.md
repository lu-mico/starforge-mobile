# Starforge Mobile — Project Plan

**Codename:** Starforge Mobile
**Owner:** Luminary (CEO) / Nagi (Project Lead) / Mico (COO, advisor)
**Target launch:** v1.0 in ~10 weeks from 2026-08-29

---

## Milestones

### v0.1 — "Playable Loop" (Week 1-2, target 2026-09-12)
- ✅ Godot 4 project scaffold + GitHub repo (THIS COMMIT)
- [ ] 1 arena, 3 lanes with side + king towers
- [ ] 4 units (Marine / Marauder / Hellion / Siege Tank) walk + attack + die
- [ ] Card hand (4 cards), drag-to-lane deploy
- [ ] Minerals HUD + regen
- [ ] Basic AI opponent (scripted deployment)
- [ ] Win/Lose screen
- [ ] APK builds + launches on Android emulator
- **Deliverable:** 3-min match you can finish vs AI on your phone

### v0.3 — "Pacing Pass" (Week 3-4, target 2026-09-26)
- [ ] Match timer + sudden death
- [ ] Tutorial (3 screens)
- [ ] Settings menu (audio, controls)
- [ ] Save/load (player prefs)
- [ ] Sound + music pass
- [ ] 1 internal playtest + fix critical bugs
- **Deliverable:** Smooth 5-min match, tutorial explains the game in 30s

### v0.5 — "Engagement Test" (Week 5-6, target 2026-10-10)
- [ ] Expand to 8 cards (add Reaper, Medic, Stim, Medivac)
- [ ] Battle Pass (7-day, 2 tiers)
- [ ] Daily login + daily missions
- [ ] Card pack rewards
- [ ] Rewarded ads integration
- [ ] Internal beta (10 testers)
- **Deliverable:** Closed beta build on TestFlight-equivalent Android track

### v0.8 — "Soft Launch" (Week 7-8, target 2026-10-24)
- [ ] TapTap China soft launch
- [ ] Balance pass based on telemetry
- [ ] Bug bash + crash rate <1%
- [ ] 12-card roster
- [ ] Visual polish pass (VFX, juice)
- **Deliverable:** Live on TapTap with 1000 DAU

### v1.0 — "Launch" (Week 9-10, target 2026-11-07)
- [ ] Google Play worldwide launch
- [ ] F2P economy live
- [ ] Cosmetics shop (3 sets)
- [ ] First paid Battle Pass
- [ ] Discord community + bug report channel
- **Deliverable:** Public Android launch, marketing push

### v1.5 — "PvP & Social" (Post-launch, target 2026-12-15)
- [ ] 1v1 async PvP (climb ladder)
- [ ] Clan system
- [ ] Leaderboards
- [ ] 1 more arena (different terrain)

---

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
- [ ] APK builds cleanly (Gradle + JDK 17 toolchain)
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
