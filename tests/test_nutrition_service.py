"""
Test suite for NutritionService (TDD RED phase first).
Service orchestrates meal plan generation with macro calculations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from src.nutrition_service import NutritionService
from src.models import (
    UserProfile,
    NutritionRequest,
    NutritionPlan,
    Meal,
    GymAssistantError
)


@pytest.fixture
def sample_user_bulking():
    """Fixture for a user trying to build muscle"""
    return UserProfile(
        user_id="test123",
        age=25,
        weight_kg=75.0,
        height_cm=180.0,
        gender="M",
        fitness_level="intermediate",
        goals=["build_muscle"],
        equipment_available=["dumbbells"]
    )


@pytest.fixture
def sample_user_cutting():
    """Fixture for a user trying to lose weight"""
    return UserProfile(
        user_id="test456",
        age=30,
        weight_kg=85.0,
        height_cm=175.0,
        gender="F",
        fitness_level="beginner",
        goals=["lose_weight"],
        equipment_available=[]
    )


@pytest.fixture
def mock_nutrition_json():
    """Fixture for mock AI nutrition response"""
    return {
        "date": "2025-10-14",
        "meals": [
            {
                "name": "Protein Pancakes with Berries",
                "meal_type": "breakfast",
                "calories": 450,
                "protein_g": 30.0,
                "carbs_g": 50.0,
                "fats_g": 12.0,
                "ingredients": ["eggs", "protein powder", "oats", "berries"],
                "instructions": "Mix ingredients, cook pancakes, top with berries",
                "prep_time_minutes": 15
            },
            {
                "name": "Grilled Chicken with Rice and Vegetables",
                "meal_type": "lunch",
                "calories": 600,
                "protein_g": 50.0,
                "carbs_g": 65.0,
                "fats_g": 15.0,
                "ingredients": ["chicken breast", "brown rice", "broccoli", "olive oil"],
                "instructions": "Grill chicken, cook rice, steam vegetables",
                "prep_time_minutes": 30
            },
            {
                "name": "Salmon with Sweet Potato",
                "meal_type": "dinner",
                "calories": 550,
                "protein_g": 45.0,
                "carbs_g": 55.0,
                "fats_g": 18.0,
                "ingredients": ["salmon", "sweet potato", "asparagus"],
                "instructions": "Bake salmon and sweet potato, steam asparagus",
                "prep_time_minutes": 35
            }
        ],
        "notes": "High protein for muscle building"
    }


class TestNutritionServiceInitialization:
    """Test service initialization"""
    
    def test_service_initialization(self):
        """Test service initializes with client"""
        mock_client = Mock()
        service = NutritionService(mock_client)
        assert service.client == mock_client
    
    def test_service_initialization_without_client(self):
        """Test service can initialize without explicit client"""
        with patch('src.nutrition_service.GymAssistantClient'):
            service = NutritionService()
            assert service.client is not None


class TestMacroCalculation:
    """Test macro nutrient calculation logic"""
    
    def test_calculate_macros_for_muscle_building(self, sample_user_bulking):
        """Test macro calculation for muscle building goal"""
        service = NutritionService(Mock())
        
        macros = service.calculate_macros(sample_user_bulking)
        
        assert "calories" in macros
        assert "protein_g" in macros
        assert "carbs_g" in macros
        assert "fats_g" in macros
        
        # Muscle building should have calorie surplus
        assert macros["calories"] > 2000
        # High protein for muscle building
        assert macros["protein_g"] > 100
    
    def test_calculate_macros_for_weight_loss(self, sample_user_cutting):
        """Test macro calculation for weight loss goal"""
        service = NutritionService(Mock())
        
        macros = service.calculate_macros(sample_user_cutting)
        
        # Weight loss should have calorie deficit
        assert macros["calories"] < 2500
        # Still adequate protein to preserve muscle
        assert macros["protein_g"] > 80
    
    def test_calculate_macros_for_maintenance(self):
        """Test macro calculation for maintenance goal"""
        user = UserProfile(
            user_id="test789",
            age=28,
            weight_kg=70.0,
            height_cm=170.0,
            gender="F",
            fitness_level="intermediate",
            goals=["endurance"]  # Not muscle building or weight loss
        )
        
        service = NutritionService(Mock())
        macros = service.calculate_macros(user)
        
        # Maintenance calories
        assert 1800 <= macros["calories"] <= 2500
        assert macros["protein_g"] > 60
    
    def test_calculate_macros_uses_bmr(self, sample_user_bulking):
        """Test macro calculation uses BMR formula"""
        service = NutritionService(Mock())
        
        macros = service.calculate_macros(sample_user_bulking)
        
        # Verify reasonable calorie range based on user stats
        # For 75kg, 180cm, 25yo male building muscle, expect 2500-3500 calories
        assert 2500 <= macros["calories"] <= 3500
    
    def test_calculate_macros_protein_adequate(self, sample_user_bulking):
        """Test protein recommendation is adequate for goals"""
        service = NutritionService(Mock())
        
        macros = service.calculate_macros(sample_user_bulking)
        
        # Protein should be ~2g per kg bodyweight for muscle building
        expected_protein = sample_user_bulking.weight_kg * 2.0
        assert macros["protein_g"] >= expected_protein * 0.9  # Allow 10% variance
    
    def test_macros_sum_to_calories(self, sample_user_bulking):
        """Test that macro calories approximately sum to total calories"""
        service = NutritionService(Mock())
        
        macros = service.calculate_macros(sample_user_bulking)
        
        # Calculate calories from macros (protein=4, carbs=4, fats=9 cal/g)
        macro_calories = (
            macros["protein_g"] * 4 +
            macros["carbs_g"] * 4 +
            macros["fats_g"] * 9
        )
        
        # Should be within 10% of target
        assert abs(macro_calories - macros["calories"]) <= macros["calories"] * 0.1


class TestNutritionPlanGeneration:
    """Test nutrition plan generation"""
    
    def test_generate_meal_plan_success(self, sample_user_bulking, mock_nutrition_json):
        """Test successful meal plan generation"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_nutrition_json)
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            dietary_restrictions=None,
            budget_level="medium"
        )
        
        plan = service.generate_meal_plan(request)
        
        assert isinstance(plan, NutritionPlan)
        assert len(plan.meals) == 3
        assert plan.total_calories > 0
        assert mock_client.generate_completion.called
    
    def test_generate_meal_plan_builds_correct_prompt(self, sample_user_bulking):
        """Test that service builds appropriate prompt for AI"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Test Meal",
                "meal_type": "lunch",
                "calories": 500,
                "protein_g": 40.0,
                "carbs_g": 50.0,
                "fats_g": 15.0,
                "ingredients": ["food"],
                "instructions": "Cook",
                "prep_time_minutes": 20
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        service.generate_meal_plan(request)
        
        # Check that prompt was passed to client
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        # Verify key information is in prompt
        assert "meal" in prompt.lower() or "nutrition" in prompt.lower()
        assert str(sample_user_bulking.age) in prompt
    
    def test_generate_meal_plan_includes_macros(self, sample_user_bulking, mock_nutrition_json):
        """Test prompt includes calculated macro targets"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_nutrition_json)
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        # Should include macro targets
        assert "protein" in prompt.lower()
        assert "calor" in prompt.lower()


