"""Accessorial Invoice Checker (v1) - Streamlit Web Application.

Deterministic auditing and dispute package generation for freight brokers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from src.ocr import process_invoice
from src.report import (
    build_csv_report,
    build_markdown_report,
    format_currency,
    generate_reports,
)
from src.rules import (
    STATUS_APPROVE,
    STATUS_DISPUTE,
    STATUS_REQUIRE_PROOF,
    AuditResult,
    audit_invoice,
)

# Page configuration
st.set_page_config(
    page_title="Accessorial Invoice Checker",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern UI styling
st.markdown(
    """
<style>
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-value {
        font-size: 2.0rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 4px;
    }
    .badge-approved {
        background-color: #d1fae5;
        color: #065f46;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        border: 1px solid #10b981;
        display: inline-block;
    }
    .badge-disputed {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        border: 1px solid #ef4444;
        display: inline-block;
    }
    .badge-proof {
        background-color: #fef3c7;
        color: #92400e;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        border: 1px solid #f59e0b;
        display: inline-block;
    }
    .badge-flag {
        background-color: #ffedd5;
        color: #c2410c;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #fdba74;
        margin-right: 4px;
        display: inline-block;
    }
    .audit-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .audit-table th {
        background-color: #f8fafc;
        color: #475569;
        font-weight: 700;
        text-align: left;
        padding: 12px 14px;
        border-bottom: 2px solid #e2e8f0;
    }
    .audit-table td {
        padding: 12px 14px;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: top;
    }
    .audit-table tr:hover {
        background-color: #fbfcfe;
    }
    .broker-disclaimer {
        background: #eff6ff;
        border-left: 6px solid #2563eb;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 25px 0 15px 0;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.08);
    }
