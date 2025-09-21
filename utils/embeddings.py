"""Embedding generation utilities."""

from typing import Optional, List
import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings

class EmbeddingGenerator:
    """Generate text embeddings."""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            self.model = SentenceTransformer(settings.embedding_model)
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print("Embeddings will not be available")
    
    def generate(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.model or not text:
            return None
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, show_progress_bar=False)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not self.model or not texts:
            return []
        
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return []