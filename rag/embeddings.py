"""
Embedding generation using HuggingFace Inference Client.
Uses the all-MiniLM-L6-v2 model via HuggingFace Hub SDK with batch support.
"""
from typing import List, Union
from huggingface_hub import InferenceClient
from config import config


class EmbeddingGenerator:
    """Generates embeddings using HuggingFace Inference API."""
    
    _instance = None
    _client = None
    
    # Model for embeddings
    MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize with HuggingFace Inference Client."""
        if self._client is None:
            print(f"Initializing embedding client for {self.MODEL_ID}")
            self._client = InferenceClient(token=config.HUGGINGFACE_API_KEY)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        result = self._client.feature_extraction(
            text=text,
            model=self.MODEL_ID
        )
        return self._normalize_embedding(result)
    
    def _normalize_embedding(self, result) -> List[float]:
        """Normalize embedding result to flat list of floats."""
        # Convert numpy array to list if needed
        if hasattr(result, 'tolist'):
            result = result.tolist()
        # Handle potential nesting
        while isinstance(result, list) and len(result) == 1 and isinstance(result[0], list):
            result = result[0]
        return result
    
    def embed_texts(self, texts: List[str], show_progress: bool = False) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(texts)
        
        for i, text in enumerate(texts):
            embedding = self.embed_text(text)
            embeddings.append(embedding)
            
            if show_progress and (i + 1) % 100 == 0:
                print(f"  Embedded {i + 1}/{total} documents...")
        
        return embeddings
    
    @property
    def dimension(self) -> int:
        """Return the embedding dimension for all-MiniLM-L6-v2."""
        return 384


# Convenience function
def get_embeddings(texts: Union[str, List[str]], show_progress: bool = False) -> Union[List[float], List[List[float]]]:
    """Get embeddings for text(s).
    
    Args:
        texts: Single text or list of texts
        show_progress: Whether to show progress for batch embedding
        
    Returns:
        Single embedding vector or list of vectors
    """
    generator = EmbeddingGenerator()
    if isinstance(texts, str):
        return generator.embed_text(texts)
    return generator.embed_texts(texts, show_progress=show_progress)