</style>
""",
    unsafe_allow_html=True,
)


# Default Sample Data definitions
DEFAULT_TERMS = {
    "linehaul_fsc": 1500.0,
    "prepull_fee": 150.0,
    "chassis_per_day": 45.0,
    "storage_per_day": 45.0,
    "detention_per_hour": 75.0,
    "detention_free_hours": 2.0,
    "chassis_day_policy": "calendar_day",
    "chassis_free_days": 0,
    "chassis_min_days": 0,
    "storage_free_days": 0,
    "prepull_includes_first_storage_day": "unknown",
    "direct_move_hours_threshold": 24.0,
}

DEFAULT_TIMELINE_TIMESTAMPS = {
    "terminal_pickup": ("2026-06-23T21:00", False),
    "yard_in": ("", True),
    "yard_out": ("", True),
    "warehouse_appointment": ("2026-06-24T08:00", False),
    "delivery_actual": ("2026-06-24T08:00", False),
    "warehouse_in": ("", True),
    "warehouse_out": ("", True),
    "empty_return": ("2026-06-24T16:00", False),
}

DEFAULT_INVOICE_LINES = [
    {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1500.0, "amount": 1500.0},
    {"type": "prepull", "qty": 1.0, "unit_rate": 150.0, "amount": 150.0},
    {"type": "chassis", "qty": 3.0, "unit_rate": 45.0, "amount": 135.0},
    {"type": "storage", "qty": 2.0, "unit_rate": 45.0, "amount": 90.0},
]
DEFAULT_INVOICE_TOTAL = 1875.0

TIMESTAMPS_METADATA = [
    ("terminal_pickup", "Terminal Pickup", "Container out-gate from marine port or rail ramp"),
    ("yard_in", "Yard In-Gate", "Arrival at carrier staging yard"),
    ("yard_out", "Yard Out-Gate", "Departure from carrier staging yard"),
    ("warehouse_appointment", "Warehouse Appt", "Consignee delivery appointment schedule"),
    ("delivery_actual", "Actual Delivery", "Physical container delivery / drop at consignee"),
    ("warehouse_in", "Warehouse In-Gate", "Driver check-in at consignee facility"),
    ("warehouse_out", "Warehouse Out-Gate", "Driver departure after unloading"),
    ("empty_return", "Empty Return", "In-gate of empty container at port or depot"),
]


def init_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    if "editor_version" not in st.session_state:
        st.session_state["editor_version"] = 0

    if "invoice_lines_data" not in st.session_state:
        st.session_state["invoice_lines_data"] = [dict(x) for x in DEFAULT_INVOICE_LINES]

    if "invoice_total" not in st.session_state:
        st.session_state["invoice_total"] = DEFAULT_INVOICE_TOTAL

    if "audit_result" not in st.session_state:
        st.session_state["audit_result"] = None

    if "ocr_raw_text" not in st.session_state:
        st.session_state["ocr_raw_text"] = ""

    # Rate Terms
    for k, v in DEFAULT_TERMS.items():
        key_name = f"term_{k}"
        if key_name not in st.session_state:
            st.session_state[key_name] = v

    # Timeline Timestamps
    for k, (val_str, is_null) in DEFAULT_TIMELINE_TIMESTAMPS.items():
        if f"ts_val_{k}" not in st.session_state:
            st.session_state[f"ts_val_{k}"] = val_str
        if f"ts_null_{k}" not in st.session_state:
            st.session_state[f"ts_null_{k}"] = is_null

    if "pod_provided" not in st.session_state:
        st.session_state["pod_provided"] = False

    if "prepull_request_documented" not in st.session_state:
        st.session_state["prepull_request_documented"] = "unknown"


def load_sample_case_1() -> None:
    """Load exact sample data from sample_data/ or fallback defaults."""
    terms_file = Path("sample_data/terms.json")
    timeline_file = Path("sample_data/timeline.json")
    invoice_file = Path("sample_data/invoice.json")

    # 1. Rate Terms
    if terms_file.is_file():
        try:
            with open(terms_file, "r", encoding="utf-8") as f:
                t = json.load(f)
        except Exception:
            t = DEFAULT_TERMS
    else:
        t = DEFAULT_TERMS

    st.session_state["term_linehaul_fsc"] = float(t.get("linehaul_fsc", 1500.0))
    st.session_state["term_prepull_fee"] = float(t.get("prepull_fee", 150.0))
    st.session_state["term_chassis_per_day"] = float(t.get("chassis_per_day", 45.0))
    st.session_state["term_storage_per_day"] = float(t.get("storage_per_day", 45.0))
    st.session_state["term_detention_per_hour"] = float(t.get("detention_per_hour", 75.0))
    st.session_state["term_detention_free_hours"] = float(t.get("detention_free_hours", 2.0))

    policy = t.get("chassis_day_policy")
    if policy in ("calendar_day", "24h_block"):
        st.session_state["term_chassis_day_policy"] = policy
    else:
        st.session_state["term_chassis_day_policy"] = "unknown (show both side-by-side)"

    st.session_state["term_chassis_free_days"] = int(t.get("chassis_free_days", 0))
    st.session_state["term_chassis_min_days"] = int(t.get("chassis_min_days", 0))
    st.session_state["term_storage_free_days"] = int(t.get("storage_free_days", 0))

    prepull_storage = t.get("prepull_includes_first_storage_day")
    if prepull_storage is True:
        st.session_state["term_prepull_includes_first_storage_day"] = "yes"
    elif prepull_storage is False:
        st.session_state["term_prepull_includes_first_storage_day"] = "no"
    else:
        st.session_state["term_prepull_includes_first_storage_day"] = "unknown"

    st.session_state["term_direct_move_hours_threshold"] = float(
        t.get("direct_move_hours_threshold", 24.0)
    )

    # 2. Timeline
    if timeline_file.is_file():
        try:
            with open(timeline_file, "r", encoding="utf-8") as f:
                tl = json.load(f)
        except Exception:
            tl = {}
    else:
        tl = {}

    for k, (def_val, def_null) in DEFAULT_TIMELINE_TIMESTAMPS.items():
        v = tl.get(k)
        if v is None or str(v).lower() in ("null", "none", ""):
            st.session_state[f"ts_null_{k}"] = True
            st.session_state[f"ts_val_{k}"] = ""
        else:
            st.session_state[f"ts_null_{k}"] = False
            st.session_state[f"ts_val_{k}"] = str(v)

    st.session_state["pod_provided"] = bool(tl.get("pod_provided", False))

    prepull_req = tl.get("prepull_request_documented")
    if prepull_req is True:
        st.session_state["prepull_request_documented"] = "yes"
    elif prepull_req is False:
        st.session_state["prepull_request_documented"] = "no"
    else:
        st.session_state["prepull_request_documented"] = "unknown"

    # 3. Invoice
    if invoice_file.is_file():
        try:
            with open(invoice_file, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = {"lines": DEFAULT_INVOICE_LINES, "total": DEFAULT_INVOICE_TOTAL}
    else:
        inv = {"lines": DEFAULT_INVOICE_LINES, "total": DEFAULT_INVOICE_TOTAL}

    st.session_state["invoice_lines_data"] = [dict(x) for x in inv.get("lines", DEFAULT_INVOICE_LINES)]
    st.session_state["invoice_total"] = float(inv.get("total", DEFAULT_INVOICE_TOTAL))
    st.session_state["editor_version"] += 1
    st.session_state["audit_result"] = None
    st.toast("✅ Sample Data (Test Case 1) loaded successfully!", icon="🚚")


init_session_state()

# Top Navigation & Header
st.title("🚚 Accessorial Invoice Checker")
st.caption(
    "Deterministic drayage invoice audit engine — Protect freight brokers from overbilling on chassis fees, yard storage, pre-pull, and detention."
)

# Header Action Bar
col_h1, col_h2, col_h3 = st.columns([2.5, 1, 1])
with col_h1:
    st.markdown(
        "**Operating Mode:** 100% Deterministic & Local | **Zero AI APIs** | **Zero Paid Subscriptions**"
    )
with col_h2:
    if st.button("⚡ Load Sample Data (Test Case 1)", use_container_width=True, type="secondary"):
        load_sample_case_1()
        st.rerun()
with col_h3:
    if st.button("🔄 Reset to Blank", use_container_width=True):
        for k in list(DEFAULT_TERMS.keys()):
            st.session_state[f"term_{k}"] = 0.0 if "per" in k or "fee" in k or "rate" in k else 0
        st.session_state["term_chassis_day_policy"] = "calendar_day"
        st.session_state["term_prepull_includes_first_storage_day"] = "unknown"
        st.session_state["term_direct_move_hours_threshold"] = 24.0
        for k in DEFAULT_TIMELINE_TIMESTAMPS:
            st.session_state[f"ts_val_{k}"] = ""
            st.session_state[f"ts_null_{k}"] = True
        st.session_state["pod_provided"] = False
        st.session_state["prepull_request_documented"] = "unknown"
        st.session_state["invoice_lines_data"] = []
        st.session_state["invoice_total"] = 0.0
        st.session_state["editor_version"] += 1
        st.session_state["audit_result"] = None
        st.rerun()

st.divider()

# Main Tabs
tab_terms, tab_timeline, tab_invoice = st.tabs(
    [
        "📋 1. Rate Terms",
        "⏱️ 2. Container Timeline",
        "🧾 3. Invoice & OCR Extraction",
    ]
)

# -------------------------------------------------------------
# TAB 1: RATE TERMS
# -------------------------------------------------------------
with tab_terms:
    st.subheader("Contracted Drayage Rate Agreement")
    st.markdown(
        "Enter the agreed accessorial rates and billing terms established with the carrier for this container move."
    )

    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.session_state["term_linehaul_fsc"] = st.number_input(
            "Base Linehaul + FSC ($)",
            min_value=0.0,
            value=float(st.session_state["term_linehaul_fsc"]),
            step=50.0,
            format="%.2f",
            help="Agreed combined linehaul and fuel surcharge amount",
        )
        st.session_state["term_prepull_fee"] = st.number_input(
            "Pre-pull Fee ($)",
            min_value=0.0,
            value=float(st.session_state["term_prepull_fee"]),
            step=25.0,
            format="%.2f",
            help="Agreed rate if pre-pull is requested and authorized",
        )
        st.session_state["term_direct_move_hours_threshold"] = st.number_input(
            "Direct Move Threshold (Hours)",
            min_value=1.0,
            value=float(st.session_state["term_direct_move_hours_threshold"]),
            step=1.0,
            format="%.1f",
            help="Pickup-to-delivery elapsed hours threshold below which a move without yard timestamps is flagged as a direct move (default 24h)",
        )

    with col_t2:
        st.session_state["term_chassis_per_day"] = st.number_input(
            "Chassis Daily Rate ($/day)",
            min_value=0.0,
            value=float(st.session_state["term_chassis_per_day"]),
            step=5.0,
            format="%.2f",
            help="Contracted per-day chassis usage rate",
        )
        policy_options = ["calendar_day", "24h_block", "unknown (show both side-by-side)"]
        curr_policy = st.session_state["term_chassis_day_policy"]
        pol_idx = policy_options.index(curr_policy) if curr_policy in policy_options else 0
        st.session_state["term_chassis_day_policy"] = st.selectbox(
            "Chassis Day Billing Policy",
            options=policy_options,
            index=pol_idx,
            help="Calendar day (counts midnights/calendar dates) vs 24-hour block (counts elapsed duration in 24h increments)",
        )
        col_cp1, col_cp2 = st.columns(2)
        with col_cp1:
            st.session_state["term_chassis_free_days"] = st.number_input(
                "Chassis Free Days",
                min_value=0,
                value=int(st.session_state["term_chassis_free_days"]),
                step=1,
            )
        with col_cp2:
            st.session_state["term_chassis_min_days"] = st.number_input(
                "Chassis Min Days",
                min_value=0,
                value=int(st.session_state["term_chassis_min_days"]),
                step=1,
            )

    with col_t3:
        st.session_state["term_storage_per_day"] = st.number_input(
            "Yard Storage Daily Rate ($/day)",
            min_value=0.0,
            value=float(st.session_state["term_storage_per_day"]),
            step=5.0,
            format="%.2f",
            help="Contracted per-day carrier yard storage fee",
        )
        st.session_state["term_storage_free_days"] = st.number_input(
            "Storage Free Days",
            min_value=0,
            value=int(st.session_state["term_storage_free_days"]),
            step=1,
        )
        prepull_store_options = ["unknown", "yes", "no"]
        curr_ps = st.session_state["term_prepull_includes_first_storage_day"]
        ps_idx = prepull_store_options.index(curr_ps) if curr_ps in prepull_store_options else 0
        st.session_state["term_prepull_includes_first_storage_day"] = st.selectbox(
            "Pre-pull Includes 1st Storage Day?",
            options=prepull_store_options,
            index=ps_idx,
            help="Does the agreed pre-pull fee include the first night of yard storage?",
        )

    st.markdown("##### Driver Detention Terms")
    col_det1, col_det2 = st.columns(2)
    with col_det1:
        st.session_state["term_detention_per_hour"] = st.number_input(
            "Detention Hourly Rate ($/hr)",
            min_value=0.0,
            value=float(st.session_state["term_detention_per_hour"]),
            step=5.0,
            format="%.2f",
        )
    with col_det2:
        st.session_state["term_detention_free_hours"] = st.number_input(
            "Detention Free Hours (Allowable Wait Time)",
            min_value=0.0,
            value=float(st.session_state["term_detention_free_hours"]),
            step=0.5,
            format="%.1f",
        )

# -------------------------------------------------------------
# TAB 2: CONTAINER TIMELINE
# -------------------------------------------------------------
with tab_timeline:
    st.subheader("Container Move Milestones & Verification Timestamps")
    st.markdown(
        "Enter verified event timestamps (from port out-gate slips, GPS logs, or receiver in-gates). "
        "Check **Unknown / Null** if a milestone was not recorded."
    )

    # Render 8 timestamps in a clean 2-column grid
    col_grid_left, col_grid_right = st.columns(2)
    for idx, (ts_key, ts_label, ts_desc) in enumerate(TIMESTAMPS_METADATA):
        target_col = col_grid_left if idx < 4 else col_grid_right
        with target_col:
            st.markdown(f"**{ts_label}** <span style='font-size:0.8rem; color:#64748b;'>({ts_desc})</span>", unsafe_allow_html=True)
            col_inp, col_nl = st.columns([3, 1.2])
            with col_nl:
                is_null = st.checkbox(
                    "Unknown / Null",
                    value=st.session_state.get(f"ts_null_{ts_key}", True),
                    key=f"ts_null_{ts_key}",
                )
            with col_inp:
                st.text_input(
                    label=ts_label,
                    label_visibility="collapsed",
                    value="" if is_null else st.session_state.get(f"ts_val_{ts_key}", ""),
                    placeholder="YYYY-MM-DDTHH:MM",
                    disabled=is_null,
                    key=f"ts_val_{ts_key}",
                )
            st.write("")

    st.divider()
    st.markdown("##### Supporting Documentation Checklist")
    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        st.session_state["pod_provided"] = st.checkbox(
            "📄 Proof of Delivery (POD) signed and provided",
            value=bool(st.session_state.get("pod_provided", False)),
            help="Carrier provided a signed delivery receipt. (If unchecked, approval is PROVISIONAL).",
        )
    with col_doc2:
        prepull_req_opts = ["unknown", "yes", "no"]
        curr_pr = st.session_state.get("prepull_request_documented", "unknown")
        pr_idx = prepull_req_opts.index(curr_pr) if curr_pr in prepull_req_opts else 0
        st.session_state["prepull_request_documented"] = st.selectbox(
            "📋 Pre-pull Request Documented & Authorized by Broker / Customer?",
            options=prepull_req_opts,
            index=pr_idx,
            help="Was an early pull specifically requested in writing?",
        )

# -------------------------------------------------------------
# TAB 3: INVOICE & OCR EXTRACTION
# -------------------------------------------------------------
with tab_invoice:
    st.subheader("Carrier Invoice Intake & Line-Item Review")
    st.markdown(
        "Upload an invoice (JSON or PDF/Image) or review and edit the extracted line items directly in the table."
    )

    with st.expander("📤 Ingest Invoice from File (JSON or PDF/Image)", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose invoice file",
            type=["json", "pdf", "png", "jpg", "jpeg"],
            help="Upload structured JSON or scan PDF/Image via OCR",
        )

        if uploaded_file is not None:
            col_up1, col_up2 = st.columns(2)
            fname = uploaded_file.name.lower()

            if fname.endswith(".json"):
                with col_up1:
                    if st.button("📂 Load Uploaded JSON Invoice", use_container_width=True):
                        try:
                            data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                            lines = data.get("lines", [])
                            tot = float(data.get("total", 0.0))
                            st.session_state["invoice_lines_data"] = lines
                            st.session_state["invoice_total"] = tot
                            st.session_state["editor_version"] += 1
                            st.success(f"Loaded {len(lines)} lines from JSON invoice (Total: {format_currency(tot)})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to parse JSON file: {e}")

            if fname.endswith((".pdf", ".png", ".jpg", ".jpeg")):
                with col_up2:
                    if st.button("🔍 Extract from PDF / Image (Free OCR.space & pdfplumber)", type="primary", use_container_width=True):
                        with st.spinner("Extracting invoice text and classifying accessorial charges..."):
                            try:
                                parsed = process_invoice(uploaded_file.getvalue())
                                st.session_state["ocr_raw_text"] = parsed.get("raw_text", "")
                                lines = parsed.get("lines", [])
                                tot = parsed.get("total", 0.0)

                                if lines:
                                    st.session_state["invoice_lines_data"] = lines
                                    st.session_state["invoice_total"] = float(tot)
                                    st.session_state["editor_version"] += 1
                                    st.success(f"Extracted {len(lines)} line items! (Total: {format_currency(tot)})")
                                    st.rerun()
                                else:
                                    st.warning("OCR completed, but no standard drayage line items were automatically matched. You can enter lines manually below.")
                            except Exception as exc:
                                st.error(f"OCR extraction error: {exc}")

    if st.session_state.get("ocr_raw_text"):
        with st.expander("📄 View Raw OCR Extracted Text", expanded=False):
            st.text_area("Extracted Raw Text", st.session_state["ocr_raw_text"], height=160, disabled=True)

    st.markdown("##### Human-in-the-Loop Line Review & Editor")
    st.caption("Review, edit, add (+), or delete line items before running the audit.")

    # Convert session data into DataFrame for data_editor
    current_lines = st.session_state.get("invoice_lines_data", [])
    df_raw = pd.DataFrame(current_lines)
    if df_raw.empty:
        df_raw = pd.DataFrame(columns=["type", "qty", "unit_rate", "amount"])

    # Ensure required columns exist
    for col in ["type", "qty", "unit_rate", "amount"]:
        if col not in df_raw.columns:
            df_raw[col] = 0.0 if col != "type" else "chassis"

    editor_key = f"inv_editor_{st.session_state['editor_version']}"
    edited_df = st.data_editor(
        df_raw[["type", "qty", "unit_rate", "amount"]],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "type": st.column_config.SelectboxColumn(
                "Charge Type",
                help="Drayage accessorial category",
                width="medium",
                options=["linehaul_fsc", "prepull", "chassis", "storage", "detention"],
                required=True,
            ),
            "qty": st.column_config.NumberColumn(
                "Billed Qty / Days",
                help="Quantity billed by carrier",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                required=True,
            ),
            "unit_rate": st.column_config.NumberColumn(
                "Unit Rate ($)",
                help="Rate billed per unit",
                min_value=0.0,
                step=5.0,
                format="$%.2f",
                required=True,
            ),
            "amount": st.column_config.NumberColumn(
                "Line Total ($)",
                help="Total billed for this line",
                min_value=0.0,
                step=5.0,
                format="$%.2f",
                required=True,
            ),
        },
        key=editor_key,
    )

    col_tot1, col_tot2 = st.columns([2, 1])
    with col_tot1:
        st.session_state["invoice_total"] = st.number_input(
            "Invoice Stated Total Billed ($)",
            min_value=0.0,
            value=float(st.session_state["invoice_total"]),
            step=10.0,
            format="%.2f",
            help="Grand total billed on the carrier's invoice",
        )
    with col_tot2:
        st.write("")
        st.write("")
        calc_sum = float(edited_df["amount"].sum()) if not edited_df.empty else 0.0
        if st.button(f"⚡ Sync Total to Sum of Lines ({format_currency(calc_sum)})", use_container_width=True):
            st.session_state["invoice_total"] = round(calc_sum, 2)
            st.rerun()

# -------------------------------------------------------------
# AUDIT TRIGGER ACTION BAR
# -------------------------------------------------------------
st.write("")
col_run_btn, col_run_info = st.columns([2, 3])

with col_run_btn:
    run_audit_clicked = st.button(
        "🚀 Check Invoice & Audit Discrepancies",
        type="primary",
        use_container_width=True,
    )

with col_run_info:
    st.caption(
        "Executes deterministic rules engine, generates audit summary, and writes `report.md`, `result.json`, and `result.csv` to `output/`."
    )

if run_audit_clicked:
    # 1. Gather terms dict
    terms_dict: Dict[str, Any] = {
        "linehaul_fsc": float(st.session_state["term_linehaul_fsc"]),
        "prepull_fee": float(st.session_state["term_prepull_fee"]),
        "chassis_per_day": float(st.session_state["term_chassis_per_day"]),
        "storage_per_day": float(st.session_state["term_storage_per_day"]),
        "detention_per_hour": float(st.session_state["term_detention_per_hour"]),
        "detention_free_hours": float(st.session_state["term_detention_free_hours"]),
        "chassis_free_days": int(st.session_state["term_chassis_free_days"]),
        "chassis_min_days": int(st.session_state["term_chassis_min_days"]),
        "storage_free_days": int(st.session_state["term_storage_free_days"]),
        "direct_move_hours_threshold": float(st.session_state["term_direct_move_hours_threshold"]),
    }

    # Policy
    pol_selection = st.session_state["term_chassis_day_policy"]
    if pol_selection == "unknown (show both side-by-side)":
        terms_dict["chassis_day_policy"] = None
        override_pol = None
    else:
        terms_dict["chassis_day_policy"] = pol_selection
        override_pol = pol_selection

    # Pre-pull includes storage
    pps = st.session_state["term_prepull_includes_first_storage_day"]
    if pps == "yes":
        terms_dict["prepull_includes_first_storage_day"] = True
    elif pps == "no":
        terms_dict["prepull_includes_first_storage_day"] = False
    else:
        terms_dict["prepull_includes_first_storage_day"] = None

    # 2. Gather timeline dict
    timeline_dict: Dict[str, Any] = {}
    for ts_key, _, _ in TIMESTAMPS_METADATA:
        is_nl = st.session_state.get(f"ts_null_{ts_key}", True)
        val = st.session_state.get(f"ts_val_{ts_key}", "").strip()
        timeline_dict[ts_key] = None if (is_nl or not val) else val

    timeline_dict["pod_provided"] = bool(st.session_state.get("pod_provided", False))

    prd = st.session_state.get("prepull_request_documented", "unknown")
    if prd == "yes":
        timeline_dict["prepull_request_documented"] = True
    elif prd == "no":
        timeline_dict["prepull_request_documented"] = False
    else:
        timeline_dict["prepull_request_documented"] = None

    # 3. Gather invoice dict
    invoice_lines_list: List[Dict[str, Any]] = []
    if not edited_df.empty:
        for _, r in edited_df.iterrows():
            c_type = str(r["type"]).strip().lower()
            q = float(r["qty"]) if pd.notna(r["qty"]) else 0.0
            u = float(r["unit_rate"]) if pd.notna(r["unit_rate"]) else 0.0
            a = float(r["amount"]) if pd.notna(r["amount"]) else (q * u)
            invoice_lines_list.append({"type": c_type, "qty": q, "unit_rate": u, "amount": a})

    invoice_dict: Dict[str, Any] = {
        "lines": invoice_lines_list,
        "total": float(st.session_state["invoice_total"]),
    }

    # Run deterministic audit
    with st.spinner("Running deterministic audit rules..."):
        try:
            audit_res = audit_invoice(
                invoice=invoice_dict,
                terms=terms_dict,
                timeline=timeline_dict,
                override_policy=override_pol,
            )

            # Generate files in output/
            output_dir = Path("output")
            report_paths = generate_reports(audit_res, output_dir=output_dir)

            st.session_state["audit_result"] = audit_res
            st.session_state["report_paths"] = {k: str(v) for k, v in report_paths.items()}
            st.toast("🎉 Invoice checked! Reports generated in output/ folder.", icon="✅")
        except Exception as e:
            st.error(f"Audit engine execution failed: {e}")

# -------------------------------------------------------------
# AUDIT RESULTS VIEW
# -------------------------------------------------------------
audit_result: Optional[AuditResult] = st.session_state.get("audit_result")

if audit_result is not None:
    st.divider()
    summary = audit_result.summary

    st.header("📊 Audit Results & Financial Findings")

    # Financial Metric Cards
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

    with col_m1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-title">Total Billed</div>
            <div class="metric-value">{format_currency(summary.total_billed)}</div>
            <div class="metric-sub">Carrier invoice total</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_m2:
        prov_badge = (
            '<span class="badge-proof" style="font-size:0.65rem; padding: 2px 6px;">PROVISIONAL</span>'
            if summary.is_provisional
            else ""
        )
        st.markdown(
            f"""
        <div class="metric-card" style="background:#f0fdf4; border-color:#bbf7d0;">
            <div class="metric-title" style="color:#15803d;">
                <span>Approved</span> {prov_badge}
            </div>
            <div class="metric-value" style="color:#16a34a;">{format_currency(summary.approved_amount)}</div>
            <div class="metric-sub" style="color:#15803d;">Verified against terms</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_m3:
        st.markdown(
            f"""
        <div class="metric-card" style="background:#fff5f5; border-color:#fecaca;">
            <div class="metric-title" style="color:#991b1b;">Disputed</div>
            <div class="metric-value" style="color:#dc2626;">{format_currency(summary.disputed_amount)}</div>
            <div class="metric-sub" style="color:#b91c1c;">Rejected excess charges</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_m4:
        st.markdown(
            f"""
        <div class="metric-card" style="background:#fffbeb; border-color:#fde68a;">
            <div class="metric-title" style="color:#92400e;">Needs Proof</div>
            <div class="metric-value" style="color:#d97706;">{format_currency(summary.needs_proof_amount)}</div>
            <div class="metric-sub" style="color:#b45309;">Held pending records</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_m5:
        st.markdown(
            f"""
        <div class="metric-card" style="background:#f8fafc; border:2px solid #cbd5e1;">
            <div class="metric-title" style="color:#334155;">Total Not Approved</div>
            <div class="metric-value" style="color:#0f172a;">{format_currency(summary.not_approved_amount)}</div>
            <div class="metric-sub" style="color:#64748b;">Disputed + Needs Proof</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Flags notification if any
    if summary.flags:
        flags_html = "".join([f'<span class="badge-flag">{fl}</span>' for fl in summary.flags])
        st.markdown(
            f"""
        <div style="background:#fff7ed; border-left:4px solid #ea580c; padding:10px 14px; border-radius:6px; margin: 10px 0 16px 0;">
            <strong style="color:#9a3412;">⚠️ Invoice Integrity Flags:</strong> {flags_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Side-by-side comparison if policy was unknown / null
    if audit_result.alternative_policy_result:
        alt_res = audit_result.alternative_policy_result
        alt_sum = alt_res.get("summary", {})

        st.markdown("#### ⚖️ Side-by-Side Billing Policy Comparison")
        st.caption(
            "Because `chassis_day_policy` was unspecified in the contract, both industry-standard interpretations are computed side-by-side:"
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(
                f"""
            <div class="metric-card" style="border-top: 4px solid #3b82f6;">
                <h4 style="margin-top:0; color:#1e40af;">📅 Policy A: Calendar Day</h4>
                <p style="font-size:0.85rem; color:#64748b;">Counts distinct calendar dates / midnight crossovers.</p>
                <hr style="margin: 8px 0;"/>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>Approved:</span> <strong>{format_currency(summary.approved_amount)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>Disputed:</span> <strong style="color:#dc2626;">{format_currency(summary.disputed_amount)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>Needs Proof:</span> <strong style="color:#d97706;">{format_currency(summary.needs_proof_amount)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; font-weight:700; border-top:1px solid #e2e8f0; padding-top:4px;">
                    <span>Total Withheld:</span> <span>{format_currency(summary.not_approved_amount)}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_p2:
            st.markdown(
                f"""
            <div class="metric-card" style="border-top: 4px solid #8b5cf6;">
                <h4 style="margin-top:0; color:#6d28d9;">⏱️ Policy B: 24-Hour Block</h4>
                <p style="font-size:0.85rem; color:#64748b;">Counts elapsed duration in 24-hour blocks (ceil(hours / 24)).</p>
                <hr style="margin: 8px 0;"/>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>Approved:</span> <strong>{format_currency(alt_sum.get("approved_amount", 0.0))}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>Disputed:</span> <strong style="color:#dc2626;">{format_currency(alt_sum.get("disputed_amount", 0.0))}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>Needs Proof:</span> <strong style="color:#d97706;">{format_currency(alt_sum.get("needs_proof_amount", 0.0))}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; font-weight:700; border-top:1px solid #e2e8f0; padding-top:4px;">
                    <span>Total Withheld:</span> <span>{format_currency(alt_sum.get("not_approved_amount", 0.0))}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Line-by-Line Table styled with color badges
    st.markdown("#### 🔎 Line-by-Line Audit Breakdown")

    table_rows_html = []
    for line in audit_result.lines:
        if line.status == STATUS_APPROVE:
            status_badge = '<span class="badge-approved">APPROVE</span>'
        elif line.status == STATUS_DISPUTE:
            status_badge = '<span class="badge-disputed">DISPUTE</span>'
        elif line.status == STATUS_REQUIRE_PROOF:
            status_badge = '<span class="badge-proof">REQUIRE_PROOF</span>'
        else:
            status_badge = f'<span class="badge-flag">{line.status}</span>'

        flags_str = (
            "".join([f'<span class="badge-flag">{f}</span>' for f in line.flags])
            if line.flags
            else '<span style="color:#94a3b8;">—</span>'
        )

        table_rows_html.append(
            f"""
        <tr>
            <td><strong><code>{line.type}</code></strong></td>
            <td>{line.qty:g} @ {format_currency(line.unit_rate)}<br/><strong>{format_currency(line.amount)}</strong></td>
            <td style="color:#16a34a; font-weight:700;">{format_currency(line.approved_amount)}</td>
            <td style="color:#dc2626; font-weight:700;">{format_currency(line.disputed_amount)}</td>
            <td style="color:#d97706; font-weight:700;">{format_currency(line.needs_proof_amount)}</td>
            <td>{status_badge}</td>
            <td>{flags_str}</td>
            <td style="font-size:0.87rem; color:#334155; line-height:1.4;">{line.reason}</td>
        </tr>
        """
        )

    full_table_html = f"""
    <div style="overflow-x:auto;">
    <table class="audit-table">
        <thead>
            <tr>
                <th>Type</th>
                <th>Billed</th>
                <th>Approved</th>
                <th>Disputed</th>
                <th>Needs Proof</th>
                <th>Status</th>
                <th>Flags</th>
                <th>Plain English Evidence & Math</th>
            </tr>
        </thead>
        <tbody>
            {"".join(table_rows_html)}
        </tbody>
    </table>
    </div>
    """
    st.markdown(full_table_html, unsafe_allow_html=True)

    # Expandable details for timestamps used
    with st.expander("🕒 View Milestones & Timestamps Used in Line Calculations", expanded=False):
        for idx, line in enumerate(audit_result.lines, 1):
            st.markdown(f"**Line {idx} ({line.type}):**")
            if line.timestamps_used:
                ts_pairs = [f"`{k}`: {v}" for k, v in line.timestamps_used.items() if v]
                st.markdown(" • " + ", ".join(ts_pairs))
            else:
                st.caption("No timeline milestones required for this charge.")

    # Documents Needed Checklist
    st.markdown("#### 📋 Documents Needed Before Final Approval")
    if audit_result.documents_needed:
        st.caption("Carrier documentation and clarifications required to release provisional holds:")
        for idx, doc_text in enumerate(audit_result.documents_needed):
            st.checkbox(f"{doc_text}", value=False, key=f"req_doc_{idx}")
    else:
        st.success("✅ All required documents and timestamps were verified! No outstanding items.")

    # MANDATORY SENTENCE PROMINENTLY DISPLAYED
    st.markdown(
        """
    <div class="broker-disclaimer">
        <strong style="color: #1e3a8a; font-size: 1.15rem; display: block; margin-bottom: 4px;">
            ⚠️ Final approval decision belongs to the broker.
        </strong>
        <span style="color: #1e40af; font-size: 0.92rem;">
            RateGuard AI provides mathematical calculations, contract matching, and evidence compilation.
            The final determination to approve, adjust, dispute, or pay any accessorial invoice remains strictly with the freight brokerage.
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Download Buttons Section
    st.markdown("#### 💾 Export & Download Audit Artifacts")
    col_d1, col_d2, col_d3 = st.columns(3)

    md_report_data = build_markdown_report(audit_result)
    json_report_data = json.dumps(audit_result.to_dict(), indent=2)
    csv_report_data = build_csv_report(audit_result)

    with col_d1:
        st.download_button(
            label="📄 Download report.md (Dispute Packet)",
            data=md_report_data,
            file_name="report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_d2:
        st.download_button(
            label="📊 Download result.json (Structured)",
            data=json_report_data,
            file_name="result.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_d3:
        st.download_button(
            label="📈 Download result.csv (Spreadsheet)",
            data=csv_report_data,
            file_name="result.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    # Empty State Guidance
    st.info(
        "👋 **Ready to audit!** Review the Rate Terms, Container Timeline, and Invoice items above, "
        "or click **⚡ Load Sample Data (Test Case 1)** at the top right to test the audit engine instantly."
    )
