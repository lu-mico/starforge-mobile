# Starforge Mobile

> Mobile lane-RTS inspired by StarCraft, built in Godot 4 for Android.

## Genre

Real-time strategy meets lane-battle (Clash Royale-style pacing). 5-8 minute matches, three lanes, auto-pushing units, destroy-the-king-tower victory.

## Status

**v0.1 (pre-dev)** — project scaffolding, GDD locked, awaiting implementation kickoff.

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
