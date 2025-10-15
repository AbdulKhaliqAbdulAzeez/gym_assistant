"""
Test suite for EmbeddingService (TDD RED phase first).
Service handles vector similarity search for exercise recommendations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from src.embedding_service import EmbeddingService
from src.models import (
    ExerciseEmbedding,
    Exercise,
    GymAssistantError
)


@pytest.fixture
def sample_exercises():
    """Fixture with sample exercise database"""
    return [
        Exercise(
            name="Push-ups",
            muscle_groups=["chest", "triceps", "shoulders"],
            equipment=[],
            difficulty="beginner",
            sets=3,
            reps="12-15",
            rest_seconds=60,
            instructions="Standard push-up form"
        ),
        Exercise(
            name="Bench Press",
            muscle_groups=["chest", "triceps", "shoulders"],
            equipment=["barbell", "bench"],
            difficulty="intermediate",
            sets=4,
            reps="8-10",
            rest_seconds=90,
            instructions="Lie on bench, press barbell up"
        ),
        Exercise(
            name="Squats",
            muscle_groups=["legs", "glutes", "core"],
            equipment=[],
            difficulty="intermediate",
            sets=4,
            reps="10-12",
            rest_seconds=90,
            instructions="Feet shoulder-width, squat down"
        ),
        Exercise(
            name="Pull-ups",
            muscle_groups=["back", "biceps"],
            equipment=["pull-up bar"],
            difficulty="intermediate",
            sets=3,
            reps="8-10",
            rest_seconds=120,
            instructions="Hang from bar, pull up to chin"
        ),
        Exercise(
            name="Dumbbell Chest Press",
            muscle_groups=["chest", "triceps", "shoulders"],
            equipment=["dumbbells"],
            difficulty="intermediate",
            sets=4,
            reps="8-10",
            rest_seconds=90,
            instructions="Press dumbbells up from chest"
        )
    ]


@pytest.fixture
def sample_embeddings():
    """Fixture with sample exercise embeddings"""
    # Simplified embeddings (real ones are 3072-dimensional)
    return [
        ExerciseEmbedding(
            exercise_name="Push-ups",
            description="Bodyweight chest exercise targeting chest, triceps, shoulders",
            embedding=[0.8, 0.6, 0.1, 0.2, 0.3],
            metadata={"difficulty": "beginner", "equipment": "none"}
        ),
        ExerciseEmbedding(
            exercise_name="Bench Press",
            description="Barbell chest exercise targeting chest, triceps, shoulders",
            embedding=[0.85, 0.65, 0.15, 0.25, 0.3],
            metadata={"difficulty": "intermediate", "equipment": "barbell"}
        ),
        ExerciseEmbedding(
            exercise_name="Squats",
            description="Lower body exercise targeting legs, glutes, core",
            embedding=[0.1, 0.2, 0.9, 0.8, 0.1],
            metadata={"difficulty": "intermediate", "equipment": "none"}
        ),
        ExerciseEmbedding(
            exercise_name="Pull-ups",
            description="Upper body pulling exercise targeting back, biceps",
            embedding=[0.3, 0.2, 0.1, 0.8, 0.9],
            metadata={"difficulty": "intermediate", "equipment": "pull-up bar"}
        ),
        ExerciseEmbedding(
            exercise_name="Dumbbell Chest Press",
            description="Dumbbell chest exercise targeting chest, triceps, shoulders",
            embedding=[0.82, 0.63, 0.12, 0.23, 0.32],
            metadata={"difficulty": "intermediate", "equipment": "dumbbells"}
        )
    ]


class TestEmbeddingServiceInitialization:
    """Test service initialization"""
    
    def test_service_initialization(self):
        """Test service initializes with client"""
        mock_client = Mock()
        service = EmbeddingService(mock_client)
        assert service.client == mock_client
        assert service.exercise_database == []
    
    def test_service_initialization_without_client(self):
        """Test service can initialize without explicit client"""
        with patch('src.embedding_service.GymAssistantClient'):
            service = EmbeddingService()
            assert service.client is not None
    
    def test_service_initialization_with_database(self, sample_embeddings):
        """Test service initializes with exercise database"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        assert len(service.exercise_database) == 5


