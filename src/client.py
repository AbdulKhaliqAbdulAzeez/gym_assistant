"""
OpenAI API client wrapper for the Gym Assistant.
Handles all communication with OpenAI's GPT and Embeddings APIs.
"""

import time
from typing import Optional, List
import openai
from openai import OpenAI
from dotenv import load_dotenv
from src.models import GymAssistantError
from src.config import get_config

# Load environment variables from .env file
load_dotenv()


class GymAssistantClient:
    """Client for OpenAI API interactions with retry logic and error handling"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, loads from config (which reads OPENAI_API_KEY env var).
        
        Raises:
            GymAssistantError: If no API key is provided or found.
        """
        config = get_config()
        self.api_key = api_key or config.openai_api_key
        
        if not self.api_key:
            raise GymAssistantError(
                "No OpenAI API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.",
                "configuration_error"
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = config.openai_default_model
        self.embedding_model = config.openai_embedding_model
    
    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: Optional[int] = None
    ) -> str:
        """
        Generate a completion using OpenAI's Chat API.
        
        Args:
            prompt: User prompt/query
            model: Model to use. If None, uses default from config.
            system_message: Optional system message to set context
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts on rate limits. If None, uses config default.
        
        Returns:
            Generated text response
        
        Raises:
            GymAssistantError: On authentication or API errors
        """
        config = get_config()
        model = model or self.default_model
        max_retries = max_retries if max_retries is not None else config.openai_max_retries
        
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
            
            except openai.AuthenticationError as e:
                raise GymAssistantError(
                    f"Authentication failed: {str(e)}",
                    "authentication_error"
                )
            
            except openai.RateLimitError as e:
                retry_count += 1
                last_error = e
                if retry_count <= max_retries:
                    # Exponential backoff: 2^retry seconds
                    wait_time = 2 ** retry_count
                    time.sleep(wait_time)
                    continue
                else:
                    break
            
            except openai.APIError as e:
                raise GymAssistantError(
                    f"OpenAI API error: {str(e)}",
                    "api_error"
                )
        
        # If we get here, max retries exceeded
        raise GymAssistantError(
            f"Max retries ({max_retries}) exceeded. Last error: {str(last_error)}",
            "api_error"
        )
    
    def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding vector for text using OpenAI's Embeddings API.
        
        Args:
            text: Text to embed
            model: Model to use (defaults to text-embedding-3-large)
        
        Returns:
            List of floats representing the embedding vector (3072 dimensions)
        
        Raises:
            GymAssistantError: On API errors
        """
        if model is None:
            model = self.embedding_model
        
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
        
        except openai.AuthenticationError as e:
            raise GymAssistantError(
                f"Authentication failed: {str(e)}",
                "authentication_error"
            )
        
        except openai.APIError as e:
            raise GymAssistantError(
                f"OpenAI API error: {str(e)}",
                "api_error"
            )
