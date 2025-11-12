from roster import Player, Team, initialize_teams
from game_functions import sim_kickoff, sim_pat, apply_baseline_fatigue, produce_box_score, sim_two_point_conversion
from drive_functions import sim_drive
import random

# Debug tracking
debug_touchdowns = []
debug_field_goals = []
debug_pats = []

teams = initialize_teams("rosters.json")
home_team = teams[0]
away_team = teams[1]
apply_baseline_fatigue(home_team)
apply_baseline_fatigue(away_team)

def determine_receiving_team(receive_prob=0.8):
    toss_winner = random.choice(["home", "away"])
    return toss_winner if random.random() < receive_prob else ("away" if toss_winner == "home" else "home")

def start_half(receiving_team_str, score_dict, half=1, verbose=False):
    seconds_remaining = 2400
    driving_team = home_team if receiving_team_str == "home" else away_team
    kicking_team = away_team if driving_team == home_team else home_team

    kickoff_yardline = sim_kickoff(kicking_team.get_kicker())
    seconds_remaining -= random.randint(4, 12)
    
    # Handle kickoff return touchdown
    if kickoff_yardline == 100:
        if verbose:
            print(f"{driving_team.name} KICKOFF RETURN TOUCHDOWN!")
        score_dict[driving_team.name] += 6
        driving_team.team_stats["kickoff_return_touchdowns"] += 1
        debug_touchdowns.append({
            'team': driving_team.name,
            'play_type': 'kickoff_return',
            'points': 6
        })
        pat_made = sim_pat(driving_team.get_kicker())
        if pat_made:
            if verbose:
                print(f"{driving_team.name} PAT is GOOD.")
            score_dict[driving_team.name] += 1
            debug_pats.append({'team': driving_team.name, 'made': True})
        else:
            if verbose:
                print(f"{driving_team.name} PAT is NO GOOD.")
            debug_pats.append({'team': driving_team.name, 'made': False})
        # Next kickoff
        kickoff_yardline = sim_kickoff(driving_team.get_kicker())
        seconds_remaining -= random.randint(4, 12)
    
    start_yardline = kickoff_yardline
    
    # Track score at start of half and at quarter mark
    score_at_start = {home_team.name: score_dict[home_team.name], away_team.name: score_dict[away_team.name]}
    score_at_quarter = None
    quarter_mark = 1200  # Midpoint of half

    if verbose:
        print(f"\n=== START OF HALF {half} ===")

    while seconds_remaining > 0:
        offense = driving_team
        defense = away_team if driving_team == home_team else home_team
        hurrying = seconds_remaining <= 120

        play_ran, result, yardline, seconds_remaining = sim_drive(
            offense, defense, 1, 10, start_yardline, seconds_remaining, hurrying, verbose=False
        )

        if result == 'touchdown':
            if verbose:
                print(f"{driving_team.name} TOUCHDOWN!", play_ran)
            score_dict[driving_team.name] += 6
            debug_touchdowns.append({
                'team': driving_team.name,
                'play_type': play_ran,
                'points': 6
            })
            pat_made = sim_pat(driving_team.get_kicker())
            if pat_made:
                if verbose:
                    print(f"{driving_team.name} PAT is GOOD.")
                score_dict[driving_team.name] += 1
                debug_pats.append({'team': driving_team.name, 'made': True})
            else:
                if verbose:
                    print(f"{driving_team.name} PAT is NO GOOD.")
                debug_pats.append({'team': driving_team.name, 'made': False})
            kickoff_yardline = sim_kickoff(driving_team.get_kicker())
            seconds_remaining -= random.randint(4, 12)
                # Handle kickoff return touchdown
            if kickoff_yardline == 100:
                if verbose:
                    print(f"{driving_team.name} KICKOFF RETURN TOUCHDOWN!")
                score_dict[driving_team.name] += 6
                driving_team.team_stats["kickoff_return_touchdowns"] += 1
                debug_touchdowns.append({
                    'team': driving_team.name,
                    'play_type': 'kickoff_return',
                    'points': 6
                })
                pat_made = sim_pat(driving_team.get_kicker())
                if pat_made:
                    if verbose:
                        print(f"{driving_team.name} PAT is GOOD.")
                    score_dict[driving_team.name] += 1
                    debug_pats.append({'team': driving_team.name, 'made': True})
                else:
                    if verbose:
                        print(f"{driving_team.name} PAT is NO GOOD.")
                    debug_pats.append({'team': driving_team.name, 'made': False})
                # Next kickoff
                kickoff_yardline = sim_kickoff(driving_team.get_kicker())
                seconds_remaining -= random.randint(4, 12)
            start_yardline = kickoff_yardline

        elif result == 'field goal':
            if verbose:
                print(f"{driving_team.name} FIELD GOAL is GOOD.")
            score_dict[driving_team.name] += 3
            debug_field_goals.append({
                'team': driving_team.name,
                'points': 3
            })
            kickoff_yardline = sim_kickoff(driving_team.get_kicker())
            seconds_remaining -= random.randint(4, 12)
                # Handle kickoff return touchdown
            if kickoff_yardline == 100:
                if verbose:
                    print(f"{driving_team.name} KICKOFF RETURN TOUCHDOWN!")
                score_dict[driving_team.name] += 6
                driving_team.team_stats["kickoff_return_touchdowns"] += 1
                debug_touchdowns.append({
                    'team': driving_team.name,
                    'play_type': 'kickoff_return',
                    'points': 6
                })
                pat_made = sim_pat(driving_team.get_kicker())
                if pat_made:
                    if verbose:
                        print(f"{driving_team.name} PAT is GOOD.")
                    score_dict[driving_team.name] += 1
                    debug_pats.append({'team': driving_team.name, 'made': True})
                else:
                    if verbose:
                        print(f"{driving_team.name} PAT is NO GOOD.")
                    debug_pats.append({'team': driving_team.name, 'made': False})
                # Next kickoff
                kickoff_yardline = sim_kickoff(driving_team.get_kicker())
                seconds_remaining -= random.randint(4, 12)
            start_yardline = kickoff_yardline

        elif result == 'punt':
            if verbose:
                print(f"{driving_team.name} punts.")
            start_yardline = 100 - yardline

        elif result == 'missed kick':
            if verbose:
                print(f"{driving_team.name} missed a field goal.")
            start_yardline = 100 - yardline

        elif result == 'turnover':
            if verbose:
                print(f"{driving_team.name} turned it over.")
            start_yardline = 100 - yardline

        # Track score at quarter mark (midpoint of half)
        if score_at_quarter is None and seconds_remaining <= quarter_mark:
            score_at_quarter = {
                home_team.name: score_dict[home_team.name] - score_at_start[home_team.name],
                away_team.name: score_dict[away_team.name] - score_at_start[away_team.name]
            }
        
        # Switch possession
        driving_team = away_team if driving_team == home_team else home_team

    if verbose:
        print(f"--- End of Half {half} ---")
        print(f"Score: {home_team.name} {score_dict[home_team.name]} - {away_team.name} {score_dict[away_team.name]}\n")

    # Calculate points scored in each quarter of this half
    if score_at_quarter is None:
        # If we never reached the quarter mark, all points in first quarter
        q1_home = score_dict[home_team.name] - score_at_start[home_team.name]
        q1_away = score_dict[away_team.name] - score_at_start[away_team.name]
        q2_home = 0
        q2_away = 0
    else:
        q1_home = score_at_quarter[home_team.name]
        q1_away = score_at_quarter[away_team.name]
        q2_home = (score_dict[home_team.name] - score_at_start[home_team.name]) - q1_home
        q2_away = (score_dict[away_team.name] - score_at_start[away_team.name]) - q1_away
    
    return score_dict, (q1_home, q2_home), (q1_away, q2_away)

