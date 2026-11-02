"""
View 7: Live Interactive "Try-It" Sandbox.
Allows any visitor, mentor, or product evaluator to paste arbitrary review or discussion text
and inspect live Pydantic extraction, theme assignment, and quote integrity assertions.
"""

import streamlit as st
import json

from src.pipeline.extractor import StructuredExtractor
from src.analytics.opportunity_matrix import get_addressability_for_theme


SAMPLE_SNIPPETS = {
    "Hinglish Mandate Bounce": "Bhai mere account se 590 rs kat gaye mandate bounce ke naam pe! Salary 3rd ko aayi aur debit date 1st thi. Groww should give option to change date without cancel. Band kar raha hu SIP.",
    "Month 3 Volatility Panic": "Started SIP of 10000 in Nifty Smallcap 250 three months ago. Portfolio is down -6% and showing red every single day. Extremely anxious. Should I stop and put money in Fixed Deposit?",
    "Disciplined Continuer": "Have been running a monthly 5000 SIP on Groww for 3 years without a single pause. Key is setting auto-debit on the 7th after salary and ignoring daily NAV market noise.",
    "NAV Delay Confusion": "Money got deducted from my SBI bank account on Friday at 1 PM, but units are still not showing in my Groww mutual fund portfolio on Monday morning. Customer support is unresponsive."
}


def render():
    st.title("🧪 Live Interactive 'Try-It' Sandbox")
    st.markdown(
        "Paste any raw user review, tweet, Reddit post, or YouTube comment below to test the "
        "live extraction engine, schema validation, and thematic classification."
    )

    # Preset sample selector
    st.markdown("#### Or Select a Pre-Seeded Real-World Sample:")
    sample_cols = st.columns(len(SAMPLE_SNIPPETS))
    selected_sample = None
    for idx, (sname, stext) in enumerate(SAMPLE_SNIPPETS.items()):
        if sample_cols[idx].button(sname):
            selected_sample = stext

    default_text = selected_sample if selected_sample else (
        "Bank charged 590 rs mandate bounce fee because debit date was 1st and salary came on 3rd. "
        "Groww should let us choose debit date easily. Stopped my SIP immediately."
    )

    user_input = st.text_area("Input Raw Feedback Text:", value=default_text, height=120)

    if st.button("🚀 Run Live Behavioral Extraction", type="primary"):
        if not user_input.strip():
            st.error("Please enter some feedback text to analyze.")
            return

        with st.spinner("Executing schema-validated extraction..."):
            extractor = StructuredExtractor()
            insight = extractor.extract(user_input)

            # Check quote integrity
            quote_valid = insight.verbatim_quote in user_input

            st.success("✅ Extraction Complete — Strict Pydantic v2 Schema Validated!")

            # Metric cards
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Journey Stage", insight.journey_stage.replace('_', ' ').title())
            m2.metric("Drop Trigger", insight.drop_trigger.replace('_', ' ').title())
            m3.metric("Action Taken", insight.action_taken.replace('_', ' ').title())
            m4.metric("Distress Severity", f"{insight.severity} / 5")

            # Quote Verification Card
            st.markdown("### 💬 Verified Verbatim Quote Substring")
            if quote_valid:
                st.info(f"**Verbatim Quote:** \"{insight.verbatim_quote}\"")
                st.caption(f"✅ Verified: Programmatic check confirms exact match (`assert quote in raw_text`). Confidence: {insight.confidence * 100:.1f}%")
            else:
                st.error(f"⚠️ Quote Integrity Mismatch: \"{insight.verbatim_quote}\"")

            # Demographic & Cues
            st.markdown("### 👤 Demographic Cues & Behavior")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"- **Income Stability:** `{insight.segment_cues.income_stability}`")
                st.write(f"- **Primary Influencer:** `{insight.segment_cues.influencer}`")
                st.write(f"- **Investor Experience:** `{insight.segment_cues.investor_experience}`")
                st.write(f"- **Detected Emotion:** `{insight.emotion.title()}`")

            with c2:
                st.write(f"- **Check Frequency:** `{insight.check_behaviour.frequency}`")
                st.write(f"- **Metrics Checked:** `{', '.join(insight.check_behaviour.metrics_checked)}`")
                st.write(f"- **Outside App Sources:** `{', '.join(insight.outside_app_behaviour)}`")
                st.write(f"- **Synthesized Unmet Need:** `{insight.unmet_need}`")

            # JSON Schema View
            with st.expander("📄 View Raw Validated Pydantic JSON"):
                st.code(json.dumps(insight.model_dump(), indent=2), language="json")

