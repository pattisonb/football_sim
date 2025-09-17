import { Player } from "./roster";
import { applyPassFatigue, applyRunFatigue } from "./gameFunctions";

// Core play outcome logic ported from Python `play_functions.py`.
// The goal is feature parity while keeping the same probabilities and effects.

export function handleQbScramble(qb: Player, verbose = false): number | null {
  const intelligence = qb.intelligence ?? 50;
  const speed = qb.speed ?? 50;
  let scramble_chance = Math.max(0.05, (100 - intelligence) / 150);
  if (speed < 60) scramble_chance *= 0.5;
  if (Math.random() > scramble_chance) return null;

  const gain_odds = Math.min(0.95, Math.max(0.1, 0.5 + (speed - 50) / 100));
  const gain_yards = randInt(1, 12);
  const lose_yards = -randInt(1, 6);
  const yards = Math.random() < gain_odds ? gain_yards : lose_yards;
  return yards;
}

export function assignForcedFumble(defense: Player[], base_yards: number, verbose = false): Player {
  let valid: string[];
  if (base_yards <= 2) valid = ["rolb", "olb", "mlb"];
  else if (base_yards <= 7) valid = ["rolb", "olb", "mlb", "s"];
  else valid = ["cb", "s"];

  let candidates = defense.filter((p) => valid.includes(p.position.toLowerCase()));
  if (!candidates.length) candidates = defense;
  const weights = candidates.map((p) => ((p.tackling ?? 50) + (p.strength ?? 50)) / 2);
  const forced_by = weightedChoice(candidates, weights);
  forced_by.stats.forced_fumbles = (forced_by.stats.forced_fumbles ?? 0) + 1;
  if (verbose) {
    // eslint-disable-next-line no-console
    console.log(`Fumble forced by ${forced_by.name} (${forced_by.position})`);
  }
  return forced_by;
}

export function assignTackles(defense: Player[], base_yards: number, verbose = false): Player[] {
  const shortW = { dl: 0.35, rolb: 0.2, olb: 0.15, lb: 0.2, s: 0.1 } as Record<string, number>;
  const midW = { rolb: 0.25, olb: 0.2, lb: 0.25, s: 0.2, dl: 0.1 } as Record<string, number>;
  const longW = { s: 0.4, cb: 0.4, rolb: 0.08, olb: 0.06, lb: 0.06 } as Record<string, number>;
  const profile = base_yards <= 2 ? shortW : base_yards <= 7 ? midW : longW;

  const candidates: Player[] = [];
  const weights: number[] = [];
  let cbCount = 0;
  for (const p of defense) {
    const pos = p.position.toLowerCase();
    const posGroup = profile[pos] != null ? pos : pos.slice(0, 2);
    if (posGroup === "cb" && cbCount >= 3) continue;
    if (profile[posGroup] != null) {
      const skillWeight = ((p.tackling ?? 50) + (p.intelligence ?? 50)) / 2;
      candidates.push(p);
      weights.push(profile[posGroup] * skillWeight);
      if (posGroup === "cb") cbCount += 1;
    }
  }
  if (!candidates.length) {
    return [weightedChoice(defense, defense.map((p) => ((p.tackling ?? 50) + (p.intelligence ?? 50)) / 2))];
  }

  const isAssisted = Math.random() < 0.35;
  if (isAssisted && candidates.length >= 2) {
    const picks = weightedSampleNoReplace(candidates, weights, 2);
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log(`Tackle by ${picks[0].name} (solo) and ${picks[1].name} (assist)`);
    }
    return picks;
  }
  const solo = weightedChoice(candidates, weights);
  if (verbose) {
    // eslint-disable-next-line no-console
    console.log(`Tackle by ${solo.name} (solo)`);
  }
  return [solo];
}

