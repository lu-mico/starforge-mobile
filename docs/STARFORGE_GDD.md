# Starforge Mobile — Game Design Document

**Version:** 0.1 (locked 2026-08-29)
**Author:** Nagi (Project Lead)
**Approved by:** Luminary (CEO)

---

## 1. Elevator Pitch

A real-time lane-battle mobile game where two commanders clash across three lanes with auto-deploying units, hero abilities, and a single resource. 5-8 minute matches. StarCraft-flavored units and aesthetic, Clash Royale pacing.

**Tagline:** _"Command the swarm. Burn their core."_

---

## 2. Core Loop

```
[Match Start]
   ↓
[Deploy units from hand → unit walks lane → auto-attacks enemies/towers]
   ↓
[Resource (Minerals) regenerates over time → unlocks more unit cards]
   ↓
[Side towers fall → King Tower activates → final push]
   ↓
[King Tower destroyed = match ends]
   ↓
[Win → +XP / +Currency / +Trophies] → Next match
```

**Match length target:** 4:00 base + 1:00 sudden death = **3-6 min realistic**.

---

## 3. Resource: Minerals

Single resource (StarCraft-flavored; one stat to track on mobile).

| Property | Value |
|---|---|
| Starting minerals | 5 |
| Max minerals | 10 |
| Regen rate | 1 per 2.0 sec (increases slowly during match: 1 per 1.7s at 3:00 mark) |
| Visual | Top-center HUD bar with crystal icon, animates on gain |

---

## 4. The Arena (3 Lanes)

```
   [Enemy Base]
   [E-King] [E-Tower-L] [E-Tower-R]
       |         |          |
     [Lane L]  [Mid Lane] [Lane R]
       |         |          |
   [P-Tower-L] [P-Tower-R] [P-King]
   [Player Base]
```

- 3 parallel lanes (left, middle, right)
- Each side has **2 side towers** (Towers of each lane) + **1 King Tower** (center, behind both side towers)
- Side tower HP: 2500 / King Tower HP: 4500
- When side tower falls, King Tower becomes active (can deploy troops from its zone)
- Troops auto-walk their lane, auto-attack nearest enemy (troop → tower priority)

---

## 5. Card Hand & Deployment

**Hand size:** 4 cards visible at bottom of screen.
**Deck size:** 8 cards per commander (chosen pre-match).
**Deploy:** tap card → drag to lane → release to spawn.

### v0.1 MVP Card Roster (4 cards total — proves the loop)

| Card | Cost | Rarity | HP | DPS | Speed | Role |
|---|---|---|---|---|---|---|
| **Marine** | 3 | Common | 200 | 25 | Fast (90 px/s) | Ranged, ground, anti-swarm |
| **Marauder** | 4 | Rare | 500 | 35 | Slow (55 px/s) | Heavy, ground, anti-armor |
| **Hellion** | 4 | Rare | 350 | 30 | Fast (130 px/s) | Anti-light, dodge-roll charges |
| **Siege Tank** | 7 | Epic | 900 | 80 | Very slow (30 px/s) | Long-range siege, deploys to siege mode |

### v0.5 Expansion (8 cards)

Add: **Reaper** (5, jumps walls), **Medic** (3, heals nearby), **Stim Pack** (2 spell, +50% AS/MS for 4s), **Medivac Drop** (5 spell, drops 2 Marines behind enemy lines).

### v1.0 Expansion (12 cards + 1 commander hero ability)

Adds hero units with 3-use abilities: **Ghost (Nuke)**, **Battlecruiser (Yamato Cannon)**.

---

## 6. Combat Rules

- **Target priority:** troops > towers > king tower (within range)
- **Range:** melee (Marine base 60px) vs ranged (Siege Tank 350px siege)
- **Death:** at 0 HP, unit removed + small crystal shatter VFX
- **Friendly fire:** off (units ignore allies)
- **Spells:** AOE effects respect friendly fire = off (same as Clash Royale convention)

---

## 7. Win / Lose

| Condition | Result |
|---|---|
| Destroy enemy King Tower | WIN (+30 trophies, +50 XP) |
| Your King Tower destroyed | LOSE (-20 trophies, +25 XP for participation) |
| Timer hits 6:00 with no winner | Sud death: 2x DPS for both sides until king falls |
| Disconnect / quit | LOSE (forfeit penalty) |

---

## 8. Monetization (F2P mobile)

### v0.1 (release) — zero monetization, pure gameplay validation
### v0.5 (public test) — engagement hooks
- Daily login bonus (1 card pack)
- Win 3 matches → unlock new card
- Battle Pass (7-day, free tier + $4.99 premium tier)

### v1.0 (launch) — full F2P economy
- **Soft currency:** Credits (earned by matches)
- **Hard currency:** Crystals ($0.99 per 100)
- **Card packs:** 100 Credits common, 250 rare, 500 epic
- **IAP:** Remove-ads pass $4.99, Premium Battle Pass $9.99/season, Cosmetics $1.99-$4.99
- **Rewarded ads:** +25% post-match XP, free card pack every 4h

---

## 9. Visual & Audio Direction

- **Style:** 2D pixel-art (32×32 sprites scaled 2x on mobile), StarCraft color palette (blue HUD, orange enemy, neutral gray terrain)
- **Lanes:** parallel horizontal tracks with simple terrain texture (no scrolling)
- **HUD:** top = minerals, mid = arena, bottom = card hand
- **Music:** synth + orchestral, StarCraft-evocative but original
- **SFX:** unit death (zap), tower hit (thud), card deploy (whoosh)

---

## 10. Out of Scope (v0.1)

- ❌ Multiplayer PvP (vs AI only for v0.1; PvP at v1.0)
- ❌ Multiple arenas (1 arena for v0.1)
- ❌ Multiple factions (1 faction for v0.1)
- ❌ Clan / social systems
- ❌ Story / campaign mode

---

## 11. Success Metrics (v0.5 → v1.0 gate)

| Metric | v0.5 Target | v1.0 Target |
|---|---|---|
| Day-1 retention | 35% | 45% |
| Day-7 retention | 12% | 20% |
| Avg match length | 4:30 | 5:00 |
| Tutorial completion | 80% | 90% |
| Crash rate | <2% | <0.5% |
| ARPDAU | $0.02 | $0.08 |
