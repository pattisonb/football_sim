import { Player, Team } from "./roster";
import { applyGeneralFatigue, getKickAttemptRange, getPuntDistance } from "./gameFunctions";
import { getPassYards, getRunYards } from "./playFunctions";

// Drive-level playcalling, penalties, downs, punts and field goals.

const RUN_PASS_TABLE: Record<number, Array<[number, number]>> = {
  1: [ [3, 0.75], [6, 0.65], [10, 0.55], [Number.POSITIVE_INFINITY, 0.40] ],
  2: [ [3, 0.70], [6, 0.50], [10, 0.40], [Number.POSITIVE_INFINITY, 0.25] ],
  3: [ [3, 0.60], [6, 0.35], [10, 0.20], [Number.POSITIVE_INFINITY, 0.10] ],
  4: [ [1, 0.55], [3, 0.35], [6, 0.20], [Number.POSITIVE_INFINITY, 0.05] ],
};

export function runProbability(down: number, to_go: number): number {
  const entries = RUN_PASS_TABLE[down] ?? [];
  for (const [thresh, prob] of entries) if (to_go <= thresh) return prob;
  return 0.25;
}

export function determineOffensePlay(down: number, first_down: number, last_play_type?: "run" | "pass" | null, last_gain = 0): "run" | "pass" {
  let run_chance = runProbability(down, first_down);
  if (last_play_type === "run" && last_gain >= 6) run_chance += 0.1;
  else if (last_play_type === "pass" && last_gain >= 10) run_chance -= 0.05;
  run_chance = Math.max(0.1, Math.min(0.9, run_chance));
  return Math.random() < run_chance ? "run" : "pass";
}

export function determineDefensePlay(down: number, first_down: number): "defend_run" | "defend_pass" {
  if (down === 1) {
    if (first_down <= 3) return Math.random() < 0.75 ? "defend_run" : "defend_pass";
    if (first_down <= 6) return Math.random() < 0.6 ? "defend_run" : "defend_pass";
    if (first_down <= 10) return Math.random() < 0.55 ? "defend_pass" : "defend_run";
    return Math.random() < 0.7 ? "defend_pass" : "defend_run";
  } else if (down === 2) {
    if (first_down <= 3) return Math.random() < 0.65 ? "defend_run" : "defend_pass";
    if (first_down <= 6) return Math.random() < 0.6 ? "defend_pass" : "defend_run";
    if (first_down <= 10) return Math.random() < 0.7 ? "defend_pass" : "defend_run";
    return Math.random() < 0.8 ? "defend_pass" : "defend_run";
  } else if (down === 3) {
    if (first_down <= 3) return Math.random() < 0.6 ? "defend_run" : "defend_pass";
    if (first_down <= 6) return Math.random() < 0.7 ? "defend_pass" : "defend_run";
    if (first_down <= 10) return Math.random() < 0.85 ? "defend_pass" : "defend_run";
    return Math.random() < 0.9 ? "defend_pass" : "defend_run";
  }
  return "defend_pass"; // 4th down default
}

export function determineLineAdvantage(offense: Player[], defense: Player[], offense_play: "run" | "pass", defense_play: "defend_run" | "defend_pass"): number {
  let offense_blocking = 0;
  for (const p of offense) {
    if (p.position === "OL" || (offense_play === "run" && p.position === "TE")) {
      offense_blocking += p.strength ?? 50;
      if (offense_play === "run") offense_blocking += p.run_blocking ?? 50;
      else offense_blocking += p.pass_blocking ?? 50;
    }
  }
  let defense_rushing = 0;
  for (const p of defense) {
    if (p.position === "DL" || (defense_play === "defend_run" && p.position.includes("LB"))) {
      defense_rushing += p.strength ?? 50;
      defense_rushing += p.rushing ?? 50;
    }
  }
  return offense_blocking - defense_rushing;
}

