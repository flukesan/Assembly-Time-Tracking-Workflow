"""
Analytics REST API Endpoints
Advanced analytics queries and data retrieval.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from analytics.realtime_analytics import RealtimeAnalytics, EventType
from analytics.predictive_analytics import PredictiveAnalytics

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Global instances (will be injected)
realtime_analytics: Optional[RealtimeAnalytics] = None
predictive_analytics: Optional[PredictiveAnalytics] = None


def set_realtime_analytics(analytics: RealtimeAnalytics):
    """Inject real-time analytics instance"""
    global realtime_analytics
    realtime_analytics = analytics


def set_predictive_analytics(analytics: PredictiveAnalytics):
    """Inject predictive analytics instance"""
    global predictive_analytics
    predictive_analytics = analytics


# Pydantic models
class MetricsSnapshot(BaseModel):
    """Current metrics snapshot"""
    total_workers: int
    active_workers: int
    avg_productivity: float
    total_output: int
    alerts_count: int
    last_update: str


class AnalyticsStats(BaseModel):
    """Analytics system statistics"""
    active_connections: int
    event_queue_size: int
    event_history_size: int
    is_running: bool
    current_metrics: Dict[str, Any]


class EventHistoryRequest(BaseModel):
    """Event history query request"""
    event_type: Optional[str] = Field(None, description="Filter by event type")
    limit: int = Field(50, ge=1, le=500, description="Maximum events to return")


class EventHistoryResponse(BaseModel):
    """Event history response"""
    total_events: int
    events: List[Dict[str, Any]]


# Endpoints

@router.get("/metrics", response_model=MetricsSnapshot)
async def get_current_metrics():
    """
    Get current real-time metrics snapshot

    Returns:
        Current metrics including worker counts, productivity, output, etc.
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        metrics = await realtime_analytics.get_metrics_snapshot()
        return MetricsSnapshot(**metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AnalyticsStats)