export function assignSack(defense: Player[], guessed_play = false): { sackers: Player[]; is_half: boolean } {
  let candidates = defense.filter((p) => p.position === "DL" || (guessed_play && p.position.includes("LB")));
  if (!candidates.length) return { sackers: [], is_half: false };
  const is_half = Math.random() < 0.25;
  const k = is_half ? 2 : 1;
  const weights = candidates.map((p) => p.rushing ?? 50);
  const selected = weightedSampleWithReplace(candidates, weights, k);
  return { sackers: selected, is_half };
}

export function getRunYards(
  offense: Player[],
  defense: Player[],
  down: number,
  first_down: number,
  guessed_play: boolean,
  offense_line_advantage: number,
  yardline: number,
  verbose = false
): ["fumble" | "run", number] {
  let base_yards = 4.5;
  if (down === 2) base_yards -= 0.5;
  else if (down === 3) base_yards -= 5.5;
  if (down === 3 && first_down > 6) base_yards *= 0.75;

  base_yards *= 1 + offense_line_advantage / 750;

  for (const player of defense) {
    if (!["DL", "OLB", "MLB", "ROLB"].includes(player.position)) continue;
    const tackle_val = player.tackling ?? 50;
    const factor = tackle_val >= 50 ? tackle_val / 250 : (100 - tackle_val) / 250;
    const chance = (tackle_val >= 50 ? tackle_val / 100 : (100 - tackle_val) / 100) * 0.5;
    if (Math.random() < chance) base_yards *= tackle_val >= 50 ? 1 - factor : 1 + factor;
  }

  const candidates = offense.filter(
    (p) => p.position === "RB" || p.position === "WR" || (p.position === "QB" && (p.speed ?? 50) > 60)
  );
  const weights = candidates.map((p) => (p.position === "RB" ? 0.8 : p.position === "WR" ? 0.03 : (p.speed ?? 50) / 1000));
  const rushing_player = weightedChoice(candidates, weights);

  for (const key of ["speed", "strength", "intelligence", "elusiveness", "vision"] as const) {
    if ((key === "elusiveness" || key === "vision") && rushing_player.position !== "RB") continue;
    const val = (rushing_player as any)[key] ?? 50;
    const factor = val >= 50 ? val / 250 : (100 - val) / 250;
    const chance = (val >= 50 ? val / 100 : (100 - val) / 100) * 0.5;
    if (Math.random() < chance) base_yards *= val >= 50 ? 1 + factor : 1 - factor;
  }

  const fumble_base = 0.003;
  const strength_factor = (100 - (rushing_player.strength ?? 50)) / 100;
  const intel_factor = (100 - (rushing_player.intelligence ?? 50)) / 100;
  const fumble_chance = fumble_base + strength_factor * 0.005 + intel_factor * 0.005;
  if (Math.random() < fumble_chance) {
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log("Fumble lost by", rushing_player.name);
    }
    rushing_player.stats.carries = (rushing_player.stats.carries ?? 0) + 1;
    rushing_player.stats.rush_yards = (rushing_player.stats.rush_yards ?? 0) + Math.round(base_yards);
    rushing_player.stats.fumbles = (rushing_player.stats.fumbles ?? 0) + 1;
    applyRunFatigue(offense, defense, rushing_player, base_yards);
    const ff = assignForcedFumble(defense, base_yards);
    ff.stats.forced_fumbles = (ff.stats.forced_fumbles ?? 0) + 1;
    ff.stats.tackles = (ff.stats.tackles ?? 0) + 1;
    return ["fumble", 0];
  }

  if ((rushing_player.speed ?? 50) > 75 && Math.random() < 0.1) {
    base_yards += randInt(15, 40);
  }
  if (guessed_play && Math.random() < 0.5) base_yards += -randInt(1, 10);
  if (first_down <= 2 && base_yards > -1.25 && Math.random() < 0.6) base_yards = first_down;
  if (base_yards < 2.0) base_yards = Math.max(base_yards, randUniform(1.5, 3.5));

  if (verbose) {
    // eslint-disable-next-line no-console
    console.log("Rush for", Math.round(base_yards), "yards by", rushing_player.name);
  }
  if (yardline + base_yards > 100) {
    rushing_player.stats.touchdowns = (rushing_player.stats.touchdowns ?? 0) + 1;
    base_yards = 100 - yardline;
  }
  rushing_player.stats.carries = (rushing_player.stats.carries ?? 0) + 1;
  rushing_player.stats.rush_yards = (rushing_player.stats.rush_yards ?? 0) + Math.round(base_yards);
  applyRunFatigue(offense, defense, rushing_player, base_yards);
  const tacklers = assignTackles(defense, base_yards);
  for (const t of tacklers) t.stats.tackles = (t.stats.tackles ?? 0) + 1;
  return ["run", Math.round(base_yards)];
}

