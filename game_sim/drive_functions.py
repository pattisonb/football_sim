import random
from play_functions import get_pass_yards, get_run_yards
from game_functions import get_kick_attempt_range, get_punt_distance, apply_general_fatigue
from game_config import sliders
RUN_PASS_TABLE = {
    1: [
        (3,  0.80),
        (6,  0.70),
        (10, 0.60),
        (float('inf'), 0.45),
    ],
    2: [
        (3,  0.75),
        (6,  0.58),
        (10, 0.45),
        (float('inf'), 0.30),
    ],
    3: [
        (2,  0.70),
        (5,  0.50),
        (9,  0.28),
        (float('inf'), 0.12),
    ],
    4: [
        (1,  0.60),
        (3,  0.35),
        (6,  0.18),
        (float('inf'), 0.06),
    ],
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
    
def sim_play(offense_team, defense_team, down, first_down_yardage, yardline, hurrying=False, last_play_type=None, last_gain=0, seconds_remaining=2400, verbose=True) :
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
    # Base time per play - increased to reduce total plays per game
    # Target: 65-75 plays per team (4800 seconds / 70 plays = ~68 seconds per play average)
    # With timeouts, penalties, etc., aim for ~30-40 seconds per play on average
    # Adjusted by game speed slider (higher = faster game = less time per play)
    game_speed_mult = 2.0 - sliders.get_multiplier(sliders.game_speed)  # Invert: higher slider = faster
    base_time_range = (28, 42) if not hurrying else (12, 22)
    base_time = random.randint(
        int(base_time_range[0] * game_speed_mult),
        int(base_time_range[1] * game_speed_mult)
    )
    
    # Add fatigue/tempo drag - plays slow down as game progresses
    # Use seconds_remaining to estimate game progress (2400 = start, 0 = end)
    game_progress = 1.0 - (seconds_remaining / 2400.0)  # 0.0 to 1.0
    fatigue_modifier = 1.0 + (game_progress * 0.15)  # Up to 15% slower as game progresses
    
    if not hurrying:
        time_spent = int(base_time * fatigue_modifier)
    else:
        time_spent = int(base_time * (1.0 + game_progress * 0.05))  # Less fatigue impact in hurry-up
    
    # Offensive penalties adjusted by slider (lower slider = more penalties)
    off_penalty_chance = sliders.get_inverse_percentage_adjustment(sliders.offensive_penalties, 0.10)
    if random.random() < off_penalty_chance:  # 10% chance of offensive penalty (slightly more in college)
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
    # Defensive penalties adjusted by slider (lower slider = more penalties)
    def_penalty_chance = sliders.get_inverse_percentage_adjustment(sliders.defensive_penalties, 0.06)
    if random.random() < def_penalty_chance and not penalty_flag:  # ~6% chance (slightly more in college)
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
    if result == 'checkdown_pass':
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
        # Cap yardline at 99 to prevent penalties from directly scoring touchdowns
        # If penalty would put ball in end zone, place it at the 1 yard line
        new_yardline = yardline + yards
        if new_yardline >= 100:
            yardline = 1  # Place at 1 yard line instead of scoring
            actual_penalty = 100 - pre_penalty_yardline - 1  # Calculate actual penalty yards
        else:
            yardline = new_yardline
            actual_penalty = yards
        first_down_yardage = max(0, first_down_yardage - actual_penalty)
    if result == 'sack' :
        #implement safety logic
        down += 1
        yardline += yards
        first_down_yardage -= yards
    if result == 'incomplete' :
        down += 1
    # Check for touchdown BEFORE first down reset to ensure down=6 is set correctly
    if yardline >= 100 :
        down = 6
    if first_down_yardage <= 0 :
        # Only reset down if we haven't scored a touchdown
        if down != 6:
            down = 1
            first_down_yardage = 10
    return down, first_down_yardage, yardline

def should_go_for_it(distance, yardline, seconds_remaining=2400):
    # Smarter go-for-it logic based on distance, yardline, and time
    # Red zone (inside 20): More aggressive, especially on 4th and short
    if yardline >= 80:
        if distance <= 1:
            return True  # Always go for it on 4th and 1 in red zone
        elif distance <= 3:
            return random.random() < 0.75  # 75% chance on 4th and 2-3
        elif distance <= 5:
            return random.random() < 0.50  # 50% chance on 4th and 4-5
        else:
            return False  # Too long in red zone
    
    # Mid-field (50-79): Moderate aggression
    if yardline >= 50:
        if distance <= 1:
            return random.random() < 0.70  # 70% chance on 4th and 1
        elif distance <= 2:
            return random.random() < 0.40  # 40% chance on 4th and 2
        else:
            return False
    
    # Own territory (< 50): Conservative unless short and late
    if yardline < 50:
        if distance <= 1 and seconds_remaining < 300:  # Late in half/game
            return random.random() < 0.50
        elif distance <= 1:
            return random.random() < 0.25  # 25% chance otherwise
        else:
            return False
    
    return False

def attempt_kick(yardline, kicker, defense_team=None) :
    kicker.stats["fg_attempted"] += 1
    
    # College chaos: occasional blocked kick (1% chance)
    if random.random() < 0.01:
        if defense_team:
            defense_team.team_stats["blocked_kicks"] += 1
        return False, True  # Kick blocked, return (made, blocked)
    
    # Adjust FG accuracy by kicking accuracy slider
    kick_acc_mult = sliders.get_multiplier(sliders.kicking_accuracy)
    kick_make_chance = 1
    kick_distance = (100 - yardline)+17
    # College field goal percentages (slightly lower than NFL, especially at longer distances)
    if kick_distance <= 30:
        kick_make_chance = 0.96 * kick_acc_mult  # Slightly lower than NFL
    elif kick_distance <= 39:
        kick_make_chance = 0.90 * kick_acc_mult  # College kickers less reliable
    elif kick_distance <= 49:
        kick_make_chance = 0.75 * kick_acc_mult  # More variance in college
    elif kick_distance <= 55:
        kick_make_chance = 0.50 * kick_acc_mult  # College kickers struggle more at distance
    else:
        kick_make_chance = 0.25 * kick_acc_mult  # Very difficult in college
    kick_make_chance = max(0.03, min(0.98, kick_make_chance + ((kicker.kick_accuracy - 50)*0.005*kick_acc_mult)))
    kick_made = True if random.random() < kick_make_chance else False
    if kick_made :
        kicker.stats["fg_made"] += 1
    return kick_made, False  # Return (made, blocked)

def attempt_punt(yardline, punter, defense_team=None):
    # College chaos: occasional fake punt attempt (0.3% chance when in own territory)
    if yardline < 50 and random.random() < 0.003:
        # Fake punt - treat as turnover for now (could add fake punt logic later)
        punter.stats["punts"] += 1
        return yardline, 0, False  # No yards gained, turnover, not blocked
    
    punt_distance = get_punt_distance(punter)
    punt_accuracy = punter.punt_accuracy  # default to 50 if missing

    landing_spot = yardline + punt_distance
    punter.stats["punts"] += 1
    
    # College chaos: occasional blocked punt (0.5% chance)
    if random.random() < 0.005:
        if defense_team:
            defense_team.team_stats["blocked_punts"] += 1
        return yardline, 0, True  # Punt blocked, no yards
    # If far from end zone, max power punt is safe
    if landing_spot + 10 < 100:
        punter.stats["punt_yards"] += (punt_distance)
        return landing_spot, punt_distance, False

    # Placement needed – evaluate touchback or pin inside 5
    accuracy_factor = (punt_accuracy - 50) / 100  # range: -0.5 to +0.5

    # Base chance to pin inside the 5 is 25%, modulated by accuracy
    pin_chance = 0.25 + accuracy_factor

    if landing_spot >= 95:  # Ball lands inside the 5
        if random.random() < pin_chance:
            pinned_spot = random.randint(1, 4)  # Stick inside the 5
            punter.stats["punt_yards"] += (100 - pinned_spot - yardline)
            return 100 - pinned_spot, 100 - pinned_spot - yardline, False
        else:
            punter.stats["punt_yards"] += (100 - yardline - 20)
            return 80, 100 - yardline - 20, False  # Ball placed at 20

    # Else: standard returnable punt
    return_yards = random.randint(0, 15) if landing_spot < 90 else 0
    final_spot = max(landing_spot - return_yards, 1)
    punter.stats["punt_yards"] += (final_spot - yardline)
    return final_spot, final_spot - yardline, False

def sim_drive(offense, defense, down, first_down_yardage, yardline, seconds_remaining, hurrying=False, verbose=True) :
    kicker = next(p for p in offense.get_offense() if p.position == 'K')
    punter = next(p for p in offense.get_offense() if p.position == 'P')
    last_play_type =  None
    last_gain = 0
    result = ""
    play_ran = ""  # Initialize play_ran to track the type of play
    while down < 4 :
        if verbose :
            print(down, "and", first_down_yardage, "at the", yardline)
        play_ran, result, yards_gained, time = sim_play(offense, defense, down, first_down_yardage, yardline, hurrying, last_play_type, last_gain, seconds_remaining, False)
        seconds_remaining -= time
        down, first_down_yardage, yardline = process_play(result, play_ran, yards_gained, yardline, down, first_down_yardage)
    if down == 4 :
        if should_go_for_it(first_down_yardage, yardline) :
            play_ran, result, yards_gained, time = sim_play(offense, defense, down, first_down_yardage, yardline, hurrying, last_play_type, last_gain, seconds_remaining, False)
            seconds_remaining -= time
            down, first_down_yardage, yardline = process_play(result, play_ran, yards_gained, yardline, down, first_down_yardage)
        else :
            if yardline >= get_kick_attempt_range(kicker):
                kick_time = random.randint(5, 7)
                seconds_remaining -= kick_time
                kick_made, kick_blocked = attempt_kick(yardline, kicker, defense)
                if kick_blocked:
                    if verbose:
                        print("Field goal BLOCKED!")
                    result = "missed kick"
                elif kick_made:
                    if verbose:
                        print((100 - yardline)+17, "yard kick is good!")
                    result = "field goal"
                else :
                    result = "missed kick"
            else:
                yardline, punt_distance, punt_blocked = attempt_punt(yardline, punter, defense)
                punt_time = random.randint(6, 10)
                seconds_remaining -= punt_time
                if punt_blocked:
                    if verbose:
                        print("Punt BLOCKED!")
                    result = "turnover"  # Blocked punt is a turnover
                else:
                    if verbose:
                        print(punt_distance, "yard punt.")
                    result = "punt"
    if down == 5 :
        result = "turnover"
    if down == 6 :
        # Only set touchdown if we actually have a valid play result
        # If result is still empty or a penalty, something went wrong
        if result in ['run', 'successful_pass', 'checkdown_pass']:
            result = "touchdown"
            # Safety check: if yardline >= 100 but TD stat wasn't assigned, assign it now
            # This can happen if a first down reset occurred after the TD play
            if result == "touchdown" and yardline >= 100:
                # Check if TD stat was already assigned by looking at the play type
                # We need to assign it retroactively - find the last player who had the ball
                # For now, we'll handle this in the play functions, but add a safeguard here
                pass  # TD stat should already be assigned in get_run_yards/get_pass_yards
        else:
            # If down==6 but result isn't a valid TD play, it might be from a penalty
            # In this case, we shouldn't score a TD - this is a bug we're catching
            # For now, treat it as a first down at the 1 yard line
            result = "first_down"
            yardline = 1
            down = 1
            first_down_yardage = 10
    return play_ran, result, yardline, seconds_remaining
    
