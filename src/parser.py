"""Parser utilities for transforming AI responses into typed models."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from src.defaults import (
    DEFAULT_CALORIE_BASE_RATE,
    DEFAULT_COOLDOWN_TEXT,
    DEFAULT_DIFFICULTY_LEVELS,
    DEFAULT_EXERCISE_DIFFICULTY,
    DEFAULT_EXERCISE_REPS,
    DEFAULT_EXERCISE_REST_SECONDS,
    DEFAULT_EXERCISE_SETS,
    DEFAULT_MEAL_NAME,
    DEFAULT_MEAL_PREP_TIME,
    DEFAULT_MEAL_TYPE,
    DEFAULT_PLACEHOLDER_SAFETY,
    DEFAULT_WARMUP_TEXT,
    DEFAULT_WORKOUT_DURATION,
    DEFAULT_WORKOUT_TITLE,
)
from src.models import Exercise, Meal, NutritionPlan, Workout, GymAssistantError


class ParserError(GymAssistantError):
    """Raised when parsing AI output fails."""

    def __init__(self, message: str):
        super().__init__(message, "parser_error")


class ExerciseParser:
    """Convert exercise dictionaries into model instances."""

    DIFFICULTY_LEVELS = DEFAULT_DIFFICULTY_LEVELS

    @staticmethod
    def parse(data: Dict[str, Any]) -> Exercise:
        if data is None:
            raise ParserError("Cannot parse None as exercise")
        if not isinstance(data, dict):
            raise ParserError(f"Expected dict, got {type(data)}")
        if not data:
            raise ParserError("Cannot parse empty dictionary as exercise")

        try:
            name = ExerciseParser._get_string(data, "name", required=True)

            raw_muscles = data.get("muscle_groups", [])
            if isinstance(raw_muscles, str):
                raw_muscles = [raw_muscles]
            muscle_groups = [muscle.strip() for muscle in raw_muscles if muscle]

            equipment = data.get("equipment", [])
            if not isinstance(equipment, list):
                equipment = []
            equipment = [item.strip() for item in equipment if item]

            difficulty = ExerciseParser._validate_difficulty(
                data.get("difficulty", DEFAULT_EXERCISE_DIFFICULTY)
            )

            sets = ExerciseParser._validate_sets(data.get("sets", DEFAULT_EXERCISE_SETS))
            reps = str(data.get("reps", DEFAULT_EXERCISE_REPS)).strip() or DEFAULT_EXERCISE_REPS
            rest_seconds = ExerciseParser._validate_rest(
                data.get("rest_seconds", DEFAULT_EXERCISE_REST_SECONDS)
            )

            instructions = ExerciseParser._get_string(data, "instructions", required=True)
            safety_tips = ExerciseParser._get_string(data, "safety_tips") or DEFAULT_PLACEHOLDER_SAFETY

            return Exercise(
                name=name,
                muscle_groups=muscle_groups,
                equipment=equipment,
                difficulty=difficulty,
                sets=sets,
                reps=reps,
                rest_seconds=rest_seconds,
                instructions=instructions,
                safety_tips=safety_tips,
            )

        except KeyError as exc:
            raise ParserError(f"Missing required field: {exc}") from exc
        except Exception as exc:
            raise ParserError(f"Error parsing exercise: {exc}") from exc

    @staticmethod
    def _get_string(data: Dict[str, Any], key: str, required: bool = False) -> str:
        value = data.get(key)
        if required and not value:
            raise ParserError(f"Required field '{key}' is missing or empty")
        return str(value).strip() if value is not None else ""

    @classmethod
    def _validate_difficulty(cls, raw: Any) -> str:
        normalized = str(raw).strip().lower() if raw else ""
        if normalized not in cls.DIFFICULTY_LEVELS:
            return DEFAULT_EXERCISE_DIFFICULTY
        return normalized

    @staticmethod
    def _validate_sets(raw_sets: Any) -> int:
        try:
            sets = int(raw_sets)
        except (TypeError, ValueError):
            return DEFAULT_EXERCISE_SETS
        if sets < 1:
            return 1
        if sets > 10:
            return 10
        return sets

    @staticmethod
    def _validate_rest(raw_rest: Any) -> int:
        try:
            rest = int(raw_rest)
        except (TypeError, ValueError):
            return DEFAULT_EXERCISE_REST_SECONDS
        return max(0, rest)


class WorkoutParser:
    """Convert workout dictionaries into Workout models."""

    @staticmethod
    def parse(data: Dict[str, Any]) -> Workout:
        if data is None or not isinstance(data, dict):
            raise ParserError("Invalid workout data")

        try:
            title = data.get("title", DEFAULT_WORKOUT_TITLE).strip() or DEFAULT_WORKOUT_TITLE
            duration_minutes = int(data.get("duration_minutes", DEFAULT_WORKOUT_DURATION))

            exercises_data = data.get("exercises", [])
            if not exercises_data:
                raise ParserError("Workout must contain at least one exercise")

            exercises = [ExerciseParser.parse(ex_data) for ex_data in exercises_data]

            warmup = data.get("warmup", DEFAULT_WARMUP_TEXT).strip() or DEFAULT_WARMUP_TEXT
            cooldown = data.get("cooldown", DEFAULT_COOLDOWN_TEXT).strip() or DEFAULT_COOLDOWN_TEXT

            target_muscles = data.get("target_muscles", [])
            if not target_muscles:
                target_muscles = WorkoutParser._infer_target_muscles(exercises)

            calories_estimate = data.get("calories_estimate")
            if not calories_estimate:
                calories_estimate = WorkoutParser._estimate_calories(duration_minutes, exercises)

            difficulty = WorkoutParser._infer_difficulty(exercises)
            workout_id = f"workout_{uuid.uuid4().hex[:8]}"

            return Workout(
                workout_id=workout_id,
                title=title,
                duration_minutes=duration_minutes,
                exercises=exercises,
                warmup=warmup,
                cooldown=cooldown,
                difficulty=difficulty,
                target_muscles=target_muscles,
                calories_estimate=calories_estimate,
            )

        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(f"Error parsing workout: {exc}") from exc

    @staticmethod
    def parse_from_string(json_string: str) -> Workout:
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as exc:
            raise ParserError(f"Invalid JSON: {exc}") from exc
        return WorkoutParser.parse(data)

    @staticmethod
    def _infer_target_muscles(exercises: List[Exercise]) -> List[str]:
        muscles: List[str] = []
        for exercise in exercises:
            for muscle in exercise.muscle_groups:
                if muscle and muscle not in muscles:
                    muscles.append(muscle)
        return muscles

    @staticmethod
    def _estimate_calories(duration: int, exercises: List[Exercise]) -> int:
        base_rate = DEFAULT_CALORIE_BASE_RATE
        multiplier = 1.0
        for exercise in exercises:
            if exercise.difficulty == "advanced":
                multiplier = max(multiplier, 1.3)
            elif exercise.difficulty == "intermediate":
                multiplier = max(multiplier, 1.1)
        return int(duration * base_rate * multiplier)

    @staticmethod
    def _infer_difficulty(exercises: List[Exercise]) -> str:
        if not exercises:
            return "beginner"
        level_map = {"beginner": 1, "intermediate": 2, "advanced": 3}
        highest = max(level_map.get(ex.difficulty, 1) for ex in exercises)
        for label, level in level_map.items():
            if level == highest:
                return label
        return "beginner"


class NutritionParser:
    """Convert nutrition dictionaries into NutritionPlan models."""

    @staticmethod
    def parse_meal(data: Dict[str, Any]) -> Meal:
        if data is None or not isinstance(data, dict):
            raise ParserError("Invalid meal data")

        try:
            name = data.get("name", DEFAULT_MEAL_NAME).strip() or DEFAULT_MEAL_NAME
            meal_type = data.get("meal_type", DEFAULT_MEAL_TYPE).lower().strip() or DEFAULT_MEAL_TYPE

            calories = int(data.get("calories", 0))
            protein_g = max(0.0, float(data.get("protein_g", 0)))
            carbs_g = max(0.0, float(data.get("carbs_g", 0)))
            fats_g = max(0.0, float(data.get("fats_g", 0)))

            ingredients = data.get("ingredients", [])
            if not isinstance(ingredients, list):
                ingredients = []
            instructions = data.get("instructions", "").strip()
            prep_time_minutes = int(data.get("prep_time_minutes", DEFAULT_MEAL_PREP_TIME))

            return Meal(
                name=name,
                meal_type=meal_type,
                calories=calories,
                protein_g=protein_g,
                carbs_g=carbs_g,
                fats_g=fats_g,
                ingredients=ingredients,
                instructions=instructions,
                prep_time_minutes=prep_time_minutes,
            )

        except Exception as exc:
            raise ParserError(f"Error parsing meal: {exc}") from exc

    @staticmethod
    def parse_plan(data: Dict[str, Any]) -> NutritionPlan:
        if data is None or not isinstance(data, dict):
            raise ParserError("Invalid nutrition plan data")

        try:
            date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

            meals_data = data.get("meals", [])
            meals = [NutritionParser.parse_meal(meal_data) for meal_data in meals_data]

            total_calories = sum(meal.calories for meal in meals)
            total_protein_g = sum(meal.protein_g for meal in meals)
            total_carbs_g = sum(meal.carbs_g for meal in meals)
            total_fats_g = sum(meal.fats_g for meal in meals)

            notes = data.get("notes")
            plan_id = f"plan_{uuid.uuid4().hex[:8]}"

            return NutritionPlan(
                plan_id=plan_id,
                date=date,
                meals=meals,
                total_calories=total_calories,
                total_protein_g=total_protein_g,
                total_carbs_g=total_carbs_g,
                total_fats_g=total_fats_g,
                notes=notes,
            )

        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(f"Error parsing nutrition plan: {exc}") from exc

    @staticmethod
    def parse_plan_from_string(json_string: str) -> NutritionPlan:
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as exc:
            raise ParserError(f"Invalid JSON: {exc}") from exc
        return NutritionParser.parse_plan(data)
