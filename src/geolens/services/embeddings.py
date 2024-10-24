"""
Embedding service for text-to-vector conversion.
"""
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """Service for generating embeddings from text."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def get_embedding(self, text: str) -> str:
        """
        Convert text to a vector embedding.
        Returns the vector in pgvector's string format: [x,y,z,...]
        """
        embedding = self.model.encode(text)
        return self._format_for_pgvector(embedding)
    
    def get_batch_embeddings(self, texts: list[str]) -> list[str]:
        """
        Convert multiple texts to vector embeddings.
        Returns vectors in pgvector's string format.
        """
        embeddings = self.model.encode(texts)
        return [self._format_for_pgvector(emb) for emb in embeddings]
    
    def _format_for_pgvector(self, embedding: np.ndarray) -> str:
        """Convert numpy array to pgvector string format."""
        return f"[{','.join(str(x) for x in embedding)}]"

@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get or create a cached embedding service instance."""
    return EmbeddingService()