export function simPlay(
  offense_team: Team,
  defense_team: Team,
  down: number,
  first_down_yardage: number,
  yardline: number,
  hurrying = false,
  last_play_type: "run" | "pass" | null = null,
  last_gain = 0,
  verbose = true
): ["run" | "pass" | "penalty", "offensive penalty" | "defensive penalty" | "run" | "successful_pass" | "checkdown_pass" | "interception" | "sack" | "incomplete" | "fumble", number, number] {
  applyGeneralFatigue(offense_team.get_offense(), defense_team.get_defense());
  offense_team.apply_fatigue_penalties();
  defense_team.apply_fatigue_penalties();
  offense_team.sub_skill_position_players(50);
  defense_team.sub_defensive_players(50);
  offense_team.recover_bench_players();
  defense_team.recover_bench_players();

  const offense = offense_team.get_offense();
  const defense = defense_team.get_defense();

  let time_spent = hurrying ? randInt(10, 25) : randInt(25, 40);

  // Offensive penalty ~8%
  if (Math.random() < 0.08) {
    const penaltyType = weightedChoice([
      "false_start",
      "holding",
      "offensive_pass_interference",
      "delay_of_game",
    ], [0.3, 0.4, 0.15, 0.15]);
    let penalty_yards = 0;
    if (penaltyType === "false_start") penalty_yards = -5;
    else if (penaltyType === "holding") penalty_yards = -10;
    else if (penaltyType === "offensive_pass_interference") penalty_yards = -15;
    else if (penaltyType === "delay_of_game") penalty_yards = -5;
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log(`Penalty: ${toTitle(penaltyType.replace(/_/g, " "))} for ${Math.abs(penalty_yards)} yards`);
    }
    return ["penalty", "offensive penalty", penalty_yards, time_spent];
  }

  // Defensive penalty ~5%
  if (Math.random() < 0.05) {
    const penaltyType = weightedChoice(["offside", "pass_interference", "facemask"], [0.4, 0.4, 0.2]);
    let yards = 0;
    if (penaltyType === "offside") yards = 5;
    else if (penaltyType === "pass_interference") yards = randInt(10, 25);
    else if (penaltyType === "facemask") yards = 15;
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log(`Defensive Penalty: ${toTitle(penaltyType.replace(/_/g, " "))}`);
    }
    return ["penalty", "defensive penalty", yards, time_spent];
  }

  const offense_play = determineOffensePlay(down, first_down_yardage, last_play_type, last_gain);
  const defense_play = determineDefensePlay(down, first_down_yardage);
  const offense_line_advantage = determineLineAdvantage(offense, defense, offense_play, defense_play);
  const guessed_play = offense_play === "run" ? defense_play === "defend_run" : defense_play === "defend_pass";

  if (offense_play === "run") {
    const [result, yards_gained] = getRunYards(offense, defense, down, first_down_yardage, guessed_play, offense_line_advantage, yardline);
    return ["run", result, yards_gained, time_spent];
  } else {
    const [result, yards_gained] = getPassYards(offense, defense, down, first_down_yardage, guessed_play, offense_line_advantage, yardline);
    return ["pass", result, yards_gained, time_spent];
  }
}

export function processPlay(result: string, play_type: string, yards: number, yardline: number, down: number, first_down_yardage: number): [number, number, number] {
  if (result === "fumble" || result === "interception") down = 5;
  if (result === "run" || result === "successful_pass") {
    yardline += yards; first_down_yardage -= yards; down += 1;
  }
  if (result === "offensive penalty") {
    const pre = yardline; yardline = Math.max(0, yardline + yards); const actual = pre - yardline; first_down_yardage += actual;
  }
  if (result === "defensive penalty") {
    const pre = yardline; yardline = Math.min(99, yardline + yards); const actual = yardline - pre; first_down_yardage = Math.max(0, first_down_yardage - actual);
  }
  if (result === "sack") { down += 1; yardline += yards; first_down_yardage -= yards; }
  if (result === "incomplete") { down += 1; }
  if (first_down_yardage <= 0) { down = 1; first_down_yardage = 10; }
  if (yardline >= 100) { down = 6; }
  return [down, first_down_yardage, yardline];
}

export function shouldGoForIt(distance: number, yardline: number): boolean {
  if (yardline < 50) return distance <= 1 && Math.random() < 0.3;
  if (distance <= 2 && yardline >= 50 && yardline < 70) return Math.random() < 0.5;
  if (yardline > 85) return distance <= 5 && Math.random() < 0.6;
  return false;
}

export function attemptKick(yardline: number, kicker: Player): boolean {
  kicker.stats.fg_attempted = (kicker.stats.fg_attempted ?? 0) + 1;
  const kick_distance = (100 - yardline) + 17;
  let make = 1;
  if (kick_distance <= 30) make = 0.98;
  else if (kick_distance <= 39) make = 0.94;
  else if (kick_distance <= 49) make = 0.85;
  else if (kick_distance <= 55) make = 0.65;
  else make = 0.4;
  const kick_accuracy = kicker.kick_accuracy ?? 50;
  make = Math.max(0.05, Math.min(1.0, make + (kick_accuracy - 50) * 0.005));
  const made = Math.random() < make;
  if (made) kicker.stats.fg_made = (kicker.stats.fg_made ?? 0) + 1;
  return made;
}

