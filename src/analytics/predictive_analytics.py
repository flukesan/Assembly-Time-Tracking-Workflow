"""
Predictive Analytics
Time-series forecasting and predictive models for productivity and output.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class Forecast:
    """Forecast result"""
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float = 0.95
    forecast_date: Optional[datetime] = None
    model_type: str = "unknown"


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    trend: str  # "increasing", "decreasing", "stable"
    slope: float
    r_squared: float
    prediction_7days: float
    prediction_30days: float


class PredictiveAnalytics:
    """
    Predictive Analytics Engine

    Provides time-series forecasting and predictive models.
    Uses statistical methods for productivity and output prediction.
    """

    def __init__(self):
        """Initialize predictive analytics"""
        self.min_data_points = 5
        logger.info("Predictive Analytics initialized")

    def forecast_productivity(
        self,
        historical_data: List[float],
        forecast_days: int = 7,
        confidence_level: float = 0.95
    ) -> List[Forecast]:
        """
        Forecast future productivity values

        Args:
            historical_data: Historical productivity values (time-ordered)
            forecast_days: Number of days to forecast
            confidence_level: Confidence level for intervals (default 0.95)

        Returns:
            List of Forecast objects for each future day
        """
        if len(historical_data) < self.min_data_points:
            logger.warning(f"Insufficient data for forecasting (need {self.min_data_points})")
            return []

        try:
            # Use exponential smoothing for forecasting
            forecasts = []
            alpha = 0.3  # Smoothing parameter

            # Calculate smoothed series
            smoothed = self._exponential_smoothing(historical_data, alpha)

            # Calculate trend
            trend = self._calculate_trend(smoothed)

            # Standard deviation for confidence intervals
            std_dev = np.std(historical_data)

            # Forecast future values
            last_value = smoothed[-1]
            for day in range(1, forecast_days + 1):
                # Forecast with trend
                predicted = last_value + (trend * day)

                # Confidence intervals (wider as we go further)
                margin = 1.96 * std_dev * np.sqrt(day)  # 95% CI

                forecast = Forecast(
                    predicted_value=max(0, predicted),  # Can't be negative
                    confidence_lower=max(0, predicted - margin),
                    confidence_upper=min(100, predicted + margin),  # Cap at 100
                    confidence_level=confidence_level,
                    forecast_date=datetime.now() + timedelta(days=day),
                    model_type="exponential_smoothing"
                )
                forecasts.append(forecast)

            return forecasts

        except Exception as e:
            logger.error(f"Error forecasting productivity: {e}")
            return []

    def forecast_output(
        self,
        historical_output: List[int],
        forecast_days: int = 7,
        confidence_level: float = 0.95
    ) -> List[Forecast]:
        """
        Forecast future output values

        Args:
            historical_output: Historical output values (units produced)
            forecast_days: Number of days to forecast
            confidence_level: Confidence level for intervals

        Returns:
            List of Forecast objects for each future day
        """
        if len(historical_output) < self.min_data_points:
            logger.warning(f"Insufficient data for output forecasting")
            return []

        try:
            # Use moving average with trend
            forecasts = []

            # Calculate moving average
            window_size = min(7, len(historical_output))
            moving_avg = self._moving_average(historical_output, window_size)

            # Calculate trend from recent data
            recent_data = historical_output[-window_size:]
            trend = self._calculate_trend(recent_data)

            # Standard deviation for confidence intervals
            std_dev = np.std(historical_output)

            # Forecast future values
            last_value = moving_avg[-1]
            for day in range(1, forecast_days + 1):
                # Forecast with trend
                predicted = last_value + (trend * day)

                # Confidence intervals
                margin = 1.96 * std_dev * np.sqrt(day)

                forecast = Forecast(
                    predicted_value=max(0, predicted),
                    confidence_lower=max(0, predicted - margin),
                    confidence_upper=predicted + margin,
                    confidence_level=confidence_level,
                    forecast_date=datetime.now() + timedelta(days=day),
                    model_type="moving_average_with_trend"
                )
                forecasts.append(forecast)

            return forecasts

        except Exception as e:
            logger.error(f"Error forecasting output: {e}")
            return []

    def analyze_trend(
        self,
        time_series_data: List[float],
        data_type: str = "productivity"
    ) -> TrendAnalysis:
        """
        Analyze trend in time-series data

        Args:
            time_series_data: Time-ordered data points
            data_type: Type of data (productivity, output, efficiency)

        Returns:
            TrendAnalysis object with trend information
        """
        if len(time_series_data) < self.min_data_points:
            return TrendAnalysis(
                trend="unknown",
                slope=0.0,
                r_squared=0.0,
                prediction_7days=0.0,
                prediction_30days=0.0
            )

        try:
            # Linear regression for trend
            n = len(time_series_data)
            x = np.arange(n)
            y = np.array(time_series_data)

            # Calculate slope and intercept
            slope, intercept, r_squared = self._linear_regression(x, y)

            # Determine trend direction
            if abs(slope) < 0.1:
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"

            # Predictions
            prediction_7days = intercept + slope * (n + 7)
            prediction_30days = intercept + slope * (n + 30)

            return TrendAnalysis(
                trend=trend,
                slope=slope,
                r_squared=r_squared,
                prediction_7days=max(0, prediction_7days),
                prediction_30days=max(0, prediction_30days)
            )

        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return TrendAnalysis(
                trend="unknown",
                slope=0.0,
                r_squared=0.0,
                prediction_7days=0.0,
                prediction_30days=0.0
            )

    def predict_anomaly_probability(
        self,
        current_value: float,
        historical_data: List[float],
        threshold_std: float = 2.0
    ) -> Dict[str, Any]:
        """
        Predict probability of anomaly

        Args:
            current_value: Current value to check
            historical_data: Historical values for comparison
            threshold_std: Standard deviation threshold

        Returns:
            Dictionary with anomaly probability and details
        """
        if len(historical_data) < self.min_data_points:
            return {
                "is_anomaly": False,
                "probability": 0.0,
                "z_score": 0.0,
                "reason": "insufficient_data"
            }

        try:
            mean = np.mean(historical_data)
            std = np.std(historical_data)

            if std == 0:
                return {
                    "is_anomaly": False,
                    "probability": 0.0,
                    "z_score": 0.0,
                    "reason": "no_variance"
                }

            # Calculate z-score
            z_score = (current_value - mean) / std

            # Probability based on z-score (using normal distribution)
            probability = 1 - np.exp(-abs(z_score) / 2)

            is_anomaly = abs(z_score) > threshold_std

            return {
                "is_anomaly": is_anomaly,
                "probability": probability,
                "z_score": z_score,
                "mean": mean,
                "std": std,
                "deviation_percent": ((current_value - mean) / mean) * 100 if mean != 0 else 0,
                "severity": self._get_anomaly_severity(abs(z_score))
            }

        except Exception as e:
            logger.error(f"Error predicting anomaly: {e}")
            return {
                "is_anomaly": False,
                "probability": 0.0,
                "z_score": 0.0,
                "reason": f"error: {str(e)}"
            }

    def predict_worker_performance(
        self,
        worker_history: List[Dict[str, float]],
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict worker performance for upcoming days

        Args:
            worker_history: List of historical productivity records
                Each record: {"date": "2025-12-14", "productivity": 85.5, "efficiency": 78.2, ...}
            forecast_days: Number of days to forecast

        Returns:
            Dictionary with predictions for various metrics
        """
        if len(worker_history) < self.min_data_points:
            return {
                "error": "Insufficient historical data",
                "min_required": self.min_data_points,
                "data_points": len(worker_history)
            }

        try:
            # Extract time series for each metric
            productivity_series = [r.get("productivity", 0) for r in worker_history]
            efficiency_series = [r.get("efficiency", 0) for r in worker_history]
            output_series = [r.get("output", 0) for r in worker_history]

            # Forecast each metric
            productivity_forecast = self.forecast_productivity(productivity_series, forecast_days)
            output_forecast = self.forecast_output(output_series, forecast_days)
            efficiency_forecast = self.forecast_productivity(efficiency_series, forecast_days)

            # Analyze trends
            productivity_trend = self.analyze_trend(productivity_series, "productivity")
            efficiency_trend = self.analyze_trend(efficiency_series, "efficiency")

            # Calculate performance score
            recent_productivity = np.mean(productivity_series[-7:]) if len(productivity_series) >= 7 else np.mean(productivity_series)
            predicted_productivity = productivity_forecast[0].predicted_value if productivity_forecast else recent_productivity

            performance_change = predicted_productivity - recent_productivity

            return {
                "forecasts": {
                    "productivity": [
                        {
                            "day": i + 1,
                            "date": f.forecast_date.strftime("%Y-%m-%d") if f.forecast_date else None,
                            "predicted": round(f.predicted_value, 2),
                            "confidence_lower": round(f.confidence_lower, 2),
                            "confidence_upper": round(f.confidence_upper, 2)
                        }
                        for i, f in enumerate(productivity_forecast)
                    ],
                    "output": [
                        {
                            "day": i + 1,
                            "date": f.forecast_date.strftime("%Y-%m-%d") if f.forecast_date else None,
                            "predicted": int(f.predicted_value),
                            "confidence_lower": int(f.confidence_lower),
                            "confidence_upper": int(f.confidence_upper)
                        }
                        for i, f in enumerate(output_forecast)
                    ],
                    "efficiency": [
                        {
                            "day": i + 1,
                            "date": f.forecast_date.strftime("%Y-%m-%d") if f.forecast_date else None,
                            "predicted": round(f.predicted_value, 2),
                            "confidence_lower": round(f.confidence_lower, 2),
                            "confidence_upper": round(f.confidence_upper, 2)
                        }
                        for i, f in enumerate(efficiency_forecast)
                    ]
                },
                "trends": {
                    "productivity": {
                        "direction": productivity_trend.trend,
                        "slope": round(productivity_trend.slope, 3),
                        "r_squared": round(productivity_trend.r_squared, 3),
                        "prediction_7days": round(productivity_trend.prediction_7days, 2),
                        "prediction_30days": round(productivity_trend.prediction_30days, 2)
                    },
                    "efficiency": {
                        "direction": efficiency_trend.trend,
                        "slope": round(efficiency_trend.slope, 3),
                        "r_squared": round(efficiency_trend.r_squared, 3)
                    }
                },
                "summary": {
                    "current_productivity": round(recent_productivity, 2),
                    "predicted_productivity": round(predicted_productivity, 2),
                    "performance_change": round(performance_change, 2),
                    "trend": "improving" if performance_change > 0 else "declining" if performance_change < 0 else "stable",
                    "confidence": "high" if productivity_trend.r_squared > 0.7 else "medium" if productivity_trend.r_squared > 0.4 else "low"
                }
            }

        except Exception as e:
            logger.error(f"Error predicting worker performance: {e}")
            return {"error": str(e)}

    # Helper methods

    def _exponential_smoothing(self, data: List[float], alpha: float) -> List[float]:
        """Apply exponential smoothing"""
        smoothed = [data[0]]
        for i in range(1, len(data)):
            smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[i - 1])
        return smoothed

    def _moving_average(self, data: List[float], window_size: int) -> List[float]:
        """Calculate moving average"""
        if len(data) < window_size:
            return [np.mean(data)]

        moving_avg = []
        for i in range(len(data) - window_size + 1):
            window = data[i:i + window_size]
            moving_avg.append(np.mean(window))
        return moving_avg

    def _calculate_trend(self, data: List[float]) -> float:
        """Calculate linear trend (slope)"""
        if len(data) < 2:
            return 0.0

        n = len(data)
        x = np.arange(n)
        y = np.array(data)

        # Calculate slope
        x_mean = np.mean(x)
        y_mean = np.mean(y)

        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return slope

    def _linear_regression(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Perform linear regression

        Returns:
            (slope, intercept, r_squared)
        """
        x_mean = np.mean(x)
        y_mean = np.mean(y)

        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator == 0:
            return 0.0, y_mean, 0.0

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Calculate R²
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return slope, intercept, r_squared

    def _get_anomaly_severity(self, z_score: float) -> str:
        """Get anomaly severity based on z-score"""
        if z_score > 3.0:
            return "critical"
        elif z_score > 2.5:
            return "high"
        elif z_score > 2.0:
            return "medium"
        elif z_score > 1.5:
            return "low"
        else:
            return "normal"
