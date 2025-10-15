"""Shared default values and constants for the Gym Assistant project.

This module provides backward-compatible constants by importing from the
centralized config module. For new code, prefer importing from src.config
and using get_config() directly.
"""

from src.config import get_config

# Initialize config
_config = get_config()

# Export config values as module-level constants for backward compatibility
DEFAULT_DIFFICULTY_LEVELS = _config.default_difficulty_levels
DEFAULT_EXERCISE_DIFFICULTY = _config.default_exercise_difficulty
DEFAULT_EXERCISE_SETS = _config.default_exercise_sets
DEFAULT_EXERCISE_REPS = _config.default_exercise_reps
DEFAULT_EXERCISE_REST_SECONDS = _config.default_exercise_rest_seconds
DEFAULT_PLACEHOLDER_INSTRUCTIONS = _config.default_placeholder_instructions
DEFAULT_PLACEHOLDER_SAFETY = _config.default_placeholder_safety

DEFAULT_WORKOUT_TITLE = _config.default_workout_title
DEFAULT_WORKOUT_DURATION = _config.default_workout_duration
DEFAULT_WARMUP_TEXT = _config.default_warmup_text
DEFAULT_COOLDOWN_TEXT = _config.default_cooldown_text
DEFAULT_CALORIE_BASE_RATE = _config.default_calorie_base_rate

DEFAULT_MEAL_NAME = _config.default_meal_name
DEFAULT_MEAL_TYPE = _config.default_meal_type
DEFAULT_MEAL_PREP_TIME = _config.default_meal_prep_time
