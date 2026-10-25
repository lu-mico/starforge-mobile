# Starforge Mobile

> Mobile lane-RTS inspired by StarCraft, built in Godot 4 for Android.

## Genre

Real-time strategy meets lane-battle (Clash Royale-style pacing). 5-8 minute matches, three lanes, auto-pushing units, destroy-the-king-tower victory.

## Status

**v0.1.0-alpha.1** — playable skeleton, in active development.

| | Status |
|---|---|
| Godot 4.6 project + GitHub repo | ✅ |
| Mineral economy (5/10, +1 per 2.0s) | ✅ verified by `tests/smoke_test.tscn` |
| Marine + Hellion: walk / attack / take damage / die | ✅ verified |
| APK builds + installs + launches on Android emulator | ✅ verified 2026-10-25 |
| 3 lanes + towers with HP | 🔶 1 lane, `EnemyTower` has no HP script |
| 4-unit roster | 🔶 2 of 4 (Marauder + Siege Tank pending) |
| Card hand + drag-to-lane deploy | ❌ keyboard `1`/`2` spawn only |
| AI opponent | ❌ not started |
| Win/Lose screen | ❌ not started |

Target: v0.1 **2026-11-15** (re-baselined from 2026-09-12 — see
[Project Plan](docs/PROJECT_PLAN.md#schedule-re-baseline-2026-10-25)).

## Quick Links

- [Game Design Doc](docs/STARFORGE_GDD.md)
- [Project Plan & Milestones](docs/PROJECT_PLAN.md)
- [Mechanics Spec](docs/game_mechanics_spec.md)

## Tech Stack

- **Engine:** Godot 4.6 (GL Compatibility renderer for mobile)
- **Language:** GDScript
- **Build target:** Android (APK via Gradle 8.6 + JDK 17)
- **Asset pipeline:** ComfyUI / gemini-image for sprite generation
- **Distribution:** Google Play + TapTap (China)

## Project Layout

```
starforge-mobile/
├── scenes/
│   ├── main/         # Main menu, splash, settings
│   ├── ui/           # HUD, hand of cards, build buttons
│   └── battle/       # Arena, lanes, towers
├── src/
│   ├── core/         # Game state, resource manager, match loop
│   ├── units/        # Unit definitions, behavior, AI
│   ├── buildings/    # Tower behavior, damage, death
│   └── ui/           # Touch controls, card hand
├── assets/
│   ├── sprites/      # Unit / tower / spell art
│   ├── audio/        # SFX, music
│   └── fonts/        # Pixel fonts for HUD
├── docs/             # GDD, plan, specs
└── android/          # Godot Android export template
```

## License

Proprietary — © Luminary Organization.