export function getPassYards(
  offense: Player[],
  defense: Player[],
  down: number,
  first_down: number,
  guessed_play: boolean,
  offense_line_advantage: number,
  yardline: number,
  verbose = false
): ["fumble" | "sack" | "successful_pass" | "checkdown_pass" | "interception" | "run" | "incomplete", number] {
  const qb = offense.find((p) => p.position === "QB")!;
  let sack_rate = 0.005 + 0.005 * down;
  if (guessed_play) sack_rate += 0.1;
  sack_rate -= offense_line_advantage / 5000;
  if (Math.random() < sack_rate) {
    const sack_yards = -Math.abs(Math.round(gauss(8, 2)));
    const { sackers, is_half } = assignSack(defense, guessed_play);
    for (const s of sackers) {
      s.stats.sacks = (s.stats.sacks ?? 0) + (is_half ? 0.5 : 1);
      s.stats.tackles = (s.stats.tackles ?? 0) + 1;
    }
    qb.stats.sacks_taken = (qb.stats.sacks_taken ?? 0) + 1;
    const strength_factor = (100 - (qb.strength ?? 50)) / 100;
    const intel_factor = (100 - (qb.intelligence ?? 50)) / 100;
    const fumble_chance = 0.02 + strength_factor * 0.01 + intel_factor * 0.005;
    if (Math.random() < fumble_chance) {
      qb.stats.fumbles = (qb.stats.fumbles ?? 0) + 1;
      for (const s of sackers) s.stats.forced_fumbles = (s.stats.forced_fumbles ?? 0) + (is_half ? 0.5 : 1);
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log("Fumble lost by", qb.name);
      }
      applyPassFatigue(offense, defense);
      return ["fumble", yardline + sack_yards];
    }
    applyPassFatigue(offense, defense);
    return ["sack", sack_yards];
  }

  const coverage_players: string[] = ["CB", "S"]; if (guessed_play) coverage_players.push("LOLB", "MLB", "ROLB");
  const coverage_factor = defense
    .filter((p) => coverage_players.includes(p.position))
    .reduce((a, p) => a + (p.coverage ?? 50) / 1000, 0);
  const defense_speed = defense.filter((p) => ["CB", "S"].includes(p.position)).map((p) => p.speed ?? 50);
  const avg_def_speed = defense_speed.length ? defense_speed.reduce((a, b) => a + b, 0) / defense_speed.length : 50;

  let completion_chance = 0.35 + ((qb.intelligence ?? 50) + (qb.passing ?? 50) + (qb.decision_making ?? 50)) / 1000;
  let receiving_candidates = offense.filter((p) => ["WR", "TE"].includes(p.position));
  receiving_candidates = weightedShuffle(receiving_candidates, receiving_candidates.map((p) => ((p.route_running ?? 50) + (p.hands ?? 50) + (p.intelligence ?? 50)) / 3));

  if (down === 3 || yardline > 80) {
    for (const p of receiving_candidates) if (p.position === "TE") completion_chance += 0.05;
  }

  let receiving_player: Player | null = null;
  for (const player of receiving_candidates) {
    const route_running_factor = ((player.route_running ?? 50) - 50) / 200;
    const speed_factor = ((player.speed ?? 50) - 50) / 300;
    completion_chance = completion_chance + route_running_factor + speed_factor - coverage_factor / 1.9;
    if (completion_chance < 0) completion_chance = 0.01;
    if (Math.random() < completion_chance) {
      receiving_player = player; break;
    }
    completion_chance -= 0.05;
  }

  if (receiving_player) {
    let base_yards = gauss(9.5, 4);
    const speed_factor = (receiving_player.speed ?? 50) / avg_def_speed;
    base_yards *= speed_factor;
    if (speed_factor > 1 && Math.random() < 0.1) base_yards = randInt(20, 70);
    let yards = Math.min(Math.round(base_yards), 40);
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log("Pass for", yards, "yards to", receiving_player.name);
    }
    if (yards + yardline > 100) {
      yards = 100 - yardline;
      qb.stats.touchdowns = (qb.stats.touchdowns ?? 0) + 1;
      receiving_player.stats.touchdowns = (receiving_player.stats.touchdowns ?? 0) + 1;
    } else {
      const tacklers = assignTackles(defense, yards);
      for (const t of tacklers) t.stats.tackles = (t.stats.tackles ?? 0) + 1;
    }
    qb.stats.pass_attempts = (qb.stats.pass_attempts ?? 0) + 1;
    qb.stats.completions = (qb.stats.completions ?? 0) + 1;
    qb.stats.pass_yards = (qb.stats.pass_yards ?? 0) + yards;
    receiving_player.stats.targets = (receiving_player.stats.targets ?? 0) + 1;
    receiving_player.stats.receptions = (receiving_player.stats.receptions ?? 0) + 1;
    receiving_player.stats.receiving_yards = (receiving_player.stats.receiving_yards ?? 0) + yards;
    applyPassFatigue(offense, defense, receiving_player, yards);
    return ["successful_pass", yards];
  }

  if (Math.random() < 0.18) {
    const rbs = offense.filter((p) => p.position === "RB");
    if (rbs.length) {
      const rb = rbs[Math.floor(Math.random() * rbs.length)];
      let yards = gauss(3, 2);
      if (Math.random() < (rb.speed ?? 50) / 100) yards += randInt(1, 9);
      yards = Math.round(Math.max(0, yards));
      if (yards + yardline > 100) {
        yards = 100 - yardline;
        qb.stats.touchdowns = (qb.stats.touchdowns ?? 0) + 1;
        rb.stats.touchdowns = (rb.stats.touchdowns ?? 0) + 1;
      } else {
        const tacklers = assignTackles(defense, yards);
        for (const t of tacklers) t.stats.tackles = (t.stats.tackles ?? 0) + 1;
      }
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log("Checkdown for", yards, "yards to", rb.name);
      }
      qb.stats.pass_attempts = (qb.stats.pass_attempts ?? 0) + 1;
      qb.stats.completions = (qb.stats.completions ?? 0) + 1;
      qb.stats.pass_yards = (qb.stats.pass_yards ?? 0) + yards;
      rb.stats.targets = (rb.stats.targets ?? 0) + 1;
      rb.stats.receptions = (rb.stats.receptions ?? 0) + 1;
      rb.stats.receiving_yards = (rb.stats.receiving_yards ?? 0) + yards;
      applyPassFatigue(offense, defense, rb, yards);
      return ["checkdown_pass", yards];
    }
  }

  let highest_chance = 0;
  let best_defender: Player | null = null;
  for (const p of defense) {
    if (!coverage_players.includes(p.position)) continue;
    let chance = 0.02 + (p.coverage ?? 50) / 10000;
    if (guessed_play) chance += 0.005;
    chance += (100 - (qb.decision_making ?? 50)) / 2000;
    if (chance > highest_chance) { highest_chance = chance; best_defender = p; }
  }
  if (best_defender && Math.random() < Math.min(highest_chance, 0.03)) {
    if (verbose) {
      // eslint-disable-next-line no-console
      console.log("Intercepted by", best_defender.name);
    }
    qb.stats.pass_attempts = (qb.stats.pass_attempts ?? 0) + 1;
    qb.stats.interceptions_thrown = (qb.stats.interceptions_thrown ?? 0) + 1;
    best_defender.stats.interceptions = (best_defender.stats.interceptions ?? 0) + 1;
    applyPassFatigue(offense, defense);
    return ["interception", yardline + 10];
  }

  const scramble = handleQbScramble(qb, false);
  if (scramble != null) {
    let s = scramble;
    if (s + yardline > 100) {
      s = 100 - yardline;
      qb.stats.touchdowns = (qb.stats.touchdowns ?? 0) + s;
    } else {
      const tacklers = assignTackles(defense, s);
      for (const t of tacklers) t.stats.tackles = (t.stats.tackles ?? 0) + 1;
    }
    qb.stats.carries = (qb.stats.carries ?? 0) + 1;
    qb.stats.rush_yards = (qb.stats.rush_yards ?? 0) + Math.round(s);
    applyRunFatigue(offense, defense, qb, s);
    return ["run", s];
  }

  const receiving_candidates2 = offense.filter((p) => ["WR", "TE", "RB"].includes(p.position));
  const weights2 = receiving_candidates2.map((p) => (p.position === "RB" ? 1 : ((p.route_running ?? 50) + (p.hands ?? 50) + (p.intelligence ?? 50)) / 3));
  const total_non_rb = weights2.reduce((a, w, i) => a + (receiving_candidates2[i].position !== "RB" ? w : 0), 0);
  const rb_count = receiving_candidates2.filter((p) => p.position === "RB").length;
  let rb_weight = 0;
  if (rb_count > 0) rb_weight = (0.01 * total_non_rb) / rb_count;
  const adjustedWeights = weights2.map((w, i) => (receiving_candidates2[i].position === "RB" ? rb_weight : w));
  const intended = weightedChoice(receiving_candidates2, adjustedWeights);
  qb.stats.pass_attempts = (qb.stats.pass_attempts ?? 0) + 1;
  intended.stats.targets = (intended.stats.targets ?? 0) + 1;
  applyPassFatigue(offense, defense);
  return ["incomplete", 0];
}

