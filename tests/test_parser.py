"""
Test suite for AI response parser (TDD RED phase first).
Parser transforms AI JSON/text responses into typed data models.
"""

import pytest
import json
from datetime import datetime
from src.parser import (
    WorkoutParser,
    NutritionParser,
    ExerciseParser,
    ParserError
)
from src.models import (
    Workout,
    Exercise,
    Meal,
    NutritionPlan,
    GymAssistantError
)


class TestExerciseParser:
    """Test parsing individual exercises from JSON"""
    
    def test_parse_exercise_complete_data(self):
        """Test parsing exercise with all fields present"""
        exercise_json = {
            "name": "Dumbbell Bench Press",
            "muscle_groups": ["chest", "triceps", "shoulders"],
            "equipment": ["dumbbells", "bench"],
            "difficulty": "intermediate",
            "sets": 4,
            "reps": "8-10",
            "rest_seconds": 90,
            "instructions": "Lie on bench, press dumbbells up from chest level",
            "safety_tips": "Keep back flat on bench, don't lock elbows"
        }
        
        exercise = ExerciseParser.parse(exercise_json)
        
        assert exercise.name == "Dumbbell Bench Press"
        assert exercise.muscle_groups == ["chest", "triceps", "shoulders"]
        assert exercise.equipment == ["dumbbells", "bench"]
        assert exercise.difficulty == "intermediate"
        assert exercise.sets == 4
        assert exercise.reps == "8-10"
        assert exercise.rest_seconds == 90
        assert "Lie on bench" in exercise.instructions
        assert exercise.safety_tips is not None
    
    def test_parse_exercise_missing_optional_fields(self):
        """Test parser provides defaults for missing optional fields"""
        exercise_json = {
            "name": "Push-ups",
            "muscle_groups": ["chest"],
            "equipment": [],
            "difficulty": "beginner",
            "sets": 3,
            "reps": "12-15",
            "rest_seconds": 60,
            "instructions": "Standard push-up form"
        }
        
        exercise = ExerciseParser.parse(exercise_json)
        
        assert exercise.name == "Push-ups"
        assert exercise.safety_tips is None
    
    def test_parse_exercise_missing_required_fields(self):
        """Test parser raises error when required fields missing"""
        exercise_json = {
            "name": "Squats",
            "muscle_groups": ["legs"]
            # Missing required fields
        }
        
        with pytest.raises(ParserError) as exc_info:
            ExerciseParser.parse(exercise_json)
        
        assert "required field" in str(exc_info.value).lower()
    
    def test_parse_exercise_validates_sets_range(self):
        """Test parser validates sets in reasonable range"""
        exercise_json = {
            "name": "Test Exercise",
            "muscle_groups": ["chest"],
            "equipment": [],
            "difficulty": "beginner",
            "sets": 100,  # Unreasonable
            "reps": "10",
            "rest_seconds": 60,
            "instructions": "Test"
        }
        
        # Parser should either clamp to max or raise error
        result = ExerciseParser.parse(exercise_json)
        assert result.sets <= 10  # Should be clamped to reasonable max
    
    def test_parse_exercise_validates_rest_time(self):
        """Test parser validates rest time"""
        exercise_json = {
            "name": "Test Exercise",
            "muscle_groups": ["chest"],
            "equipment": [],
            "difficulty": "beginner",
            "sets": 3,
            "reps": "10",
            "rest_seconds": -10,  # Invalid
            "instructions": "Test"
        }
        
        result = ExerciseParser.parse(exercise_json)
        assert result.rest_seconds >= 0  # Should be non-negative
    
    def test_parse_exercise_handles_empty_equipment(self):
        """Test parser handles bodyweight exercises (no equipment)"""
        exercise_json = {
            "name": "Plank",
            "muscle_groups": ["core"],
            "equipment": [],
            "difficulty": "intermediate",
            "sets": 3,
            "reps": "60 seconds",
            "rest_seconds": 30,
            "instructions": "Hold plank position"
        }
        
        exercise = ExerciseParser.parse(exercise_json)
        assert exercise.equipment == []


