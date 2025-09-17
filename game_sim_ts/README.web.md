## Football Sim Engine (TypeScript Port)

This folder contains a browser-ready TypeScript port of your Python football simulator. It mirrors functionality and preserves probabilities and mechanics.

Files:
- `types.ts`: Strong types for players, teams, stats, and box scores.
- `roster.ts`: `Player` and `Team` classes, substitution and fatigue penalties.
- `gameFunctions.ts`: Special teams (kickoffs, PATs), fatigue, and box score utils.
- `playFunctions.ts`: Core play outcomes (runs, passes, sacks, tackles, fatigue).
- `driveFunctions.ts`: Playcalling, penalties, downs, punts/FGs, drive loop.
- `startGame.ts`: Game orchestration with halves, scoring, and pretty stats.

Usage example (in a web app):
```ts
import { simulateFullGame } from './startGame';

// Provide two teams from JSON (converted to objects)
const result = simulateFullGame(rawTeamsArray, true);
console.log(result.score);
```


