"""
Workout Service for orchestrating workout generation.
Coordinates between client (API calls) and parser (data transformation).
"""

from typing import Optional
from src.client import GymAssistantClient
from src.parser import WorkoutParser
from src.models import WorkoutRequest, Workout, GymAssistantError


class WorkoutService:
    """Service for generating personalized workout plans"""
    
    def __init__(self, client: Optional[GymAssistantClient] = None):
        """
        Initialize workout service.
        
        Args:
            client: Optional GymAssistantClient. If None, creates new client.
        """
        self.client = client if client else GymAssistantClient()
    
    def generate_workout(self, request: WorkoutRequest) -> Workout:
        """
        Generate a personalized workout plan.
        
        Args:
            request: WorkoutRequest with user profile and preferences
        
        Returns:
            Workout object with exercises and details
        
        Raises:
            GymAssistantError: If generation or parsing fails
        """
        if request is None:
            raise GymAssistantError("Workout request cannot be None", "validation_error")
        
        try:
            # Build the prompt for AI
            prompt = self._build_workout_prompt(request)
            
            # Build system message
            system_message = self._build_system_message()
            
            # Call OpenAI API
            response = self.client.generate_completion(
                prompt=prompt,
                model=request.model,
                system_message=system_message,
                temperature=0.7,
                max_tokens=2500
            )
            
            # Parse response into Workout object
            workout = WorkoutParser.parse_from_string(response)
            
            # Validate the workout
            self._validate_workout(workout, request)
            
            return workout
        
        except GymAssistantError:
            raise
        except Exception as e:
            raise GymAssistantError(
                f"Error generating workout: {str(e)}",
                "workout_generation_error"
            )
    
    def _build_workout_prompt(self, request: WorkoutRequest) -> str:
        """
        Build the prompt for workout generation.
        
        Args:
            request: WorkoutRequest with user details
        
        Returns:
            Formatted prompt string
        """
        user = request.user_profile
        
        # Build equipment list
        equipment_str = ", ".join(user.equipment_available) if user.equipment_available else "none (bodyweight only)"
        
        # Build injury/restriction list
        injury_str = ""
        if user.injuries:
            injury_str = f"\n- Injuries to avoid: {', '.join(user.injuries)}"
        
        # Build target muscles
        target_str = ""
        if request.target_muscles:
            target_str = f"\n- Target these muscle groups: {', '.join(request.target_muscles)}"
        
        # Build goals
        goals_str = ", ".join(user.goals) if user.goals else "general fitness"
        
        prompt = f"""You are an expert personal trainer. Create a {request.duration_minutes}-minute {request.workout_type} workout plan.

USER PROFILE:
- Age: {user.age}, Gender: {user.gender}
- Weight: {user.weight_kg}kg, Height: {user.height_cm}cm (BMI: {user.bmi:.1f})
- Fitness Level: {user.fitness_level}
- Goals: {goals_str}
- Equipment Available: {equipment_str}{injury_str}{target_str}

REQUIREMENTS:
1. Create a {request.duration_minutes}-minute {request.workout_type} workout
2. Match the user's {user.fitness_level} fitness level
3. Only use available equipment: {equipment_str}
4. Include appropriate number of exercises for the duration
5. Provide sets, reps, rest time, detailed instructions, and safety tips for each exercise
6. Include specific warm-up and cool-down routines
7. Estimate total calorie burn
8. Consider the user's goals: {goals_str}{injury_str}

Return the workout as JSON following this EXACT structure:
{{
  "title": "Descriptive Workout Title",
  "duration_minutes": {request.duration_minutes},
  "exercises": [
    {{
      "name": "Exercise Name",
      "muscle_groups": ["chest", "triceps"],
      "equipment": ["dumbbells"],
      "difficulty": "{user.fitness_level}",
      "sets": 4,
      "reps": "8-10",
      "rest_seconds": 90,
      "instructions": "Detailed step-by-step instructions on proper form and execution",
      "safety_tips": "Important safety considerations and common mistakes to avoid"
    }}
  ],
  "warmup": "Specific 5-minute warm-up routine",
  "cooldown": "Specific 5-minute cool-down and stretching routine",
  "target_muscles": ["{request.workout_type}"],
  "calories_estimate": 350
}}

IMPORTANT: Return ONLY the JSON, no additional text."""
        
        return prompt
    
    def _build_system_message(self) -> str:
        """
        Build the system message for AI context.
        
        Returns:
            System message string
        """
        return """You are an expert certified personal trainer and fitness coach with years of experience. 
You create safe, effective, and personalized workout plans. You understand proper exercise form, 
safety considerations, and how to adapt exercises for different fitness levels and limitations. 
Always prioritize safety and proper form over intensity."""
    
    def _validate_workout(self, workout: Workout, request: WorkoutRequest) -> None:
        """
        Validate the generated workout meets requirements.
        
        Args:
            workout: Generated workout to validate
            request: Original request to validate against
        
        Raises:
            GymAssistantError: If workout doesn't meet requirements
        """
        # Check has exercises
        if not workout.exercises or len(workout.exercises) == 0:
            raise GymAssistantError(
                "Generated workout has no exercises",
                "validation_error"
            )
        
        # Check duration is reasonable
        duration_diff = abs(workout.duration_minutes - request.duration_minutes)
        if duration_diff > 15:  # Allow 15 minute variance
            raise GymAssistantError(
                f"Workout duration {workout.duration_minutes} differs too much from requested {request.duration_minutes}",
                "validation_error"
            )
        
        # Check exercises have required fields
        for exercise in workout.exercises:
            if not exercise.name or not exercise.instructions:
                raise GymAssistantError(
                    "Exercise missing required fields (name or instructions)",
                    "validation_error"
                )
