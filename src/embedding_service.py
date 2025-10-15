"""
Embedding Service for exercise similarity search using vector embeddings.
Uses OpenAI's text-embedding-3-large for semantic search.
"""

from typing import List, Optional, Tuple
import numpy as np
from src.client import GymAssistantClient
from src.models import ExerciseEmbedding, Exercise, GymAssistantError


class EmbeddingService:
    """Service for finding similar exercises using vector embeddings"""
    
    def __init__(
        self,
        client: Optional[GymAssistantClient] = None,
        exercise_database: Optional[List[ExerciseEmbedding]] = None
    ):
        """
        Initialize embedding service.
        
        Args:
            client: Optional GymAssistantClient. If None, creates new client.
            exercise_database: Optional pre-loaded exercise embeddings.
        """
        self.client = client if client else GymAssistantClient()
        self.exercise_database = exercise_database if exercise_database else []
    
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            v1: First vector
            v2: Second vector
        
        Returns:
            Similarity score between -1 and 1 (1 = identical, 0 = orthogonal, -1 = opposite)
        
        Raises:
            ValueError: If vectors have different lengths or are invalid
        """
        if len(v1) != len(v2):
            raise ValueError(f"Vectors must have same length: {len(v1)} vs {len(v2)}")
        
        # Convert to numpy arrays for easier computation
        vec1 = np.array(v1)
        vec2 = np.array(v2)
        
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        
        return float(similarity)
    
    def find_similar_exercises(
        self,
        query: str,
        top_k: int = 5,
        equipment_filter: Optional[List[str]] = None,
        difficulty_filter: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Find exercises similar to a text query.
        
        Args:
            query: Natural language query (e.g., "chest exercises without weights")
            top_k: Number of results to return
            equipment_filter: Optional list of allowed equipment
            difficulty_filter: Optional difficulty level filter
        
        Returns:
            List of (exercise_name, similarity_score) tuples, sorted by similarity
        
        Raises:
            GymAssistantError: If embedding generation or search fails
        """
        if not self.exercise_database:
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self.client.generate_embedding(query)
            
            # Calculate similarities
            similarities = []
            for exercise_emb in self.exercise_database:
                # Apply filters
                if equipment_filter is not None:
                    exercise_equipment = exercise_emb.metadata.get("equipment", "none")
                    # Check if exercise equipment matches any in the filter
                    equipment_matches = False
                    for allowed in equipment_filter:
                        if allowed.lower() in exercise_equipment.lower() or exercise_equipment.lower() in allowed.lower():
                            equipment_matches = True
                            break
                        if allowed == "none" and exercise_equipment == "none":
                            equipment_matches = True
                            break
                    if not equipment_matches:
                        continue
                
                if difficulty_filter is not None:
                    exercise_difficulty = exercise_emb.metadata.get("difficulty", "")
                    if exercise_difficulty != difficulty_filter:
                        continue
                
                # Calculate similarity
                similarity = self.cosine_similarity(query_embedding, exercise_emb.embedding)
                similarities.append((exercise_emb.exercise_name, similarity))
            
            # Sort by similarity (highest first) and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
        
        except GymAssistantError:
            raise
        except Exception as e:
            raise GymAssistantError(
                f"Error finding similar exercises: {str(e)}",
                "embedding_search_error"
            )
    
    def find_alternatives(
        self,
        exercise_name: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find alternative exercises similar to a given exercise.
        
        Args:
            exercise_name: Name of the exercise to find alternatives for
            top_k: Number of alternatives to return
        
        Returns:
            List of (exercise_name, similarity_score) tuples
        
        Raises:
            GymAssistantError: If exercise not found or search fails
        """
        if not exercise_name or not exercise_name.strip():
            raise GymAssistantError("Exercise name cannot be empty", "validation_error")
        
        # Find the exercise in database
        target_exercise = None
        for exercise_emb in self.exercise_database:
            if exercise_emb.exercise_name.lower() == exercise_name.lower():
                target_exercise = exercise_emb
                break
        
        if target_exercise is None:
            raise GymAssistantError(
                f"Exercise '{exercise_name}' not found in database",
                "not_found_error"
            )
        
        try:
            # Calculate similarities with all other exercises
            similarities = []
            for exercise_emb in self.exercise_database:
                # Skip the original exercise
                if exercise_emb.exercise_name.lower() == exercise_name.lower():
                    continue
                
                similarity = self.cosine_similarity(
                    target_exercise.embedding,
                    exercise_emb.embedding
                )
                similarities.append((exercise_emb.exercise_name, similarity))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
        
        except Exception as e:
            raise GymAssistantError(
                f"Error finding alternatives: {str(e)}",
                "embedding_search_error"
            )
    
    def build_database(self, exercises: List[Exercise]) -> None:
        """
        Build exercise database with embeddings.
        
        Args:
            exercises: List of Exercise objects to embed
        
        Raises:
            GymAssistantError: If embedding generation fails
        """
        self.exercise_database = []
        
        try:
            for exercise in exercises:
                # Create description for embedding
                description = self._create_exercise_description(exercise)
                
                # Generate embedding
                embedding = self.client.generate_embedding(description)
                
                # Create metadata
                metadata = {
                    "difficulty": exercise.difficulty,
                    "equipment": exercise.equipment[0] if exercise.equipment else "none",
                    "equipment_list": exercise.equipment,
                    "muscle_groups": exercise.muscle_groups,
                    "sets": exercise.sets,
                    "reps": exercise.reps,
                    "rest_seconds": exercise.rest_seconds,
                    "instructions": exercise.instructions,
                    "safety_tips": exercise.safety_tips
                }
                
                # Create ExerciseEmbedding
                exercise_emb = ExerciseEmbedding(
                    exercise_name=exercise.name,
                    description=description,
                    embedding=embedding,
                    metadata=metadata
                )
                
                self.exercise_database.append(exercise_emb)
        
        except GymAssistantError:
            raise
        except Exception as e:
            raise GymAssistantError(
                f"Error building exercise database: {str(e)}",
                "database_build_error"
            )
    
    def _create_exercise_description(self, exercise: Exercise) -> str:
        """
        Create a text description for embedding.
        
        Args:
            exercise: Exercise object
        
        Returns:
            Text description combining key exercise attributes
        """
        equipment_str = ", ".join(exercise.equipment) if exercise.equipment else "bodyweight"
        muscles_str = ", ".join(exercise.muscle_groups)
        
        description = f"{exercise.name} - {exercise.difficulty} exercise "
        description += f"targeting {muscles_str} using {equipment_str}. "
        description += exercise.instructions
        
        return description
    
    def get_exercise_details(self, exercise_name: str) -> Optional[ExerciseEmbedding]:
        """
        Get full details for an exercise by name.
        
        Args:
            exercise_name: Name of the exercise
        
        Returns:
            ExerciseEmbedding if found, None otherwise
        """
        for exercise_emb in self.exercise_database:
            if exercise_emb.exercise_name.lower() == exercise_name.lower():
                return exercise_emb
        
        return None
