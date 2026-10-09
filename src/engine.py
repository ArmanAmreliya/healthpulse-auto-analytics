import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import io

class AutoAnalyticsEngine:
    """
    Auto-Analytics Engine for District Healthcare Performance Data.
    Ingests healthcare CSV and dynamically detects:
      - Trends (Month-over-Month percentage change)
      - Outliers (IQR or Z-Score method)
      - Pearson Correlations across indicators
      - Structured human-readable Insights with dynamic severity rating
    """
    
    DEFAULT_INDICATORS = ['anc_coverage', 'institutional_delivery', 'immunization', 'high_risk_cases']

    def __init__(self, df: pd.DataFrame):
        self.raw_df = df.copy()
        self.df = df.copy()
        self._prepare_data()
        
    def _prepare_data(self):
        """Standardize column names, data types, and sorting."""
        # Clean column names
        self.df.columns = [str(c).strip().lower() for c in self.df.columns]
        
        # Ensure required columns exist
        if 'month' in self.df.columns:
            self.df['month'] = self.df['month'].astype(str)
        if 'district' in self.df.columns:
            self.df['district'] = self.df['district'].astype(str)
            
        # Ensure numerical indicators are numeric
        self.numerical_cols = [c for c in self.df.columns if c not in ['month', 'district']]
        for col in self.numerical_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
        # Sort chronologically by month and district
        if 'month' in self.df.columns and 'district' in self.df.columns:
            self.df = self.df.sort_values(by=['district', 'month']).reset_index(drop=True)

    def get_validation_summary(self) -> Dict[str, Any]:
        """Part A: Data Validation Summary (missing values, head, info)."""
        missing_counts = self.df.isnull().sum().to_dict()
        unique_districts = sorted(self.df['district'].unique().tolist()) if 'district' in self.df.columns else []
        unique_months = sorted(self.df['month'].unique().tolist()) if 'month' in self.df.columns else []
        
        return {
            "total_rows": int(len(self.df)),
            "columns": list(self.df.columns),
            "missing_values": {str(k): int(v) for k, v in missing_counts.items()},
            "unique_districts": unique_districts,
            "unique_months": unique_months,
            "numerical_indicators": self.numerical_cols
        }

    def filter_data(self, 
                    districts: Optional[List[str]] = None, 
                    months: Optional[List[str]] = None, 
                    indicators: Optional[List[str]] = None) -> pd.DataFrame:
        """Filter dataset dynamically based on UI selections."""
        filtered = self.df.copy()
        if districts:
            filtered = filtered[filtered['district'].isin(districts)]
        if months:
            filtered = filtered[filtered['month'].isin(months)]
        
        active_indicators = indicators if indicators else self.numerical_cols
        keep_cols = ['month', 'district'] + [col for col in active_indicators if col in filtered.columns]
        return filtered[keep_cols]

    def detect_trends(self, df_subset: pd.DataFrame, threshold_pct: float = 10.0) -> List[Dict[str, Any]]:
        """
        Part B: Trend Detection.
        Computes pct_change = ((current - prev) / prev) * 100 for each (district, indicator) pair.
        Flags pairs where |pct_change| >= threshold_pct.
        """
        trends = []
        indicators = [c for c in df_subset.columns if c not in ['month', 'district']]
        
        # Sort by district and month
        df_sorted = df_subset.sort_values(by=['district', 'month'])
        
        for district, group in df_sorted.groupby('district'):
            group = group.sort_values('month')
            months = group['month'].tolist()
            
            for col in indicators:
                values = group[col].tolist()
                for i in range(1, len(values)):
                    prev_val = values[i-1]
                    curr_val = values[i]
                    prev_month = months[i-1]
                    curr_month = months[i]
                    
                    if pd.isna(prev_val) or pd.isna(curr_val) or prev_val == 0:
                        continue
                        
                    pct_change = ((curr_val - prev_val) / prev_val) * 100.0
                    abs_change = abs(pct_change)
                    
                    if abs_change >= threshold_pct:
                        # Determine severity dynamically
                        if abs_change >= 25.0:
                            severity = "High"
                        elif abs_change >= 15.0:
                            severity = "Medium"
                        else:
                            severity = "Low"
                            
                        direction = "dropped" if pct_change < 0 else "increased"
                        indicator_title = col.replace('_', ' ').title()
                        
                        explanation = (
                            f"{indicator_title} in {district} {direction} by {abs(pct_change):.1f}% "
                            f"in {curr_month} compared to previous month {prev_month} ({prev_val:.0f} -> {curr_val:.0f})."
                        )
                        
                        trends.append({
                            "type": "trend",
                            "indicator": col,
                            "entity": district,
                            "period": curr_month,
                            "value": float(curr_val),
                            "prev_value": float(prev_val),
                            "change_pct": round(float(pct_change), 2),
                            "severity": severity,
                            "explanation": explanation
                        })
        return trends

    def detect_outliers(self, df_subset: pd.DataFrame, method: str = "iqr", threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Part C: Outlier Detection.
        Supports IQR rule (Q3 + threshold*IQR / Q1 - threshold*IQR) or Z-Score (|z| >= threshold).
        """
        outliers = []
        indicators = [c for c in df_subset.columns if c not in ['month', 'district']]
        
        for col in indicators:
            series = df_subset[col].dropna()
            if len(series) < 3:
                continue
                
            mean_val = series.mean()
            std_val = series.std(ddof=1)
            
            if method == "zscore":
                if std_val == 0:
                    continue
                z_scores = (df_subset[col] - mean_val) / std_val
                
                for idx, z in z_scores.items():
                    if abs(z) >= threshold:
                        row = df_subset.loc[idx]
                        val = row[col]
                        district = row['district']
                        month = row['month']
                        
                        # Dynamic severity
                        if abs(z) >= 3.0:
                            severity = "High"
                        elif abs(z) >= 2.0:
                            severity = "Medium"
                        else:
                            severity = "Low"
                            
                        indicator_title = col.replace('_', ' ').title()
                        direction = "below" if z < 0 else "above"
                        
                        explanation = (
                            f"{district}'s {indicator_title} of {val:.0f} in {month} is {abs(z):.1f}σ "
                            f"{direction} the benchmark mean ({mean_val:.1f}), flagging for review."
                        )
                        
                        outliers.append({
                            "type": "outlier",
                            "indicator": col,
                            "entity": district,
                            "period": month,
                            "value": float(val),
                            "prev_value": None,
                            "change_pct": round(float(z), 2),  # store Z score in change_pct field for context
                            "severity": severity,
                            "explanation": explanation
                        })
                        
            else:  # IQR Method
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - (threshold * iqr)
                upper_bound = q3 + (threshold * iqr)
                
                for idx, row in df_subset.iterrows():
                    val = row[col]
                    if pd.isna(val):
                        continue
                    if val < lower_bound or val > upper_bound:
                        district = row['district']
                        month = row['month']
                        
                        dev_from_mean = abs(val - mean_val) / std_val if std_val > 0 else 1.0
                        if dev_from_mean >= 2.5:
                            severity = "High"
                        elif dev_from_mean >= 1.5:
                            severity = "Medium"
                        else:
                            severity = "Low"
                            
                        indicator_title = col.replace('_', ' ').title()
                        bound_type = "lower IQR threshold" if val < lower_bound else "upper IQR threshold"
                        
                        explanation = (
                            f"{district}'s {indicator_title} ({val:.0f}) breached the district {bound_type} "
                            f"(Q1={q1:.1f}, Q3={q3:.1f}, IQR={iqr:.1f}) in {month}."
                        )
                        
                        outliers.append({
                            "type": "outlier",
                            "indicator": col,
                            "entity": district,
                            "period": month,
                            "value": float(val),
                            "prev_value": None,
                            "change_pct": round(float((val - mean_val) / (std_val if std_val > 0 else 1.0)), 2),
                            "severity": severity,
                            "explanation": explanation
                        })
                        
        return outliers

    def detect_correlations(self, df_subset: pd.DataFrame, threshold: float = 0.70) -> Tuple[Dict[str, Dict[str, float]], List[Dict[str, Any]]]:
        """
        Part D: Correlation Detection.
        Computes Pearson correlation matrix across numerical indicators.
        Flags indicator pairs with |r| >= threshold.
        """
        indicators = [c for c in df_subset.columns if c not in ['month', 'district']]
        num_df = df_subset[indicators].dropna()
        
        if len(num_df) < 3:
            return {}, []
            
        corr_matrix_df = num_df.corr(method='pearson')
        corr_dict = corr_matrix_df.to_dict()
        
        flagged_correlations = []
        cols = list(corr_matrix_df.columns)
        
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col1, col2 = cols[i], cols[j]
                r_val = corr_matrix_df.loc[col1, col2]
                
                if not pd.isna(r_val) and abs(r_val) >= threshold:
                    abs_r = abs(r_val)
                    if abs_r >= 0.90:
                        severity = "High"
                    elif abs_r >= 0.80:
                        severity = "Medium"
                    else:
                        severity = "Low"
                        
                    rel_type = "Strong Positive" if r_val > 0 else "Strong Inverse"
                    title1 = col1.replace('_', ' ').title()
                    title2 = col2.replace('_', ' ').title()
                    
                    explanation = (
                        f"{rel_type} Correlation (r = {r_val:.2f}) observed between {title1} "
                        f"and {title2} across districts. (Note: Small sample size n={len(num_df)})."
                    )
                    
                    flagged_correlations.append({
                        "type": "correlation",
                        "indicator": f"{col1} : {col2}",
                        "entity": "Statewide",
                        "period": "Overall",
                        "value": round(float(r_val), 3),
                        "prev_value": None,
                        "change_pct": round(float(r_val * 100), 1),
                        "severity": severity,
                        "explanation": explanation,
                        "pair": [col1, col2],
                        "r": round(float(r_val), 3)
                    })
                    
        return corr_dict, flagged_correlations

    def generate_all_insights(self, 
                               districts: Optional[List[str]] = None,
                               months: Optional[List[str]] = None,
                               indicators: Optional[List[str]] = None,
                               trend_threshold_pct: float = 10.0,
                               outlier_method: str = "iqr",
                               outlier_threshold: float = 1.5,
                               correlation_threshold: float = 0.70) -> Dict[str, Any]:
        """
        Part E: Automated Insight Generation.
        Combines Trends, Outliers, and Correlations, auto-assigns insight_ids (INS-0001, INS-0002...),
        and builds a complete structured payload.
        """
        filtered_df = self.filter_data(districts, months, indicators)
        
        trends = self.detect_trends(filtered_df, threshold_pct=trend_threshold_pct)
        outliers = self.detect_outliers(filtered_df, method=outlier_method, threshold=outlier_threshold)
        corr_matrix, corr_insights = self.detect_correlations(filtered_df, threshold=correlation_threshold)
        
        all_raw_insights = trends + outliers + corr_insights
        
        # Format structured insight items with INS-xxxx IDs
        formatted_insights = []
        for i, item in enumerate(all_raw_insights, start=1):
            formatted_insights.append({
                "insight_id": f"INS-{i:04d}",
                "type": item["type"],
                "indicator": item["indicator"],
                "entity": item["entity"],
                "period": item["period"],
                "value": item["value"],
                "prev_value": item["prev_value"],
                "change_pct": item["change_pct"],
                "severity": item["severity"],
                "explanation": item["explanation"]
            })
            
        # Summary counts
        severity_counts = {"High": 0, "Medium": 0, "Low": 0}
        type_counts = {"trend": 0, "outlier": 0, "correlation": 0}
        
        for ins in formatted_insights:
            sev = ins["severity"]
            typ = ins["type"]
            if sev in severity_counts:
                severity_counts[sev] += 1
            if typ in type_counts:
                type_counts[typ] += 1
                
        return {
            "validation": self.get_validation_summary(),
            "insights": formatted_insights,
            "correlation_matrix": corr_matrix,
            "flagged_correlations": corr_insights,
            "severity_counts": severity_counts,
            "insight_type_counts": type_counts,
            "total_insights": len(formatted_insights)
        }
