"""
Risk Score Analyzer
-------------------
Upload a FRDM supplier risk report CSV and detect scoring discrepancies —
cases where the overall risk level diverges significantly from the sub-scores.
"""

import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Risk Score Analyzer · FRDM Tools",
    page_icon="📊",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────

# Maps categorical risk labels → numeric 0-1 for comparison
RISK_LABEL_MAP = {
    "low": 0.15,
    "weak": 0.15,
    "moderate": 0.40,
    "elevated": 0.70,
    "high": 0.90,
    "critical": 1.00,
}

# Sub-score columns that feed the overall score (all 0-1)
SUB_SCORE_COLS = [
    "all_country_risk_score",
    "all_industry_risk_score",
    "purchase_risk",
    "trade_partner_risk",
]

# Human-friendly labels for the sub-scores
SUB_SCORE_LABELS = {
    "all_country_risk_score": "Country Risk",
    "all_industry_risk_score": "Industry Risk",
    "purchase_risk": "Purchase Risk",
    "trade_partner_risk": "Trade Partner Risk",
}

# Columns expected in the CSV (subset we actually use)
EXPECTED_COLS = {
    "Supplier",
    "Overall Risk Level",
    "topline_risk_score",
    "all_country_risk_score",
    "all_industry_risk_score",
    "purchase_risk",
    "trade_partner_risk",
}

