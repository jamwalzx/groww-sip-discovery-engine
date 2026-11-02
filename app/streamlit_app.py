"""
Groww AI Discovery Engine: Primary Streamlit Application.
Multi-page analytical dashboard diagnosing first-time mutual fund SIP continuation breakdown.
"""

import streamlit as st
import sys
from pathlib import Path

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Streamlit Page Config
st.set_page_config(
    page_title="Groww SIP Discovery Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Groww Brand Palette: Mint Green #00D09C, Slate Dark #1E222B)
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 700;
        color: #1E222B;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 20px;
    }
    .stMetric {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        padding: 12px;
        border-radius: 8px;
    }
    div[data-testid="stSidebarNav"] {
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Import View Modules
from src.db.database import init_db
from src.evals.audit_log import AuditLogManager

# Ensure database and audit tables are initialized
init_db()
AuditLogManager().seed_default_cases()

from app.views import (
    render_overview,
    render_questions,
    render_opportunity_matrix,
    render_segments,
    render_cohorts,
    render_evals,
    render_try_it
)

# Sidebar Navigation
with st.sidebar:
    st.image(
        "https://groww.in/groww-logo-270.png",
        width=130
    )
    st.markdown("### 📈 SIP Discovery Engine")
    st.caption("AI Growth Analytics for Months 1–12 SIP Retention")

    st.markdown("---")
    menu = st.radio(
        "Navigate Dashboard Views:",
        [
            "1. Overview & Data Funnel",
            "2. Questions Deep Dives (Q1-Q9)",
            "3. Opportunity Matrix",
            "4. Segment Explorer (n < 30)",
            "5. Continuers vs. Drop-offs",
            "6. Evals & Golden Set (Cohen's κ)",
            "7. Live 'Try-It' Sandbox"
        ]
    )

    st.markdown("---")
    st.markdown("### 🛡️ Compliance Guardrails")
    st.caption("• Zero PII (SHA-256 salted author hashes)")
    st.caption("• 100% Verbatim quote integrity assertion")
    st.caption("• Strictly no stock or mutual fund picking")
    st.caption("• Strictly no fear/FOMO/urgency triggers")
    st.caption("• Statistical gating: n < 30 flagged")

# Route to selected view
if menu == "1. Overview & Data Funnel":
    render_overview()
elif menu == "2. Questions Deep Dives (Q1-Q9)":
    render_questions()
elif menu == "3. Opportunity Matrix":
    render_opportunity_matrix()
elif menu == "4. Segment Explorer (n < 30)":
    render_segments()
elif menu == "5. Continuers vs. Drop-offs":
    render_cohorts()
elif menu == "6. Evals & Golden Set (Cohen's κ)":
    render_evals()
elif menu == "7. Live 'Try-It' Sandbox":
    render_try_it()

