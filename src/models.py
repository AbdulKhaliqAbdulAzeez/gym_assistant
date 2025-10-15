"""
Data models for the AI Gym Assistant.
All models use dataclasses for clean, typed data structures.
Following the design from GYM_ASSISTANT_HANDOFF.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class UserProfile:
    """User profile with fitness information and goals"""
    user_id: str
    age: int
    weight_kg: float
    height_cm: float
    gender: str  # "M", "F", "Other"
    fitness_level: str  # "beginner", "intermediate", "advanced"
    goals: List[str]  # ["build_muscle", "lose_weight", "endurance"]
    injuries: Optional[List[str]] = None
    equipment_available: Optional[List[str]] = None
    
    @property
    def bmi(self) -> float:
        """Calculate Body Mass Index (BMI)"""
        height_m = self.height_cm / 100.0
        return self.weight_kg / (height_m ** 2)


@dataclass
class Exercise:
    """Single exercise with instructions and parameters"""
    name: str
    muscle_groups: List[str]  # ["chest", "triceps", "shoulders"]
    equipment: List[str]  # ["dumbbells", "bench"]
    difficulty: str  # "beginner", "intermediate", "advanced"
    sets: int
    reps: str  # "10-12" or "30 seconds"
    rest_seconds: int
    instructions: str  # How to perform the exercise
    safety_tips: Optional[str] = None


@dataclass
class Workout:
    """Complete workout plan with multiple exercises"""
    workout_id: str
    title: str
    duration_minutes: int
    exercises: List[Exercise]
    warmup: str
    cooldown: str
    difficulty: str
    target_muscles: List[str]
    calories_estimate: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Meal:
    """Single meal with nutritional information"""
    name: str
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    ingredients: List[str]
    instructions: str
    prep_time_minutes: int


@dataclass
class NutritionPlan:
    """Daily nutrition plan with multiple meals"""
    plan_id: str
    date: str
    meals: List[Meal]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fats_g: float
    notes: Optional[str] = None


@dataclass
class WorkoutRequest:
    """Request for generating a personalized workout"""
    user_profile: UserProfile
    workout_type: str  # "strength", "cardio", "yoga", "hiit"
    duration_minutes: int
    target_muscles: Optional[List[str]] = None
    model: str = "gpt-4o"
    reasoning_effort: str = "medium"


@dataclass
class NutritionRequest:
    """Request for generating a meal plan"""
    user_profile: UserProfile
    dietary_restrictions: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None
    budget_level: str = "medium"  # "low", "medium", "high"
    model: str = "gpt-4o"


@dataclass
class ExerciseEmbedding:
    """Exercise with vector embedding for similarity search"""
    exercise_name: str
    description: str
    embedding: List[float]  # 3072-dimensional vector from text-embedding-3-large
    metadata: Dict[str, Any]  # {"difficulty": "intermediate", "equipment": [...]}


class GymAssistantError(Exception):
    """Base exception for gym assistant errors"""
    def __init__(self, message: str, error_type: str):
        self.message = message
        self.error_type = error_type  # "api_error", "validation_error", etc.
        super().__init__(self.message)
