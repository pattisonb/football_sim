import random
from collections import defaultdict

from game_config import sliders

def sim_kickoff(kicker):
    # Adjust kick power by slider
    kick_power_mult = sliders.get_multiplier(sliders.kickoff_power)
    kick_power = kicker.kick_power * kick_power_mult
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

    # Return (college chaos: occasional return TD)
    # Adjusted by kickoff return slider
    return_mult = sliders.get_multiplier(sliders.kickoff_return)
    return_td_chance = 0.005 * return_mult
    if random.random() < return_td_chance:
        return 100  # Kickoff return touchdown
    
    # Base return yards adjusted by slider
    base_return = 10 + (return_mult - 1.0) * 15  # Scale from 10-35 based on slider
    return_yards = random.randint(int(base_return), int(base_return + 15))
    end_yard = 100 - landing_yard
    end_yard += return_yards
    return round(end_yard)

def sim_pat(kicker, verbose=False):
    # Adjust base chance by kicking accuracy slider
    kick_acc_mult = sliders.get_multiplier(sliders.kicking_accuracy)
    base_chance = 0.975 * kick_acc_mult  # College PAT success rate ~97-98%
    
    # Adjust based on kicker accuracy (scale 50 = avg, 100 = elite)
    accuracy_adjustment = ((kicker.kick_accuracy - 50) * 0.003) * kick_acc_mult
    make_chance = max(0.94, min(0.995, base_chance + accuracy_adjustment))  # Tight range for college PATs
    
    # College chaos: occasional botched snap/hold (1% chance)
    if random.random() < 0.01:
        if verbose:
            print("PAT botched! Bad snap/hold!")
        kicker.stats["pat_attempts"] += 1
        return False
    
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

def sim_two_point_conversion(offense_list, defense_list, verbose=False, team_name=""):
    """Simulate a 2-point conversion attempt from the 3-yard line"""
    # 2-point conversion success rate in college is ~40-45%
    # Slightly favor pass plays (55% pass, 45% run)
    is_pass = random.random() < 0.55
    
    if is_pass:
        # Pass attempt from 3-yard line
        qb = next((p for p in offense_list if p.position == "QB"), None)
        if not qb:
            # Fallback if no QB found
            return random.random() < 0.40
        
        # High completion chance due to short distance
        base_completion = 0.50  # Base 50% completion rate for 2-pt conversion
        qb_skill = (qb.passing + qb.decision_making + qb.intelligence) / 300
        defense_coverage = sum(p.coverage for p in defense_list if p.position in ('CB', 'S')) / 2000
        
        completion_chance = base_completion + qb_skill - defense_coverage
        completion_chance = max(0.25, min(0.75, completion_chance))
        
        if random.random() < completion_chance:
            if verbose:
                print(f"{team_name} 2-point conversion PASS is GOOD!")
            return True
        else:
            if verbose:
                print(f"{team_name} 2-point conversion PASS is NO GOOD!")
            return False
    else:
        # Run attempt from 3-yard line
        # Higher success rate for runs in short yardage
        base_success = 0.45  # Base 45% success rate
        offense_line = sum(p.run_blocking for p in offense_list if p.position == 'OL') / 500
        defense_line = sum(p.tackling for p in defense_list if p.position in ('DL', 'OLB', 'MLB', 'ROLB')) / 800
        
        success_chance = base_success + offense_line - defense_line
        success_chance = max(0.30, min(0.70, success_chance))
        
        if random.random() < success_chance:
            if verbose:
                print(f"{team_name} 2-point conversion RUN is GOOD!")
            return True
        else:
            if verbose:
                print(f"{team_name} 2-point conversion RUN is NO GOOD!")
            return False

def get_kick_attempt_range(kicker) :
    # Adjust kick range by kicking power slider
    kick_power_mult = sliders.get_multiplier(sliders.kicking_power)
    base_range = 52  # College kickers have shorter range (52 yards vs NFL 65)
    kick_range = base_range * kick_power_mult
    return (round(kick_range - ((kicker.kick_power * kick_power_mult) - 50)/5))

def get_punt_distance(punter) :
    # Adjust punt distance by kicking power slider
    punt_power_mult = sliders.get_multiplier(sliders.kicking_power)
    base_punt = 43 * punt_power_mult
    punt_distance = int(random.gauss(base_punt, 5))  # College punts slightly shorter with more variance
    return (round(punt_distance + ((punter.punt_power * punt_power_mult) - 50)/5)) 

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
    
    # Add team-level stats
    stat_totals["kickoff_return_touchdowns"] = team.team_stats.get("kickoff_return_touchdowns", 0)
    stat_totals["blocked_kicks"] = team.team_stats.get("blocked_kicks", 0)
    stat_totals["blocked_punts"] = team.team_stats.get("blocked_punts", 0)

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
        "Passing Touchdowns": stat_totals.get("passing_touchdowns", 0),
        "Receiving Touchdowns": stat_totals.get("receiving_touchdowns", 0),
        "Rushing Touchdowns": stat_totals.get("rushing_touchdowns", 0),
        "Solo Tackles": stat_totals.get("solo_tackles", 0),
        "Assisted Tackles": stat_totals.get("assisted_tackles", 0),
        "Sacks": stat_totals.get("sacks", 0),
        "Interceptions": stat_totals.get("interceptions", 0),
        "Forced Fumbles": stat_totals.get("forced_fumbles", 0),
        "PATs Made": stat_totals.get("pat_made", 0),
        "PATS Attempted" : stat_totals.get("pat_attempts", 0),
        "Field Goals Made": stat_totals.get("fg_made", 0),
        "Field Goals Attempted": stat_totals.get("fg_attempted", 0),
        "Punts": stat_totals.get("punts", 0),
        "Punt Yards": stat_totals.get("punt_yards", 0),
        "Kickoff Return Touchdowns": stat_totals.get("kickoff_return_touchdowns", 0),
        "Blocked Kicks": stat_totals.get("blocked_kicks", 0),
        "Blocked Punts": stat_totals.get("blocked_punts", 0)
    }

