"""
Test suite for CLI interface (TDD RED phase first).
Tests interactive menu, user profile management, and service integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
import sys

from src.main import (
    GymAssistantCLI,
    display_menu,
    get_user_input,
    create_user_profile,
    display_workout,
    display_meal_plan,
    display_similar_exercises
)
from src.models import (
    UserProfile,
    Workout,
    Exercise,
    NutritionPlan,
    Meal,
    WorkoutRequest,
    NutritionRequest,
    ExerciseEmbedding
)


@pytest.fixture
def cli_storage_mock(monkeypatch):
    storage = MagicMock()
    storage.disabled = False
    storage.load_user_profile.return_value = None
    storage.get_history.return_value = {"workouts": [], "meal_plans": []}
    monkeypatch.setattr("src.main.Storage", lambda *args, **kwargs: storage)
    return storage


pytestmark = pytest.mark.usefixtures("cli_storage_mock")


@pytest.fixture
def sample_user():
    """Fixture for sample user profile"""
    return UserProfile(
        user_id="test123",
        age=28,
        weight_kg=75.0,
        height_cm=180.0,
        gender="M",
        fitness_level="intermediate",
        goals=["build_muscle"],
        equipment_available=["dumbbells", "barbell"],
        injuries=[]
    )


@pytest.fixture
def sample_workout():
    """Fixture for sample workout"""
    exercises = [
        Exercise(
            name="Barbell Bench Press",
            muscle_groups=["chest", "triceps"],
            equipment=["barbell"],
            difficulty="intermediate",
            sets=3,
            reps="8-12",
            rest_seconds=90,
            instructions="Lie on bench, lower bar to chest, press up",
            safety_tips="Use spotter, Keep feet flat"
        )
    ]
    return Workout(
        workout_id="workout123",
        title="Upper Body Strength",
        duration_minutes=45,
        exercises=exercises,
        warmup="5 min dynamic stretching",
        cooldown="5 min static stretching",
        difficulty="intermediate",
        target_muscles=["chest", "triceps"],
        calories_estimate=350
    )


@pytest.fixture
def sample_meal_plan():
    """Fixture for sample meal plan"""
    meals = [
        Meal(
            name="Protein Pancakes",
            meal_type="breakfast",
            calories=450,
            protein_g=30.0,
            carbs_g=50.0,
            fats_g=12.0,
            ingredients=["eggs", "protein powder", "oats"],
            instructions="Mix and cook",
            prep_time_minutes=15
        )
    ]
    return NutritionPlan(
        plan_id="plan123",
        date="2025-10-14",
        meals=meals,
        total_calories=450,
        total_protein_g=30.0,
        total_carbs_g=50.0,
        total_fats_g=12.0
    )


@pytest.fixture
def mock_services():
    """Fixture to mock all services"""
    with patch('src.main.WorkoutService') as mock_workout, \
         patch('src.main.NutritionService') as mock_nutrition, \
         patch('src.main.EmbeddingService') as mock_embedding:
        yield {
            'workout': mock_workout,
            'nutrition': mock_nutrition,
            'embedding': mock_embedding
        }


class TestCLIInitialization:
    """Test CLI initialization"""
    
    def test_cli_initialization(self):
        """Test CLI initializes with services"""
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        assert cli.workout_service is not None
        assert cli.nutrition_service is not None
        assert cli.embedding_service is not None
        assert cli.user_profile is None  # No user yet
    
    def test_cli_initialization_with_user(self, sample_user):
        """Test CLI can be initialized with existing user"""
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        assert cli.user_profile == sample_user

    def test_cli_loads_profile_from_storage(self, sample_user, cli_storage_mock):
        """CLI should load persisted profile when available."""
        cli_storage_mock.load_user_profile.return_value = sample_user

        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )

        assert cli.user_profile == sample_user
        cli_storage_mock.load_user_profile.assert_called_once()


class TestMenuDisplay:
    """Test menu display functions"""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_menu_shows_options(self, mock_stdout):
        """Test menu displays all options"""
        display_menu()
        output = mock_stdout.getvalue()
        
        assert "1" in output
        assert "2" in output
        assert "Workout" in output or "workout" in output
        assert "Meal" in output or "meal" in output or "Nutrition" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_menu_includes_exit(self, mock_stdout):
        """Test menu includes exit option"""
        display_menu()
        output = mock_stdout.getvalue()
        
        assert "Exit" in output or "exit" in output or "Quit" in output


class TestUserInput:
    """Test user input handling"""
    
    @patch('builtins.input', return_value='1')
    def test_get_user_input_returns_choice(self, mock_input):
        """Test getting user menu choice"""
        choice = get_user_input()
        assert choice == '1'
    
    @patch('builtins.input', return_value='invalid')
    def test_get_user_input_handles_invalid(self, mock_input):
        """Test handling invalid input"""
        choice = get_user_input()
        assert isinstance(choice, str)

    @patch('builtins.input', side_effect=['invalid', '2'])
    def test_get_user_input_reprompts_for_valid_choice(self, mock_input):
        """Test validated menu input reprompts until selection is valid"""
        choice = get_user_input(valid_choices={'1', '2'})
        assert choice == '2'


class TestUserProfileCreation:
    """Test user profile creation"""
    
    @patch('builtins.input', side_effect=['28', '75', '180', 'M', 'intermediate', 'build_muscle', 'dumbbells,barbell', ''])
    def test_create_user_profile_interactive(self, mock_input):
        """Test creating user profile interactively"""
        profile = create_user_profile()
        
        assert isinstance(profile, UserProfile)
        assert profile.age == 28
        assert profile.weight_kg == 75.0
        assert profile.height_cm == 180.0
        assert profile.gender == "M"
        assert profile.fitness_level == "intermediate"
    
    @patch('builtins.input', side_effect=['invalid', '25', '70', '175', 'F', 'beginner', 'lose_weight', '', ''])
    def test_create_user_profile_handles_invalid_age(self, mock_input):
        """Test profile creation handles invalid age input"""
        profile = create_user_profile()
        
        # Should retry and get valid age
        assert profile.age == 25
    
    @patch('builtins.input', side_effect=['30', '80', '170', 'M', 'advanced', 'endurance', 'running', 'knee'])
    def test_create_user_profile_with_injuries(self, mock_input):
        """Test profile creation includes injuries"""
        profile = create_user_profile()
        
        assert isinstance(profile.injuries, list)

    @patch('builtins.input', side_effect=['back'])
    def test_create_user_profile_allows_cancellation(self, mock_input):
        """Test profile creation can be cancelled with back keyword"""
        profile = create_user_profile()
        assert profile is None


class TestWorkoutGeneration:
    """Test workout generation workflow"""
    
    def test_cli_generate_workout_requires_profile(self):
        """Test workout generation requires user profile"""
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        with pytest.raises(ValueError) as exc_info:
            cli.generate_workout()
        
        assert "profile" in str(exc_info.value).lower()
    
    @patch('builtins.input', side_effect=['strength', '45', 'chest,arms'])
    def test_cli_generate_workout_with_profile(self, mock_input, sample_user, sample_workout, cli_storage_mock):
        """Test workout generation with valid profile"""
        mock_workout_service = Mock()
        mock_workout_service.generate_workout.return_value = sample_workout
        
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=mock_workout_service,
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        workout = cli.generate_workout()
        
        assert workout == sample_workout
        assert mock_workout_service.generate_workout.called
        cli_storage_mock.record_workout_summary.assert_called_once_with(sample_workout)
    
    @patch('builtins.input', side_effect=['cardio', '30', ''])
    def test_cli_generate_workout_builds_request(self, mock_input, sample_user):
        """Test CLI builds proper workout request"""
        mock_workout_service = Mock()
        
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=mock_workout_service,
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        cli.generate_workout()
        
        # Check that service was called with WorkoutRequest
        call_args = mock_workout_service.generate_workout.call_args
        assert call_args is not None
        request = call_args[0][0]
        assert isinstance(request, WorkoutRequest)
        assert request.user_profile == sample_user


class TestMealPlanGeneration:
    """Test meal plan generation workflow"""
    
    def test_cli_generate_meal_plan_requires_profile(self):
        """Test meal plan generation requires user profile"""
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        with pytest.raises(ValueError) as exc_info:
            cli.generate_meal_plan()
        
        assert "profile" in str(exc_info.value).lower()
    
    @patch('builtins.input', side_effect=['none', 'any', 'medium'])
    def test_cli_generate_meal_plan_with_profile(self, mock_input, sample_user, sample_meal_plan, cli_storage_mock):
        """Test meal plan generation with valid profile"""
        mock_nutrition_service = Mock()
        mock_nutrition_service.generate_meal_plan.return_value = sample_meal_plan
        
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=Mock(),
            nutrition_service=mock_nutrition_service,
            embedding_service=Mock()
        )
        
        plan = cli.generate_meal_plan()
        
        assert plan == sample_meal_plan
        assert mock_nutrition_service.generate_meal_plan.called
        cli_storage_mock.record_meal_plan_summary.assert_called_once_with(sample_meal_plan)
    
    @patch('builtins.input', side_effect=['vegetarian', 'Mediterranean', 'low'])
    def test_cli_generate_meal_plan_with_preferences(self, mock_input, sample_user):
        """Test meal plan generation with dietary preferences"""
        mock_nutrition_service = Mock()
        
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=Mock(),
            nutrition_service=mock_nutrition_service,
            embedding_service=Mock()
        )
        
        cli.generate_meal_plan()
        
        call_args = mock_nutrition_service.generate_meal_plan.call_args
        request = call_args[0][0]
        assert isinstance(request, NutritionRequest)
        assert request.user_profile == sample_user


class TestExerciseSearch:
    """Test exercise similarity search"""
    
    @patch('builtins.input', side_effect=['push ups', '5'])
    def test_cli_find_similar_exercises(self, mock_input):
        """Test finding similar exercises"""
        metadata = {
            "muscle_groups": ["chest", "triceps"],
            "equipment_list": ["bodyweight"],
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "sets": 3,
            "reps": "8-12",
            "rest_seconds": 60,
            "instructions": "Push-up with hands close together",
            "safety_tips": "Keep core tight"
        }

        mock_embedding_service = Mock()
        mock_embedding_service.find_similar_exercises.return_value = [("Diamond Push-ups", 0.92)]
        mock_embedding_service.get_exercise_details.return_value = ExerciseEmbedding(
            exercise_name="Diamond Push-ups",
            description="Diamond push-up variation",
            embedding=[0.1, 0.2],
            metadata=metadata
        )
        
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=mock_embedding_service
        )
        
        results = cli.find_similar_exercises()
        
        assert len(results) == 1
        exercise, similarity = results[0]
        assert isinstance(exercise, Exercise)
        assert exercise.name == "Diamond Push-ups"
        assert exercise.instructions.startswith("Push-up")
        assert pytest.approx(similarity, rel=1e-3) == 0.92
        mock_embedding_service.get_exercise_details.assert_called_with("Diamond Push-ups")
        assert mock_embedding_service.find_similar_exercises.called
    
    @patch('builtins.input', side_effect=['bench press', '3'])
    def test_cli_find_similar_with_filters(self, mock_input):
        """Test finding similar exercises with equipment filter"""
        mock_embedding_service = Mock()
        mock_embedding_service.find_similar_exercises.return_value = []
        mock_embedding_service.get_exercise_details.return_value = None
        
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=mock_embedding_service
        )
        
        cli.find_similar_exercises()
        
        # Should call embedding service
        assert mock_embedding_service.find_similar_exercises.called

    @patch('builtins.input', side_effect=['unknown move', '2'])
    def test_cli_find_similar_handles_missing_metadata(self, mock_input):
        """Test search handles exercises absent from metadata database"""
        mock_embedding_service = Mock()
        mock_embedding_service.find_similar_exercises.return_value = [("Unknown Move", 0.5)]
        mock_embedding_service.get_exercise_details.return_value = None

        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=mock_embedding_service
        )

        results = cli.find_similar_exercises()

        assert len(results) == 1
        exercise, similarity = results[0]
        assert exercise.name == "Unknown Move"
        assert exercise.instructions == "Instructions not available."
        assert pytest.approx(similarity, rel=1e-3) == 0.5
        mock_embedding_service.get_exercise_details.assert_called_with("Unknown Move")


class TestDisplayFunctions:
    """Test output display functions"""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_workout(self, mock_stdout, sample_workout):
        """Test workout display formatting"""
        display_workout(sample_workout)
        output = mock_stdout.getvalue()
        
        assert sample_workout.title in output
        assert str(sample_workout.duration_minutes) in output
        assert sample_workout.exercises[0].name in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_meal_plan(self, mock_stdout, sample_meal_plan):
        """Test meal plan display formatting"""
        display_meal_plan(sample_meal_plan)
        output = mock_stdout.getvalue()
        
        assert sample_meal_plan.meals[0].name in output
        assert str(sample_meal_plan.total_calories) in output
        assert str(sample_meal_plan.total_protein_g) in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_similar_exercises(self, mock_stdout):
        """Test exercise list display"""
        exercises = [
            Exercise(
                name="Test Exercise",
                muscle_groups=["chest"],
                equipment=["dumbbells"],
                difficulty="beginner",
                sets=3,
                reps="10-12",
                rest_seconds=60,
                instructions="Do the thing",
                safety_tips="Be safe"
            )
        ]
        
        display_similar_exercises(exercises)
        output = mock_stdout.getvalue()
        
        assert "Test Exercise" in output
        assert "chest" in output


class TestMainLoop:
    """Test main CLI loop"""
    
    @patch('builtins.input', side_effect=['n', '5'])  # Don't create profile, then exit
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_run_exits_gracefully(self, mock_stdout, mock_input):
        """Test CLI exits on exit command"""
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        # Should not raise exception
        cli.run()
    
    @patch('builtins.input', side_effect=['4', '5'])  # View profile, then exit
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_run_displays_profile(self, mock_stdout, mock_input, sample_user):
        """Test viewing user profile"""
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        cli.run()
        
        output = mock_stdout.getvalue()
        # Should display some user info
        assert str(sample_user.age) in output or "Profile" in output


class TestErrorHandling:
    """Test CLI error handling"""
    
    @patch('builtins.input', side_effect=['n', '1', '5'])  # Don't create profile, try workout, exit
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_handles_missing_profile_gracefully(self, mock_stdout, mock_input):
        """Test CLI handles missing profile error"""
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        # Should not crash
        cli.run()
        
        output = mock_stdout.getvalue()
        # Should show error message
        assert "profile" in output.lower() or "create" in output.lower()
    
    def test_cli_handles_service_errors(self, sample_user):
        """Test CLI handles service errors gracefully"""
        mock_workout_service = Mock()
        mock_workout_service.generate_workout.side_effect = Exception("API Error")
        
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=mock_workout_service,
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        with patch('builtins.input', side_effect=['strength', '30', '']):
            with patch('sys.stdout', new_callable=StringIO):
                # Should not crash - returns None on error
                result = cli.generate_workout()
                assert result is None


class TestProfileManagement:
    """Test user profile management"""
    
    @patch('builtins.input', return_value='n')
    def test_cli_view_profile_without_profile(self, mock_input):
        """Test viewing profile when none exists"""
        cli = GymAssistantCLI(
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli.view_profile()
            output = mock_stdout.getvalue()
            
            assert "no profile" in output.lower() or "create" in output.lower()
    
    def test_cli_view_profile_with_profile(self, sample_user):
        """Test viewing existing profile"""
        cli = GymAssistantCLI(
            user_profile=sample_user,
            workout_service=Mock(),
            nutrition_service=Mock(),
            embedding_service=Mock()
        )
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli.view_profile()
            output = mock_stdout.getvalue()
            
            assert str(sample_user.age) in output
            assert str(sample_user.weight_kg) in output


class TestIntegration:
    """Integration tests for full workflows"""
    
    @patch('builtins.input', side_effect=[
        '25', '70', '170', 'F', 'beginner', 'lose_weight', '', '',  # Create profile
        'cardio', '30', ''  # Generate workout
    ])
    def test_full_workflow_create_profile_and_workout(self, mock_input):
        """Test complete workflow: create profile and generate workout"""
        # Mock the workout service
        sample_workout = Workout(
            workout_id="test",
            title="Cardio Blast",
            duration_minutes=30,
            exercises=[],
            warmup="5 min",
            cooldown="5 min",
            difficulty="beginner",
            target_muscles=["legs"],
            calories_estimate=250
        )
        
        mock_workout_service = Mock()
        mock_workout_service.generate_workout.return_value = sample_workout
        
        with patch('sys.stdout', new_callable=StringIO):
            # Create profile first
            profile = create_user_profile()
            
            # Create CLI with profile
            cli = GymAssistantCLI(
                user_profile=profile,
                workout_service=mock_workout_service,
                nutrition_service=Mock(),
                embedding_service=Mock()
            )
            
            # Generate workout
            workout = cli.generate_workout()
            
            assert profile is not None
            assert workout == sample_workout


class TestInputValidation:
    """Test input validation and sanitization"""
    
    @patch('builtins.input', side_effect=[
        'abc', '  ', '-5', '25',  # Age with retries
        '70',  # Weight
        '175',  # Height
        'M',  # Gender
        'beginner',  # Fitness level
        'lose_weight',  # Goals
        '',  # Equipment
        ''  # Injuries
    ])
    def test_age_input_validation(self, mock_input):
        """Test age input validates and retries"""
        with patch('sys.stdout', new_callable=StringIO):
            profile = create_user_profile()
            
            # Should eventually get valid age
            assert profile.age == 25
    
    @patch('builtins.input', side_effect=['25', 'abc', '70'])
    def test_weight_input_validation(self, mock_input):
        """Test weight input validates and retries"""
        # Test would validate weight is float
        pass  # Implementation will handle this


class TestMacroDisplay:
    """Test macro nutrient display"""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_macros_in_meal_plan(self, mock_stdout, sample_meal_plan):
        """Test meal plan displays macro breakdown"""
        display_meal_plan(sample_meal_plan)
        output = mock_stdout.getvalue()
        
        # Should show macros
        assert "protein" in output.lower() or str(sample_meal_plan.total_protein_g) in output
        assert "carbs" in output.lower() or str(sample_meal_plan.total_carbs_g) in output
        assert "fats" in output.lower() or str(sample_meal_plan.total_fats_g) in output
