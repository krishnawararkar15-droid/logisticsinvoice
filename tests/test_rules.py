"""Automated test suite for deterministic auditing rules in src/rules.py.

Covers:
- Test Case 1 with calendar_day policy (line-by-line & executive summary)
- Test Case 1 with 24h_block policy (line-by-line & executive summary)
- Dual policy scenario when chassis_day_policy is null
- Fully supported case (100% APPROVE, $0 disputed, $0 needs proof, final approval)
- Error & validation flags (MATH_ERROR, RATE_MISMATCH, TOTAL_MISMATCH, UNAGREED_CHARGE, DUPLICATE_LINE)
- Detention scenarios (supported hours, excess hours, missing timestamps, not billed)
- Free days and minimum days (chassis_free_days, chassis_min_days, storage_free_days, prepull_includes_first_storage_day)
"""

import copy

import pytest

from src.rules import (
    FLAG_DUPLICATE_LINE,
    FLAG_MATH_ERROR,
    FLAG_RATE_MISMATCH,
    FLAG_TOTAL_MISMATCH,
    FLAG_UNAGREED_CHARGE,
    STATUS_APPROVE,
    STATUS_DISPUTE,
    STATUS_REQUIRE_PROOF,
    audit_invoice,
)


@pytest.fixture
def base_terms():
    return {
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


@pytest.fixture
def base_timeline():
    return {
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


@pytest.fixture
def base_invoice():
    return {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1, "unit_rate": 1500, "amount": 1500},
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
            {"type": "chassis", "qty": 3, "unit_rate": 45, "amount": 135},
            {"type": "storage", "qty": 2, "unit_rate": 45, "amount": 90},
        ],
        "total": 1875,
    }


# ==============================================================================
# 1. TEST CASE 1: CALENDAR DAY POLICY
# ==============================================================================

def test_test_case_1_calendar_day_policy(base_terms, base_timeline, base_invoice):
    """Verify Test Case 1 under 'calendar_day' policy:
    - linehaul_fsc: $1,500 APPROVE (pending signed POD)
    - chassis (3 days @ $45 = $135): 2 days ($90) APPROVE, 1 day ($45) DISPUTE
    - storage (2 days @ $45 = $90): 1 day ($45) DISPUTE, 1 day ($45) REQUIRE_PROOF
    - prepull ($150): REQUIRE_PROOF
    - Summary: Approved $1,590 (provisional), Disputed $90, Needs Proof $195, Total Not Approved $285.
    """
    result = audit_invoice(base_invoice, base_terms, base_timeline, override_policy="calendar_day")
    lines_by_type = {line.type: line for line in result.lines}

    # 1. linehaul_fsc
    linehaul = lines_by_type["linehaul_fsc"]
    assert linehaul.status == STATUS_APPROVE
    assert linehaul.amount == 1500.0
    assert linehaul.approved_amount == 1500.0
    assert linehaul.disputed_amount == 0.0
    assert linehaul.needs_proof_amount == 0.0
    assert "APPROVE (pending signed POD)" in linehaul.reason
    assert "Signed Proof of Delivery (POD)" in linehaul.missing_items

    # 2. chassis
    chassis = lines_by_type["chassis"]
    assert chassis.status == STATUS_DISPUTE
    assert chassis.amount == 135.0
    assert chassis.qty == 3.0
    assert chassis.approved_qty == 2.0
    assert chassis.approved_amount == 90.0
    assert chassis.disputed_qty == 1.0
    assert chassis.disputed_amount == 45.0
    assert chassis.needs_proof_amount == 0.0
    assert "2 day(s) ($90) APPROVE, 1 day(s) ($45) DISPUTE" in chassis.reason

    # 3. storage
    storage = lines_by_type["storage"]
    assert storage.status == STATUS_DISPUTE
    assert storage.amount == 90.0
    assert storage.qty == 2.0
    assert storage.approved_amount == 0.0
    assert storage.disputed_qty == 1.0
    assert storage.disputed_amount == 45.0
    assert storage.needs_proof_qty == 1.0
    assert storage.needs_proof_amount == 45.0
    assert "1 day(s) ($45) DISPUTE, 1 day(s) ($45) REQUIRE_PROOF" in storage.reason

    # 4. prepull
    prepull = lines_by_type["prepull"]
    assert prepull.status == STATUS_REQUIRE_PROOF
    assert prepull.amount == 150.0
    assert prepull.approved_amount == 0.0
    assert prepull.disputed_amount == 0.0
    assert prepull.needs_proof_amount == 150.0
    assert "REQUIRE_PROOF" in prepull.reason

    # Executive Financial Summary
    summary = result.summary
    assert summary.total_billed == 1875.0
    assert summary.approved_amount == 1590.0
    assert summary.is_provisional is True
    assert summary.disputed_amount == 90.0
    assert summary.needs_proof_amount == 195.0
    assert summary.not_approved_amount == 285.0
    assert summary.not_approved_amount == summary.disputed_amount + summary.needs_proof_amount


