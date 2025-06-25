import random
from game_functions import apply_pass_fatigue, apply_run_fatigue

#{'pass_attempts': 0, 'completions': 0, 'pass_yards': 0, 'interceptions_thrown': 0, 'sacks_taken': 0, 'carries': 0, 
# 'rush_yards': 0, 'fumbles': 0, 'receptions': 0, 'receiving_yards': 0, 'targets': 0, 'touchdowns': 0}
def handle_qb_scramble(qb, verbose=False):
    intelligence = qb.intelligence
    speed = qb.speed
    # Chance to scramble if no one is open
    scramble_chance = max(0.05, (100 - intelligence) / 150)
    if speed < 60:
        scramble_chance *= 0.5

    if random.random() > scramble_chance:
        return None  # No scramble

    # Scramble happens
    gain_odds = 0.5 + ((speed - 50) / 100)  # 50% base + bonus for speed > 50
    gain_odds = min(0.95, max(0.1, gain_odds))  # Clamp between 10% and 95%

    gain_yards = random.randint(1, 12)
    lose_yards = random.randint(-6, -1)

    yards = gain_yards if random.random() < gain_odds else lose_yards
    return yards

def assign_forced_fumble(defense, base_yards, verbose=False):
    # Map yardage to positional group
    if base_yards <= 2:
        valid_positions = ['rolb', 'olb', 'mlb']  # front seven - assume close to line
    elif base_yards <= 7:
        valid_positions = ['rolb', 'olb', 'mlb', 's']  # LBs and safeties
    else:
        valid_positions = ['cb', 's']  # defensive backs

    # Filter defense players matching valid positions
    candidates = [p for p in defense if p.position.lower() in valid_positions]
    if not candidates:
        candidates = defense  # fallback to anyone on defense

    # Weight by tackling and strength (or just tackling if you want it simpler)
    weights = [(p.tackling + p.strength) / 2 for p in candidates]

    # Choose one
    forced_by = random.choices(candidates, weights=weights, k=1)[0]
    forced_by.stats['forced_fumbles'] = forced_by.stats.get('forced_fumbles', 0) + 1

    if verbose:
        print(f"Fumble forced by {forced_by.name} ({forced_by.position})")

    return forced_by

import random

def assign_tackles(defense, base_yards, verbose=False):
    # Define tiered weights
    short_weights = {
        'dl': 0.35,
        'rolb': 0.2,
        'olb': 0.15,
        'lb': 0.2,
        's': 0.1
    }
    mid_weights = {
        'rolb': 0.25,
        'olb': 0.2,
        'lb': 0.25,
        's': 0.2,
        'dl': 0.1
    }
    long_weights = {
        's': 0.4,
        'cb': 0.4,
        'rolb': 0.08,
        'olb': 0.06,
        'lb': 0.06
    }

    # Determine blend weights
    if base_yards <= 2:
        weight_profile = short_weights
    elif base_yards <= 7:
        weight_profile = mid_weights
    else:
        weight_profile = long_weights

    # Build weighted candidate list
    candidates = []
    weights = []
    cb_count = 0

    for p in defense:
        pos = p.position.lower()
        pos_group = pos if pos in weight_profile else pos[:2]

        if pos_group == 'cb':
            if cb_count >= 3:
                continue  # cap CB participation
            cb_count += 1

        if pos_group in weight_profile:
            skill_weight = (p.tackling + p.intelligence) / 2
            position_weight = weight_profile[pos_group]
            candidates.append(p)
            weights.append(position_weight * skill_weight)

    # Fallback if candidate pool is empty
    if not candidates:
        candidates = defense
        weights = [(p.tackling + p.intelligence) / 2 for p in defense]

    # Solo vs assisted tackle
    is_assisted = random.random() < 0.35

    if is_assisted:
        # Weighted sampling without replacement
        if len(candidates) >= 2:
            tacklers = random.choices(candidates, weights=weights, k=5)
            seen = set()
            unique = []
            for t in tacklers:
                if t not in seen:
                    unique.append(t)
                    seen.add(t)
                if len(unique) == 2:
                    break
            tacklers = unique
        else:
            tacklers = random.choices(candidates, weights=weights, k=1)
    else:
        tacklers = random.choices(candidates, weights=weights, k=1)

    if verbose:
        if is_assisted and len(tacklers) == 2:
            print(f"Tackle by {tacklers[0].name} (solo) and {tacklers[1].name} (assist)")
        else:
            print(f"Tackle by {tacklers[0].name} (solo)")

    return tacklers


