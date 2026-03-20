import streamlit as st

st.set_page_config(
    page_title="FRDM Internal Tools",
    page_icon="🛡️",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="padding: 1.5rem 0 0.5rem 0;">
        <h1 style="font-size:2rem; font-weight:700; color:#1a1a2e; margin:0;">
            🛡️ FRDM Internal Tools
        </h1>
        <p style="color:#555; margin-top:0.25rem; font-size:1rem;">
            Internal QA & testing utilities for the FRDM platform.
        </p>
    </div>
    <hr style="border:none; border-top:2px solid #e8eaf0; margin-bottom:1.5rem;">
    """,
    unsafe_allow_html=True,
)

# ── Tool card helper ──────────────────────────────────────────────────────────
def tool_card(icon, title, description, page_path, status="available"):
    status_color = {"available": "#28a745", "coming_soon": "#6c757d"}.get(status, "#6c757d")
    status_label = {"available": "Available", "coming_soon": "Coming Soon"}.get(status, status)
    clickable = status == "available"

    card_style = (
        "border:1px solid #e0e4ef; border-radius:10px; padding:1.25rem 1.5rem; "
        "background:#fff; height:100%; box-shadow:0 1px 4px rgba(0,0,0,0.06); "
        + ("cursor:pointer; transition:box-shadow 0.15s;" if clickable else "opacity:0.7;")
    )

    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="font-size:2rem; margin-bottom:0.4rem;">{icon}</div>
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.3rem;">
                <span style="font-size:1.05rem; font-weight:600; color:#1a1a2e;">{title}</span>
                <span style="font-size:0.7rem; font-weight:600; color:{status_color};
                    background:{status_color}18; border-radius:20px; padding:2px 8px;">
                    {status_label}
                </span>
            </div>
            <p style="color:#666; font-size:0.88rem; margin:0; line-height:1.5;">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if clickable:
        st.page_link(page_path, label=f"Open {title} →")


# ── Tools grid ────────────────────────────────────────────────────────────────
st.markdown("### Available Tools")

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    tool_card(
        icon="📊",
        title="Risk Score Analyzer",
        description=(
            "Upload a supplier risk report CSV and automatically detect scoring discrepancies "
            "— flagging suppliers where the overall risk level doesn't match their sub-scores. "
            "Useful for weekly QA of the scoring algorithm."
        ),
        page_path="pages/1_Risk_Score_Analyzer.py",
        status="available",
    )

with col2:
    tool_card(
        icon="🌿",
        title="Commitments Matcher",
        description=(
            "Upload a supplier file and reference databases (RE100, SBTi, CDP) to fuzzy-match "
            "suppliers against sustainability commitments. Review each match and export approved "
            "results as a clean CSV."
        ),
        page_path="pages/2_Commitments_Matcher.py",
        status="available",
    )

with col3:
    tool_card(
        icon="🔧",
        title="Tool 3",
        description="Next tool — description coming soon.",
        page_path="pages/3_Tool_3.py",
        status="coming_soon",
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <hr style="border:none; border-top:1px solid #e8eaf0; margin-top:3rem;">
    <p style="text-align:center; color:#aaa; font-size:0.8rem;">
        FRDM Internal Tools &nbsp;·&nbsp; For internal QA use only
    </p>
    """,
    unsafe_allow_html=True,
)
