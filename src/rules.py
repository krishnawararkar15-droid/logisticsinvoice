"""Deterministic auditing rules engine for Accessorial Invoice Checker (v1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.dates import (
    calculate_24h_blocks,
    calculate_calendar_days,
    count_midnights_between,
    hours_between,
    parse_iso_timestamp,
)

# Status constants
STATUS_APPROVE = "APPROVE"
STATUS_DISPUTE = "DISPUTE"
STATUS_REQUIRE_PROOF = "REQUIRE_PROOF"
STATUS_NOT_BILLED = "NOT_BILLED"

# Flag constants
FLAG_MATH_ERROR = "MATH_ERROR"
FLAG_RATE_MISMATCH = "RATE_MISMATCH"
FLAG_TOTAL_MISMATCH = "TOTAL_MISMATCH"
FLAG_UNAGREED_CHARGE = "UNAGREED_CHARGE"
FLAG_DUPLICATE_LINE = "DUPLICATE_LINE"


@dataclass
class LineAuditResult:
    type: str
    qty: float
    unit_rate: float
    amount: float
    agreed_rate: Optional[float]
    approved_amount: float
    disputed_amount: float
    needs_proof_amount: float
    status: str
    flags: List[str] = field(default_factory=list)
    reason: str = ""
    timestamps_used: Dict[str, Any] = field(default_factory=dict)
    missing_items: List[str] = field(default_factory=list)
    approved_qty: Optional[float] = None
    disputed_qty: Optional[float] = None
    needs_proof_qty: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditSummary:
    total_billed: float
    approved_amount: float
    is_provisional: bool
    disputed_amount: float
    needs_proof_amount: float
    not_approved_amount: float
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditResult:
    policy_used: str
    lines: List[LineAuditResult]
    summary: AuditSummary
    documents_needed: List[str]
    notes: List[str] = field(default_factory=list)
    alternative_policy_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "policy_used": self.policy_used,
            "lines": [line.to_dict() for line in self.lines],
            "summary": self.summary.to_dict(),
            "documents_needed": self.documents_needed,
            "notes": self.notes,
        }
        if self.alternative_policy_result:
            d["alternative_policy_result"] = self.alternative_policy_result
        return d


RATE_KEY_MAP = {
    "linehaul_fsc": "linehaul_fsc",
    "prepull": "prepull_fee",
    "chassis": "chassis_per_day",
    "storage": "storage_per_day",
    "detention": "detention_per_hour",
}

DEFAULT_SHORT_HAUL_THRESHOLD_MILES = 150.0


def resolve_haul_type(terms: Dict[str, Any], timeline: Optional[Dict[str, Any]] = None) -> str:
    """
    Resolve haul_type ('short' or 'long').
    If lane_miles is given, haul_type is calculated from the configurable threshold:
      lane_miles <= threshold -> 'short'
      lane_miles > threshold -> 'long'
    Otherwise, uses haul_type if provided (defaulting to 'long' if unspecified).
    """
    timeline = timeline or {}
    lane_miles = terms.get("lane_miles")
    if lane_miles is None or lane_miles == "":
        lane_miles = timeline.get("lane_miles")

    threshold = terms.get("short_haul_miles_threshold")
    if threshold is None or threshold == "":
        threshold = terms.get("lane_miles_threshold", DEFAULT_SHORT_HAUL_THRESHOLD_MILES)
    try:
        threshold_val = float(threshold)
    except (ValueError, TypeError):
        threshold_val = DEFAULT_SHORT_HAUL_THRESHOLD_MILES

    if lane_miles is not None and lane_miles != "":
        try:
            miles = float(lane_miles)
            return "short" if miles <= threshold_val else "long"
        except (ValueError, TypeError):
            pass

    haul = terms.get("haul_type") or timeline.get("haul_type")
    if haul and str(haul).strip().lower() in ("short", "long"):
        return str(haul).strip().lower()

    return "long"


def _audit_single_line(
    line: Dict[str, Any],
    terms: Dict[str, Any],
    timeline: Dict[str, Any],
    chassis_policy: str,
    seen_types: set,
) -> LineAuditResult:
    charge_type = line.get("type", "").strip().lower()
    qty = float(line.get("qty", 0))
    unit_rate = float(line.get("unit_rate", 0))
    amount = float(line.get("amount", 0))

    flags: List[str] = []
    missing_items: List[str] = []
    timestamps_used: Dict[str, Any] = {}

    # Rule A checks
    # 1. Math check
    calc_amount = round(qty * unit_rate, 2)
    if abs(calc_amount - amount) > 0.01:
        flags.append(FLAG_MATH_ERROR)

    # 2. Duplicate line check
    if charge_type in seen_types:
        flags.append(FLAG_DUPLICATE_LINE)

    # 3. Agreed rate lookup
    rate_key = RATE_KEY_MAP.get(charge_type)
    agreed_rate = terms.get(rate_key) if rate_key else None
    if agreed_rate is None and rate_key not in terms:
        flags.append(FLAG_UNAGREED_CHARGE)
    elif agreed_rate is not None and abs(float(agreed_rate) - unit_rate) > 0.01:
        flags.append(FLAG_RATE_MISMATCH)

    # If unagreed charge or duplicate line, dispute entirely
    if FLAG_UNAGREED_CHARGE in flags:
        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=None,
            approved_amount=0.0,
            disputed_amount=amount,
            needs_proof_amount=0.0,
            status=STATUS_DISPUTE,
            flags=flags,
            reason=f"Charge '{charge_type}' is not in agreed contract terms.",
            timestamps_used={},
            missing_items=[],
            approved_qty=0.0,
            disputed_qty=qty,
            needs_proof_qty=0.0,
        )

    if FLAG_DUPLICATE_LINE in flags:
        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=float(agreed_rate) if agreed_rate is not None else None,
            approved_amount=0.0,
            disputed_amount=amount,
            needs_proof_amount=0.0,
            status=STATUS_DISPUTE,
            flags=flags,
            reason=f"Duplicate line for charge '{charge_type}'.",
            timestamps_used={},
            missing_items=[],
            approved_qty=0.0,
            disputed_qty=qty,
            needs_proof_qty=0.0,
        )

    expected_rate = float(agreed_rate) if agreed_rate is not None else unit_rate

    # Rule B: Linehaul + FSC
    if charge_type == "linehaul_fsc":
        pod_provided = bool(timeline.get("pod_provided", False))
        if not pod_provided:
            missing_items.append("Signed Proof of Delivery (POD)")

        rate_diff = max(0.0, round((unit_rate - expected_rate) * qty, 2))
        math_diff = max(0.0, round(amount - calc_amount, 2))
        disputed_amount = rate_diff + math_diff
        approved_amount = max(0.0, round(amount - disputed_amount, 2))
        needs_proof_amount = 0.0

        status = STATUS_APPROVE if disputed_amount == 0 else STATUS_DISPUTE
        reason_parts = []
        if pod_provided:
            reason_parts.append("Approved. Signed POD provided.")
        else:
            reason_parts.append("APPROVE (pending signed POD).")
        reason_parts.append("Note: FSC cannot be verified separately because Linehaul and FSC are combined in one line.")
        if rate_diff > 0:
            reason_parts.append(f"Rate mismatch: billed ${unit_rate:.2f}/ea vs agreed ${expected_rate:.2f}/ea.")
        if math_diff > 0:
            reason_parts.append(f"Math error: billed ${amount:.2f} vs calculated ${calc_amount:.2f}.")

        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=expected_rate,
            approved_amount=approved_amount,
            disputed_amount=disputed_amount,
            needs_proof_amount=needs_proof_amount,
            status=status,
            flags=flags,
            reason=" ".join(reason_parts),
            timestamps_used={},
            missing_items=missing_items,
            approved_qty=qty if disputed_amount == 0 else 0.0,
            disputed_qty=0.0 if disputed_amount == 0 else qty,
            needs_proof_qty=0.0,
        )

    # Rule C: Chassis
    elif charge_type == "chassis":
        t_pickup = parse_iso_timestamp(timeline.get("terminal_pickup"))
        e_return = parse_iso_timestamp(timeline.get("empty_return"))

        if not t_pickup:
            missing_items.append("Terminal pickup timestamp (terminal_pickup)")
        if not e_return:
            missing_items.append("Empty return timestamp (empty_return)")

        if not t_pickup or not e_return:
            return LineAuditResult(
                type=charge_type,
                qty=qty,
                unit_rate=unit_rate,
                amount=amount,
                agreed_rate=expected_rate,
                approved_amount=0.0,
                disputed_amount=0.0,
                needs_proof_amount=amount,
                status=STATUS_REQUIRE_PROOF,
                flags=flags,
                reason="Chassis charge requires terminal pickup and empty return timestamps to verify days.",
                timestamps_used={
                    "terminal_pickup": timeline.get("terminal_pickup"),
                    "empty_return": timeline.get("empty_return"),
                },
                missing_items=missing_items,
                approved_qty=0.0,
                disputed_qty=0.0,
                needs_proof_qty=qty,
            )

        timestamps_used = {
            "terminal_pickup": t_pickup.isoformat(),
            "empty_return": e_return.isoformat(),
        }

        # Calculate raw supported days based on policy
        if chassis_policy == "24h_block":
            raw_days = calculate_24h_blocks(t_pickup, e_return)
            hours_elapsed = hours_between(t_pickup, e_return)
            calc_note = f"{hours_elapsed:.1f} hours elapsed -> ceil({hours_elapsed:.1f}/24) = {raw_days} block(s)"
        else:  # calendar_day
            raw_days = calculate_calendar_days(t_pickup, e_return)
            calc_note = f"Calendar dates {t_pickup.date()} to {e_return.date()} -> {raw_days} calendar day(s)"

        free_days = int(terms.get("chassis_free_days", 0) or 0)
        min_days_val = terms.get("chassis_min_days")
        min_days = 2 if min_days_val is None else int(min_days_val)

        calc_days = max(0, raw_days - free_days)
        supported_days = max(calc_days, min_days)

        if min_days > calc_days:
            calc_note += f"; {min_days}-day drayage minimum applied (calculated {calc_days} day(s))"
        elif min_days > 0:
            calc_note += f"; meets {min_days}-day drayage minimum"

        if qty <= supported_days:
            approved_qty = qty
            disputed_qty = 0.0
            approved_amount = round(qty * expected_rate, 2)
            disputed_amount = round(amount - approved_amount, 2)
            status = STATUS_APPROVE
            reason = f"{int(qty)} day(s) (${approved_amount:.0f}) APPROVE. Supported by timeline ({calc_note})."
        else:
            approved_qty = float(supported_days)
            disputed_qty = float(qty - supported_days)
            approved_amount = round(approved_qty * expected_rate, 2)
            disputed_amount = round(disputed_qty * expected_rate, 2)
            # Add any rate/math excess to disputed
            extra_dispute = max(0.0, round(amount - (approved_amount + disputed_amount), 2))
            disputed_amount += extra_dispute
            status = STATUS_DISPUTE
            reason = (
                f"{int(approved_qty)} day(s) (${approved_amount:.0f}) APPROVE, "
                f"{int(disputed_qty)} day(s) (${disputed_amount:.0f}) DISPUTE. "
                f"Timeline supports {supported_days} day(s) under {chassis_policy} policy ({calc_note})."
            )

        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=expected_rate,
            approved_amount=approved_amount,
            disputed_amount=disputed_amount,
            needs_proof_amount=0.0,
            status=status,
            flags=flags,
            reason=reason,
            timestamps_used=timestamps_used,
            missing_items=missing_items,
            approved_qty=approved_qty,
            disputed_qty=disputed_qty,
            needs_proof_qty=0.0,
        )

    # Rule D: Yard Storage
    elif charge_type == "storage":
        y_in = parse_iso_timestamp(timeline.get("yard_in"))
        y_out = parse_iso_timestamp(timeline.get("yard_out"))
        t_pickup = parse_iso_timestamp(timeline.get("terminal_pickup"))
        d_actual = parse_iso_timestamp(timeline.get("delivery_actual"))

        storage_free_days = int(terms.get("storage_free_days", 0) or 0)
        prepull_includes_storage = terms.get("prepull_includes_first_storage_day")
        effective_storage_free_days = storage_free_days + (1 if prepull_includes_storage is True else 0)

        if y_in and y_out:
            timestamps_used = {
                "yard_in": y_in.isoformat(),
                "yard_out": y_out.isoformat(),
            }
            midnights = count_midnights_between(y_in, y_out)
            supported_days = max(0, midnights - effective_storage_free_days)
            if qty <= supported_days:
                approved_qty = qty
                disputed_qty = 0.0
                approved_amount = round(qty * expected_rate, 2)
                disputed_amount = round(amount - approved_amount, 2)
                status = STATUS_APPROVE
                reason = f"{int(qty)} day(s) supported by yard timestamps ({midnights} midnight(s) between {y_in} and {y_out})."
            else:
                approved_qty = float(supported_days)
                disputed_qty = float(qty - supported_days)
                approved_amount = round(approved_qty * expected_rate, 2)
                disputed_amount = round(disputed_qty * expected_rate, 2)
                status = STATUS_DISPUTE
                reason = (
                    f"{int(approved_qty)} day(s) (${approved_amount:.0f}) APPROVE, "
                    f"{int(disputed_qty)} day(s) (${disputed_amount:.0f}) DISPUTE. "
                    f"Yard timestamps support {supported_days} day(s)."
                )

            if prepull_includes_storage is True:
                reason += " Note: Pre-pull fee includes the first yard storage day."

            return LineAuditResult(
                type=charge_type,
                qty=qty,
                unit_rate=unit_rate,
                amount=amount,
                agreed_rate=expected_rate,
                approved_amount=approved_amount,
                disputed_amount=disputed_amount,
                needs_proof_amount=0.0,
                status=status,
                flags=flags,
                reason=reason,
                timestamps_used=timestamps_used,
                missing_items=[],
                approved_qty=approved_qty,
                disputed_qty=disputed_qty,
                needs_proof_qty=0.0,
            )

        # Missing yard timestamps -> calculate maximum possible storage
        missing_items.extend([
            "Yard-in and yard-out timestamps (proof of yard hold)",
            "Reason for yard hold / storage documentation",
        ])

        if t_pickup and d_actual:
            timestamps_used = {
                "terminal_pickup": t_pickup.isoformat(),
                "delivery_actual": d_actual.isoformat(),
            }
            max_midnights = count_midnights_between(t_pickup, d_actual)
            max_possible = max(0, max_midnights - effective_storage_free_days)
        else:
            max_possible = 0

        # Excess above max_possible is disputed; remaining within max_possible requires proof
        if qty > max_possible:
            disputed_qty = float(qty - max_possible)
            proof_qty = float(max_possible)
            disputed_amount = round(disputed_qty * expected_rate, 2)
            needs_proof_amount = round(proof_qty * expected_rate, 2)
            approved_amount = 0.0
            status = STATUS_DISPUTE
            reason_parts = [
                f"Maximum possible storage from pickup to delivery window is {max_possible} night(s).",
                f"{int(disputed_qty)} day(s) (${disputed_amount:.0f}) DISPUTE, "
                f"{int(proof_qty)} day(s) (${needs_proof_amount:.0f}) REQUIRE_PROOF."
            ]
        else:
            disputed_qty = 0.0
            proof_qty = float(qty)
            disputed_amount = 0.0
            needs_proof_amount = round(proof_qty * expected_rate, 2)
            approved_amount = 0.0
            status = STATUS_REQUIRE_PROOF
            reason_parts = [
                f"Storage billed is within maximum window of {max_possible} night(s), but yard timestamps are missing.",
                f"{int(proof_qty)} day(s) (${needs_proof_amount:.0f}) REQUIRE_PROOF."
            ]

        if prepull_includes_storage is None:
            reason_parts.append(
                "Note: Confirm whether the first storage day is already included in the pre-pull fee."
            )
        elif prepull_includes_storage is True:
            reason_parts.append(
                "Note: Pre-pull fee includes the first yard storage day per agreed terms."
            )

        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=expected_rate,
            approved_amount=approved_amount,
            disputed_amount=disputed_amount,
            needs_proof_amount=needs_proof_amount,
            status=status,
            flags=flags,
            reason=" ".join(reason_parts),
            timestamps_used=timestamps_used,
            missing_items=missing_items,
            approved_qty=0.0,
            disputed_qty=disputed_qty,
            needs_proof_qty=proof_qty,
        )

    # Rule E: Pre-pull
    elif charge_type == "prepull":
        y_in = parse_iso_timestamp(timeline.get("yard_in"))
        y_out = parse_iso_timestamp(timeline.get("yard_out"))
        prepull_req = timeline.get("prepull_request_documented")
        has_yard_drop = bool(y_in and y_out)
        has_request = bool(prepull_req is True)

        t_pickup = parse_iso_timestamp(timeline.get("terminal_pickup"))
        d_actual = parse_iso_timestamp(timeline.get("delivery_actual"))

        haul_type = resolve_haul_type(terms, timeline)

        if has_yard_drop or has_request:
            approved_amount = round(amount, 2)
            status = STATUS_APPROVE
            reason = "Approved. Pre-pull justified by yard drop evidence and/or documented pre-pull request."
            return LineAuditResult(
                type=charge_type,
                qty=qty,
                unit_rate=unit_rate,
                amount=amount,
                agreed_rate=expected_rate,
                approved_amount=approved_amount,
                disputed_amount=0.0,
                needs_proof_amount=0.0,
                status=status,
                flags=flags,
                reason=reason,
                timestamps_used={
                    "yard_in": y_in.isoformat() if y_in else None,
                    "yard_out": y_out.isoformat() if y_out else None,
                },
                missing_items=[],
                approved_qty=qty,
                disputed_qty=0.0,
                needs_proof_qty=0.0,
            )

        # Without yard drop or documented request:
        if haul_type == "short":
            # Short haul: pre-pull is expected and normal. APPROVE, with a note asking for written authorization if not documented.
            missing_items.append("Written pre-pull authorization from broker (requested for records)")
            reason = "Approved. On a short haul, pre-pull is expected and normal. Note: Written authorization requested for broker records."
            return LineAuditResult(
                type=charge_type,
                qty=qty,
                unit_rate=unit_rate,
                amount=amount,
                agreed_rate=expected_rate,
                approved_amount=round(amount, 2),
                disputed_amount=0.0,
                needs_proof_amount=0.0,
                status=STATUS_APPROVE,
                flags=flags,
                reason=reason,
                timestamps_used={},
                missing_items=missing_items,
                approved_qty=qty,
                disputed_qty=0.0,
                needs_proof_qty=0.0,
            )

        # Long haul: carriers usually do NOT charge a pre-pull when pickup is at night and delivery is next day.
        # If move is a direct move (pickup to delivery under direct_move_hours_threshold) and no written request is documented:
        # DISPUTE with reason "unusual on a long haul, carrier may submit proof"
        thresh = float(terms.get("direct_move_hours_threshold", 24) or 24)
        hrs = hours_between(t_pickup, d_actual) if (t_pickup and d_actual) else None
        is_direct_move = (hrs is not None and hrs < thresh)

        if is_direct_move:
            status = STATUS_DISPUTE
            disputed_amount = round(amount, 2)
            reason = (
                f"DISPUTE: unusual on a long haul, carrier may submit proof. "
                f"Direct move ({hrs:.1f}h pickup-to-delivery < {thresh:.0f}h threshold) with night pickup and next-day delivery; "
                f"no written pre-pull authorization or yard drop documented."
            )
            missing_items.extend([
                "Yard-in and yard-out timestamps (proof of yard drop)",
                "Proof early pull was requested by broker/customer",
            ])
            return LineAuditResult(
                type=charge_type,
                qty=qty,
                unit_rate=unit_rate,
                amount=amount,
                agreed_rate=expected_rate,
                approved_amount=0.0,
                disputed_amount=disputed_amount,
                needs_proof_amount=0.0,
                status=status,
                flags=flags,
                reason=reason,
                timestamps_used={
                    "terminal_pickup": t_pickup.isoformat() if t_pickup else None,
                    "delivery_actual": d_actual.isoformat() if d_actual else None,
                },
                missing_items=missing_items,
                approved_qty=0.0,
                disputed_qty=qty,
                needs_proof_qty=0.0,
            )

        # Long haul but not direct move or missing timestamps: REQUIRE_PROOF
        missing_items.extend([
            "Yard-in and yard-out timestamps (proof of yard drop)",
            "Proof early pull was requested by broker/customer",
            "Terminal last free day (LFD) record",
        ])
        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=expected_rate,
            approved_amount=0.0,
            disputed_amount=0.0,
            needs_proof_amount=round(amount, 2),
            status=STATUS_REQUIRE_PROOF,
            flags=flags,
            reason="REQUIRE_PROOF: Pre-pull requires proof of a yard drop or documented broker/customer authorization.",
            timestamps_used={
                "terminal_pickup": t_pickup.isoformat() if t_pickup else None,
                "delivery_actual": d_actual.isoformat() if d_actual else None,
            },
            missing_items=missing_items,
            approved_qty=0.0,
            disputed_qty=0.0,
            needs_proof_qty=qty,
        )

    # Rule F: Detention
    elif charge_type == "detention":
        w_in = parse_iso_timestamp(timeline.get("warehouse_in"))
        w_out = parse_iso_timestamp(timeline.get("warehouse_out"))

        if not w_in or not w_out:
            if not w_in:
                missing_items.append("Warehouse arrival timestamp (warehouse_in)")
            if not w_out:
                missing_items.append("Warehouse departure timestamp (warehouse_out)")
            return LineAuditResult(
                type=charge_type,
                qty=qty,
                unit_rate=unit_rate,
                amount=amount,
                agreed_rate=expected_rate,
                approved_amount=0.0,
                disputed_amount=0.0,
                needs_proof_amount=amount,
                status=STATUS_REQUIRE_PROOF,
                flags=flags,
                reason="Detention billed requires warehouse arrival and departure timestamps or signed driver timesheet.",
                timestamps_used={
                    "warehouse_in": timeline.get("warehouse_in"),
                    "warehouse_out": timeline.get("warehouse_out"),
                },
                missing_items=missing_items,
                approved_qty=0.0,
                disputed_qty=0.0,
                needs_proof_qty=qty,
            )

        duration = hours_between(w_in, w_out)
        free_hrs = float(terms.get("detention_free_hours", 2) or 2)
        billable_hrs = max(0.0, round(duration - free_hrs, 2))
        timestamps_used = {
            "warehouse_in": w_in.isoformat(),
            "warehouse_out": w_out.isoformat(),
        }

        if qty <= billable_hrs:
            approved_amount = round(qty * expected_rate, 2)
            disputed_amount = round(amount - approved_amount, 2)
            status = STATUS_APPROVE
            reason = (
                f"{qty:.2f} hrs (${approved_amount:.2f}) APPROVE. "
                f"{duration:.2f} hrs on site minus {free_hrs:.1f} free hrs supports {billable_hrs:.2f} billable hrs."
            )
            approved_qty = qty
            disputed_qty = 0.0
        else:
            approved_qty = billable_hrs
            disputed_qty = round(qty - billable_hrs, 2)
            approved_amount = round(approved_qty * expected_rate, 2)
            disputed_amount = round(disputed_qty * expected_rate, 2)
            # Add any math/rate excess
            extra_dispute = max(0.0, round(amount - (approved_amount + disputed_amount), 2))
            disputed_amount += extra_dispute
            status = STATUS_DISPUTE
            reason = (
                f"{approved_qty:.2f} hrs (${approved_amount:.2f}) APPROVE, "
                f"{disputed_qty:.2f} hrs (${disputed_amount:.2f}) DISPUTE. "
                f"Warehouse duration ({duration:.2f}h - {free_hrs:.1f}h free) supports {billable_hrs:.2f} billable hrs."
            )

        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=expected_rate,
            approved_amount=approved_amount,
            disputed_amount=disputed_amount,
            needs_proof_amount=0.0,
            status=status,
            flags=flags,
            reason=reason,
            timestamps_used=timestamps_used,
            missing_items=missing_items,
            approved_qty=approved_qty,
            disputed_qty=disputed_qty,
            needs_proof_qty=0.0,
        )

    # Generic or unknown charge type in terms
    else:
        # If rate matches and math matches
        approved_amount = round(qty * expected_rate, 2)
        disputed_amount = max(0.0, round(amount - approved_amount, 2))
        status = STATUS_APPROVE if disputed_amount == 0 else STATUS_DISPUTE
        return LineAuditResult(
            type=charge_type,
            qty=qty,
            unit_rate=unit_rate,
            amount=amount,
            agreed_rate=expected_rate,
            approved_amount=approved_amount,
            disputed_amount=disputed_amount,
            needs_proof_amount=0.0,
            status=status,
            flags=flags,
            reason=f"Charge '{charge_type}' audited against agreed rate ${expected_rate:.2f}.",
            timestamps_used={},
            missing_items=[],
            approved_qty=qty if disputed_amount == 0 else 0.0,
            disputed_qty=0.0 if disputed_amount == 0 else qty,
            needs_proof_qty=0.0,
        )


def audit_invoice(
    invoice: Dict[str, Any],
    terms: Dict[str, Any],
    timeline: Dict[str, Any],
    override_policy: Optional[str] = None,
) -> AuditResult:
    """Run deterministic audit against an invoice using agreed terms and container timeline."""
    configured_policy = terms.get("chassis_day_policy")
    effective_policy = override_policy or configured_policy

    # If policy is null and no override was specified, compute both side-by-side
    if effective_policy is None:
        result_cal = audit_invoice(invoice, terms, timeline, override_policy="calendar_day")
        result_24h = audit_invoice(invoice, terms, timeline, override_policy="24h_block")
        result_cal.policy_used = "null (showing calendar_day vs 24h_block)"
        result_cal.summary.is_provisional = True
        result_cal.alternative_policy_result = result_24h.to_dict()
        result_cal.notes.append(
            "Chassis day policy is unknown in terms.json. Both 'calendar_day' and '24h_block' policies were calculated."
        )
        return result_cal

    lines_data = invoice.get("lines", [])
    invoice_total = float(invoice.get("total", 0.0))

    audited_lines: List[LineAuditResult] = []
    seen_types = set()
    all_flags: List[str] = []

    sum_line_amounts = 0.0
    for line in lines_data:
        res = _audit_single_line(line, terms, timeline, effective_policy, seen_types)
        seen_types.add(res.type)
        audited_lines.append(res)
        sum_line_amounts += res.amount
        all_flags.extend(res.flags)

    # Check for detention billed or not billed
    has_detention = any(line_item.type == "detention" for line_item in audited_lines)
    notes: List[str] = []
    if not has_detention:
        notes.append("Detention: NOT_BILLED on this invoice.")

    # Rule A: Check invoice total vs sum of line amounts
    if abs(sum_line_amounts - invoice_total) > 0.01:
        all_flags.append(FLAG_TOTAL_MISMATCH)

    # Compute overall summary
    total_billed = round(sum_line_amounts, 2)
    approved_amount = round(sum(line_item.approved_amount for line_item in audited_lines), 2)
    disputed_amount = round(sum(line_item.disputed_amount for line_item in audited_lines), 2)
    needs_proof_amount = round(sum(line_item.needs_proof_amount for line_item in audited_lines), 2)
    not_approved_amount = round(disputed_amount + needs_proof_amount, 2)

    # Check provisional conditions:
    # 1. Needs proof > 0
    # 2. POD not provided
    # 3. Policy unknown / null
    is_provisional = (
        (needs_proof_amount > 0)
        or (not bool(timeline.get("pod_provided", False)))
        or (terms.get("chassis_day_policy") is None)
    )

    # Collect deduplicated missing documents
    documents_needed: List[str] = []
    for line in audited_lines:
        for item in line.missing_items:
            if item not in documents_needed:
                documents_needed.append(item)

    # Special note if prepull_includes_first_storage_day is null
    if terms.get("prepull_includes_first_storage_day") is None:
        note_str = "Clarify whether agreed pre-pull fee includes the first yard storage day (terms.prepull_includes_first_storage_day is null)."
        if note_str not in documents_needed:
            documents_needed.append(note_str)

    unique_flags = list(dict.fromkeys(all_flags))

    summary = AuditSummary(
        total_billed=total_billed,
        approved_amount=approved_amount,
        is_provisional=is_provisional,
        disputed_amount=disputed_amount,
        needs_proof_amount=needs_proof_amount,
        not_approved_amount=not_approved_amount,
        flags=unique_flags,
    )

    return AuditResult(
        policy_used=effective_policy,
        lines=audited_lines,
        summary=summary,
        documents_needed=documents_needed,
        notes=notes,
    )
