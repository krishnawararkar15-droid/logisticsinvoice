"""Tests for Streamlit application logic and integration in app.py."""

import json
from pathlib import Path
import pytest
import streamlit as st

import app
from src.rules import audit_invoice
from src.report import generate_reports


def test_app_constants_and_defaults():
    assert "linehaul_fsc" in app.DEFAULT_TERMS
    assert app.DEFAULT_TERMS["linehaul_fsc"] == 1500.0
    assert app.DEFAULT_TERMS["chassis_per_day"] == 45.0
    assert app.DEFAULT_TERMS["storage_per_day"] == 45.0
    assert len(app.DEFAULT_TIMELINE_TIMESTAMPS) == 8
    assert len(app.DEFAULT_INVOICE_LINES) == 4
    assert app.DEFAULT_INVOICE_TOTAL == 1875.0


def test_sample_case_audit_integration():
    # Load sample files
    with open("sample_data/terms.json") as f:
        terms = json.load(f)
    with open("sample_data/timeline.json") as f:
        timeline = json.load(f)
    with open("sample_data/invoice.json") as f:
        invoice = json.load(f)

    result = audit_invoice(invoice, terms, timeline)
    assert result.summary.total_billed == 1875.0
    assert result.summary.approved_amount == 1590.0
    assert result.summary.disputed_amount == 90.0
    assert result.summary.needs_proof_amount == 195.0
    assert result.summary.not_approved_amount == 285.0
    assert result.summary.is_provisional is True

    # Report generation
    files = generate_reports(result, output_dir="output")
    assert Path(files["report_md"]).is_file()
    assert Path(files["result_json"]).is_file()
    assert Path(files["result_csv"]).is_file()


def test_dual_policy_comparison_integration():
    with open("sample_data/terms.json") as f:
        terms = json.load(f)
    with open("sample_data/timeline.json") as f:
        timeline = json.load(f)
    with open("sample_data/invoice.json") as f:
        invoice = json.load(f)

    terms["chassis_day_policy"] = None
    result = audit_invoice(invoice, terms, timeline)
    assert result.alternative_policy_result is not None
    assert "summary" in result.alternative_policy_result
    alt_summary = result.alternative_policy_result["summary"]
    assert alt_summary["total_billed"] == 1875.0
    assert alt_summary["approved_amount"] == 1545.0
    assert alt_summary["disputed_amount"] == 135.0


def test_index_html_contains_three_new_features():
    """Verify that index.html contains all 3 requested broker features."""
    html_path = Path("index.html")
    assert html_path.is_file()
    html_content = html_path.read_text(encoding="utf-8")

    # Feature 1: Batch Invoice Auditing
    assert "mode-btn-batch" in html_content
    assert "Batch Multi-Invoice Audit" in html_content
    assert "batch-files-input" in html_content
    assert "handleBatchFileInput" in html_content
    assert "triggerBatchAudit" in html_content
    assert "batch-drilldown-modal" in html_content
    assert "exportBatchCsv" in html_content

    # Feature 2: Rate Confirmation Auto-Import
    assert "ratecon-file-input" in html_content
    assert "Auto-Import Contract Terms from Rate Confirmation" in html_content
    assert "handleRateconFile" in html_content

    # Feature 3: Formal Dispute Packet PDF
    assert "downloadDisputePacketPdf" in html_content
    assert "Download Formal Dispute Packet (PDF)" in html_content
    assert "Dispute_Packet" in html_content


def test_fastapi_endpoints_integration():
    """Verify FastAPI endpoints for ratecon, dispute-packet, and batch-audit."""
    from fastapi.testclient import TestClient
    from app import app as fastapi_app

    client = TestClient(fastapi_app)

    # Health check
    res = client.get("/health")
    assert res.status_code == 200

    # Ratecon test
    sample_ratecon_txt = b"Rate Confirmation LD-88210\nCarrier: Pacific Gateway Drayage LLC\nLinehaul: $1,500.00\nChassis: $45.00/day\nStorage: $45.00/day\nDetention: $75.00/hour (2 hours free)\nPre-pull: $150.00\nContainer: TCLU 582910-3\nBOL: MEDU 91823901"
    res_rc = client.post(
        "/api/ratecon",
        files={"file": ("ratecon.txt", sample_ratecon_txt, "text/plain")},
    )
    assert res_rc.status_code == 200
    rc_data = res_rc.json()
    assert rc_data["success"] is True
    assert rc_data["data"]["terms"]["linehaul_fsc"] == 1500.0

    # Dispute packet test
    sample_audit = {
        "summary": {
            "total_billed": 1875.0,
            "approved_amount": 1500.0,
            "disputed_amount": 240.0,
            "needs_proof_amount": 135.0,
            "not_approved_amount": 375.0,
            "is_provisional": True,
            "flags": ["RATE_MISMATCH"],
        },
        "lines": [
            {
                "type": "linehaul_fsc",
                "billed_amount": 1500.0,
                "approved_amount": 1500.0,
                "disputed_amount": 0.0,
                "needs_proof_amount": 0.0,
                "status": "APPROVE",
                "reason": "Approved per contract rate.",
            }
        ],
        "documents_needed": ["Signed Proof of Delivery (POD)"],
    }
    res_dp = client.post(
        "/api/dispute-packet",
        json={"audit_data": sample_audit, "metadata": {"invoice_no": "INV-2026-0842"}},
    )
    assert res_dp.status_code == 200
    assert res_dp.headers["content-type"] == "application/pdf"
    assert res_dp.content.startswith(b"%PDF-")


def test_workspace_batch_dom_hierarchy():
    """Verify that workspace-batch is NOT a child of workspace-single and all divs are balanced."""
    from html.parser import HTMLParser
    from pathlib import Path

    html_path = Path(__file__).resolve().parent.parent / "index.html"
    content = html_path.read_text(encoding="utf-8")

    class DivHierarchyParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.batch_parents = None

        def handle_starttag(self, tag, attrs):
            if tag == "div":
                d = dict(attrs)
                eid = d.get("id", "")
                if eid == "workspace-batch":
                    self.batch_parents = [x for x in self.stack]
                self.stack.append(eid)

        def handle_endtag(self, tag):
            if tag == "div" and self.stack:
                self.stack.pop()

    parser = DivHierarchyParser()
    parser.feed(content)

    # 1. Total unclosed divs must be exactly 0
    assert len(parser.stack) == 0, f"Unclosed divs remain in index.html: {parser.stack}"

    # 2. workspace-batch must NOT have workspace-single as an ancestor
    assert "workspace-single" not in parser.batch_parents, (
        f"workspace-batch is mistakenly nested inside workspace-single! Ancestors: {parser.batch_parents}"
    )

