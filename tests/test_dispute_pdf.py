"""Unit test suite for Dispute PDF generator (src/dispute_pdf.py).

Covers:
- generate_dispute_packet_pdf returns valid PDF bytes starting with b"%PDF-".
- Verification of the mandatory broker disclaimer:
  "Final approval decision belongs to the broker. This document represents a formal debit memo / audit statement under UIIA and broker-carrier contract terms."
- Verification of Header, Carrier/Shipment Info Box, Financial Summary, Itemized Table, and Checklist.
- End-to-end integration with AuditResult from src.rules.audit_invoice.
- Graceful handling of missing or partial metadata.
"""

import io
import pdfplumber
import pytest

from src.dispute_pdf import generate_dispute_packet_pdf
from src.rules import audit_invoice


@pytest.fixture
def sample_audit_dict():
    return {
        "policy_used": "calendar_day",
        "summary": {
            "total_billed": 1875.0,
            "approved_amount": 1500.0,
            "is_provisional": True,
            "disputed_amount": 240.0,
            "needs_proof_amount": 135.0,
            "not_approved_amount": 375.0,
            "flags": ["RATE_MISMATCH"],
        },
        "lines": [
            {
                "type": "linehaul_fsc",
                "qty": 1.0,
                "unit_rate": 1500.0,
                "amount": 1500.0,
                "agreed_rate": 1500.0,
                "approved_amount": 1500.0,
                "disputed_amount": 0.0,
                "needs_proof_amount": 0.0,
                "status": "APPROVE",
                "reason": "Approved. Signed POD provided on file.",
            },
            {
                "type": "prepull",
                "qty": 1.0,
                "unit_rate": 150.0,
                "amount": 150.0,
                "agreed_rate": 150.0,
                "approved_amount": 0.0,
                "disputed_amount": 150.0,
                "needs_proof_amount": 0.0,
                "status": "DISPUTE",
                "reason": "Direct move under 24 hrs. No written broker authorization.",
            },
            {
                "type": "chassis",
                "qty": 3.0,
                "unit_rate": 45.0,
                "amount": 135.0,
                "agreed_rate": 45.0,
                "approved_amount": 0.0,
                "disputed_amount": 0.0,
                "needs_proof_amount": 135.0,
                "status": "REQUIRE_PROOF",
                "reason": "Chassis charge requires terminal pickup and empty return timestamps.",
            },
            {
                "type": "storage",
                "qty": 2.0,
                "unit_rate": 45.0,
                "amount": 90.0,
                "agreed_rate": 45.0,
                "approved_amount": 0.0,
                "disputed_amount": 90.0,
                "needs_proof_amount": 0.0,
                "status": "DISPUTE",
                "reason": "Yard storage not authorized in contract.",
            },
        ],
        "documents_needed": [
            "Signed Proof of Delivery (POD)",
            "Terminal pickup timestamp (terminal_pickup)",
            "Written Broker Pre-pull Authorization",
        ],
    }


@pytest.fixture
def sample_metadata():
    return {
        "carrier_name": "Pacific Gateway Drayage LLC",
        "mc_dot": "MC# 892341 | DOT# 2948190",
        "invoice_no": "INV-2026-0842",
        "container_no": "TCLU 582910-3",
        "bol_no": "MEDU 91823901",
        "load_id": "LD-88210",
        "audit_date": "October 13, 2026",
        "broker_name": "Premier Freight Logistics LLC",
    }


def test_generate_dispute_packet_pdf_valid_bytes(sample_audit_dict, sample_metadata):
    """Verify that generate_dispute_packet_pdf returns valid PDF binary data."""
    pdf_bytes = generate_dispute_packet_pdf(sample_audit_dict, metadata=sample_metadata)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000


def test_dispute_pdf_content_and_mandatory_disclaimer(sample_audit_dict, sample_metadata):
    """Verify that the generated PDF contains all required sections and the statutory disclaimer."""
    pdf_bytes = generate_dispute_packet_pdf(sample_audit_dict, metadata=sample_metadata)

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        assert len(pdf.pages) >= 1
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # 1. Header & Organization
    assert "PREMIER FREIGHT LOGISTICS" in all_text
    assert "DRAYAGE AUDIT & DISPUTE NOTICE" in all_text
    assert "FORMAL DISPUTE PACKET & DEBIT MEMO" in all_text

    # 2. Carrier & Shipment Info Box
    assert "Pacific Gateway Drayage LLC" in all_text
    assert "INV-2026-0842" in all_text
    assert "TCLU 582910-3" in all_text
    assert "MEDU 91823901" in all_text

    # 3. Financial Summary
    assert "$1,875.00" in all_text
    assert "$1,500.00" in all_text
    assert "$375.00" in all_text

    # 4. Mandatory Disclaimer (Exact legal wording)
    expected_disclaimer = (
        "Final approval decision belongs to the broker. "
        "This document represents a formal debit memo / audit statement under UIIA and broker-carrier contract terms."
    )
    assert expected_disclaimer in all_text

    # 5. Required Documents Checklist
    assert "REAL-WORLD REQUIRED DOCUMENTS CHECKLIST" in all_text
    assert "Proof of Delivery" in all_text

    # 6. Remittance & Signature
    assert "REMITTANCE INSTRUCTIONS" in all_text
    assert "Accounts Payable Authorized Signature" in all_text


def test_generate_dispute_packet_pdf_from_audit_engine(sample_metadata):
    """Verify integration when passing an AuditResult object directly from rules.audit_invoice."""
    terms = {
        "linehaul_fsc": 1500,
        "prepull_fee": 150,
        "chassis_per_day": 45,
        "storage_per_day": 45,
        "detention_per_hour": 75,
        "detention_free_hours": 2,
        "chassis_day_policy": "calendar_day",
        "chassis_free_days": 0,
        "chassis_min_days": 0,
        "storage_free_days": 0,
        "prepull_includes_first_storage_day": None,
        "direct_move_hours_threshold": 24,
    }
    timeline = {
        "terminal_pickup": "2026-06-23T21:00",
        "warehouse_appointment": "2026-06-24T08:00",
        "delivery_actual": "2026-06-24T08:00",
        "empty_return": "2026-06-24T16:00",
        "pod_provided": True,
        "prepull_request_documented": False,
    }
    invoice = {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1, "unit_rate": 1500, "amount": 1500},
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
            {"type": "chassis", "qty": 3, "unit_rate": 45, "amount": 135},
        ],
        "total": 1785,
    }

    audit_res = audit_invoice(invoice, terms, timeline)
    pdf_bytes = generate_dispute_packet_pdf(audit_res, metadata=sample_metadata)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_dispute_packet_pdf_missing_metadata(sample_audit_dict):
    """Verify that PDF generation completes cleanly even when metadata is completely omitted."""
    pdf_bytes = generate_dispute_packet_pdf(sample_audit_dict, metadata=None)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000