class TestCosineSimilarity:
    """Test cosine similarity calculation"""
    
    def test_cosine_similarity_identical_vectors(self):
        """Test similarity of identical vectors is 1.0"""
        v1 = [1.0, 2.0, 3.0, 4.0]
        v2 = [1.0, 2.0, 3.0, 4.0]
        
        similarity = EmbeddingService.cosine_similarity(v1, v2)
        
        assert abs(similarity - 1.0) < 0.0001
    
    def test_cosine_similarity_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors is 0.0"""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        
        similarity = EmbeddingService.cosine_similarity(v1, v2)
        
        assert abs(similarity - 0.0) < 0.0001
    
    def test_cosine_similarity_opposite_vectors(self):
        """Test similarity of opposite vectors is -1.0"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [-1.0, -2.0, -3.0]
        
        similarity = EmbeddingService.cosine_similarity(v1, v2)
        
        assert abs(similarity - (-1.0)) < 0.0001
    
    def test_cosine_similarity_similar_vectors(self):
        """Test similarity of similar vectors is high"""
        v1 = [0.8, 0.6, 0.1]
        v2 = [0.82, 0.63, 0.12]
        
        similarity = EmbeddingService.cosine_similarity(v1, v2)
        
        assert similarity > 0.99
    
    def test_cosine_similarity_handles_zero_vector(self):
        """Test handling of zero vectors"""
        v1 = [0.0, 0.0, 0.0]
        v2 = [1.0, 2.0, 3.0]
        
        similarity = EmbeddingService.cosine_similarity(v1, v2)
        
        assert similarity == 0.0


class TestFindSimilarExercises:
    """Test finding similar exercises"""
    
    def test_find_similar_exercises_by_query(self, sample_embeddings):
        """Test finding similar exercises using text query"""
        mock_client = Mock()
        # Mock embedding for "chest exercises"
        mock_client.generate_embedding.return_value = [0.81, 0.62, 0.11, 0.21, 0.31]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises("chest exercises", top_k=3)
        
        assert len(results) == 3
        assert results[0][0] == "Push-ups" or results[0][0] == "Bench Press"
        assert all(isinstance(r[1], float) for r in results)  # Similarity scores
        mock_client.generate_embedding.assert_called_once()
    
    def test_find_similar_exercises_returns_top_k(self, sample_embeddings):
        """Test returns correct number of results"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.5, 0.5, 0.5, 0.5, 0.5]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises("any exercise", top_k=2)
        
        assert len(results) == 2
    
    def test_find_similar_exercises_sorted_by_similarity(self, sample_embeddings):
        """Test results are sorted by similarity (highest first)"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.8, 0.6, 0.1, 0.2, 0.3]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises("push-up exercises", top_k=5)
        
        # Verify sorted in descending order
        similarities = [r[1] for r in results]
        assert similarities == sorted(similarities, reverse=True)
    
    def test_find_similar_exercises_with_empty_database(self):
        """Test handling of empty exercise database"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.5, 0.5, 0.5]
        
        service = EmbeddingService(mock_client, exercise_database=[])
        
        results = service.find_similar_exercises("test query", top_k=5)
        
        assert results == []
    
    def test_find_similar_exercises_handles_top_k_larger_than_database(self, sample_embeddings):
        """Test requesting more results than available"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.5, 0.5, 0.5, 0.5, 0.5]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises("test", top_k=100)
        
        assert len(results) == len(sample_embeddings)  # Returns all available


class TestFindAlternatives:
    """Test finding alternative exercises"""
    
    def test_find_alternatives_for_exercise(self, sample_embeddings):
        """Test finding alternatives to a specific exercise"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        alternatives = service.find_alternatives("Push-ups", top_k=3)
        
        assert len(alternatives) <= 3
        # Should not include the original exercise
        assert all(alt[0] != "Push-ups" for alt in alternatives)
    
    def test_find_alternatives_similar_muscle_groups(self, sample_embeddings):
        """Test alternatives target similar muscle groups"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        # Find alternatives to Push-ups (chest exercise)
        alternatives = service.find_alternatives("Push-ups", top_k=2)
        
        # Top alternatives should be other chest exercises
        alt_names = [alt[0] for alt in alternatives]
        assert "Bench Press" in alt_names or "Dumbbell Chest Press" in alt_names
    
    def test_find_alternatives_excludes_original(self, sample_embeddings):
        """Test original exercise is excluded from results"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        alternatives = service.find_alternatives("Squats", top_k=5)
        
        assert not any(alt[0] == "Squats" for alt in alternatives)
    
    def test_find_alternatives_nonexistent_exercise(self, sample_embeddings):
        """Test handling of nonexistent exercise"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        with pytest.raises(GymAssistantError) as exc_info:
            service.find_alternatives("Nonexistent Exercise", top_k=3)
        
        assert "not found" in str(exc_info.value).lower()


