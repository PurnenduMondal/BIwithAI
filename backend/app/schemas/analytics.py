from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID

class ForecastRequest(BaseModel):
    data_source_id: UUID
    time_column: str
    metric: str
    periods: int = Field(30, ge=1, le=365)
    method: str = Field("auto", pattern="^(auto|prophet|linear|moving_average|exponential)$")
    confidence_interval: float = Field(0.95, ge=0.8, le=0.99)

class ForecastDataPoint(BaseModel):
    date: str
    forecast: float
    lower_bound: float
    upper_bound: float

class HistoricalDataPoint(BaseModel):
    date: str
    actual: float

class AccuracyMetrics(BaseModel):
    mae: float
    rmse: float
    mape: float
    r_squared: float

class ForecastResponse(BaseModel):
    historical: List[HistoricalDataPoint]
    forecast: List[ForecastDataPoint]
    accuracy: AccuracyMetrics
    trend: str
    metadata: Dict[str, Any]
    model_params: Optional[Dict[str, Any]] = None

class AnomalyDetectionRequest(BaseModel):
    data_source_id: UUID
    time_column: str
    metric: str
    sensitivity: float = Field(2.0, ge=1.0, le=5.0)

class Anomaly(BaseModel):
    date: str
    value: float
    expected_value: float
    type: str  # high or low
    deviation_score: float
    lower_bound: float
    upper_bound: float

class AnomalyDetectionResponse(BaseModel):
    anomalies: List[Anomaly]
    total_anomalies: int
    data_source_id: str
    metric: str

class TrendAnalysisResponse(BaseModel):
    direction: str  # increasing, decreasing, stable
    strength: str  # strong, moderate, weak
    slope: float
    r_squared: float
    percentage_change: float
    start_value: float
    end_value: float
    time_period_days: float