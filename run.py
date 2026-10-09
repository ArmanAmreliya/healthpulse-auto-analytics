import os
import pandas as pd
import json
from src.engine import AutoAnalyticsEngine
from src.exporter import export_insights_to_csv, export_correlation_matrix_to_csv

def main():
    print("=" * 80)
    print("      AUTOMATED INSIGHT GENERATION ENGINE - HEALTHCARE PERFORMANCE ANALYTICS")
    print("=" * 80)
    
    # 1. Load Data
    csv_path = os.path.join("data", "district_healthcare_data.csv")
    print(f"\n[PART A] Loading CSV dataset from: {csv_path}")
    
    df = pd.read_csv(csv_path)
    engine = AutoAnalyticsEngine(df)
    
    val = engine.get_validation_summary()
    print("\n--- DATA VALIDATION SUMMARY ---")
    print(f"Total Rows: {val['total_rows']}")
    print(f"Columns: {val['columns']}")
    print(f"Missing Values per Column: {val['missing_values']}")
    print(f"Districts ({len(val['unique_districts'])}): {val['unique_districts']}")
    print(f"Months: {val['unique_months']}")
    print(f"Indicators: {val['numerical_indicators']}")
    
    print("\nDataFrame Head:")
    print(df.head())
    
    # 2. Run Engine (Parts B, C, D, E)
    print("\n[PARTS B-E] Running AutoAnalytics Engine...")
    results = engine.generate_all_insights(
        trend_threshold_pct=10.0,
        outlier_method="iqr",
        outlier_threshold=1.5,
        correlation_threshold=0.70
    )
    
    print(f"\nEngine processing complete! Total Insights Generated: {results['total_insights']}")
    print(f"Severity Breakdown: {results['severity_counts']}")
    print(f"Insight Types Breakdown: {results['insight_type_counts']}")
    
    print("\n" + "-" * 80)
    print("DYNAMIC HUMAN-READABLE INSIGHTS:")
    print("-" * 80)
    
    for ins in results['insights']:
        sev_badge = f"[{ins['severity'].upper()}]"
        print(f"{ins['insight_id']} | {ins['type'].upper():12s} | {sev_badge:8s} | {ins['explanation']}")
        
    # 3. Export Deliverables
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    insights_csv = os.path.join(output_dir, "insights.csv")
    corr_csv = os.path.join(output_dir, "correlation_matrix.csv")
    
    export_insights_to_csv(results['insights'], insights_csv)
    export_correlation_matrix_to_csv(results['correlation_matrix'], corr_csv)
    
    print("\n" + "=" * 80)
    print(f"[OK] Insights CSV exported to: {insights_csv}")
    print(f"[OK] Correlation Matrix CSV exported to: {corr_csv}")
    print("=" * 80)

if __name__ == "__main__":
    main()
