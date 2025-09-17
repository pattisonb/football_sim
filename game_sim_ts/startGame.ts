import { Team, initializeTeams } from "./roster";
import { produceBoxScore, simKickoff, simPat, applyBaselineFatigue } from "./gameFunctions";
import { simDrive } from "./driveFunctions";

export function determineReceivingTeam(receive_prob = 0.8): "home" | "away" {
  const toss_winner: "home" | "away" = Math.random() < 0.5 ? "home" : "away";
  return Math.random() < receive_prob ? toss_winner : toss_winner === "home" ? "away" : "home";
}

export function startHalf(
  home_team: Team,
  away_team: Team,
  receiving_team_str: "home" | "away",
  score_dict: Record<string, number>,
  half = 1,
  verbose = false
): Record<string, number> {
  let seconds_remaining = 2000;
  let driving_team = receiving_team_str === "home" ? home_team : away_team;
  let kicking_team = driving_team === home_team ? away_team : home_team;

  const kickoff_yardline = simKickoff(kicking_team.get_kicker()!);
  seconds_remaining -= randInt(4, 12);
  let start_yardline = kickoff_yardline;

  if (verbose) {
    // eslint-disable-next-line no-console
    console.log(`\n=== START OF HALF ${half} ===`);
  }

  while (seconds_remaining > 0) {
    const offense = driving_team;
    const defense = driving_team === home_team ? away_team : home_team;
    const hurrying = seconds_remaining <= 120;

    const [play_ran, result, yardline, new_time] = simDrive(
      offense, defense, 1, 10, start_yardline, seconds_remaining, hurrying, false
    );
    seconds_remaining = new_time;

    if (result === "touchdown") {
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log(`${driving_team.name} TOUCHDOWN!`, play_ran);
      }
      score_dict[driving_team.name] += 6;
      if (simPat(driving_team.get_kicker()!)) {
        if (verbose) {
          // eslint-disable-next-line no-console
          console.log(`${driving_team.name} PAT is GOOD.`);
        }
        score_dict[driving_team.name] += 1;
      } else if (verbose) {
        // eslint-disable-next-line no-console
        console.log(`${driving_team.name} PAT is NO GOOD.`);
      }
      start_yardline = simKickoff(driving_team.get_kicker()!);
    } else if (result === "field goal") {
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log(`${driving_team.name} FIELD GOAL is GOOD.`);
      }
      score_dict[driving_team.name] += 3;
      start_yardline = simKickoff(driving_team.get_kicker()!);
    } else if (result === "punt") {
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log(`${driving_team.name} punts.`);
      }
      start_yardline = 100 - yardline;
    } else if (result === "missed kick") {
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log(`${driving_team.name} missed a field goal.`);
      }
      start_yardline = 100 - yardline;
    } else if (result === "turnover") {
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log(`${driving_team.name} turned it over.`);
      }
      start_yardline = 100 - yardline;
    }
    driving_team = driving_team === home_team ? away_team : home_team;
  }

  if (verbose) {
    // eslint-disable-next-line no-console
    console.log(`--- End of Half ${half} ---`);
    // eslint-disable-next-line no-console
    console.log(`Score: ${home_team.name} ${score_dict[home_team.name]} - ${away_team.name} ${score_dict[away_team.name]}\n`);
  }
  return score_dict;
}

export function prettyPrintStats(team: Team, side: "offense" | "defense" | "both" = "both"): void {
  if (side === "offense" || side === "both") {
    // eslint-disable-next-line no-console
    console.log(`\n== ${team.name} Offensive Stats ==`);
    for (const player of team.get_all_offense()) {
      const sum = Object.values(player.stats).reduce((a, b) => a + (b ?? 0), 0);
      if (sum > 0) {
        // eslint-disable-next-line no-console
        console.log(`${player.name} (${player.position}):`);
        for (const [stat, val] of Object.entries(player.stats)) if ((val ?? 0) > 0) console.log(`  ${toTitle(stat.replace(/_/g, " "))}: ${val}`);
        // eslint-disable-next-line no-console
        console.log("");
      }
    }
  }
  if (side === "defense" || side === "both") {
    // eslint-disable-next-line no-console
    console.log(`\n== ${team.name} Defensive Stats ==`);
    for (const player of team.get_all_defense()) {
      const sum = Object.values(player.stats).reduce((a, b) => a + (b ?? 0), 0);
      if (sum > 0) {
        // eslint-disable-next-line no-console
        console.log(`${player.name} (${player.position}):`);
        for (const [stat, val] of Object.entries(player.stats)) if ((val ?? 0) > 0) console.log(`  ${toTitle(stat.replace(/_/g, " "))}: ${val}`);
        // eslint-disable-next-line no-console
        console.log("");
      }
    }
  }
}

export function simulateFullGame(rawTeams: Parameters<typeof initializeTeams>[0], verbose = true) {
  const teams = initializeTeams(rawTeams);
  const home_team = teams[0];
  const away_team = teams[1];
  applyBaselineFatigue(home_team);
  applyBaselineFatigue(away_team);
  const score: Record<string, number> = { [home_team.name]: 0, [away_team.name]: 0 };
  const receiving_team_first_half = determineReceivingTeam();
  startHalf(home_team, away_team, receiving_team_first_half, score, 1, verbose);
  const receiving_team_second_half = receiving_team_first_half === "home" ? "away" : "home";
  startHalf(home_team, away_team, receiving_team_second_half, score, 2, verbose);
  produceBoxScore(home_team, away_team, score[home_team.name], score[away_team.name], verbose);
  if (verbose) {
    prettyPrintStats(away_team);
    prettyPrintStats(home_team);
  }
  return { home_team, away_team, score };
}

function randInt(min: number, maxInclusive: number): number { return Math.floor(Math.random() * (maxInclusive - min + 1)) + min; }
function toTitle(s: string): string { return s.replace(/\b\w/g, (c) => c.toUpperCase()); }


