import { PlayerStats, Position, RawPlayerData, RawTeamData } from "./types";

// Player mirrors the Python Player class, including a snapshot of original
// attributes for fatigue penalties.
export class Player {
  name: string;
  position: Position;
  speed: number;
  strength: number;
  intelligence: number;
  endurance: number;
  fatigue: number;
  in_game: boolean;
  stats: PlayerStats;

  // Skill-specific
  passing?: number;
  decision_making?: number;
  elusiveness?: number;
  vision?: number;
  hands?: number;
  route_running?: number;
  run_blocking?: number;
  pass_blocking?: number;
  rushing?: number;
  tackling?: number;
  coverage?: number;
  kick_power?: number;
  kick_accuracy?: number;
  punt_power?: number;
  punt_accuracy?: number;

  private _originalAttrs: Partial<Record<string, number>>;

  constructor(data: RawPlayerData) {
    this.name = data.name;
    this.position = data.position;
    this.speed = data.speed ?? 50;
    this.strength = data.strength ?? 50;
    this.intelligence = data.intelligence ?? 50;
    this.endurance = data.endurance ?? 50;
    this.fatigue = data.fatigue ?? 0;
    this.in_game = data.in_game ?? false;
    this.stats = { ...(data.stats ?? {}) };

    this.passing = data.passing;
    this.decision_making = data.decision_making;
    this.elusiveness = data.elusiveness;
    this.vision = data.vision;
    this.hands = data.hands;
    this.route_running = data.route_running;
    this.run_blocking = data.run_blocking;
    this.pass_blocking = data.pass_blocking;
    this.rushing = data.rushing;
    this.tackling = data.tackling;
    this.coverage = data.coverage;
    this.kick_power = data.kick_power;
    this.kick_accuracy = data.kick_accuracy;
    this.punt_power = data.punt_power;
    this.punt_accuracy = data.punt_accuracy;

    this._originalAttrs = {
      speed: this.speed,
      strength: this.strength,
      elusiveness: this.elusiveness,
      vision: this.vision,
      hands: this.hands,
      route_running: this.route_running,
      run_blocking: this.run_blocking,
      pass_blocking: this.pass_blocking,
      rushing: this.rushing,
      tackling: this.tackling,
      coverage: this.coverage,
    };
  }

  is_offense(): boolean {
    return ["QB", "RB", "WR", "TE", "OL", "K", "P"].includes(this.position);
  }

  is_defense(): boolean {
    return ["DL", "ROLB", "MLB", "LOLB", "CB", "S"].includes(this.position);
  }

  fatigue_level(): number {
    return this.fatigue / Math.max(this.endurance, 1);
  }
}

export class Team {
  name: string;
  offense: Player[];
  defense: Player[];

  constructor(name: string, offense: RawPlayerData[], defense: RawPlayerData[]) {
    this.name = name;
    this.offense = offense.map((p) => new Player(p));
    this.defense = defense.map((p) => new Player(p));
  }

  get_offense(side: "offense" | "defense" = "offense"): Player[] {
    const players = (this as any)[side] as Player[];
    return players.filter((p) => p.in_game);
  }

  get_all_offense(side: "offense" | "defense" = "offense"): Player[] {
    const players = (this as any)[side] as Player[];
    return [...players];
  }

  get_defense(side: "offense" | "defense" = "defense"): Player[] {
    const players = (this as any)[side] as Player[];
    return players.filter((p) => p.in_game);
  }

  get_all_defense(side: "offense" | "defense" = "defense"): Player[] {
    const players = (this as any)[side] as Player[];
    return [...players];
  }

  get_player_by_name(name: string): Player | undefined {
    return [...this.offense, ...this.defense].find((p) => p.name === name);
  }

  recover_bench_players(): void {
    for (const p of [...this.offense, ...this.defense]) {
      if (!p.in_game) {
        const recovery = p.endurance / 10;
        p.fatigue = Math.max(0, p.fatigue - recovery);
      }
    }
  }

  sub_skill_position_players(fatigue_threshold = 50): void {
    const skillPositions: Position[] = ["RB", "WR", "TE"] as Position[];
    const statSum = (player: Player) =>
      Object.values(player.stats).reduce((a, b) => a + (b ?? 0), 0);

    for (const pos of skillPositions) {
      const starters = this.offense.filter(
        (p) => p.position === pos && p.in_game && p.fatigue > fatigue_threshold
      );
      if (!starters.length) continue;

      const bench = this.offense
        .filter((p) => p.position === pos && !p.in_game && p.fatigue <= fatigue_threshold)
        .sort((a, b) => {
          const statDiff = statSum(b) - statSum(a);
          if (statDiff !== 0) return statDiff;
          return a.fatigue - b.fatigue;
        });
      if (!bench.length) continue;

      for (const tired of starters) {
        const sub = bench.shift();
        if (!sub) break;
        tired.in_game = false;
        sub.in_game = true;
      }
    }
  }

  sub_defensive_players(fatigue_threshold = 50): void {
    const positions = new Set(this.defense.map((p) => p.position));
    const statSum = (player: Player) =>
      Object.values(player.stats).reduce((a, b) => a + (b ?? 0), 0);

    for (const pos of positions) {
      const tiredPlayers = this.defense.filter(
        (p) => p.position === pos && p.in_game && p.fatigue > fatigue_threshold
      );
      if (!tiredPlayers.length) continue;

      const bench = this.defense
        .filter((p) => p.position === pos && !p.in_game && p.fatigue <= fatigue_threshold)
        .sort((a, b) => {
          const fatigueDiff = a.fatigue - b.fatigue; // freshest first
          if (fatigueDiff !== 0) return fatigueDiff;
          return statSum(b) - statSum(a); // then more productive
        });
      if (!bench.length) continue;

      for (const tired of tiredPlayers) {
        const fresh = bench.shift();
        if (!fresh) break;
        tired.in_game = false;
        fresh.in_game = true;
      }
    }
  }

  get_kicker(): Player | undefined {
    return this.offense.find((p) => p.position === "K");
  }

  apply_fatigue_penalties(): void {
    for (const player of [...this.offense, ...this.defense]) {
      const fatiguePct = player.fatigue / 100;
      const penaltyScale = fatiguePct * 0.15; // max 15% drop

      const original = (player as any)._originalAttrs as Record<string, number | undefined>;
      for (const [attr, originalValue] of Object.entries(original)) {
        if (originalValue == null) continue;
        const minAllowed = Math.round(originalValue * (2 / 3));
        const newValue = Math.round(originalValue * (1 - penaltyScale));
        (player as any)[attr] = Math.max(minAllowed, newValue);
      }
    }
  }
}

export function initializeTeams(rawTeams: RawTeamData[]): Team[] {
  return rawTeams.map((t) => {
    const team = new Team(t.team_name, t.offense, t.defense);
    const anyOffenseActive = team.offense.some((p) => p.in_game);
    const anyDefenseActive = team.defense.some((p) => p.in_game);
    // Fallback: if no starters flagged in roster JSON, activate everyone
    if (!anyOffenseActive) team.offense.forEach((p) => (p.in_game = true));
    if (!anyDefenseActive) team.defense.forEach((p) => (p.in_game = true));
    return team;
  });
}


