"""
Commitments Matcher
-------------------
Upload a supplier file to fuzzy-match suppliers against bundled RE100, SBTi,
and CDP reference databases. Review each match and export approved results as CSV.

Reference databases are loaded from the data/ folder at the project root:
    data/re_100.xlsx
    data/sbti_most_update.xlsx   (sheet: "WebsiteData")
    data/cdp_grades_full.csv
"""

import io
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

# ── Paths to bundled reference databases ──────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_RE100_PATH = _DATA_DIR / "re_100.xlsx"
_SBTI_PATH  = _DATA_DIR / "sbti_most_update.xlsx"
_CDP_PATH   = _DATA_DIR / "cdp_grades_full.csv"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Commitments Matcher · FRDM Tools",
    page_icon="🌿",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_COMMITMENT_TYPES = [
    "SBTI_NEAR_TERM",
    "SBTI_NET_ZERO",
    "SBTI_LONG_TERM",
    "SBTI_LONG_TERM_PRE_CNZS",
    "CDP_GRADE_2024",
    "RE100",
]

OUTPUT_COLUMNS = [
    "business_entity_id",
    "commitment_type",
    "commitment_status",
    "target_year",
    "base_year",
    "scope_coverage",
    "commitment_details",
]

# ── Session state init ────────────────────────────────────────────────────────

def _try_load_bundled_dbs():
    """Load reference databases from data/ if they exist and haven't been loaded yet."""
    if st.session_state.re100_df is None and _RE100_PATH.exists():
        try:
            st.session_state.re100_df = pd.read_excel(_RE100_PATH, engine="openpyxl")
            st.session_state["_re100_source"] = "bundled"
        except Exception:
            pass

    if st.session_state.sbti_df is None and _SBTI_PATH.exists():
        try:
            xf = pd.ExcelFile(_SBTI_PATH, engine="openpyxl")
            sheet = "WebsiteData" if "WebsiteData" in xf.sheet_names else xf.sheet_names[0]
            st.session_state.sbti_df = pd.read_excel(_SBTI_PATH, sheet_name=sheet, engine="openpyxl")
            st.session_state["_sbti_source"] = "bundled"
        except Exception:
            pass

    if st.session_state.cdp_df is None and _CDP_PATH.exists():
        try:
            st.session_state.cdp_df = pd.read_csv(_CDP_PATH)
            st.session_state["_cdp_source"] = "bundled"
        except Exception:
            pass


