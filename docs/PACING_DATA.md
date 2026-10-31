# Pacing Data — the v0.3 retune's evidence

**Added:** 2026-10-31 (v0.3 Pacing Pass prep)
**Owner:** Nagi
**Why:** the v0.3 Pacing Pass retunes lane speed, AI cadence and tower HP against
a **~3-minute match**. Every number in that retune has to come from played
matches, not from estimates — the same lesson that caught the v0.1 wording
("3-minute match" vs the measured ~30s). This file documents the recorder that
makes that possible.

---

## What is recorded

One JSON object per finished match, written the moment the match ends (the
result screen appears):

| Field | Meaning |
|---|---|
| `result` | `VICTORY` / `DEFEAT` |
| `duration_s` | game seconds from match start to the result screen |
| `taps` | lane taps that landed inside the deploy band |
| `deploys` | units the player actually deployed |
| `card_selects` | card taps (selected or deselected) |
| `actions` | `taps + card_selects + deploys` — how busy the player was |
| `minerals_spent` | minerals the player spent |
| `player_lost` | player units that died |
| `enemy_lost` | enemy units the player killed |
| `cards` | per card: `deployed` / `lost` / `alive` |
| `ts`, `unix`, `build` | when it happened, and which build |

## Where it lands

```
user://stats/matches.jsonl    one JSON object per line, oldest first
user://stats/summary.json     the aggregate over every match on the device
```

`user://` is the app's own storage. On Android that is internal app storage,
so a match comes off the device with:

```bash
adb shell run-as <pkg> cat files/stats/matches.jsonl
adb shell run-as <pkg> cat files/stats/summary.json
```

On a desktop run of the project the same files are under the Godot user data
folder (`~/Library/Application Support/Godot/app_userdata/Starforge Mobile/stats/`
on macOS).

## The summary — the win/loss distribution

`summary.json` is recomputed from `matches.jsonl` every time a match ends, so
it can never drift from the raw records:

```json
{
  "matches": 12, "victories": 7, "defeats": 5, "win_rate": 0.583,
  "avg_duration_s": 29.4, "avg_deploys": 8.1, "avg_actions": 19.7,
  "cards": { "marine": { "deployed": 31, "lost": 18, "alive": 13,
                         "matches_played": 9, "matches_won": 5,
                         "win_rate": 0.556 } }
}
```

The per-card `win_rate` is the number the retune starts from: the card that
is deployed in the matches the player goes on to win is the card to keep; the
card that loses its matches is the card to fix.

## What the v0.3 retune will read it for

1. **Match length.** `avg_duration_s` is the number the ~3-minute target is
   compared against. Measured, not estimated.
2. **Player pressure.** `avg_actions` and `avg_deploys` say how much the player
   is doing per match — the retune changes how often the player has to act.
3. **Card balance.** The per-card `deployed / lost / win_rate` say which card
   carries the win and which card dies for nothing.
4. **Outcome balance.** `victories / defeats` over a real play session says
   whether the AI is beatable but not trivial.

## Rules of the recorder

- **A headless gate never writes to the real file.** The gates run with
  `--script`, and `MatchStats` refuses to persist in that mode, so synthetic
  matches (a script tapping the lane) cannot pollute the data the retune
  reads. `set_output_dir()` turns persistence back on for a specific folder —
  that is how the acceptance gate tests the writer without touching the real
  file.
- **One record per match.** The arena starts a record when it appears (which
  is also after every RESTART, because the scene is reloaded) and writes it
  when the match ends.
- **The clock is game time, not wall time.** The recorder accumulates the
  scaled frame delta, so `duration_s` is what the player experienced even if
  the engine is running at a different frame rate.

## Verified on a real device (2026-10-31)

The recorder was verified on the Android emulator (`Medium_Phone_API_36.1`,
APK rebuilt and installed), not only in headless gates:

1. Launch the app, tap the marine card and the lane a few times.
2. Let the match end.
3. Pull the files off the device:

```bash
adb shell run-as com.starforge.game cat files/stats/matches.jsonl
adb shell run-as com.starforge.game cat files/stats/summary.json
```

What came off the device after one tap session (6 card taps, 5 lane taps):

```json
{"actions":15,"card_selects":6,"cards":{"marine":{"alive":0,"deployed":4,"lost":4}},
 "deploys":4,"duration_s":135.68,"minerals_spent":12,"player_lost":4,"result":"DEFEAT",
 "schema":1,"taps":5,"build":"0.1.0-alpha.1","ts":"2026-10-31T11:34:11"}
```

and the summary over it:

```json
{"matches":1,"victories":0,"defeats":1,"win_rate":0.0,"avg_duration_s":135.68,
 "avg_deploys":4.0,"avg_actions":15.0,
 "cards":{"marine":{"deployed":4,"lost":4,"matches_played":1,"matches_won":0,"win_rate":0.0}}}
```

So the file path, the counters and the aggregate all work on the surface the
player actually touches. (The first device match on the same build was an idle
one: `DEFEAT` after 31.6s, zero deploys — the same number the headless
measurement gives, 32.6s.)

## The gate

`tools/accept_pacing_stats.gd` (27 checks) plays two full matches — one the
"player" wins by tapping the lane the way a phone does (the real Android event
pair: the emulated mouse event plus the screen touch), one the player never
touches — and then reads the file back:

- a finished match lands in `matches.jsonl`, and a second match **appends**
- the recorded duration equals the recorder's own clock, and is consistent with
  the match the gate measured
- deploys / taps / card selects / actions / minerals are counted
- the per-card counters add up (`deployed == lost + alive`)
- the untouched match is a `DEFEAT` with zero deploys
- `summary.json` holds the win/loss distribution and the per-card win rate

```bash
godot --headless --import
godot --headless --script tools/accept_pacing_stats.gd
```
