"""Batch Audit Engine for Accessorial Invoices.

Processes multiple carrier invoices in a batch, executes deterministic
auditing rules against agreed rate sheets and timeline timestamps,
and compiles executive-level portfolio summaries and itemized findings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.rules import AuditResult, audit_invoice


def _normalize_terms(terms: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize terms dictionary keys and values for audit engine."""
    if not terms:
        return {}
    t = dict(terms)
    if t.get("chassis_day_policy") == "unknown":
        t["chassis_day_policy"] = None
    if t.get("prepull_includes_first_storage_day") == "unknown":
        t["prepull_includes_first_storage_day"] = None
    elif t.get("prepull_includes_first_storage_day") in ("yes", True):
        t["prepull_includes_first_storage_day"] = True
    elif t.get("prepull_includes_first_storage_day") in ("no", False):
        t["prepull_includes_first_storage_day"] = False
    return t


def _normalize_timeline(timeline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize timeline timestamps and flags for audit engine."""
    if not timeline:
        return {}
    tl = dict(timeline)
    if tl.get("prepull_request_documented") == "unknown":
        tl["prepull_request_documented"] = None
    elif tl.get("prepull_request_documented") in ("yes", True):
        tl["prepull_request_documented"] = True
    elif tl.get("prepull_request_documented") in ("no", False):
        tl["prepull_request_documented"] = False
    return tl


def batch_audit_invoices(
    invoices: List[Dict[str, Any]],
    terms: Dict[str, Any],
    timeline: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Audit multiple carrier invoices against agreed terms and container timelines.

    Args:
        invoices: List of invoice dictionaries. Each item may be:
                  - A direct invoice dictionary with 'lines' and optional 'total' / 'id' / 'invoice_id'.
                  - An enveloped dictionary with 'invoice': {...}, and optional per-invoice 'terms' / 'timeline'.
        terms: Default agreed contract terms.
        timeline: Default operational timeline timestamps.

    Returns:
        Dictionary containing:
        - 'batch_summary': Aggregated executive metrics across all invoices.
        - 'invoices': Itemized list of audited invoices with index, id, summary, lines, and documents_needed.
    """
    default_terms = _normalize_terms(terms)
    default_timeline = _normalize_timeline(timeline)

    audited_invoices: List[Dict[str, Any]] = []

    total_billed = 0.0
    total_approved = 0.0
    total_disputed = 0.0
    total_needs_proof = 0.0
    total_not_approved = 0.0
    clean_invoices_count = 0
    disputed_invoices_count = 0

    for idx, item in enumerate(invoices):
        # Extract invoice payload, per-invoice terms & timeline if present
        if isinstance(item, dict) and "invoice" in item and isinstance(item["invoice"], dict):
            inv_data = dict(item["invoice"])
            inv_terms = _normalize_terms(item.get("terms")) if item.get("terms") else default_terms
            inv_timeline = _normalize_timeline(item.get("timeline")) if item.get("timeline") else default_timeline
            invoice_id = (
                item.get("invoice_id")
                or item.get("id")
                or item.get("invoice_number")
                or inv_data.get("invoice_id")
                or inv_data.get("id")
                or inv_data.get("invoice_number")
                or f"INV-{idx + 1:03d}"
            )
        else:
            inv_data = dict(item) if isinstance(item, dict) else {}
            inv_terms = default_terms
            inv_timeline = default_timeline
            invoice_id = (
                inv_data.get("invoice_id")
                or inv_data.get("id")
                or inv_data.get("invoice_number")
                or f"INV-{idx + 1:03d}"
            )

        # Run deterministic rules engine
        audit_res: AuditResult = audit_invoice(inv_data, inv_terms, inv_timeline)
        res_dict = audit_res.to_dict()
        summary_dict = res_dict["summary"]

        inv_billed = float(summary_dict["total_billed"])
        inv_approved = float(summary_dict["approved_amount"])
        inv_disputed = float(summary_dict["disputed_amount"])
        inv_needs_proof = float(summary_dict["needs_proof_amount"])
        inv_not_approved = float(summary_dict["not_approved_amount"])

        # Tally metrics
        total_billed += inv_billed
        total_approved += inv_approved
        total_disputed += inv_disputed
        total_needs_proof += inv_needs_proof
        total_not_approved += inv_not_approved

        # Clean invoice: 0 disputes and 0 needs proof
        if inv_disputed == 0.0 and inv_needs_proof == 0.0:
            clean_invoices_count += 1
        else:
            disputed_invoices_count += 1

        carrier_name = (
            item.get("carrier_name")
            or inv_data.get("carrier_name")
            or (item.get("metadata", {}).get("carrier_name") if isinstance(item.get("metadata"), dict) else None)
            or "Pacific Gateway Drayage LLC"
        )
        container_no = (
            item.get("container_no")
            or inv_data.get("container_no")
            or (item.get("metadata", {}).get("container_no") if isinstance(item.get("metadata"), dict) else None)
            or f"CONT-{idx + 1:04d}"
        )
        bol_no = (
            item.get("bol_no")
            or inv_data.get("bol_no")
            or (item.get("metadata", {}).get("bol_no") if isinstance(item.get("metadata"), dict) else None)
            or f"BOL-{idx + 1:04d}"
        )

        invoice_entry: Dict[str, Any] = {
            "invoice_index": idx,
            "invoice_id": str(invoice_id),
            "carrier_name": str(carrier_name),
            "container_no": str(container_no),
            "bol_no": str(bol_no),
            "summary": summary_dict,
            "lines": res_dict["lines"],
            "documents_needed": res_dict["documents_needed"],
            "notes": res_dict.get("notes", []),
            "policy_used": res_dict.get("policy_used", ""),
        }
        if "alternative_policy_result" in res_dict:
            invoice_entry["alternative_policy_result"] = res_dict["alternative_policy_result"]

        audited_invoices.append(invoice_entry)

    total_invoices_audited = len(invoices)
    total_billed = round(total_billed, 2)
    total_approved = round(total_approved, 2)
    total_disputed = round(total_disputed, 2)
    total_needs_proof = round(total_needs_proof, 2)
    total_not_approved = round(total_not_approved, 2)
    total_dollars_saved = round(total_disputed + total_needs_proof, 2)

    batch_summary = {
        "total_invoices_audited": total_invoices_audited,
        "total_billed": total_billed,
        "total_approved": total_approved,
        "total_disputed": total_disputed,
        "total_needs_proof": total_needs_proof,
        "total_not_approved": total_not_approved,
        "total_dollars_saved": total_dollars_saved,
        "clean_invoices_count": clean_invoices_count,
        "disputed_invoices_count": disputed_invoices_count,
    }

    return {
        "batch_summary": batch_summary,
        "invoices": audited_invoices,
    }
