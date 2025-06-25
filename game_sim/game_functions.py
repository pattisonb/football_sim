import random
from collections import defaultdict

def sim_kickoff(kicker):
    kick_power = kicker.kick_power
    kick_accuracy = kicker.kick_accuracy

    # Landing distance
    base_distance = 45 + (kick_power * 0.5)
    variance = random.uniform(-5, 5)
    landing_yard = min(max(base_distance + variance, 0), 100)

    # Out-of-bounds probability
    out_of_bounds_chance = max(0.15 - (kick_accuracy / 100) * 0.15, 0.01)
    if random.random() < out_of_bounds_chance:
        return 40

    # Touchback
    if landing_yard >= 95:
        return 25

    # Fair catch
    if random.random() < 0.1:
        return 100 - round(landing_yard)

    # Return
    return_yards = random.randint(10, 35)
    end_yard = 100 - landing_yard
    end_yard += return_yards
    return round(end_yard)

def sim_pat(kicker, verbose=False):
    base_chance = 0.94  # baseline PAT success rate (~94%)
    
    # Adjust based on kicker accuracy (scale 50 = avg, 100 = elite)
    accuracy_adjustment = (kicker.kick_accuracy - 50) * 0.005
    make_chance = max(0.80, min(0.99, base_chance + accuracy_adjustment))
    kicker.stats["pat_attempts"] += 1
    made = random.random() < make_chance
    if made :
        kicker.stats["pat_made"] += 1
    if verbose:
        if made:
            print(f"PAT is good! ({int(make_chance*100)}% chance)")
        else:
            print(f"PAT missed! ({int(make_chance*100)}% chance)")

    return made

def get_kick_attempt_range(kicker) :
    kick_range = 65
    return (round(kick_range - (kicker.kick_power - 50)/5))

def get_punt_distance(punter) :
    punt_distance = int(random.gauss(47, 4))
    return (round(punt_distance + (punter.punt_power - 50)/5)) 

def apply_baseline_fatigue(team):
    for player in team.offense + team.defense:
        base_chance = (100 - player.endurance) / 10  # chance out of 100
        if random.random() < base_chance / 100:
            max_fatigue = base_chance  # cap fatigue by same amount
            player.fatigue = random.randint(1, round(max_fatigue))
        else:
            player.fatigue = 0

def apply_general_fatigue(offense, defense):
    skill_positions = {'RB', 'TE', 'WR', 'CB', 'OLB', 'MLB', 'ROLB', 'S'}
    
    for player in offense + defense:
        if player.position in skill_positions:
            base_fatigue = 1.8  # skill players exert more per play
        else:
            base_fatigue = 0.1  # linemen/special teams, etc.

        endurance_factor = (100 - player.endurance) / 100  # 0.0–1.0
        fatigue = base_fatigue + (endurance_factor * base_fatigue)
        player.fatigue = min(100, player.fatigue + fatigue)

def apply_pass_fatigue(offense, defense, receiver=None, yards=0):
    # Apply fatigue to offensive skill players
    for player in offense:
        if player.position not in ("WR", "RB", "TE"):
            continue

        base_fatigue = 1 + (100 - player.endurance) / 80

        if receiver is not None and player == receiver:
            effort = 1 + (yards / 10)
            fatigue = base_fatigue + effort * (1 + (100 - player.endurance) / 100)
        else:
            fatigue = base_fatigue

        player.fatigue = min(100, player.fatigue + round(fatigue))

    # Apply lighter fatigue to defensive coverage players
    for player in defense:
        if player.position not in ("CB", "S", "OLB", "MLB", "ROLB", "LOLB"):
            continue

        fatigue = 0.5 + (100 - player.endurance) / 120  # ~0.5–1.3 range
        player.fatigue = min(100, player.fatigue + round(fatigue, 1))

def apply_run_fatigue(offense, defense, rusher=None, yards=0):
    # Apply fatigue to offensive skill players
    for player in offense:
        if player.position not in ("RB", "WR", "TE"):
            continue

        base_fatigue = 1 + (100 - player.endurance) / 80  # ~1–2.25

        if rusher is not None and player == rusher:
            effort = 1 + (yards / 7)  # Runs are more tiring per yard than catches
            fatigue = base_fatigue + effort * (1 + (100 - player.endurance) / 100)
        else:
            fatigue = base_fatigue * 0.75  # lighter if just blocking/running a decoy route

        player.fatigue = min(100, player.fatigue + round(fatigue))

    # Apply fatigue to front-seven defenders
    for player in defense:
        if player.position in ("DL", "OLB", "MLB", "ROLB", "LOLB", "S"):
            fatigue = 0.6 + (100 - player.endurance) / 110  # slightly higher than pass D
            player.fatigue = min(100, player.fatigue + round(fatigue, 1))

def summarize_stats(team):
    stat_totals = defaultdict(int)

    for player in team.offense + team.defense:
        for stat, value in player.stats.items():
            if isinstance(value, (int, float)):
                stat_totals[stat] += value

    return {
        "Pass Attempts": stat_totals.get("pass_attempts", 0),
        "Completions": stat_totals.get("completions", 0),
        "Pass Yards": stat_totals.get("pass_yards", 0),
        "Interceptions Thrown": stat_totals.get("interceptions_thrown", 0),
        "Sacks Taken": stat_totals.get("sacks_taken", 0),
        "Carries": stat_totals.get("carries", 0),
        "Rush Yards": stat_totals.get("rush_yards", 0),
        "Fumbles": stat_totals.get("fumbles", 0),
        "Receptions": stat_totals.get("receptions", 0),
        "Receiving Yards": stat_totals.get("receiving_yards", 0),
        "Targets": stat_totals.get("targets", 0),
        "Touchdowns": stat_totals.get("touchdowns", 0),
        "Tackles": stat_totals.get("tackles", 0),
        "Sacks": stat_totals.get("sacks", 0),
        "Interceptions": stat_totals.get("interceptions", 0),
        "PATs Made": stat_totals.get("pat_made", 0),
        "PATS Attempted" : stat_totals.get("pat_attempts", 0),
        "Field Goals Made": stat_totals.get("fg_made", 0),
        "Field Goals Attempted": stat_totals.get("fg_attempted", 0),
        "Punts": stat_totals.get("punts", 0),
        "Punt Yards": stat_totals.get("punt_yards", 0)
    }

def produce_box_score(team1, team2, score1, score2, verbose=False):
    stats1 = summarize_stats(team1)
    stats2 = summarize_stats(team2)

    if verbose:
        print(f"\n=== Final Score ===")
        print(f"{team1.name}: {score1}")
        print(f"{team2.name}: {score2}")
        print("\n=== Team Comparison Box Score ===")
        print(f"{'STAT':<25}{team1.name:<20}{team2.name:<20}")
        print("-" * 65)
        for stat in stats1:
            print(f"{stat:<25}{str(stats1[stat]):<20}{str(stats2[stat]):<20}")

    return {
        "team1": {
            "name": team1.name,
            "score": score1,
            "stats": stats1
        },
        "team2": {
            "name": team2.name,
            "score": score2,
            "stats": stats2
        }
    }