class TestWorkoutParser:
    """Test parsing complete workouts from JSON"""
    
    def test_parse_workout_from_json(self):
        """Test parsing AI JSON response into Workout object"""
        workout_json = {
            "title": "Upper Body Strength",
            "duration_minutes": 45,
            "exercises": [
                {
                    "name": "Push-ups",
                    "muscle_groups": ["chest", "triceps"],
                    "equipment": [],
                    "difficulty": "beginner",
                    "sets": 3,
                    "reps": "12-15",
                    "rest_seconds": 60,
                    "instructions": "Standard push-up form"
                },
                {
                    "name": "Dumbbell Rows",
                    "muscle_groups": ["back", "biceps"],
                    "equipment": ["dumbbells"],
                    "difficulty": "intermediate",
                    "sets": 4,
                    "reps": "8-10",
                    "rest_seconds": 90,
                    "instructions": "Pull dumbbell to hip"
                }
            ],
            "warmup": "5 minutes of light cardio",
            "cooldown": "5 minutes of stretching",
            "target_muscles": ["chest", "back", "arms"],
            "calories_estimate": 350
        }
        
        workout = WorkoutParser.parse(workout_json)
        
        assert workout.title == "Upper Body Strength"
        assert workout.duration_minutes == 45
        assert len(workout.exercises) == 2
        assert workout.exercises[0].name == "Push-ups"
        assert workout.exercises[1].name == "Dumbbell Rows"
        assert workout.warmup == "5 minutes of light cardio"
        assert workout.cooldown == "5 minutes of stretching"
        assert workout.target_muscles == ["chest", "back", "arms"]
        assert workout.calories_estimate == 350
        assert workout.difficulty == "intermediate"  # Should infer from exercises (highest level)
    
    def test_parse_workout_from_json_string(self):
        """Test parsing workout from JSON string (as from API)"""
        workout_json_str = json.dumps({
            "title": "Quick Cardio",
            "duration_minutes": 20,
            "exercises": [
                {
                    "name": "Jumping Jacks",
                    "muscle_groups": ["cardio"],
                    "equipment": [],
                    "difficulty": "beginner",
                    "sets": 3,
                    "reps": "30 seconds",
                    "rest_seconds": 30,
                    "instructions": "Jump with arms and legs spread"
                }
            ],
            "warmup": "2 minutes light jog",
            "cooldown": "3 minutes walking",
            "target_muscles": ["cardio"],
            "calories_estimate": 150
        })
        
        workout = WorkoutParser.parse_from_string(workout_json_str)
        
        assert workout.title == "Quick Cardio"
        assert workout.duration_minutes == 20
        assert len(workout.exercises) == 1
    
    def test_parse_workout_handles_missing_fields(self):
        """Test parser provides defaults for missing optional fields"""
        workout_json = {
            "title": "Basic Workout",
            "duration_minutes": 30,
            "exercises": [
                {
                    "name": "Squats",
                    "muscle_groups": ["legs"],
                    "equipment": [],
                    "difficulty": "beginner",
                    "sets": 3,
                    "reps": "15",
                    "rest_seconds": 60,
                    "instructions": "Standard squat"
                }
            ],
            "warmup": "5 min warmup",
            "cooldown": "5 min cooldown"
            # Missing target_muscles and calories_estimate
        }
        
        workout = WorkoutParser.parse(workout_json)
        
        assert workout.title == "Basic Workout"
        assert workout.target_muscles == ["legs"]  # Should infer from exercises
        assert workout.calories_estimate > 0  # Should provide reasonable default
    
    def test_parse_workout_infers_difficulty(self):
        """Test parser infers workout difficulty from exercises"""
        workout_json = {
            "title": "Mixed Workout",
            "duration_minutes": 40,
            "exercises": [
                {
                    "name": "Exercise 1",
                    "muscle_groups": ["chest"],
                    "equipment": [],
                    "difficulty": "advanced",
                    "sets": 4,
                    "reps": "6-8",
                    "rest_seconds": 120,
                    "instructions": "Test"
                },
                {
                    "name": "Exercise 2",
                    "muscle_groups": ["back"],
                    "equipment": [],
                    "difficulty": "intermediate",
                    "sets": 3,
                    "reps": "10",
                    "rest_seconds": 60,
                    "instructions": "Test"
                }
            ],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        }
        
        workout = WorkoutParser.parse(workout_json)
        
        # Should pick the highest difficulty level
        assert workout.difficulty in ["intermediate", "advanced"]
    
    def test_parse_workout_invalid_json(self):
        """Test parser handles malformed JSON gracefully"""
        invalid_json = "{ this is not valid json }"
        
        with pytest.raises(ParserError) as exc_info:
            WorkoutParser.parse_from_string(invalid_json)
        
        assert "json" in str(exc_info.value).lower()