export function attemptPunt(yardline: number, punter: Player): [number, number] {
  const punt_distance = getPuntDistance(punter);
  const punt_accuracy = punter.punt_accuracy ?? 50;
  const landing_spot = yardline + punt_distance;
  punter.stats.punts = (punter.stats.punts ?? 0) + 1;
  if (landing_spot + 10 < 100) {
    punter.stats.punt_yards = (punter.stats.punt_yards ?? 0) + punt_distance;
    return [landing_spot, punt_distance];
  }
  const accuracy_factor = (punt_accuracy - 50) / 100;
  const pin_chance = 0.25 + accuracy_factor;
  if (landing_spot >= 95) {
    if (Math.random() < pin_chance) {
      const pinned = randInt(1, 4);
      punter.stats.punt_yards = (punter.stats.punt_yards ?? 0) + (100 - pinned - yardline);
      return [100 - pinned, 100 - pinned - yardline];
    } else {
      punter.stats.punt_yards = (punter.stats.punt_yards ?? 0) + (100 - yardline - 20);
      return [80, 100 - yardline - 20];
    }
  }
  const return_yards = landing_spot < 90 ? randInt(0, 15) : 0;
  const final_spot = Math.max(landing_spot - return_yards, 1);
  punter.stats.punt_yards = (punter.stats.punt_yards ?? 0) + (final_spot - yardline);
  return [final_spot, final_spot - yardline];
}

export function simDrive(
  offense: Team,
  defense: Team,
  down: number,
  first_down_yardage: number,
  yardline: number,
  seconds_remaining: number,
  hurrying = false,
  verbose = true
): ["run" | "pass", "touchdown" | "field goal" | "punt" | "missed kick" | "turnover", number, number] {
  const kicker = offense.get_offense().find((p) => p.position === "K")!;
  const punter = offense.get_offense().find((p) => p.position === "P")!;
  let last_play_type: "run" | "pass" | null = null;
  let last_gain = 0;
  let result = "" as any;
  while (down < 4) {
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log(down, "and", first_down_yardage, "at the", yardline);
    }
    const [play_ran, res, yards_gained, time] = simPlay(offense, defense, down, first_down_yardage, yardline, hurrying, last_play_type, last_gain, false);
    seconds_remaining -= time;
    [down, first_down_yardage, yardline] = processPlay(res, play_ran, yards_gained, yardline, down, first_down_yardage);
    last_play_type = play_ran as any;
    last_gain = typeof yards_gained === "number" ? yards_gained : 0;
  }
  if (down === 4) {
    if (shouldGoForIt(first_down_yardage, yardline)) {
      const [play_ran, res, yards_gained, time] = simPlay(offense, defense, down, first_down_yardage, yardline, hurrying, last_play_type, last_gain, false);
      seconds_remaining -= time;
      [down, first_down_yardage, yardline] = processPlay(res, play_ran, yards_gained, yardline, down, first_down_yardage);
    } else {
      if (yardline >= getKickAttemptRange(kicker)) {
        const kick_time = randInt(5, 7);
        seconds_remaining -= kick_time;
        if (attemptKick(yardline, kicker)) {
          if (verbose) {
            // eslint-disable-next-line no-console
            console.log((100 - yardline) + 17, "yard kick is good!");
          }
          result = "field goal";
        } else {
          result = "missed kick";
        }
      } else {
        const [newYard, puntDist] = attemptPunt(yardline, punter);
        const punt_time = randInt(6, 10);
        seconds_remaining -= punt_time;
        if (verbose) {
          // eslint-disable-next-line no-console
          console.log(puntDist, "yard punt.");
        }
        yardline = newYard;
        result = "punt";
      }
    }
  }
  if (down === 5) result = "turnover";
  if (down === 6) result = "touchdown";
  return [last_play_type || "run", result, yardline, seconds_remaining];
}

// --- helpers ---
function randInt(min: number, maxInclusive: number): number {
  return Math.floor(Math.random() * (maxInclusive - min + 1)) + min;
}
function weightedChoice<T>(items: T[], weights: number[]): T {
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (let i = 0; i < items.length; i++) { r -= weights[i]; if (r <= 0) return items[i]; }
  return items[items.length - 1];
}
function toTitle(s: string): string { return s.replace(/\b\w/g, (c) => c.toUpperCase()); }


