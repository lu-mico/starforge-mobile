# Starforge Mobile — Mechanics Spec (Stub)

**Status:** v0.1 scaffolding. Detailed mechanics to be filled as features ship.

This document will contain:
- Unit stat blocks (HP, DPS, range, speed, abilities)
- Tower stat blocks
- Mineral economy curve
- AI behavior tree
- Damage formula
- Deploy rules (spawn radius, cooldowns)

Detailed mechanics for v0.1 MVP units:

## Marine
- HP: 200
- DPS: 25 (rate: 0.4s/shot = 5 shots in 2s)
- Range: 60px (ranged — fires while walking)
- Speed: 90 px/s
- Target priority: nearest enemy troop > nearest enemy tower > enemy king
- Behavior: walks lane, stops to shoot when in range

## Marauder
- HP: 500
- DPS: 35 (slow shots, 0.6s/shot)
- Range: 50px (melee-ish)
- Speed: 55 px/s
- Damage type: Concussive (+50% vs armored, -25% vs light)
- Behavior: front-liner, holds ground to fire

## Hellion
- HP: 350
- DPS: 30 (rapid, 0.25s/shot)
- Range: melee
- Speed: 130 px/s (fast)
- Special: charge that does 3x damage on first contact
- Behavior: zips ahead, skirmishes, then circles back

## Siege Tank
- HP: 900
- DPS: 80 (slow shots, 1.0s/shot)
- Range: 350px (long)
- Speed: 30 px/s (slow walk)
- Damage type: Explosive (splash, 80px radius)
- Special: deploys to siege mode (immobile, +50% range, +25% damage)
- Behavior: walks lane, auto-deploys at 200px from enemy tower