class TestNutritionParser:
    """Test parsing meal plans from JSON"""
    
    def test_parse_meal_from_json(self):
        """Test parsing individual meal"""
        meal_json = {
            "name": "Grilled Chicken with Rice",
            "meal_type": "lunch",
            "calories": 450,
            "protein_g": 40.0,
            "carbs_g": 50.0,
            "fats_g": 10.0,
            "ingredients": ["chicken breast", "brown rice", "broccoli", "olive oil"],
            "instructions": "Grill chicken, cook rice, steam broccoli",
            "prep_time_minutes": 25
        }
        
        meal = NutritionParser.parse_meal(meal_json)
        
        assert meal.name == "Grilled Chicken with Rice"
        assert meal.meal_type == "lunch"
        assert meal.calories == 450
        assert meal.protein_g == 40.0
        assert meal.carbs_g == 50.0
        assert meal.fats_g == 10.0
        assert len(meal.ingredients) == 4
        assert meal.prep_time_minutes == 25
    
    def test_parse_nutrition_plan(self):
        """Test parsing complete nutrition plan"""
        plan_json = {
            "date": "2025-10-14",
            "meals": [
                {
                    "name": "Breakfast",
                    "meal_type": "breakfast",
                    "calories": 400,
                    "protein_g": 25.0,
                    "carbs_g": 45.0,
                    "fats_g": 12.0,
                    "ingredients": ["eggs", "oatmeal"],
                    "instructions": "Cook eggs, prepare oatmeal",
                    "prep_time_minutes": 15
                },
                {
                    "name": "Lunch",
                    "meal_type": "lunch",
                    "calories": 550,
                    "protein_g": 40.0,
                    "carbs_g": 60.0,
                    "fats_g": 15.0,
                    "ingredients": ["chicken", "rice"],
                    "instructions": "Grill chicken, cook rice",
                    "prep_time_minutes": 30
                }
            ],
            "notes": "High protein for muscle building"
        }
        
        plan = NutritionParser.parse_plan(plan_json)
        
        assert plan.date == "2025-10-14"
        assert len(plan.meals) == 2
        assert plan.total_calories == 950  # 400 + 550
        assert plan.total_protein_g == 65.0  # 25 + 40
        assert plan.total_carbs_g == 105.0  # 45 + 60
        assert plan.total_fats_g == 27.0  # 12 + 15
        assert plan.notes == "High protein for muscle building"
    
    def test_parse_nutrition_plan_calculates_totals(self):
        """Test parser automatically calculates macro totals"""
        plan_json = {
            "date": "2025-10-14",
            "meals": [
                {
                    "name": "Meal 1",
                    "meal_type": "breakfast",
                    "calories": 300,
                    "protein_g": 20.0,
                    "carbs_g": 30.0,
                    "fats_g": 10.0,
                    "ingredients": ["food"],
                    "instructions": "Cook",
                    "prep_time_minutes": 10
                },
                {
                    "name": "Meal 2",
                    "meal_type": "lunch",
                    "calories": 500,
                    "protein_g": 35.0,
                    "carbs_g": 50.0,
                    "fats_g": 15.0,
                    "ingredients": ["food"],
                    "instructions": "Cook",
                    "prep_time_minutes": 20
                }
            ]
        }
        
        plan = NutritionParser.parse_plan(plan_json)
        
        # Parser should calculate totals even if not provided in JSON
        assert plan.total_calories == 800
        assert plan.total_protein_g == 55.0
        assert plan.total_carbs_g == 80.0
        assert plan.total_fats_g == 25.0
    
    def test_parse_meal_validates_macros(self):
        """Test parser validates macro nutrients are positive"""
        meal_json = {
            "name": "Test Meal",
            "meal_type": "dinner",
            "calories": 500,
            "protein_g": -10.0,  # Invalid
            "carbs_g": 50.0,
            "fats_g": 15.0,
            "ingredients": ["food"],
            "instructions": "Cook",
            "prep_time_minutes": 20
        }
        
        meal = NutritionParser.parse_meal(meal_json)
        assert meal.protein_g >= 0  # Should be corrected to 0 or positive
    
    def test_parse_nutrition_plan_from_string(self):
        """Test parsing nutrition plan from JSON string"""
        plan_json_str = json.dumps({
            "date": "2025-10-14",
            "meals": [
                {
                    "name": "Snack",
                    "meal_type": "snack",
                    "calories": 200,
                    "protein_g": 15.0,
                    "carbs_g": 20.0,
                    "fats_g": 8.0,
                    "ingredients": ["protein shake"],
                    "instructions": "Mix and drink",
                    "prep_time_minutes": 5
                }
            ]
        })
        
        plan = NutritionParser.parse_plan_from_string(plan_json_str)
        
        assert plan.date == "2025-10-14"
        assert len(plan.meals) == 1
        assert plan.total_calories == 200


