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
from analytics.visualization_data import VisualizationData
from analytics.benchmarking import Benchmarking
from analytics.export_manager import ExportManager

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Global instances (will be injected)
realtime_analytics: Optional[RealtimeAnalytics] = None
predictive_analytics: Optional[PredictiveAnalytics] = None
visualization_data: Optional[VisualizationData] = None
benchmarking: Optional[Benchmarking] = None
export_manager: Optional[ExportManager] = None


def set_realtime_analytics(analytics: RealtimeAnalytics):
    """Inject real-time analytics instance"""
    global realtime_analytics
    realtime_analytics = analytics


def set_predictive_analytics(analytics: PredictiveAnalytics):
    """Inject predictive analytics instance"""
    global predictive_analytics
    predictive_analytics = analytics


def set_visualization_data(viz_data: VisualizationData):
    """Inject visualization data instance"""
    global visualization_data
    visualization_data = viz_data


def set_benchmarking(bench: Benchmarking):
    """Inject benchmarking instance"""
    global benchmarking
    benchmarking = bench


def set_export_manager(export_mgr: ExportManager):
    """Inject export manager instance"""
    global export_manager
    export_manager = export_mgr


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


# ============================================================================
# Visualization Data Endpoints
# ============================================================================

@router.post("/visualize/heatmap")
async def generate_heatmap(
    data: List[Dict[str, Any]],
    x_axis: str = Query("hour", description="X-axis dimension"),
    y_axis: str = Query("worker", description="Y-axis dimension"),
    value_field: str = Query("productivity", description="Value field")
):
    """
    Generate productivity heatmap data

    Args:
        data: List of productivity records
        x_axis: X-axis dimension (hour, day, week)
        y_axis: Y-axis dimension (worker, zone, shift)
        value_field: Field to visualize

    Returns:
        Heatmap data structure
    """
    if not visualization_data:
        raise HTTPException(status_code=503, detail="Visualization data not initialized")

    try:
        heatmap = visualization_data.generate_productivity_heatmap(
            data=data,
            x_axis=x_axis,
            y_axis=y_axis,
            value_field=value_field
        )

        return heatmap

    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize/time-series")
async def generate_time_series(
    data: List[Dict[str, Any]],
    time_field: str = Query("timestamp", description="Time field"),
    value_fields: Optional[List[str]] = Query(None, description="Value fields to plot"),
    aggregation: str = Query("mean", description="Aggregation method"),
    interval: str = Query("hour", description="Time interval")
):
    """
    Generate time-series chart data

    Args:
        data: List of records with timestamps
        time_field: Field containing timestamp
        value_fields: Fields to plot
        aggregation: Aggregation method (mean, sum, count, min, max)
        interval: Time interval (hour, day, week, month)

    Returns:
        Time-series chart data
    """
    if not visualization_data:
        raise HTTPException(status_code=503, detail="Visualization data not initialized")

    try:
        chart = visualization_data.generate_time_series_chart(
            data=data,
            time_field=time_field,
            value_fields=value_fields,
            aggregation=aggregation,
            interval=interval
        )

        return chart

    except Exception as e:
        logger.error(f"Error generating time-series: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize/distribution")
async def generate_distribution(
    data: List[float],
    bins: int = Query(10, ge=5, le=50, description="Number of bins"),
    value_name: str = Query("value", description="Value name")
):
    """
    Generate distribution chart data (histogram)

    Args:
        data: List of values
        bins: Number of bins (5-50)
        value_name: Name of the value

    Returns:
        Distribution chart data with statistics
    """
    if not visualization_data:
        raise HTTPException(status_code=503, detail="Visualization data not initialized")

    try:
        distribution = visualization_data.generate_distribution_chart(
            data=data,
            bins=bins,
            value_name=value_name
        )

        return distribution

    except Exception as e:
        logger.error(f"Error generating distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize/correlation")