def _init_state():
    defaults = {
        "supplier_df": None,
        "supplier_name_col": None,
        "entity_id_col": None,
        "re100_df": None,
        "sbti_df": None,
        "cdp_df": None,
        "pending_matches": [],
        "approved_matches": [],
        "review_idx": 0,
        "matching_done": False,
        "columns_confirmed": False,
        # track supplier file id to detect re-uploads
        "_supplier_file_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()
_try_load_bundled_dbs()

# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_name(name: str) -> str:
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()
    name = re.sub(r"[,\.]", "", name)
    return name


def extract_year(year_value) -> int | None:
    if pd.isna(year_value):
        return None
    match = re.search(r"(\d{4})", str(year_value))
    return int(match.group(1)) if match else None


def fuzzy_match(supplier_name: str, target_df: pd.DataFrame, target_column: str, threshold: int = 80):
    """Return (matched_original_name, score) or (None, 0)."""
    if pd.isna(supplier_name):
        return None, 0
    supplier_norm = normalize_name(supplier_name)
    target_names = target_df[target_column].dropna().unique()
    target_norm = [normalize_name(n) for n in target_names]
    if not target_norm:
        return None, 0
    result = process.extractOne(supplier_norm, target_norm, scorer=fuzz.ratio)
    if result and result[1] >= threshold:
        idx = target_norm.index(result[0])
        return target_names[idx], result[1]
    return None, 0


def classify_sbti_long_term(sbti_records: pd.DataFrame) -> str:
    target_types = set(sbti_records["target"].dropna().str.strip())
    has_net_zero = "Net-zero" in target_types or "Net-Zero" in target_types
    return "SBTI_LONG_TERM" if has_net_zero else "SBTI_LONG_TERM_PRE_CNZS"


def generate_matches_for_supplier(
    supplier_name, entity_id, re100_df, sbti_df, cdp_df, threshold: int
) -> list[dict]:
    results = []

    # RE100
    match, score = fuzzy_match(supplier_name, re100_df, "Name", threshold)
    if match:
        row = re100_df[re100_df["Name"] == match].iloc[0]
        results.append({
            "business_entity_id": entity_id,
            "commitment_type": "RE100",
            "commitment_status": "Member",
            "target_year": extract_year(row.get("Target year")),
            "base_year": extract_year(row.get("Joining year")),
            "scope_coverage": None,
            "commitment_details": f"Industry: {row.get('Industry', 'N/A')}",
            "_meta": {
                "source_db": "RE100",
                "supplier_name": supplier_name,
                "matched_name": match,
                "score": score,
            },
        })

    # SBTi
    match, score = fuzzy_match(supplier_name, sbti_df, "company_name", threshold)
    if match:
        records = sbti_df[sbti_df["company_name"] == match]
        long_term_type = classify_sbti_long_term(records)

        for _, srow in records.iterrows():
            target_type = srow.get("target")
            if pd.isna(target_type):
                continue
            target_type = str(target_type).strip()
            wording = srow.get("target_wording", "")
            details = str(wording)[:200] if pd.notna(wording) else None

            if target_type == "Near-term":
                ctype = "SBTI_NEAR_TERM"
            elif target_type == "Long-term":
                ctype = long_term_type
            elif target_type in ("Net-zero", "Net-Zero"):
                ctype = "SBTI_NET_ZERO"
            else:
                continue

            scope = srow.get("scope")
            base_year = srow.get("base_year")
            target_year = srow.get("target_year")

            results.append({
                "business_entity_id": entity_id,
                "commitment_type": ctype,
                "commitment_status": "Committed",
                "target_year": int(target_year) if pd.notna(target_year) else None,
                "base_year": int(base_year) if pd.notna(base_year) else None,
                "scope_coverage": scope if pd.notna(scope) else None,
                "commitment_details": details,
                "_meta": {
                    "source_db": "SBTi",
                    "supplier_name": supplier_name,
                    "matched_name": match,
                    "score": score,
                    "sbti_target_type": target_type,
                },
            })

    # CDP
    match, score = fuzzy_match(supplier_name, cdp_df, "Company Name", threshold)
    if match:
        row = cdp_df[cdp_df["Company Name"] == match].iloc[0]
        if pd.notna(row.get("Grade")):
            results.append({
                "business_entity_id": entity_id,
                "commitment_type": "CDP_GRADE_2024",
                "commitment_status": row["Grade"],
                "target_year": None,
                "base_year": None,
                "scope_coverage": None,
                "commitment_details": None,
                "_meta": {
                    "source_db": "CDP",
                    "supplier_name": supplier_name,
                    "matched_name": match,
                    "score": score,
                },
            })

    return results


def load_excel_or_csv(uploaded_file, sheet_name=None):
    """Read an uploaded file into a DataFrame, auto-detecting format."""
    fname = uploaded_file.name.lower()
    raw = io.BytesIO(uploaded_file.read())
    if fname.endswith(".csv"):
        return pd.read_csv(raw), None
    elif fname.endswith(".tsv"):
        return pd.read_csv(raw, sep="\t"), None
    elif fname.endswith(".ods"):
        xf = pd.ExcelFile(raw, engine="odf")
        sname = sheet_name or xf.sheet_names[0]
        raw.seek(0)
        return pd.read_excel(raw, sheet_name=sname, engine="odf"), xf.sheet_names
    else:  # xlsx / xls
        xf = pd.ExcelFile(raw, engine="openpyxl")
        sname = sheet_name or xf.sheet_names[0]
        raw.seek(0)
        return pd.read_excel(raw, sheet_name=sname, engine="openpyxl"), xf.sheet_names


def score_color(score: int) -> str:
    if score >= 95:
        return "#28a745"
    if score >= 85:
        return "#fd7e14"
    return "#dc3545"


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="font-size:1.8rem; font-weight:700; color:#1a1a2e; margin-bottom:0.2rem;">
        🌿 Commitments Matcher
    </h1>
    <p style="color:#555; margin-top:0; margin-bottom:1.5rem;">
        Upload a supplier file and sustainability reference databases to fuzzy-match
        suppliers against RE100, SBTi, and CDP commitments. Review each match, then
        export the approved results as a clean CSV.
    </p>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Match Settings")
    threshold = st.slider(
        "Fuzzy match threshold",
        min_value=50,
        max_value=100,
        value=80,
        step=5,
        help="Minimum similarity score (0–100) required to consider two names a match.",
    )
    st.markdown("---")
    st.markdown(
        """
        **Workflow**

        1. Upload your supplier file
        2. Map the name & ID columns
        3. Run matching
        4. Review each match — Approve ✅ or Deny ❌
        5. Export approved commitments as CSV

        **Reference databases** are loaded automatically
        from the `data/` folder in the repo:
        - `re_100.xlsx`
        - `sbti_most_update.xlsx`
        - `cdp_grades_full.csv`

        **Commitment types produced**
        - `RE100`
        - `SBTI_NEAR_TERM`
        - `SBTI_LONG_TERM`
        - `SBTI_LONG_TERM_PRE_CNZS`
        - `SBTI_NET_ZERO`
        - `CDP_GRADE_2024`
        """
    )
    st.markdown("---")
    st.caption("FRDM Internal Tools · QA use only")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Upload supplier file
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 1 — Upload Supplier File")

supplier_file = st.file_uploader(
    "Supplier file",
    type=["xlsx", "xls", "csv", "ods", "tsv"],
    key="supplier_upload",
    help="Supported formats: Excel (.xlsx/.xls), CSV, ODS, TSV",
)

if supplier_file is not None:
    file_id = f"{supplier_file.name}-{supplier_file.size}"

    # Re-load only if a new file is uploaded
    if file_id != st.session_state._supplier_file_id:
        st.session_state._supplier_file_id = file_id
        st.session_state.columns_confirmed = False
        st.session_state.matching_done = False
        st.session_state.pending_matches = []
        st.session_state.approved_matches = []
        st.session_state.review_idx = 0

        fname_lower = supplier_file.name.lower()
        if fname_lower.endswith((".xlsx", ".xls", ".ods")):
            # Need sheet selection — defer loading
            raw = io.BytesIO(supplier_file.read())
            engine = "odf" if fname_lower.endswith(".ods") else "openpyxl"
            xf = pd.ExcelFile(raw, engine=engine)
            st.session_state["_supplier_sheets"] = xf.sheet_names
            st.session_state["_supplier_engine"] = engine
            st.session_state["_supplier_bytes"] = supplier_file.getvalue()
            st.session_state["_supplier_selected_sheet"] = xf.sheet_names[0]
            # Load first sheet immediately
            raw2 = io.BytesIO(st.session_state["_supplier_bytes"])
            df = pd.read_excel(raw2, sheet_name=xf.sheet_names[0], engine=engine)
            st.session_state.supplier_df = df
        else:
            df, _ = load_excel_or_csv(supplier_file)
            st.session_state.supplier_df = df
            st.session_state["_supplier_sheets"] = None

    # Sheet picker (Excel/ODS only)
    sheets = st.session_state.get("_supplier_sheets")
    if sheets:
        selected_sheet = st.selectbox(
            "Select sheet",
            options=sheets,
            index=sheets.index(st.session_state.get("_supplier_selected_sheet", sheets[0])),
        )
        if selected_sheet != st.session_state.get("_supplier_selected_sheet"):
            st.session_state["_supplier_selected_sheet"] = selected_sheet
            st.session_state.columns_confirmed = False
            raw2 = io.BytesIO(st.session_state["_supplier_bytes"])
            engine = st.session_state["_supplier_engine"]
            st.session_state.supplier_df = pd.read_excel(raw2, sheet_name=selected_sheet, engine=engine)

    df = st.session_state.supplier_df
    if df is not None:
        cols = list(df.columns)

        # Auto-detect likely columns
        def _auto_pick(cols, keywords_list):
            for col in cols:
                cl = col.lower().replace("_", " ")
                if all(k in cl for k in keywords_list):
                    return col
            return cols[0]

        default_name = _auto_pick(cols, ["supplier", "name"]) or _auto_pick(cols, ["name"])
        default_id = _auto_pick(cols, ["business", "entity", "id"])

        col_left, col_right = st.columns(2)
        with col_left:
            name_col = st.selectbox(
                "Supplier name column",
                options=cols,
                index=cols.index(default_name) if default_name in cols else 0,
            )
        with col_right:
            id_col = st.selectbox(
                "Business entity ID column",
                options=cols,
                index=cols.index(default_id) if default_id in cols else 0,
            )

        st.dataframe(df.head(10), use_container_width=True, height=220)

        if st.button("✅ Confirm Column Mapping", type="primary"):
            st.session_state.supplier_name_col = name_col
            st.session_state.entity_id_col = id_col
            st.session_state.columns_confirmed = True
            st.session_state.matching_done = False
            st.session_state.pending_matches = []
            st.session_state.approved_matches = []
            st.session_state.review_idx = 0

        if st.session_state.columns_confirmed:
            st.success(
                f"Columns confirmed — **name**: `{st.session_state.supplier_name_col}` | "
                f"**entity ID**: `{st.session_state.entity_id_col}` | "
                f"**{len(df):,}** rows loaded."
            )
else:
    st.info("Upload a supplier file to begin.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Reference database status
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 2 — Reference Databases")

db_col1, db_col2, db_col3 = st.columns(3)

def _db_status(label, df, path):
    if df is not None:
        st.success(f"**{label}** — {len(df):,} records")
    else:
        st.error(f"**{label}** — file not found: `{path.name}`")

with db_col1:
    _db_status("RE100", st.session_state.re100_df, _RE100_PATH)
with db_col2:
    _db_status("SBTi", st.session_state.sbti_df, _SBTI_PATH)
with db_col3:
    _db_status("CDP", st.session_state.cdp_df, _CDP_PATH)

all_dbs_ready = (
    st.session_state.re100_df is not None
    and st.session_state.sbti_df is not None
    and st.session_state.cdp_df is not None
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Run matching
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 3 — Run Commitment Matching")

ready_to_run = st.session_state.columns_confirmed and all_dbs_ready

if not ready_to_run:
    missing = []
    if not st.session_state.columns_confirmed:
        missing.append("confirm column mapping (Step 1)")
    if not all_dbs_ready:
        missing.append("upload all three reference databases (Step 2)")
    st.info(f"To run matching, please: {' and '.join(missing)}.")
else:
    if st.button("🚀 Run Matching", type="primary"):
        df = st.session_state.supplier_df
        name_col = st.session_state.supplier_name_col
        id_col = st.session_state.entity_id_col

        all_pending = []
        total = len(df)

        progress = st.progress(0, text="Starting…")
        for i, (_, row) in enumerate(df.iterrows()):
            supplier_name = row[name_col]
            entity_id = row[id_col]

            if pd.isna(supplier_name):
                continue

            matches = generate_matches_for_supplier(
                supplier_name,
                entity_id,
                st.session_state.re100_df,
                st.session_state.sbti_df,
                st.session_state.cdp_df,
                threshold,
            )
            all_pending.extend(matches)

            pct = int((i + 1) / total * 100)
            if (i + 1) % 20 == 0 or i == total - 1:
                progress.progress(pct, text=f"Processed {i+1:,} / {total:,} suppliers…")

        progress.empty()

        st.session_state.pending_matches = all_pending
        st.session_state.approved_matches = []
        st.session_state.review_idx = 0
        st.session_state.matching_done = True
        st.rerun()

if st.session_state.matching_done:
    n = len(st.session_state.pending_matches)
    st.success(f"Matching complete — **{n:,}** potential commitment matches found.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Review matches
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 4 — Review Matches")

if not st.session_state.matching_done:
    st.info("Run matching first (Step 3).")
else:
    pending = st.session_state.pending_matches
    idx = st.session_state.review_idx
    approved = st.session_state.approved_matches
    n_pending = len(pending)

    if idx >= n_pending:
        # Review complete
        n_approved = len(approved)
        n_denied = n_pending - n_approved
        st.success(
            f"Review complete! **{n_approved}** approved, **{n_denied}** denied/skipped."
        )
    else:
        # Progress indicator
        reviewed = idx
        pct = int(reviewed / n_pending * 100) if n_pending else 100
        st.progress(pct, text=f"Reviewed {reviewed} / {n_pending} matches")

        # Auto-approve panel
        with st.expander("⚡ Auto-approve by score threshold", expanded=False):
            auto_threshold = st.number_input(
                "Auto-approve all remaining matches with score ≥",
                min_value=50,
                max_value=100,
                value=95,
                step=1,
            )
            if st.button("⚡ Apply Auto-Approve"):
                auto_count = 0
                i = st.session_state.review_idx
                while i < len(pending):
                    if pending[i]["_meta"]["score"] >= auto_threshold:
                        st.session_state.approved_matches.append(pending[i])
                        auto_count += 1
                    i += 1
                st.session_state.review_idx = len(pending)
                st.toast(f"Auto-approved {auto_count} matches with score ≥ {auto_threshold}.")
                st.rerun()

        st.markdown("---")

        # Current match card
        match = pending[idx]
        meta = match["_meta"]
        sc = meta["score"]

        st.markdown(f"#### Match {idx + 1} / {n_pending}")

        info_col, score_col = st.columns([3, 1])
        with info_col:
            st.markdown(
                f"**Your supplier:** `{meta['supplier_name']}`  \n"
                f"**Matched to ({meta['source_db']}):** `{meta['matched_name']}`"
            )
        with score_col:
            color = score_color(sc)
            st.markdown(
                f"<div style='text-align:center; padding:0.5rem;'>"
                f"<div style='font-size:0.75rem; color:#888;'>Fuzzy score</div>"
                f"<div style='font-size:2rem; font-weight:700; color:{color};'>{sc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Commitment details table
        display = {k: v for k, v in match.items() if k != "_meta"}
        st.dataframe(pd.DataFrame([display]), use_container_width=True, hide_index=True)

        # Action buttons
        btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 3])
        with btn_col1:
            if st.button("✅ Approve", type="primary", use_container_width=True):
                st.session_state.approved_matches.append(pending[idx])
                st.session_state.review_idx += 1
                st.rerun()
        with btn_col2:
            if st.button("❌ Deny", use_container_width=True):
                st.session_state.review_idx += 1
                st.rerun()
        with btn_col3:
            if st.button("⏭ Skip", use_container_width=True):
                st.session_state.review_idx += 1
                st.rerun()

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Export
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 5 — Export Approved Commitments")

review_done = st.session_state.matching_done and (
    st.session_state.review_idx >= len(st.session_state.pending_matches)
)

if not review_done:
    st.info("Complete the review (Step 4) to export results.")
else:
    approved = st.session_state.approved_matches

    if not approved:
        st.warning("No approved matches to export.")
    else:
        include_name = st.checkbox(
            "Include supplier name column in output (for manual QA)",
            value=False,
        )

        clean_rows = []
        for m in approved:
            row = {k: v for k, v in m.items() if k != "_meta"}
            if include_name:
                row["supplier_name"] = m["_meta"]["supplier_name"]
            clean_rows.append(row)

        out_df = pd.DataFrame(clean_rows)

        # Column ordering
        ordered_cols = ["business_entity_id"]
        if include_name:
            ordered_cols.append("supplier_name")
        ordered_cols += [c for c in OUTPUT_COLUMNS[1:] if c in out_df.columns]
        out_df = out_df[[c for c in ordered_cols if c in out_df.columns]]
        out_df = out_df.sort_values(["business_entity_id", "commitment_type"])

        # Warn on unexpected types
        unexpected = out_df[~out_df["commitment_type"].isin(VALID_COMMITMENT_TYPES)]
        if len(unexpected):
            st.warning(
                f"{len(unexpected)} rows have unexpected `commitment_type` values: "
                f"`{'`, `'.join(unexpected['commitment_type'].unique())}`"
            )

        st.markdown(f"**{len(out_df):,}** commitment rows ready to export.")
        st.dataframe(out_df.head(20), use_container_width=True, hide_index=True)

        csv_bytes = out_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Commitments CSV",
            data=csv_bytes,
            file_name="commitments_output.csv",
            mime="text/csv",
            type="primary",
        )