# ==============================================================================
# 2. TEST CASE 1: 24-HOUR BLOCK POLICY
# ==============================================================================

def test_test_case_1_24h_block_policy(base_terms, base_timeline, base_invoice):
    """Verify Test Case 1 under '24h_block' policy:
    - chassis: 1 day ($45) APPROVE, 2 days ($90) DISPUTE
    - Summary: Approved $1,545 (provisional), Disputed $135, Needs Proof $195, Total Not Approved $330.
    """
    result = audit_invoice(base_invoice, base_terms, base_timeline, override_policy="24h_block")
    lines_by_type = {line.type: line for line in result.lines}

    # chassis
    chassis = lines_by_type["chassis"]
    assert chassis.status == STATUS_DISPUTE
    assert chassis.amount == 135.0
    assert chassis.qty == 3.0
    assert chassis.approved_qty == 1.0
    assert chassis.approved_amount == 45.0
    assert chassis.disputed_qty == 2.0
    assert chassis.disputed_amount == 90.0
    assert chassis.needs_proof_amount == 0.0
    assert "1 day(s) ($45) APPROVE, 2 day(s) ($90) DISPUTE" in chassis.reason

    # Executive Financial Summary
    summary = result.summary
    assert summary.total_billed == 1875.0
    assert summary.approved_amount == 1545.0
    assert summary.is_provisional is True
    assert summary.disputed_amount == 135.0
    assert summary.needs_proof_amount == 195.0
    assert summary.not_approved_amount == 330.0
    assert summary.not_approved_amount == summary.disputed_amount + summary.needs_proof_amount


# ==============================================================================
# 3. DUAL POLICY SCENARIO (CHASSIS_DAY_POLICY IS NULL)
# ==============================================================================

def test_dual_policy_scenario_when_policy_null(base_terms, base_timeline, base_invoice):
    """Verify dual policy side-by-side evaluation when chassis_day_policy is null."""
    terms_null = copy.deepcopy(base_terms)
    terms_null["chassis_day_policy"] = None

    result = audit_invoice(base_invoice, terms_null, base_timeline)

    # Primary policy (calendar_day baseline)
    assert "null" in result.policy_used
    assert result.summary.approved_amount == 1590.0
    assert result.summary.disputed_amount == 90.0
    assert result.summary.needs_proof_amount == 195.0
    assert result.summary.not_approved_amount == 285.0
    assert result.summary.is_provisional is True

    # Alternative policy (24h_block)
    assert result.alternative_policy_result is not None
    alt = result.alternative_policy_result
    alt_summary = alt["summary"]
    assert alt_summary["approved_amount"] == 1545.0
    assert alt_summary["disputed_amount"] == 135.0
    assert alt_summary["needs_proof_amount"] == 195.0
    assert alt_summary["not_approved_amount"] == 330.0

    # Notes explain both policies evaluated
    assert any("Both 'calendar_day' and '24h_block' policies were calculated" in n for n in result.notes)


# ==============================================================================
# 4. FULLY SUPPORTED CASE (100% APPROVAL)
# ==============================================================================

