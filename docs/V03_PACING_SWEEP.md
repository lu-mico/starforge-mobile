# v0.3 Pacing Sweep — the first measured grid

**Measured:** 2026-11-10, headless, on branch `feature/v0.3-pacing`
**Harness:** `tools/tune_pacing.gd`
**Why:** the v0.3 Pacing Pass retunes toward **~3 minutes per match**. The
frozen-unit fix changes who wins, so no v0.1 number can be reused as-is —
every candidate has to be measured, not estimated (same discipline that caught
the v0.1 "3-minute" wording).

---

## How it was measured

The harness runs the **real arena scene** headless with the tuning knobs
applied to the live scene (tower `max_hp`/`_hp`, AI `first_spawn_delay` /
`spawn_interval`), three player behaviours per config, and prints the duration
and the result of each match:

- **idle** — the player never deploys (can the AI close a match on its own?)
- **defender** — the player spends every mineral, best unit first (siege tank →
  marauder → marine → hellion)
- **marine** — the player only ever buys Marines (the weakest realistic card)

```bash
godot --headless --script tools/tune_pacing.gd
```

The sweep runs the game at `Engine.time_scale = 10`, so **the durations it
prints are game seconds**, not wall-clock. The watchdog is a real-time budget
(`ignore_time_scale = true`, 1800 s) — a scaled watchdog expired after 90 real
seconds and cut the first run off after 2 of 4 configs (fixed 2026-11-10).

## The grid (2026-11-10)

| tower_hp | ai_first | ai_interval | idle | defender | marine-only |
|---|---|---|---|---|---|
| 3600 | 30.0 | 18.0 | DEFEAT 65.0s | VICTORY 173.5s | VICTORY 170.5s |
| 4200 | 30.0 | 18.0 | DEFEAT 70.1s | VICTORY 205.8s | VICTORY 189.7s |
| 4200 | 36.0 | 18.0 | DEFEAT 76.1s | VICTORY 180.2s | VICTORY 196.8s |
| 4800 | 36.0 | 21.0 | DEFEAT 81.4s | VICTORY 222.5s | VICTORY 201.8s |

(repeat run of the first two configs: 64.3s / 173.5s / 169.4s and 70.2s /
191.0s / 194.7s — i.e. the same numbers within ~10s run-to-run)

## What the grid says

1. **The idle player is always crushed, and fast** — 65s to 81s. That is the
   "player does nothing" floor and it is nowhere near 3 minutes.
2. **The defender wins, but the match still ends in 2.9-3.7 minutes of game
   time only when the AI is slowed** — 173.5s to 222.5s. The 3-minute target
   sits *inside* this band, but only for the defender; the idle match is
   roughly half the target.
3. **One duration number cannot serve both player types.** A single match
   length has to be set by the **slower** side, otherwise a passive player is
   ejected at half the intended pace. The retune therefore has to pick which
   scenario defines "a match" — and that is a **design call for Luminary**,
   not something the numbers decide.
4. **The grid is a candidate set, not a decision.** Nothing here is merged.
   `main` still runs 1200 tower HP / AI first unit 18s / one every 9s.

## Gate consequence (measured, same branch)

The frozen-unit fix (`src/units/Unit.gd`, validity check before the type
check) is what makes these numbers meaningful — but it also removes the
defender's v0.1 win **at v0.1 numbers**:

| gate | main | `feature/v0.3-pacing` |
|---|---|---|
| `tools/accept_pacing_stats.gd` (27 checks) | **PASS** | **FAIL 4/27** — both played matches DEFEAT, win rate 0.000 |
| `tools/accept_sfx_wiring.gd` (25) | PASS | PASS |
| `tools/accept_match_result.gd` (24) | PASS | PASS |
| `tools/accept_ui.gd` (118) | PASS | PASS |
| `tools/accept_tower_feedback.gd` (40) | PASS | PASS |
| `tools/accept_tap_input.gd` (8) | PASS | PASS |
| `tests/smoke_test.tscn` (14/14) | PASS | PASS |

The pacing-stats gate is the one gate that encodes the old balance (it expects
one VICTORY and one DEFEAT from its two scripted matches). Re-balancing means
either the gate's expectation or the new balance changes — **after** Luminary
picks the target scenario, not before.

## Next

1. Luminary decides which scenario defines a match length (defender-driven
   ~3 min vs idle-driven ~3 min vs "both within 2-4 min").
2. Pick the config from the grid (or extend it) that satisfies it.
3. Re-run the full gate suite, rebuild the APK, device pass.
4. Only then merge `feature/v0.3-pacing` into `main`.
