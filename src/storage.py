"""Lightweight local storage for user profiles and plan history."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import get_config
from src.models import NutritionPlan, UserProfile, Workout


class Storage:
    """Persist user profile and plan history to a JSON file."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        filename: Optional[str] = None,
        disabled: Optional[bool] = None,
    ) -> None:
        config = get_config()
        
        self.disabled = disabled if disabled is not None else config.storage_disabled
        
        storage_dir = base_dir or config.storage_dir
        self.base_path = Path(storage_dir)
        self.state_path = self.base_path / (filename or config.storage_filename)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def save_user_profile(self, profile: UserProfile) -> None:
        if self.disabled:
            return
        state = self._load_state()
        state["user_profile"] = self._serialize_profile(profile)
        self._save_state(state)

    def load_user_profile(self) -> Optional[UserProfile]:
        if self.disabled:
            return None
        state = self._load_state()
        data = state.get("user_profile")
        if not data:
            return None
        return self._deserialize_profile(data)

    def record_workout_summary(self, workout: Workout) -> None:
        if self.disabled:
            return
        state = self._load_state()
        history = self._history_section(state)
        summary = self._summarize_workout(workout)
        history["workouts"] = self._prepend_and_trim(history["workouts"], summary)
        self._save_state(state)

    def record_meal_plan_summary(self, plan: NutritionPlan) -> None:
        if self.disabled:
            return
        state = self._load_state()
        history = self._history_section(state)
        summary = self._summarize_meal_plan(plan)
        history["meal_plans"] = self._prepend_and_trim(history["meal_plans"], summary)
        self._save_state(state)

    def get_history(self) -> Dict[str, List[Dict[str, Any]]]:
        if self.disabled:
            return {"workouts": [], "meal_plans": []}
        state = self._load_state()
        history = state.get("history", {})
        return {
            "workouts": list(history.get("workouts", [])),
            "meal_plans": list(history.get("meal_plans", [])),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                with self.state_path.open("r", encoding="utf-8") as fp:
                    return json.load(fp)
            except (json.JSONDecodeError, OSError):
                pass
        return {"user_profile": None, "history": {"workouts": [], "meal_plans": []}}

    def _save_state(self, state: Dict[str, Any]) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as fp:
            json.dump(state, fp, indent=2)

    @staticmethod
    def _history_section(state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        history = state.setdefault("history", {})
        history.setdefault("workouts", [])
        history.setdefault("meal_plans", [])
        return history

    @staticmethod
    def _serialize_profile(profile: UserProfile) -> Dict[str, Any]:
        data = asdict(profile)
        # Dataclass asdict returns lists already; ensure Optional None remains None
        return data

    @staticmethod
    def _deserialize_profile(data: Dict[str, Any]) -> UserProfile:
        injuries_data = data.get("injuries")
        equipment_data = data.get("equipment_available")
        return UserProfile(
            user_id=data["user_id"],
            age=int(data["age"]),
            weight_kg=float(data["weight_kg"]),
            height_cm=float(data["height_cm"]),
            gender=data["gender"],
            fitness_level=data["fitness_level"],
            goals=list(data.get("goals", [])),
            injuries=list(injuries_data) if isinstance(injuries_data, list) else injuries_data,
            equipment_available=list(equipment_data) if isinstance(equipment_data, list) else equipment_data,
        )

    @staticmethod
    def _summarize_workout(workout: Workout) -> Dict[str, Any]:
        created_at = workout.created_at.isoformat()
        return {
            "workout_id": workout.workout_id,
            "title": workout.title,
            "duration_minutes": workout.duration_minutes,
            "calories_estimate": workout.calories_estimate,
            "target_muscles": workout.target_muscles,
            "created_at": created_at,
        }

    @staticmethod
    def _summarize_meal_plan(plan: NutritionPlan) -> Dict[str, Any]:
        return {
            "plan_id": plan.plan_id,
            "date": plan.date,
            "total_calories": plan.total_calories,
            "meal_names": [meal.name for meal in plan.meals],
        }

    @staticmethod
    def _prepend_and_trim(entries: List[Dict[str, Any]], new_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        config = get_config()
        new_key = new_entry.get("workout_id") or new_entry.get("plan_id")

        def entry_key(entry: Dict[str, Any]) -> Optional[Any]:
            return entry.get("workout_id") or entry.get("plan_id")

        filtered = [entry for entry in entries if entry_key(entry) != new_key]
        filtered.insert(0, new_entry)
        return filtered[:config.storage_history_limit]