async def get_analytics_stats():
    """
    Get analytics system statistics

    Returns:
        System statistics including connection count, queue sizes, etc.
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        stats = realtime_analytics.get_stats()
        return AnalyticsStats(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=EventHistoryResponse)
async def get_event_history(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum events to return")
):
    """
    Get event history

    Args:
        event_type: Optional event type filter (worker_status, productivity_update, etc.)
        limit: Maximum number of events to return (1-500)

    Returns:
        List of historical events
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        # Validate event type
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type. Valid types: {[e.value for e in EventType]}"
                )

        events = await realtime_analytics.get_event_history(
            event_type=event_type_enum,
            limit=limit
        )

        return EventHistoryResponse(
            total_events=len(events),
            events=events
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def get_connection_info():
    """
    Get WebSocket connection information

    Returns:
        Information about active WebSocket connections
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        return {
            "active_connections": realtime_analytics.get_connection_count(),
            "is_running": realtime_analytics.is_running,
            "websocket_endpoints": [
                "/ws/analytics",
                "/ws/live-metrics"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-event")
async def test_event(
    event_type: str = Query(..., description="Event type to test"),
    message: str = Query("Test event", description="Test message")
):
    """
    Test event publishing (development only)

    Args:
        event_type: Type of event to publish
        message: Test message

    Returns:
        Success message
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        # Validate event type
        try:
            EventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type. Valid types: {[e.value for e in EventType]}"
            )

        # Publish test event based on type
        if event_type == "worker_status":
            await realtime_analytics.update_worker_status(
                worker_id="TEST001",
                worker_name="Test Worker",
                status="active",
                current_zone="Test Zone",
                productivity=85.5
            )
        elif event_type == "productivity_update":
            await realtime_analytics.update_productivity(
                worker_id="TEST001",
                worker_name="Test Worker",
                indices={
                    "index_11_overall_productivity": 85.5,
                    "index_5_work_efficiency": 78.2
                },
                shift="morning"
            )
        elif event_type == "alert":
            await realtime_analytics.publish_alert(
                alert_type="test_alert",
                message=message,
                severity="warning",
                worker_id="TEST001",
                worker_name="Test Worker"
            )
        elif event_type == "system_status":
            await realtime_analytics.publish_system_status({
                "status": "healthy",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=400, detail="Event type not supported for testing")

        return {
            "success": True,
            "event_type": event_type,
            "message": "Test event published successfully",
            "active_connections": realtime_analytics.get_connection_count()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Predictive Analytics Endpoints
# ============================================================================

@router.post("/predict/productivity")
async def predict_productivity(
    historical_data: List[float] = Query(..., description="Historical productivity values"),
    forecast_days: int = Query(7, ge=1, le=30, description="Days to forecast")
):
    """
    Forecast future productivity values

    Args:
        historical_data: List of historical productivity values (time-ordered)
        forecast_days: Number of days to forecast (1-30)

    Returns:
        Productivity forecast with confidence intervals
    """
    if not predictive_analytics:
        raise HTTPException(status_code=503, detail="Predictive analytics not initialized")

    try:
        forecasts = predictive_analytics.forecast_productivity(
            historical_data=historical_data,
            forecast_days=forecast_days
        )

        return {
            "forecast_days": forecast_days,
            "forecasts": [
                {
                    "day": i + 1,
                    "date": f.forecast_date.strftime("%Y-%m-%d") if f.forecast_date else None,
                    "predicted_value": round(f.predicted_value, 2),
                    "confidence_lower": round(f.confidence_lower, 2),
                    "confidence_upper": round(f.confidence_upper, 2),
                    "model": f.model_type
                }
                for i, f in enumerate(forecasts)
            ],
            "historical_mean": round(sum(historical_data) / len(historical_data), 2),
            "data_points": len(historical_data)
        }

    except Exception as e:
        logger.error(f"Error predicting productivity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/output")
async def predict_output(
    historical_output: List[int] = Query(..., description="Historical output values"),
    forecast_days: int = Query(7, ge=1, le=30, description="Days to forecast")
):
    """
    Forecast future output values

    Args:
        historical_output: List of historical output values (units produced)
        forecast_days: Number of days to forecast (1-30)

    Returns:
        Output forecast with confidence intervals
    """
    if not predictive_analytics:
        raise HTTPException(status_code=503, detail="Predictive analytics not initialized")

    try:
        forecasts = predictive_analytics.forecast_output(
            historical_output=historical_output,
            forecast_days=forecast_days
        )

        return {
            "forecast_days": forecast_days,
            "forecasts": [
                {
                    "day": i + 1,
                    "date": f.forecast_date.strftime("%Y-%m-%d") if f.forecast_date else None,
                    "predicted_value": int(f.predicted_value),
                    "confidence_lower": int(f.confidence_lower),
                    "confidence_upper": int(f.confidence_upper),
                    "model": f.model_type
                }
                for i, f in enumerate(forecasts)
            ],
            "historical_mean": round(sum(historical_output) / len(historical_output), 2),
            "total_historical_output": sum(historical_output),
            "data_points": len(historical_output)
        }

    except Exception as e:
        logger.error(f"Error predicting output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/trend")
async def analyze_trend(
    time_series_data: List[float] = Query(..., description="Time-series data"),
    data_type: str = Query("productivity", description="Type of data")
):
    """
    Analyze trend in time-series data

    Args:
        time_series_data: Time-ordered data points
        data_type: Type of data (productivity, output, efficiency)

    Returns:
        Trend analysis with predictions
    """
    if not predictive_analytics:
        raise HTTPException(status_code=503, detail="Predictive analytics not initialized")

    try:
        trend_analysis = predictive_analytics.analyze_trend(
            time_series_data=time_series_data,
            data_type=data_type
        )

        return {
            "data_type": data_type,
            "trend": trend_analysis.trend,
            "slope": round(trend_analysis.slope, 4),
            "r_squared": round(trend_analysis.r_squared, 4),
            "prediction_7days": round(trend_analysis.prediction_7days, 2),
            "prediction_30days": round(trend_analysis.prediction_30days, 2),
            "data_points": len(time_series_data),
            "interpretation": {
                "trend_strength": "strong" if trend_analysis.r_squared > 0.7 else "moderate" if trend_analysis.r_squared > 0.4 else "weak",
                "trend_description": f"The {data_type} is {trend_analysis.trend} with a {'strong' if trend_analysis.r_squared > 0.7 else 'moderate' if trend_analysis.r_squared > 0.4 else 'weak'} trend."
            }
        }

    except Exception as e:
        logger.error(f"Error analyzing trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/anomaly")
async def predict_anomaly(
    current_value: float = Query(..., description="Current value to check"),
    historical_data: List[float] = Query(..., description="Historical data"),
    threshold_std: float = Query(2.0, description="Standard deviation threshold")
):
    """
    Predict anomaly probability

    Args:
        current_value: Current value to check
        historical_data: Historical values for comparison
        threshold_std: Standard deviation threshold (default 2.0)

    Returns:
        Anomaly prediction with probability and details
    """
    if not predictive_analytics:
        raise HTTPException(status_code=503, detail="Predictive analytics not initialized")

    try:
        prediction = predictive_analytics.predict_anomaly_probability(
            current_value=current_value,
            historical_data=historical_data,
            threshold_std=threshold_std
        )

        return {
            "current_value": current_value,
            "threshold_std": threshold_std,
            **prediction
        }

    except Exception as e:
        logger.error(f"Error predicting anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/worker-performance")
async def predict_worker_performance(
    worker_id: str = Query(..., description="Worker ID"),
    worker_history: List[Dict[str, Any]] = Query(..., description="Worker history"),
    forecast_days: int = Query(7, ge=1, le=30, description="Days to forecast")
):
    """
    Predict worker performance for upcoming days

    Args:
        worker_id: Worker ID
        worker_history: List of historical productivity records
        forecast_days: Number of days to forecast

    Returns:
        Comprehensive performance prediction
    """
    if not predictive_analytics:
        raise HTTPException(status_code=503, detail="Predictive analytics not initialized")

    try:
        prediction = predictive_analytics.predict_worker_performance(
            worker_history=worker_history,
            forecast_days=forecast_days
        )

        if "error" in prediction:
            raise HTTPException(status_code=400, detail=prediction["error"])

        return {
            "worker_id": worker_id,
            "forecast_days": forecast_days,
            "data_points": len(worker_history),
            **prediction
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting worker performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
