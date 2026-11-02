"""
Quote Card Component for Streamlit UI.
Renders authenticated verbatim user quotes with integrity verification badges and permalinks.
"""

import streamlit as st
from typing import Dict, Any


PLATFORM_COLORS = {
    "play_store": "#01875F",
    "app_store": "#0071E3",
    "reddit": "#FF4500",
    "youtube": "#FF0000",
    "manual_import": "#6B7280"
}


def render_quote_card(card: Dict[str, Any]):
    """
    Renders an authenticated verbatim quote card with source badge and permalink.
    """
    source = card.get("source", "play_store")
    color = PLATFORM_COLORS.get(source, "#00D09C")
    url = card.get("url", "#")
    quote = card.get("verbatim_quote", "")
    author = card.get("author_hash", "anonymous")
    severity = card.get("severity", 3)
    emotion = card.get("emotion", "neutral")
    is_verified = card.get("is_verified", True)

    badge_html = f"""
    <div style="
        border: 1px solid #E5E7EB;
        border-left: 4px solid {color};
        background: #F9FAFB;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="display: flex; gap: 8px; align-items: center;">
                <span style="
                    background: {color};
                    color: white;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 8px;
                    border-radius: 12px;
                    text-transform: uppercase;
                ">{source.replace('_', ' ')}</span>
                <span style="font-size: 12px; color: #6B7280; font-family: monospace;">ID: {author}</span>
            </div>
            <div>
                {'<span style="color: #059669; font-size: 11px; font-weight: 600; background: #D1FAE5; padding: 2px 6px; border-radius: 4px;">✅ Verbatim Verified</span>' if is_verified else '<span style="color: #DC2626; font-size: 11px; font-weight: 600; background: #FEE2E2; padding: 2px 6px; border-radius: 4px;">⚠️ Unverified</span>'}
            </div>
        </div>
        <p style="
            font-size: 14px;
            color: #1F2937;
            font-style: italic;
            line-height: 1.5;
            margin: 0 0 10px 0;
        ">"{quote}"</p>
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #4B5563;">
            <div>
                <span><b>Severity:</b> {severity}/5</span> &nbsp;|&nbsp;
                <span><b>Emotion:</b> {emotion.title()}</span>
            </div>
            <div>
                <a href="{url}" target="_blank" style="color: #00D09C; text-decoration: none; font-weight: 600;">View Original Post ↗</a>
            </div>
        </div>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)

