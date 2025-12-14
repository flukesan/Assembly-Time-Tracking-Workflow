"""
Visualization Data Generators
Generates data structures optimized for various chart and visualization types.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from loguru import logger


class VisualizationData:
    """
    Visualization Data Generator

    Generates data structures for various visualization types including
    heatmaps, time-series charts, distributions, and correlations.
    """

    def __init__(self):
        """Initialize visualization data generator"""
        logger.info("Visualization Data Generator initialized")

    def generate_productivity_heatmap(
        self,
        data: List[Dict[str, Any]],
        x_axis: str = "hour",  # hour, day, week
        y_axis: str = "worker",  # worker, zone, shift
        value_field: str = "productivity"
    ) -> Dict[str, Any]:
        """
        Generate heatmap data for productivity visualization

        Args:
            data: List of productivity records
            x_axis: X-axis dimension (hour, day, week)
            y_axis: Y-axis dimension (worker, zone, shift)
            value_field: Field to visualize (productivity, efficiency, output)

        Returns:
            Heatmap data structure
        """
        try:
            # Initialize heatmap matrix
            x_labels = []
            y_labels = []
            values = defaultdict(lambda: defaultdict(list))

            # Process data
            for record in data:
                x_value = self._extract_dimension(record, x_axis)
                y_value = self._extract_dimension(record, y_axis)
                val = record.get(value_field, 0)

                if x_value not in x_labels:
                    x_labels.append(x_value)
                if y_value not in y_labels:
                    y_labels.append(y_value)

                values[y_value][x_value].append(val)

            # Sort labels
            x_labels = sorted(x_labels)
            y_labels = sorted(y_labels)

            # Calculate averages for each cell
            matrix = []
            for y in y_labels:
                row = []
                for x in x_labels:
                    cell_values = values[y][x]
                    avg = np.mean(cell_values) if cell_values else 0
                    row.append(round(avg, 2))
                matrix.append(row)

            return {
                "x_labels": x_labels,
                "y_labels": y_labels,
                "values": matrix,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "value_field": value_field,
                "min_value": round(float(np.min([v for row in matrix for v in row])), 2) if matrix else 0,
                "max_value": round(float(np.max([v for row in matrix for v in row])), 2) if matrix else 0,
                "data_points": len(data)
            }

        except Exception as e:
            logger.error(f"Error generating productivity heatmap: {e}")
            return {
                "error": str(e),
                "x_labels": [],
                "y_labels": [],
                "values": []
            }

    def generate_time_series_chart(
        self,
        data: List[Dict[str, Any]],
        time_field: str = "timestamp",
        value_fields: List[str] = None,
        aggregation: str = "mean",  # mean, sum, count, min, max
        interval: str = "hour"  # hour, day, week, month
    ) -> Dict[str, Any]:
        """
        Generate time-series chart data

        Args:
            data: List of records with timestamps
            time_field: Field containing timestamp
            value_fields: Fields to plot (if None, use all numeric fields)
            aggregation: Aggregation method
            interval: Time interval for grouping

        Returns:
            Time-series chart data
        """
        try:
            if value_fields is None:
                # Auto-detect numeric fields
                value_fields = []
                if data:
                    for key, val in data[0].items():
                        if isinstance(val, (int, float)) and key != time_field:
                            value_fields.append(key)

            # Group data by time interval
            time_groups = defaultdict(lambda: defaultdict(list))

            for record in data:
                timestamp = record.get(time_field)
                if not timestamp:
                    continue

                # Group by interval
                time_key = self._get_time_interval_key(timestamp, interval)

                for field in value_fields:
                    value = record.get(field)
                    if value is not None:
                        time_groups[time_key][field].append(value)

            # Sort time keys
            sorted_times = sorted(time_groups.keys())

            # Aggregate values
            series_data = defaultdict(list)
            timestamps = []

            for time_key in sorted_times:
                timestamps.append(time_key)
                for field in value_fields:
                    values = time_groups[time_key][field]
                    if values:
                        agg_value = self._aggregate(values, aggregation)
                        series_data[field].append(round(agg_value, 2))
                    else:
                        series_data[field].append(None)

            return {
                "timestamps": timestamps,
                "series": {
                    field: series_data[field]
                    for field in value_fields
                },
                "interval": interval,
                "aggregation": aggregation,
                "data_points": len(data)
            }

        except Exception as e:
            logger.error(f"Error generating time-series chart: {e}")
            return {
                "error": str(e),
                "timestamps": [],
                "series": {}
            }

    def generate_distribution_chart(
        self,
        data: List[float],
        bins: int = 10,
        value_name: str = "value"
    ) -> Dict[str, Any]:
        """
        Generate distribution chart data (histogram)

        Args:
            data: List of values
            bins: Number of bins
            value_name: Name of the value being analyzed

        Returns:
            Distribution chart data
        """
        try:
            if not data:
                return {
                    "error": "No data provided",
                    "bins": [],
                    "counts": []
                }

            # Calculate histogram
            counts, bin_edges = np.histogram(data, bins=bins)

            # Format bin labels
            bin_labels = []
            for i in range(len(counts)):
                label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
                bin_labels.append(label)

            # Calculate statistics
            mean = np.mean(data)
            median = np.median(data)
            std = np.std(data)
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)

            return {
                "bin_labels": bin_labels,
                "counts": counts.tolist(),
                "value_name": value_name,
                "statistics": {
                    "mean": round(mean, 2),
                    "median": round(median, 2),
                    "std": round(std, 2),
                    "min": round(float(np.min(data)), 2),
                    "max": round(float(np.max(data)), 2),
                    "q1": round(q1, 2),
                    "q3": round(q3, 2)
                },
                "data_points": len(data)
            }

        except Exception as e:
            logger.error(f"Error generating distribution chart: {e}")
            return {
                "error": str(e),
                "bins": [],
                "counts": []
            }

    def generate_correlation_matrix(
        self,
        data: List[Dict[str, float]],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate correlation matrix

        Args:
            data: List of records with numeric fields
            fields: Fields to correlate (if None, use all numeric fields)

        Returns:
            Correlation matrix data
        """
        try:
            if not data:
                return {
                    "error": "No data provided",
                    "fields": [],
                    "matrix": []
                }

            # Auto-detect numeric fields if not specified
            if fields is None:
                fields = []
                for key, val in data[0].items():
                    if isinstance(val, (int, float)):
                        fields.append(key)

            # Extract values for each field
            field_values = {field: [] for field in fields}
            for record in data:
                for field in fields:
                    value = record.get(field)
                    if value is not None:
                        field_values[field].append(value)

            # Calculate correlation matrix
            n = len(fields)
            matrix = [[0.0 for _ in range(n)] for _ in range(n)]

            for i, field1 in enumerate(fields):
                for j, field2 in enumerate(fields):
                    if i == j:
                        matrix[i][j] = 1.0
                    else:
                        corr = self._calculate_correlation(
                            field_values[field1],
                            field_values[field2]
                        )
                        matrix[i][j] = round(corr, 3)

            return {
                "fields": fields,
                "matrix": matrix,
                "data_points": len(data)
            }

        except Exception as e:
            logger.error(f"Error generating correlation matrix: {e}")
            return {
                "error": str(e),
                "fields": [],
                "matrix": []
            }

    def generate_comparison_chart(
        self,
        data: List[Dict[str, Any]],
        group_by: str,
        value_field: str,
        aggregation: str = "mean"
    ) -> Dict[str, Any]:
        """
        Generate comparison chart data (bar chart)

        Args:
            data: List of records
            group_by: Field to group by
            value_field: Field to aggregate
            aggregation: Aggregation method

        Returns:
            Comparison chart data
        """
        try:
            # Group data
            groups = defaultdict(list)
            for record in data:
                group = record.get(group_by)
                value = record.get(value_field)
                if group is not None and value is not None:
                    groups[group].append(value)

            # Aggregate
            labels = sorted(groups.keys(), key=str)
            values = []

            for label in labels:
                group_values = groups[label]
                agg_value = self._aggregate(group_values, aggregation)
                values.append(round(agg_value, 2))

            return {
                "labels": [str(l) for l in labels],
                "values": values,
                "group_by": group_by,
                "value_field": value_field,
                "aggregation": aggregation,
                "data_points": len(data)
            }

        except Exception as e:
            logger.error(f"Error generating comparison chart: {e}")
            return {
                "error": str(e),
                "labels": [],
                "values": []
            }

    def generate_gauge_chart(
        self,
        current_value: float,
        min_value: float = 0,
        max_value: float = 100,
        thresholds: Optional[List[Tuple[float, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate gauge chart data

        Args:
            current_value: Current value
            min_value: Minimum value
            max_value: Maximum value
            thresholds: List of (threshold, color/label) tuples

        Returns:
            Gauge chart data
        """
        try:
            # Default thresholds if not provided
            if thresholds is None:
                thresholds = [
                    (33.33, "low"),
                    (66.67, "medium"),
                    (100.0, "high")
                ]

            # Calculate percentage
            percentage = ((current_value - min_value) / (max_value - min_value)) * 100

            # Determine current threshold
            current_threshold = "unknown"
            for threshold, label in thresholds:
                if percentage <= threshold:
                    current_threshold = label
                    break

            return {
                "current_value": round(current_value, 2),
                "min_value": min_value,
                "max_value": max_value,
                "percentage": round(percentage, 2),
                "threshold": current_threshold,
                "thresholds": thresholds
            }

        except Exception as e:
            logger.error(f"Error generating gauge chart: {e}")
            return {
                "error": str(e),
                "current_value": 0,
                "percentage": 0
            }

    # Helper methods

    def _extract_dimension(self, record: Dict[str, Any], dimension: str) -> str:
        """Extract dimension value from record"""
        if dimension == "hour":
            timestamp = record.get("timestamp", datetime.now())
            return str(timestamp.hour if hasattr(timestamp, 'hour') else 0)
        elif dimension == "day":
            timestamp = record.get("timestamp", datetime.now())
            return timestamp.strftime("%Y-%m-%d") if hasattr(timestamp, 'strftime') else "unknown"
        elif dimension == "week":
            timestamp = record.get("timestamp", datetime.now())
            return f"W{timestamp.isocalendar()[1]}" if hasattr(timestamp, 'isocalendar') else "unknown"
        elif dimension in record:
            return str(record[dimension])
        else:
            return "unknown"

    def _get_time_interval_key(self, timestamp: datetime, interval: str) -> str:
        """Get time interval key from timestamp"""
        if interval == "hour":
            return timestamp.strftime("%Y-%m-%d %H:00")
        elif interval == "day":
            return timestamp.strftime("%Y-%m-%d")
        elif interval == "week":
            return f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
        elif interval == "month":
            return timestamp.strftime("%Y-%m")
        else:
            return str(timestamp)

    def _aggregate(self, values: List[float], aggregation: str) -> float:
        """Aggregate values using specified method"""
        if not values:
            return 0.0

        if aggregation == "mean":
            return np.mean(values)
        elif aggregation == "sum":
            return np.sum(values)
        elif aggregation == "count":
            return len(values)
        elif aggregation == "min":
            return np.min(values)
        elif aggregation == "max":
            return np.max(values)
        elif aggregation == "median":
            return np.median(values)
        else:
            return np.mean(values)  # Default to mean

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        # Remove None values
        pairs = [(xi, yi) for xi, yi in zip(x, y) if xi is not None and yi is not None]
        if len(pairs) < 2:
            return 0.0

        x_clean, y_clean = zip(*pairs)
        x_arr = np.array(x_clean)
        y_arr = np.array(y_clean)

        # Calculate correlation
        if np.std(x_arr) == 0 or np.std(y_arr) == 0:
            return 0.0

        corr = np.corrcoef(x_arr, y_arr)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0
