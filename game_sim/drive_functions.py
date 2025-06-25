import random
from play_functions import get_pass_yards, get_run_yards
from game_functions import get_kick_attempt_range, get_punt_distance, apply_general_fatigue
RUN_PASS_TABLE = {
    1: [(3,  0.75), (6,  0.65), (10, 0.55), (float('inf'), 0.40)],
    2: [(3,  0.70), (6,  0.50), (10, 0.40), (float('inf'), 0.25)],
    3: [(3,  0.60), (6,  0.35), (10, 0.20), (float('inf'), 0.10)],
    4: [(1,  0.55), (3,  0.35), (6,  0.20), (float('inf'), 0.05)],
}

def run_probability(down, to_go):
    """Lookup run% by down & distance."""
    for thresh, prob in RUN_PASS_TABLE.get(down, []):
        if to_go <= thresh:
            return prob
    return 0.25

def determine_offense_play(down, first_down, last_play_type=None, last_gain=0):
    run_chance = run_probability(down, first_down)

    # Reward success
    if last_play_type == "run" and last_gain >= 6:
        run_chance += 0.1
    elif last_play_type == "pass" and last_gain >= 10:
        run_chance -= 0.05

    # Clamp between 0.1 and 0.9
    run_chance = max(0.1, min(0.9, run_chance))

    return "run" if random.random() < run_chance else "pass"

def determine_defense_play(down, first_down):
    if down == 1:
        if first_down <= 3:
            return "defend_run" if random.random() < 0.75 else "defend_pass"
        elif first_down <= 6:
            return "defend_run" if random.random() < 0.6 else "defend_pass"
        elif first_down <= 10:
            return "defend_pass" if random.random() < 0.55 else "defend_run"
        else:
            return "defend_pass" if random.random() < 0.7 else "defend_run"

    elif down == 2:
        if first_down <= 3:
            return "defend_run" if random.random() < 0.65 else "defend_pass"
        elif first_down <= 6:
            return "defend_pass" if random.random() < 0.6 else "defend_run"
        elif first_down <= 10:
            return "defend_pass" if random.random() < 0.7 else "defend_run"
        else:
            return "defend_pass" if random.random() < 0.8 else "defend_run"

    elif down == 3:
        if first_down <= 3:
            return "defend_run" if random.random() < 0.6 else "defend_pass"
        elif first_down <= 6:
            return "defend_pass" if random.random() < 0.7 else "defend_run"
        elif first_down <= 10:
            return "defend_pass" if random.random() < 0.85 else "defend_run"
        else:
            return "defend_pass" if random.random() < 0.9 else "defend_run"

    else:
        return "defend_pass"
    
def determine_line_advantage(offense, defense, offense_play, defense_play) :
    offense_blocking = 0
    for player in offense :
        if player.position == 'OL' or offense_play == "run" and player.position == 'TE':
            offense_blocking += player.strength
            if offense_play == "run" :
                offense_blocking += player.run_blocking
            elif offense_play == "pass" :
                offense_blocking += player.pass_blocking
    defense_rushing = 0
    for player in defense :
        if player.position == 'DL' or defense_play == "defend_run" and 'LB' in player.position:
            defense_rushing += player.strength
            if defense_play == "defend_run" :
                defense_rushing += player.rushing
            elif defense_play == "defend_pass" :
                defense_rushing += player.rushing
    return offense_blocking - defense_rushing
    
