"""Accessorial Invoice Checker (v1) - Web Application & API Entrypoint.

Deterministic auditing and dispute package generation for freight brokers.
Compatible with Vercel Serverless Functions (FastAPI ASGI) and local uvicorn.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

from src.ocr import parse_invoice_text, process_invoice
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

# Initialize FastAPI application (Vercel entrypoints: app, application, handler)
app = FastAPI(
    title="Accessorial Invoice Checker",
    description="Deterministic Drayage & Intermodal Accessorial Invoice Audit Engine",
    version="1.0.0",
)
application = app
handler = app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default Sample Data definitions (Test Case 1)
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


class AuditPayload(BaseModel):
    terms: Dict[str, Any]
    timeline: Dict[str, Any]
    invoice: Dict[str, Any]


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Accessorial Invoice Checker v1"}


@app.post("/api/audit")
def run_audit(payload: AuditPayload):
    try:
        # Normalize terms
        terms = dict(payload.terms)
        if terms.get("chassis_day_policy") == "unknown":
            terms["chassis_day_policy"] = None
        if terms.get("prepull_includes_first_storage_day") == "unknown":
            terms["prepull_includes_first_storage_day"] = None
        elif terms.get("prepull_includes_first_storage_day") in ("yes", True):
            terms["prepull_includes_first_storage_day"] = True
        elif terms.get("prepull_includes_first_storage_day") in ("no", False):
            terms["prepull_includes_first_storage_day"] = False

        # Normalize timeline
        timeline = dict(payload.timeline)
        if timeline.get("prepull_request_documented") == "unknown":
            timeline["prepull_request_documented"] = None
        elif timeline.get("prepull_request_documented") in ("yes", True):
            timeline["prepull_request_documented"] = True
        elif timeline.get("prepull_request_documented") in ("no", False):
            timeline["prepull_request_documented"] = False

        # Run core audit
        result: AuditResult = audit_invoice(payload.invoice, terms, timeline)

        # Build markdown and csv
        md_content = build_markdown_report(result)
        csv_content = build_csv_report(result)

        return {
            "success": True,
            "data": result.to_dict(),
            "markdown": md_content,
            "csv": csv_content,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ocr")
async def extract_ocr(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        parsed = process_invoice(file_bytes, filename=file.filename)
        return {"success": True, "data": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Extraction failed: {str(e)}")


@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTML_CONTENT


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accessorial Invoice Checker (v1)</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #1e40af;
      --primary-hover: #1d4ed8;
      --success: #16a34a;
      --success-bg: #f0fdf4;
      --danger: #dc2626;
      --danger-bg: #fef2f2;
      --warning: #d97706;
      --warning-bg: #fffbeb;
      --slate-50: #f8fafc;
      --slate-100: #f1f5f9;
      --slate-200: #e2e8f0;
      --slate-600: #475569;
      --slate-700: #334155;
      --slate-800: #1e293b;
      --slate-900: #0f172a;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #f8fafc;
      color: var(--slate-900);
      line-height: 1.5;
      padding-bottom: 60px;
    }
    .header {
      background: white;
      border-bottom: 1px solid var(--slate-200);
      padding: 24px 32px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .header-inner {
      max-width: 1300px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }
    .logo-group h1 {
      font-size: 1.45rem;
      font-weight: 800;
      color: var(--slate-900);
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-group p {
      color: var(--slate-600);
      font-size: 0.88rem;
      margin-top: 3px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      font-size: 0.85rem;
      padding: 9px 16px;
      border-radius: 8px;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      text-decoration: none;
    }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: white; border-color: var(--slate-200); color: var(--slate-700); }
    .btn-secondary:hover { background: var(--slate-100); }
    .btn-lg { font-size: 1rem; padding: 13px 28px; border-radius: 10px; }
    .btn-success { background: var(--success); color: white; }
    .btn-warning { background: var(--warning); color: white; }

    .container {
      max-width: 1300px;
      margin: 28px auto;
      padding: 0 24px;
    }

    .tabs {
      display: flex;
      gap: 8px;
      border-bottom: 2px solid var(--slate-200);
      margin-bottom: 24px;
    }
    .tab-btn {
      padding: 10px 18px;
      font-weight: 600;
      font-size: 0.92rem;
      border: none;
      background: none;
      color: var(--slate-600);
      cursor: pointer;
      position: relative;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
    }
    .tab-btn.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }

    .card {
      background: white;
      border: 1px solid var(--slate-200);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      margin-bottom: 24px;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--slate-900);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
    @media(max-width: 900px) {
      .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
    }

    .form-group { margin-bottom: 14px; }
    .form-label {
      display: block;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--slate-700);
      margin-bottom: 5px;
    }
    .form-sublabel { font-size: 0.75rem; color: var(--slate-600); margin-bottom: 4px; display: block; }
    .form-control {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--slate-200);
      border-radius: 7px;
      font-size: 0.88rem;
      background: white;
      color: var(--slate-900);
      outline: none;
      font-family: inherit;
    }
    .form-control:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(30,64,175,0.1); }
    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 7px;
      font-size: 0.8rem;
      color: var(--slate-600);
      margin-top: 5px;
      cursor: pointer;
    }

    /* Metric Cards */
    .metrics-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .metric-card {
      background: white;
      border: 1px solid var(--slate-200);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      position: relative;
    }
    .metric-title {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--slate-600);
      margin-bottom: 6px;
    }
    .metric-value {
      font-size: 1.7rem;
      font-weight: 800;
      color: var(--slate-900);
    }
    .metric-sub {
      font-size: 0.78rem;
      margin-top: 4px;
      color: var(--slate-600);
    }
    .metric-card.approved .metric-value { color: var(--success); }
    .metric-card.disputed { border-left: 4px solid var(--danger); }
    .metric-card.disputed .metric-value { color: var(--danger); }
    .metric-card.needs-proof { border-left: 4px solid var(--warning); }
    .metric-card.needs-proof .metric-value { color: var(--warning); }
    .metric-card.not-approved .metric-value { color: #b91c1c; }

    /* Badges */
    .badge {
      display: inline-block;
      padding: 4px 10px;
      font-size: 0.78rem;
      font-weight: 700;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .badge-approve { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .badge-dispute { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .badge-proof { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .badge-flag { background: #ffedd5; color: #c2410c; border: 1px solid #fdba74; font-size: 0.72rem; padding: 2px 7px; border-radius: 4px; margin-right: 4px; }
    .badge-provisional { background: #e0e7ff; color: #4338ca; border: 1px solid #c7d2fe; font-size: 0.68rem; margin-left: 6px; }

    /* Tables */
    .table-responsive { width: 100%; overflow-x: auto; }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }
    .data-table th {
      background: var(--slate-50);
      color: var(--slate-600);
      font-weight: 700;
      text-align: left;
      padding: 12px 14px;
      border-bottom: 2px solid var(--slate-200);
      white-space: nowrap;
    }
    .data-table td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--slate-200);
      vertical-align: top;
    }
    .data-table tr:hover { background: #fbfcfe; }

    .disclaimer-box {
      background: #eff6ff;
      border-left: 5px solid #2563eb;
      padding: 16px 20px;
      border-radius: 8px;
      margin: 24px 0 16px 0;
      color: #1e3a8a;
      font-weight: 600;
      font-size: 0.95rem;
    }

    .checklist-card {
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .checklist-title {
      font-size: 0.98rem;
      font-weight: 700;
      color: #92400e;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .checklist-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 0.88rem;
      color: #78350f;
    }

    .dropzone {
      border: 2px dashed var(--slate-200);
      border-radius: 10px;
      padding: 30px;
      text-align: center;
      background: var(--slate-50);
      cursor: pointer;
      transition: all 0.15s;
    }
    .dropzone:hover { border-color: var(--primary); background: #f0f4ff; }
  </style>
</head>
<body>

  <header class="header">
    <div class="header-inner">
      <div class="logo-group">
        <h1>🚚 Accessorial Invoice Checker</h1>
        <p>Deterministic Drayage & Intermodal Audit Engine — No AI APIs, 100% Explainable Date Math</p>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-primary" onclick="loadSampleData()">⚡ Load Sample Data (Test Case 1)</button>
        <button class="btn btn-secondary" onclick="resetForm()">🔄 Reset</button>
      </div>
    </div>
  </header>

  <main class="container">

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('terms', this)">📋 1. Rate Terms</button>
      <button class="tab-btn" onclick="switchTab('timeline', this)">⏱️ 2. Container Timeline</button>
      <button class="tab-btn" onclick="switchTab('invoice', this)">🧾 3. Invoice & OCR</button>
    </div>

    <!-- TAB 1: RATE TERMS -->
    <div id="tab-terms" class="tab-content card">
      <h2 class="card-title">Agreed Contract Rate Terms</h2>
      <div class="grid-3">
        <div class="form-group">
          <label class="form-label">Linehaul + FSC ($)</label>
          <input type="number" id="linehaul_fsc" class="form-control" value="1500" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Pre-pull Fee ($)</label>
          <input type="number" id="prepull_fee" class="form-control" value="150" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Chassis Daily Rate ($/day)</label>
          <input type="number" id="chassis_per_day" class="form-control" value="45" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Storage Daily Rate ($/day)</label>
          <input type="number" id="storage_per_day" class="form-control" value="45" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Detention Hourly Rate ($/hr)</label>
          <input type="number" id="detention_per_hour" class="form-control" value="75" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Detention Free Hours</label>
          <input type="number" id="detention_free_hours" class="form-control" value="2" step="0.5">
        </div>
      </div>

      <div class="grid-3" style="margin-top: 10px;">
        <div class="form-group">
          <label class="form-label">Chassis Day Policy</label>
          <select id="chassis_day_policy" class="form-control">
            <option value="calendar_day" selected>Calendar Day (Empty Return - Pickup + 1)</option>
            <option value="24h_block">24-Hour Block (ceil(hours / 24))</option>
            <option value="unknown">Unknown / Null (Calculate BOTH side-by-side)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Chassis Free Days</label>
          <input type="number" id="chassis_free_days" class="form-control" value="0">
        </div>
        <div class="form-group">
          <label class="form-label">Chassis Minimum Days</label>
          <input type="number" id="chassis_min_days" class="form-control" value="0">
        </div>
        <div class="form-group">
          <label class="form-label">Storage Free Days</label>
          <input type="number" id="storage_free_days" class="form-control" value="0">
        </div>
        <div class="form-group">
          <label class="form-label">Pre-pull Includes 1st Storage Day?</label>
          <select id="prepull_includes_first_storage_day" class="form-control">
            <option value="unknown" selected>Unknown / Null (Prompt broker)</option>
            <option value="yes">Yes (1st yard day covered in prepull)</option>
            <option value="no">No (Storage billed separately)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Direct Move Threshold (Hours)</label>
          <input type="number" id="direct_move_hours_threshold" class="form-control" value="24">
        </div>
      </div>
    </div>

    <!-- TAB 2: CONTAINER TIMELINE -->
    <div id="tab-timeline" class="tab-content card" style="display:none;">
      <h2 class="card-title">Container Milestone Timestamps</h2>
      <p style="font-size: 0.85rem; color: var(--slate-600); margin-bottom: 18px;">
        Enter dates as <code>YYYY-MM-DDTHH:MM</code> or check "Unknown / Null" if timestamp is missing from records.
      </p>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">1. Terminal Pickup (Port / Rail Out-Gate)</label>
          <input type="text" id="terminal_pickup" class="form-control" value="2026-06-23T21:00">
          <label class="checkbox-label"><input type="checkbox" id="null_terminal_pickup" onchange="toggleNull('terminal_pickup')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">2. Carrier Yard In-Gate</label>
          <input type="text" id="yard_in" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_yard_in" checked onchange="toggleNull('yard_in')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">3. Carrier Yard Out-Gate</label>
          <input type="text" id="yard_out" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_yard_out" checked onchange="toggleNull('yard_out')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">4. Warehouse Appointment Schedule</label>
          <input type="text" id="warehouse_appointment" class="form-control" value="2026-06-24T08:00">
          <label class="checkbox-label"><input type="checkbox" id="null_warehouse_appointment" onchange="toggleNull('warehouse_appointment')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">5. Actual Delivery Date / Drop</label>
          <input type="text" id="delivery_actual" class="form-control" value="2026-06-24T08:00">
          <label class="checkbox-label"><input type="checkbox" id="null_delivery_actual" onchange="toggleNull('delivery_actual')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">6. Warehouse In-Gate (Driver Check-in)</label>
          <input type="text" id="warehouse_in" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_warehouse_in" checked onchange="toggleNull('warehouse_in')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">7. Warehouse Out-Gate (Driver Check-out)</label>
          <input type="text" id="warehouse_out" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_warehouse_out" checked onchange="toggleNull('warehouse_out')"> Unknown / Null</label>
        </div>

        <div class="form-group">
          <label class="form-label">8. Empty Container Return</label>
          <input type="text" id="empty_return" class="form-control" value="2026-06-24T16:00">
          <label class="checkbox-label"><input type="checkbox" id="null_empty_return" onchange="toggleNull('empty_return')"> Unknown / Null</label>
        </div>
      </div>

      <div class="grid-2" style="margin-top: 14px; border-top: 1px solid var(--slate-200); padding-top: 14px;">
        <div class="form-group">
          <label class="form-label">Signed Proof of Delivery (POD)</label>
          <label class="checkbox-label" style="font-size: 0.9rem;">
            <input type="checkbox" id="pod_provided"> Signed POD Provided & Verified
          </label>
        </div>
        <div class="form-group">
          <label class="form-label">Pre-pull Written Request Documented?</label>
          <select id="prepull_request_documented" class="form-control">
            <option value="unknown" selected>Unknown / Not Documented</option>
            <option value="yes">Yes (Documented email / EDI dispatch request)</option>
            <option value="no">No (Carrier pulled at their own convenience)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- TAB 3: INVOICE & OCR -->
    <div id="tab-invoice" class="tab-content card" style="display:none;">
      <h2 class="card-title">Carrier Invoice Lines & Free OCR Extraction</h2>

      <!-- OCR File Upload -->
      <div style="margin-bottom: 20px;">
        <div class="dropzone" onclick="document.getElementById('ocr-file').click()">
          <p style="font-weight: 700; color: var(--primary); font-size: 1rem;">📄 Click to Upload Invoice (PDF or Image) for Free OCR</p>
          <p style="font-size: 0.8rem; color: var(--slate-600); margin-top: 4px;">Free OCR.space API (Key: K81108510188957) + Local PDFPlumber Engine</p>
          <input type="file" id="ocr-file" style="display:none" accept=".pdf,.png,.jpg,.jpeg" onchange="uploadInvoiceOcr(this)">
        </div>
        <div id="ocr-status" style="margin-top: 8px; font-size: 0.85rem; font-weight: 600; display: none;"></div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--slate-700);">Billed Line Items</h3>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary" onclick="addInvoiceLine()">+ Add Line</button>
          <button class="btn btn-secondary" onclick="autoSumLines()">Calculate Total</button>
        </div>
      </div>

      <div class="table-responsive">
        <table class="data-table" id="invoice-lines-table">
          <thead>
            <tr>
              <th>Charge Type</th>
              <th style="width: 120px;">Qty</th>
              <th style="width: 140px;">Unit Rate ($)</th>
              <th style="width: 150px;">Amount ($)</th>
              <th style="width: 60px;">Action</th>
            </tr>
          </thead>
          <tbody id="invoice-lines-body">
            <!-- Dynamically populated -->
          </tbody>
        </table>
      </div>

      <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px; margin-top: 16px;">
        <label class="form-label" style="margin: 0; font-size: 1rem;">Invoice Total Billed ($):</label>
        <input type="number" id="invoice_total" class="form-control" style="width: 180px; font-weight: 700; font-size: 1rem;" value="1875" step="0.01">
      </div>
    </div>

    <!-- AUDIT ACTION BUTTON -->
    <div style="text-align: center; margin: 30px 0;">
      <button class="btn btn-primary btn-lg" onclick="triggerAudit()" style="box-shadow: 0 4px 14px rgba(30,64,175,0.3);">
        🚀 Check Invoice & Audit Discrepancies
      </button>
    </div>

    <!-- RESULTS SECTION -->
    <div id="audit-results" style="display: none;">

      <!-- Metrics -->
      <div class="metrics-container" id="metrics-cards">
        <!-- Injected via JS -->
      </div>

      <!-- Side-by-side policy alert (if applicable) -->
      <div id="dual-policy-alert" style="display: none; margin-bottom: 20px;"></div>

      <!-- Line by line table -->
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
          <h2 class="card-title" style="margin: 0;">Line-by-Line Audit Findings</h2>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary" onclick="downloadReport('md')">📄 Download report.md</button>
            <button class="btn btn-secondary" onclick="downloadReport('json')">📊 Download result.json</button>
            <button class="btn btn-secondary" onclick="downloadReport('csv')">📈 Download result.csv</button>
          </div>
        </div>

        <div class="table-responsive">
          <table class="data-table" id="audit-results-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Billed</th>
                <th>Approved</th>
                <th>Disputed</th>
                <th>Needs Proof</th>
                <th>Status</th>
                <th>Flags</th>
                <th>Plain English Audit Evidence & Math</th>
              </tr>
            </thead>
            <tbody id="audit-results-body">
              <!-- Injected via JS -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- Checklist -->
      <div class="checklist-card" id="checklist-container">
        <div class="checklist-title">📋 Documents Needed Before Final Approval</div>
        <div id="checklist-items"></div>
      </div>

      <!-- Mandatory Disclaimer -->
      <div class="disclaimer-box">
        ⚖️ Final approval decision belongs to the broker. The approved amount is PROVISIONAL whenever documentation is pending or contractual terms require confirmation.
      </div>

    </div>

  </main>

  <script>
    let currentAuditData = null;

    const sampleInvoiceLines = [
      { type: "linehaul_fsc", qty: 1, unit_rate: 1500, amount: 1500 },
      { type: "prepull", qty: 1, unit_rate: 150, amount: 150 },
      { type: "chassis", qty: 3, unit_rate: 45, amount: 135 },
      { type: "storage", qty: 2, unit_rate: 45, amount: 90 }
    ];

    function switchTab(tabId, el) {
      document.querySelectorAll('.tab-content').forEach(d => d.style.display = 'none');
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + tabId).style.display = 'block';
      el.classList.add('active');
    }

    function toggleNull(fieldId) {
      const checkbox = document.getElementById('null_' + fieldId);
      const input = document.getElementById(fieldId);
      if (checkbox.checked) {
        input.disabled = true;
        input.dataset.oldVal = input.value;
        input.value = "";
        input.placeholder = "Null / Not Provided";
      } else {
        input.disabled = false;
        input.value = input.dataset.oldVal || "2026-06-24T08:00";
        input.placeholder = "YYYY-MM-DDTHH:MM";
      }
    }

    function renderInvoiceLines(lines) {
      const tbody = document.getElementById('invoice-lines-body');
      tbody.innerHTML = '';
      lines.forEach((line, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>
            <select class="form-control line-type">
              <option value="linehaul_fsc" ${line.type === 'linehaul_fsc' ? 'selected' : ''}>Linehaul + FSC</option>
              <option value="chassis" ${line.type === 'chassis' ? 'selected' : ''}>Chassis</option>
              <option value="storage" ${line.type === 'storage' ? 'selected' : ''}>Yard Storage</option>
              <option value="prepull" ${line.type === 'prepull' ? 'selected' : ''}>Pre-pull</option>
              <option value="detention" ${line.type === 'detention' ? 'selected' : ''}>Detention</option>
              <option value="other" ${!['linehaul_fsc','chassis','storage','prepull','detention'].includes(line.type) ? 'selected' : ''}>Other / Unknown</option>
            </select>
          </td>
          <td><input type="number" class="form-control line-qty" value="${line.qty}" step="0.5" oninput="updateLineAmount(${index})"></td>
          <td><input type="number" class="form-control line-rate" value="${line.unit_rate}" step="0.01" oninput="updateLineAmount(${index})"></td>
          <td><input type="number" class="form-control line-amount" value="${line.amount}" step="0.01"></td>
          <td><button class="btn btn-secondary" style="color:var(--danger); padding:6px 10px;" onclick="removeInvoiceLine(${index})">✕</button></td>
        `;
        tbody.appendChild(tr);
      });
    }

    function updateLineAmount(index) {
      const rows = document.querySelectorAll('#invoice-lines-body tr');
      if (rows[index]) {
        const qty = parseFloat(rows[index].querySelector('.line-qty').value) || 0;
        const rate = parseFloat(rows[index].querySelector('.line-rate').value) || 0;
        rows[index].querySelector('.line-amount').value = (qty * rate).toFixed(2);
      }
    }

    function autoSumLines() {
      const rows = document.querySelectorAll('#invoice-lines-body tr');
      let sum = 0;
      rows.forEach(r => {
        sum += parseFloat(r.querySelector('.line-amount').value) || 0;
      });
      document.getElementById('invoice_total').value = sum.toFixed(2);
    }

    function addInvoiceLine() {
      const lines = getInvoiceLines();
      lines.push({ type: "chassis", qty: 1, unit_rate: 45, amount: 45 });
      renderInvoiceLines(lines);
      autoSumLines();
    }

    function removeInvoiceLine(index) {
      const lines = getInvoiceLines();
      lines.splice(index, 1);
      renderInvoiceLines(lines);
      autoSumLines();
    }

    function getInvoiceLines() {
      const rows = document.querySelectorAll('#invoice-lines-body tr');
      const lines = [];
      rows.forEach(r => {
        lines.push({
          type: r.querySelector('.line-type').value,
          qty: parseFloat(r.querySelector('.line-qty').value) || 0,
          unit_rate: parseFloat(r.querySelector('.line-rate').value) || 0,
          amount: parseFloat(r.querySelector('.line-amount').value) || 0
        });
      });
      return lines;
    }

    function loadSampleData() {
      // Terms
      document.getElementById('linehaul_fsc').value = 1500;
      document.getElementById('prepull_fee').value = 150;
      document.getElementById('chassis_per_day').value = 45;
      document.getElementById('storage_per_day').value = 45;
      document.getElementById('detention_per_hour').value = 75;
      document.getElementById('detention_free_hours').value = 2;
      document.getElementById('chassis_day_policy').value = "calendar_day";
      document.getElementById('chassis_free_days').value = 0;
      document.getElementById('chassis_min_days').value = 0;
      document.getElementById('storage_free_days').value = 0;
      document.getElementById('prepull_includes_first_storage_day').value = "unknown";
      document.getElementById('direct_move_hours_threshold').value = 24;

      // Timeline
      setTimestamp('terminal_pickup', '2026-06-23T21:00', false);
      setTimestamp('yard_in', '', true);
      setTimestamp('yard_out', '', true);
      setTimestamp('warehouse_appointment', '2026-06-24T08:00', false);
      setTimestamp('delivery_actual', '2026-06-24T08:00', false);
      setTimestamp('warehouse_in', '', true);
      setTimestamp('warehouse_out', '', true);
      setTimestamp('empty_return', '2026-06-24T16:00', false);

      document.getElementById('pod_provided').checked = false;
      document.getElementById('prepull_request_documented').value = "unknown";

      // Invoice
      renderInvoiceLines(sampleInvoiceLines);
      document.getElementById('invoice_total').value = 1875;

      alert("Sample Data (Test Case 1) loaded successfully! Click 'Check Invoice' to audit.");
    }

    function setTimestamp(id, val, isNull) {
      const chk = document.getElementById('null_' + id);
      const inp = document.getElementById(id);
      chk.checked = isNull;
      if (isNull) {
        inp.disabled = true;
        inp.value = "";
      } else {
        inp.disabled = false;
        inp.value = val;
      }
    }

    function resetForm() {
      if (confirm("Reset all form fields to blank?")) {
        document.querySelectorAll('input[type="number"]').forEach(i => i.value = "0");
        document.querySelectorAll('input[type="checkbox"]').forEach(c => c.checked = true);
        document.querySelectorAll('input[type="text"]').forEach(t => { t.value = ""; t.disabled = true; });
        renderInvoiceLines([]);
        document.getElementById('invoice_total').value = "0";
        document.getElementById('audit-results').style.display = 'none';
      }
    }

    async function uploadInvoiceOcr(input) {
      const file = input.files[0];
      if (!file) return;

      const status = document.getElementById('ocr-status');
      status.style.display = 'block';
      status.style.color = 'var(--primary)';
      status.innerText = "⏳ Uploading and extracting invoice via Free OCR API...";

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/ocr', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.success && data.data) {
          status.style.color = 'var(--success)';
          status.innerText = `✅ OCR Extraction Succeeded! Parsed ${data.data.lines.length} lines.`;
          renderInvoiceLines(data.data.lines);
          if (data.data.total) {
            document.getElementById('invoice_total').value = data.data.total;
          }
        } else {
          status.style.color = 'var(--danger)';
          status.innerText = "❌ OCR Extraction failed: " + (data.detail || "Unknown error");
        }
      } catch (err) {
        status.style.color = 'var(--danger)';
        status.innerText = "❌ Network error connecting to OCR API: " + err.message;
      }
    }

    async function triggerAudit() {
      // Build Terms
      const terms = {
        linehaul_fsc: parseFloat(document.getElementById('linehaul_fsc').value) || 0,
        prepull_fee: parseFloat(document.getElementById('prepull_fee').value) || 0,
        chassis_per_day: parseFloat(document.getElementById('chassis_per_day').value) || 0,
        storage_per_day: parseFloat(document.getElementById('storage_per_day').value) || 0,
        detention_per_hour: parseFloat(document.getElementById('detention_per_hour').value) || 0,
        detention_free_hours: parseFloat(document.getElementById('detention_free_hours').value) || 0,
        chassis_day_policy: document.getElementById('chassis_day_policy').value,
        chassis_free_days: parseInt(document.getElementById('chassis_free_days').value) || 0,
        chassis_min_days: parseInt(document.getElementById('chassis_min_days').value) || 0,
        storage_free_days: parseInt(document.getElementById('storage_free_days').value) || 0,
        prepull_includes_first_storage_day: document.getElementById('prepull_includes_first_storage_day').value,
        direct_move_hours_threshold: parseFloat(document.getElementById('direct_move_hours_threshold').value) || 24
      };

      // Build Timeline
      const getTs = id => document.getElementById('null_' + id).checked ? null : (document.getElementById(id).value.trim() || null);
      const timeline = {
        terminal_pickup: getTs('terminal_pickup'),
        yard_in: getTs('yard_in'),
        yard_out: getTs('yard_out'),
        warehouse_appointment: getTs('warehouse_appointment'),
        delivery_actual: getTs('delivery_actual'),
        warehouse_in: getTs('warehouse_in'),
        warehouse_out: getTs('warehouse_out'),
        empty_return: getTs('empty_return'),
        pod_provided: document.getElementById('pod_provided').checked,
        prepull_request_documented: document.getElementById('prepull_request_documented').value
      };

      // Build Invoice
      const invoice = {
        lines: getInvoiceLines(),
        total: parseFloat(document.getElementById('invoice_total').value) || 0
      };

      try {
        const res = await fetch('/api/audit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ terms, timeline, invoice })
        });
        const resData = await res.json();
        if (!resData.success) {
          alert("Audit error: " + (resData.detail || "Unknown error"));
          return;
        }

        currentAuditData = resData;
        displayAuditResults(resData.data);
      } catch (err) {
        alert("Network error running audit: " + err.message);
      }
    }

    function displayAuditResults(result) {
      document.getElementById('audit-results').style.display = 'block';
      const summary = result.summary;

      // Render Metric Cards
      const provTag = summary.is_provisional ? '<span class="badge badge-provisional">PROVISIONAL</span>' : '';
      document.getElementById('metrics-cards').innerHTML = `
        <div class="metric-card">
          <div class="metric-title">Total Billed</div>
          <div class="metric-value">$${summary.total_billed.toFixed(2)}</div>
          <div class="metric-sub">Invoice amount</div>
        </div>
        <div class="metric-card approved">
          <div class="metric-title">Approved ${provTag}</div>
          <div class="metric-value">$${summary.approved_amount.toFixed(2)}</div>
          <div class="metric-sub">${summary.is_provisional ? 'Pending documents' : 'Final supported'}</div>
        </div>
        <div class="metric-card disputed">
          <div class="metric-title">Disputed</div>
          <div class="metric-value">$${summary.disputed_amount.toFixed(2)}</div>
          <div class="metric-sub">Direct overcharge</div>
        </div>
        <div class="metric-card needs-proof">
          <div class="metric-title">Needs Proof</div>
          <div class="metric-value">$${summary.needs_proof_amount.toFixed(2)}</div>
          <div class="metric-sub">Held pending proof</div>
        </div>
        <div class="metric-card not-approved">
          <div class="metric-title">Total Not Approved</div>
          <div class="metric-value">$${summary.not_approved_amount.toFixed(2)}</div>
          <div class="metric-sub">Disputed + Needs proof</div>
        </div>
      `;

      // Dual policy alert if alternative is present
      const dualAlert = document.getElementById('dual-policy-alert');
      if (result.alternative_policy_result) {
        const alt = result.alternative_policy_result.summary;
        dualAlert.style.display = 'block';
        dualAlert.innerHTML = `
          <div class="card" style="background:#f8fafc; border:1px solid #cbd5e1; padding:18px;">
            <h3 style="font-size:0.95rem; font-weight:700; color:var(--primary); margin-bottom:8px;">
              ⚖️ Side-by-Side Policy Comparison (Chassis Day Policy Unknown)
            </h3>
            <p style="font-size:0.85rem; color:var(--slate-600); margin-bottom:12px;">
              Contract policy was null. Both policies evaluated side-by-side:
            </p>
            <div class="grid-2">
              <div style="background:white; border:1px solid var(--slate-200); padding:14px; border-radius:8px;">
                <div style="font-weight:700; color:var(--slate-700);">Calendar Day Policy</div>
                <div style="font-size:1.1rem; font-weight:800; color:var(--success); margin:4px 0;">Approved: $${summary.approved_amount.toFixed(2)}</div>
                <div style="font-size:0.82rem; color:var(--danger);">Disputed: $${summary.disputed_amount.toFixed(2)} | Not Approved: $${summary.not_approved_amount.toFixed(2)}</div>
              </div>
              <div style="background:white; border:1px solid var(--slate-200); padding:14px; border-radius:8px;">
                <div style="font-weight:700; color:var(--slate-700);">24-Hour Block Policy</div>
                <div style="font-size:1.1rem; font-weight:800; color:var(--success); margin:4px 0;">Approved: $${alt.approved_amount.toFixed(2)}</div>
                <div style="font-size:0.82rem; color:var(--danger);">Disputed: $${alt.disputed_amount.toFixed(2)} | Not Approved: $${alt.not_approved_amount.toFixed(2)}</div>
              </div>
            </div>
          </div>
        `;
      } else {
        dualAlert.style.display = 'none';
      }

      // Render Line Items Table
      const tbody = document.getElementById('audit-results-body');
      tbody.innerHTML = '';
      result.lines.forEach(l => {
        let statusBadge = '';
        if (l.status === 'APPROVE') statusBadge = '<span class="badge badge-approve">APPROVE</span>';
        else if (l.status === 'DISPUTE') statusBadge = '<span class="badge badge-dispute">DISPUTE</span>';
        else if (l.status === 'REQUIRE_PROOF') statusBadge = '<span class="badge badge-proof">REQUIRE_PROOF</span>';
        else statusBadge = `<span class="badge">${l.status}</span>`;

        const flagsHtml = l.flags.map(f => `<span class="badge-flag">${f}</span>`).join('');

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="font-weight:700; text-transform:capitalize;">${l.type.replace('_', ' ')}</td>
          <td>$${l.billed_amount.toFixed(2)}</td>
          <td style="color:var(--success); font-weight:600;">$${l.approved_amount.toFixed(2)}</td>
          <td style="color:var(--danger); font-weight:600;">$${l.disputed_amount.toFixed(2)}</td>
          <td style="color:var(--warning); font-weight:600;">$${l.needs_proof_amount.toFixed(2)}</td>
          <td>${statusBadge}</td>
          <td>${flagsHtml || '<span style="color:var(--slate-600); font-size:0.8rem;">None</span>'}</td>
          <td style="font-size:0.85rem; color:var(--slate-700);">${l.reason}</td>
        `;
        tbody.appendChild(tr);
      });

      // Checklist
      const checklistItems = document.getElementById('checklist-items');
      const allMissing = [];
      result.lines.forEach(l => {
        l.missing_items.forEach(m => {
          if (!allMissing.includes(m)) allMissing.push(m);
        });
      });

      if (allMissing.length > 0) {
        document.getElementById('checklist-container').style.display = 'block';
        checklistItems.innerHTML = allMissing.map(item => `
          <div class="checklist-item">
            <input type="checkbox" style="margin-top:3px;">
            <span>${item}</span>
          </div>
        `).join('');
      } else {
        document.getElementById('checklist-container').style.display = 'none';
      }

      // Smooth scroll to results
      document.getElementById('audit-results').scrollIntoView({ behavior: 'smooth' });
    }

    function downloadReport(format) {
      if (!currentAuditData) return;
      let content = "";
      let filename = "";
      let mimeType = "text/plain";

      if (format === 'md') {
        content = currentAuditData.markdown;
        filename = "report.md";
        mimeType = "text/markdown";
      } else if (format === 'json') {
        content = JSON.stringify(currentAuditData.data, null, 2);
        filename = "result.json";
        mimeType = "application/json";
      } else if (format === 'csv') {
        content = currentAuditData.csv;
        filename = "result.csv";
        mimeType = "text/csv";
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    // Initialize with sample lines
    renderInvoiceLines(sampleInvoiceLines);
  </script>
</body>
</html>
"""