class TestParserErrorHandling:
    """Test parser error handling and defensive programming"""
    
    def test_parser_handles_empty_dict(self):
        """Test parser handles empty dictionary gracefully"""
        with pytest.raises(ParserError):
            ExerciseParser.parse({})
    
    def test_parser_handles_none(self):
        """Test parser handles None input"""
        with pytest.raises(ParserError):
            ExerciseParser.parse(None)
    
    def test_parser_handles_wrong_type(self):
        """Test parser handles wrong data types"""
        exercise_json = {
            "name": "Test",
            "muscle_groups": "chest",  # Should be list, not string
            "equipment": [],
            "difficulty": "beginner",
            "sets": "three",  # Should be int, not string
            "reps": "10",
            "rest_seconds": 60,
            "instructions": "Test"
        }
        
        # Parser should either convert or provide sensible defaults
        exercise = ExerciseParser.parse(exercise_json)
        assert isinstance(exercise.muscle_groups, list)
        assert isinstance(exercise.sets, int)
    
    def test_workout_parser_handles_empty_exercises(self):
        """Test workout parser handles workout with no exercises"""
        workout_json = {
            "title": "Empty Workout",
            "duration_minutes": 30,
            "exercises": [],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        }
        
        with pytest.raises(ParserError) as exc_info:
            WorkoutParser.parse(workout_json)
        
        assert "exercise" in str(exc_info.value).lower()
    
    def test_parser_sanitizes_strings(self):
        """Test parser trims whitespace and sanitizes strings"""
        exercise_json = {
            "name": "  Push-ups  ",  # Extra whitespace
            "muscle_groups": ["chest", "  triceps  "],
            "equipment": [],
            "difficulty": "beginner",
            "sets": 3,
            "reps": "12-15",
            "rest_seconds": 60,
            "instructions": "  Standard push-up form  "
        }
        
        exercise = ExerciseParser.parse(exercise_json)
        
        assert exercise.name == "Push-ups"  # Trimmed
        assert "triceps" in exercise.muscle_groups  # Trimmed in list


class TestParserUtilities:
    """Test parser utility functions"""
    
    def test_parser_generates_unique_ids(self):
        """Test parser generates unique IDs for workouts/plans"""
        workout_json = {
            "title": "Test Workout",
            "duration_minutes": 30,
            "exercises": [
                {
                    "name": "Exercise",
                    "muscle_groups": ["chest"],
                    "equipment": [],
                    "difficulty": "beginner",
                    "sets": 3,
                    "reps": "10",
                    "rest_seconds": 60,
                    "instructions": "Test"
                }
            ],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        }
        
        workout1 = WorkoutParser.parse(workout_json)
        workout2 = WorkoutParser.parse(workout_json)
        
        # Should generate different IDs for different instances
        assert workout1.workout_id != workout2.workout_id
    
    def test_parser_validates_difficulty_levels(self):
        """Test parser validates difficulty levels"""
        exercise_json = {
            "name": "Test",
            "muscle_groups": ["chest"],
            "equipment": [],
            "difficulty": "super_hard",  # Invalid level
            "sets": 3,
            "reps": "10",
            "rest_seconds": 60,
            "instructions": "Test"
        }
        
        exercise = ExerciseParser.parse(exercise_json)
        
        # Should default to valid difficulty level
        assert exercise.difficulty in ["beginner", "intermediate", "advanced"]