class TestDietaryRestrictions:
    """Test handling of dietary restrictions"""
    
    def test_generate_plan_with_vegetarian(self, sample_user_bulking):
        """Test generating vegetarian meal plan"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Veggie Meal",
                "meal_type": "lunch",
                "calories": 500,
                "protein_g": 30.0,
                "carbs_g": 60.0,
                "fats_g": 15.0,
                "ingredients": ["tofu", "vegetables"],
                "instructions": "Cook",
                "prep_time_minutes": 20
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            dietary_restrictions=["vegetarian"],
            budget_level="medium"
        )
        
        plan = service.generate_meal_plan(request)
        
        # Check prompt mentioned vegetarian
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        assert "vegetarian" in prompt.lower()
    
    def test_generate_plan_with_multiple_restrictions(self, sample_user_cutting):
        """Test generating plan with multiple dietary restrictions"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Special Meal",
                "meal_type": "dinner",
                "calories": 400,
                "protein_g": 35.0,
                "carbs_g": 40.0,
                "fats_g": 12.0,
                "ingredients": ["chicken", "rice"],
                "instructions": "Cook",
                "prep_time_minutes": 25
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_cutting,
            dietary_restrictions=["gluten-free", "dairy-free"],
            budget_level="low"
        )
        
        plan = service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        assert "gluten-free" in prompt.lower() or "gluten" in prompt.lower()
        assert "dairy-free" in prompt.lower() or "dairy" in prompt.lower()


