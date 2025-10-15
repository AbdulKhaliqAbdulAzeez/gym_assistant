import json
from pathlib import Path

import pytest

from src.config import get_config
from src.models import Exercise, Meal, NutritionPlan, UserProfile, Workout
from src.storage import Storage


def build_user_profile(user_id: str = "user_1") -> UserProfile:
    return UserProfile(
        user_id=user_id,
        age=30,
        weight_kg=80.0,
        height_cm=180.0,
        gender="M",
        fitness_level="intermediate",
        goals=["build_muscle"],
        equipment_available=["dumbbells"],
        injuries=[],
    )


def build_workout(workout_id: str) -> Workout:
    exercise = Exercise(
        name="Push-Up",
        muscle_groups=["chest"],
        equipment=[],
        difficulty="beginner",
        sets=3,
        reps="12",
        rest_seconds=60,
        instructions="Keep core engaged",
    )
    return Workout(
        workout_id=workout_id,
        title="Bodyweight Session",
        duration_minutes=30,
        exercises=[exercise],
        warmup="Light jogging",
        cooldown="Stretch",
        difficulty="beginner",
        target_muscles=["chest"],
        calories_estimate=200,
    )


def build_meal_plan(plan_id: str) -> NutritionPlan:
    meal = Meal(
        name="Oatmeal",
        meal_type="breakfast",
        calories=350,
        protein_g=15.0,
        carbs_g=55.0,
        fats_g=10.0,
        ingredients=["oats", "milk"],
        instructions="Cook oats with milk",
        prep_time_minutes=10,
    )
    return NutritionPlan(
        plan_id=plan_id,
        date="2025-01-01",
        meals=[meal],
        total_calories=350,
        total_protein_g=15.0,
        total_carbs_g=55.0,
        total_fats_g=10.0,
    )


class TestStoragePersistence:
    def test_save_and_load_profile(self, tmp_path: Path):
        storage = Storage(base_dir=str(tmp_path), disabled=False)
        profile = build_user_profile()

        storage.save_user_profile(profile)
        loaded = storage.load_user_profile()

        assert loaded == profile

    def test_disabled_storage_noop(self, tmp_path: Path):
        storage = Storage(base_dir=str(tmp_path), disabled=True)
        profile = build_user_profile()
        storage.save_user_profile(profile)

        assert storage.load_user_profile() is None
        assert not (tmp_path / "state.json").exists()


class TestStorageHistory:
    def test_record_workout_summary(self, tmp_path: Path):
        storage = Storage(base_dir=str(tmp_path), disabled=False)
        workout = build_workout("workout_1")

        storage.record_workout_summary(workout)
        history = storage.get_history()

        assert history["workouts"]
        entry = history["workouts"][0]
        assert entry["workout_id"] == "workout_1"
        assert entry["title"] == "Bodyweight Session"

    def test_history_trim_limit(self, tmp_path: Path):
        config = get_config()
        history_limit = config.storage_history_limit
        
        storage = Storage(base_dir=str(tmp_path), disabled=False)
        for idx in range(history_limit + 5):
            storage.record_workout_summary(build_workout(f"w_{idx}"))

        history = storage.get_history()
        assert len(history["workouts"]) == history_limit
        assert history["workouts"][0]["workout_id"] == f"w_{history_limit + 4}"

    def test_record_meal_plan_summary(self, tmp_path: Path):
        storage = Storage(base_dir=str(tmp_path), disabled=False)
        plan = build_meal_plan("plan_1")

        storage.record_meal_plan_summary(plan)
        history = storage.get_history()

        assert history["meal_plans"]
        entry = history["meal_plans"][0]
        assert entry["plan_id"] == "plan_1"
        assert "Oatmeal" in entry["meal_names"]

    def test_history_file_is_json_serializable(self, tmp_path: Path):
        storage = Storage(base_dir=str(tmp_path), disabled=False)
        storage.save_user_profile(build_user_profile())
        storage.record_workout_summary(build_workout("w_json"))
        storage.record_meal_plan_summary(build_meal_plan("plan_json"))

        state_path = Path(tmp_path) / "state.json"
        with state_path.open("r", encoding="utf-8") as fp:
            loaded = json.load(fp)

        assert "user_profile" in loaded
        assert "history" in loaded
