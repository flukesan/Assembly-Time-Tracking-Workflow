"""
Worker Manager - CRUD operations for workers
"""

import threading
from typing import Dict, List, Optional
import logging
import numpy as np

from .worker_models import Worker, WorkerStatus, Shift

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages worker data and operations"""

    def __init__(self):
        """Initialize worker manager"""
        self.workers: Dict[str, Worker] = {}  # worker_id -> Worker
        self.badge_map: Dict[str, str] = {}   # badge_id -> worker_id
        self._lock = threading.Lock()

        logger.info("WorkerManager initialized")

    def add_worker(self, worker: Worker) -> bool:
        """
        Add a new worker

        Args:
            worker: Worker object

        Returns:
            True if worker added successfully
        """
        with self._lock:
            if worker.worker_id in self.workers:
                logger.warning(f"Worker {worker.worker_id} already exists")
                return False

            self.workers[worker.worker_id] = worker

            # Update badge mapping
            if worker.badge_id:
                self.badge_map[worker.badge_id] = worker.worker_id

            logger.info(f"Added worker {worker.worker_id}: {worker.name}")
            return True

    def update_worker(self, worker: Worker) -> bool:
        """
        Update existing worker

        Args:
            worker: Worker object with updated data

        Returns:
            True if worker updated successfully
        """
        with self._lock:
            if worker.worker_id not in self.workers:
                logger.warning(f"Worker {worker.worker_id} not found")
                return False

            old_worker = self.workers[worker.worker_id]

            # Update badge mapping if changed
            if old_worker.badge_id and old_worker.badge_id != worker.badge_id:
                del self.badge_map[old_worker.badge_id]

            if worker.badge_id:
                self.badge_map[worker.badge_id] = worker.worker_id

            self.workers[worker.worker_id] = worker

            logger.info(f"Updated worker {worker.worker_id}: {worker.name}")
            return True

    def remove_worker(self, worker_id: str) -> bool:
        """
        Remove a worker

        Args:
            worker_id: Worker ID

        Returns:
            True if worker removed successfully
        """
        with self._lock:
            if worker_id not in self.workers:
                logger.warning(f"Worker {worker_id} not found")
                return False

            worker = self.workers[worker_id]

            # Remove badge mapping
            if worker.badge_id and worker.badge_id in self.badge_map:
                del self.badge_map[worker.badge_id]

            del self.workers[worker_id]

            logger.info(f"Removed worker {worker_id}: {worker.name}")
            return True

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """
        Get worker by ID

        Args:
            worker_id: Worker ID

        Returns:
            Worker object or None
        """
        with self._lock:
            return self.workers.get(worker_id)

    def get_worker_by_badge(self, badge_id: str) -> Optional[Worker]:
        """
        Get worker by badge ID

        Args:
            badge_id: Badge ID

        Returns:
            Worker object or None
        """
        with self._lock:
            worker_id = self.badge_map.get(badge_id)
            if worker_id:
                return self.workers.get(worker_id)
            return None

    def get_all_workers(self) -> List[Worker]:
        """
        Get all workers

        Returns:
            List of all workers
        """
        with self._lock:
            return list(self.workers.values())

    def get_active_workers(self) -> List[Worker]:
        """
        Get all active workers

        Returns:
            List of active workers
        """
        with self._lock:
            return [w for w in self.workers.values() if w.active]

    def get_workers_by_shift(self, shift: Shift) -> List[Worker]:
        """
        Get workers by shift

        Args:
            shift: Shift type

        Returns:
            List of workers in specified shift
        """
        with self._lock:
            return [w for w in self.workers.values() if w.shift == shift]

    def enroll_face(self, worker_id: str, face_embedding: np.ndarray) -> bool:
        """
        Enroll face embedding for a worker

        Args:
            worker_id: Worker ID
            face_embedding: Face embedding vector (numpy array)

        Returns:
            True if face enrolled successfully
        """
        with self._lock:
            if worker_id not in self.workers:
                logger.warning(f"Worker {worker_id} not found")
                return False

            worker = self.workers[worker_id]
            worker.set_face_embedding(face_embedding)

            logger.info(f"Enrolled face for worker {worker_id}")
            return True

    def find_worker_by_face(
        self,
        face_embedding: np.ndarray,
        threshold: float = 0.6
    ) -> Optional[tuple]:
        """
        Find worker by face embedding (cosine similarity)

        Args:
            face_embedding: Face embedding to match
            threshold: Similarity threshold (0-1)

        Returns:
            Tuple of (worker, similarity) or None
        """
        with self._lock:
            best_match = None
            best_similarity = threshold

            for worker in self.workers.values():
                if not worker.active:
                    continue

                stored_embedding = worker.get_face_embedding()
                if stored_embedding is None:
                    continue

                # Cosine similarity
                similarity = self._cosine_similarity(face_embedding, stored_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = worker

            if best_match:
                logger.info(
                    f"Matched face to worker {best_match.worker_id} "
                    f"with similarity {best_similarity:.3f}"
                )
                return (best_match, best_similarity)

            return None

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_stats(self) -> Dict:
        """Get worker statistics"""
        with self._lock:
            return {
                'total_workers': len(self.workers),
                'active_workers': len([w for w in self.workers.values() if w.active]),
                'with_face_enrolled': len([w for w in self.workers.values() if w.face_embedding]),
                'with_badge': len([w for w in self.workers.values() if w.badge_id]),
                'by_shift': {
                    'morning': len([w for w in self.workers.values() if w.shift == Shift.MORNING]),
                    'afternoon': len([w for w in self.workers.values() if w.shift == Shift.AFTERNOON]),
                    'night': len([w for w in self.workers.values() if w.shift == Shift.NIGHT]),
                    'flexible': len([w for w in self.workers.values() if w.shift == Shift.FLEXIBLE])
                }
            }
