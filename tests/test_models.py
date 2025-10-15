"""
Test suite for data models (TDD RED phase first).
Following the design from GYM_ASSISTANT_HANDOFF.md
"""

import pytest
from datetime import datetime
from typing import List, Optional
from src.models import (
    UserProfile,
    Exercise,
    Workout,
    Meal,
    NutritionPlan,
    WorkoutRequest,
    NutritionRequest,
    ExerciseEmbedding,
    GymAssistantError
)


class TestUserProfile:
    """Test UserProfile dataclass and BMI calculation"""
    
    def test_user_profile_creation(self):
        """Test creating a user profile with valid data"""
        user = UserProfile(
            user_id="test123",
            age=28,
            weight_kg=75.0,
            height_cm=175.0,
            gender="M",
            fitness_level="intermediate",
            goals=["build_muscle", "endurance"],
            injuries=["knee"],
            equipment_available=["dumbbells", "resistance_bands"]
        )
        
        assert user.user_id == "test123"
        assert user.age == 28
        assert user.weight_kg == 75.0
        assert user.height_cm == 175.0
        assert user.gender == "M"
        assert user.fitness_level == "intermediate"
        assert user.goals == ["build_muscle", "endurance"]
        assert user.injuries == ["knee"]
        assert user.equipment_available == ["dumbbells", "resistance_bands"]
    
    def test_user_profile_calculates_bmi(self):
        """Test BMI property calculation"""
        user = UserProfile(
            user_id="test456",
            age=30,
            weight_kg=80.0,
            height_cm=180.0,
            gender="F",
            fitness_level="beginner",
            goals=["lose_weight"]
        )
        
        # BMI = weight_kg / (height_m)^2
        # 80 / (1.8)^2 = 80 / 3.24 = 24.69...
        expected_bmi = 80.0 / (1.8 ** 2)
        assert abs(user.bmi - expected_bmi) < 0.01
    
    def test_user_profile_optional_fields(self):
        """Test user profile with minimal required fields"""
        user = UserProfile(
            user_id="test789",
            age=25,
            weight_kg=70.0,
            height_cm=170.0,
            gender="Other",
            fitness_level="advanced",
            goals=["endurance"]
        )
        
        assert user.injuries is None
        assert user.equipment_available is None


class TestExercise:
    """Test Exercise dataclass"""
    
    def test_exercise_creation(self):
        """Test creating an exercise with all fields"""
        exercise = Exercise(
            name="Dumbbell Bench Press",
            muscle_groups=["chest", "triceps", "shoulders"],
            equipment=["dumbbells", "bench"],
            difficulty="intermediate",
            sets=4,
            reps="8-10",
            rest_seconds=90,
            instructions="Lie on bench, press dumbbells up from chest level",
            safety_tips="Keep back flat on bench, don't lock elbows"
        )
        
        assert exercise.name == "Dumbbell Bench Press"
        assert exercise.muscle_groups == ["chest", "triceps", "shoulders"]
        assert exercise.equipment == ["dumbbells", "bench"]
        assert exercise.difficulty == "intermediate"
        assert exercise.sets == 4
        assert exercise.reps == "8-10"
        assert exercise.rest_seconds == 90
        assert "Lie on bench" in exercise.instructions
        assert exercise.safety_tips is not None
    
    def test_exercise_without_safety_tips(self):
        """Test exercise with optional safety_tips missing"""
        exercise = Exercise(
            name="Jumping Jacks",
            muscle_groups=["cardio"],
            equipment=[],
            difficulty="beginner",
            sets=3,
            reps="30 seconds",
            rest_seconds=30,
            instructions="Jump with arms and legs spread"
        )
        
        assert exercise.safety_tips is None


class TestWorkout:
    """Test Workout dataclass"""
    
    def test_workout_with_exercises(self):
        """Test workout contains multiple exercises"""
        exercise1 = Exercise(
            name="Push-ups",
            muscle_groups=["chest", "triceps"],
            equipment=[],
            difficulty="beginner",
            sets=3,
            reps="12-15",
            rest_seconds=60,
            instructions="Standard push-up form"
        )
        
        exercise2 = Exercise(
            name="Squats",
            muscle_groups=["legs", "glutes"],
            equipment=[],
            difficulty="beginner",
            sets=3,
            reps="15",
            rest_seconds=60,
            instructions="Feet shoulder-width apart"
        )
        
        workout = Workout(
            workout_id="workout_001",
            title="Full Body Beginner",
            duration_minutes=30,
            exercises=[exercise1, exercise2],
            warmup="5 minutes of light cardio",
            cooldown="5 minutes of stretching",
            difficulty="beginner",
            target_muscles=["chest", "legs"],
            calories_estimate=250
        )
        
        assert workout.workout_id == "workout_001"
        assert workout.title == "Full Body Beginner"
        assert workout.duration_minutes == 30
        assert len(workout.exercises) == 2
        assert workout.exercises[0].name == "Push-ups"
        assert workout.exercises[1].name == "Squats"
        assert workout.warmup == "5 minutes of light cardio"
        assert workout.cooldown == "5 minutes of stretching"
        assert workout.difficulty == "beginner"
        assert workout.target_muscles == ["chest", "legs"]
        assert workout.calories_estimate == 250
        assert isinstance(workout.created_at, datetime)


