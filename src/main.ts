import { simulateFullGame } from "../game_sim_ts/startGame";
import { summarizeStats } from "../game_sim_ts/gameFunctions";
import { RawTeamData } from "../game_sim_ts/types";
import rosters from "../game_sim/rosters.json";

const homeName = document.getElementById("home-name") as HTMLHeadingElement;
const awayName = document.getElementById("away-name") as HTMLHeadingElement;
const homeList = document.getElementById("home-roster") as HTMLUListElement;
const awayList = document.getElementById("away-roster") as HTMLUListElement;
const btnSim = document.getElementById("btn-sim") as HTMLButtonElement;
const btnSim100 = document.getElementById("btn-sim-100") as HTMLButtonElement;
const btnReset = document.getElementById("btn-reset") as HTMLButtonElement;
const hfaCheckbox = document.getElementById("hfa") as HTMLInputElement;
const scoreLine = document.getElementById("score-line") as HTMLDivElement;
const homeStats = document.getElementById("home-stats") as HTMLUListElement;
const awayStats = document.getElementById("away-stats") as HTMLUListElement;

let teams: RawTeamData[] = [];
const playerBoostPct = new Map<string, number>();

function loadRostersSync() {
  teams = (rosters as { teams: RawTeamData[] }).teams;
  renderRosters(teams);
}

function renderRosters(data: RawTeamData[]) {
  const [home, away] = data;
  
  // Calculate team overalls
  const homeOffOverall = calculateOffensiveOverall(home);
  const homeDefOverall = calculateDefensiveOverall(home);
  const awayOffOverall = calculateOffensiveOverall(away);
  const awayDefOverall = calculateDefensiveOverall(away);
  
  homeName.innerHTML = `${home.team_name}<br><small style="color: #9ca3af; font-size: 12px;">Off: ${homeOffOverall} | Def: ${homeDefOverall}</small>`;
  awayName.innerHTML = `${away.team_name}<br><small style="color: #9ca3af; font-size: 12px;">Off: ${awayOffOverall} | Def: ${awayDefOverall}</small>`;
  
  const renderTeam = (team: RawTeamData, ul: HTMLUListElement) => {
    ul.innerHTML = "";
    const order: string[] = [
      // Offense depth chart order
      'QB','RB','WR','TE','OL','K','P',
      // Defense depth chart order
      'DL','MLB','ROLB','LOLB','CB','S'
    ];

    const players = [...team.offense, ...team.defense];

    for (const pos of order) {
      const posPlayers = players
        .filter(p => p.position === pos)
        .map(p => ({ p, ovr: calculatePlayerOverall(p) }))
        .sort((a, b) => Number(b.p.in_game ? 1 : 0) - Number(a.p.in_game ? 1 : 0) || b.ovr - a.ovr);

      if (!posPlayers.length) continue;

      // Position header
      const header = document.createElement("li");
      header.style.borderBottom = "1px solid #1f2937";
      header.style.padding = "6px 0";
      header.innerHTML = `<strong>${pos}</strong>`;
      ul.appendChild(header);

      for (const { p, ovr } of posPlayers) {
        const li = document.createElement("li");
        const left = document.createElement("div");
        const starterTag = p.in_game ? ' <span class="pos" style="color:#34d399">(Starter)</span>' : '';
        const boost = getBoostPct(p.name);
        left.innerHTML = `${p.name}${starterTag} <span class="pos" style="margin-left:6px;color:#9ca3af">${boost >= 0 ? "+" : ""}${boost}%</span>`;
        const controls = document.createElement("span");
        controls.style.marginLeft = "8px";
        const minus = document.createElement("button");
        minus.textContent = "-";
        minus.style.marginRight = "4px";
        minus.style.padding = "0 6px";
        minus.style.borderRadius = "4px";
        minus.style.border = "1px solid #1f2937";
        minus.style.background = "#0b1220";
        minus.style.color = "#e5e7eb";
        minus.onclick = () => { adjustBoost(p.name, -5); renderRosters(teams); };
        const plus = document.createElement("button");
        plus.textContent = "+";
        plus.style.padding = "0 6px";
        plus.style.borderRadius = "4px";
        plus.style.border = "1px solid #1f2937";
        plus.style.background = "#0b1220";
        plus.style.color = "#e5e7eb";
        plus.onclick = () => { adjustBoost(p.name, +5); renderRosters(teams); };
        controls.appendChild(minus);
        controls.appendChild(plus);
        left.appendChild(controls);
        const right = document.createElement("div");
        right.className = "pos";
        right.textContent = `${pos} • OVR ${ovr}`;
        li.appendChild(left);
        li.appendChild(right);
        ul.appendChild(li);
      }
    }
  };
  renderTeam(home, homeList);
  renderTeam(away, awayList);
}

function calculateOffensiveOverall(team: RawTeamData): number {
  const offensiveStats = ['speed', 'strength', 'intelligence', 'passing', 'decision_making', 'hands', 'route_running', 'run_blocking', 'pass_blocking', 'elusiveness', 'vision'];
  let total = 0;
  let count = 0;
  
  for (const player of team.offense) {
    const weight = player.in_game ? 3 : 1; // Starters weighted 3x more
    for (const stat of offensiveStats) {
      const value = applyBoost(player.name, (player as any)[stat]);
      if (typeof value === 'number') {
        total += value * weight;
        count += weight;
      }
    }
  }
  
  return count > 0 ? Math.round(total / count) : 0;
}

