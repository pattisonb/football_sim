import json

class Player:
    def __init__(self, data):
        self.name = data["name"]
        self.position = data["position"]
        self.speed = data.get("speed", 50)
        self.strength = data.get("strength", 50)
        self.intelligence = data.get("intelligence", 50)
        self.endurance = data.get("endurance", 50)
        self.fatigue = data.get("fatigue", 0)
        self.in_game = data.get("in_game", False)
        self.stats = data.get("stats", {})

        # Skill-specific
        self.passing = data.get("passing")
        self.decision_making = data.get("decision_making")
        self.elusiveness = data.get("elusiveness")
        self.vision = data.get("vision")
        self.hands = data.get("hands")
        self.route_running = data.get("route_running")
        self.run_blocking = data.get("run_blocking")
        self.pass_blocking = data.get("pass_blocking")
        self.rushing = data.get("rushing")
        self.tackling = data.get("tackling")
        self.coverage = data.get("coverage")
        self.kick_power = data.get("kick_power")
        self.kick_accuracy = data.get("kick_accuracy")
        self.punt_power = data.get("punt_power")
        self.punt_accuracy = data.get("punt_accuracy")

        self._original_attrs = {
            "speed": self.speed,
            "strength": self.strength,
            "elusiveness": self.elusiveness,
            "vision": self.vision,
            "hands": self.hands,
            "route_running": self.route_running,
            "run_blocking": self.run_blocking,
            "pass_blocking": self.pass_blocking,
            "rushing": self.rushing,
            "tackling": self.tackling,
            "coverage": self.coverage
        }

    def is_offense(self):
        return self.position in {"QB", "RB", "WR", "TE", "OL", "K", "P"}

    def is_defense(self):
        return self.position in {"DL", "ROLB", "MLB", "LOLB", "CB", "S"}

    def fatigue_level(self):
        return self.fatigue / max(self.endurance, 1)

    def to_dict(self):
        return self.__dict__.copy()


class Team:
    def __init__(self, name, offense, defense):
        self.name = name
        self.offense = [Player(p) for p in offense]
        self.defense = [Player(p) for p in defense]

    def get_offense(self, side="offense"):
        players = getattr(self, side)
        return [p for p in players if p.in_game]
    
    def get_all_offense(self, side="offense"):
        players = getattr(self, side)
        return [p for p in players]
    
    def get_defense(self, side="defense"):
        players = getattr(self, side)
        return [p for p in players if p.in_game]
        
    def get_all_defense(self, side="defense"):
        players = getattr(self, side)
        return [p for p in players]

    def get_player_by_name(self, name):
        for p in self.offense + self.defense:
            if p.name == name:
                return p
        return None
    
    def recover_bench_players(self):
        for p in self.offense + self.defense:
            if not p.in_game:
                recovery = p.endurance / 10
                p.fatigue = max(0, p.fatigue - recovery)

    def sub_skill_position_players(self, fatigue_threshold=50):
        from operator import itemgetter

        skill_positions = ['RB', 'WR', 'TE']

        for pos in skill_positions:
            # Get current in-game players of this position
            starters = [p for p in self.offense if p.position == pos and p.in_game and p.fatigue > fatigue_threshold]
            if not starters:
                continue  # no one too tired

            # Get bench players of same position who are fresh enough
            bench = [p for p in self.offense if p.position == pos and not p.in_game and p.fatigue <= fatigue_threshold]
            if not bench:
                continue  # no fresh players available

            # Prioritize fresh subs by fatigue ASC, then by total stats DESC
            def stat_sum(player):
                return sum(player.stats.values())

            bench.sort(key=lambda p: (-stat_sum(p), p.fatigue))

            # Sub one-for-one
            for tired_player in starters:
                if not bench:
                    break
                sub = bench.pop(0)
                tired_player.in_game = False
                sub.in_game = True

    def sub_defensive_players(self, fatigue_threshold=50):
        positions = set(p.position for p in self.defense)

        for pos in positions:
            # Players currently in the game and too tired
            tired_players = [p for p in self.defense if p.position == pos and p.in_game and p.fatigue > fatigue_threshold]
            if not tired_players:
                continue

            # Bench players eligible to sub in
            bench = [p for p in self.defense if p.position == pos and not p.in_game and p.fatigue <= fatigue_threshold]
            if not bench:
                continue

            # Prioritize by freshest and most productive
            def stat_sum(player):
                return sum(player.stats.values())

            bench.sort(key=lambda p: (p.fatigue, -stat_sum(p)))

            # Swap one-for-one
            for tired in tired_players:
                if not bench:
                    break
                fresh = bench.pop(0)
                tired.in_game = False
                fresh.in_game = True


    def get_kicker(self):
        for p in self.offense:
            if p.position == "K":
                return p
        return None
    
    def apply_fatigue_penalties(self):
        for player in self.offense + self.defense:
            fatigue_pct = player.fatigue / 100
            penalty_scale = fatigue_pct * 0.15  # max 15% drop

            for attr, original_value in player._original_attrs.items():
                if original_value is None:
                    continue

                min_allowed = round(original_value * (2 / 3))
                new_value = round(original_value * (1 - penalty_scale))
                setattr(player, attr, max(min_allowed, new_value))

def initialize_teams(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    teams = []
    for team_data in data["teams"]:
        team = Team(
            name=team_data["team_name"],
            offense=team_data["offense"],
            defense=team_data["defense"]
        )
        teams.append(team)

    return teams
