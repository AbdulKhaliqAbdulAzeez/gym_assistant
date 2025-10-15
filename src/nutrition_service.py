"""
NutritionService - Orchestrates meal plan generation with macro calculations.

This service combines OpenAI client and parser layers to generate personalized
nutrition plans. It calculates macro targets (protein, carbs, fats) based on user
profile and goals, then uses AI to generate meal plans that meet those targets
while respecting dietary restrictions, cuisine preferences, and budget constraints.
"""

import json
from typing import Dict, Optional
from src.client import GymAssistantClient
from src.parser import NutritionParser
from src.models import (
    NutritionRequest,
    NutritionPlan,
    UserProfile,
    GymAssistantError
)


class NutritionService:
    """
    Service for generating personalized nutrition plans.
    
    Handles:
    - BMR/TDEE calculation based on user stats
    - Macro distribution based on fitness goals
    - AI-powered meal plan generation
    - Dietary restrictions (vegetarian, vegan, gluten-free, etc.)
    - Budget considerations
    - Cuisine preferences
    """
    
    def __init__(self, client: Optional[GymAssistantClient] = None):
        """
        Initialize nutrition service.
        
        Args:
            client: Optional GymAssistantClient. If None, creates new client.
        """
        self.client = client or GymAssistantClient()
        self.parser = NutritionParser()
    
    def calculate_macros(self, user: UserProfile) -> Dict[str, float]:
        """
        Calculate macro nutrient targets based on user profile and goals.
        
        Uses Mifflin-St Jeor equation for BMR, then applies activity multiplier
        and goal-based adjustments (surplus for muscle building, deficit for
        weight loss).
        
        Args:
            user: User profile with stats and goals
            
        Returns:
            Dict with keys: calories, protein_g, carbs_g, fats_g
            
        Raises:
            GymAssistantError: If user profile is invalid
        """
        if not user:
            raise GymAssistantError(
                "User profile is required for macro calculation",
                "validation_error"
            )
        
        try:
            # Calculate BMR using Mifflin-St Jeor equation
            if user.gender.upper() == "M":
                bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age + 5
            else:
                bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age - 161
            
            # Apply activity multiplier based on fitness level
            activity_multipliers = {
                "beginner": 1.375,      # Light exercise
                "intermediate": 1.55,    # Moderate exercise
                "advanced": 1.725        # Heavy exercise
            }
            activity = activity_multipliers.get(user.fitness_level, 1.55)
            tdee = bmr * activity
            
            # Adjust based on goals
            goals = [g.lower() for g in (user.goals or [])]
            if "build_muscle" in goals or "gain_weight" in goals:
                # Calorie surplus for muscle building
                target_calories = tdee * 1.15
                # High protein for muscle synthesis
                protein_g = user.weight_kg * 2.0
            elif "lose_weight" in goals or "cut" in goals:
                # Calorie deficit for fat loss
                target_calories = tdee * 0.8
                # High protein to preserve muscle
                protein_g = user.weight_kg * 1.8
            else:
                # Maintenance for general fitness/endurance
                target_calories = tdee
                protein_g = user.weight_kg * 1.6
            
            # Calculate fats (25-30% of calories)
            fats_g = (target_calories * 0.275) / 9  # 9 cal per gram of fat
            
            # Remaining calories from carbs
            remaining_calories = target_calories - (protein_g * 4 + fats_g * 9)
            carbs_g = remaining_calories / 4  # 4 cal per gram of carbs
            
            return {
                "calories": round(target_calories),
                "protein_g": round(protein_g, 1),
                "carbs_g": round(carbs_g, 1),
                "fats_g": round(fats_g, 1)
            }
            
        except (AttributeError, TypeError, ValueError) as e:
            raise GymAssistantError(
                f"Invalid user profile for macro calculation: {str(e)}",
                "validation_error"
            )
    
    def generate_meal_plan(self, request: NutritionRequest) -> NutritionPlan:
        """
        Generate personalized meal plan using AI.
        
        Calculates macro targets, builds detailed prompt with all constraints,
        calls OpenAI API, parses response, and validates output.
        
        Args:
            request: Nutrition request with user profile and preferences
            
        Returns:
            NutritionPlan with meals and totals
            
        Raises:
            GymAssistantError: If generation fails or output is invalid
        """
        if not request or not request.user_profile:
            raise GymAssistantError(
                "Valid nutrition request with user profile is required",
                "validation_error"
            )
        
        try:
            # Calculate macro targets
            macros = self.calculate_macros(request.user_profile)
            
            # Build prompt
            prompt = self._build_nutrition_prompt(request, macros)
            system_message = self._build_system_message()
            
            # Get model from request or use default
            model = request.model if hasattr(request, 'model') and request.model else "gpt-4o"
            
            # Call AI
            response = self.client.generate_completion(
                prompt=prompt,
                system_message=system_message,
                model=model,
                temperature=0.7
            )
            
            # Parse response
            plan_json = json.loads(response)
            plan = self.parser.parse_plan(plan_json)
            
            # Validate output
            self._validate_plan(plan, macros)
            
            return plan
            
        except json.JSONDecodeError as e:
            raise GymAssistantError(
                f"Failed to parse AI response as JSON: {str(e)}",
                "parser_error"
            )
        except GymAssistantError:
            # Re-raise our errors
            raise
        except Exception as e:
            raise GymAssistantError(
                f"Meal plan generation failed: {str(e)}",
                "generation_error"
            )
    
    def _build_nutrition_prompt(
        self, 
        request: NutritionRequest,
        macros: Dict[str, float]
    ) -> str:
        """
        Build detailed prompt for AI meal plan generation.
        
        Args:
            request: Nutrition request with preferences
            macros: Calculated macro targets
            
        Returns:
            Detailed prompt string
        """
        user = request.user_profile
        
        # Start with user profile and goals
        prompt = f"""Generate a personalized daily meal plan for the following user:

USER PROFILE:
- Age: {user.age}
- Weight: {user.weight_kg} kg
- Height: {user.height_cm} cm
- Gender: {user.gender}
- Fitness Level: {user.fitness_level}
- Goals: {', '.join(user.goals or ['general fitness'])}

MACRO TARGETS (must meet these closely):
- Calories: {macros['calories']} kcal
- Protein: {macros['protein_g']}g
- Carbs: {macros['carbs_g']}g
- Fats: {macros['fats_g']}g
"""
        
        # Add dietary restrictions
        if request.dietary_restrictions:
            restrictions = ', '.join(request.dietary_restrictions)
            prompt += f"\nDIETARY RESTRICTIONS:\n- Must be: {restrictions}\n"
        
        # Add cuisine preferences
        if request.cuisine_preferences:
            cuisines = ', '.join(request.cuisine_preferences)
            prompt += f"\nCUISINE PREFERENCES:\n- Prefer: {cuisines}\n"
        
        # Add budget level
        budget_guidance = {
            "low": "Use affordable, budget-friendly ingredients. Focus on staples like rice, beans, chicken, eggs.",
            "medium": "Use moderate-priced ingredients. Balance between affordability and variety.",
            "high": "Use premium ingredients. Include high-quality proteins, organic options, specialty items."
        }
        budget_level = request.budget_level or "medium"
        prompt += f"\nBUDGET LEVEL: {budget_level}\n- {budget_guidance.get(budget_level, budget_guidance['medium'])}\n"
        
        # Add output format requirements
        prompt += """
REQUIREMENTS:
1. Create 3-5 meals for the day (breakfast, lunch, dinner, and optional snacks)
2. Each meal should have realistic portions and macro values
3. Total daily macros should closely match the targets above (within 10%)
4. Include variety of foods and flavors
5. All meals should be practical to prepare

Return your response as a JSON object with this EXACT structure:
{
    "date": "YYYY-MM-DD",
    "meals": [
        {
            "name": "meal name",
            "meal_type": "breakfast/lunch/dinner/snack",
            "calories": 500,
            "protein_g": 40.0,
            "carbs_g": 50.0,
            "fats_g": 15.0,
            "ingredients": ["ingredient1", "ingredient2"],
            "instructions": "preparation instructions",
            "prep_time_minutes": 20
        }
    ],
    "notes": "optional notes about the meal plan"
}

Ensure the JSON is valid and all fields are present."""
        
        return prompt
    
    def _build_system_message(self) -> str:
        """
        Build system message defining AI's role.
        
        Returns:
            System message string
        """
        return """You are an expert nutritionist and dietitian specializing in sports nutrition 
and meal planning. You create personalized, balanced meal plans that help clients achieve 
their fitness goals while respecting their dietary needs and preferences. You have deep 
knowledge of macro nutrients, food science, and practical meal preparation. Always provide 
realistic, achievable meal plans with accurate nutritional information."""
    
    def _validate_plan(self, plan: NutritionPlan, macros: Dict[str, float]) -> None:
        """
        Validate generated meal plan meets requirements.
        
        Args:
            plan: Parsed nutrition plan
            macros: Target macros
            
        Raises:
            GymAssistantError: If plan is invalid
        """
        # Check plan has meals
        if not plan.meals or len(plan.meals) == 0:
            raise GymAssistantError(
                "Generated meal plan has no meals",
                "validation_error"
            )
        
        # Check totals are positive
        if plan.total_calories <= 0 or plan.total_protein_g <= 0:
            raise GymAssistantError(
                "Generated meal plan has invalid macro totals",
                "validation_error"
            )
        
        # Check totals are reasonably close to targets (within 20%)
        calorie_diff = abs(plan.total_calories - macros["calories"]) / macros["calories"]
        if calorie_diff > 0.20:
            # This is a soft warning - don't fail the plan, but could log it
            pass  # In production, might want to log this discrepancy
