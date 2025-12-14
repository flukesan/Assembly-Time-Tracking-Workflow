"""
Productivity Calculator
Calculates 11 productivity indices from worker session data
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List
import numpy as np

from workers.worker_models import ProductivityIndex, WorkerSession, Shift

logger = logging.getLogger(__name__)


class ProductivityCalculator:
    """
    Calculates 11 productivity indices for workers

    Indices:
    1-4: Time-based (active, idle, break, total)
    5-7: Efficiency (work efficiency %, zone transitions, avg time per zone)
    8-10: Output (tasks completed, output per hour, quality score)
    11: Overall productivity (weighted average)
    """

    def __init__(
        self,
        target_output_per_hour: float = 10.0,
        quality_weight: float = 0.4,
        efficiency_weight: float = 0.4,
        time_weight: float = 0.2
    ):
        """
        Initialize productivity calculator

        Args:
            target_output_per_hour: Target output rate for 100% score
            quality_weight: Weight for quality in overall score
            efficiency_weight: Weight for efficiency in overall score
            time_weight: Weight for time management in overall score
        """
        self.target_output_per_hour = target_output_per_hour
        self.quality_weight = quality_weight
        self.efficiency_weight = efficiency_weight
        self.time_weight = time_weight

        logger.info(
            f"ProductivityCalculator initialized "
            f"(target_output={target_output_per_hour}/hr)"
        )

    def calculate_indices(
        self,
        session: WorkerSession,
        zone_transitions: List[Dict] = None,
        tasks_completed: int = 0,
        quality_score: float = 100.0,
        current_time: Optional[datetime] = None
    ) -> ProductivityIndex:
        """
        Calculate all 11 productivity indices for a session

        Args:
            session: Worker session data
            zone_transitions: List of zone transition records
            tasks_completed: Number of tasks/units completed
            quality_score: Quality rating (0-100)
            current_time: Current timestamp (default: now)

        Returns:
            ProductivityIndex with all 11 indices calculated
        """
        current_time = current_time or datetime.now()

        # Create productivity index
        index = ProductivityIndex(
            session_id=session.session_id or 0,
            worker_id=session.worker_id,
            shift=session.shift,
            timestamp=current_time
        )

        # Calculate time-based indices (1-4)
        self._calculate_time_indices(index, session, current_time)

        # Calculate efficiency indices (5-7)
        self._calculate_efficiency_indices(
            index, session, zone_transitions, current_time
        )

        # Calculate output indices (8-10)
        self._calculate_output_indices(
            index, session, tasks_completed, quality_score, current_time
        )

        # Calculate overall productivity (11)
        index.calculate_overall_productivity()

        logger.debug(
            f"Calculated productivity indices for {session.worker_id}: "
            f"overall={index.index_11_overall_productivity:.1f}"
        )

        return index

    def _calculate_time_indices(
        self,
        index: ProductivityIndex,
        session: WorkerSession,
        current_time: datetime
    ):
        """
        Calculate indices 1-4 (time-based)

        Args:
            index: ProductivityIndex to update
            session: Worker session
            current_time: Current timestamp
        """
        # Index 1: Active time
        index.index_1_active_time = session.active_time_seconds

        # Index 2: Idle time
        index.index_2_idle_time = session.idle_time_seconds

        # Index 3: Break time
        index.index_3_break_time = session.break_time_seconds

        # Index 4: Total time
        if session.end_time:
            total_time = (session.end_time - session.start_time).total_seconds()
        else:
            total_time = (current_time - session.start_time).total_seconds()

        index.index_4_total_time = total_time

    def _calculate_efficiency_indices(
        self,
        index: ProductivityIndex,
        session: WorkerSession,
        zone_transitions: Optional[List[Dict]],
        current_time: datetime
    ):
        """
        Calculate indices 5-7 (efficiency)

        Args:
            index: ProductivityIndex to update
            session: Worker session
            zone_transitions: Zone transition records
            current_time: Current timestamp
        """
        # Index 5: Work efficiency (active time / total time %)
        if index.index_4_total_time > 0:
            index.index_5_work_efficiency = (
                index.index_1_active_time / index.index_4_total_time
            ) * 100.0
        else:
            index.index_5_work_efficiency = 0.0

        # Index 6: Zone transitions count
        if zone_transitions:
            index.index_6_zone_transitions = len(zone_transitions)
        else:
            # Estimate from zones visited
            index.index_6_zone_transitions = max(0, len(session.zones_visited) - 1)

        # Index 7: Average time per zone
        if index.index_6_zone_transitions > 0 and index.index_4_total_time > 0:
            # Approximate average time per zone
            index.index_7_avg_time_per_zone = (
                index.index_4_total_time / (index.index_6_zone_transitions + 1)
            )
        else:
            index.index_7_avg_time_per_zone = index.index_4_total_time

    def _calculate_output_indices(
        self,
        index: ProductivityIndex,
        session: WorkerSession,
        tasks_completed: int,
        quality_score: float,
        current_time: datetime
    ):
        """
        Calculate indices 8-10 (output)

        Args:
            index: ProductivityIndex to update
            session: Worker session
            tasks_completed: Number of tasks completed
            quality_score: Quality rating (0-100)
            current_time: Current timestamp
        """
        # Index 8: Tasks completed
        index.index_8_tasks_completed = tasks_completed

        # Index 9: Output per hour
        if index.index_4_total_time > 0:
            hours = index.index_4_total_time / 3600.0
            index.index_9_output_per_hour = tasks_completed / hours if hours > 0 else 0
        else:
            index.index_9_output_per_hour = 0.0

        # Index 10: Quality score
        index.index_10_quality_score = min(100.0, max(0.0, quality_score))

    def calculate_shift_summary(
        self,
        indices_list: List[ProductivityIndex]
    ) -> Dict:
        """
        Calculate summary statistics for a shift

        Args:
            indices_list: List of ProductivityIndex objects for the shift

        Returns:
            Dict with summary statistics
        """
        if not indices_list:
            return {
                'count': 0,
                'avg_overall_productivity': 0.0,
                'avg_work_efficiency': 0.0,
                'avg_output_per_hour': 0.0,
                'avg_quality_score': 0.0,
                'total_tasks_completed': 0
            }

        return {
            'count': len(indices_list),
            'avg_overall_productivity': np.mean([
                i.index_11_overall_productivity for i in indices_list
            ]),
            'avg_work_efficiency': np.mean([
                i.index_5_work_efficiency for i in indices_list
            ]),
            'avg_output_per_hour': np.mean([
                i.index_9_output_per_hour for i in indices_list
            ]),
            'avg_quality_score': np.mean([
                i.index_10_quality_score for i in indices_list
            ]),
            'total_tasks_completed': sum([
                i.index_8_tasks_completed for i in indices_list
            ]),
            'total_active_time': sum([
                i.index_1_active_time for i in indices_list
            ]),
            'total_time': sum([
                i.index_4_total_time for i in indices_list
            ])
        }

    def calculate_worker_trend(
        self,
        indices_list: List[ProductivityIndex],
        window_size: int = 5
    ) -> Dict:
        """
        Calculate productivity trend for a worker

        Args:
            indices_list: List of ProductivityIndex objects (chronological order)
            window_size: Moving average window size

        Returns:
            Dict with trend analysis
        """
        if len(indices_list) < 2:
            return {
                'trend': 'insufficient_data',
                'direction': 'stable',
                'recent_avg': 0.0,
                'change_percent': 0.0
            }

        # Get overall productivity scores
        scores = [i.index_11_overall_productivity for i in indices_list]

        # Calculate moving average
        if len(scores) >= window_size:
            recent_avg = np.mean(scores[-window_size:])
            previous_avg = np.mean(scores[-window_size*2:-window_size])
        else:
            recent_avg = np.mean(scores)
            previous_avg = scores[0]

        # Calculate change
        if previous_avg > 0:
            change_percent = ((recent_avg - previous_avg) / previous_avg) * 100
        else:
            change_percent = 0.0

        # Determine direction
        if change_percent > 5:
            direction = 'improving'
        elif change_percent < -5:
            direction = 'declining'
        else:
            direction = 'stable'

        return {
            'trend': direction,
            'direction': direction,
            'recent_avg': recent_avg,
            'change_percent': change_percent,
            'data_points': len(scores)
        }

    def get_recommendations(
        self,
        index: ProductivityIndex
    ) -> List[str]:
        """
        Get recommendations based on productivity indices

        Args:
            index: ProductivityIndex

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Work efficiency
        if index.index_5_work_efficiency < 60:
            recommendations.append(
                f"Low work efficiency ({index.index_5_work_efficiency:.1f}%). "
                f"Consider reducing idle time."
            )

        # Zone transitions
        if index.index_6_zone_transitions > 20:
            recommendations.append(
                f"High zone transitions ({index.index_6_zone_transitions}). "
                f"Optimize workflow to reduce movement."
            )

        # Output rate
        if index.index_9_output_per_hour < self.target_output_per_hour * 0.8:
            recommendations.append(
                f"Output below target ({index.index_9_output_per_hour:.1f}/{self.target_output_per_hour} per hour). "
                f"Review process efficiency."
            )

        # Quality score
        if index.index_10_quality_score < 80:
            recommendations.append(
                f"Quality score needs improvement ({index.index_10_quality_score:.1f}/100). "
                f"Focus on accuracy and quality."
            )

        # Overall productivity
        if index.index_11_overall_productivity < 70:
            recommendations.append(
                f"Overall productivity below standard ({index.index_11_overall_productivity:.1f}/100). "
                f"Comprehensive review recommended."
            )

        if not recommendations:
            recommendations.append(
                f"Excellent performance! Overall productivity: {index.index_11_overall_productivity:.1f}/100"
            )

        return recommendations

    def get_stats(self) -> dict:
        """Get calculator statistics"""
        return {
            'target_output_per_hour': self.target_output_per_hour,
            'quality_weight': self.quality_weight,
            'efficiency_weight': self.efficiency_weight,
            'time_weight': self.time_weight
        }
