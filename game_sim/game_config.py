"""
Game Configuration - Slider System
Similar to EA Sports College Football sliders
All values range from 0-100, where 50 = default/normal
Adjusting above 50 increases that attribute, below 50 decreases it
"""

class GameSliders:
    """Centralized slider configuration for game parameters"""
    
    def __init__(self):
        # ========== OFFENSE SLIDERS ==========
        self.qb_accuracy = 50          # QB passing accuracy (affects completion %)
        self.wr_catching = 50          # WR/TE catching ability
        self.pass_blocking = 50        # Offensive line pass protection
        self.run_blocking = 50         # Offensive line run blocking
        self.running_ability = 50      # RB rushing effectiveness
        self.fumble_frequency = 50     # Offensive fumble rate (lower = fewer fumbles)
        self.offensive_penalties = 50  # Offensive penalty frequency (lower = fewer penalties)
        
        # ========== DEFENSE SLIDERS ==========
        self.pass_defense = 50         # Pass coverage effectiveness
        self.interceptions = 50        # Interception frequency
        self.pass_rush = 50            # Defensive pass rush / sack rate
        self.run_defense = 50          # Run defense effectiveness
        self.tackling = 50             # Tackling ability
        self.defensive_penalties = 50  # Defensive penalty frequency (lower = fewer penalties)
        self.forced_fumbles = 50       # Forced fumble frequency
        
        # ========== SPECIAL TEAMS SLIDERS ==========
        self.kicking_power = 50        # Kicker/punter power
        self.kicking_accuracy = 50     # Kicker accuracy (PATs, FGs)
        self.punt_accuracy = 50        # Punter accuracy (pinning, distance)
        self.kickoff_power = 50        # Kickoff distance
        self.kickoff_return = 50       # Kickoff return effectiveness
        
        # ========== GAME PLAY SLIDERS ==========
        self.game_speed = 50           # Overall game tempo (affects time per play)
        self.injury_frequency = 50     # Injury frequency (not yet implemented)
        self.home_field_advantage = 50 # Home field advantage (not yet implemented)
        
    def get_multiplier(self, slider_value):
        """
        Convert slider value (0-100) to multiplier
        50 = 1.0 (normal)
        0 = 0.5 (50% of normal)
        100 = 1.5 (150% of normal)
        """
        return 0.5 + (slider_value / 100)
    
    def get_percentage_adjustment(self, slider_value, base_percentage):
        """
        Adjust a percentage based on slider
        50 = base percentage
        0 = base * 0.5
        100 = base * 1.5
        """
        multiplier = self.get_multiplier(slider_value)
        return base_percentage * multiplier
    
    def get_inverse_percentage_adjustment(self, slider_value, base_percentage):
        """
        For sliders where lower = better (like fumbles, penalties)
        50 = base percentage
        0 = base * 1.5 (more frequent)
        100 = base * 0.5 (less frequent)
        """
        multiplier = 1.5 - (slider_value / 100)
        return base_percentage * multiplier


# Global slider instance - can be modified before running simulation
sliders = GameSliders()

