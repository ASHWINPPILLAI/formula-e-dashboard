"""Pydantic v2 models for Formula E Driver Performance Analyzer."""

from pydantic import BaseModel, Field


class TelemetryInput(BaseModel):
    """Incoming telemetry data for a single lap."""

    driver_id: str = Field(..., min_length=1, max_length=10)
    lap_number: int = Field(..., ge=1, le=1000)
    turn_3_regen_kw: float = Field(..., ge=0, le=1500)
    turn_13_regen_kw: float = Field(..., ge=0, le=1500)
    lift_coast_distance_meters: float = Field(..., ge=0, le=5000)


class EvaluationResponse(BaseModel):
    """Evaluation result returned to the caller."""

    driver_id: str
    lap_number: int
    efficiency_score: int
    rating: str
    sensor_fault_detected: bool
    feedback: list[str]
    chart_url: str
    # Historical data (optional if it's the first lap)
    historical_average_score: float | None = None
    score_delta: float | None = None