class TestCuisinePreferences:
    """Test handling of cuisine preferences"""
    
    def test_generate_plan_with_cuisine_preferences(self, sample_user_bulking):
        """Test generating plan with specific cuisine preferences"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Mediterranean Meal",
                "meal_type": "lunch",
                "calories": 550,
                "protein_g": 40.0,
                "carbs_g": 55.0,
                "fats_g": 18.0,
                "ingredients": ["fish", "vegetables"],
                "instructions": "Cook",
                "prep_time_minutes": 30
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            cuisine_preferences=["Mediterranean", "Asian"],
            budget_level="high"
        )
        
        plan = service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        assert "mediterranean" in prompt.lower() or "asian" in prompt.lower()


class TestBudgetLevels:
    """Test budget level considerations"""
    
    def test_generate_plan_low_budget(self, sample_user_cutting):
        """Test generating budget-friendly meal plan"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Budget Meal",
                "meal_type": "lunch",
                "calories": 450,
                "protein_g": 35.0,
                "carbs_g": 50.0,
                "fats_g": 12.0,
                "ingredients": ["rice", "beans", "chicken"],
                "instructions": "Cook",
                "prep_time_minutes": 25
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_cutting,
            budget_level="low"
        )
        
        plan = service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        assert "budget" in prompt.lower() or "affordable" in prompt.lower() or "low" in prompt.lower()
    
    def test_generate_plan_high_budget(self, sample_user_bulking):
        """Test generating premium meal plan"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Premium Meal",
                "meal_type": "dinner",
                "calories": 600,
                "protein_g": 50.0,
                "carbs_g": 60.0,
                "fats_g": 20.0,
                "ingredients": ["steak", "quinoa"],
                "instructions": "Cook",
                "prep_time_minutes": 40
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="high"
        )
        
        service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        prompt = call_args.kwargs.get("prompt", call_args[0][0] if call_args[0] else "")
        
        assert "high" in prompt.lower() or "premium" in prompt.lower()


class TestPromptBuilding:
    """Test prompt building logic"""
    
    def test_build_nutrition_prompt(self, sample_user_bulking):
        """Test prompt builder creates valid prompt"""
        service = NutritionService(Mock())
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        macros = service.calculate_macros(sample_user_bulking)
        
        prompt = service._build_nutrition_prompt(request, macros)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "meal" in prompt.lower() or "nutrition" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt
    
    def test_build_prompt_includes_user_goals(self, sample_user_bulking):
        """Test prompt includes user fitness goals"""
        service = NutritionService(Mock())
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        macros = service.calculate_macros(sample_user_bulking)
        
        prompt = service._build_nutrition_prompt(request, macros)
        
        assert "build_muscle" in prompt or "muscle" in prompt.lower()
    
    def test_build_prompt_requests_json(self, sample_user_bulking):
        """Test prompt requests JSON format"""
        service = NutritionService(Mock())
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        macros = service.calculate_macros(sample_user_bulking)
        
        prompt = service._build_nutrition_prompt(request, macros)
        
        assert "json" in prompt.lower()


class TestErrorHandling:
    """Test error handling in nutrition service"""
    
    def test_generate_plan_handles_client_error(self, sample_user_bulking):
        """Test service handles client errors gracefully"""
        mock_client = Mock()
        mock_client.generate_completion.side_effect = GymAssistantError(
            "API error", "api_error"
        )
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        with pytest.raises(GymAssistantError) as exc_info:
            service.generate_meal_plan(request)
        
        assert exc_info.value.error_type == "api_error"
    
    def test_generate_plan_handles_invalid_json(self, sample_user_bulking):
        """Test service handles invalid JSON response"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = "This is not JSON"
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        with pytest.raises(GymAssistantError) as exc_info:
            service.generate_meal_plan(request)
        
        assert "parser" in exc_info.value.error_type.lower()
    
    def test_generate_plan_validates_request(self):
        """Test service validates nutrition request"""
        service = NutritionService(Mock())
        
        with pytest.raises((GymAssistantError, TypeError, AttributeError)):
            service.generate_meal_plan(None)
    
    def test_calculate_macros_handles_invalid_user(self):
        """Test macro calculation validates user profile"""
        service = NutritionService(Mock())
        
        with pytest.raises((GymAssistantError, TypeError, AttributeError)):
            service.calculate_macros(None)


