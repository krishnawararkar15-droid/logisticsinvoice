"""Automated test suite for report generator in src/report.py.

Covers:
- Verification of report.md, result.json, and result.csv file generation.
- Verification of the mandatory broker disclaimer in report.md:
  "Final approval decision belongs to the broker."
- Verification of the documents checklist when proof is required.
- Verification of clean checklist state when all documents are provided.
- Verification of dual policy comparison table when policy is null.
- Verification of CSV formatting (headers, line items, totals row).
- Verification of JSON structure and field consistency.
"""

import csv
import json

import pytest

from src.report import (
    build_markdown_report,
    generate_report_files,
)
from src.rules import audit_invoice


@pytest.fixture
def sample_test_case_1_result():
    terms = {
        "linehaul_fsc": 1500,
        "prepull_fee": 150,
        "chassis_per_day": 45,
        "storage_per_day": 45,
        "detention_per_hour": 75,
        "detention_free_hours": 2,
        "chassis_day_policy": "calendar_day",
        "chassis_free_days": 0,
        "chassis_min_days": 2,
        "storage_free_days": 0,
        "prepull_includes_first_storage_day": None,
        "direct_move_hours_threshold": 24,
        "haul_type": "long",
    }
    timeline = {
        "terminal_pickup": "2026-06-23T21:00",
        "yard_in": None,
        "yard_out": None,
        "warehouse_appointment": "2026-06-24T08:00",
        "delivery_actual": "2026-06-24T08:00",
        "warehouse_in": None,
        "warehouse_out": None,
        "empty_return": "2026-06-24T16:00",
        "pod_provided": False,
        "prepull_request_documented": None,
    }
    invoice = {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1, "unit_rate": 1500, "amount": 1500},
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
            {"type": "chassis", "qty": 3, "unit_rate": 45, "amount": 135},
            {"type": "storage", "qty": 2, "unit_rate": 45, "amount": 90},
        ],
        "total": 1875,
    }
    return audit_invoice(invoice, terms, timeline)


def test_generate_report_files_creates_all_artifacts(tmp_path, sample_test_case_1_result):
    """Verify report generator generates report.md, result.json, and result.csv."""
    files = generate_report_files(sample_test_case_1_result, output_dir=tmp_path)

    assert "report_md" in files
    assert "result_json" in files
    assert "result_csv" in files

    md_path = files["report_md"]
    json_path = files["result_json"]
    csv_path = files["result_csv"]

    assert md_path.exists() and md_path.is_file()
    assert json_path.exists() and json_path.is_file()
    assert csv_path.exists() and csv_path.is_file()

    # Check non-empty content
    assert md_path.stat().st_size > 0
    assert json_path.stat().st_size > 0
    assert csv_path.stat().st_size > 0


def test_report_contains_mandatory_disclaimer(sample_test_case_1_result):
    """Verify report.md contains the mandatory disclaimer:
    'Final approval decision belongs to the broker.'
    """
    md_content = build_markdown_report(sample_test_case_1_result)
    assert "Final approval decision belongs to the broker." in md_content


def test_report_checklist_when_proof_is_needed(sample_test_case_1_result):
    """Verify checklist of documents needed is present when proof is needed."""
    md_content = build_markdown_report(sample_test_case_1_result)

    assert "## 4. Documents Needed Before Final Approval Checklist" in md_content
    # There are missing items in Test Case 1 (POD, yard timestamps, authorization, etc.)
    assert "- [ ]" in md_content
    assert "- [ ] Signed Proof of Delivery (POD)" in md_content
    assert any("Yard-in and yard-out timestamps" in doc for doc in sample_test_case_1_result.documents_needed)


def test_report_checklist_when_all_documents_provided():
    """Verify checklist reflects completion when no documentation is required."""
    terms = {
        "linehaul_fsc": 1500,
        "prepull_fee": 150,
        "chassis_per_day": 45,
        "storage_per_day": 45,
        "chassis_day_policy": "calendar_day",
        "storage_free_days": 0,
        "prepull_includes_first_storage_day": False,
    }
    timeline = {
        "terminal_pickup": "2026-06-23T21:00",
        "yard_in": "2026-06-23T22:00",
        "yard_out": "2026-06-24T06:00",
        "delivery_actual": "2026-06-24T08:00",
        "empty_return": "2026-06-24T16:00",
        "pod_provided": True,
        "prepull_request_documented": True,
    }
    invoice = {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1, "unit_rate": 1500, "amount": 1500},
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
        ],
        "total": 1650,
    }
    result = audit_invoice(invoice, terms, timeline)
    assert len(result.documents_needed) == 0

    md_content = build_markdown_report(result)
    assert "All required documents and timestamps were provided. No outstanding items." in md_content


def test_report_dual_policy_comparison_table():
    """Verify report.md includes the comparison table when policy is null."""
    terms = {
        "linehaul_fsc": 1500,
        "chassis_per_day": 45,
        "chassis_day_policy": None,
        "prepull_includes_first_storage_day": False,
    }
    timeline = {
        "terminal_pickup": "2026-06-23T21:00",
        "empty_return": "2026-06-24T16:00",
        "pod_provided": True,
    }
    invoice = {
        "lines": [
            {"type": "chassis", "qty": 3, "unit_rate": 45, "amount": 135},
        ],
        "total": 135,
    }
    result = audit_invoice(invoice, terms, timeline)
    assert result.alternative_policy_result is not None

    md_content = build_markdown_report(result)
    assert "Policy Comparison (Calendar Day vs 24-Hour Block)" in md_content
    assert "Calendar Day" in md_content
    assert "24-Hour Block" in md_content


def test_json_structure(tmp_path, sample_test_case_1_result):
    """Verify result.json contains valid JSON structure and correct financial totals."""
    files = generate_report_files(sample_test_case_1_result, output_dir=tmp_path)
    with open(files["result_json"], "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["policy_used"] == "calendar_day"
    assert "summary" in data
    assert data["summary"]["total_billed"] == 1875.0
    assert data["summary"]["approved_amount"] == 1590.0
    assert data["summary"]["disputed_amount"] == 240.0
    assert data["summary"]["needs_proof_amount"] == 45.0
    assert data["summary"]["not_approved_amount"] == 285.0
    assert data["summary"]["is_provisional"] is True
    assert len(data["lines"]) == 4


def test_csv_structure(tmp_path, sample_test_case_1_result):
    """Verify result.csv structure including headers, line rows, and totals."""
    files = generate_report_files(sample_test_case_1_result, output_dir=tmp_path)
    with open(files["result_csv"], "r", encoding="utf-8", newline="") as f:
        reader = list(csv.reader(f))

    # Header row
    header = reader[0]
    assert header == [
        "line_type",
        "billed_qty",
        "billed_unit_rate",
        "billed_amount",
        "agreed_rate",
        "approved_amount",
        "disputed_amount",
        "needs_proof_amount",
        "status",
        "flags",
        "reason",
        "missing_items",
    ]

    # Line item rows (4 lines)
    line_rows = reader[1:5]
    assert len(line_rows) == 4
    types = [row[0] for row in line_rows]
    assert types == ["linehaul_fsc", "prepull", "chassis", "storage"]

    # Totals row at the bottom
    totals_row = reader[-1]
    assert totals_row[0] == "TOTALS"
    assert float(totals_row[3]) == 1875.0  # total_billed
    assert float(totals_row[5]) == 1590.0  # approved_amount
    assert float(totals_row[6]) == 240.0   # disputed_amount
    assert float(totals_row[7]) == 45.0    # needs_proof_amount