class TestMeal:
    """Test Meal dataclass"""
    
    def test_meal_creation(self):
        """Test meal with macros and ingredients"""
        meal = Meal(
            name="Grilled Chicken Breast with Rice",
            meal_type="lunch",
            calories=450,
            protein_g=40.0,
            carbs_g=50.0,
            fats_g=10.0,
            ingredients=["chicken breast", "brown rice", "broccoli", "olive oil"],
            instructions="Grill chicken, cook rice, steam broccoli",
            prep_time_minutes=25
        )
        
        assert meal.name == "Grilled Chicken Breast with Rice"
        assert meal.meal_type == "lunch"
        assert meal.calories == 450
        assert meal.protein_g == 40.0
        assert meal.carbs_g == 50.0
        assert meal.fats_g == 10.0
        assert len(meal.ingredients) == 4
        assert "chicken breast" in meal.ingredients
        assert meal.prep_time_minutes == 25


class TestNutritionPlan:
    """Test NutritionPlan dataclass"""
    
    def test_nutrition_plan_calculates_totals(self):
        """Test nutrition plan sums macros correctly"""
        meal1 = Meal(
            name="Breakfast",
            meal_type="breakfast",
            calories=400,
            protein_g=25.0,
            carbs_g=45.0,
            fats_g=12.0,
            ingredients=["eggs", "oatmeal"],
            instructions="Cook eggs, prepare oatmeal",
            prep_time_minutes=15
        )
        
        meal2 = Meal(
            name="Lunch",
            meal_type="lunch",
            calories=550,
            protein_g=40.0,
            carbs_g=60.0,
            fats_g=15.0,
            ingredients=["chicken", "rice"],
            instructions="Grill chicken, cook rice",
            prep_time_minutes=30
        )
        
        nutrition_plan = NutritionPlan(
            plan_id="plan_001",
            date="2025-10-14",
            meals=[meal1, meal2],
            total_calories=950,
            total_protein_g=65.0,
            total_carbs_g=105.0,
            total_fats_g=27.0,
            notes="High protein for muscle building"
        )
        
        assert nutrition_plan.plan_id == "plan_001"
        assert nutrition_plan.date == "2025-10-14"
        assert len(nutrition_plan.meals) == 2
        assert nutrition_plan.total_calories == 950
        assert nutrition_plan.total_protein_g == 65.0
        assert nutrition_plan.total_carbs_g == 105.0
        assert nutrition_plan.total_fats_g == 27.0
        assert nutrition_plan.notes == "High protein for muscle building"


class TestWorkoutRequest:
    """Test WorkoutRequest dataclass"""
    
    def test_workout_request_creation(self):
        """Test creating a workout request"""
        user = UserProfile(
            user_id="test001",
            age=25,
            weight_kg=70.0,
            height_cm=175.0,
            gender="M",
            fitness_level="intermediate",
            goals=["build_muscle"]
        )
        
        request = WorkoutRequest(
            user_profile=user,
            workout_type="strength",
            duration_minutes=45,
            target_muscles=["chest", "triceps"],
            model="gpt-4o",
            reasoning_effort="medium"
        )
        
        assert request.user_profile == user
        assert request.workout_type == "strength"
        assert request.duration_minutes == 45
        assert request.target_muscles == ["chest", "triceps"]
        assert request.model == "gpt-4o"
        assert request.reasoning_effort == "medium"


class TestNutritionRequest:
    """Test NutritionRequest dataclass"""
    
    def test_nutrition_request_creation(self):
        """Test creating a nutrition request"""
        user = UserProfile(
            user_id="test002",
            age=30,
            weight_kg=65.0,
            height_cm=165.0,
            gender="F",
            fitness_level="beginner",
            goals=["lose_weight"]
        )
        
        request = NutritionRequest(
            user_profile=user,
            dietary_restrictions=["vegetarian", "gluten-free"],
            cuisine_preferences=["Mediterranean", "Asian"],
            budget_level="medium",
            model="gpt-4o"
        )
        
        assert request.user_profile == user
        assert request.dietary_restrictions == ["vegetarian", "gluten-free"]
        assert request.cuisine_preferences == ["Mediterranean", "Asian"]
        assert request.budget_level == "medium"
        assert request.model == "gpt-4o"


class TestExerciseEmbedding:
    """Test ExerciseEmbedding dataclass"""
    
    def test_exercise_embedding_creation(self):
        """Test creating an exercise embedding"""
        # Simulate a small embedding vector (real one is 3072-dimensional)
        embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        embedding = ExerciseEmbedding(
            exercise_name="Push-ups",
            description="Bodyweight chest exercise",
            embedding=embedding_vector,
            metadata={"difficulty": "beginner", "equipment": "none"}
        )
        
        assert embedding.exercise_name == "Push-ups"
        assert embedding.description == "Bodyweight chest exercise"
        assert embedding.embedding == embedding_vector
        assert embedding.metadata["difficulty"] == "beginner"
        assert embedding.metadata["equipment"] == "none"


class TestGymAssistantError:
    """Test custom exception class"""
    
    def test_gym_assistant_error_creation(self):
        """Test creating custom error with type"""
        error = GymAssistantError("API request failed", "api_error")
        
        assert error.message == "API request failed"
        assert error.error_type == "api_error"
        assert str(error) == "API request failed"
    
    def test_gym_assistant_error_can_be_raised(self):
        """Test that error can be raised and caught"""
        with pytest.raises(GymAssistantError) as exc_info:
            raise GymAssistantError("Invalid input", "validation_error")
        
        assert exc_info.value.error_type == "validation_error"
        assert "Invalid input" in str(exc_info.value)
