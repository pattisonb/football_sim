import { simulateFullGame } from "./startGame";
import { RawTeamData } from "./types";

// Minimal demo with two tiny teams. Replace with your parsed `rosters.json`.
const rawTeams: RawTeamData[] = [
  {
    team_name: "Home",
    offense: [
      { name: "QB Home", position: "QB", in_game: true, intelligence: 65, passing: 70, decision_making: 65, strength: 60, speed: 55, stats: {} },
      { name: "RB Home", position: "RB", in_game: true, speed: 70, strength: 65, elusiveness: 68, vision: 66, endurance: 60, stats: {} },
      { name: "WR Home", position: "WR", in_game: true, speed: 75, hands: 70, route_running: 70, stats: {} },
      { name: "TE Home", position: "TE", in_game: true, strength: 65, hands: 60, route_running: 60, run_blocking: 65, pass_blocking: 60, stats: {} },
      { name: "OL1 Home", position: "OL", in_game: true, strength: 70, run_blocking: 68, pass_blocking: 68, stats: {} },
      { name: "K Home", position: "K", in_game: true, kick_power: 65, kick_accuracy: 65, stats: {} },
      { name: "P Home", position: "P", in_game: true, punt_power: 65, punt_accuracy: 60, stats: {} }
    ],
    defense: [
      { name: "DL Home", position: "DL", in_game: true, strength: 70, rushing: 65, tackling: 65, stats: {} },
      { name: "MLB Home", position: "MLB", in_game: true, tackling: 70, intelligence: 65, rushing: 60, stats: {} },
      { name: "CB Home", position: "CB", in_game: true, speed: 70, coverage: 68, tackling: 55, stats: {} },
      { name: "S Home", position: "S", in_game: true, speed: 68, coverage: 66, tackling: 60, stats: {} }
    ]
  },
  {
    team_name: "Away",
    offense: [
      { name: "QB Away", position: "QB", in_game: true, intelligence: 60, passing: 65, decision_making: 60, strength: 58, speed: 52, stats: {} },
      { name: "RB Away", position: "RB", in_game: true, speed: 68, strength: 64, elusiveness: 66, vision: 64, endurance: 58, stats: {} },
      { name: "WR Away", position: "WR", in_game: true, speed: 73, hands: 68, route_running: 68, stats: {} },
      { name: "TE Away", position: "TE", in_game: true, strength: 64, hands: 58, route_running: 58, run_blocking: 64, pass_blocking: 58, stats: {} },
      { name: "OL1 Away", position: "OL", in_game: true, strength: 68, run_blocking: 66, pass_blocking: 66, stats: {} },
      { name: "K Away", position: "K", in_game: true, kick_power: 63, kick_accuracy: 62, stats: {} },
      { name: "P Away", position: "P", in_game: true, punt_power: 63, punt_accuracy: 60, stats: {} }
    ],
    defense: [
      { name: "DL Away", position: "DL", in_game: true, strength: 68, rushing: 64, tackling: 64, stats: {} },
      { name: "MLB Away", position: "MLB", in_game: true, tackling: 68, intelligence: 62, rushing: 60, stats: {} },
      { name: "CB Away", position: "CB", in_game: true, speed: 69, coverage: 66, tackling: 54, stats: {} },
      { name: "S Away", position: "S", in_game: true, speed: 67, coverage: 65, tackling: 59, stats: {} }
    ]
  }
];

// Run a full game in Node/Browser console
simulateFullGame(rawTeams, true);


