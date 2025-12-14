"""
Performance Benchmarking
Compare worker/team performance against benchmarks and historical data.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class BenchmarkResult:
    """Benchmark comparison result"""
    current_value: float
    benchmark_value: float
    difference: float
    difference_percent: float
    performance_level: str  # "excellent", "good", "average", "below_average", "poor"


class Benchmarking:
    """
    Performance Benchmarking Engine

    Compares current performance against benchmarks,
    historical data, and peer groups.
    """

    def __init__(self):
        """Initialize benchmarking engine"""
        self.default_benchmarks = {
            "productivity": 75.0,
            "efficiency": 70.0,
            "quality": 85.0,
            "output_per_hour": 10.0
        }
        logger.info("Benchmarking Engine initialized")

    def compare_to_benchmark(
        self,
        current_value: float,
        metric_name: str,
        benchmark_value: Optional[float] = None
    ) -> BenchmarkResult:
        """
        Compare current value to benchmark

        Args:
            current_value: Current metric value
            metric_name: Name of metric
            benchmark_value: Benchmark value (uses default if None)

        Returns:
            BenchmarkResult object
        """
        if benchmark_value is None:
            benchmark_value = self.default_benchmarks.get(metric_name, 75.0)

        difference = current_value - benchmark_value
        difference_percent = (difference / benchmark_value * 100) if benchmark_value != 0 else 0

        # Determine performance level
        if difference_percent >= 20:
            level = "excellent"
        elif difference_percent >= 10:
            level = "good"
        elif difference_percent >= -5:
            level = "average"
        elif difference_percent >= -15:
            level = "below_average"
        else:
            level = "poor"

        return BenchmarkResult(
            current_value=round(current_value, 2),
            benchmark_value=round(benchmark_value, 2),
            difference=round(difference, 2),
            difference_percent=round(difference_percent, 2),
            performance_level=level
        )

    def compare_to_historical(
        self,
        current_value: float,
        historical_values: List[float],
        comparison_period: str = "all"  # all, recent_7days, recent_30days
    ) -> Dict[str, Any]:
        """
        Compare to historical performance

        Args:
            current_value: Current value
            historical_values: Historical values
            comparison_period: Period to compare against

        Returns:
            Comparison results
        """
        if not historical_values:
            return {"error": "No historical data"}

        # Filter historical data based on period
        if comparison_period == "recent_7days" and len(historical_values) > 7:
            historical_values = historical_values[-7:]
        elif comparison_period == "recent_30days" and len(historical_values) > 30:
            historical_values = historical_values[-30:]

        mean = np.mean(historical_values)
        median = np.median(historical_values)
        std = np.std(historical_values)
        min_val = np.min(historical_values)
        max_val = np.max(historical_values)

        # Calculate percentile rank
        percentile_rank = (sum(1 for v in historical_values if v <= current_value) / len(historical_values)) * 100

        # Determine trend
        if current_value > mean + std:
            trend = "significantly_above_average"
        elif current_value > mean:
            trend = "above_average"
        elif current_value > mean - std:
            trend = "average"
        else:
            trend = "below_average"

        return {
            "current_value": round(current_value, 2),
            "historical_mean": round(mean, 2),
            "historical_median": round(median, 2),
            "historical_std": round(std, 2),
            "historical_min": round(float(min_val), 2),
            "historical_max": round(float(max_val), 2),
            "percentile_rank": round(percentile_rank, 2),
            "trend": trend,
            "difference_from_mean": round(current_value - mean, 2),
            "difference_percent": round(((current_value - mean) / mean * 100) if mean != 0 else 0, 2),
            "data_points": len(historical_values)
        }

    def compare_to_peers(
        self,
        worker_value: float,
        peer_values: List[float],
        worker_name: str = "Worker"
    ) -> Dict[str, Any]:
        """
        Compare to peer group

        Args:
            worker_value: Worker's value
            peer_values: Peer group values
            worker_name: Worker name

        Returns:
            Peer comparison results
        """
        if not peer_values:
            return {"error": "No peer data"}

        all_values = peer_values + [worker_value]
        all_values_sorted = sorted(all_values, reverse=True)

        rank = all_values_sorted.index(worker_value) + 1
        total = len(all_values)

        peer_mean = np.mean(peer_values)
        peer_median = np.median(peer_values)
        peer_std = np.std(peer_values)

        # Calculate percentile
        percentile = ((total - rank) / total) * 100

        # Determine ranking category
        if percentile >= 90:
            category = "top_10_percent"
        elif percentile >= 75:
            category = "top_25_percent"
        elif percentile >= 50:
            category = "above_median"
        elif percentile >= 25:
            category = "below_median"
        else:
            category = "bottom_25_percent"

        return {
            "worker_name": worker_name,
            "worker_value": round(worker_value, 2),
            "rank": rank,
            "total_workers": total,
            "percentile": round(percentile, 2),
            "category": category,
            "peer_mean": round(peer_mean, 2),
            "peer_median": round(peer_median, 2),
            "peer_std": round(peer_std, 2),
            "difference_from_mean": round(worker_value - peer_mean, 2),
            "difference_percent": round(((worker_value - peer_mean) / peer_mean * 100) if peer_mean != 0 else 0, 2)
        }

    def generate_performance_score(
        self,
        metrics: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate weighted performance score

        Args:
            metrics: Dictionary of metric values
            weights: Dictionary of weights (default: equal weights)

        Returns:
            Performance score and breakdown
        """
        if not metrics:
            return {"error": "No metrics provided"}

        # Default equal weights
        if weights is None:
            weights = {k: 1.0 for k in metrics.keys()}

        # Normalize weights
        total_weight = sum(weights.values())
        normalized_weights = {k: v / total_weight for k, v in weights.items()}

        # Calculate weighted score
        weighted_score = sum(
            metrics[k] * normalized_weights.get(k, 0)
            for k in metrics.keys()
        )

        # Calculate contribution of each metric
        contributions = {
            k: round((metrics[k] * normalized_weights.get(k, 0) / weighted_score * 100) if weighted_score != 0 else 0, 2)
            for k in metrics.keys()
        }

        return {
            "weighted_score": round(weighted_score, 2),
            "metrics": {k: round(v, 2) for k, v in metrics.items()},
            "weights": {k: round(v, 3) for k, v in normalized_weights.items()},
            "contributions": contributions
        }

    def analyze_consistency(
        self,
        values: List[float],
        metric_name: str = "metric"
    ) -> Dict[str, Any]:
        """
        Analyze performance consistency

        Args:
            values: List of values
            metric_name: Name of metric

        Returns:
            Consistency analysis
        """
        if len(values) < 2:
            return {"error": "Insufficient data"}

        mean = np.mean(values)
        std = np.std(values)
        cv = (std / mean * 100) if mean != 0 else 0  # Coefficient of variation

        # Determine consistency level
        if cv < 10:
            consistency = "very_consistent"
        elif cv < 20:
            consistency = "consistent"
        elif cv < 30:
            consistency = "moderate"
        elif cv < 40:
            consistency = "inconsistent"
        else:
            consistency = "very_inconsistent"

        # Calculate consecutive differences
        diffs = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        avg_change = np.mean(diffs) if diffs else 0

        return {
            "metric_name": metric_name,
            "consistency_level": consistency,
            "coefficient_of_variation": round(cv, 2),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(float(np.min(values)), 2),
            "max": round(float(np.max(values)), 2),
            "range": round(float(np.max(values) - np.min(values)), 2),
            "average_consecutive_change": round(avg_change, 2),
            "data_points": len(values)
        }
