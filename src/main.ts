import { simulateFullGame } from "../game_sim_ts/startGame";
import { summarizeStats } from "../game_sim_ts/gameFunctions";
import { RawTeamData } from "../game_sim_ts/types";
import rosters from "../game_sim/rosters.json";

const homeName = document.getElementById("home-name") as HTMLHeadingElement;
const awayName = document.getElementById("away-name") as HTMLHeadingElement;
const homeList = document.getElementById("home-roster") as HTMLUListElement;
const awayList = document.getElementById("away-roster") as HTMLUListElement;
const btnSim = document.getElementById("btn-sim") as HTMLButtonElement;
const scoreLine = document.getElementById("score-line") as HTMLDivElement;
const homeStats = document.getElementById("home-stats") as HTMLUListElement;
const awayStats = document.getElementById("away-stats") as HTMLUListElement;

let teams: RawTeamData[] = [];

function loadRostersSync() {
  teams = (rosters as { teams: RawTeamData[] }).teams;
  renderRosters(teams);
}

function renderRosters(data: RawTeamData[]) {
  const [home, away] = data;
  homeName.textContent = home.team_name;
  awayName.textContent = away.team_name;
  const renderTeam = (team: RawTeamData, ul: HTMLUListElement) => {
    ul.innerHTML = "";
    const rows: Array<{ name: string; position: string }> = [];
    for (const p of team.offense) rows.push({ name: p.name, position: p.position });
    for (const p of team.defense) rows.push({ name: p.name, position: p.position });
    rows.forEach(({ name, position }) => {
      const li = document.createElement("li");
      const left = document.createElement("div");
      left.textContent = name;
      const right = document.createElement("div");
      right.className = "pos";
      right.textContent = position;
      li.appendChild(left);
      li.appendChild(right);
      ul.appendChild(li);
    });
  };
  renderTeam(home, homeList);
  renderTeam(away, awayList);
}

btnSim.addEventListener("click", () => {
  if (!teams.length) return;
  btnSim.disabled = true;
  scoreLine.textContent = "Simulating...";
  try {
    const result = simulateFullGame(teams, false);
    const { home_team, away_team, score } = result;
    scoreLine.textContent = `${home_team.name}: ${score[home_team.name]} — ${away_team.name}: ${score[away_team.name]}`;
    renderOffensiveStats(home_team, homeStats);
    renderOffensiveStats(away_team, awayStats);
    // Also render team-level offensive summaries to ensure output
    renderTeamOffenseSummary(home_team, homeStats);
    renderTeamOffenseSummary(away_team, awayStats);
  } finally {
    btnSim.disabled = false;
  }
});

loadRostersSync();

function renderOffensiveStats(team: any, listEl: HTMLUListElement) {
  listEl.innerHTML = "";
  const players: any[] = team.get_all_offense();
  const showKeys = new Set([
    "pass_attempts",
    "completions",
    "pass_yards",
    "interceptions_thrown",
    "sacks_taken",
    "carries",
    "rush_yards",
    "fumbles",
    "receptions",
    "receiving_yards",
    "targets",
    "touchdowns",
    // Special teams
    "pat_made",
    "pat_attempts",
    "fg_made",
    "fg_attempted",
    "punts",
    "punt_yards"
  ]);
  for (const p of players) {
    const total = Object.values(p.stats).reduce((a: number, b: any) => a + (typeof b === "number" ? b : 0), 0);
    if (!total) continue;
    const li = document.createElement("li");
    const name = document.createElement("div");
    name.textContent = `${p.name} (${p.position})`;
    li.appendChild(name);
    const sub = document.createElement("div");
    sub.className = "muted";
    const parts: string[] = [];
    for (const [k, v] of Object.entries(p.stats)) {
      if (!showKeys.has(k) || !v) continue;
      parts.push(`${k.replace(/_/g, " ")}: ${v}`);
    }
    sub.textContent = parts.join(" | ");
    li.appendChild(sub);
    listEl.appendChild(li);
  }
}

function renderTeamOffenseSummary(team: any, listEl: HTMLUListElement) {
  const stats = summarizeStats(team);
  // If list already has player rows, append a divider and totals; else just show totals
  if (listEl.children.length) {
    const hr = document.createElement("li");
    hr.style.borderBottom = "1px solid #1f2937";
    hr.style.margin = "8px 0";
    listEl.appendChild(hr);
  }
  const totals = document.createElement("li");
  const left = document.createElement("div");
  left.textContent = "Team Totals";
  const sub = document.createElement("div");
  sub.className = "muted";
  const parts = [
    `Pass: ${stats["Completions"]}/${stats["Pass Attempts"]} ${stats["Pass Yards"]}y`,
    `Rush: ${stats["Carries"]} for ${stats["Rush Yards"]}y`,
    `Rec: ${stats["Receptions"]} for ${stats["Receiving Yards"]}y`,
    `TD: ${stats["Touchdowns"]}`,
    `PAT: ${stats["PATs Made"]}/${stats["PATS Attempted"]}`,
    `FG: ${stats["Field Goals Made"]}/${stats["Field Goals Attempted"]}`,
    `Punts: ${stats["Punts"]} for ${stats["Punt Yards"]}y`
  ];
  sub.textContent = parts.join(" | ");
  totals.appendChild(left);
  totals.appendChild(sub);
  listEl.appendChild(totals);
}


