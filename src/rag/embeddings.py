"""
Embedding Generator
Converts text to vector embeddings using sentence-transformers
"""

import logging
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings for text using multilingual models
    Supports Thai + English
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        device: str = "cpu"
    ):
        """
        Initialize embedding generator

        Args:
            model_name: Sentence-transformer model name
            device: "cpu" or "cuda"
        """
        self.model_name = model_name
        self.device = device
        self.model = None

        logger.info(
            f"EmbeddingGenerator initialized (model={model_name}, device={device})"
        )

    def _load_model(self):
        """Load sentence-transformer model (lazy loading)"""
        if self.model is not None:
            return

        logger.info(f"Loading embedding model {self.model_name}...")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        logger.info("Embedding model loaded successfully")

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode text(s) to embeddings

        Args:
            texts: Single text or list of texts
            normalize: Normalize embeddings to unit length
            batch_size: Batch size for encoding

        Returns:
            Embeddings as numpy array (single text -> 1D, multiple -> 2D)
        """
        # Lazy load model
        if self.model is None:
            self._load_model()

        # Convert single text to list
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Return single embedding for single text
        if is_single:
            return embeddings[0]

        return embeddings

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode query for similarity search

        Args:
            query: Query text

        Returns:
            Query embedding
        """
        return self.encode(query, normalize=True)

    def encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode multiple documents

        Args:
            documents: List of document texts
            batch_size: Batch size for encoding

        Returns:
            Document embeddings (2D array)
        """
        return self.encode(documents, normalize=True, batch_size=batch_size)

    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score (0-1)
        """
        return float(np.dot(embedding1, embedding2))

    def get_embedding_dim(self) -> int:
        """
        Get embedding dimension

        Returns:
            Embedding dimension
        """
        if self.model is None:
            self._load_model()

        return self.model.get_sentence_embedding_dimension()

    def get_stats(self) -> dict:
        """Get embedding generator statistics"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'embedding_dim': self.get_embedding_dim() if self.model else None,
            'model_loaded': self.model is not None
        }