def test_fully_supported_invoice():
    """Verify clean, 100% approved invoice with complete documentation:
    - yard_in and yard_out provided (1 night yard hold), 1 day storage billed @ $45 -> APPROVE
    - prepull_request_documented = True and yard drop present -> prepull $150 APPROVE
    - signed POD = True -> linehaul_fsc APPROVE (no pending pod note)
    - chassis days match actual duration -> APPROVE
    - Entire invoice: 100% APPROVE, $0 disputed, $0 needs proof, not provisional.
    """
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
        "prepull_includes_first_storage_day": False,
        "direct_move_hours_threshold": 24,
    }

    # 1 night yard hold: 2026-06-23 22:00 to 2026-06-24 06:00 (1 midnight)
    # Chassis pickup 2026-06-23 21:00, return 2026-06-24 16:00 (2 calendar days)
    timeline = {
        "terminal_pickup": "2026-06-23T21:00",
        "yard_in": "2026-06-23T22:00",
        "yard_out": "2026-06-24T06:00",
        "warehouse_appointment": "2026-06-24T08:00",
        "delivery_actual": "2026-06-24T08:00",
        "warehouse_in": None,
        "warehouse_out": None,
        "empty_return": "2026-06-24T16:00",
        "pod_provided": True,
        "prepull_request_documented": True,
    }

    invoice = {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1, "unit_rate": 1500, "amount": 1500},
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
            {"type": "chassis", "qty": 2, "unit_rate": 45, "amount": 90},
            {"type": "storage", "qty": 1, "unit_rate": 45, "amount": 45},
        ],
        "total": 1785,
    }

    result = audit_invoice(invoice, terms, timeline)
    lines_by_type = {line.type: line for line in result.lines}

    # 1. linehaul_fsc
    linehaul = lines_by_type["linehaul_fsc"]
    assert linehaul.status == STATUS_APPROVE
    assert linehaul.approved_amount == 1500.0
    assert linehaul.disputed_amount == 0.0
    assert "pending signed POD" not in linehaul.reason
    assert "Signed POD provided" in linehaul.reason

    # 2. prepull
    prepull = lines_by_type["prepull"]
    assert prepull.status == STATUS_APPROVE
    assert prepull.approved_amount == 150.0
    assert prepull.disputed_amount == 0.0
    assert prepull.needs_proof_amount == 0.0

    # 3. chassis
    chassis = lines_by_type["chassis"]
    assert chassis.status == STATUS_APPROVE
    assert chassis.approved_amount == 90.0
    assert chassis.disputed_amount == 0.0

    # 4. storage
    storage = lines_by_type["storage"]
    assert storage.status == STATUS_APPROVE
    assert storage.approved_amount == 45.0
    assert storage.disputed_amount == 0.0
    assert storage.needs_proof_amount == 0.0

    # Executive Summary: 100% APPROVE
    summary = result.summary
    assert summary.total_billed == 1785.0
    assert summary.approved_amount == 1785.0
    assert summary.disputed_amount == 0.0
    assert summary.needs_proof_amount == 0.0
    assert summary.not_approved_amount == 0.0
    assert summary.is_provisional is False
    assert len(summary.flags) == 0
    assert len(result.documents_needed) == 0


# ==============================================================================
# 5. ERROR & VALIDATION FLAGS
# ==============================================================================

def test_flag_math_error(base_terms, base_timeline):
    """qty=2, unit_rate=45, amount=100 (should be 90) -> flag MATH_ERROR."""
    invoice = {
        "lines": [
            {"type": "storage", "qty": 2, "unit_rate": 45, "amount": 100},
        ],
        "total": 100,
    }
    result = audit_invoice(invoice, base_terms, base_timeline)
    line = result.lines[0]
    assert FLAG_MATH_ERROR in line.flags
    assert FLAG_MATH_ERROR in result.summary.flags


def test_flag_rate_mismatch(base_terms, base_timeline):
    """agreed storage is 45, billed unit_rate is 55 -> flag RATE_MISMATCH."""
    invoice = {
        "lines": [
            {"type": "storage", "qty": 2, "unit_rate": 55, "amount": 110},
        ],
        "total": 110,
    }
    result = audit_invoice(invoice, base_terms, base_timeline)
    line = result.lines[0]
    assert FLAG_RATE_MISMATCH in line.flags
    assert FLAG_RATE_MISMATCH in result.summary.flags


def test_flag_total_mismatch(base_terms, base_timeline):
    """sum of lines is 1875, invoice total is 2000 -> flag TOTAL_MISMATCH."""
    invoice = {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1, "unit_rate": 1500, "amount": 1500},
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
            {"type": "chassis", "qty": 3, "unit_rate": 45, "amount": 135},
            {"type": "storage", "qty": 2, "unit_rate": 45, "amount": 90},
        ],
        "total": 2000,  # 1875 vs 2000
    }
    result = audit_invoice(invoice, base_terms, base_timeline)
    assert FLAG_TOTAL_MISMATCH in result.summary.flags