def sim_play(offense_team, defense_team, down, first_down_yardage, yardline, hurrying=False, last_play_type=None, last_gain=0, verbose=True) :
    apply_general_fatigue(offense_team.get_offense(), defense_team.get_defense())
    offense_team.apply_fatigue_penalties()
    defense_team.apply_fatigue_penalties()
    offense_team.sub_skill_position_players(50)
    defense_team.sub_defensive_players(50)
    offense_team.recover_bench_players()
    defense_team.recover_bench_players()
    offense = offense_team.get_offense()
    defense = defense_team.get_defense()
    penalty_yards = 0
    penalty_flag = False
    time_spent = 0
    if not hurrying:
        time_spent = random.randint(25, 40)  # normal tempo
    else:
        time_spent = random.randint(10, 25)
    if random.random() < 0.08:  # 8% chance of offensive penalty
            penalty_type = random.choices(
                ["false_start", "holding", "offensive_pass_interference", "delay_of_game"],
                weights=[0.3, 0.4, 0.15, 0.15],
                k=1
            )[0]

            if penalty_type == "false_start":
                penalty_yards = -5
            elif penalty_type == "holding":
                penalty_yards = -10
            elif penalty_type == "offensive_pass_interference":
                penalty_yards = -15
            elif penalty_type == "delay_of_game":
                penalty_yards = -5

            yardline = max(1, yardline + penalty_yards)
            first_down_yardage += abs(penalty_yards)
            penalty_flag = True
            if verbose:
                print(f"Penalty: {penalty_type.replace('_', ' ').title()} for {abs(penalty_yards)} yards")
            return "penalty", "offensive penalty", penalty_yards, time_spent
    # --- Random Defensive Penalty Logic ---
    if random.random() < 0.05 and not penalty_flag:  # ~5% chance
            penalty_flag = True
            penalty_type = random.choices(
                ["offside", "pass_interference", "facemask"],
                weights=[0.4, 0.4, 0.2],
                k=1
            )[0]

            if penalty_type == "offside":
                yardline = min(99, yardline + 5)
                penalty_yards -= 5
            elif penalty_type == "pass_interference":
                gain = random.randint(10, 25)
                penalty_yards = gain  # reset first down
            elif penalty_type == "facemask":
                penalty_yards = 15

            if verbose:
                print(f"Defensive Penalty: {penalty_type.replace('_', ' ').title()}")
            return "penalty", "defensive penalty", penalty_yards, time_spent

    elif not penalty_flag :
        offense_play = determine_offense_play(down, first_down_yardage, last_play_type, last_gain)
        defense_play = determine_defense_play(down, first_down_yardage)
        offense_line_advantage = determine_line_advantage(offense, defense, offense_play, defense_play)
        guessed_play = offense_play in defense_play
        play_ran = "run"
        if offense_play == "run":
            result, yards_gained = get_run_yards(offense, defense, down, first_down_yardage, guessed_play, offense_line_advantage, yardline)
        elif offense_play == "pass":
            result, yards_gained = get_pass_yards(offense, defense, down, first_down_yardage, guessed_play, offense_line_advantage, yardline)
            play_ran = "pass"
        return(play_ran, result, yards_gained, time_spent)

def process_play(result, play_type, yards, yardline, down, first_down_yardage) :
    if result == "fumble" or result == "interception" :
        down = 5
    if result == 'run':
        yardline += yards
        first_down_yardage -= yards
        down += 1
    if result == 'successful_pass':
        yardline += yards
        first_down_yardage -= yards
        down += 1
    if result == 'offensive penalty':
        pre_penalty_yardline = yardline
        yardline = max(0, yardline + yards)
        actual_penalty = pre_penalty_yardline - yardline
        first_down_yardage += actual_penalty
    if result == 'defensive penalty':
        pre_penalty_yardline = yardline
        yardline = min(99, yardline + yards)
        actual_penalty = yardline - pre_penalty_yardline
        first_down_yardage = max(0, first_down_yardage - actual_penalty)
    if result == 'sack' :
        #implement safety logic
        down += 1
        yardline += yards
        first_down_yardage -= yards
    if result == 'incomplete' :
        down += 1
    if first_down_yardage <= 0 :
        down = 1
        first_down_yardage = 10
    if yardline >= 100 :
        down = 6
    return down, first_down_yardage, yardline

def should_go_for_it(distance, yardline):
    # Never go for it in own territory unless it's short and late in game
    if yardline < 50:
        return distance <= 1 and random.random() < 0.3
    # 4th and short in enemy territory
    if distance <= 2 and yardline >= 50 and yardline < 70:
        return random.random() < 0.5

    if yardline > 85:
        return distance <= 5 and random.random() < 0.6

    return False

