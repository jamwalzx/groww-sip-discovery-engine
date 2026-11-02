"""
View 1: Overview & Data Health Funnel.
Displays executive KPI metrics, the multi-stage cleaning/filtering funnel,
and the cross-platform source bias audit.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.db.database import get_db
from src.db.models import RawFeedback, CleanedFeedback, ExtractedInsight, Theme, OpportunityScoreRecord
from src.evals.bias_panel import SourceBiasAuditor


def render():
    st.title("📊 Overview & Data Health Funnel")
    st.markdown(
        "Welcome to the **Groww AI Discovery Engine** for first-time mutual fund SIP continuation. "
        "This platform monitors multi-channel Indian investor conversations at scale to diagnose why first-time "
        "investors drop off within Months 1–12."
    )

    # 1. Fetch DB metrics
    with get_db() as db:
        raw_count = db.query(RawFeedback).count()
        clean_count = db.query(CleanedFeedback).filter(
            CleanedFeedback.is_duplicate == False,
            CleanedFeedback.is_spam == False
        ).count()
        insights_count = db.query(ExtractedInsight).count()
        themes_count = db.query(Theme).count()
        opp_count = db.query(OpportunityScoreRecord).count()

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Raw Feedback", f"{raw_count:,}", help="Total raw public records ingested across all channels")
    col2.metric("Clean Records", f"{clean_count:,}", delta=f"{clean_count - raw_count} noise/dup", help="Cleaned & deduplicated items")
    col3.metric("Relevant Insights", f"{insights_count:,}", help="Pydantic schema-validated behavioral insights")
    col4.metric("Discovered Themes", f"{themes_count}", help="Semantic clusters uncovered via embeddings")
    col5.metric("Prioritized Opps", f"{opp_count}", help="Quantified product opportunity matrix items")

    st.markdown("---")

    # 2. Data Health Conversion Funnel
    st.subheader("🔻 Data Health Conversion Funnel")
    col_funnel, col_stats = st.columns([3, 2])

    with col_funnel:
        funnel_stages = [
            "Raw Scraped Records",
            "Cleaned & Deduplicated",
            "Behaviorally Relevant SIP Items",
            "Clustered Thematic Groups"
        ]
        funnel_values = [raw_count, clean_count, insights_count, themes_count]

        fig = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textinfo="value+percent previous",
            marker={
                "color": ["#1E222B", "#00D09C", "#3B82F6", "#F59E0B"],
            }
        ))
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        st.markdown("### Funnel Health Diagnostic")
        st.write(
            f"- **Spam & Deduplication Filter:** Dropped **{raw_count - clean_count} items** "
            f"({((raw_count - clean_count) / raw_count * 100.0) if raw_count else 0:.1f}%) of referral/duplicate noise."
        )
        st.write(
            f"- **SIP Relevance Filter:** Screened out **{clean_count - insights_count} general support items** "
            f"(KYC timeouts, bank OTP lags) to isolate true SIP continuation signals."
        )
        st.write(
            f"- **Thematic Synthesis:** Condensed **{insights_count} verified quotes** into **{themes_count} distinct problem themes** "
            "ranked by quantified business opportunity."
        )

    st.markdown("---")

    # 3. Source Bias & Channel Representation
    st.subheader("⚖️ Source Distribution & Structural Channel Bias")
    st.markdown(
        "Different digital channels attract different user personas. "
        "The engine explicitly audits source distribution to protect Growth PMs from over-indexing on platform-specific vocal biases."
    )

    bias_auditor = SourceBiasAuditor()
    bias_data = bias_auditor.audit()

    platforms = bias_data.get("platforms", {})
    if platforms:
        table_rows = []
        for pkey, pinfo in platforms.items():
            table_rows.append({
                "Channel": pinfo["channel_name"],
                "Raw Volume": f"{pinfo['raw_count']} ({pinfo['raw_share_pct']}%)",
                "Insight Volume": f"{pinfo['extracted_count']} ({pinfo['extracted_share_pct']}%)",
                "Avg Severity": f"{pinfo['avg_severity']:.2f} / 5.0",
                "Primary User Cohort": pinfo["primary_cohort"],
                "Structural Bias": pinfo["inherent_bias"],
                "PM Interpretation Guide": pinfo["pm_interpretation_guide"]
            })

        df_bias = pd.DataFrame(table_rows)
        st.dataframe(df_bias, use_container_width=True, hide_index=True)

        # Bar chart comparison
        df_chart = pd.DataFrame([
            {"Channel": pinfo["channel_name"], "Raw Volume": pinfo["raw_count"], "Insights": pinfo["extracted_count"]}
            for pinfo in platforms.values()
        ])
        fig_bar = px.bar(
            df_chart,
            x="Channel",
            y=["Raw Volume", "Insights"],
            barmode="group",
            title="Channel Representation (Raw Ingestion vs. Qualified Behavioral Insights)",
            color_discrete_sequence=["#1E222B", "#00D09C"]
        )
        fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