def produce_box_score(team1, team2, score1, score2, quarter_scores=None, ot_periods=None, verbose=False):
    stats1 = summarize_stats(team1)
    stats2 = summarize_stats(team2)

    if verbose:
        # Traditional box score format with quarters
        print("\n" + "=" * 70)
        print(" " * 20 + "BOX SCORE")
        print("=" * 70)
        
        # Score by quarter (and overtime if applicable)
        if quarter_scores:
            q1_home = quarter_scores[team1.name][0] if len(quarter_scores[team1.name]) > 0 else 0
            q2_home = quarter_scores[team1.name][1] if len(quarter_scores[team1.name]) > 1 else 0
            q3_home = quarter_scores[team1.name][2] if len(quarter_scores[team1.name]) > 2 else 0
            q4_home = quarter_scores[team1.name][3] if len(quarter_scores[team1.name]) > 3 else 0
            q1_away = quarter_scores[team2.name][0] if len(quarter_scores[team2.name]) > 0 else 0
            q2_away = quarter_scores[team2.name][1] if len(quarter_scores[team2.name]) > 1 else 0
            q3_away = quarter_scores[team2.name][2] if len(quarter_scores[team2.name]) > 2 else 0
            q4_away = quarter_scores[team2.name][3] if len(quarter_scores[team2.name]) > 3 else 0
            
            # Build header with quarters and OT periods
            header = f"\n{'Team':<20}{'1':<8}{'2':<8}{'3':<8}{'4':<8}"
            if ot_periods:
                for ot in ot_periods:
                    header += f"OT{ot['period']:<6}"
            header += f"{'Final':<8}"
            print(header)
            print("-" * (60 + (len(ot_periods) * 8) if ot_periods else 0))
            
            # Build score lines
            team1_line = f"{team1.name:<20}{q1_home:<8}{q2_home:<8}{q3_home:<8}{q4_home:<8}"
            team2_line = f"{team2.name:<20}{q1_away:<8}{q2_away:<8}{q3_away:<8}{q4_away:<8}"
            
            if ot_periods:
                for ot in ot_periods:
                    team1_line += f"{ot['home_score']:<8}"
                    team2_line += f"{ot['away_score']:<8}"
            
            team1_line += f"{score1:<8}"
            team2_line += f"{score2:<8}"
            print(team1_line)
            print(team2_line)
        else:
            # Fallback if no quarter scores
            print(f"\n{'Team':<30}{'Score':<10}")
            print("-" * 40)
            print(f"{team1.name:<30}{score1:<10}")
            print(f"{team2.name:<30}{score2:<10}")
        
        print("\n" + "=" * 70)
        print(" " * 15 + "TEAM STATISTICS")
        print("=" * 70)
        print(f"\n{'STAT':<30}{team1.name:<20}{team2.name:<20}")
        print("-" * 70)
        
        # Group stats logically
        offense_stats = [
            "Pass Attempts", "Completions", "Pass Yards", "Interceptions Thrown", 
            "Sacks Taken", "Carries", "Rush Yards", "Fumbles"
        ]
        receiving_stats = [
            "Receptions", "Receiving Yards", "Targets"
        ]
        scoring_stats = [
            "Passing Touchdowns", "Receiving Touchdowns", "Rushing Touchdowns"
        ]
        defense_stats = [
            "Solo Tackles", "Assisted Tackles", "Sacks", "Interceptions", "Forced Fumbles"
        ]
        special_teams_stats = [
            "PATs Made", "PATS Attempted", "Field Goals Made", "Field Goals Attempted",
            "Punts", "Punt Yards", "Kickoff Return Touchdowns", "Blocked Kicks", "Blocked Punts"
        ]
        
        stat_groups = [
            ("OFFENSE", offense_stats),
            ("RECEIVING", receiving_stats),
            ("SCORING", scoring_stats),
            ("DEFENSE", defense_stats),
            ("SPECIAL TEAMS", special_teams_stats)
        ]
        
        for group_name, stat_list in stat_groups:
            print(f"\n{group_name}:")
            for stat in stat_list:
                if stat in stats1:
                    print(f"  {stat:<28}{str(stats1[stat]):<20}{str(stats2[stat]):<20}")
        
        print("\n" + "=" * 70)

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