function calculateDefensiveOverall(team: RawTeamData): number {
  const defensiveStats = ['speed', 'strength', 'intelligence', 'tackling', 'coverage', 'rushing'];
  let total = 0;
  let count = 0;
  
  for (const player of team.defense) {
    const weight = player.in_game ? 3 : 1; // Starters weighted 3x more
    for (const stat of defensiveStats) {
      const value = applyBoost(player.name, (player as any)[stat]);
      if (typeof value === 'number') {
        total += value * weight;
        count += weight;
      }
    }
  }
  
  return count > 0 ? Math.round(total / count) : 0;
}

function calculatePlayerOverall(player: any): number {
  const pos = player.position as string;
  let primaryKeys: string[] = [];
  let secondaryKeys: string[] = [];
  
  if (["QB","RB","WR","TE","OL"].includes(pos)) {
    // Primary offensive stats (weighted 3x)
    primaryKeys = ['speed','strength','intelligence','passing','decision_making','hands','route_running','run_blocking','pass_blocking','elusiveness','vision'];
    // Secondary defensive stats (weighted 1x)
    secondaryKeys = ['tackling','coverage','rushing'];
  } else if (pos === 'K') {
    // Primary kicking stats (weighted 3x)
    primaryKeys = ['kick_power','kick_accuracy'];
    // Secondary stats (weighted 1x)
    secondaryKeys = ['speed','strength','intelligence','passing','decision_making','hands','route_running','run_blocking','pass_blocking','elusiveness','vision','tackling','coverage','rushing'];
  } else if (pos === 'P') {
    // Primary punting stats (weighted 3x)
    primaryKeys = ['punt_power','punt_accuracy'];
    // Secondary stats (weighted 1x)
    secondaryKeys = ['speed','strength','intelligence','passing','decision_making','hands','route_running','run_blocking','pass_blocking','elusiveness','vision','tackling','coverage','rushing'];
  } else {
    // Defense - primary defensive stats (weighted 3x)
    primaryKeys = ['speed','strength','intelligence','tackling','coverage','rushing'];
    // Secondary offensive stats (weighted 1x)
    secondaryKeys = ['passing','decision_making','hands','route_running','run_blocking','pass_blocking','elusiveness','vision'];
  }
  
  let weightedSum = 0;
  let weightedCount = 0;
  
  // Add primary stats with 3x weight
  for (const k of primaryKeys) {
    const v = applyBoost(player.name, player[k]);
    if (typeof v === 'number') {
      weightedSum += v * 3;
      weightedCount += 3;
    }
  }
  
  // Add secondary stats with 1x weight
  for (const k of secondaryKeys) {
    const v = applyBoost(player.name, player[k]);
    if (typeof v === 'number') {
      weightedSum += v * 1;
      weightedCount += 1;
    }
  }
  
  return weightedCount > 0 ? Math.round(weightedSum / weightedCount) : 0;
}

function getBoostPct(name: string): number {
  return playerBoostPct.get(name) ?? 0;
}
function adjustBoost(name: string, deltaPct: number) {
  const cur = playerBoostPct.get(name) ?? 0;
  const next = Math.max(-50, Math.min(100, cur + deltaPct));
  playerBoostPct.set(name, next);
}
function applyBoost(name: string, value: any): any {
  if (typeof value !== 'number') return value;
  const pct = getBoostPct(name);
  return Math.round(value * (1 + pct / 100));
}

function applyBoostsToTeams(data: RawTeamData[], homeFieldPct = 0): RawTeamData[] {
  const numericKeys = new Set([
    'speed','strength','intelligence','endurance','fatigue',
    'passing','decision_making','elusiveness','vision','hands','route_running','run_blocking','pass_blocking','rushing','tackling','coverage',
    'kick_power','kick_accuracy','punt_power','punt_accuracy'
  ]);
  const deep = (obj: any) => JSON.parse(JSON.stringify(obj));
  const copy = deep(data) as RawTeamData[];
  for (let t = 0; t < copy.length; t++) {
    const team = copy[t];
    for (const p of [...team.offense, ...team.defense]) {
      const pct = getBoostPct(p.name);
      const teamPct = (t === 0 ? homeFieldPct : 0);
      const totalPct = pct + teamPct;
      if (!totalPct) continue;
      for (const k of Object.keys(p)) {
        if (!numericKeys.has(k)) continue;
        const v = (p as any)[k];
        if (typeof v === 'number') (p as any)[k] = Math.round(v * (1 + totalPct / 100));
      }
    }
  }
  return copy;
}

btnSim.addEventListener("click", () => {
  if (!teams.length) return;
  btnSim.disabled = true;
  scoreLine.textContent = "Simulating...";
  try {
    const boosted = applyBoostsToTeams(teams, hfaCheckbox && hfaCheckbox.checked ? 3 : 0);
    const result = simulateFullGame(boosted, false);
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

btnReset.addEventListener("click", () => {
  playerBoostPct.clear();
  renderRosters(teams);
});

btnSim100.addEventListener("click", () => {
  if (!teams.length) return;
  btnSim.disabled = true; btnSim100.disabled = true;
  scoreLine.textContent = "Simulating 100 games...";
  try {
    const n = 100;
    let homeWins = 0, awayWins = 0, ties = 0;
    let totalDiff = 0; // home - away
    for (let i = 0; i < n; i++) {
      const boosted = applyBoostsToTeams(teams, hfaCheckbox && hfaCheckbox.checked ? 3 : 0);
      const res = simulateFullGame(boosted, false);
      const h = res.score[res.home_team.name];
      const a = res.score[res.away_team.name];
      if (h > a) homeWins++; else if (a > h) awayWins++; else ties++;
      totalDiff += (h - a);
    }
    const avgMargin = Math.round((totalDiff / n) * 10) / 10;
    scoreLine.textContent = `100 sims → Home W:${homeWins} L:${awayWins} T:${ties} | Avg margin (home): ${avgMargin}`;
  } finally {
    btnSim.disabled = false; btnSim100.disabled = false;
  }
});

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


