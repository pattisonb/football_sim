from roster import Player, Team, initialize_teams
from game_functions import sim_kickoff, sim_pat, apply_baseline_fatigue, produce_box_score
from drive_functions import sim_drive
import random

teams = initialize_teams("game_sim/rosters.json")
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
    start_yardline = kickoff_yardline

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
            if sim_pat(driving_team.get_kicker()):
                if verbose:
                    print(f"{driving_team.name} PAT is GOOD.")
                score_dict[driving_team.name] += 1
            else:
                if verbose:
                    print(f"{driving_team.name} PAT is NO GOOD.")
            start_yardline = sim_kickoff(driving_team.get_kicker())

        elif result == 'field goal':
            if verbose:
                print(f"{driving_team.name} FIELD GOAL is GOOD.")
            score_dict[driving_team.name] += 3
            start_yardline = sim_kickoff(driving_team.get_kicker())

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

        # Switch possession
        driving_team = away_team if driving_team == home_team else home_team

    if verbose:
        print(f"--- End of Half {half} ---")
        print(f"Score: {home_team.name} {score_dict[home_team.name]} - {away_team.name} {score_dict[away_team.name]}\n")

    return score_dict

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

def simulate_full_game():
    score = {home_team.name: 0, away_team.name: 0}
    receiving_team_first_half = determine_receiving_team()
    score = start_half(receiving_team_first_half, score, half=1)
    receiving_team_second_half = "away" if receiving_team_first_half == "home" else "home"
    score = start_half(receiving_team_second_half, score, half=2)
    produce_box_score(home_team, away_team, score[home_team.name], score[away_team.name], True)