def attempt_kick(yardline, kicker) :
    kicker.stats["fg_attempted"] += 1
    kick_make_chance = 1
    kick_distance = (100 - yardline)+17
    if kick_distance <= 30:
        kick_make_chance = 0.98
    elif kick_distance <= 39:
        kick_make_chance = 0.94
    elif kick_distance <= 49:
        kick_make_chance = 0.85
    elif kick_distance <= 55:
        kick_make_chance = 0.65
    else:
        kick_make_chance = 0.4
    kick_make_chance = max(0.05, min(1.0, kick_make_chance + ((kicker.kick_accuracy - 50)*0.005)))
    kick_made = True if random.random() < kick_make_chance else False
    if kick_made :
        kicker.stats["fg_made"] += 1
    return kick_made

def attempt_punt(yardline, punter):
    punt_distance = get_punt_distance(punter)
    punt_accuracy = punter.punt_accuracy  # default to 50 if missing

    landing_spot = yardline + punt_distance
    punter.stats["punts"] += 1
    # If far from end zone, max power punt is safe
    if landing_spot + 10 < 100:
        punter.stats["punt_yards"] += (punt_distance)
        return landing_spot, punt_distance

    # Placement needed – evaluate touchback or pin inside 5
    accuracy_factor = (punt_accuracy - 50) / 100  # range: -0.5 to +0.5

    # Base chance to pin inside the 5 is 25%, modulated by accuracy
    pin_chance = 0.25 + accuracy_factor

    if landing_spot >= 95:  # Ball lands inside the 5
        if random.random() < pin_chance:
            pinned_spot = random.randint(1, 4)  # Stick inside the 5
            punter.stats["punt_yards"] += (100 - pinned_spot - yardline)
            return 100 - pinned_spot, 100 - pinned_spot - yardline
        else:
            punter.stats["punt_yards"] += (100 - yardline - 20)
            return 80, 100 - yardline - 20  # Ball placed at 20

    # Else: standard returnable punt
    return_yards = random.randint(0, 15) if landing_spot < 90 else 0
    final_spot = max(landing_spot - return_yards, 1)
    punter.stats["punt_yards"] += (final_spot - yardline)
    return final_spot, final_spot - yardline

def sim_drive(offense, defense, down, first_down_yardage, yardline, seconds_remaining, hurrying=False, verbose=True) :
    kicker = next(p for p in offense.get_offense() if p.position == 'K')
    punter = next(p for p in offense.get_offense() if p.position == 'P')
    last_play_type =  None
    last_gain = 0
    result = ""
    while down < 4 :
        if verbose :
            print(down, "and", first_down_yardage, "at the", yardline)
        play_ran, result, yards_gained, time = sim_play(offense, defense, down, first_down_yardage, yardline, hurrying, last_play_type, last_gain, False)
        seconds_remaining -= time
        down, first_down_yardage, yardline = process_play(result, play_ran, yards_gained, yardline, down, first_down_yardage)
    if down == 4 :
        if should_go_for_it(first_down_yardage, yardline) :
            play_ran, result, yards_gained, time = sim_play(offense, defense, down, first_down_yardage, yardline, hurrying, last_play_type, last_gain, False)
            seconds_remaining -= time
            down, first_down_yardage, yardline = process_play(result, play_ran, yards_gained, yardline, down, first_down_yardage)
        else :
            if yardline >= get_kick_attempt_range(kicker):
                kick_time = random.randint(5, 7)
                seconds_remaining -= kick_time
                if attempt_kick(yardline, kicker):
                    if verbose:
                        print((100 - yardline)+17, "yard kick is good!")
                    result = "field goal"
                else :
                    result = "missed kick"
            else:
                yardline, punt_distance = attempt_punt(yardline, punter)
                punt_time = random.randint(6, 10)
                seconds_remaining -= punt_time
                if verbose:
                    print(punt_distance, "yard punt.")
                result = "punt"
    if down == 5 :
        result = "turnover"
    if down == 6 :
        result = "touchdown"
    return play_ran, result, yardline, seconds_remaining
    