def assign_sack(defense, guessed_play=False):
    # Sack candidates: DL always, LB only if not guessed correctly
    candidates = [p for p in defense if p.position == 'DL' or (guessed_play and 'LB' in p.position)]
    if not candidates:
        return [], False

    # 25% chance to split sack
    is_half = random.random() < 0.25

    # Pick 1 or 2 players based on is_half
    selected = random.choices(candidates, weights=[p.rushing for p in candidates], k=2 if is_half else 1)

    return selected, is_half

def get_run_yards(offense, defense, down, first_down, guessed_play, offense_line_advantage, yardline, verbose=False):
    base_yards = 4.5

    # Adjust for down
    if down == 2:
        base_yards -= 0.5
    elif down == 3:
        base_yards -= 5.5
    if down == 3 and first_down > 6:
        base_yards *= 0.75

    # Always apply O-line effect (softened)
    base_yards *= (1 + offense_line_advantage / 750)

    # Defensive impact (tackling DL/LBs, reduced chance)
    for player in defense:
        if player.position not in ('DL', 'OLB', 'MLB', 'ROLB'):
            continue
        tackle_val = player.tackling
        factor = tackle_val / 250 if tackle_val >= 50 else (100 - tackle_val) / 250
        chance = (tackle_val / 100 if tackle_val >= 50 else (100 - tackle_val) / 100) * 0.5
        if random.random() < chance:
            if tackle_val >= 50:
                base_yards *= (1 - factor)
            else:
                base_yards *= (1 + factor)

    # Choose ball carrier (mostly RB, sometimes WR/QB)
    candidates = [
    p for p in offense 
    if (p.position == 'RB') or 
       (p.position == 'WR') or 
       (p.position == 'QB' and p.speed > 60)
    ]

    weights = []
    for p in candidates:
        if p.position == 'RB':
            weights.append(0.80)
        elif p.position == 'WR':
            weights.append(0.03)
        elif p.position == 'QB':
            weights.append(p.speed / 1000)  # e.g. speed 60 = 0.012
        else:
            weights.append(0.02)
    rushing_player = random.choices(candidates, weights=weights, k=1)[0]

    for key in ['speed', 'strength', 'intelligence', 'elusiveness', 'vision']:
        if key in ('elusiveness', 'vision') and rushing_player.position != 'RB':
            continue  # Skip non-RBs for these traits

        val = getattr(rushing_player, key)
        factor = val / 250 if val >= 50 else (100 - val) / 250
        chance = (val / 100 if val >= 50 else (100 - val) / 100) * 0.5
        if random.random() < chance:
            if val >= 50:
                base_yards *= (1 + factor)
            else:
                base_yards *= (1 - factor)

    # Fumble logic (based on strength and intelligence)
    fumble_base = 0.003
    strength_factor = (100 - rushing_player.strength) / 100
    intel_factor = (100 - rushing_player.intelligence) / 100
    fumble_chance = fumble_base + (strength_factor * 0.005) + (intel_factor * 0.005)

    if random.random() < fumble_chance:
        if verbose:
            print("Fumble lost by", rushing_player.name)
        rushing_player.stats["carries"] += 1
        rushing_player.stats["rush_yards"] += round(base_yards)
        rushing_player.stats["fumbles"] += 1
        apply_run_fatigue(offense, defense, rushing_player, base_yards)
        ff_player = assign_forced_fumble(defense, base_yards)
        ff_player.stats["forced_fumbles"] += 1
        ff_player.stats["tackles"] += 1
        return "fumble", 0  # turnover

    # Big Play Logic
    if rushing_player.speed > 75:
        if random.random() < 0.10:
            base_yards += random.randint(15, 40)

    # Guessed play penalty
    if guessed_play and random.random() < 0.5:
        base_yards += random.randint(-10, -1)

    # Short yardage conversion
    if first_down <= 2 and base_yards > -1.25:
        if random.random() < 0.6:
            base_yards = first_down

    # Prevent overly suppressed plays
    if base_yards < 2.0:
        base_yards = max(base_yards, random.uniform(1.5, 3.5))

    if verbose:
        print("Rush for", round(base_yards), "yards by", rushing_player.name)
    if yardline + base_yards > 100 :
        rushing_player.stats["touchdowns"] += 1
        base_yards = 100 - yardline
    rushing_player.stats["carries"] += 1
    rushing_player.stats["rush_yards"] += round(base_yards)
    apply_run_fatigue(offense, defense, rushing_player, base_yards)
    tacklers = assign_tackles(defense, base_yards)
    for player in tacklers :
        player.stats['tackles'] += 1
    return "run", round(base_yards)

