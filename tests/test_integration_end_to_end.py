import json
from unittest.mock import patch

import pytest

from src.embedding_service import EmbeddingService
from src.main import GymAssistantCLI
from src.models import Exercise, NutritionPlan, UserProfile
from src.nutrition_service import NutritionService
from src.storage import Storage
from src.workout_service import WorkoutService


class FakeClient:
    """Deterministic stand-in for OpenAI client used in integration tests."""

    def generate_completion(self, *, prompt: str, **kwargs) -> str:
        lower = prompt.lower()
        if "workout" in lower:
            return json.dumps(
                {
                    "title": "Integration Strength Session",
                    "duration_minutes": 45,
                    "exercises": [
                        {
                            "name": "Push-Up",
                            "muscle_groups": ["chest", "triceps"],
                            "equipment": [],
                            "difficulty": "beginner",
                            "sets": 3,
                            "reps": "12",
                            "rest_seconds": 60,
                            "instructions": "Keep core tight and lower chest to the floor.",
                            "safety_tips": "Avoid flaring elbows."
                        }
                    ],
                    "warmup": "Jumping jacks",
                    "cooldown": "Light stretching",
                    "target_muscles": ["chest"],
                    "calories_estimate": 320
                }
            )
        if "meal plan" in lower:
            return json.dumps(
                {
                    "date": "2025-01-01",
                    "meals": [
                        {
                            "name": "Chicken Bowl",
                            "meal_type": "lunch",
                            "calories": 500,
                            "protein_g": 45.0,
                            "carbs_g": 55.0,
                            "fats_g": 15.0,
                            "ingredients": ["chicken", "rice", "vegetables"],
                            "instructions": "Combine cooked chicken with rice and veggies.",
                            "prep_time_minutes": 20
                        }
                    ],
                    "notes": "Hydrate well throughout the day."
                }
            )
        raise AssertionError("FakeClient received unexpected prompt")

    def generate_embedding(self, text: str):
        tokens = text.lower()
        features = [
            1.0 if "chest" in tokens else 0.0,
            1.0 if "back" in tokens else 0.0,
            1.0 if "leg" in tokens else 0.0,
            1.0 if "cardio" in tokens else 0.0,
            1.0,
        ]
        return features


class FakeStorage(Storage):
    """In-memory storage stub for verifying persistence hooks."""

    def __init__(self):
        super().__init__(base_dir="/tmp", disabled=False)
        self.saved_profile = None
        self.history = {"workouts": [], "meal_plans": []}

    def save_user_profile(self, profile: UserProfile) -> None:
        self.saved_profile = profile

    def load_user_profile(self):
        return None

    def record_workout_summary(self, workout):
        self.history["workouts"].append(
            {"workout_id": workout.workout_id, "title": workout.title}
        )

    def record_meal_plan_summary(self, plan: NutritionPlan) -> None:
        self.history["meal_plans"].append(
            {"plan_id": plan.plan_id, "meal_names": [meal.name for meal in plan.meals]}
        )

    def get_history(self):
        return {"workouts": list(self.history["workouts"]), "meal_plans": list(self.history["meal_plans"])}


def build_user_profile() -> UserProfile:
    return UserProfile(
        user_id="integration_user",
        age=30,
        weight_kg=80.0,
        height_cm=180.0,
        gender="M",
        fitness_level="intermediate",
        goals=["build_muscle"],
        equipment_available=["mat"],
        injuries=[],
    )


@pytest.fixture
def fake_services():
    client = FakeClient()
    return {
        "workout": WorkoutService(client=client),
        "nutrition": NutritionService(client=client),
        "embedding": EmbeddingService(client=client),
    }


def test_cli_end_to_end_generates_and_persists(fake_services):
    user = build_user_profile()
    storage = FakeStorage()

    cli = GymAssistantCLI(
        user_profile=user,
        workout_service=fake_services["workout"],
        nutrition_service=fake_services["nutrition"],
        embedding_service=fake_services["embedding"],
        storage=storage,
    )

    with patch("builtins.input", side_effect=["strength", "45", ""]):
        workout = cli.generate_workout()
    with patch("builtins.input", side_effect=["none", "any", "medium"]):
        meal_plan = cli.generate_meal_plan()

    assert workout.title == "Integration Strength Session"
    assert meal_plan.total_calories == 500
    history = storage.get_history()
    assert history["workouts"][0]["title"] == workout.title
    assert meal_plan.plan_id == history["meal_plans"][0]["plan_id"]


def test_embedding_service_builds_and_queries(fake_services):
    exercises = [
        Exercise(
            name="Push-Up",
            muscle_groups=["chest"],
            equipment=[],
            difficulty="beginner",
            sets=3,
            reps="12",
            rest_seconds=60,
            instructions="Keep spine neutral.",
        ),
        Exercise(
            name="Bodyweight Squat",
            muscle_groups=["legs"],
            equipment=[],
            difficulty="beginner",
            sets=3,
            reps="15",
            rest_seconds=60,
            instructions="Sit back through heels.",
        ),
    ]

    embedding_service = fake_services["embedding"]
    embedding_service.build_database(exercises)

    results = embedding_service.find_similar_exercises("chest bodyweight move", top_k=1)

    assert results
    assert results[0][0] == "Push-Up"

    details = embedding_service.get_exercise_details("Push-Up")
    assert details is not None
    assert "chest" in details.metadata.get("muscle_groups", [])
