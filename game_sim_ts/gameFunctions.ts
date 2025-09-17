import { Player, Team } from "./roster";
import { ProducedBoxScore, TeamSummaryStats } from "./types";

// Special teams and fatigue utilities ported from Python `game_functions.py`.

export function simKickoff(kicker: Player): number {
  const kick_power = kicker.kick_power ?? 50;
  const kick_accuracy = kicker.kick_accuracy ?? 50;

  const base_distance = 45 + kick_power * 0.5;
  const variance = randUniform(-5, 5);
  const landing_yard = clamp(base_distance + variance, 0, 100);

  const out_of_bounds_chance = Math.max(0.15 - (kick_accuracy / 100) * 0.15, 0.01);
  if (Math.random() < out_of_bounds_chance) {
    return 40;
  }

  if (landing_yard >= 95) {
    return 25; // touchback
  }

  if (Math.random() < 0.1) {
    return 100 - Math.round(landing_yard); // fair catch
  }

  const return_yards = randInt(10, 35);
  let end_yard = 100 - landing_yard;
  end_yard += return_yards;
  return Math.round(end_yard);
}

export function simPat(kicker: Player, verbose = false): boolean {
  const base_chance = 0.94;
  const kick_accuracy = kicker.kick_accuracy ?? 50;
  const accuracy_adjustment = (kick_accuracy - 50) * 0.005;
  const make_chance = clamp(base_chance + accuracy_adjustment, 0.80, 0.99);

  kicker.stats.pat_attempts = (kicker.stats.pat_attempts ?? 0) + 1;
  const made = Math.random() < make_chance;
  if (made) kicker.stats.pat_made = (kicker.stats.pat_made ?? 0) + 1;
  if (verbose) {
    // eslint-disable-next-line no-console
    console.log(made ? `PAT is good! (${Math.floor(make_chance * 100)}% chance)` : `PAT missed! (${Math.floor(make_chance * 100)}% chance)`);
  }
  return made;
}

export function getKickAttemptRange(kicker: Player): number {
  const kick_range = 65;
  const kick_power = kicker.kick_power ?? 50;
  return Math.round(kick_range - (kick_power - 50) / 5);
}

export function getPuntDistance(punter: Player): number {
  const punt_power = punter.punt_power ?? 50;
  const punt_distance = Math.round(gauss(47, 4));
  return Math.round(punt_distance + (punt_power - 50) / 5);
}

export function applyBaselineFatigue(team: Team): void {
  for (const player of [...team.offense, ...team.defense]) {
    const base_chance = (100 - (player.endurance ?? 50)) / 10; // chance out of 100
    if (Math.random() < base_chance / 100) {
      const max_fatigue = base_chance;
      player.fatigue = randInt(1, Math.round(max_fatigue));
    } else {
      player.fatigue = 0;
    }
  }
}

export function applyGeneralFatigue(offense: Player[], defense: Player[]): void {
  const skill_positions = new Set(["RB", "TE", "WR", "CB", "OLB", "MLB", "ROLB", "S"]);
  for (const player of [...offense, ...defense]) {
    const isSkill = skill_positions.has(player.position);
    const base_fatigue = isSkill ? 1.8 : 0.1;
    const endurance_factor = (100 - (player.endurance ?? 50)) / 100;
    const fatigue = base_fatigue + endurance_factor * base_fatigue;
    player.fatigue = Math.min(100, player.fatigue + fatigue);
  }
}

export function applyPassFatigue(offense: Player[], defense: Player[], receiver?: Player, yards = 0): void {
  for (const player of offense) {
    if (!(["WR", "RB", "TE"] as string[]).includes(player.position)) continue;
    const base_fatigue = 1 + (100 - (player.endurance ?? 50)) / 80;
    let fatigue = base_fatigue;
    if (receiver && player === receiver) {
      const effort = 1 + yards / 10;
      fatigue = base_fatigue + effort * (1 + (100 - (player.endurance ?? 50)) / 100);
    }
    player.fatigue = Math.min(100, player.fatigue + Math.round(fatigue));
  }

  for (const player of defense) {
    if (!(["CB", "S", "OLB", "MLB", "ROLB", "LOLB"] as string[]).includes(player.position)) continue;
    const fatigue = 0.5 + (100 - (player.endurance ?? 50)) / 120;
    player.fatigue = Math.min(100, player.fatigue + Math.round(fatigue));
  }
}

