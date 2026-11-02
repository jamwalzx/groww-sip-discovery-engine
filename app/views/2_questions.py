"""
View 2: Core Behavioral Questions (Q1 to Q9) Deep Dives.
Dedicated analytical tabs for each of the 9 core product questions,
featuring interactive distribution charts, quantified metrics, and 3-5 verified quote cards.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.analytics.question_views import QuestionViewAggregator
from app.components.quote_card import render_quote_card


def render():
    st.title("🎯 Core Behavioral Question Deep Dives (Q1 - Q9)")
    st.markdown(
        "Explore quantitative distributions and verified verbatim quotes for the 9 core "
        "strategic questions driving first-time mutual fund SIP continuation breakdown."
    )

    aggregator = QuestionViewAggregator()
    all_q = aggregator.get_all_questions()

    tab_names = [
        "Q1: Start & Expectations",
        "Q2: Behavioral Evolution",
        "Q3: Drop Triggers & Churn",
        "Q4: Checking Frequency",
        "Q5: In-App Friction",
        "Q6: Outside-App Diet",
        "Q7: Continuers vs. Drop-offs",
        "Q8: Demographic Segments",
        "Q9: Unmet Product Needs"
    ]

    tabs = st.tabs(tab_names)

    # --- Q1 ---
    with tabs[0]:
        q1 = all_q.get("Q1", {})
        st.subheader("Q1: Why do people start a SIP, and what do they expect?")
        st.info(f"💡 **Key Growth PM Finding:** {q1.get('key_takeaway')}")

        col_m, col_e = st.columns(2)
        with col_m:
            st.markdown("#### Initial Motivations")
            m_data = [{"Motivation": k, "Count": v["count"], "Share (%)": v["pct"]} for k, v in q1.get("motivations_distribution", {}).items()]
            df_m = pd.DataFrame(m_data)
            fig_m = px.bar(df_m, x="Share (%)", y="Motivation", orientation="h", color="Share (%)", color_continuous_scale="Mint")
            fig_m.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_m, use_container_width=True)

        with col_e:
            st.markdown("#### Return Expectations at Start")
            e_data = [{"Expectation": k, "Count": v["count"], "Share (%)": v["pct"]} for k, v in q1.get("expectations_distribution", {}).items()]
            df_e = pd.DataFrame(e_data)
            fig_e = px.bar(df_e, x="Share (%)", y="Expectation", orientation="h", color="Share (%)", color_continuous_scale="Teal")
            fig_e.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_e, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (Day-1 Mindsets)")
        for card in q1.get("quote_cards", []):
            render_quote_card(card)

    # --- Q2 ---
    with tabs[1]:
        q2 = all_q.get("Q2", {})
        st.subheader("Q2: What changes in their behaviour in the months after starting?")
        st.info(f"💡 **Key Growth PM Finding:** {q2.get('key_takeaway')}")

        col_stg, col_shf = st.columns(2)
        with col_stg:
            st.markdown("#### Distribution Across Journey Stages")
            stg_data = [{"Stage": k.replace('_', ' ').title(), "Count": v["count"], "Share (%)": v["pct"]} for k, v in q2.get("journey_stage_breakdown", {}).items()]
            df_stg = pd.DataFrame(stg_data)
            fig_stg = px.pie(df_stg, names="Stage", values="Count", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_stg, use_container_width=True)

        with col_shf:
            st.markdown("#### Behavioral Shifts Encountered")
            shf_data = [{"Shift": k, "Count": v["count"], "Share (%)": v["pct"]} for k, v in q2.get("behavioural_shifts", {}).items()]
            df_shf = pd.DataFrame(shf_data)
            fig_shf = px.bar(df_shf, x="Share (%)", y="Shift", orientation="h", color_discrete_sequence=["#3B82F6"])
            fig_shf.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_shf, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (Evolution & Shifts)")
        for card in q2.get("quote_cards", []):
            render_quote_card(card)

    # --- Q3 ---
    with tabs[2]:
        q3 = all_q.get("Q3", {})
        st.subheader("Q3: What leads investors to pause, reduce or stop a SIP?")
        st.info(f"💡 **Key Growth PM Finding:** {q3.get('key_takeaway')}")

        col_trig, col_act = st.columns(2)
        with col_trig:
            st.markdown("#### Primary Discontinuation Triggers")
            t_data = [{"Trigger": k.replace('_', ' ').title(), "Count": v["count"], "Share (%)": v["pct"]} for k, v in q3.get("drop_triggers_distribution", {}).items()]
            df_trig = pd.DataFrame(t_data)
            fig_trig = px.bar(df_trig, x="Share (%)", y="Trigger", orientation="h", color="Share (%)", color_continuous_scale="Reds")
            fig_trig.update_layout(yaxis=dict(autorange="reversed"), height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_trig, use_container_width=True)

        with col_act:
            st.markdown("#### Actions Taken by Users")
            a_data = [{"Action": k.replace('_', ' ').title(), "Count": v["count"], "Share (%)": v["pct"]} for k, v in q3.get("actions_taken_distribution", {}).items()]
            df_act = pd.DataFrame(a_data)
            fig_act = px.pie(df_act, names="Action", values="Count", color_discrete_sequence=["#EF4444", "#F59E0B", "#10B981", "#6B7280"])
            st.plotly_chart(fig_act, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (Discontinuation Drivers)")
        for card in q3.get("quote_cards", []):
            render_quote_card(card)

    # --- Q4 ---
    with tabs[3]:
        q4 = all_q.get("Q4", {})
        st.subheader("Q4: What do investors check, and how often, once they have started?")
        st.info(f"💡 **Key Growth PM Finding:** {q4.get('key_takeaway')}")

        col_fq, col_mc = st.columns(2)
        with col_fq:
            st.markdown("#### Portfolio Checking Cadence")
            fq_data = [{"Frequency": k.replace('_', ' ').title(), "Share (%)": v["pct"]} for k, v in q4.get("frequency_distribution", {}).items()]
            df_fq = pd.DataFrame(fq_data)
            fig_fq = px.bar(df_fq, x="Frequency", y="Share (%)", color_discrete_sequence=["#00D09C"])
            fig_fq.update_layout(height=280)
            st.plotly_chart(fig_fq, use_container_width=True)

        with col_mc:
            st.markdown("#### Primary Metrics Scrutinized")
            mc_data = [{"Metric": k, "Mentions": v["count"], "Share (%)": v["pct"]} for k, v in q4.get("metrics_distribution", {}).items()]
            df_mc = pd.DataFrame(mc_data)
            fig_mc = px.bar(df_mc, x="Metric", y="Share (%)", color_discrete_sequence=["#3B82F6"])
            fig_mc.update_layout(height=280)
            st.plotly_chart(fig_mc, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (Checking Habits)")
        for card in q4.get("quote_cards", []):
            render_quote_card(card)

    # --- Q5 ---
    with tabs[4]:
        q5 = all_q.get("Q5", {})
        st.subheader("Q5: What confuses or worries them inside the app?")
        st.info(f"💡 **Key Growth PM Finding:** {q5.get('key_takeaway')}")

        fric_data = [{"Friction Point": k, "Mentions": v["count"], "Share (%)": v["pct"]} for k, v in q5.get("in_app_friction_distribution", {}).items()]
        df_fric = pd.DataFrame(fric_data)
        fig_fric = px.bar(df_fric, x="Share (%)", y="Friction Point", orientation="h", color="Share (%)", color_continuous_scale="Purples")
        fig_fric.update_layout(yaxis=dict(autorange="reversed"), height=300)
        st.plotly_chart(fig_fric, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (In-App Worry Points)")
        for card in q5.get("quote_cards", []):
            render_quote_card(card)

    # --- Q6 ---
    with tabs[5]:
        q6 = all_q.get("Q6", {})
        st.subheader("Q6: What do they do outside the app when they feel unsure?")
        st.info(f"💡 **Key Growth PM Finding:** {q6.get('key_takeaway')}")

        out_data = [{"Channel": k.replace('_', ' ').title(), "Count": v["count"], "Share (%)": v["pct"]} for k, v in q6.get("outside_sources_distribution", {}).items()]
        df_out = pd.DataFrame(out_data)
        fig_out = px.bar(df_out, x="Channel", y="Share (%)", color="Channel", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_out.update_layout(height=300)
        st.plotly_chart(fig_out, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (Outside-App Consultation)")
        for card in q6.get("quote_cards", []):
            render_quote_card(card)

    # --- Q7 ---
    with tabs[6]:
        q7 = all_q.get("Q7", {})
        st.subheader("Q7: What separates continuers from quiet drop-offs?")
        st.info(f"💡 **Key Growth PM Finding:** {q7.get('key_takeaway')}")

        col_c_vol, col_d_vol = st.columns(2)
        col_c_vol.metric("Disciplined Continuers", f"{q7.get('continuers_count')} ({q7.get('continuers_pct')}%)")
        col_d_vol.metric("Drop-offs & Churned", f"{q7.get('drop_offs_count')} ({q7.get('drop_offs_pct')}%)")

        st.markdown("#### Comparative Behavioral Contrast")
        for finding in q7.get("contrast_findings", []):
            with st.expander(f"🔍 {finding['dimension']}", expanded=True):
                st.write(f"**Finding:** {finding['finding']}")
                c_sub, d_sub = st.columns(2)
                c_sub.success(f"**Continuers:** {finding.get('continuers_stat') or finding.get('continuers_severity') or finding.get('continuers_top_source')}")
                d_sub.error(f"**Drop-offs:** {finding.get('drop_offs_stat') or finding.get('drop_offs_severity') or finding.get('drop_offs_top_source')}")

        st.markdown("#### 💬 Verified Verbatim Quotes (Continuers vs. Drop-offs)")
        for card in q7.get("quote_cards", []):
            render_quote_card(card)

    # --- Q8 ---
    with tabs[7]:
        q8 = all_q.get("Q8", {})
        st.subheader("Q8: How do patterns differ across user segments?")
        st.info(f"💡 **Key Growth PM Finding:** {q8.get('key_takeaway')}")
        st.write("Detailed multi-dimensional cross-tabulations and statistical confidence badges are available in the **Segment Explorer** tab.")

        st.markdown("#### 💬 Verified Verbatim Quotes Across Segments")
        for card in q8.get("quote_cards", []):
            render_quote_card(card)

    # --- Q9 ---
    with tabs[8]:
        q9 = all_q.get("Q9", {})
        st.subheader("Q9: What unmet needs emerge consistently across conversations?")
        st.info(f"💡 **Key Growth PM Finding:** {q9.get('key_takeaway')}")

        col_unm, col_emo = st.columns(2)
        with col_unm:
            st.markdown("#### Top Unmet Feature & Product Needs")
            u_data = [{"Feature / Need": k, "Mentions": v["count"], "Share (%)": v["pct"]} for k, v in q9.get("unmet_needs_distribution", {}).items()]
            df_u = pd.DataFrame(u_data)
            fig_u = px.bar(df_u, x="Share (%)", y="Feature / Need", orientation="h", color="Share (%)", color_continuous_scale="Viridis")
            fig_u.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_u, use_container_width=True)

        with col_emo:
            st.markdown("#### User Emotional States Expressed")
            emo_data = [{"Emotion": k.title(), "Count": v["count"], "Share (%)": v["pct"]} for k, v in q9.get("emotions_distribution", {}).items()]
            df_emo = pd.DataFrame(emo_data)
            fig_emo = px.pie(df_emo, names="Emotion", values="Count", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_emo, use_container_width=True)

        st.markdown("#### 💬 Verified Verbatim Quotes (Unmet Needs)")
        for card in q9.get("quote_cards", []):
            render_quote_card(card)