def get_pass_yards(offense, defense, down, first_down, guessed_play, offense_line_advantage, yardline, verbose=False):
    qb = next(p for p in offense if p.position == "QB")
    # --- Sack logic ---
    sack_rate = 0.005 + (0.005 * down)
    if guessed_play: sack_rate += 0.1
    sack_rate -= offense_line_advantage / 5000
    if random.random() < sack_rate:
        sack_yards = int(-abs(random.gauss(8, 2)))  # More realistic sack losses
        sackers, is_half = assign_sack(defense, guessed_play=guessed_play) 
        for sacker in (sackers):
            if is_half :
                sacker.stats['sacks'] += 0.5
            else :
                sacker.stats['sacks'] += 1
            sacker.stats['tackles'] += 1
        qb.stats["sacks_taken"] += 1
        strength_factor = (100 - qb.strength) / 100
        intel_factor = (100 - qb.intelligence) / 100
        fumble_chance = 0.02 + (strength_factor * 0.01) + (intel_factor * 0.005)

        if random.random() < fumble_chance:
            qb.stats["fumbles"] += 1
            for sacker in (sackers):
                if is_half :
                    sacker.stats['forced_fumbles'] += 0.5
                else :
                    sacker.stats['forced_fumbles'] += 1
            if verbose: print("Fumble lost by", qb.name)
            apply_pass_fatigue(offense, defense)
            return "fumble", yardline + sack_yards  # Fumble
        apply_pass_fatigue(offense, defense)
        return "sack", sack_yards

    # --- Begin Pass Logic --
    coverage_players = ['CB', 'S']
    if guessed_play :
        coverage_players.append(['LOLB', 'MLB', 'ROLB'])
    coverage_factor = sum(p.coverage / 1000 for p in defense if p.position in ('CB', 'S'))
    defense_speed = [p.speed for p in defense if p.position in ('CB', 'S')]
    avg_def_speed = sum(defense_speed) / len(defense_speed) if defense_speed else 50
    # Completion chance baseline
    completion_chance = 0.35 + (
        qb.intelligence + qb.passing + qb.decision_making
    ) / 1000
    # Select potential receivers
    receiving_candidates = [p for p in offense if p.position in ('WR', 'TE')]
    receiving_candidates = random.choices(
        receiving_candidates,
        weights=[(p.route_running + p.hands + p.intelligence) / 3 for p in receiving_candidates],
        k=len(receiving_candidates)
    )

    # Boost TE targets situationally
    if down == 3 or yardline > 80:
        for p in receiving_candidates:
            if p.position == 'TE':
                completion_chance += 0.05

    receiving_player = None
    for player in receiving_candidates:
        route_running_factor = (player.route_running - 50)/200
        speed_factor = (player.speed - 50)/300
        completion_chance = completion_chance + route_running_factor + speed_factor - (coverage_factor/1.9)
        if completion_chance < 0 :
            completion_chance = 0.01
        if random.random() < completion_chance:
            receiving_player = player
            break
        completion_chance -= 0.05  # Decrease for next option

    # Successful pass
    if receiving_player:
        base_yards = random.gauss(9.5, 4)
        speed_factor = receiving_player.speed / avg_def_speed
        base_yards *= speed_factor
        if speed_factor > 1 and random.random() < 0.1:
            base_yards = random.randint(20, 70)
        yards = min(round(base_yards), 40)

        if verbose: print("Pass for", yards, "yards to", receiving_player.name)
        if yards + yardline > 100 :
                yards = 100 - yardline
                qb.stats["touchdowns"] += 1
                receiving_player.stats["touchdowns"] += 1
        else :
            tacklers = assign_tackles(defense, yards)
            for player in tacklers :
                player.stats['tackles'] += 1
        qb.stats["pass_attempts"] += 1
        qb.stats["completions"] += 1
        qb.stats["pass_yards"] += yards
        receiving_player.stats["targets"] += 1
        receiving_player.stats["receptions"] += 1
        receiving_player.stats["receiving_yards"] += yards
        apply_pass_fatigue(offense, defense, receiving_player, yards)
        return "successful_pass", yards

    # --- Checkdown fallback ---
    if random.random() < 0.18:
        rbs = [p for p in offense if p.position == 'RB']
        if rbs:
            rb = random.choice(rbs)
            yards = random.gauss(3, 2)
            if random.random() < rb.speed / 100:
                yards += random.randint(1, 9)
            yards = round(max(0, yards))
            if yards + yardline > 100 :
                yards = 100 - yardline
                qb.stats["touchdowns"] += 1
                rb.stats["touchdowns"] += 1
            else :
                tacklers = assign_tackles(defense, yards)
                for player in tacklers :
                    player.stats['tackles'] += 1
            if verbose: print("Checkdown for", yards, "yards to", rb.name)
            qb.stats["pass_attempts"] += 1
            qb.stats["completions"] += 1
            qb.stats["pass_yards"] += yards
            rb.stats["targets"] += 1
            rb.stats["receptions"] += 1
            rb.stats["receiving_yards"] += yards
            apply_pass_fatigue(offense, defense, rb, yards)
            return "checkdown_pass", yards
    highest_chance = 0
    best_defender = None
    for p in defense:
        if p.position not in coverage_players:
            continue
        chance = 0.02 + p.coverage / 10000
        if guessed_play: chance += 0.005
        chance += (100 - qb.decision_making) / 2000
        if chance > highest_chance:
            highest_chance = chance
            best_defender = p
    if best_defender and random.random() < min(highest_chance, 0.03):
        if verbose: print("Intercepted by", best_defender.name)
        #add logic for interception returns later
        qb.stats["pass_attempts"] += 1
        qb.stats["interceptions_thrown"] += 1
        best_defender.stats["interceptions"] += 1
        apply_pass_fatigue(offense, defense)
        return "interception", yardline + 10
    
 # --- QB scramble ---
    scramble_result = handle_qb_scramble(qb, verbose=False)
    if scramble_result is not None:
        if scramble_result + yardline > 100 :
                scramble_result = 100 - yardline
                qb.stats['touchdowns'] += round(scramble_result)
        else :
            tacklers = assign_tackles(defense, scramble_result)
            for player in tacklers :
                player.stats['tackles'] += 1
        qb.stats['carries'] += 1
        qb.stats['rush_yards'] += round(scramble_result)
        apply_run_fatigue(offense, defense, qb, scramble_result)
        return "run", scramble_result
    receiving_candidates = [
    p for p in offense if p.position in ('WR', 'TE', 'RB')
    ]
    weights = []
    for p in receiving_candidates:
        if p.position == 'RB':
            weights.append(1)  # fixed low weight
        else:
            weights.append((p.route_running + p.hands + p.intelligence) / 3)

    # Normalize RB weights to ~1% of total
    total_non_rb = sum(w for p, w in zip(receiving_candidates, weights) if p.position != 'RB')
    rb_count = sum(1 for p in receiving_candidates if p.position == 'RB')
    if rb_count > 0:
        rb_weight = (0.01 * total_non_rb) / rb_count
        weights = [
            rb_weight if p.position == 'RB' else w
            for p, w in zip(receiving_candidates, weights)
        ]

    # Select one target
    intended_target = random.choices(receiving_candidates, weights=weights, k=1)[0]
    qb.stats['pass_attempts'] += 1
    intended_target.stats['targets'] +=1
    apply_pass_fatigue(offense, defense)
    return "incomplete", 0