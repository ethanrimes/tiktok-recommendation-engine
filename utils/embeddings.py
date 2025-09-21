"""Embedding generation utilities."""

from typing import Optional, List
import numpy as np

from config import settings

class EmbeddingGenerator:
    """Generate text embeddings using OpenAI."""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            print("Embeddings will not be available")
    
    def generate(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list or None if failed
        """
        if not self.client or not text:
            return None
        
        try:
            # Generate embedding using OpenAI API
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            
            # Extract embedding vector and return as list
            embedding = response.data[0].embedding
            return embedding  # Already a list from OpenAI API
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not self.client or not texts:
            return []
        
        try:
            # Generate embeddings using OpenAI API
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts
            )
            
            # Extract embedding vectors as lists
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return []