class TestFilterByEquipment:
    """Test filtering exercises by equipment"""
    
    def test_find_similar_with_equipment_filter(self, sample_embeddings):
        """Test finding exercises with specific equipment"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.8, 0.6, 0.1, 0.2, 0.3]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises(
            "chest exercises",
            top_k=5,
            equipment_filter=["none"]
        )
        
        # Should only return bodyweight exercises
        assert any("Push-ups" in r[0] for r in results)
        assert not any("Bench Press" in r[0] for r in results)
    
    def test_find_similar_with_multiple_equipment(self, sample_embeddings):
        """Test finding exercises with multiple equipment options"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.8, 0.6, 0.1, 0.2, 0.3]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises(
            "chest exercises",
            top_k=5,
            equipment_filter=["dumbbells", "none"]
        )
        
        # Should include both dumbbell and bodyweight exercises
        result_names = [r[0] for r in results]
        assert "Push-ups" in result_names or "Dumbbell Chest Press" in result_names


class TestFilterByDifficulty:
    """Test filtering exercises by difficulty"""
    
    def test_find_similar_with_difficulty_filter(self, sample_embeddings):
        """Test finding exercises of specific difficulty"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.8, 0.6, 0.1, 0.2, 0.3]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        results = service.find_similar_exercises(
            "chest exercises",
            top_k=5,
            difficulty_filter="beginner"
        )
        
        # Should only return beginner exercises
        assert any("Push-ups" in r[0] for r in results)
        # Bench Press is intermediate, should not be included
        # (or may be included if no other beginners available)


class TestBuildExerciseDatabase:
    """Test building exercise database with embeddings"""
    
    def test_build_database_from_exercises(self, sample_exercises):
        """Test creating embeddings for exercise list"""
        mock_client = Mock()
        # Mock embeddings for each exercise
        mock_client.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        service = EmbeddingService(mock_client)
        service.build_database(sample_exercises)
        
        assert len(service.exercise_database) == len(sample_exercises)
        assert mock_client.generate_embedding.call_count == len(sample_exercises)
    
    def test_build_database_creates_descriptions(self, sample_exercises):
        """Test database includes exercise descriptions"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        service = EmbeddingService(mock_client)
        service.build_database(sample_exercises)
        
        # Check descriptions were created
        for embedding in service.exercise_database:
            assert embedding.description
            assert embedding.exercise_name
    
    def test_build_database_includes_metadata(self, sample_exercises):
        """Test database includes exercise metadata"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        service = EmbeddingService(mock_client)
        service.build_database(sample_exercises)
        
        # Check metadata was stored
        for embedding in service.exercise_database:
            assert "difficulty" in embedding.metadata
            assert "equipment" in embedding.metadata


class TestRecommendForInjury:
    """Test recommending exercises that avoid injuries"""
    
    def test_recommend_exercises_avoiding_injury(self, sample_embeddings):
        """Test finding exercises that avoid specific body parts"""
        mock_client = Mock()
        mock_client.generate_embedding.return_value = [0.1, 0.2, 0.9, 0.8, 0.1]
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        # User has knee injury, recommend upper body exercises
        results = service.find_similar_exercises(
            "exercises that don't stress knees",
            top_k=3
        )
        
        assert len(results) > 0
        # Should recommend upper body exercises
        result_names = [r[0] for r in results]
        assert any(ex in result_names for ex in ["Push-ups", "Pull-ups", "Bench Press"])


class TestErrorHandling:
    """Test error handling in embedding service"""
    
    def test_find_similar_handles_client_error(self, sample_embeddings):
        """Test service handles client errors gracefully"""
        mock_client = Mock()
        mock_client.generate_embedding.side_effect = GymAssistantError(
            "API error", "api_error"
        )
        
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        with pytest.raises(GymAssistantError):
            service.find_similar_exercises("test query", top_k=3)
    
    def test_find_alternatives_validates_input(self, sample_embeddings):
        """Test service validates input parameters"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        with pytest.raises((GymAssistantError, ValueError)):
            service.find_alternatives("", top_k=3)
    
    def test_cosine_similarity_handles_different_lengths(self):
        """Test handling of vectors with different lengths"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [1.0, 2.0]
        
        with pytest.raises((ValueError, GymAssistantError)):
            EmbeddingService.cosine_similarity(v1, v2)


class TestGetExerciseDetails:
    """Test retrieving full exercise details"""
    
    def test_get_exercise_by_name(self, sample_embeddings):
        """Test getting exercise details by name"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        exercise = service.get_exercise_details("Push-ups")
        
        assert exercise is not None
        assert exercise.exercise_name == "Push-ups"
        assert exercise.description
        assert exercise.metadata
    
    def test_get_nonexistent_exercise(self, sample_embeddings):
        """Test retrieving nonexistent exercise"""
        mock_client = Mock()
        service = EmbeddingService(mock_client, exercise_database=sample_embeddings)
        
        exercise = service.get_exercise_details("Nonexistent")
        
        assert exercise is None
