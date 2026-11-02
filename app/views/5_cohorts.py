"""
View 5: Continuers vs. Drop-offs Comparative Analytics.
Side-by-side behavioral, emotional, and habit comparison between investors who persist
versus those who pause or drop off.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.analytics.cohort_comparison import CohortComparator


def render():
    st.title("⚖️ Continuers vs. Drop-offs Behavioral Breakdown")
    st.markdown(
        "Direct side-by-side contrast between first-time investors who maintained their SIP "
        "versus those who paused, reduced, or cancelled within the first 12 months."
    )

    comparator = CohortComparator()
    cohort_data = comparator.compute_all()

    if not cohort_data:
        st.warning("No feedback data available for cohort comparison.")
        return

    c_summary = cohort_data.get("continuers", {})
    d_summary = cohort_data.get("drop_offs", {})

    # Top KPI comparison
    col_c, col_d = st.columns(2)
    with col_c:
        st.success(f"### 🟢 Disciplined Continuers ({cohort_data['continuers_count']} items, {cohort_data['continuers_pct']}%)")
        st.metric("Mean Distress Severity", f"{c_summary.get('avg_severity', 1.0):.2f} / 5.0", delta="- Low Friction", delta_color="normal")
        st.write("**Key Habit:** Monthly statement review ('set-and-forget'), automated debits 2–3 days post-salary.")

    with col_d:
        st.error(f"### 🔴 Churned / Paused Drop-offs ({cohort_data['drop_offs_count']} items, {cohort_data['drop_offs_pct']}%)")
        st.metric("Mean Distress Severity", f"{d_summary.get('avg_severity', 1.0):.2f} / 5.0", delta="+ High Friction", delta_color="inverse")
        st.write("**Key Habit:** Daily NAV obsession, speculative YouTube consumption during market corrections.")

    st.markdown("---")

    # 1. Contrast Findings Table
    st.subheader("🔍 Core Behavioral Differences")
    findings = cohort_data.get("contrast_findings", [])
    for f in findings:
        with st.container():
            st.markdown(f"#### 📌 {f['dimension']}")
            st.write(f"**Diagnostic Takeaway:** {f['finding']}")
            fc1, fc2 = st.columns(2)
            fc1.info(f"**Continuers:** {f.get('continuers_stat') or f.get('continuers_severity') or f.get('continuers_top_source')}")
            fc2.warning(f"**Drop-offs:** {f.get('drop_offs_stat') or f.get('drop_offs_severity') or f.get('drop_offs_top_source')}")
            st.markdown("---")

    # 2. Portfolio Checking Frequency Comparison Chart
    st.subheader("📱 Portfolio Checking Frequency Comparison")
    cf_data = []
    for freq_key, fval in c_summary.get("check_frequency", {}).items():
        cf_data.append({"Frequency": freq_key.replace('_', ' ').title(), "Cohort": "Continuers", "Share (%)": fval["pct"]})
    for freq_key, fval in d_summary.get("check_frequency", {}).items():
        cf_data.append({"Frequency": freq_key.replace('_', ' ').title(), "Cohort": "Drop-offs", "Share (%)": fval["pct"]})

    if cf_data:
        df_cf = pd.DataFrame(cf_data)
        fig_cf = px.bar(
            df_cf,
            x="Frequency",
            y="Share (%)",
            color="Cohort",
            barmode="group",
            color_discrete_map={"Continuers": "#00D09C", "Drop-offs": "#EF4444"}
        )
        fig_cf.update_layout(height=320)
        st.plotly_chart(fig_cf, use_container_width=True)

    # 3. Verbatim User Quotes Comparison
    st.subheader("💬 Verbatim Voice Comparison")
    qc1, qc2 = st.columns(2)
    with qc1:
        st.markdown("#### Continuers Perspective")
        for q in c_summary.get("sample_quotes", [])[:3]:
            st.markdown(f"> *\"{q}\"*")

    with qc2:
        st.markdown("#### Drop-offs Perspective")
        for q in d_summary.get("sample_quotes", [])[:3]:
            st.markdown(f"> *\"{q}\"*")

