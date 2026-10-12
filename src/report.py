"""Report generation module for Accessorial Invoice Checker (v1).

Produces:
- report.md: Human-readable markdown audit report with math, timestamps, and checklist.
- result.json: Structured machine-readable JSON data.
- result.csv: Line-by-line spreadsheet CSV.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.rules import AuditResult


def format_currency(amount: Optional[float]) -> str:
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"


def build_markdown_report(result: AuditResult) -> str:
    summary = result.summary
    prov_label = " (PROVISIONAL)" if summary.is_provisional else ""

    md_lines: List[str] = [
        "# Accessorial Invoice Audit Report",
        "",
        f"**Chassis Day Policy Applied:** `{result.policy_used}`  ",
        f"**Audit Status:** {'⚠️ Provisional Approval (Documentation / Clarification Required)' if summary.is_provisional else '✅ Final Approval Ready'}  ",
        "",
        "---",
        "",
        "## 1. Executive Financial Summary",
        "",
        "| Metric | Amount | Description |",
        "| :--- | :--- | :--- |",
        f"| **Total Billed** | **{format_currency(summary.total_billed)}** | Total amount billed by carrier on invoice |",
        f"| **Approved{prov_label}** | **{format_currency(summary.approved_amount)}** | Amount verified against contract & timeline |",
        f"| **Disputed** | **{format_currency(summary.disputed_amount)}** | Amount rejected due to excess days or contract discrepancies |",
        f"| **Needs Proof** | **{format_currency(summary.needs_proof_amount)}** | Amount held pending carrier documentation |",
        f"| **Total Not Approved** | **{format_currency(summary.not_approved_amount)}** | Total withheld by broker (Disputed + Needs Proof) |",
        "",
    ]

    if summary.flags:
        md_lines.append(f"> [!WARNING]\n> **Invoice Flags Detected:** {', '.join(f'`{fl}`' for fl in summary.flags)}")
        md_lines.append("")

    # If alternative policy comparison is available (e.g. policy was null)
    if result.alternative_policy_result:
        alt = result.alternative_policy_result
        alt_sum = alt.get("summary", {})
        md_lines.extend([
            "### Policy Comparison (Calendar Day vs 24-Hour Block)",
            "",
            "Because `chassis_day_policy` was unspecified, both scenarios are evaluated:",
            "",
            "| Policy | Total Billed | Approved | Disputed | Needs Proof | Not Approved |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
            f"| **Calendar Day** | {format_currency(summary.total_billed)} | {format_currency(summary.approved_amount)} | {format_currency(summary.disputed_amount)} | {format_currency(summary.needs_proof_amount)} | {format_currency(summary.not_approved_amount)} |",
            f"| **24-Hour Block** | {format_currency(alt_sum.get('total_billed'))} | {format_currency(alt_sum.get('approved_amount'))} | {format_currency(alt_sum.get('disputed_amount'))} | {format_currency(alt_sum.get('needs_proof_amount'))} | {format_currency(alt_sum.get('not_approved_amount'))} |",
            "",
        ])

    md_lines.extend([
        "---",
        "",
        "## 2. Line-by-Line Audit Breakdown",
        "",
    ])

    for idx, line in enumerate(result.lines, 1):
        status_icon = "✅" if line.status == "APPROVE" else ("❌" if line.status == "DISPUTE" else "⚠️")
        md_lines.extend([
            f"### Line {idx}: `{line.type}` — {status_icon} **{line.status}**",
            "",
            f"- **Billed:** {line.qty:g} @ {format_currency(line.unit_rate)} = **{format_currency(line.amount)}**",
            f"- **Contract Agreed Rate:** {format_currency(line.agreed_rate) if line.agreed_rate is not None else 'N/A'}",
            "- **Audit Breakdown:**",
            f"  - Approved: **{format_currency(line.approved_amount)}**",
            f"  - Disputed: **{format_currency(line.disputed_amount)}**",
            f"  - Needs Proof: **{format_currency(line.needs_proof_amount)}**",
            f"- **Audit Finding & Math:** {line.reason}",
        ])

        if line.flags:
            md_lines.append(f"- **Flags:** {', '.join(f'`{fl}`' for fl in line.flags)}")

        if line.timestamps_used:
            ts_str = ", ".join(f"`{k}`: {v}" for k, v in line.timestamps_used.items() if v)
            md_lines.append(f"- **Timestamps Used:** {ts_str}")

        if line.missing_items:
            md_lines.append(f"- **Missing Documentation:** {'; '.join(line.missing_items)}")

        md_lines.append("")

    if result.notes:
        md_lines.extend([
            "---",
            "",
            "## 3. General Notes",
            "",
        ])
        for note in result.notes:
            md_lines.append(f"- {note}")
        md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 4. Documents Needed Before Final Approval Checklist",
        "",
    ])

    if result.documents_needed:
        for doc in result.documents_needed:
            md_lines.append(f"- [ ] {doc}")
    else:
        md_lines.append("All required documents and timestamps were provided. No outstanding items.")

    md_lines.extend([
        "",
        "---",
        "",
        "> [!IMPORTANT]",
        "> **Final approval decision belongs to the broker.**",
        "",
    ])

    return "\n".join(md_lines)


def build_csv_report(result: AuditResult) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Header
    writer.writerow([
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
    ])

    for line in result.lines:
        writer.writerow([
            line.type,
            line.qty,
            line.unit_rate,
            line.amount,
            line.agreed_rate if line.agreed_rate is not None else "",
            line.approved_amount,
            line.disputed_amount,
            line.needs_proof_amount,
            line.status,
            "; ".join(line.flags),
            line.reason,
            "; ".join(line.missing_items),
        ])

    # Summary Row
    summary = result.summary
    writer.writerow([])
    writer.writerow(["TOTALS", "", "", summary.total_billed, "", summary.approved_amount, summary.disputed_amount, summary.needs_proof_amount, "PROVISIONAL" if summary.is_provisional else "FINAL", "", f"Not Approved: ${summary.not_approved_amount:.2f}", ""])

    return output.getvalue()


def generate_report_files(
    result: AuditResult, output_dir: Union[str, Path] = "output"
) -> Dict[str, Path]:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    md_file = out_path / "report.md"
    json_file = out_path / "result.json"
    csv_file = out_path / "result.csv"

    # Write report.md
    md_content = build_markdown_report(result)
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Write result.json
    json_content = json.dumps(result.to_dict(), indent=2)
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(json_content)

    # Write result.csv
    csv_content = build_csv_report(result)
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)

    return {
        "report_md": md_file,
        "result_json": json_file,
        "result_csv": csv_file,
    }


# Convenient alias
generate_reports = generate_report_files

