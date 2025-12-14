"""
Automated Insights Module
Generates AI-powered insights and recommendations
"""

from .insight_generator import InsightGenerator
from .anomaly_detector import AnomalyDetector
from .recommendation_engine import RecommendationEngine

__all__ = ["InsightGenerator", "AnomalyDetector", "RecommendationEngine"]