async def generate_correlation(
    data: List[Dict[str, float]],
    fields: Optional[List[str]] = Query(None, description="Fields to correlate")
):
    """
    Generate correlation matrix

    Args:
        data: List of records with numeric fields
        fields: Fields to correlate (if None, use all numeric fields)

    Returns:
        Correlation matrix
    """
    if not visualization_data:
        raise HTTPException(status_code=503, detail="Visualization data not initialized")

    try:
        correlation = visualization_data.generate_correlation_matrix(
            data=data,
            fields=fields
        )

        return correlation

    except Exception as e:
        logger.error(f"Error generating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize/comparison")
async def generate_comparison(
    data: List[Dict[str, Any]],
    group_by: str = Query(..., description="Field to group by"),
    value_field: str = Query(..., description="Field to aggregate"),
    aggregation: str = Query("mean", description="Aggregation method")
):
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
    if not visualization_data:
        raise HTTPException(status_code=503, detail="Visualization data not initialized")

    try:
        comparison = visualization_data.generate_comparison_chart(
            data=data,
            group_by=group_by,
            value_field=value_field,
            aggregation=aggregation
        )

        return comparison

    except Exception as e:
        logger.error(f"Error generating comparison chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualize/gauge")
async def generate_gauge(
    current_value: float = Query(..., description="Current value"),
    min_value: float = Query(0, description="Minimum value"),
    max_value: float = Query(100, description="Maximum value")
):
    """
    Generate gauge chart data

    Args:
        current_value: Current value
        min_value: Minimum value
        max_value: Maximum value

    Returns:
        Gauge chart data
    """
    if not visualization_data:
        raise HTTPException(status_code=503, detail="Visualization data not initialized")

    try:
        gauge = visualization_data.generate_gauge_chart(
            current_value=current_value,
            min_value=min_value,
            max_value=max_value
        )

        return gauge

    except Exception as e:
        logger.error(f"Error generating gauge chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Benchmarking Endpoints
# ============================================================================

@router.post("/benchmark/compare")
async def compare_to_benchmark(
    current_value: float = Query(..., description="Current value"),
    metric_name: str = Query(..., description="Metric name"),
    benchmark_value: Optional[float] = Query(None, description="Benchmark value")
):
    """Compare current value to benchmark"""
    if not benchmarking:
        raise HTTPException(status_code=503, detail="Benchmarking not initialized")

    try:
        result = benchmarking.compare_to_benchmark(current_value, metric_name, benchmark_value)
        return {
            "current_value": result.current_value,
            "benchmark_value": result.benchmark_value,
            "difference": result.difference,
            "difference_percent": result.difference_percent,
            "performance_level": result.performance_level
        }
    except Exception as e:
        logger.error(f"Error comparing to benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark/historical")
async def compare_to_historical(
    current_value: float,
    historical_values: List[float],
    comparison_period: str = Query("all", description="Comparison period")
):
    """Compare to historical performance"""
    if not benchmarking:
        raise HTTPException(status_code=503, detail="Benchmarking not initialized")

    try:
        return benchmarking.compare_to_historical(current_value, historical_values, comparison_period)
    except Exception as e:
        logger.error(f"Error comparing to historical: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post("/export/json")
async def export_json(data: Dict[str, Any], pretty: bool = Query(True)):
    """Export data to JSON format"""
    if not export_manager:
        raise HTTPException(status_code=503, detail="Export manager not initialized")

    try:
        json_content = export_manager.export_to_json(data, pretty)
        return export_manager.create_download_response(
            content=json_content,
            filename=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            content_type="application/json"
        )
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/csv")
async def export_csv(data: List[Dict[str, Any]], columns: Optional[List[str]] = None):
    """Export data to CSV format"""
    if not export_manager:
        raise HTTPException(status_code=503, detail="Export manager not initialized")

    try:
        csv_content = export_manager.export_to_csv(data, columns)
        return export_manager.create_download_response(
            content=csv_content,
            filename=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            content_type="text/csv"
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
