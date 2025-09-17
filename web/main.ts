import { simulateFullGame } from "../game_sim_ts/startGame";
import { RawTeamData } from "../game_sim_ts/types";
import rosters from "../game_sim/rosters.json";

const homeName = document.getElementById("home-name") as HTMLHeadingElement;
const awayName = document.getElementById("away-name") as HTMLHeadingElement;
const homeList = document.getElementById("home-roster") as HTMLUListElement;
const awayList = document.getElementById("away-roster") as HTMLUListElement;
const btnSim = document.getElementById("btn-sim") as HTMLButtonElement;
const scoreLine = document.getElementById("score-line") as HTMLDivElement;

let teams: RawTeamData[] = [];
function loadRostersSync() {
  // rosters.json shape: { teams: RawTeamData[] }
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

btnSim.addEventListener("click", async () => {
  if (!teams.length) return;
  btnSim.disabled = true;
  scoreLine.textContent = "Simulating...";
  try {
    const result = simulateFullGame(teams, false);
    const { home_team, away_team, score } = result;
    scoreLine.textContent = `${home_team.name}: ${score[home_team.name]} — ${away_team.name}: ${score[away_team.name]}`;
  } finally {
    btnSim.disabled = false;
  }
});
loadRostersSync();