def pretty_print_stats(team, side='both'):
    if side == 'offense' or side == 'both' :
        print(f"\n== {team.name} Offensive Stats ==")
        for player in team.get_all_offense():
            if sum(player.stats.values()) > 0:
                print(f"{player.name} ({player.position}):")
                for stat, val in player.stats.items():
                    if val > 0:
                        print(f"  {stat.replace('_', ' ').title()}: {val}")
                print("")
    if side == 'defense' or side == 'both' :
        print(f"\n== {team.name} Defensive Stats ==")
        for player in team.get_all_defense():
            if sum(player.stats.values()) > 0:
                print(f"{player.name} ({player.position}):")
                for stat, val in player.stats.items():
                    if val > 0:
                        print(f"  {stat.replace('_', ' ').title()}: {val}")
                print("")

def verify_scoring(team, actual_score):
    """Verify that the actual score matches the stats totals"""
    from collections import defaultdict
    stat_totals = defaultdict(int)
    
    for player in team.offense + team.defense:
        for stat, value in player.stats.items():
            if isinstance(value, (int, float)):
                stat_totals[stat] += value
    
    # Add team-level stats
    stat_totals["kickoff_return_touchdowns"] = team.team_stats.get("kickoff_return_touchdowns", 0)
    
    # Calculate expected score from stats
    passing_tds = stat_totals.get("passing_touchdowns", 0)
    receiving_tds = stat_totals.get("receiving_touchdowns", 0)
    rushing_tds = stat_totals.get("rushing_touchdowns", 0)
    kickoff_return_tds = stat_totals.get("kickoff_return_touchdowns", 0)
    fgs = stat_totals.get("fg_made", 0)
    pats = stat_totals.get("pat_made", 0)
    
    # Note: passing_tds and receiving_tds are the same plays, so count unique TDs
    # They should always be equal, but use max to handle any edge cases
    # If they're not equal, that's a bug we should catch
    pass_rec_tds = max(passing_tds, receiving_tds)
    if passing_tds != receiving_tds:
        print(f"  ⚠️  WARNING: Passing TDs ({passing_tds}) != Receiving TDs ({receiving_tds})!")
    total_tds = pass_rec_tds + rushing_tds + kickoff_return_tds
    
    expected_score = (total_tds * 6) + (pats * 1) + (fgs * 3)
    
    print(f"\n=== SCORING VERIFICATION: {team.name} ===")
    print(f"Actual Score: {actual_score}")
    print(f"Expected from Stats: {expected_score}")
    print(f"  - Passing TDs: {passing_tds}")
    print(f"  - Receiving TDs: {receiving_tds}")
    print(f"  - Rushing TDs: {rushing_tds}")
    print(f"  - Kickoff Return TDs: {kickoff_return_tds}")
    print(f"  - Unique Pass/Rec TDs: {pass_rec_tds}")
    print(f"  - Total TDs: {total_tds}")
    print(f"  - PATs Made: {pats}")
    print(f"  - Field Goals: {fgs}")
    print(f"  - Calculation: ({total_tds} TDs × 6) + ({pats} PATs × 1) + ({fgs} FGs × 3) = {expected_score}")
    
    if actual_score != expected_score:
        print(f"⚠️  MISMATCH! Difference: {actual_score - expected_score} points")
    else:
        print("✅ Score matches stats!")
    
    return actual_score == expected_score

