"""
Test suite for WorkoutService (TDD RED phase first).
Service orchestrates workout generation using client and parser.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from src.workout_service import WorkoutService
from src.models import (
    UserProfile,
    WorkoutRequest,
    Workout,
    Exercise,
    GymAssistantError
)


@pytest.fixture
def sample_user():
    """Fixture for a standard test user"""
    return UserProfile(
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


@pytest.fixture
def mock_workout_json():
    """Fixture for mock AI workout response"""
    return {
        "title": "Upper Body Strength",
        "duration_minutes": 45,
        "exercises": [
            {
                "name": "Push-ups",
                "muscle_groups": ["chest", "triceps"],
                "equipment": [],
                "difficulty": "intermediate",
                "sets": 3,
                "reps": "12-15",
                "rest_seconds": 60,
                "instructions": "Standard push-up form",
                "safety_tips": "Keep core engaged"
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


class TestWorkoutServiceInitialization:
    """Test service initialization"""
    
    def test_service_initialization(self):
        """Test service initializes with client"""
        mock_client = Mock()
        service = WorkoutService(mock_client)
        assert service.client == mock_client
    
    def test_service_initialization_without_client(self):
        """Test service can initialize without explicit client"""
        with patch('src.workout_service.GymAssistantClient'):
            service = WorkoutService()
            assert service.client is not None


class TestWorkoutGeneration:
    """Test workout generation functionality"""
    
    def test_generate_workout_success(self, sample_user, mock_workout_json):
        """Test successful workout generation"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_workout_json)
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45,
            target_muscles=["chest", "back"]
        )
        
        workout = service.generate_workout(request)
        
        assert isinstance(workout, Workout)
        assert workout.title == "Upper Body Strength"
        assert workout.duration_minutes == 45
        assert len(workout.exercises) == 2
        assert mock_client.generate_completion.called
    
    def test_generate_workout_builds_correct_prompt(self, sample_user):
        """Test that service builds appropriate prompt for AI"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Workout",
            "duration_minutes": 30,
            "exercises": [{
                "name": "Squats",
                "muscle_groups": ["legs"],
                "equipment": [],
                "difficulty": "intermediate",
                "sets": 3,
                "reps": "12",
                "rest_seconds": 60,
                "instructions": "Standard squat"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45,
            target_muscles=["chest"]
        )
        
        service.generate_workout(request)
        
        # Check that prompt was passed to client
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        # Verify key information is in prompt
        assert "45" in prompt or "45-minute" in prompt.lower()
        assert "strength" in prompt.lower()
        assert "intermediate" in prompt.lower()
        assert str(sample_user.age) in prompt
        assert "chest" in prompt.lower()
    
    def test_generate_workout_includes_user_profile(self, sample_user):
        """Test prompt includes user profile details"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Workout",
            "duration_minutes": 30,
            "exercises": [{
                "name": "Exercise",
                "muscle_groups": ["chest"],
                "equipment": [],
                "difficulty": "intermediate",
                "sets": 3,
                "reps": "10",
                "rest_seconds": 60,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="cardio",
            duration_minutes=30
        )
        
        service.generate_workout(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        # Check user details in prompt
        assert str(sample_user.age) in prompt
        assert str(sample_user.weight_kg) in prompt
        assert str(sample_user.height_cm) in prompt
        assert sample_user.fitness_level in prompt.lower()
    
    def test_generate_workout_respects_equipment(self, sample_user):
        """Test prompt includes available equipment"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Workout",
            "duration_minutes": 30,
            "exercises": [{
                "name": "Exercise",
                "muscle_groups": ["chest"],
                "equipment": ["dumbbells"],
                "difficulty": "intermediate",
                "sets": 3,
                "reps": "10",
                "rest_seconds": 60,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=30
        )
        
        service.generate_workout(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        # Check equipment is mentioned
        assert "dumbbells" in prompt.lower()
        assert "resistance" in prompt.lower() or "band" in prompt.lower()
    
    def test_generate_workout_respects_injuries(self, sample_user):
        """Test prompt includes injury restrictions"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Workout",
            "duration_minutes": 30,
            "exercises": [{
                "name": "Exercise",
                "muscle_groups": ["chest"],
                "equipment": [],
                "difficulty": "intermediate",
                "sets": 3,
                "reps": "10",
                "rest_seconds": 60,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=30
        )
        
        service.generate_workout(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        # Check injuries are mentioned
        assert "knee" in prompt.lower()
        assert "avoid" in prompt.lower() or "injury" in prompt.lower()


class TestWorkoutTypes:
    """Test different workout types"""
    
    def test_generate_strength_workout(self, sample_user):
        """Test generating strength training workout"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Strength Training",
            "duration_minutes": 45,
            "exercises": [{
                "name": "Bench Press",
                "muscle_groups": ["chest"],
                "equipment": ["dumbbells"],
                "difficulty": "intermediate",
                "sets": 4,
                "reps": "8-10",
                "rest_seconds": 90,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        workout = service.generate_workout(request)
        assert "strength" in workout.title.lower() or len(workout.exercises) > 0
    
    def test_generate_cardio_workout(self, sample_user):
        """Test generating cardio workout"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Cardio Blast",
            "duration_minutes": 30,
            "exercises": [{
                "name": "Jumping Jacks",
                "muscle_groups": ["cardio"],
                "equipment": [],
                "difficulty": "beginner",
                "sets": 3,
                "reps": "30 seconds",
                "rest_seconds": 30,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="cardio",
            duration_minutes=30
        )
        
        workout = service.generate_workout(request)
        assert workout.duration_minutes == 30
    
    def test_generate_hiit_workout(self, sample_user):
        """Test generating HIIT workout"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "HIIT Session",
            "duration_minutes": 20,
            "exercises": [{
                "name": "Burpees",
                "muscle_groups": ["full_body"],
                "equipment": [],
                "difficulty": "advanced",
                "sets": 4,
                "reps": "20 seconds",
                "rest_seconds": 10,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="hiit",
            duration_minutes=20
        )
        
        workout = service.generate_workout(request)
        assert workout.duration_minutes == 20


class TestPromptBuilding:
    """Test prompt building logic"""
    
    def test_build_workout_prompt(self, sample_user):
        """Test prompt builder creates valid prompt"""
        service = WorkoutService(Mock())
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45,
            target_muscles=["chest", "back"]
        )
        
        prompt = service._build_workout_prompt(request)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "workout" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt
    
    def test_build_prompt_includes_goals(self, sample_user):
        """Test prompt includes user goals"""
        service = WorkoutService(Mock())
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        prompt = service._build_workout_prompt(request)
        
        # Check goals are mentioned
        assert "build_muscle" in prompt or "muscle" in prompt.lower()
        assert "endurance" in prompt.lower()
    
    def test_build_prompt_requests_json(self, sample_user):
        """Test prompt requests JSON format"""
        service = WorkoutService(Mock())
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        prompt = service._build_workout_prompt(request)
        
        # Should request JSON response
        assert "json" in prompt.lower()


class TestErrorHandling:
    """Test error handling in workout service"""
    
    def test_generate_workout_handles_client_error(self, sample_user):
        """Test service handles client errors gracefully"""
        mock_client = Mock()
        mock_client.generate_completion.side_effect = GymAssistantError(
            "API error", "api_error"
        )
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        with pytest.raises(GymAssistantError) as exc_info:
            service.generate_workout(request)
        
        assert exc_info.value.error_type == "api_error"
    
    def test_generate_workout_handles_invalid_json(self, sample_user):
        """Test service handles invalid JSON response"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = "This is not JSON"
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        with pytest.raises(GymAssistantError) as exc_info:
            service.generate_workout(request)
        
        assert "parser" in exc_info.value.error_type.lower()
    
    def test_generate_workout_validates_request(self):
        """Test service validates workout request"""
        service = WorkoutService(Mock())
        
        with pytest.raises((GymAssistantError, TypeError, AttributeError)):
            service.generate_workout(None)


class TestSystemMessage:
    """Test system message configuration"""
    
    def test_service_uses_system_message(self, sample_user):
        """Test service provides system message to client"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Workout",
            "duration_minutes": 30,
            "exercises": [{
                "name": "Exercise",
                "muscle_groups": ["chest"],
                "equipment": [],
                "difficulty": "intermediate",
                "sets": 3,
                "reps": "10",
                "rest_seconds": 60,
                "instructions": "Test"
            }],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=30
        )
        
        service.generate_workout(request)
        
        # Check system_message was passed
        call_args = mock_client.generate_completion.call_args
        assert "system_message" in call_args.kwargs
        system_msg = call_args.kwargs["system_message"]
        assert "trainer" in system_msg.lower() or "fitness" in system_msg.lower()


class TestWorkoutValidation:
    """Test workout output validation"""
    
    def test_service_validates_workout_output(self, sample_user):
        """Test service validates generated workout"""
        mock_client = Mock()
        # Return invalid workout (no exercises)
        mock_client.generate_completion.return_value = json.dumps({
            "title": "Bad Workout",
            "duration_minutes": 30,
            "exercises": [],
            "warmup": "Warmup",
            "cooldown": "Cooldown"
        })
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=30
        )
        
        # Should raise error for invalid workout
        with pytest.raises(GymAssistantError):
            service.generate_workout(request)
    
    def test_service_validates_duration(self, sample_user, mock_workout_json):
        """Test service checks duration matches request"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_workout_json)
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        workout = service.generate_workout(request)
        
        # Duration should match or be close
        assert abs(workout.duration_minutes - request.duration_minutes) <= 10


class TestModelConfiguration:
    """Test AI model configuration"""
    
    def test_service_uses_specified_model(self, sample_user, mock_workout_json):
        """Test service uses model from request"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_workout_json)
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45,
            model="gpt-4o-mini"
        )
        
        service.generate_workout(request)
        
        call_args = mock_client.generate_completion.call_args
        assert call_args.kwargs.get("model") == "gpt-4o-mini"
    
    def test_service_uses_default_model(self, sample_user, mock_workout_json):
        """Test service uses default model if not specified"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_workout_json)
        
        service = WorkoutService(mock_client)
        request = WorkoutRequest(
            user_profile=sample_user,
            workout_type="strength",
            duration_minutes=45
        )
        
        service.generate_workout(request)
        
        call_args = mock_client.generate_completion.call_args
        model = call_args.kwargs.get("model", "gpt-4o")
        assert model in ["gpt-4o", "gpt-4o-mini"]
