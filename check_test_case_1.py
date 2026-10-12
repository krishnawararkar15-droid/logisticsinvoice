"""Verification script for Test Case 1."""

import json
from pathlib import Path
from src.rules import audit_invoice

def run_checks():
    terms_path = Path("sample_data/terms.json")
    timeline_path = Path("sample_data/timeline.json")
    invoice_path = Path("sample_data/invoice.json")

    with open(terms_path, "r", encoding="utf-8") as f:
        terms = json.load(f)
    with open(timeline_path, "r", encoding="utf-8") as f:
        timeline = json.load(f)
    with open(invoice_path, "r", encoding="utf-8") as f:
        invoice = json.load(f)

    print("=" * 60)
    print("TEST CASE 1: CALENDAR DAY POLICY")
    print("=" * 60)
    result_cal = audit_invoice(invoice, terms, timeline, override_policy="calendar_day")
    
    for line in result_cal.lines:
        print(f"Line: {line.type:12} | Billed: ${line.amount:6.2f} | Approved: ${line.approved_amount:6.2f} | Disputed: ${line.disputed_amount:6.2f} | Needs Proof: ${line.needs_proof_amount:6.2f} | Status: {line.status}")
        print(f"   Reason: {line.reason}")
        if line.missing_items:
            print(f"   Missing: {', '.join(line.missing_items)}")

    s_cal = result_cal.summary
    print("-" * 60)
    print(f"Total Billed:  ${s_cal.total_billed:,.2f}")
    print(f"Approved:      ${s_cal.approved_amount:,.2f} {'(PROVISIONAL)' if s_cal.is_provisional else ''}")
    print(f"Disputed:      ${s_cal.disputed_amount:,.2f}")
    print(f"Needs Proof:   ${s_cal.needs_proof_amount:,.2f}")
    print(f"Not Approved:  ${s_cal.not_approved_amount:,.2f}")
    print("=" * 60)

    # Assertions for calendar_day
    assert s_cal.total_billed == 1875.0, f"Expected 1875, got {s_cal.total_billed}"
    assert s_cal.approved_amount == 1590.0, f"Expected 1590, got {s_cal.approved_amount}"
    assert s_cal.disputed_amount == 90.0, f"Expected 90, got {s_cal.disputed_amount}"
    assert s_cal.needs_proof_amount == 195.0, f"Expected 195, got {s_cal.needs_proof_amount}"
    assert s_cal.not_approved_amount == 285.0, f"Expected 285, got {s_cal.not_approved_amount}"
    assert s_cal.is_provisional is True, "Expected provisional approval"

    print("\n" + "=" * 60)
    print("TEST CASE 1: 24-HOUR BLOCK POLICY")
    print("=" * 60)
    result_24h = audit_invoice(invoice, terms, timeline, override_policy="24h_block")
    for line in result_24h.lines:
        print(f"Line: {line.type:12} | Billed: ${line.amount:6.2f} | Approved: ${line.approved_amount:6.2f} | Disputed: ${line.disputed_amount:6.2f} | Needs Proof: ${line.needs_proof_amount:6.2f} | Status: {line.status}")
        print(f"   Reason: {line.reason}")

    s_24h = result_24h.summary
    print("-" * 60)
    print(f"Total Billed:  ${s_24h.total_billed:,.2f}")
    print(f"Approved:      ${s_24h.approved_amount:,.2f} {'(PROVISIONAL)' if s_24h.is_provisional else ''}")
    print(f"Disputed:      ${s_24h.disputed_amount:,.2f}")
    print(f"Needs Proof:   ${s_24h.needs_proof_amount:,.2f}")
    print(f"Not Approved:  ${s_24h.not_approved_amount:,.2f}")
    print("=" * 60)

    # Assertions for 24h_block
    assert s_24h.total_billed == 1875.0, f"Expected 1875, got {s_24h.total_billed}"
    assert s_24h.approved_amount == 1545.0, f"Expected 1545, got {s_24h.approved_amount}"
    assert s_24h.disputed_amount == 135.0, f"Expected 135, got {s_24h.disputed_amount}"
    assert s_24h.needs_proof_amount == 195.0, f"Expected 195, got {s_24h.needs_proof_amount}"
    assert s_24h.not_approved_amount == 330.0, f"Expected 330, got {s_24h.not_approved_amount}"
    assert s_24h.is_provisional is True, "Expected provisional approval"

    # Test report generation
    from src.report import generate_report_files
    report_files = generate_report_files(result_cal, output_dir="output")
    for key, path in report_files.items():
        assert path.exists(), f"File {path} was not created"
        print(f"Generated {key}: {path} ({path.stat().st_size} bytes)")

    # Verify report.md contains key required sentences
    report_text = report_files["report_md"].read_text(encoding="utf-8")
    assert "Final approval decision belongs to the broker." in report_text, "Missing broker final approval statement"
    assert "Documents Needed Before Final Approval Checklist" in report_text, "Missing checklist"
    print("Report validation passed: required disclaimers and checklists confirmed!")

    print("\n" + "=" * 60)
    print("TEST CASE 1: NULL POLICY (BOTH SCENARIOS SIDE BY SIDE)")
    print("=" * 60)
    terms_null = dict(terms)
    terms_null["chassis_day_policy"] = None
    result_null = audit_invoice(invoice, terms_null, timeline)
    assert result_null.alternative_policy_result is not None, "Expected alternative policy result"
    print("Null policy correctly returned side-by-side results!")
    print("ALL ASSERTIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_checks()