def simulate_overtime(home_team, away_team, score_dict, verbose=False):
    """
    Simulate college football overtime
    Rules:
    - Each team gets a possession starting at opponent's 25-yard line
    - Teams alternate possessions
    - If tied after both teams have had a possession, go to next OT period
    - Starting in 2nd OT: Teams must go for 2 after touchdowns (no PATs)
    - Starting in 3rd OT: Teams alternate 2-point conversion attempts (no full possessions)
    """
    ot_periods = []
    ot_number = 1
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"OVERTIME - Score tied {score_dict[home_team.name]}-{score_dict[away_team.name]}")
        print(f"{'='*70}\n")
    
    while True:
        if verbose:
            print(f"\n--- OVERTIME PERIOD {ot_number} ---")
        
        # Starting in 3rd OT, use 2-point conversion attempts only
        if ot_number >= 3:
            if verbose:
                print("3rd Overtime: 2-point conversion attempts")
            
            # Home team attempts first
            home_success = sim_two_point_conversion(home_team.get_offense(), away_team.get_defense(), verbose, home_team.name)
            if home_success:
                score_dict[home_team.name] += 2
            
            # Away team attempts
            away_success = sim_two_point_conversion(away_team.get_offense(), home_team.get_defense(), verbose, away_team.name)
            if away_success:
                score_dict[away_team.name] += 2
            
            ot_periods.append({
                'period': ot_number,
                'home_score': 2 if home_success else 0,
                'away_score': 2 if away_success else 0
            })
            
            # Check if game is decided
            if score_dict[home_team.name] != score_dict[away_team.name]:
                if verbose:
                    print(f"\nGame Over! {home_team.name if score_dict[home_team.name] > score_dict[away_team.name] else away_team.name} wins in Overtime Period {ot_number}!")
                break
            
            # If still tied, continue to next period
            ot_number += 1
            continue
        
        # Overtime periods 1-2: Full possessions from 25-yard line
        ot_scores = {home_team.name: 0, away_team.name: 0}
        
        # Home team possession first
        if verbose:
            print(f"{home_team.name} possession (starting at 25-yard line)")
        offense = home_team
        defense = away_team
        
        # Simulate drive from 25-yard line (75 yards from own goal = 25 yards from opponent goal)
        play_ran, result, yardline, _ = sim_drive(
            offense, defense, 1, 10, 75, 9999, hurrying=False, verbose=verbose
        )
        
        if result == 'touchdown':
            ot_scores[home_team.name] += 6
            score_dict[home_team.name] += 6
            debug_touchdowns.append({
                'team': home_team.name,
                'play_type': play_ran,
                'points': 6
            })
            
            # In 2nd OT and beyond, must go for 2 (no PATs)
            if ot_number >= 2:
                if verbose:
                    print(f"{home_team.name} must go for 2...")
                two_pt_success = sim_two_point_conversion(offense.get_offense(), defense.get_defense(), verbose, home_team.name)
                if two_pt_success:
                    ot_scores[home_team.name] += 2
                    score_dict[home_team.name] += 2
            else:
                # 1st OT: Regular PAT
                pat_made = sim_pat(home_team.get_kicker(), verbose)
                if pat_made:
                    ot_scores[home_team.name] += 1
                    score_dict[home_team.name] += 1
                    debug_pats.append({'team': home_team.name, 'made': True})
                else:
                    debug_pats.append({'team': home_team.name, 'made': False})
        elif result == 'field goal':
            ot_scores[home_team.name] += 3
            score_dict[home_team.name] += 3
            debug_field_goals.append({
                'team': home_team.name,
                'points': 3
            })
        
        # Away team possession
        if verbose:
            print(f"\n{away_team.name} possession (starting at 25-yard line)")
        offense = away_team
        defense = home_team
        
        play_ran, result, yardline, _ = sim_drive(
            offense, defense, 1, 10, 75, 9999, hurrying=False, verbose=verbose
        )
        
        if result == 'touchdown':
            ot_scores[away_team.name] += 6
            score_dict[away_team.name] += 6
            debug_touchdowns.append({
                'team': away_team.name,
                'play_type': play_ran,
                'points': 6
            })
            
            # In 2nd OT and beyond, must go for 2 (no PATs)
            if ot_number >= 2:
                if verbose:
                    print(f"{away_team.name} must go for 2...")
                two_pt_success = sim_two_point_conversion(offense.get_offense(), defense.get_defense(), verbose, away_team.name)
                if two_pt_success:
                    ot_scores[away_team.name] += 2
                    score_dict[away_team.name] += 2
            else:
                # 1st OT: Regular PAT
                pat_made = sim_pat(away_team.get_kicker(), verbose)
                if pat_made:
                    ot_scores[away_team.name] += 1
                    score_dict[away_team.name] += 1
                    debug_pats.append({'team': away_team.name, 'made': True})
                else:
                    debug_pats.append({'team': away_team.name, 'made': False})
        elif result == 'field goal':
            ot_scores[away_team.name] += 3
            score_dict[away_team.name] += 3
            debug_field_goals.append({
                'team': away_team.name,
                'points': 3
            })
        
        ot_periods.append({
            'period': ot_number,
            'home_score': ot_scores[home_team.name],
            'away_score': ot_scores[away_team.name]
        })
        
        if verbose:
            print(f"\nOT Period {ot_number} Score: {home_team.name} {ot_scores[home_team.name]}, {away_team.name} {ot_scores[away_team.name]}")
            print(f"Total Score: {home_team.name} {score_dict[home_team.name]}, {away_team.name} {score_dict[away_team.name]}")
        
        # Check if game is decided
        if score_dict[home_team.name] != score_dict[away_team.name]:
            if verbose:
                print(f"\nGame Over! {home_team.name if score_dict[home_team.name] > score_dict[away_team.name] else away_team.name} wins in Overtime Period {ot_number}!")
            break
        
        # If still tied, continue to next period
        ot_number += 1
    
    return ot_periods