export function applyRunFatigue(offense: Player[], defense: Player[], rusher?: Player, yards = 0): void {
  for (const player of offense) {
    if (!(["RB", "WR", "TE"] as string[]).includes(player.position)) continue;
    const base_fatigue = 1 + (100 - (player.endurance ?? 50)) / 80;
    let fatigue = base_fatigue * 0.75;
    if (rusher && player === rusher) {
      const effort = 1 + yards / 7;
      fatigue = base_fatigue + effort * (1 + (100 - (player.endurance ?? 50)) / 100);
    }
    player.fatigue = Math.min(100, player.fatigue + Math.round(fatigue));
  }

  for (const player of defense) {
    if ((["DL", "OLB", "MLB", "ROLB", "LOLB", "S"] as string[]).includes(player.position)) {
      const fatigue = 0.6 + (100 - (player.endurance ?? 50)) / 110;
      player.fatigue = Math.min(100, player.fatigue + Math.round(fatigue));
    }
  }
}

export function summarizeStats(team: Team): TeamSummaryStats {
  const totals: Record<string, number> = {};
  for (const player of [...team.offense, ...team.defense]) {
    for (const [k, v] of Object.entries(player.stats)) {
      if (typeof v === "number") totals[k] = (totals[k] ?? 0) + v;
    }
  }
  return {
    "Pass Attempts": totals["pass_attempts"] ?? 0,
    Completions: totals["completions"] ?? 0,
    "Pass Yards": totals["pass_yards"] ?? 0,
    "Interceptions Thrown": totals["interceptions_thrown"] ?? 0,
    "Sacks Taken": totals["sacks_taken"] ?? 0,
    Carries: totals["carries"] ?? 0,
    "Rush Yards": totals["rush_yards"] ?? 0,
    Fumbles: totals["fumbles"] ?? 0,
    Receptions: totals["receptions"] ?? 0,
    "Receiving Yards": totals["receiving_yards"] ?? 0,
    Targets: totals["targets"] ?? 0,
    Touchdowns: totals["touchdowns"] ?? 0,
    Tackles: totals["tackles"] ?? 0,
    Sacks: totals["sacks"] ?? 0,
    Interceptions: totals["interceptions"] ?? 0,
    "PATs Made": totals["pat_made"] ?? 0,
    "PATS Attempted": totals["pat_attempts"] ?? 0,
    "Field Goals Made": totals["fg_made"] ?? 0,
    "Field Goals Attempted": totals["fg_attempted"] ?? 0,
    Punts: totals["punts"] ?? 0,
    "Punt Yards": totals["punt_yards"] ?? 0,
  };
}

export function produceBoxScore(team1: Team, team2: Team, score1: number, score2: number, verbose = false): ProducedBoxScore {
  const stats1 = summarizeStats(team1);
  const stats2 = summarizeStats(team2);
  if (verbose) {
    // eslint-disable-next-line no-console
    console.log("\n=== Final Score ===");
    // eslint-disable-next-line no-console
    console.log(`${team1.name}: ${score1}`);
    // eslint-disable-next-line no-console
    console.log(`${team2.name}: ${score2}`);
    // eslint-disable-next-line no-console
    console.log("\n=== Team Comparison Box Score ===");
    // eslint-disable-next-line no-console
    console.log(`${pad("STAT", 25)}${pad(team1.name, 20)}${pad(team2.name, 20)}`);
    // eslint-disable-next-line no-console
    console.log("-".repeat(65));
    for (const key of Object.keys(stats1)) {
      // eslint-disable-next-line no-console
      console.log(`${pad(key, 25)}${pad(String((stats1 as any)[key]), 20)}${pad(String((stats2 as any)[key]), 20)}`);
    }
  }
  return {
    team1: { name: team1.name, score: score1, stats: stats1 },
    team2: { name: team2.name, score: score2, stats: stats2 },
  };
}

// --- helpers ---
function clamp(x: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, x));
}

function randInt(min: number, maxInclusive: number): number {
  return Math.floor(Math.random() * (maxInclusive - min + 1)) + min;
}

function randUniform(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

function gauss(mean: number, stdDev: number): number {
  // Box–Muller transform
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  return z * stdDev + mean;
}

function pad(s: string, w: number): string {
  if (s.length >= w) return s;
  return s + " ".repeat(w - s.length);
}


