"""
View 4: Segment Explorer & Cross-Tabulations.
Multi-dimensional segmentation (Income, Age, Influencer, Source of Funds)
with dynamic n < 30 statistical sample size safeguards.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.analytics.segmentation import SegmentAnalyzer


def render():
    st.title("👥 Segment Explorer & Cross-Tabulations")
    st.markdown(
        "Analyze how friction, churn triggers, and continuation behaviors differ across demographic "
        "and behavioral segments."
    )

    analyzer = SegmentAnalyzer()
    seg_data = analyzer.compute_all_segments()

    if not seg_data or "dimensions" not in seg_data:
        st.warning("No extracted insight data available to segment.")
        return

    dimensions = seg_data["dimensions"]

    # Dimension selector
    dim_options = {
        "income_stability": "Income Stability (Salaried vs. Gig vs. Student)",
        "age_band": "Age Band (<22, 22-28, 29-35, 36+)",
        "influencer": "Primary Influencer (Self, Peer, Finfluencer, Family)",
        "source_of_money": "Source of Funds (Salary, Savings, Pocket Money)",
        "investor_experience": "Investor Experience Level (First-time vs. Experienced)"
    }

    selected_dim_key = st.selectbox(
        "Select Demographic / Behavioral Dimension to Slice:",
        options=list(dim_options.keys()),
        format_func=lambda x: dim_options[x]
    )

    dim_info = dimensions.get(selected_dim_key, {})
    st.subheader(f"📊 Breakdown by {dim_info.get('label')}")

    cohorts = dim_info.get("cohorts", {})

    # Overview table
    summary_rows = []
    for cval, cinfo in cohorts.items():
        conf = cinfo["confidence"]
        badge_text = "⚠️ Low (n<30)" if conf["low_confidence"] else "✅ High (n>=30)"
        summary_rows.append({
            "Cohort": cval.replace('_', ' ').title(),
            "Sample Size (n)": cinfo["sample_size"],
            "Confidence": badge_text,
            "Avg Severity (1-5)": cinfo["avg_severity"],
            "Top Churn Trigger": cinfo["top_drop_trigger"].replace('_', ' ').title(),
            "Drop-off Rate": f"{cinfo['drop_off_rate_pct']:.1f}%",
            "Continuer Rate": f"{cinfo['continuer_rate_pct']:.1f}%"
        })

    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # Detailed cohort drilldown
    st.markdown("### 🔍 Cohort Detail Cards & Statistical Guardrails")

    for cval, cinfo in cohorts.items():
        conf = cinfo["confidence"]
        with st.expander(f"Cohort: {cval.replace('_', ' ').title()} (n={cinfo['sample_size']})", expanded=True):
            if conf["low_confidence"]:
                st.warning(conf["confidence_status"])
            else:
                st.success(conf["confidence_status"])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Sample Size", f"n = {cinfo['sample_size']}")
            c2.metric("Mean Severity", f"{cinfo['avg_severity']:.2f} / 5.0")
            c3.metric("Drop-off Rate", f"{cinfo['drop_off_rate_pct']:.1f}%")
            c4.metric("Continuer Rate", f"{cinfo['continuer_rate_pct']:.1f}%")

            # Trigger distribution chart
            trig_data = [
                {"Trigger": k.replace('_', ' ').title(), "Share (%)": v["pct"]}
                for k, v in cinfo.get("drop_triggers", {}).items()
            ]
            if trig_data:
                df_trig = pd.DataFrame(trig_data)
                fig_trig = px.bar(df_trig, x="Trigger", y="Share (%)", color_discrete_sequence=["#00D09C"], title=f"Drop Triggers for {cval.title()}")
                fig_trig.update_layout(height=240, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_trig, use_container_width=True)

            # Sample quotes
            quotes = cinfo.get("sample_verbatim_quotes", [])
            if quotes:
                st.markdown("**Sample Verbatim User Voices:**")
                for q in quotes:
                    st.markdown(f"> *\"{q}\"*")