def simulate_full_game():
    global debug_touchdowns, debug_field_goals, debug_pats
    from play_functions import debug_td_stats
    debug_touchdowns = []
    debug_field_goals = []
    debug_pats = []
    debug_td_stats.clear()  # Reset TD stats tracking
    
    score = {home_team.name: 0, away_team.name: 0}
    receiving_team_first_half = determine_receiving_team()
    score, home_half1, away_half1 = start_half(receiving_team_first_half, score, half=1)
    receiving_team_second_half = "away" if receiving_team_first_half == "home" else "home"
    score, home_half2, away_half2 = start_half(receiving_team_second_half, score, half=2)
    
    # Combine quarter scores from both halves
    quarter_scores = {
        home_team.name: [home_half1[0], home_half1[1], home_half2[0], home_half2[1]],
        away_team.name: [away_half1[0], away_half1[1], away_half2[0], away_half2[1]]
    }
    
    # Check for tie and go to overtime if needed
    ot_periods = []
    if score[home_team.name] == score[away_team.name]:
        ot_periods = simulate_overtime(home_team, away_team, score, verbose=True)
    
    # Debug summary
    print("\n=== DEBUG: Scoring Events ===")
    print(f"Touchdowns Scored: {len(debug_touchdowns)}")
    for i, td in enumerate(debug_touchdowns, 1):
        print(f"  TD {i}: {td['team']} - {td['play_type']} (+6 points)")
    print(f"\nTouchdown Stats Assigned: {len(debug_td_stats)}")
    for i, td_stat in enumerate(debug_td_stats, 1):
        if td_stat['type'] in ['passing', 'passing_checkdown']:
            print(f"  TD Stat {i}: {td_stat['type']} - QB: {td_stat['qb']}, Receiver: {td_stat['receiver']} ({td_stat['receiver_position']})")
        else:
            print(f"  TD Stat {i}: {td_stat['type']} - Player: {td_stat['player']} ({td_stat['position']})")
    print(f"\nField Goals: {len(debug_field_goals)}")
    for i, fg in enumerate(debug_field_goals, 1):
        print(f"  FG {i}: {fg['team']} (+3 points)")
    print(f"PATs: {len(debug_pats)}")
    pats_by_team = {}
    for pat in debug_pats:
        team = pat['team']
        if team not in pats_by_team:
            pats_by_team[team] = {'made': 0, 'missed': 0}
        if pat['made']:
            pats_by_team[team]['made'] += 1
        else:
            pats_by_team[team]['missed'] += 1
    for team, counts in pats_by_team.items():
        print(f"  {team}: {counts['made']} made, {counts['missed']} missed")
    
    # Compare touchdowns scored vs stats assigned
    # Count player-level TDs (exclude kickoff return TDs which are team-level stats)
    player_level_tds = [td for td in debug_touchdowns if td.get('play_type') != 'kickoff_return']
    if len(player_level_tds) != len(debug_td_stats):
        print(f"\n⚠️  WARNING: Mismatch! {len(player_level_tds)} player-level TDs scored but {len(debug_td_stats)} TD stats assigned!")
    
    produce_box_score(home_team, away_team, score[home_team.name], score[away_team.name], quarter_scores, ot_periods, True)
    
    # Verify scoring
    verify_scoring(home_team, score[home_team.name])
    verify_scoring(away_team, score[away_team.name])

