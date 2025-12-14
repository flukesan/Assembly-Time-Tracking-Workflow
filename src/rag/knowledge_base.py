"""
Knowledge Base Manager
Manages RAG knowledge retrieval for worker analytics
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .embeddings import EmbeddingGenerator
from .qdrant_manager import QdrantManager
from workers.worker_models import Worker, ProductivityIndex, WorkerSession

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Knowledge Base for RAG system
    Stores and retrieves worker information, productivity data, and insights
    """

    # Collection names
    COLLECTION_WORKERS = "workers"
    COLLECTION_PRODUCTIVITY = "productivity"
    COLLECTION_SESSIONS = "sessions"
    COLLECTION_INSIGHTS = "insights"

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        embedding_generator: EmbeddingGenerator
    ):
        """
        Initialize knowledge base

        Args:
            qdrant_manager: Qdrant manager instance
            embedding_generator: Embedding generator instance
        """
        self.qdrant = qdrant_manager
        self.embedder = embedding_generator

        logger.info("KnowledgeBase initialized")

    async def initialize_collections(self):
        """Create all required collections"""
        collections = [
            self.COLLECTION_WORKERS,
            self.COLLECTION_PRODUCTIVITY,
            self.COLLECTION_SESSIONS,
            self.COLLECTION_INSIGHTS
        ]

        for collection in collections:
            self.qdrant.create_collection(collection)

        logger.info("Knowledge base collections initialized")

    # Worker Management
    def index_worker(self, worker: Worker) -> bool:
        """
        Index a worker profile

        Args:
            worker: Worker object

        Returns:
            True if successful
        """
        try:
            # Create searchable text
            text = f"""Worker Profile:
Name: {worker.name}
ID: {worker.worker_id}
Badge: {worker.badge_id or 'N/A'}
Shift: {worker.shift.value}
Skill Level: {worker.skill_level.value}
Stations: {', '.join(worker.station_assignments) if worker.station_assignments else 'None'}
Status: {'Active' if worker.active else 'Inactive'}
"""

            # Generate embedding
            embedding = self.embedder.encode(text)

            # Prepare point
            point = {
                'id': worker.worker_id,
                'type': 'worker_profile',
                'worker_id': worker.worker_id,
                'name': worker.name,
                'badge_id': worker.badge_id,
                'shift': worker.shift.value,
                'skill_level': worker.skill_level.value,
                'active': worker.active,
                'text': text,
                'indexed_at': datetime.now().isoformat()
            }

            # Upsert to Qdrant
            self.qdrant.upsert_points(
                collection_name=self.COLLECTION_WORKERS,
                points=[point],
                embeddings=embedding.reshape(1, -1)
            )

            logger.info(f"Indexed worker {worker.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to index worker {worker.worker_id}: {e}")
            return False

    # Productivity Management
    def index_productivity(
        self,
        worker_id: str,
        worker_name: str,
        indices: ProductivityIndex
    ) -> bool:
        """
        Index productivity indices

        Args:
            worker_id: Worker ID
            worker_name: Worker name
            indices: Productivity indices

        Returns:
            True if successful
        """
        try:
            # Create searchable text
            text = f"""Productivity Report for {worker_name}:
Shift: {indices.shift.value}
Date: {indices.timestamp.strftime('%Y-%m-%d')}

Time Management:
- Active Time: {indices.index_1_active_time/3600:.2f} hours
- Idle Time: {indices.index_2_idle_time/3600:.2f} hours
- Break Time: {indices.index_3_break_time/3600:.2f} hours
- Total Time: {indices.index_4_total_time/3600:.2f} hours

Efficiency:
- Work Efficiency: {indices.index_5_work_efficiency:.1f}%
- Zone Transitions: {indices.index_6_zone_transitions}
- Avg Time Per Zone: {indices.index_7_avg_time_per_zone/60:.1f} minutes

Output:
- Tasks Completed: {indices.index_8_tasks_completed}
- Output Per Hour: {indices.index_9_output_per_hour:.2f}
- Quality Score: {indices.index_10_quality_score:.1f}/100

Overall Productivity: {indices.index_11_overall_productivity:.1f}/100
"""

            # Generate embedding
            embedding = self.embedder.encode(text)

            # Prepare point
            point = {
                'id': f"{worker_id}_{indices.timestamp.isoformat()}",
                'type': 'productivity_indices',
                'worker_id': worker_id,
                'worker_name': worker_name,
                'shift': indices.shift.value,
                'timestamp': indices.timestamp.isoformat(),
                'overall_productivity': indices.index_11_overall_productivity,
                'work_efficiency': indices.index_5_work_efficiency,
                'output_per_hour': indices.index_9_output_per_hour,
                'quality_score': indices.index_10_quality_score,
                'indices': indices.dict(),
                'text': text,
                'indexed_at': datetime.now().isoformat()
            }

            # Upsert to Qdrant
            self.qdrant.upsert_points(
                collection_name=self.COLLECTION_PRODUCTIVITY,
                points=[point],
                embeddings=embedding.reshape(1, -1)
            )

            logger.info(f"Indexed productivity for {worker_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to index productivity for {worker_id}: {e}")
            return False

    # Session Management
    def index_session(self, session: WorkerSession) -> bool:
        """
        Index a worker session

        Args:
            session: Worker session

        Returns:
            True if successful
        """
        try:
            # Create searchable text
            duration_hours = session.total_duration_seconds / 3600 if session.total_duration_seconds else 0

            text = f"""Work Session for {session.worker_name}:
Shift: {session.shift.value}
Start: {session.start_time.strftime('%Y-%m-%d %H:%M')}
End: {session.end_time.strftime('%Y-%m-%d %H:%M') if session.end_time else 'Ongoing'}
Duration: {duration_hours:.2f} hours
Zones Visited: {', '.join(session.zones_visited) if session.zones_visited else 'None'}
Current Zone: {session.current_zone or 'N/A'}
Status: {'Active' if session.is_active else 'Completed'}
"""

            # Generate embedding
            embedding = self.embedder.encode(text)

            # Prepare point
            point = {
                'id': str(session.session_id) if session.session_id else f"{session.worker_id}_{session.start_time.isoformat()}",
                'type': 'worker_session',
                'worker_id': session.worker_id,
                'worker_name': session.worker_name,
                'shift': session.shift.value,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration_seconds': session.total_duration_seconds,
                'is_active': session.is_active,
                'zones': session.zones_visited,
                'text': text,
                'indexed_at': datetime.now().isoformat()
            }

            # Upsert to Qdrant
            self.qdrant.upsert_points(
                collection_name=self.COLLECTION_SESSIONS,
                points=[point],
                embeddings=embedding.reshape(1, -1)
            )

            logger.info(f"Indexed session for {session.worker_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to index session for {session.worker_id}: {e}")
            return False

    # Insight Management
    def index_insight(
        self,
        insight_type: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Index an AI-generated insight

        Args:
            insight_type: Type of insight (recommendation, analysis, etc.)
            content: Insight content
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = self.embedder.encode(content)

            # Prepare point
            point = {
                'id': f"{insight_type}_{datetime.now().isoformat()}",
                'type': 'insight',
                'insight_type': insight_type,
                'content': content,
                'metadata': metadata or {},
                'text': content,
                'created_at': datetime.now().isoformat()
            }

            # Upsert to Qdrant
            self.qdrant.upsert_points(
                collection_name=self.COLLECTION_INSIGHTS,
                points=[point],
                embeddings=embedding.reshape(1, -1)
            )

            logger.info(f"Indexed insight: {insight_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to index insight: {e}")
            return False

    # Search and Retrieval
    def search_workers(
        self,
        query: str,
        limit: int = 5,
        filter_shift: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for workers by query

        Args:
            query: Search query
            limit: Maximum results
            filter_shift: Filter by shift

        Returns:
            List of matching workers
        """
        # Generate query embedding
        query_vector = self.embedder.encode_query(query)

        # Build filter
        filter_conditions = {'type': 'worker_profile'}
        if filter_shift:
            filter_conditions['shift'] = filter_shift

        # Search
        results = self.qdrant.search(
            collection_name=self.COLLECTION_WORKERS,
            query_vector=query_vector,
            limit=limit,
            filter_conditions=filter_conditions
        )

        return results

    def search_productivity(
        self,
        query: str,
        limit: int = 5,
        worker_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search productivity data

        Args:
            query: Search query
            limit: Maximum results
            worker_id: Filter by worker ID

        Returns:
            List of matching productivity records
        """
        # Generate query embedding
        query_vector = self.embedder.encode_query(query)

        # Build filter
        filter_conditions = {'type': 'productivity_indices'}
        if worker_id:
            filter_conditions['worker_id'] = worker_id

        # Search
        results = self.qdrant.search(
            collection_name=self.COLLECTION_PRODUCTIVITY,
            query_vector=query_vector,
            limit=limit,
            filter_conditions=filter_conditions
        )

        return results

    def get_context_for_query(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant context for a natural language query

        Args:
            query: User's question
            max_results: Maximum results per collection

        Returns:
            Dict with context from all collections
        """
        query_vector = self.embedder.encode_query(query)

        context = {
            'query': query,
            'workers': [],
            'productivity': [],
            'sessions': [],
            'insights': []
        }

        # Search all collections
        try:
            context['workers'] = self.qdrant.search(
                collection_name=self.COLLECTION_WORKERS,
                query_vector=query_vector,
                limit=max_results
            )
        except:
            pass

        try:
            context['productivity'] = self.qdrant.search(
                collection_name=self.COLLECTION_PRODUCTIVITY,
                query_vector=query_vector,
                limit=max_results
            )
        except:
            pass

        try:
            context['sessions'] = self.qdrant.search(
                collection_name=self.COLLECTION_SESSIONS,
                query_vector=query_vector,
                limit=max_results
            )
        except:
            pass

        try:
            context['insights'] = self.qdrant.search(
                collection_name=self.COLLECTION_INSIGHTS,
                query_vector=query_vector,
                limit=max_results
            )
        except:
            pass

        return context

    def get_stats(self) -> dict:
        """Get knowledge base statistics"""
        return {
            'qdrant': self.qdrant.get_stats(),
            'embedder': self.embedder.get_stats()
        }
