from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class InsightRecord(BaseModel):
    insight_id: str
    type: str  # 'trend', 'outlier', 'correlation', 'threshold_breach'
    indicator: str
    entity: str  # district or statewide
    period: str  # month
    value: float
    prev_value: Optional[float] = None
    change_pct: Optional[float] = None
    severity: str  # 'Low', 'Medium', 'High'
    explanation: str

class ValidationSummary(BaseModel):
    total_rows: int
    columns: List[str]
    missing_values: Dict[str, int]
    unique_districts: List[str]
    unique_months: List[str]
    numerical_indicators: List[str]

class AnalyticsResult(BaseModel):
    validation: ValidationSummary
    insights: List[InsightRecord]
    correlation_matrix: Dict[str, Dict[str, float]]
    flagged_correlations: List[Dict[str, Any]]
    severity_counts: Dict[str, int]
    insight_type_counts: Dict[str, int]

class FilterConfig(BaseModel):
    districts: Optional[List[str]] = None
    months: Optional[List[str]] = None
    indicators: Optional[List[str]] = None
    trend_threshold_pct: float = 10.0
    outlier_method: str = "iqr"  # "iqr" or "zscore"
    outlier_threshold: float = 1.5  # 1.5 for IQR, 3.0 for Z-Score
    correlation_threshold: float = 0.70
