"""Tests for batch invoice auditing engine and API routes."""

import pytest
from starlette.testclient import TestClient

from app import app
from src.batch import batch_audit_invoices


@pytest.fixture
def base_terms():
    return {
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
        "prepull_includes_first_storage_day": False,
        "direct_move_hours_threshold": 24.0,
    }


@pytest.fixture
def base_timeline():
    return {
        "terminal_pickup": "2026-06-23T08:00",
        "yard_in": "2026-06-23T10:00",
        "yard_out": "2026-06-23T14:00",
        "warehouse_appointment": "2026-06-24T08:00",
        "delivery_actual": "2026-06-24T08:00",
        "warehouse_in": "2026-06-24T08:00",
        "warehouse_out": "2026-06-24T09:30",
        "empty_return": "2026-06-24T16:00",
        "pod_provided": True,
        "prepull_request_documented": True,
    }


@pytest.fixture
def three_invoices():
    # Invoice 1: Perfectly clean move
    # 2 calendar days chassis (23rd, 24th) @ $45 = $90, prepull $150, linehaul $1500 -> Total $1740
    inv1 = {
        "invoice_id": "INV-CLEAN-001",
        "lines": [
            {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1500.0, "amount": 1500.0},
            {"type": "prepull", "qty": 1.0, "unit_rate": 150.0, "amount": 150.0},
            {"type": "chassis", "qty": 2.0, "unit_rate": 45.0, "amount": 90.0},
        ],
        "total": 1740.0,
    }

    # Invoice 2: Rate mismatch / overcharge (disputes expected)
    # Chassis billed at $65 instead of agreed $45 (3 days = $195 vs $90 max days and $45 rate)
    # Storage billed 2 days without documentation
    inv2 = {
        "invoice_id": "INV-DISPUTE-002",
        "lines": [
            {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1500.0, "amount": 1500.0},
            {"type": "chassis", "qty": 3.0, "unit_rate": 65.0, "amount": 195.0},
            {"type": "storage", "qty": 2.0, "unit_rate": 45.0, "amount": 90.0},
        ],
        "total": 1785.0,
    }

    # Invoice 3: Detention billed without proof / documentation
    # Consignee wait time billed 4 hours ($300), but timeline has no wait or missing timestamps
    inv3 = {
        "invoice_id": "INV-PROOF-003",
        "lines": [
            {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1500.0, "amount": 1500.0},
            {"type": "detention", "qty": 4.0, "unit_rate": 75.0, "amount": 300.0},
        ],
        "total": 1800.0,
    }

    return [inv1, inv2, inv3]


def test_batch_audit_three_distinct_invoices(three_invoices, base_terms, base_timeline):
    result = batch_audit_invoices(three_invoices, base_terms, base_timeline)

    assert "batch_summary" in result
    assert "invoices" in result
    assert len(result["invoices"]) == 3

    summary = result["batch_summary"]
    assert summary["total_invoices_audited"] == 3
    assert summary["total_billed"] > 0
    assert summary["total_approved"] > 0
    assert summary["total_disputed"] > 0
    assert summary["total_dollars_saved"] == round(
        summary["total_disputed"] + summary["total_needs_proof"], 2
    )

    # Clean invoice count + disputed invoice count must equal total invoices
    assert summary["clean_invoices_count"] + summary["disputed_invoices_count"] == 3
    assert summary["clean_invoices_count"] == 1
    assert summary["disputed_invoices_count"] == 2


def test_batch_totals_sum_reconciliation(three_invoices, base_terms, base_timeline):
    result = batch_audit_invoices(three_invoices, base_terms, base_timeline)
    summary = result["batch_summary"]
    inv_list = result["invoices"]

    calc_billed = round(sum(inv["summary"]["total_billed"] for inv in inv_list), 2)
    calc_approved = round(sum(inv["summary"]["approved_amount"] for inv in inv_list), 2)
    calc_disputed = round(sum(inv["summary"]["disputed_amount"] for inv in inv_list), 2)
    calc_needs_proof = round(sum(inv["summary"]["needs_proof_amount"] for inv in inv_list), 2)
    calc_not_approved = round(sum(inv["summary"]["not_approved_amount"] for inv in inv_list), 2)

    assert summary["total_billed"] == calc_billed
    assert summary["total_approved"] == calc_approved
    assert summary["total_disputed"] == calc_disputed
    assert summary["total_needs_proof"] == calc_needs_proof
    assert summary["total_not_approved"] == calc_not_approved
    assert summary["total_dollars_saved"] == round(calc_disputed + calc_needs_proof, 2)

    # Check invoice item structures
    for idx, inv in enumerate(inv_list):
        assert inv["invoice_index"] == idx
        assert inv["invoice_id"] == three_invoices[idx]["invoice_id"]
        assert "lines" in inv
        assert "documents_needed" in inv
        assert isinstance(inv["lines"], list)
        assert isinstance(inv["documents_needed"], list)


def test_batch_empty_list(base_terms, base_timeline):
    result = batch_audit_invoices([], base_terms, base_timeline)
    summary = result["batch_summary"]

    assert summary["total_invoices_audited"] == 0
    assert summary["total_billed"] == 0.0
    assert summary["total_approved"] == 0.0
    assert summary["total_disputed"] == 0.0
    assert summary["total_needs_proof"] == 0.0
    assert summary["total_not_approved"] == 0.0
    assert summary["total_dollars_saved"] == 0.0
    assert summary["clean_invoices_count"] == 0
    assert summary["disputed_invoices_count"] == 0
    assert result["invoices"] == []


def test_batch_with_enveloped_invoices_and_per_invoice_overrides(base_terms, base_timeline):
    # Enveloped invoice format with individual timeline overrides
    enveloped = [
        {
            "invoice_id": "ENV-01",
            "invoice": {
                "lines": [
                    {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1500.0, "amount": 1500.0}
                ],
                "total": 1500.0,
            },
            "terms": base_terms,
            "timeline": base_timeline,
        },
        {
            "id": "ENV-02",
            "invoice": {
                "lines": [
                    {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1600.0, "amount": 1600.0}
                ],
                "total": 1600.0,
            },
        },
    ]

    result = batch_audit_invoices(enveloped, base_terms, base_timeline)
    assert result["batch_summary"]["total_invoices_audited"] == 2
    assert result["invoices"][0]["invoice_id"] == "ENV-01"
    assert result["invoices"][1]["invoice_id"] == "ENV-02"
    # Second invoice has rate mismatch on linehaul (1600 vs agreed 1500 -> 100 disputed)
    assert result["invoices"][1]["summary"]["disputed_amount"] == 100.0


def test_api_batch_audit_routes(three_invoices, base_terms, base_timeline):
    client = TestClient(app)
    payload = {
        "invoices": three_invoices,
        "terms": base_terms,
        "timeline": base_timeline,
    }

    # Test POST /api/batch-audit
    resp_api = client.post("/api/batch-audit", json=payload)
    assert resp_api.status_code == 200
    data_api = resp_api.json()
    assert data_api["success"] is True
    assert "data" in data_api
    assert data_api["data"]["batch_summary"]["total_invoices_audited"] == 3

    # Test POST /batch-audit alias
    resp_alias = client.post("/batch-audit", json=payload)
    assert resp_alias.status_code == 200
    data_alias = resp_alias.json()
    assert data_alias["success"] is True
    assert data_alias["data"]["batch_summary"]["total_invoices_audited"] == 3
