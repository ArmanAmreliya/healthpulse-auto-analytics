import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

from src.engine import AutoAnalyticsEngine
from src.exporter import export_insights_to_csv, export_correlation_matrix_to_csv

# Streamlit Page Config
st.set_page_config(
    page_title="Auto-Analytics Healthcare Engine",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit Design System Custom CSS Injection (Light Mode with Coral #ff4b4b Accent & Black Table Borders)
STREAMLIT_DESIGN_SYSTEM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
  
  html, body, [class*="css"] {
    font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;
  }
  
  /* Main Container Background */
  .stApp {
    background-color: #f8fafc;
  }
  
  /* Sidebar Clean Design */
  section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
  }
  
  /* Coral Primary Buttons & Accents */
  .stButton > button {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s ease;
  }
  
  .stButton > button:hover {
    border-color: #ff4b4b;
    color: #ff4b4b;
    background-color: #fff5f5;
  }
  
  .stButton > button[kind="primary"] {
    background-color: #ff4b4b;
    color: #ffffff;
    border: none;
  }
  
  .stButton > button[kind="primary"]:hover {
    background-color: #e63939;
    color: #ffffff;
  }
  
  /* Metric Card Clean Border */
  div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  }
  
  /* Custom High-Contrast Table Styling with Black Borders */
  .custom-insights-table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 2px solid #0f172a;
    border-radius: 6px;
    overflow: hidden;
  }
  
  .custom-insights-table th {
    background-color: #0f172a;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: 12px 14px;
    border: 1px solid #0f172a;
    font-size: 15px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  
  .custom-insights-table td {
    padding: 12px 14px;
    border: 1px solid #64748b;
    color: #0f172a;
    line-height: 1.5;
    vertical-align: top;
    font-size: 15px;
  }
  
  .custom-insights-table tr:nth-child(even) {
    background-color: #f8fafc;
  }
  
  .custom-insights-table tr:hover {
    background-color: #f1f5f9;
  }
  
  .badge-pill-high {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1px solid #dc2626;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 13px;
    display: inline-block;
  }
  
  .badge-pill-med {
    background-color: #fffbeb;
    color: #d97706;
    border: 1px solid #d97706;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 13px;
    display: inline-block;
  }
  
  .badge-pill-low {
    background-color: #eff6ff;
    color: #2563eb;
    border: 1px solid #2563eb;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 13px;
    display: inline-block;
  }
  
  .badge-pill-type {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #475569;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 12px;
  }
</style>
"""
st.markdown(STREAMLIT_DESIGN_SYSTEM_CSS, unsafe_allow_html=True)

def render_insights_html_table(insights_data):
    """Generates a high-contrast HTML table without leading spaces to prevent Markdown code-block interpretation."""
    if not insights_data:
        return "<div style='padding:15px; text-align:center; color:#64748b;'>No insights match current filters.</div>"
    
    rows_html = []
    for item in insights_data:
        sev = item["severity"]
        if sev == "High":
            badge = '<span class="badge-pill-high">HIGH</span>'
        elif sev == "Medium":
            badge = '<span class="badge-pill-med">MEDIUM</span>'
        else:
            badge = '<span class="badge-pill-low">LOW</span>'
            
        ind_title = item["indicator"].replace('_', ' ').title()
        
        row = (
            f"<tr>"
            f"<td style=\"font-family: monospace; font-weight: 700; color: #1e293b;\">{item['insight_id']}</td>"
            f"<td><span class=\"badge-pill-type\">{item['type'].upper()}</span></td>"
            f"<td>{badge}</td>"
            f"<td style=\"font-weight: 700;\">{item['entity']}</td>"
            f"<td style=\"font-weight: 600;\">{ind_title}</td>"
            f"<td>{item['period']}</td>"
            f"<td style=\"font-weight: 700;\">{item['value']:.1f}</td>"
            f"<td style=\"color: #0f172a; line-height: 1.5;\">{item['explanation']}</td>"
            f"</tr>"
        )
        rows_html.append(row)
        
    table_body = "".join(rows_html)
    
    full_html = (
        f'<table class="custom-insights-table">'
        f'<thead><tr>'
        f'<th style="width: 9%;">ID</th>'
        f'<th style="width: 10%;">Type</th>'
        f'<th style="width: 10%;">Severity</th>'
        f'<th style="width: 13%;">District / Entity</th>'
        f'<th style="width: 14%;">Indicator</th>'
        f'<th style="width: 8%;">Period</th>'
        f'<th style="width: 7%;">Value</th>'
        f'<th style="width: 29%;">Narrative Explanation</th>'
        f'</tr></thead>'
        f'<tbody>{table_body}</tbody>'
        f'</table>'
    )
    return full_html

# ---------------------------------------------------------
# MAIN TITLE & SUBTITLE
# ---------------------------------------------------------
st.title("🏥 Auto-Analytics Healthcare Engine")
st.caption("District Healthcare Performance Analytics & Insight Generation System")

st.divider()

# Dataset File Loading
CSV_PATH = os.path.join("data", "district_healthcare_data.csv")
EXTENDED_CSV_PATH = os.path.join("data", "district_healthcare_extended.csv")

# ---------------------------------------------------------
# SIDEBAR — STREAMLIT LOGO AT TOP & CONTROLS
# ---------------------------------------------------------
if os.path.exists("images.png"):
    st.sidebar.image("images.png", width=180)

st.sidebar.markdown("### Dataset Selection")
dataset_choice = st.sidebar.radio(
    "Choose Dataset Source",
    options=["Benchmark Dataset (12 rows)", "Extended Multi-Month Dataset (30 rows)", "Upload Custom CSV"],
    index=0
)

df = None
if dataset_choice == "Upload Custom CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success(f"Loaded custom file ({len(df)} rows)")
    elif os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        st.sidebar.info("Awaiting file upload. Showing benchmark dataset.")
elif dataset_choice == "Extended Multi-Month Dataset (30 rows)" and os.path.exists(EXTENDED_CSV_PATH):
    df = pd.read_csv(EXTENDED_CSV_PATH)
    st.sidebar.success("Loaded extended multi-month dataset.")
else:
    df = pd.read_csv(CSV_PATH)
    st.sidebar.success("Loaded benchmark 12-row dataset.")

if df is None or df.empty:
    st.error("No valid dataset available.")
    st.stop()

# Initialize Engine
engine = AutoAnalyticsEngine(df)
val_summary = engine.get_validation_summary()

st.sidebar.divider()

st.sidebar.markdown("### Algorithm UI Sliders")

trend_threshold = st.sidebar.slider(
    "Trend Threshold (|Δ%|)",
    min_value=1.0,
    max_value=50.0,
    value=10.0,
    step=1.0,
    help="Flags Month-over-Month percentage changes exceeding this percentage."
)

outlier_method = st.sidebar.selectbox(
    "Outlier Detection Method",
    options=["iqr", "zscore"],
    format_func=lambda x: "IQR Rule (1.5x IQR)" if x == "iqr" else "Z-Score Method (|z| >= threshold)"
)

outlier_threshold = st.sidebar.slider(
    "Outlier Threshold Multiplier / Z-Score",
    min_value=0.5,
    max_value=4.0,
    value=1.5 if outlier_method == "iqr" else 3.0,
    step=0.1
)

corr_threshold = st.sidebar.slider(
    "Correlation Threshold (|r|)",
    min_value=0.50,
    max_value=0.95,
    value=0.70,
    step=0.05
)

st.sidebar.divider()

st.sidebar.markdown("### Dynamic Filters")
selected_districts = st.sidebar.multiselect("Filter Districts", options=val_summary["unique_districts"])
selected_months = st.sidebar.multiselect("Filter Months", options=val_summary["unique_months"])
selected_indicators = st.sidebar.multiselect("Filter Indicators", options=val_summary["numerical_indicators"])

st.sidebar.divider()

st.sidebar.markdown("### Insight Search & Filtering")
severity_filter = st.sidebar.selectbox("Severity Filter", options=["All Severities", "High", "Medium", "Low"])
search_query = st.sidebar.text_input("Search Insights Narrative", value="", placeholder="Search narrative or district...")

# ---------------------------------------------------------
# RUN ANALYTICS ENGINE
# ---------------------------------------------------------
results = engine.generate_all_insights(
    districts=selected_districts if selected_districts else None,
    months=selected_months if selected_months else None,
    indicators=selected_indicators if selected_indicators else None,
    trend_threshold_pct=trend_threshold,
    outlier_method=outlier_method,
    outlier_threshold=outlier_threshold,
    correlation_threshold=corr_threshold
)

# Apply Severity & Text Filtering
insights_list = results["insights"]

if severity_filter != "All Severities":
    insights_list = [ins for ins in insights_list if ins["severity"] == severity_filter]

if search_query:
    q = search_query.lower()
    insights_list = [
        ins for ins in insights_list if (
            q in ins["explanation"].lower() or
            q in ins["indicator"].lower() or
            q in ins["entity"].lower() or
            q in ins["insight_id"].lower()
        )
    ]

# ---------------------------------------------------------
# MAIN DASHBOARD METRICS
# ---------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(label="Total Insights", value=results["total_insights"])
with k2:
    st.metric(label="High Severity Alerts", value=results["severity_counts"].get("High", 0))
with k3:
    st.metric(label="Flagged Trends", value=results["insight_type_counts"].get("trend", 0))
with k4:
    st.metric(label="Key Correlations (|r| ≥ thresh)", value=len(results["flagged_correlations"]))

st.divider()

# ---------------------------------------------------------
# CHARTS SECTION
# ---------------------------------------------------------
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### Severity Distribution")
    sev_counts = results["severity_counts"]
    sev_df = pd.DataFrame({
        "Severity": list(sev_counts.keys()),
        "Count": list(sev_counts.values())
    })
    
    fig_donut = px.pie(
        sev_df,
        names="Severity",
        values="Count",
        hole=0.5,
        color="Severity",
        color_discrete_map={"High": "#ff4b4b", "Medium": "#f59e0b", "Low": "#38bdf8"}
    )
    fig_donut.update_traces(textinfo="percent+value")
    fig_donut.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_chart2:
    st.markdown("#### District Performance Trajectory")
    filtered_df = engine.filter_data(selected_districts, selected_months, selected_indicators)
    
    if not filtered_df.empty and 'anc_coverage' in filtered_df.columns:
        fig_line = px.area(
            filtered_df,
            x="month",
            y="anc_coverage",
            color="district",
            markers=True,
            color_discrete_sequence=["#ff4b4b", "#38bdf8", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"],
            labels={"anc_coverage": "ANC Coverage (%)", "month": "Month", "district": "District"}
        )
        fig_line.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No numerical data available for trajectory chart.")

st.divider()

# ---------------------------------------------------------
# PEARSON CORRELATION MATRIX
# ---------------------------------------------------------
st.markdown("#### Pearson Correlation Matrix Across Indicators")
corr_dict = results["correlation_matrix"]

if corr_dict:
    corr_df = pd.DataFrame(corr_dict)
    fig_heatmap = px.imshow(
        corr_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale=["#38bdf8", "#ffffff", "#ff4b4b"],
        zmin=-1,
        zmax=1
    )
    fig_heatmap.update_layout(
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.caption(f"Evaluated across {len(filtered_df)} data rows. Flagged pairs satisfy |r| >= {corr_threshold:.2f}.")

st.divider()

# ---------------------------------------------------------
# DYNAMIC GENERATED INSIGHTS TABLE (FIXED UNINDENTED HTML)
# ---------------------------------------------------------
st.markdown(f"#### Dynamic Generated Insights ({len(insights_list)} Displayed)")

if insights_list:
    tab_all, tab_trends, tab_outliers, tab_correlations = st.tabs(
        ["All Insights", "Trends", "Outliers", "Correlations"]
    )
    
    with tab_all:
        html_table = render_insights_html_table(insights_list)
        st.markdown(html_table, unsafe_allow_html=True)
        
    with tab_trends:
        trends_list = [ins for ins in insights_list if ins['type'] == 'trend']
        st.markdown(render_insights_html_table(trends_list), unsafe_allow_html=True)
        
    with tab_outliers:
        outliers_list = [ins for ins in insights_list if ins['type'] == 'outlier']
        st.markdown(render_insights_html_table(outliers_list), unsafe_allow_html=True)
        
    with tab_correlations:
        corr_list = [ins for ins in insights_list if ins['type'] == 'correlation']
        st.markdown(render_insights_html_table(corr_list), unsafe_allow_html=True)

    st.write("")
    
    # Download CSV Button
    raw_insights_df = pd.DataFrame(insights_list)
    cols = ['insight_id', 'type', 'indicator', 'entity', 'period', 'value', 'prev_value', 'change_pct', 'severity', 'explanation']
    existing_cols = [c for c in cols if c in raw_insights_df.columns]
    csv_bytes = raw_insights_df[existing_cols].to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Download Insights CSV",
        data=csv_bytes,
        file_name="insights.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.warning("No insights match current search query or severity filter.")

st.divider()

# ---------------------------------------------------------
# PART A DATA AUDIT EXPANDER
# ---------------------------------------------------------
with st.expander("Part A Data Quality Audit & Schema Inspection"):
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.write("**Dataset Summary:**")
        st.json({
            "total_rows": val_summary["total_rows"],
            "columns": val_summary["columns"],
            "districts": val_summary["unique_districts"],
            "months": val_summary["unique_months"]
        })
    with col_a2:
        st.write("**Missing Value Audit:**")
        st.json(val_summary["missing_values"])
    
    st.write("**DataFrame Preview (`head()`):**")
    st.dataframe(df.head(10), use_container_width=True)
