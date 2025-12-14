"""
Qdrant Vector Database Manager
Handles vector storage and similarity search
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)
import numpy as np

logger = logging.getLogger(__name__)


class QdrantManager:
    """
    Manages Qdrant vector database for RAG system

    Collections:
    - workers: Worker profiles and information
    - productivity: Productivity indices and sessions
    - insights: Generated insights and recommendations
    """

    def __init__(
        self,
        host: str = "qdrant",
        port: int = 6333,
        embedding_dim: int = 768
    ):
        """
        Initialize Qdrant manager

        Args:
            host: Qdrant host
            port: Qdrant port
            embedding_dim: Embedding dimension
        """
        self.host = host
        self.port = port
        self.embedding_dim = embedding_dim
        self.client = None

        logger.info(
            f"QdrantManager initialized (host={host}, port={port}, dim={embedding_dim})"
        )

    def connect(self):
        """Connect to Qdrant"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info("Connected to Qdrant successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False

    def create_collection(
        self,
        collection_name: str,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """
        Create a collection if it doesn't exist

        Args:
            collection_name: Collection name
            distance: Distance metric

        Returns:
            True if successful
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if exists:
                logger.info(f"Collection '{collection_name}' already exists")
                return True

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=distance
                )
            )

            logger.info(f"Created collection '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return False

    def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        embeddings: np.ndarray
    ) -> bool:
        """
        Insert or update points in collection

        Args:
            collection_name: Collection name
            points: List of point data (with metadata)
            embeddings: Embeddings for each point

        Returns:
            True if successful
        """
        try:
            # Create PointStruct objects
            point_structs = []

            for i, (point_data, embedding) in enumerate(zip(points, embeddings)):
                # Generate ID if not provided
                point_id = point_data.get('id', str(uuid.uuid4()))

                point_struct = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=point_data
                )

                point_structs.append(point_struct)

            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )

            logger.info(
                f"Upserted {len(point_structs)} points to '{collection_name}'"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to upsert points to '{collection_name}': {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            collection_name: Collection name
            query_vector: Query embedding
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Filter by metadata

        Returns:
            List of search results with scores
        """
        try:
            # Build filter if conditions provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)

            # Search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                })

            logger.debug(
                f"Found {len(formatted_results)} results in '{collection_name}'"
            )

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed in '{collection_name}': {e}")
            return []

    def delete_points(
        self,
        collection_name: str,
        point_ids: List[str]
    ) -> bool:
        """
        Delete points by IDs

        Args:
            collection_name: Collection name
            point_ids: List of point IDs to delete

        Returns:
            True if successful
        """
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )

            logger.info(
                f"Deleted {len(point_ids)} points from '{collection_name}'"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete points from '{collection_name}': {e}")
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get collection information

        Args:
            collection_name: Collection name

        Returns:
            Collection info or None
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info '{collection_name}': {e}")
            return None

    def list_collections(self) -> List[str]:
        """
        List all collection names

        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection

        Args:
            collection_name: Collection name

        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def get_stats(self) -> dict:
        """Get Qdrant manager statistics"""
        collections = self.list_collections()
        collection_stats = {}

        for collection_name in collections:
            info = self.get_collection_info(collection_name)
            if info:
                collection_stats[collection_name] = {
                    'points': info['points_count'],
                    'vectors': info['vectors_count']
                }

        return {
            'host': self.host,
            'port': self.port,
            'embedding_dim': self.embedding_dim,
            'collections': collection_stats,
            'connected': self.client is not None
        }
