// TypeScript type definitions for the Football Simulation Engine
// These types mirror the Python data model so that logic can be ported 1:1.

export type Position =
  | "QB"
  | "RB"
  | "WR"
  | "TE"
  | "OL"
  | "K"
  | "P"
  | "DL"
  | "ROLB"
  | "MLB"
  | "LOLB"
  | "CB"
  | "S";

export type Side = "offense" | "defense";

// PlayerStats tracks all numeric performance stats collected during a game.
// The Python engine uses a free-form dict; here we constrain known fields and
// still allow arbitrary numeric extensions via an index signature.
export interface PlayerStats {
  pass_attempts?: number;
  completions?: number;
  pass_yards?: number;
  interceptions_thrown?: number;
  sacks_taken?: number;
  carries?: number;
  rush_yards?: number;
  fumbles?: number;
  receptions?: number;
  receiving_yards?: number;
  targets?: number;
  touchdowns?: number;
  tackles?: number;
  sacks?: number; // can be 0.5 increments; we will store as number
  interceptions?: number;
  pat_made?: number;
  pat_attempts?: number;
  fg_made?: number;
  fg_attempted?: number;
  punts?: number;
  punt_yards?: number;
  forced_fumbles?: number; // added in play logic
  [statName: string]: number | undefined;
}

// RawPlayerData represents the JSON structure for one player from rosters.json
export interface RawPlayerData {
  name: string;
  position: Position;
  speed?: number;
  strength?: number;
  intelligence?: number;
  endurance?: number;
  fatigue?: number;
  in_game?: boolean;
  stats?: PlayerStats;
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
}

export interface RawTeamData {
  team_name: string;
  offense: RawPlayerData[];
  defense: RawPlayerData[];
}

export interface RawLeagueData {
  teams: RawTeamData[];
}

// Summarized team-level stats used for the box score output.
export interface TeamSummaryStats {
  [key: string]: number;
}

export interface ProducedBoxScoreTeam {
  name: string;
  score: number;
  stats: TeamSummaryStats;
}

export interface ProducedBoxScore {
  team1: ProducedBoxScoreTeam;
  team2: ProducedBoxScoreTeam;
}


