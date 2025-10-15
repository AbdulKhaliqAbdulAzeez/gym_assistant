"""
Interactive CLI for AI Gym Assistant.

Provides a user-friendly command-line interface for:
- Creating and managing user profiles
- Generating personalized workout plans
- Creating custom meal plans
- Finding similar exercises
"""

import sys
import uuid
from typing import Optional, List, Dict, Any, Iterable

from src.config import get_config
from src.defaults import (
    DEFAULT_EXERCISE_DIFFICULTY,
    DEFAULT_EXERCISE_REPS,
    DEFAULT_EXERCISE_REST_SECONDS,
    DEFAULT_EXERCISE_SETS,
    DEFAULT_PLACEHOLDER_INSTRUCTIONS,
)
from src.models import (
    UserProfile,
    Workout,
    NutritionPlan,
    Exercise,
    WorkoutRequest,
    NutritionRequest,
    GymAssistantError
)
from src.workout_service import WorkoutService
from src.nutrition_service import NutritionService
from src.embedding_service import EmbeddingService
from src.logging_config import setup_logging, get_logger
from src.storage import Storage

logger = get_logger(__name__)
_LOGGING_INITIALIZED = False


def initialize_logging() -> None:
    """Configure logging lazily based on environment flags."""
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED:
        return

    config = get_config()
    
    if config.logging_disabled:
        logger.disabled = True
        _LOGGING_INITIALIZED = True
        return

    setup_logging(
        log_level=config.logging_level,
        log_dir=config.logging_dir,
        log_to_console=config.logging_to_console,
        log_to_file=config.logging_to_file
    )

    _LOGGING_INITIALIZED = True