DISCREPANCY_LEVELS = {
    "Low (≥0.20)": 0.20,
    "Medium (≥0.30)": 0.30,
    "High (≥0.40)": 0.40,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def label_to_numeric(series: pd.Series) -> pd.Series:
    """Convert a risk-level label column to 0-1 numeric."""
    return series.str.strip().str.lower().map(RISK_LABEL_MAP)


def compute_composite_sub_score(df: pd.DataFrame) -> pd.Series:
    """Row-wise mean of the available sub-score columns."""
    available = [c for c in SUB_SCORE_COLS if c in df.columns]
    return df[available].apply(pd.to_numeric, errors="coerce").mean(axis=1)


def classify_discrepancy(row) -> str:
    """Return a short reason string for the flagged discrepancy."""
    overall = row.get("_overall_numeric", None)
    composite = row.get("_composite_sub_score", None)
    if pd.isna(overall) or pd.isna(composite):
        return "Missing data"
    if overall > composite:
        return "Overall higher than sub-scores"
    return "Overall lower than sub-scores"


def risk_badge(label: str) -> str:
    colors = {
        "low": ("#155724", "#d4edda"),
        "weak": ("#155724", "#d4edda"),
        "moderate": ("#856404", "#fff3cd"),
        "elevated": ("#c45500", "#ffe5cc"),
        "high": ("#721c24", "#f8d7da"),
        "critical": ("#4a0010", "#f5c6cb"),
    }
    key = str(label).strip().lower()
    fg, bg = colors.get(key, ("#333", "#eee"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:2px 8px; '
        f'border-radius:12px; font-size:0.78rem; font-weight:600;">'
        f'{label}</span>'
    )


def score_bar(value, color="#1a73e8") -> str:
    if pd.isna(value):
        return "<span style='color:#aaa;'>—</span>"
    pct = min(max(float(value), 0), 1) * 100
    return (
        f'<div style="display:flex; align-items:center; gap:6px;">'
        f'<div style="flex:1; background:#eee; border-radius:4px; height:8px;">'
        f'<div style="width:{pct:.0f}%; background:{color}; height:8px; border-radius:4px;"></div>'
        f'</div>'
        f'<span style="font-size:0.8rem; min-width:36px;">{value:.2f}</span>'
        f'</div>'
    )


def load_csv(uploaded_file) -> pd.DataFrame:
    """Load CSV, trying multiple encodings."""
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding=enc, low_memory=False)
        except Exception:
            continue
    raise ValueError("Could not parse the uploaded file.")


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed columns used for analysis."""
    df = df.copy()

    if "Overall Risk Level" in df.columns:
        df["_overall_numeric"] = label_to_numeric(df["Overall Risk Level"])
    else:
        df["_overall_numeric"] = pd.NA

    if "topline_risk_score" in df.columns:
        df["_topline"] = pd.to_numeric(df["topline_risk_score"], errors="coerce")
    else:
        df["_topline"] = pd.NA

    df["_composite_sub_score"] = compute_composite_sub_score(df)

    # Primary gap: topline_risk_score vs composite (most direct signal)
    # Fall back to overall_numeric if topline missing
    primary_score = df["_topline"].fillna(df["_overall_numeric"])
    df["_gap"] = (primary_score - df["_composite_sub_score"]).abs()

    df["_direction"] = df.apply(classify_discrepancy, axis=1)
    return df


def context_summary(row) -> str:
    """Build a short context string for why the discrepancy might be legitimate."""
    parts = []
    alerts = row.get("all_alerts_count", None)
    if pd.notna(alerts) and float(alerts) > 0:
        parts.append(f"{int(float(alerts))} alert(s)")
    prod_reg = row.get("Product Regulation", None)
    if pd.notna(prod_reg) and str(prod_reg).strip() not in ("", "nan"):
        parts.append(f"Product regs: {prod_reg}")
    ind_reg = row.get("Industry Regulation", None)
    if pd.notna(ind_reg) and str(ind_reg).strip() not in ("", "nan"):
        parts.append(f"Industry regs: {ind_reg}")
    docs = row.get("Documents", None)
    if pd.notna(docs) and str(docs).strip() not in ("", "nan", "0"):
        parts.append(f"Documents: {docs}")
    return " · ".join(parts) if parts else "No additional context in report"


# ── Page ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <h1 style="font-size:1.8rem; font-weight:700; color:#1a1a2e; margin-bottom:0.2rem;">
        📊 Risk Score Analyzer
    </h1>
    <p style="color:#555; margin-top:0; margin-bottom:1.5rem;">
        Upload a supplier risk report CSV to detect scoring discrepancies between
        the overall risk level and its contributing sub-scores.
    </p>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar – controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    threshold_label = st.selectbox(
        "Flag discrepancies at",
        options=list(DISCREPANCY_LEVELS.keys()),
        index=1,
        help=(
            "Minimum gap between the overall/topline score and the composite "
            "sub-score average to consider a row a discrepancy."
        ),
    )
    threshold = DISCREPANCY_LEVELS[threshold_label]

    st.markdown("---")
    st.markdown(
        """
        **How it works**

        For each supplier the tool computes:

        1. **Topline score** – `topline_risk_score` (0–1)
        2. **Composite sub-score** – average of country, industry, purchase,
           and trade-partner risk scores (0–1)
        3. **Gap** = |topline − composite|

        Rows where the gap exceeds the threshold are flagged.

        Alerts, regulations, and other context columns are surfaced to help
        distinguish legitimate discrepancies from algorithm errors.
        """
    )
    st.markdown("---")
    st.caption("FRDM Internal Tools · QA use only")

# ── File upload ───────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload supplier risk report CSV",
    type=["csv"],
    help="Export the supplier overview report from the FRDM platform and upload here.",
)

if not uploaded:
    st.info("Upload a CSV file above to begin analysis.")
    st.stop()

# ── Load & validate ───────────────────────────────────────────────────────────
try:
    raw_df = load_csv(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

missing = EXPECTED_COLS - set(raw_df.columns)
if missing:
    st.warning(
        f"The following expected columns were not found and will be skipped: "
        f"`{'`, `'.join(sorted(missing))}`"
    )

df = enrich(raw_df)
total = len(df)
flagged_df = df[df["_gap"] >= threshold].copy()
flagged_count = len(flagged_df)
clean_count = total - flagged_count

# ── Summary metrics ───────────────────────────────────────────────────────────
st.markdown("### Summary")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Total Suppliers", total)
with m2:
    st.metric(
        "Flagged",
        flagged_count,
        delta=f"{flagged_count/total*100:.1f}% of total" if total else None,
        delta_color="inverse",
    )
with m3:
    st.metric("Clean", clean_count)
with m4:
    avg_gap = df["_gap"].mean()
    st.metric("Avg Gap", f"{avg_gap:.3f}" if pd.notna(avg_gap) else "—")

st.markdown("---")

# ── Distribution chart ────────────────────────────────────────────────────────
col_chart, col_pie = st.columns([2, 1])

with col_chart:
    st.markdown("#### Gap Distribution")
    fig = px.histogram(
        df.dropna(subset=["_gap"]),
        x="_gap",
        nbins=20,
        labels={"_gap": "Gap (|Topline − Composite Sub-Score|)", "count": "Suppliers"},
        color_discrete_sequence=["#1a73e8"],
    )
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Threshold ({threshold})",
        annotation_position="top right",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_pie:
    st.markdown("#### Overall Risk Level Mix")
    if "Overall Risk Level" in df.columns:
        level_counts = (
            df["Overall Risk Level"]
            .fillna("Unknown")
            .str.strip()
            .str.title()
            .value_counts()
            .reset_index()
        )
        level_counts.columns = ["Level", "Count"]
        color_map = {
            "Low": "#28a745",
            "Weak": "#28a745",
            "Moderate": "#ffc107",
            "Elevated": "#fd7e14",
            "High": "#dc3545",
            "Critical": "#6f0020",
            "Unknown": "#adb5bd",
        }
        fig2 = px.pie(
            level_counts,
            values="Count",
            names="Level",
            color="Level",
            color_discrete_map=color_map,
            hole=0.45,
        )
        fig2.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=280,
            showlegend=True,
            legend=dict(orientation="v", x=1, y=0.5),
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No 'Overall Risk Level' column found.")

st.markdown("---")

# ── Flagged suppliers ─────────────────────────────────────────────────────────
st.markdown(f"### Flagged Suppliers ({flagged_count})")

if flagged_count == 0:
    st.success(
        f"No discrepancies found at the current threshold ({threshold}). "
        "All overall scores are consistent with sub-scores."
    )
else:
    # Direction filter
    directions = flagged_df["_direction"].dropna().unique().tolist()
    filter_direction = st.multiselect(
        "Filter by direction",
        options=directions,
        default=directions,
    )
    view_df = flagged_df[flagged_df["_direction"].isin(filter_direction)]

    # Sort by gap descending
    view_df = view_df.sort_values("_gap", ascending=False)

    for _, row in view_df.iterrows():
        supplier_name = row.get("Supplier", "Unknown Supplier")
        overall_label = row.get("Overall Risk Level", "—")
        topline = row.get("_topline", None)
        composite = row.get("_composite_sub_score", None)
        gap = row.get("_gap", None)
        direction = row.get("_direction", "")
        context = context_summary(row)

        direction_color = "#e74c3c" if "higher" in direction else "#e67e22"
        gap_str = f"{gap:.3f}" if pd.notna(gap) else "—"
        topline_str = f"{float(topline):.3f}" if pd.notna(topline) else "—"
        composite_str = f"{float(composite):.3f}" if pd.notna(composite) else "—"

        with st.expander(
            f"⚠️ {supplier_name}  —  Overall: {overall_label}  |  Gap: {gap_str}",
            expanded=False,
        ):
            r1, r2, r3 = st.columns(3)
            with r1:
                st.markdown("**Topline Score**")
                st.markdown(
                    score_bar(topline, "#1a73e8") if pd.notna(topline) else "—",
                    unsafe_allow_html=True,
                )
            with r2:
                st.markdown("**Composite Sub-Score**")
                st.markdown(
                    score_bar(composite, "#34a853") if pd.notna(composite) else "—",
                    unsafe_allow_html=True,
                )
            with r3:
                st.markdown("**Gap**")
                st.markdown(
                    f'<span style="font-size:1.3rem; font-weight:700; color:{direction_color};">'
                    f'{gap_str}</span> '
                    f'<span style="color:#888; font-size:0.85rem;">({direction})</span>',
                    unsafe_allow_html=True,
                )

            st.markdown("**Sub-Scores Breakdown**")
            sub_cols = st.columns(len(SUB_SCORE_COLS))
            for i, col_name in enumerate(SUB_SCORE_COLS):
                val = row.get(col_name, None)
                label = SUB_SCORE_LABELS[col_name]
                with sub_cols[i]:
                    st.markdown(f"<small style='color:#888;'>{label}</small>", unsafe_allow_html=True)
                    if pd.notna(val):
                        num_val = pd.to_numeric(val, errors="coerce")
                        st.markdown(score_bar(num_val, "#5f6368"), unsafe_allow_html=True)
                    else:
                        st.markdown("<small style='color:#aaa;'>—</small>", unsafe_allow_html=True)

            # Additional context
            st.markdown("**Context (possible explanations)**")
            st.markdown(
                f'<div style="background:#f8f9fa; border-left:3px solid #1a73e8; '
                f'padding:0.5rem 0.75rem; border-radius:4px; font-size:0.85rem; color:#555;">'
                f'{context}</div>',
                unsafe_allow_html=True,
            )

            # Country / Industry for reference
            detail_parts = []
            for col in ["countries", "Country Risk Level", "industries", "Industry Risk Level",
                        "products", "Product Risk Level", "Spend Level", "tags"]:
                val = row.get(col, None)
                if pd.notna(val) and str(val).strip() not in ("", "nan"):
                    detail_parts.append(f"**{col}:** {val}")

            if detail_parts:
                with st.expander("Show full detail", expanded=False):
                    for part in detail_parts:
                        st.markdown(part)
                    portal_url = row.get("portal_in_url", None)
                    if pd.notna(portal_url) and str(portal_url).startswith("http"):
                        st.markdown(f"[Open in FRDM Portal]({portal_url})")

    st.markdown("---")

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown("### Export Flagged Results")

    export_cols = (
        ["Supplier", "Overall Risk Level", "_topline", "_composite_sub_score", "_gap", "_direction"]
        + [c for c in SUB_SCORE_COLS if c in view_df.columns]
        + [c for c in ["all_alerts_count", "Product Regulation", "Industry Regulation",
                        "countries", "industries", "tags", "portal_in_url"]
           if c in view_df.columns]
    )
    export_df = view_df[[c for c in export_cols if c in view_df.columns]].rename(
        columns={
            "_topline": "Topline Score",
            "_composite_sub_score": "Composite Sub-Score",
            "_gap": "Gap",
            "_direction": "Direction",
        }
    )

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Flagged Suppliers CSV",
        data=csv_bytes,
        file_name="flagged_discrepancies.csv",
        mime="text/csv",
    )

# ── Full data table ───────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("View full dataset", expanded=False):
    display_cols = (
        ["Supplier", "Overall Risk Level", "_topline", "_composite_sub_score", "_gap"]
        + [c for c in SUB_SCORE_COLS if c in df.columns]
    )
    st.dataframe(
        df[[c for c in display_cols if c in df.columns]]
        .rename(
            columns={
                "_topline": "Topline",
                "_composite_sub_score": "Composite",
                "_gap": "Gap",
            }
        )
        .sort_values("Gap", ascending=False),
        use_container_width=True,
    )
