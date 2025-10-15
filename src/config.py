"""Centralized configuration management for the Gym Assistant.

This module provides a singleton configuration object that consolidates all
environment variables, default values, and settings into a single, testable,
and maintainable location.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _is_true(value: str) -> bool:
    """Helper to parse boolean environment variables."""
    return value.lower() in {"1", "true", "yes", "on"}


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean value from environment variable."""
    value = os.getenv(key, str(default).lower())
    return _is_true(value)


@dataclass
class Config:
    """Centralized configuration for the Gym Assistant application.
    
    All settings can be overridden via environment variables following the
    naming pattern: GYM_ASSISTANT_<SETTING_NAME>
    """
    
    # -------------------------------------------------------------------------
    # OpenAI API Settings
    # -------------------------------------------------------------------------
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    openai_default_model: str = field(
        default_factory=lambda: os.getenv("GYM_ASSISTANT_MODEL", "gpt-4o")
    )
    openai_embedding_model: str = field(
        default_factory=lambda: os.getenv("GYM_ASSISTANT_EMBEDDING_MODEL", "text-embedding-3-large")
    )
    openai_max_retries: int = field(
        default_factory=lambda: int(os.getenv("GYM_ASSISTANT_MAX_RETRIES", "3"))
    )
    
    # -------------------------------------------------------------------------
    # Logging Settings
    # -------------------------------------------------------------------------
    logging_disabled: bool = field(
        default_factory=lambda: _get_env_bool("GYM_ASSISTANT_DISABLE_LOGGING", False)
    )
    logging_level: str = field(
        default_factory=lambda: os.getenv("GYM_ASSISTANT_LOG_LEVEL", "INFO")
    )
    logging_dir: str = field(
        default_factory=lambda: os.getenv("GYM_ASSISTANT_LOG_DIR", "logs")
    )
    logging_to_console: bool = field(
        default_factory=lambda: _get_env_bool("GYM_ASSISTANT_LOG_CONSOLE", True)
    )
    logging_to_file: bool = field(
        default_factory=lambda: _get_env_bool("GYM_ASSISTANT_LOG_FILE", True)
    )
    
    # -------------------------------------------------------------------------
    # Storage Settings
    # -------------------------------------------------------------------------
    storage_disabled: bool = field(
        default_factory=lambda: _get_env_bool("GYM_ASSISTANT_DISABLE_STORAGE", False)
    )
    storage_dir: str = field(
        default_factory=lambda: os.getenv(
            "GYM_ASSISTANT_STORAGE_DIR",
            str(Path.home() / ".gym_assistant")
        )
    )
    storage_filename: str = field(
        default_factory=lambda: os.getenv("GYM_ASSISTANT_STORAGE_FILE", "state.json")
    )
    storage_history_limit: int = field(
        default_factory=lambda: int(os.getenv("GYM_ASSISTANT_HISTORY_LIMIT", "20"))
    )
    
    # -------------------------------------------------------------------------
    # Parser Defaults
    # -------------------------------------------------------------------------
    default_difficulty_levels: tuple[str, ...] = ("beginner", "intermediate", "advanced")
    default_exercise_difficulty: str = "intermediate"
    default_exercise_sets: int = 3
    default_exercise_reps: str = "10"
    default_exercise_rest_seconds: int = 60
    default_workout_duration: int = 30
    default_meal_prep_time: int = 15
    
    # Placeholder text
    default_placeholder_instructions: str = "Instructions not available."
    default_placeholder_safety: Optional[str] = None
    default_workout_title: str = "Workout"
    default_warmup_text: str = "5 minutes of light cardio"
    default_cooldown_text: str = "5 minutes of stretching"
    default_meal_name: str = "Meal"
    default_meal_type: str = "meal"
    
    # Calculation constants
    default_calorie_base_rate: int = 7
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate logging level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging_level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {self.logging_level}. "
                f"Must be one of {valid_levels}"
            )
        
        # Validate history limit
        if self.storage_history_limit < 1:
            raise ValueError(
                f"Storage history limit must be at least 1, got {self.storage_history_limit}"
            )
        
        # Validate difficulty levels
        if not self.default_difficulty_levels:
            raise ValueError("Difficulty levels cannot be empty")
        
        if self.default_exercise_difficulty not in self.default_difficulty_levels:
            raise ValueError(
                f"Default exercise difficulty '{self.default_exercise_difficulty}' "
                f"not in difficulty levels {self.default_difficulty_levels}"
            )
    
    @classmethod
    def from_env(cls) -> Config:
        """Create a Config instance by reading all values from environment variables.
        
        This is the recommended way to create a Config object as it ensures
        all environment variables are read at instantiation time.
        """
        return cls()
    
    def reload(self) -> None:
        """Reload configuration from environment variables.
        
        This re-reads all environment variables and updates the config.
        Useful for testing or when environment changes at runtime.
        """
        new_config = Config.from_env()
        for key, value in new_config.__dict__.items():
            setattr(self, key, value)


# Global singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Creates the config on first call. Subsequent calls return the cached instance.
    Use Config.from_env() if you need a fresh instance for testing.
    
    Returns:
        The global Config instance.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance.
    
    This is primarily useful for testing to ensure a clean state between tests.
    """
    global _config
    _config = None


def set_config(config: Config) -> None:
    """Set the global configuration instance.
    
    This is primarily useful for testing to inject a custom config.
    
    Args:
        config: The Config instance to use as the global config.
    """
    global _config
    _config = config
