"""
Anomaly Detector
Detects unusual patterns in worker performance
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in worker productivity data
    Uses statistical methods and historical comparison
    """

    def __init__(
        self,
        std_threshold: float = 2.0,
        min_data_points: int = 5
    ):
        """
        Initialize anomaly detector

        Args:
            std_threshold: Number of standard deviations for anomaly
            min_data_points: Minimum data points required for detection
        """
        self.std_threshold = std_threshold
        self.min_data_points = min_data_points

        logger.info(f"AnomalyDetector initialized (threshold={std_threshold}σ)")

    def detect_productivity_anomalies(
        self,
        current_value: float,
        historical_values: List[float]
    ) -> Dict[str, Any]:
        """
        Detect if current productivity is anomalous

        Args:
            current_value: Current productivity value
            historical_values: Historical productivity values

        Returns:
            Detection result with anomaly status
        """
        if len(historical_values) < self.min_data_points:
            return {
                'is_anomaly': False,
                'reason': 'insufficient_data',
                'data_points': len(historical_values)
            }

        # Calculate statistics
        mean = np.mean(historical_values)
        std = np.std(historical_values)

        if std == 0:
            return {
                'is_anomaly': False,
                'reason': 'no_variation',
                'mean': mean
            }

        # Calculate z-score
        z_score = (current_value - mean) / std

        is_anomaly = abs(z_score) > self.std_threshold

        result = {
            'is_anomaly': is_anomaly,
            'current_value': current_value,
            'historical_mean': mean,
            'historical_std': std,
            'z_score': z_score,
            'deviation': current_value - mean,
            'deviation_percent': ((current_value - mean) / mean * 100) if mean > 0 else 0
        }

        if is_anomaly:
            if z_score > 0:
                result['anomaly_type'] = 'unusually_high'
                result['severity'] = 'positive' if z_score > self.std_threshold * 1.5 else 'minor'
            else:
                result['anomaly_type'] = 'unusually_low'
                result['severity'] = 'critical' if z_score < -self.std_threshold * 1.5 else 'warning'

        return result

    def detect_efficiency_drop(
        self,
        current_efficiency: float,
        historical_efficiencies: List[float],
        drop_threshold: float = 0.15
    ) -> Dict[str, Any]:
        """
        Detect sudden efficiency drops

        Args:
            current_efficiency: Current efficiency (0-100)
            historical_efficiencies: Historical efficiency values
            drop_threshold: Minimum drop percentage to consider (0-1)

        Returns:
            Detection result
        """
        if len(historical_efficiencies) < self.min_data_points:
            return {'is_drop': False, 'reason': 'insufficient_data'}

        recent_avg = np.mean(historical_efficiencies[-5:])
        drop_percent = (recent_avg - current_efficiency) / recent_avg if recent_avg > 0 else 0

        is_drop = drop_percent > drop_threshold

        return {
            'is_drop': is_drop,
            'current_efficiency': current_efficiency,
            'recent_average': recent_avg,
            'drop_percent': drop_percent * 100,
            'severity': 'critical' if drop_percent > 0.25 else 'warning' if is_drop else 'normal'
        }

    def detect_quality_issues(
        self,
        recent_quality_scores: List[float],
        quality_threshold: float = 80.0
    ) -> Dict[str, Any]:
        """
        Detect quality score issues

        Args:
            recent_quality_scores: Recent quality scores
            quality_threshold: Minimum acceptable quality

        Returns:
            Detection result
        """
        if not recent_quality_scores:
            return {'has_issues': False, 'reason': 'no_data'}

        avg_quality = np.mean(recent_quality_scores)
        below_threshold = [q for q in recent_quality_scores if q < quality_threshold]

        has_issues = len(below_threshold) >= len(recent_quality_scores) / 2

        return {
            'has_issues': has_issues,
            'average_quality': avg_quality,
            'below_threshold_count': len(below_threshold),
            'total_count': len(recent_quality_scores),
            'severity': 'critical' if avg_quality < 60 else 'warning' if has_issues else 'normal'
        }

    def detect_idle_time_spike(
        self,
        current_idle_hours: float,
        historical_idle_hours: List[float],
        spike_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect unusual increases in idle time

        Args:
            current_idle_hours: Current idle time (hours)
            historical_idle_hours: Historical idle times
            spike_multiplier: Multiplier for spike detection

        Returns:
            Detection result
        """
        if len(historical_idle_hours) < self.min_data_points:
            return {'is_spike': False, 'reason': 'insufficient_data'}

        avg_idle = np.mean(historical_idle_hours)
        is_spike = current_idle_hours > avg_idle * spike_multiplier

        return {
            'is_spike': is_spike,
            'current_idle_hours': current_idle_hours,
            'average_idle_hours': avg_idle,
            'increase_factor': current_idle_hours / avg_idle if avg_idle > 0 else 0,
            'severity': 'warning' if is_spike else 'normal'
        }

    def detect_output_decline(
        self,
        current_output: float,
        historical_output: List[float],
        decline_threshold: float = 0.20
    ) -> Dict[str, Any]:
        """
        Detect significant output decline

        Args:
            current_output: Current output per hour
            historical_output: Historical output rates
            decline_threshold: Minimum decline percentage (0-1)

        Returns:
            Detection result
        """
        if len(historical_output) < self.min_data_points:
            return {'is_decline': False, 'reason': 'insufficient_data'}

        avg_output = np.mean(historical_output)
        decline_percent = (avg_output - current_output) / avg_output if avg_output > 0 else 0

        is_decline = decline_percent > decline_threshold

        return {
            'is_decline': is_decline,
            'current_output': current_output,
            'average_output': avg_output,
            'decline_percent': decline_percent * 100,
            'severity': 'critical' if decline_percent > 0.35 else 'warning' if is_decline else 'normal'
        }

    def analyze_worker_anomalies(
        self,
        current_indices: Dict[str, float],
        historical_indices: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Comprehensive anomaly analysis for a worker

        Args:
            current_indices: Current productivity indices
            historical_indices: List of historical productivity indices

        Returns:
            Complete anomaly analysis
        """
        anomalies = {
            'timestamp': datetime.now().isoformat(),
            'has_anomalies': False,
            'anomaly_count': 0,
            'details': []
        }

        # Extract historical values
        historical_productivity = [
            idx.get('index_11_overall_productivity', 0)
            for idx in historical_indices
        ]

        historical_efficiency = [
            idx.get('index_5_work_efficiency', 0)
            for idx in historical_indices
        ]

        historical_output = [
            idx.get('index_9_output_per_hour', 0)
            for idx in historical_indices
        ]

        historical_quality = [
            idx.get('index_10_quality_score', 0)
            for idx in historical_indices
        ]

        historical_idle = [
            idx.get('index_2_idle_time', 0) / 3600
            for idx in historical_indices
        ]

        # Check productivity anomaly
        productivity_anomaly = self.detect_productivity_anomalies(
            current_value=current_indices.get('index_11_overall_productivity', 0),
            historical_values=historical_productivity
        )

        if productivity_anomaly.get('is_anomaly'):
            anomalies['details'].append({
                'type': 'productivity',
                'data': productivity_anomaly
            })
            anomalies['anomaly_count'] += 1

        # Check efficiency drop
        efficiency_drop = self.detect_efficiency_drop(
            current_efficiency=current_indices.get('index_5_work_efficiency', 0),
            historical_efficiencies=historical_efficiency
        )

        if efficiency_drop.get('is_drop'):
            anomalies['details'].append({
                'type': 'efficiency_drop',
                'data': efficiency_drop
            })
            anomalies['anomaly_count'] += 1

        # Check quality issues
        quality_issues = self.detect_quality_issues(
            recent_quality_scores=historical_quality[-5:] + [current_indices.get('index_10_quality_score', 0)]
        )

        if quality_issues.get('has_issues'):
            anomalies['details'].append({
                'type': 'quality_issues',
                'data': quality_issues
            })
            anomalies['anomaly_count'] += 1

        # Check idle time spike
        idle_spike = self.detect_idle_time_spike(
            current_idle_hours=current_indices.get('index_2_idle_time', 0) / 3600,
            historical_idle_hours=historical_idle
        )

        if idle_spike.get('is_spike'):
            anomalies['details'].append({
                'type': 'idle_time_spike',
                'data': idle_spike
            })
            anomalies['anomaly_count'] += 1

        # Check output decline
        output_decline = self.detect_output_decline(
            current_output=current_indices.get('index_9_output_per_hour', 0),
            historical_output=historical_output
        )

        if output_decline.get('is_decline'):
            anomalies['details'].append({
                'type': 'output_decline',
                'data': output_decline
            })
            anomalies['anomaly_count'] += 1

        anomalies['has_anomalies'] = anomalies['anomaly_count'] > 0

        return anomalies

    def get_stats(self) -> dict:
        """Get detector statistics"""
        return {
            'std_threshold': self.std_threshold,
            'min_data_points': self.min_data_points
        }
