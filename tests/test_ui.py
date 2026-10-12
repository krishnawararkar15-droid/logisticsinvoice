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