class GymAssistantCLI:
    """
    Main CLI application class.
    
    Manages user interaction and coordinates between services.
    """
    
    def __init__(
        self, 
        user_profile: Optional[UserProfile] = None,
        workout_service: Optional[WorkoutService] = None,
        nutrition_service: Optional[NutritionService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        storage: Optional[Storage] = None,
    ):
        """
        Initialize CLI with services.
        
        Args:
            user_profile: Optional existing user profile
            workout_service: Optional workout service (for testing)
            nutrition_service: Optional nutrition service (for testing)
            embedding_service: Optional embedding service (for testing)
        """
        self.user_profile = user_profile
        self.workout_service = workout_service or WorkoutService()
        self.nutrition_service = nutrition_service or NutritionService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.storage = storage or Storage()
        self._api_usage_notice_shown = False
        self._loaded_profile_from_storage = False

        if not self.user_profile:
            stored_profile = self.storage.load_user_profile()
            if stored_profile:
                self.user_profile = stored_profile
                self._loaded_profile_from_storage = True
                logger.info("Loaded user profile from storage: %s", stored_profile.user_id)

    def _maybe_show_api_usage_notice(self) -> None:
        """Print OpenAI usage guidance once per session."""
        if self._api_usage_notice_shown:
            return

        print(
            "\nℹ️  OpenAI API usage reminder: each workout or meal plan request "
            "calls GPT-4o and counts toward your OpenAI bill."
        )
        print(
            "   • Typical plan generation uses ≈2K–3K output tokens "
            "(~$0.02 at $15/1M output tokens)."
        )
        print(
            "   • Self-serve API keys default to ~10 requests/min; space calls to "
            "avoid 429 rate limit errors."
        )
        print(
            "   • See README → 'OpenAI API Usage & Costs' for budgeting tips before "
            "batching multiple plans."
        )

        self._api_usage_notice_shown = True
    
    def run(self):
        """
        Main application loop.
        
        Displays menu and handles user choices until exit.
        """
        logger.info("Starting AI Gym Assistant CLI")
        print("\n" + "="*60)
        print("🏋️  AI GYM ASSISTANT")
        print("="*60)

        if self._loaded_profile_from_storage and self.user_profile:
            print(f"\n📁 Loaded saved profile for {self.user_profile.user_id}.")
            self._loaded_profile_from_storage = False
        
        # Check if user has profile
        if not self.user_profile:
            logger.info("No user profile found, prompting for creation")
            print("\n⚠️  No user profile found.")
            response = input("Would you like to create one now? (y/n): ").strip().lower()
            if response == 'y':
                profile = create_user_profile()
                if profile:
                    self._set_user_profile(profile)
                    logger.info(f"User profile created: {self.user_profile.user_id}")
                    print("\n✅ Profile created successfully!")
                else:
                    logger.info("User cancelled profile creation from startup prompt")
                    print("\n↩️  Profile creation cancelled. You can create one later from the menu.")
        
        # Main loop
        while True:
            try:
                display_menu()
                choice = get_user_input(valid_choices={"1", "2", "3", "4", "5"})
                logger.debug(f"User selected menu option: {choice}")
                
                if choice == '1':
                    # Generate workout
                    if not self.user_profile:
                        print("\n⚠️  Please create a user profile first (option 4)")
                        continue
                    
                    logger.info("Generating workout plan")
                    workout = self.generate_workout()
                    if workout:
                        display_workout(workout)
                        logger.info(f"Workout generated: {workout.title}")
                
                elif choice == '2':
                    # Generate meal plan
                    if not self.user_profile:
                        print("\n⚠️  Please create a user profile first (option 4)")
                        continue
                    
                    logger.info("Generating meal plan")
                    meal_plan = self.generate_meal_plan()
                    if meal_plan:
                        display_meal_plan(meal_plan)
                        logger.info(f"Meal plan generated with {len(meal_plan.meals)} meals")
                
                elif choice == '3':
                    # Find similar exercises
                    logger.info("Searching for similar exercises")
                    exercises = self.find_similar_exercises()
                    if exercises:
                        display_similar_exercises(exercises)
                        logger.info(f"Found {len(exercises)} similar exercises")
                
                elif choice == '4':
                    # View/Create profile
                    self.view_profile()
                
                elif choice == '5':
                    # Exit
                    logger.info("User exiting application")
                    print("\n👋 Thank you for using AI Gym Assistant!")
                    print("Stay healthy and keep training! 💪\n")
                    break
                
                else:
                    print("\n⚠️  Invalid choice. Please select 1-5.")
            
            except KeyboardInterrupt:
                logger.info("User interrupted with Ctrl+C")
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
                print(f"\n❌ An error occurred: {str(e)}")
                print("Please try again or contact support.\n")
    
    def generate_workout(self) -> Optional[Workout]:
        """
        Generate personalized workout plan.
        
        Returns:
            Workout object or None if generation fails
            
        Raises:
            ValueError: If no user profile exists
        """
        if not self.user_profile:
            raise ValueError("User profile required for workout generation")
        
        self._maybe_show_api_usage_notice()

        print("\n" + "-"*60)
        print("🏋️  GENERATE WORKOUT PLAN")
        print("-"*60)
        
        try:
            # Get workout preferences
            workout_type = input("\nWorkout type (strength/cardio/hiit/flexibility) [strength]: ").strip().lower()
            if not workout_type:
                workout_type = "strength"
            
            duration = input("Duration in minutes [45]: ").strip()
            try:
                duration_minutes = int(duration) if duration else 45
            except ValueError:
                duration_minutes = 45
            
            target_muscles = input("Target muscle groups (comma-separated) []: ").strip()
            target_list = [m.strip() for m in target_muscles.split(",")] if target_muscles else None
            
            # Build request
            request = WorkoutRequest(
                user_profile=self.user_profile,
                workout_type=workout_type,
                duration_minutes=duration_minutes,
                target_muscles=target_list
            )
            
            print("\n⏳ Generating your personalized workout...")
            workout = self.workout_service.generate_workout(request)
            if workout:
                self.storage.record_workout_summary(workout)
            return workout
        
        except GymAssistantError as e:
            logger.error(f"Gym assistant error during workout generation: {e.message}")
            print(f"\n❌ Error: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during workout generation: {str(e)}", exc_info=True)
            print(f"\n❌ Unexpected error: {str(e)}")
            return None
    
    def generate_meal_plan(self) -> Optional[NutritionPlan]:
        """
        Generate personalized meal plan.
        
        Returns:
            NutritionPlan object or None if generation fails
            
        Raises:
            ValueError: If no user profile exists
        """
        if not self.user_profile:
            raise ValueError("User profile required for meal plan generation")
        
        self._maybe_show_api_usage_notice()

        print("\n" + "-"*60)
        print("🍽️  GENERATE MEAL PLAN")
        print("-"*60)
        
        try:
            # Get meal plan preferences
            restrictions = input("\nDietary restrictions (comma-separated) [none]: ").strip()
            restriction_list = [r.strip() for r in restrictions.split(",")] if restrictions and restrictions.lower() != "none" else None
            
            cuisines = input("Cuisine preferences (comma-separated) [any]: ").strip()
            cuisine_list = [c.strip() for c in cuisines.split(",")] if cuisines and cuisines.lower() != "any" else None
            
            budget = input("Budget level (low/medium/high) [medium]: ").strip().lower()
            if budget not in ["low", "medium", "high"]:
                budget = "medium"
            
            # Build request
            request = NutritionRequest(
                user_profile=self.user_profile,
                dietary_restrictions=restriction_list,
                cuisine_preferences=cuisine_list,
                budget_level=budget
            )
            
            print("\n⏳ Generating your personalized meal plan...")
            meal_plan = self.nutrition_service.generate_meal_plan(request)
            if meal_plan:
                self.storage.record_meal_plan_summary(meal_plan)
            return meal_plan
        
        except GymAssistantError as e:
            logger.error(f"Gym assistant error during meal plan generation: {e.message}")
            print(f"\n❌ Error: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during meal plan generation: {str(e)}", exc_info=True)
            print(f"\n❌ Unexpected error: {str(e)}")
            return None

    def _set_user_profile(self, profile: UserProfile) -> None:
        """Store user profile in memory and persist to disk."""
        self.user_profile = profile
        self._loaded_profile_from_storage = False
        self.storage.save_user_profile(profile)

    def _display_history_summary(self) -> None:
        """Show recent workout and meal history if persistence is enabled."""
        if not self.user_profile or self.storage.disabled:
            return

        history = self.storage.get_history()
        workouts = history.get("workouts", [])[:3]
        meal_plans = history.get("meal_plans", [])[:3]

        if workouts:
            print("\n🗂️  Recent Workouts:")
            for entry in workouts:
                title = entry.get("title", "Workout")
                duration = entry.get("duration_minutes")
                created_at = entry.get("created_at")
                summary = f"   • {title}"
                if duration:
                    summary += f" ({duration} min)"
                if created_at:
                    summary += f" — {created_at}"
                print(summary)

        if meal_plans:
            print("\n🥗 Recent Meal Plans:")
            for entry in meal_plans:
                title = ", ".join(entry.get("meal_names", [])) or "Plan"
                calories = entry.get("total_calories")
                summary = f"   • {title}"
                if calories:
                    summary += f" — {calories} kcal"
                print(summary)
    
    def find_similar_exercises(self) -> Optional[List[Exercise]]:
        """
        Find similar exercises using semantic search.
        
        Returns:
            List of similar exercises or None if search fails
        """
        print("\n" + "-"*60)
        print("🔍 FIND SIMILAR EXERCISES")
        print("-"*60)
        
        try:
            query = input("\nDescribe the exercise you're looking for: ").strip()
            if not query:
                print("⚠️  Please provide a search query.")
                return None
            
            num_results = input("How many results? [5]: ").strip()
            try:
                top_k = int(num_results) if num_results else 5
            except ValueError:
                top_k = 5
            
            print(f"\n⏳ Searching for exercises similar to: {query}")
            raw_results = self.embedding_service.find_similar_exercises(query, top_k=top_k)

            if not raw_results:
                logger.info("No similar exercises returned for query")
                return []

            structured_results = []

            for result in raw_results:
                similarity_score: Optional[float] = None
                exercise_obj: Optional[Exercise] = None

                if isinstance(result, tuple) and result:
                    exercise_name = str(result[0])
                    if len(result) > 1 and isinstance(result[1], (float, int)):
                        similarity_score = float(result[1])
                    details = self.embedding_service.get_exercise_details(exercise_name)
                    metadata = details.metadata if details else {}
                    exercise_obj = self._exercise_from_metadata(exercise_name, metadata)
                elif isinstance(result, Exercise):
                    exercise_obj = result
                else:
                    exercise_name = str(result)
                    details = self.embedding_service.get_exercise_details(exercise_name)
                    metadata = details.metadata if details else {}
                    exercise_obj = self._exercise_from_metadata(exercise_name, metadata)

                if exercise_obj:
                    if similarity_score is not None:
                        structured_results.append((exercise_obj, similarity_score))
                    else:
                        structured_results.append(exercise_obj)

            if not structured_results:
                logger.warning("Similar exercise search returned results but none could be displayed")

            return structured_results
        
        except GymAssistantError as e:
            logger.error(f"Gym assistant error during exercise search: {e.message}")
            print(f"\n❌ Error: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during exercise search: {str(e)}", exc_info=True)
            print(f"\n❌ Unexpected error: {str(e)}")
            return None
    
    def view_profile(self):
        """Display or create user profile."""
        if not self.user_profile:
            print("\n" + "-"*60)
            print("👤 USER PROFILE")
            print("-"*60)
            print("\n⚠️  No profile found.")
            
            response = input("\nWould you like to create a profile? (y/n): ").strip().lower()
            if response == 'y':
                profile = create_user_profile()
                if profile:
                    self._set_user_profile(profile)
                    print("\n✅ Profile created successfully!")
                    self.view_profile()  # Display the new profile
                else:
                    print("\n↩️  Profile creation cancelled.")
        else:
            print("\n" + "-"*60)
            print("👤 YOUR PROFILE")
            print("-"*60)
            print(f"\nAge: {self.user_profile.age} years")
            print(f"Gender: {self.user_profile.gender}")
            print(f"Weight: {self.user_profile.weight_kg} kg")
            print(f"Height: {self.user_profile.height_cm} cm")
            print(f"BMI: {self.user_profile.bmi:.1f}")
            print(f"Fitness Level: {self.user_profile.fitness_level}")
            print(f"Goals: {', '.join(self.user_profile.goals or ['None'])}")
            print(f"Equipment: {', '.join(self.user_profile.equipment_available or ['None'])}")
            print(f"Injuries: {', '.join(self.user_profile.injuries or ['None'])}")
            self._display_history_summary()

    @staticmethod
    def _exercise_from_metadata(name: str, metadata: Optional[Dict[str, Any]]) -> Exercise:
        """Build Exercise object from embedding metadata."""
        metadata = metadata or {}

        muscle_groups = metadata.get("muscle_groups") or []
        if isinstance(muscle_groups, str):
            muscle_groups = [muscle_groups]
        else:
            muscle_groups = list(muscle_groups)

        equipment_list = metadata.get("equipment_list")
        if equipment_list is None:
            equipment_value = metadata.get("equipment", [])
            if isinstance(equipment_value, str):
                equipment_list = [equipment_value] if equipment_value else []
            elif isinstance(equipment_value, list):
                equipment_list = equipment_value
            else:
                equipment_list = []
        else:
            equipment_list = list(equipment_list)

        try:
            sets = int(metadata.get("sets", DEFAULT_EXERCISE_SETS))
        except (TypeError, ValueError):
            sets = DEFAULT_EXERCISE_SETS
        sets = max(1, sets)

        reps = metadata.get("reps") or DEFAULT_EXERCISE_REPS

        try:
            rest_seconds = int(metadata.get("rest_seconds", DEFAULT_EXERCISE_REST_SECONDS))
        except (TypeError, ValueError):
            rest_seconds = DEFAULT_EXERCISE_REST_SECONDS
        rest_seconds = max(0, rest_seconds)

        instructions = metadata.get("instructions") or DEFAULT_PLACEHOLDER_INSTRUCTIONS
        safety_tips = metadata.get("safety_tips")
        difficulty = metadata.get("difficulty") or DEFAULT_EXERCISE_DIFFICULTY

        return Exercise(
            name=name,
            muscle_groups=muscle_groups,
            equipment=equipment_list,
            difficulty=difficulty,
            sets=sets,
            reps=reps,
            rest_seconds=rest_seconds,
            instructions=instructions,
            safety_tips=safety_tips
        )


def display_menu():
    """Display main menu options."""
    print("\n" + "="*60)
    print("MAIN MENU")
    print("="*60)
    print("1. 🏋️  Generate Workout Plan")
    print("2. 🍽️  Generate Meal Plan")
    print("3. 🔍 Find Similar Exercises")
    print("4. 👤 View/Create User Profile")
    print("5. 🚪 Exit")
    print("="*60)


def get_user_input(
    prompt: str = "\nEnter your choice (1-5): ",
    valid_choices: Optional[Iterable[str]] = None,
) -> str:
    """Prompt for user input with optional validation."""

    normalized_choices = set(str(choice) for choice in valid_choices) if valid_choices else None

    while True:
        choice = input(prompt).strip()
        if not normalized_choices or choice in normalized_choices:
            return choice
        print("⚠️  Please select one of the available options.")


def create_user_profile() -> Optional[UserProfile]:
    """Interactive user profile creation with cancellation support."""

    print("\n" + "-" * 60)
    print("👤 CREATE USER PROFILE")
    print("-" * 60)
    print("Type 'back' at any prompt to return to the menu.\n")

    cancel_tokens = {"back", "cancel", "exit"}

    def prompt_number(
        prompt: str,
        cast,
        *,
        min_value: float,
        max_value: float,
        error_message: str,
    ):
        while True:
            raw_value = input(prompt).strip()
            if raw_value.lower() in cancel_tokens:
                return None
            try:
                value = cast(raw_value)
            except (TypeError, ValueError):
                print("⚠️  Please enter a valid number")
                continue
            if not (min_value <= value <= max_value):
                print(error_message)
                continue
            return value

    age = prompt_number(
        "Age: ",
        int,
        min_value=10,
        max_value=120,
        error_message="⚠️  Please enter a valid age between 10 and 120",
    )
    if age is None:
        return None

    weight = prompt_number(
        "Weight (kg): ",
        float,
        min_value=20,
        max_value=300,
        error_message="⚠️  Please enter a weight between 20 and 300 kg",
    )
    if weight is None:
        return None

    height = prompt_number(
        "Height (cm): ",
        float,
        min_value=100,
        max_value=250,
        error_message="⚠️  Please enter a height between 100 and 250 cm",
    )
    if height is None:
        return None

    while True:
        gender_input = input("Gender (M/F): ").strip()
        if gender_input.lower() in cancel_tokens:
            return None
        gender = gender_input.upper()
        if gender in {"M", "F"}:
            break
        print("⚠️  Please enter M or F")

    while True:
        level_input = input("Fitness level (beginner/intermediate/advanced): ").strip()
        if level_input.lower() in cancel_tokens:
            return None
        fitness_level = level_input.lower()
        if fitness_level in {"beginner", "intermediate", "advanced"}:
            break
        print("⚠️  Please enter beginner, intermediate, or advanced")

    print("\nFitness goals (comma-separated):")
    print("  Options: build_muscle, lose_weight, endurance, flexibility, general_fitness")
    goals_input = input("Goals: ").strip()
    if goals_input.lower() in cancel_tokens:
        return None
    goals = [g.strip() for g in goals_input.split(",") if g.strip()] or ["general_fitness"]

    equipment_input = input("\nAvailable equipment (comma-separated) [none]: ").strip()
    if equipment_input.lower() in cancel_tokens:
        return None
    equipment = (
        [e.strip() for e in equipment_input.split(",") if e.strip()]
        if equipment_input and equipment_input.lower() != "none"
        else []
    )

    injuries_input = input("Any injuries to consider (comma-separated) [none]: ").strip()
    if injuries_input.lower() in cancel_tokens:
        return None
    injuries = (
        [i.strip() for i in injuries_input.split(",") if i.strip()]
        if injuries_input and injuries_input.lower() != "none"
        else []
    )

    user_id = f"user_{uuid.uuid4().hex[:8]}"

    return UserProfile(
        user_id=user_id,
        age=age,
        weight_kg=weight,
        height_cm=height,
        gender=gender,
        fitness_level=fitness_level,
        goals=goals,
        equipment_available=equipment,
        injuries=injuries,
    )


def display_workout(workout: Workout):
    """
    Display formatted workout plan.
    
    Args:
        workout: Workout object to display
    """
    print("\n" + "="*60)
    print("💪 YOUR WORKOUT PLAN")
    print("="*60)
    print(f"\n📋 {workout.title}")
    print(f"⏱️  Duration: {workout.duration_minutes} minutes")
    print(f"📊 Difficulty: {workout.difficulty}")
    print(f"🎯 Target Muscles: {', '.join(workout.target_muscles)}")
    if workout.calories_estimate:
        print(f"🔥 Est. Calories: {workout.calories_estimate}")
    
    print("\n" + "-"*60)
    print("EXERCISES")
    print("-"*60)
    
    for i, exercise in enumerate(workout.exercises, 1):
        print(f"\n{i}. {exercise.name}")
        print(f"   💪 Muscles: {', '.join(exercise.muscle_groups)}")
        print(f"   📊 Difficulty: {exercise.difficulty}")
        print(f"   🔢 Sets: {exercise.sets}")
        print(f"   🔁 Reps: {exercise.reps}")
        print(f"   ⏸️  Rest: {exercise.rest_seconds}s")
        
        if exercise.equipment:
            print(f"   🏋️  Equipment: {', '.join(exercise.equipment)}")
        
        print(f"\n   📖 Instructions:")
        print(f"      {exercise.instructions}")
        
        if exercise.safety_tips:
            print(f"\n   ⚠️  Safety Tips:")
            print(f"      • {exercise.safety_tips}")
    
    if workout.warmup:
        print(f"\n🔥 Warm-up: {workout.warmup}")
    
    if workout.cooldown:
        print(f"❄️  Cool-down: {workout.cooldown}")
    
    print("\n" + "="*60)


def display_meal_plan(meal_plan: NutritionPlan):
    """
    Display formatted meal plan.
    
    Args:
        meal_plan: NutritionPlan object to display
    """
    print("\n" + "="*60)
    print("🍽️  YOUR MEAL PLAN")
    print("="*60)
    print(f"\n📅 Date: {meal_plan.date}")
    
    print("\n" + "-"*60)
    print("DAILY TOTALS")
    print("-"*60)
    print(f"🔥 Calories: {meal_plan.total_calories} kcal")
    print(f"🥩 Protein: {meal_plan.total_protein_g}g")
    print(f"🍞 Carbs: {meal_plan.total_carbs_g}g")
    print(f"🥑 Fats: {meal_plan.total_fats_g}g")
    
    print("\n" + "-"*60)
    print("MEALS")
    print("-"*60)
    
    for i, meal in enumerate(meal_plan.meals, 1):
        meal_emoji = {
            "breakfast": "🌅",
            "lunch": "☀️",
            "dinner": "🌙",
            "snack": "🍎"
        }.get(meal.meal_type, "🍽️")
        
        print(f"\n{meal_emoji} {i}. {meal.name} ({meal.meal_type.upper()})")
        print(f"   🔥 {meal.calories} kcal")
        print(f"   Protein: {meal.protein_g}g | Carbs: {meal.carbs_g}g | Fats: {meal.fats_g}g")
        print(f"   ⏱️  Prep time: {meal.prep_time_minutes} min")
        
        print(f"\n   🛒 Ingredients:")
        for ingredient in meal.ingredients:
            print(f"      • {ingredient}")
        
        print(f"\n   📖 Instructions:")
        print(f"      {meal.instructions}")
    
    if meal_plan.notes:
        print(f"\n📝 Notes: {meal_plan.notes}")
    
    print("\n" + "="*60)


def display_similar_exercises(exercises: List[Any]):
    """
    Display list of similar exercises.
    
    Args:
        exercises: List of Exercise objects or (Exercise, similarity) tuples
    """
    print("\n" + "="*60)
    print("🔍 SIMILAR EXERCISES")
    print("="*60)
    print(f"\nFound {len(exercises)} exercises:\n")
    
    for i, entry in enumerate(exercises, 1):
        similarity = None
        exercise = entry

        if isinstance(entry, tuple) and entry:
            exercise = entry[0]
            if len(entry) > 1 and isinstance(entry[1], (float, int)):
                similarity = float(entry[1])

        if not isinstance(exercise, Exercise):
            continue

        header = f"{i}. {exercise.name}"
        if similarity is not None:
            header += f" (Similarity: {similarity:.0%})"
        print(header)
        print(f"   💪 Muscles: {', '.join(exercise.muscle_groups)}")
        print(f"   📊 Difficulty: {exercise.difficulty}")
        
        if exercise.equipment:
            print(f"   🏋️  Equipment: {', '.join(exercise.equipment)}")
        else:
            print(f"   🏋️  Equipment: Bodyweight")
        
        print(f"   🔢 Sets: {exercise.sets}")
        print(f"   🔁 Reps: {exercise.reps}")
        instructions = exercise.instructions or DEFAULT_PLACEHOLDER_INSTRUCTIONS
        print(f"\n   📖 {instructions}\n")
    
    print("="*60)


def main():
    """Main entry point for CLI application."""
    initialize_logging()
    cli = GymAssistantCLI()
    cli.run()


if __name__ == "__main__":
    main()