def test_flag_unagreed_charge(base_terms, base_timeline):
    """charge type 'hazmat_fee' not in terms -> flag UNAGREED_CHARGE and DISPUTE."""
    invoice = {
        "lines": [
            {"type": "hazmat_fee", "qty": 1, "unit_rate": 250, "amount": 250},
        ],
        "total": 250,
    }
    result = audit_invoice(invoice, base_terms, base_timeline)
    line = result.lines[0]
    assert FLAG_UNAGREED_CHARGE in line.flags
    assert FLAG_UNAGREED_CHARGE in result.summary.flags
    assert line.status == STATUS_DISPUTE
    assert line.disputed_amount == 250.0
    assert line.approved_amount == 0.0


def test_flag_duplicate_line(base_terms, base_timeline):
    """two separate lines for 'chassis' -> flag DUPLICATE_LINE on second line."""
    invoice = {
        "lines": [
            {"type": "chassis", "qty": 1, "unit_rate": 45, "amount": 45},
            {"type": "chassis", "qty": 2, "unit_rate": 45, "amount": 90},
        ],
        "total": 135,
    }
    result = audit_invoice(invoice, base_terms, base_timeline)
    assert len(result.lines) == 2
    second_line = result.lines[1]
    assert FLAG_DUPLICATE_LINE in second_line.flags
    assert FLAG_DUPLICATE_LINE in result.summary.flags
    assert second_line.status == STATUS_DISPUTE
    assert second_line.disputed_amount == 90.0


# ==============================================================================
# 6. DETENTION SCENARIOS
# ==============================================================================

def test_detention_billed_exact_supported_hours(base_terms):
    """Detention billed with warehouse_in 08:00, warehouse_out 12:00 (4 hours),
    free hours = 2. Billable = 2 hours @ 75 = $150.
    Carrier billed 2 hours @ 75 ($150) -> APPROVE.
    """
    timeline = {
        "warehouse_in": "2026-06-24T08:00",
        "warehouse_out": "2026-06-24T12:00",
    }
    invoice = {
        "lines": [
            {"type": "detention", "qty": 2, "unit_rate": 75, "amount": 150},
        ],
        "total": 150,
    }
    result = audit_invoice(invoice, base_terms, timeline)
    detention = result.lines[0]
    assert detention.status == STATUS_APPROVE
    assert detention.approved_qty == 2.0
    assert detention.approved_amount == 150.0
    assert detention.disputed_amount == 0.0
    assert detention.needs_proof_amount == 0.0


def test_detention_billed_excess_hours(base_terms):
    """Detention billed with warehouse_in 08:00, warehouse_out 12:00 (4 hours),
    free hours = 2. Billable = 2 hours @ 75 = $150.
    Carrier billed 4 hours @ 75 ($300) -> 2 hours ($150) APPROVE, 2 hours ($150) DISPUTE.
    """
    timeline = {
        "warehouse_in": "2026-06-24T08:00",
        "warehouse_out": "2026-06-24T12:00",
    }
    invoice = {
        "lines": [
            {"type": "detention", "qty": 4, "unit_rate": 75, "amount": 300},
        ],
        "total": 300,
    }
    result = audit_invoice(invoice, base_terms, timeline)
    detention = result.lines[0]
    assert detention.status == STATUS_DISPUTE
    assert detention.approved_qty == 2.0
    assert detention.approved_amount == 150.0
    assert detention.disputed_qty == 2.0
    assert detention.disputed_amount == 150.0
    assert detention.needs_proof_amount == 0.0


def test_detention_billed_missing_warehouse_timestamps(base_terms):
    """Detention billed but warehouse timestamps are null/missing -> REQUIRE_PROOF."""
    timeline = {
        "warehouse_in": None,
        "warehouse_out": None,
    }
    invoice = {
        "lines": [
            {"type": "detention", "qty": 2, "unit_rate": 75, "amount": 150},
        ],
        "total": 150,
    }
    result = audit_invoice(invoice, base_terms, timeline)
    detention = result.lines[0]
    assert detention.status == STATUS_REQUIRE_PROOF
    assert detention.approved_amount == 0.0
    assert detention.disputed_amount == 0.0
    assert detention.needs_proof_amount == 150.0
    assert any("warehouse_in" in item for item in detention.missing_items)
    assert any("warehouse_out" in item for item in detention.missing_items)


def test_detention_not_billed(base_terms, base_timeline, base_invoice):
    """When detention is not billed on invoice -> note recorded."""
    result = audit_invoice(base_invoice, base_terms, base_timeline)
    assert any("Detention: NOT_BILLED on this invoice." in n for n in result.notes)


