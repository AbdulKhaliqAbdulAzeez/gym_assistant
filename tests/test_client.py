"""
Test suite for OpenAI API client wrapper (TDD RED phase first).
Tests use mocking to avoid real API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.client import GymAssistantClient
from src.models import GymAssistantError
from src.config import reset_config
import os


class TestClientInitialization:
    """Test client initialization and API key handling"""
    
    def setup_method(self):
        """Reset config before each test"""
        reset_config()
    
    def test_client_initialization_with_api_key(self):
        """Test client initializes with provided API key"""
        client = GymAssistantClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
    
    def test_client_initialization_from_env(self, monkeypatch):
        """Test client loads API key from environment"""
        monkeypatch.setenv("OPENAI_API_KEY", "env_key_456")
        reset_config()  # Reset after setting env var
        client = GymAssistantClient()
        assert client.api_key == "env_key_456"
    
    def test_client_raises_error_without_api_key(self, monkeypatch):
        """Test client raises error if no API key provided"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        reset_config()  # Reset after deleting env var
        with pytest.raises(GymAssistantError) as exc_info:
            GymAssistantClient()
        assert exc_info.value.error_type == "configuration_error"


class TestGenerateCompletion:
    """Test GPT-4o completion generation"""
    
    @patch('src.client.OpenAI')
    def test_generate_completion_success(self, mock_openai_class):
        """Test successful GPT-4o API call"""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is a workout plan"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test
        client = GymAssistantClient(api_key="test_key")
        result = client.generate_completion("Generate a workout", model="gpt-4o")
        
        assert result == "This is a workout plan"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.client.OpenAI')
    def test_generate_completion_with_custom_params(self, mock_openai_class):
        """Test completion with custom temperature and max_tokens"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Response"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = GymAssistantClient(api_key="test_key")
        result = client.generate_completion(
            "Test prompt",
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=1000
        )
        
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"
        assert call_args.kwargs["temperature"] == 0.5
        assert call_args.kwargs["max_tokens"] == 1000
    
    @patch('src.client.OpenAI')
    def test_generate_completion_with_system_message(self, mock_openai_class):
        """Test completion includes system message"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Response"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = GymAssistantClient(api_key="test_key")
        result = client.generate_completion(
            "Generate workout",
            system_message="You are a fitness expert"
        )
        
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a fitness expert"
        assert messages[1]["role"] == "user"


class TestGenerateEmbedding:
    """Test embeddings generation"""
    
    @patch('src.client.OpenAI')
    def test_generate_embedding_success(self, mock_openai_class):
        """Test successful embeddings API call"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock embedding response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        mock_client.embeddings.create.return_value = mock_response
        
        client = GymAssistantClient(api_key="test_key")
        result = client.generate_embedding("push-ups exercise")
        
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_client.embeddings.create.assert_called_once()
    
    @patch('src.client.OpenAI')
    def test_generate_embedding_uses_correct_model(self, mock_openai_class):
        """Test embedding uses text-embedding-3-large model"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 3072  # Correct dimension
        
        mock_client.embeddings.create.return_value = mock_response
        
        client = GymAssistantClient(api_key="test_key")
        result = client.generate_embedding("test text")
        
        call_args = mock_client.embeddings.create.call_args
        assert call_args.kwargs["model"] == "text-embedding-3-large"
        assert call_args.kwargs["input"] == "test text"


class TestErrorHandling:
    """Test error handling and retries"""
    
    @patch('src.client.OpenAI')
    def test_client_handles_rate_limit_error(self, mock_openai_class):
        """Test exponential backoff on rate limit errors"""
        import openai
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # First call raises rate limit, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Success"
        
        mock_client.chat.completions.create.side_effect = [
            openai.RateLimitError("Rate limit exceeded", response=Mock(), body=None),
            mock_response
        ]
        
        with patch('time.sleep'):  # Don't actually sleep in tests
            client = GymAssistantClient(api_key="test_key")
            result = client.generate_completion("test", max_retries=2)
        
        assert result == "Success"
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch('src.client.OpenAI')
    def test_client_raises_on_auth_error(self, mock_openai_class):
        """Test proper error handling for auth failures"""
        import openai
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
            "Invalid API key",
            response=Mock(),
            body=None
        )
        
        client = GymAssistantClient(api_key="invalid_key")
        with pytest.raises(GymAssistantError) as exc_info:
            client.generate_completion("test")
        
        assert exc_info.value.error_type == "authentication_error"
    
    @patch('src.client.OpenAI')
    def test_client_raises_on_api_error(self, mock_openai_class):
        """Test handling of general API errors"""
        import openai
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_client.chat.completions.create.side_effect = openai.APIError(
            "API Error",
            request=Mock(),
            body=None
        )
        
        client = GymAssistantClient(api_key="test_key")
        with pytest.raises(GymAssistantError) as exc_info:
            client.generate_completion("test", max_retries=1)
        
        assert exc_info.value.error_type == "api_error"
    
    @patch('src.client.OpenAI')
    def test_max_retries_exceeded(self, mock_openai_class):
        """Test that retries stop after max attempts"""
        import openai
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_client.chat.completions.create.side_effect = openai.RateLimitError(
            "Rate limit",
            response=Mock(),
            body=None
        )
        
        with patch('time.sleep'):
            client = GymAssistantClient(api_key="test_key")
            with pytest.raises(GymAssistantError) as exc_info:
                client.generate_completion("test", max_retries=2)
        
        assert exc_info.value.error_type == "api_error"
        # Should try initial + 2 retries = 3 total
        assert mock_client.chat.completions.create.call_count == 3


class TestClientConfiguration:
    """Test client configuration and defaults"""
    
    def test_default_model_is_gpt4o(self):
        """Test default model configuration"""
        client = GymAssistantClient(api_key="test_key")
        assert client.default_model == "gpt-4o"
    
    def test_default_embedding_model(self):
        """Test default embedding model"""
        client = GymAssistantClient(api_key="test_key")
        assert client.embedding_model == "text-embedding-3-large"
