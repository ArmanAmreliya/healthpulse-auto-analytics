import pandas as pd
import json
from typing import List, Dict, Any

def export_insights_to_csv(insights: List[Dict[str, Any]], filepath: str) -> str:
    """Export list of insights to CSV formatted per assignment specification."""
    df = pd.DataFrame(insights)
    if not df.empty:
        # Standardize column headers matching Section 4.1 Output Specification
        cols_order = ['insight_id', 'type', 'indicator', 'entity', 'period', 'value', 'prev_value', 'change_pct', 'severity', 'explanation']
        existing_cols = [c for c in cols_order if c in df.columns]
        df = df[existing_cols]
    df.to_csv(filepath, index=False)
    return filepath

def export_correlation_matrix_to_csv(corr_matrix: Dict[str, Dict[str, float]], filepath: str) -> str:
    """Export correlation matrix dictionary to CSV matching Section 4.2 Output Specification."""
    df = pd.DataFrame(corr_matrix)
    df.to_csv(filepath, index=True)
    return filepath
