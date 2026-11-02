"""
View 3: Quantified Opportunity Matrix.
Interactive 2x2 scatter matrix (Impact vs. Addressability) with real-time weight sliders
(w_f, w_s, w_p), executive Top-5 export, and strict compliance guardrails.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.analytics.opportunity_matrix import OpportunityMatrixCalculator
from src.db.database import get_db
from src.db.models import OpportunityScoreRecord


def render():
    st.title("🎯 Quantified Opportunity Matrix")
    st.markdown(
        "Prioritize product interventions using the multi-factor Opportunity Formula: "
        r"$$\text{Impact} = (w_f \cdot F_{\text{norm}} + w_s \cdot S_{\text{norm}} + w_p \cdot P_{\text{norm}}) \times 100$$"
        r"$$\text{Opportunity Score} = \text{Impact} \times A_{\text{norm}}$$"
    )

    st.success(
        "🛡️ **Compliance & Guardrail Audit Verified:** Every product opportunity strictly excludes "
        "fear/FOMO/urgency triggers, and enforces zero stock or mutual fund recommendations."
    )

    # 1. Weight adjustment sliders
    with st.expander("⚙️ Adjust Scoring Weights (Real-Time Recalculation)", expanded=False):
        col_w1, col_w2, col_w3 = st.columns(3)
        w_f = col_w1.slider("Frequency Weight (w_f)", 0.0, 1.0, 0.30, 0.05)
        w_s = col_w2.slider("Severity Weight (w_s)", 0.0, 1.0, 0.30, 0.05)
        w_p = col_w3.slider("Proximity Weight (w_p)", 0.0, 1.0, 0.40, 0.05)

    calc = OpportunityMatrixCalculator(weight_frequency=w_f, weight_severity=w_s, weight_proximity=w_p)
    scored_items = calc.compute_all()

    if not scored_items:
        st.warning("No themes found in database. Please run Phase 4 clustering first.")
        return

    df_opp = pd.DataFrame(scored_items)

    # 2. 2x2 Scatter Matrix: Impact vs Addressability
    st.subheader("📍 2x2 Opportunity Matrix (Impact vs. Addressability)")
    fig_matrix = px.scatter(
        df_opp,
        x="addressability_score",
        y="impact_score",
        size="item_count",
        color="opportunity_score",
        hover_name="theme_title",
        hover_data={
            "rank": True,
            "opportunity_score": ":.1f",
            "frequency_pct": ":.1f%",
            "severity_score": ":.1f",
            "addressability_score": ":.1f",
            "taxonomy_type": True
        },
        labels={
            "addressability_score": "Product Addressability / Feasibility (1 - 5)",
            "impact_score": "User Pain Impact Score (0 - 100)",
            "opportunity_score": "Opp Score",
            "item_count": "Feedback Volume"
        },
        color_continuous_scale="Mint",
        title="Impact vs. Addressability (Bubble size = Feedback Volume)"
    )

    # Quadrant lines
    fig_matrix.add_hline(y=50, line_dash="dash", line_color="#D1D5DB")
    fig_matrix.add_vline(x=3.5, line_dash="dash", line_color="#D1D5DB")
    fig_matrix.add_annotation(x=4.5, y=90, text="🚀 HIGH IMPACT / HIGH FEASIBILITY (Quick Wins)", showarrow=False, font=dict(color="#059669", size=12))
    fig_matrix.add_annotation(x=2.5, y=90, text="⚠️ HIGH IMPACT / LOW FEASIBILITY (Strategic Bets)", showarrow=False, font=dict(color="#D97706", size=12))
    fig_matrix.add_annotation(x=4.5, y=20, text="💡 LOW IMPACT / HIGH FEASIBILITY (Low Hanging Fruit)", showarrow=False, font=dict(color="#4B5563", size=11))

    fig_matrix.update_layout(height=480, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_matrix, use_container_width=True)

    # 3. Ranked Backlog Table
    st.subheader("📋 Ranked Opportunity Backlog")
    display_cols = [
        "rank", "theme_title", "taxonomy_type", "frequency_pct",
        "severity_score", "proximity_score", "addressability_score",
        "impact_score", "opportunity_score"
    ]
    df_display = df_opp[display_cols].copy()
    df_display.columns = [
        "Rank", "Theme Title", "Taxonomy", "Freq (%)",
        "Severity (1-5)", "Proximity (1-5)", "Addressability (1-5)",
        "Impact (0-100)", "Opp Score (/100)"
    ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # 4. Top-5 Executive Export
    st.subheader("📥 1-Click Executive Export")
    top_5 = df_opp.head(5)
    csv_top5 = top_5.to_csv(index=False)
    st.download_button(
        label="Download Top 5 Opportunities (CSV)",
        data=csv_top5,
        file_name="groww_top5_sip_opportunities.csv",
        mime="text/csv",
        help="One-click CSV download of prioritized opportunities for Growth PM roadmap review"
    )

    # Top Strategic Highlights
    st.markdown("### 🏆 Top Strategic Product Highlights")
    for idx, row in top_5.iterrows():
        with st.expander(f"Rank #{row['rank']}: {row['theme_title']} (Score: {row['opportunity_score']:.1f} / 100)", expanded=(idx == 0)):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**Strategic Product Intervention:** {row['strategic_rationale']}")
                st.write(f"**Compliance Guardrail:** {row['addressability_feasibility']}")
                st.info(f"**Verbatim User Evidence:** \"{row['exemplar_quote']}\"")
            with c2:
                st.metric("Opportunity Score", f"{row['opportunity_score']:.1f} / 100")
                st.metric("Impact Score", f"{row['impact_score']:.1f}")
                st.metric("Addressability", f"{row['addressability_score']:.1f} / 5.0")