// --- helpers ---
function randInt(min: number, maxInclusive: number): number {
  return Math.floor(Math.random() * (maxInclusive - min + 1)) + min;
}
function randUniform(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}
function gauss(mean: number, stdDev: number): number {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  return z * stdDev + mean;
}
function weightedChoice<T>(items: T[], weights: number[]): T {
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (let i = 0; i < items.length; i++) {
    r -= weights[i];
    if (r <= 0) return items[i];
  }
  return items[items.length - 1];
}
function weightedSampleNoReplace<T>(items: T[], weights: number[], k: number): T[] {
  const result: T[] = [];
  const poolItems = items.slice();
  const poolWeights = weights.slice();
  for (let i = 0; i < k && poolItems.length; i++) {
    const pick = weightedChoice(poolItems, poolWeights);
    const idx = poolItems.indexOf(pick);
    result.push(pick);
    poolItems.splice(idx, 1);
    poolWeights.splice(idx, 1);
  }
  return result;
}
function weightedSampleWithReplace<T>(items: T[], weights: number[], k: number): T[] {
  const result: T[] = [];
  for (let i = 0; i < k; i++) result.push(weightedChoice(items, weights));
  return result;
}
function weightedShuffle<T>(items: T[], weights: number[]): T[] {
  const pairs = items.map((it, i) => ({ it, w: weights[i], r: Math.random() }));
  pairs.sort((a, b) => b.w - a.w || a.r - b.r);
  return pairs.map((p) => p.it);
}