class TestSystemMessage:
    """Test system message configuration"""
    
    def test_service_uses_system_message(self, sample_user_bulking):
        """Test service provides system message to client"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": [{
                "name": "Meal",
                "meal_type": "lunch",
                "calories": 500,
                "protein_g": 40.0,
                "carbs_g": 50.0,
                "fats_g": 15.0,
                "ingredients": ["food"],
                "instructions": "Cook",
                "prep_time_minutes": 20
            }]
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        service.generate_meal_plan(request)
        
        # Check system_message was passed
        call_args = mock_client.generate_completion.call_args
        assert "system_message" in call_args.kwargs
        system_msg = call_args.kwargs["system_message"]
        assert "nutrition" in system_msg.lower() or "dietitian" in system_msg.lower()


class TestPlanValidation:
    """Test nutrition plan output validation"""
    
    def test_service_validates_plan_output(self, sample_user_bulking):
        """Test service validates generated meal plan"""
        mock_client = Mock()
        # Return invalid plan (no meals)
        mock_client.generate_completion.return_value = json.dumps({
            "date": "2025-10-14",
            "meals": []
        })
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        # Should raise error for invalid plan
        with pytest.raises(GymAssistantError):
            service.generate_meal_plan(request)
    
    def test_service_validates_macro_totals(self, sample_user_bulking, mock_nutrition_json):
        """Test service checks macro totals are reasonable"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_nutrition_json)
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        plan = service.generate_meal_plan(request)
        
        # Totals should be positive
        assert plan.total_calories > 0
        assert plan.total_protein_g > 0


class TestModelConfiguration:
    """Test AI model configuration"""
    
    def test_service_uses_specified_model(self, sample_user_bulking, mock_nutrition_json):
        """Test service uses model from request"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_nutrition_json)
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            model="gpt-4o-mini",
            budget_level="medium"
        )
        
        service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        assert call_args.kwargs.get("model") == "gpt-4o-mini"
    
    def test_service_uses_default_model(self, sample_user_bulking, mock_nutrition_json):
        """Test service uses default model if not specified"""
        mock_client = Mock()
        mock_client.generate_completion.return_value = json.dumps(mock_nutrition_json)
        
        service = NutritionService(mock_client)
        request = NutritionRequest(
            user_profile=sample_user_bulking,
            budget_level="medium"
        )
        
        service.generate_meal_plan(request)
        
        call_args = mock_client.generate_completion.call_args
        model = call_args.kwargs.get("model", "gpt-4o")
        assert model in ["gpt-4o", "gpt-4o-mini"]