# ==============================================================================
# 7. FREE DAYS AND MINIMUM DAYS
# ==============================================================================

def test_chassis_free_days_and_min_days():
    """Verify chassis_free_days and chassis_min_days:
    - 3 calendar days with free_days=1 -> supported = 2 days
    - 1 calendar day with free_days=1, min_days=2 -> supported = 2 days
    """
    terms = {
        "chassis_per_day": 45,
        "chassis_day_policy": "calendar_day",
        "chassis_free_days": 1,
        "chassis_min_days": 0,
    }
    # 3 calendar days: 2026-06-20 to 2026-06-22
    timeline = {
        "terminal_pickup": "2026-06-20T08:00",
        "empty_return": "2026-06-22T17:00",
    }
    invoice = {
        "lines": [{"type": "chassis", "qty": 3, "unit_rate": 45, "amount": 135}],
        "total": 135,
    }
    # 3 days raw - 1 free day = 2 supported days
    result = audit_invoice(invoice, terms, timeline)
    chassis = result.lines[0]
    assert chassis.approved_qty == 2.0
    assert chassis.disputed_qty == 1.0

    # Test minimum days override
    terms["chassis_min_days"] = 2
    timeline_1day = {
        "terminal_pickup": "2026-06-20T08:00",
        "empty_return": "2026-06-20T17:00",  # 1 calendar day
    }
    invoice_2days = {
        "lines": [{"type": "chassis", "qty": 2, "unit_rate": 45, "amount": 90}],
        "total": 90,
    }
    # raw=1, raw-free=0, but min_days=2 -> supported = 2 days
    res_min = audit_invoice(invoice_2days, terms, timeline_1day)
    chassis_min = res_min.lines[0]
    assert chassis_min.status == STATUS_APPROVE
    assert chassis_min.approved_qty == 2.0
    assert chassis_min.approved_amount == 90.0


def test_storage_free_days():
    """Verify storage_free_days = 1 deducts 1 day from supported storage."""
    terms = {
        "storage_per_day": 45,
        "storage_free_days": 1,
        "prepull_includes_first_storage_day": False,
    }
    # 2 nights in yard: 2026-06-20 to 2026-06-22 (2 midnights)
    timeline = {
        "yard_in": "2026-06-20T20:00",
        "yard_out": "2026-06-22T08:00",
    }
    # Carrier billed 2 days -> 1 supported (2-1), 1 disputed
    invoice = {
        "lines": [{"type": "storage", "qty": 2, "unit_rate": 45, "amount": 90}],
        "total": 90,
    }
    result = audit_invoice(invoice, terms, timeline)
    storage = result.lines[0]
    assert storage.status == STATUS_DISPUTE
    assert storage.approved_qty == 1.0
    assert storage.approved_amount == 45.0
    assert storage.disputed_qty == 1.0
    assert storage.disputed_amount == 45.0


def test_prepull_includes_first_storage_day_true():
    """Verify prepull_includes_first_storage_day = True note/adjustment:
    - First storage day is included in pre-pull fee.
    - 2 nights in yard -> 1 supported day, 1 disputed day.
    - Reason contains note about pre-pull fee including first yard storage day.
    - documents_needed does not ask to clarify prepull_includes_first_storage_day.
    """
    terms = {
        "prepull_fee": 150,
        "storage_per_day": 45,
        "storage_free_days": 0,
        "prepull_includes_first_storage_day": True,
    }
    timeline = {
        "yard_in": "2026-06-20T20:00",
        "yard_out": "2026-06-22T08:00",  # 2 midnights
        "prepull_request_documented": True,
    }
    invoice = {
        "lines": [
            {"type": "prepull", "qty": 1, "unit_rate": 150, "amount": 150},
            {"type": "storage", "qty": 2, "unit_rate": 45, "amount": 90},
        ],
        "total": 240,
    }
    result = audit_invoice(invoice, terms, timeline)
    storage = [line for line in result.lines if line.type == "storage"][0]

    # 2 nights - 1 included in prepull = 1 supported day
    assert storage.approved_qty == 1.0
    assert storage.approved_amount == 45.0
    assert storage.disputed_qty == 1.0
    assert storage.disputed_amount == 45.0
    assert "Pre-pull fee includes the first yard storage day" in storage.reason

    # documents_needed does NOT have the null clarification note
    assert not any("prepull_includes_first_storage_day is null" in doc for doc in result.documents_needed)
