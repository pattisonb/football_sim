# Football Sim Engine

This is a full-featured, relatively realistic American football simulation engine written entirely in Python. It emphasizes player stats, fatigue, substitutions, penalties, and play calling logic to mimic the nuances of a real football game.

No external frameworks are required—just pure Python logic and data structures.

---

## File Overview

### `sim_game.py`
Entry point of the simulation. Simply calls `simulate_full_game()` from `start_game.py`. Run this when you want to simulate a full game.

---

### `start_game.py`
Handles the overall flow of the game:
- Loads teams from `rosters.json`
- Applies baseline fatigue to players
- Conducts a virtual coin toss
- Simulates two halves using `start_half()`
- Tracks scoring and possession
- Prints final stats using `pretty_print_stats()`
- Calls `produce_box_score()` to display final output

---

### `rosters.json`
Defines all player and team data. Each player has:
- Basic attributes: `position`, `speed`, `strength`, `intelligence`, etc.
- Role-specific stats (e.g., `passing`, `tackling`, `route_running`)
- A `stats` dictionary that tracks in-game performance
- An `in_game` flag to determine if the player is on the field

You can customize this file to simulate different matchups.

---

### `roster.py`

#### `Player`
Represents a single player and loads data from JSON. Includes methods like:
- `is_offense()` / `is_defense()`
- `fatigue_level()`

Also stores a snapshot of original attributes for fatigue tracking.

#### `Team`
Wraps a collection of `Player` instances and provides:
- Active player retrieval (`get_offense()`, `get_defense()`)
- Bench recovery (`recover_bench_players()`)
- Fatigue-based substitutions
- Kicker identification and fatigue penalty logic

---

### `drive_functions.py`

Core simulation of individual plays and drives.

- `sim_play()`: Handles one play, including penalties and fatigue
- `process_play()`: Updates down, yardage, and drive state
- `determine_offense_play()` / `determine_defense_play()`: Decides play type
- `determine_line_advantage()`: Calculates trench advantage based on strength and blocking

Also includes logic for play tempo and random penalty generation.

---

### `play_functions.py`

Detailed implementation of play outcomes:

- `get_run_yards()`: Chooses a ball carrier, adjusts for stats and line play, computes fumble chance and big plays
- `get_pass_yards()`: Simulates passing play with coverage, sack, interception, and completion checks
- `handle_qb_scramble()`: Logic for QB scrambling
- `assign_tackles()` / `assign_sack()` / `assign_forced_fumble()`: Assigns credit based on proximity, stats, and randomness

This file contains the bulk of the on-field logic.

---

### `game_functions.py`

Utility functions for special teams and fatigue:

- `sim_kickoff()`: Computes kickoff yardline and return outcomes
- `sim_pat()`: Simulates PAT attempts
- `get_kick_attempt_range()` / `get_punt_distance()`: Range calculators for kickers
- Fatigue logic: `apply_general_fatigue()`, `apply_pass_fatigue()`, `apply_run_fatigue()`
- `summarize_stats()`: Returns summarized team-level stats for box scores

---

## Game Flow Summary

1. `sim_game.py` launches the simulation.
2. `start_game.py` loads rosters and starts both halves.
3. Each half loops through drives (`sim_drive`) and plays (`sim_play`).
4. Plays use `play_functions.py` logic to resolve outcomes.
5. Scoring, fatigue, and stats are updated throughout.

---

## How to Run

```bash
python sim_game.py
```

Everything runs from that single command.

---

## Notes

- Fatigue influences performance and triggers automatic substitutions
- Player decisions and outcomes are based on ratings and randomness
- You can modify rosters to create custom scenarios or full seasons
- Currently outputs to terminal, but could be hooked into a UI or exported easily

---