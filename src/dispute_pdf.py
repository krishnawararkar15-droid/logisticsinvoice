"""
RateGuard AI - Formal Dispute Packet & Debit Memo PDF Generator.

Generates an official, vector PDF dispute packet and debit memo for freight brokers
under UIIA and broker-carrier contract terms using fpdf2.

Sections:
1. Header: "PREMIER FREIGHT LOGISTICS — DRAYAGE AUDIT & DISPUTE NOTICE"
2. Carrier & Shipment Info Box: Carrier Name, MC/DOT#, Invoice #, Container #, BOL Ref, Audit Date
3. Executive Financial Summary: Total Billed, Approved for Remittance, Total Withheld (Disputed & Needs Proof)
4. Itemized Audit Table: Item Type, Billed, Approved, Disputed, Needs Proof, Status Badge, Finding / Reason
5. Real-World Required Documents Checklist: Signed POD, Interchange Tickets (EIR), Yard Tickets, Pre-pull Auth
6. Remittance Instructions & Accounts Payable Authorized Signature Line
7. Disclaimer: "Final approval decision belongs to the broker. This document represents a formal debit memo / audit statement under UIIA and broker-carrier contract terms."
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from fpdf import FPDF
from fpdf.fonts import FontFace


def _clean_pdf_text(text: Any) -> str:
    """
    Sanitize text for standard FPDF core fonts (latin-1).
    Replaces unicode dashes, curly quotes, and unsupported symbols.
    """
    if text is None:
        return ""
    s = str(text)
    s = s.replace("\u2014", " - ").replace("\u2013", "-")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2022", "*").replace("\u25cf", "*")
    return s.encode("latin-1", "replace").decode("latin-1")


def _fmt_money(val: Any) -> str:
    """Format numeric values as USD currency strings."""
    if val is None:
        return "$0.00"
    try:
        f = float(val)
        return f"${f:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


class DisputePacketPDF(FPDF):
    """Custom FPDF document with official corporate header and statutory UIIA footer."""

    def __init__(self, broker_name: str = "Premier Freight Logistics LLC"):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.broker_name = broker_name
        self.set_auto_page_break(auto=True, margin=18)

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(71, 85, 105)
            running_title = f"{self.broker_name.upper()} - DRAYAGE AUDIT & DISPUTE NOTICE (CONT.)"
            self.cell(0, 5, _clean_pdf_text(running_title), align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(203, 213, 225)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 205, self.get_y())
            self.ln(3)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(100, 116, 139)
        disclaimer_text = (
            "Final approval decision belongs to the broker. "
            "This document represents a formal debit memo / audit statement under UIIA and broker-carrier contract terms."
        )
        self.cell(0, 4, _clean_pdf_text(disclaimer_text), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 7.5)
        self.cell(0, 4, f"Page {self.page_no()} of {{nb}}  |  Audit Notice & Debit Memo", align="C")


def generate_dispute_packet_pdf(
    audit_data: Union[Dict[str, Any], Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Generate a formal vector PDF Dispute Packet & Debit Memo.

    Args:
        audit_data: Audit results dictionary (or AuditResult instance) containing
                    summary, lines, documents_needed, etc.
        metadata: Optional dictionary with shipment details:
                  carrier_name, mc_dot, invoice_no, container_no, bol_no, audit_date, broker_name, load_id.

    Returns:
        bytes: Raw PDF bytes starting with b"%PDF-".
    """
    # ---------------------------------------------------------
    # 1. Normalize Audit Data & Metadata
    # ---------------------------------------------------------
    if hasattr(audit_data, "to_dict"):
        data = audit_data.to_dict()
    elif isinstance(audit_data, dict):
        data = audit_data
    else:
        raise TypeError(f"Expected dict or AuditResult, got {type(audit_data)}")

    meta: Dict[str, Any] = dict(metadata or {})
    if not meta and isinstance(data.get("metadata"), dict):
        meta = data["metadata"]

    summary = data.get("summary", {})
    if hasattr(summary, "to_dict"):
        summary = summary.to_dict()

    total_billed = float(summary.get("total_billed", data.get("total_billed", 0.0)) or 0.0)
    approved_amount = float(summary.get("approved_amount", data.get("approved_amount", 0.0)) or 0.0)
    disputed_amount = float(summary.get("disputed_amount", data.get("disputed_amount", 0.0)) or 0.0)
    needs_proof_amount = float(summary.get("needs_proof_amount", data.get("needs_proof_amount", 0.0)) or 0.0)
    not_approved_amount = float(
        summary.get("not_approved_amount", data.get("not_approved_amount", disputed_amount + needs_proof_amount))
        or (disputed_amount + needs_proof_amount)
    )

    policy_used = data.get("policy_used", "calendar_day")
    raw_lines: List[Any] = data.get("lines", [])
    documents_needed: List[str] = list(data.get("documents_needed", []))

    # Shipment Metadata fields
    carrier_name = meta.get("carrier_name") or "Pacific Gateway Drayage LLC"
    mc_dot = meta.get("mc_dot") or "MC# 892341 | DOT# 2948190"
    invoice_no = meta.get("invoice_no") or meta.get("invoice_id") or "INV-2026-0842"
    container_no = meta.get("container_no") or meta.get("container_id") or "TCLU 582910-3"
    bol_no = meta.get("bol_no") or meta.get("bol_ref") or "MEDU 91823901"
    load_id = meta.get("load_id") or meta.get("order_no") or "LD-88210"
    audit_date = meta.get("audit_date") or datetime.date.today().strftime("%B %d, %Y")
    broker_name = meta.get("broker_name") or "Premier Freight Logistics LLC"

    # ---------------------------------------------------------
    # 2. Build PDF Document
    # ---------------------------------------------------------
    pdf = DisputePacketPDF(broker_name=broker_name)
    pdf.add_page()

    # SECTION 1: HEADER
    # Title: PREMIER FREIGHT LOGISTICS - DRAYAGE AUDIT & DISPUTE NOTICE
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.set_text_color(26, 54, 93)  # Navy blue (#1A365D)
    pdf.cell(0, 6.5, "PREMIER FREIGHT LOGISTICS - DRAYAGE AUDIT & DISPUTE NOTICE", align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(185, 28, 28)  # Crimson accent
    pdf.cell(100, 5, "FORMAL DISPUTE PACKET & DEBIT MEMO", new_x="RIGHT")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 116, 139)
    ref_str = f"Debit Memo Ref: DM-{invoice_no}  |  Date: {_clean_pdf_text(audit_date)}"
    pdf.cell(95, 5, _clean_pdf_text(ref_str), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(100, 116, 139)
    contact_str = f"{broker_name} | Drayage Accessorial Audit & Compliance Division | disputes@premierfreightlogistics.com"
    pdf.cell(0, 4, _clean_pdf_text(contact_str), align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(26, 54, 93)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y() + 1.5, 205, pdf.get_y() + 1.5)
    pdf.ln(4)

    # SECTION 2: CARRIER & SHIPMENT INFO BOX (Dual-Card Box)
    box_y = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.3)
    pdf.rect(10, box_y, 95, 34, "DF")
    pdf.rect(110, box_y, 95, 34, "DF")

    # Left Box: Carrier Information
    pdf.set_xy(13, box_y + 2.5)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(89, 4, "CARRIER & INVOICE IDENTIFICATION", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(13)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(26, 4.5, "Carrier Name:", new_x="RIGHT")
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(63, 4.5, _clean_pdf_text(carrier_name), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(13)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(26, 4.5, "MC / DOT #:", new_x="RIGHT")
    pdf.cell(63, 4.5, _clean_pdf_text(mc_dot), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(13)
    pdf.cell(26, 4.5, "Invoice #:", new_x="RIGHT")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(63, 4.5, _clean_pdf_text(invoice_no), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(13)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(26, 4.5, "Audit Date:", new_x="RIGHT")
    pdf.cell(63, 4.5, _clean_pdf_text(audit_date), new_x="LMARGIN", new_y="NEXT")

    # Right Box: Shipment Details
    pdf.set_xy(113, box_y + 2.5)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(89, 4, "SHIPMENT & CONTAINER DETAILS", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(113)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(26, 4.5, "Container #:", new_x="RIGHT")
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(63, 4.5, _clean_pdf_text(container_no), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(113)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(26, 4.5, "BOL Reference:", new_x="RIGHT")
    pdf.cell(63, 4.5, _clean_pdf_text(bol_no), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(113)
    pdf.cell(26, 4.5, "Load / Order Ref:", new_x="RIGHT")
    pdf.cell(63, 4.5, _clean_pdf_text(load_id), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(113)
    pdf.cell(26, 4.5, "Audit Policy:", new_x="RIGHT")
    pdf.cell(63, 4.5, _clean_pdf_text(f"{policy_used} (Contract Agreed)"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(box_y + 38)

    # SECTION 3: EXECUTIVE FINANCIAL SUMMARY
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 5, "EXECUTIVE FINANCIAL SUMMARY", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    card_y = pdf.get_y()
    card_w = 62.5
    gap = 3.5

    # Card 1: Total Billed
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, card_y, card_w, 20, "DF")
    pdf.set_xy(10, card_y + 2.5)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w, 4, "TOTAL BILLED ON INVOICE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(card_w, 7, _fmt_money(total_billed), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w, 4, f"{len(raw_lines)} Accessorial Line Items", align="C")

    # Card 2: Approved for Remittance
    pdf.set_fill_color(240, 253, 244)  # Light green
    pdf.set_draw_color(187, 247, 208)
    pdf.rect(10 + card_w + gap, card_y, card_w, 20, "DF")
    pdf.set_xy(10 + card_w + gap, card_y + 2.5)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(21, 128, 61)  # Forest green
    pdf.cell(card_w, 4, "APPROVED FOR REMITTANCE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10 + card_w + gap)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(card_w, 7, _fmt_money(approved_amount), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10 + card_w + gap)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.cell(card_w, 4, "Approved for Immediate Payment", align="C")

    # Card 3: Total Withheld (Disputed + Needs Proof)
    pdf.set_fill_color(254, 242, 242)  # Light red
    pdf.set_draw_color(254, 202, 202)
    pdf.rect(10 + (card_w + gap) * 2, card_y, card_w, 20, "DF")
    pdf.set_xy(10 + (card_w + gap) * 2, card_y + 2.5)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(185, 28, 28)
    pdf.cell(card_w, 4, "TOTAL AMOUNT WITHHELD", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10 + (card_w + gap) * 2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(card_w, 7, _fmt_money(not_approved_amount), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10 + (card_w + gap) * 2)
    pdf.set_font("Helvetica", "B", 6.5)
    withheld_subtext = f"Disputed: {_fmt_money(disputed_amount)}  |  Needs Proof: {_fmt_money(needs_proof_amount)}"
    pdf.cell(card_w, 4, _clean_pdf_text(withheld_subtext), align="C")

    pdf.set_y(card_y + 24)

    # SECTION 4: ITEMIZED AUDIT TABLE
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 5, "ITEMIZED AUDIT BREAKDOWN", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    col_widths = (25, 17, 18, 18, 18, 26, 73)
    hdr_style = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=(26, 54, 93))

    pdf.set_font("Helvetica", size=7.5)
    with pdf.table(
        col_widths=col_widths,
        text_align=("L", "R", "R", "R", "R", "C", "L"),
        line_height=4.5,
        headings_style=hdr_style,
    ) as table:
        hdr = table.row()
        for h in ["Charge Type", "Billed", "Approved", "Disputed", "Needs Proof", "Audit Status", "Finding / Contract Reason"]:
            hdr.cell(h)

        for line_item in raw_lines:
            if hasattr(line_item, "to_dict"):
                item = line_item.to_dict()
            elif isinstance(line_item, dict):
                item = line_item
            else:
                continue

            ctype = str(item.get("type", "other"))
            bld = _fmt_money(item.get("amount", 0.0))
            app = _fmt_money(item.get("approved_amount", 0.0))
            disp = _fmt_money(item.get("disputed_amount", 0.0))
            prf = _fmt_money(item.get("needs_proof_amount", 0.0))
            status = str(item.get("status", "DISPUTE")).upper()
            reason = str(item.get("reason", ""))

            r = table.row()
            r.cell(_clean_pdf_text(ctype))
            r.cell(bld)
            r.cell(app)
            r.cell(disp)
            r.cell(prf)

            # Badge styling based on status
            if status == "APPROVE":
                st_face = FontFace(emphasis="BOLD", color=(21, 128, 61), fill_color=(240, 253, 244))
            elif status == "DISPUTE":
                st_face = FontFace(emphasis="BOLD", color=(185, 28, 28), fill_color=(254, 242, 242))
            else:
                st_face = FontFace(emphasis="BOLD", color=(180, 83, 9), fill_color=(254, 243, 199))

            r.cell(_clean_pdf_text(status), style=st_face)
            r.cell(_clean_pdf_text(reason))

        # Bottom Totals row
        tot_face = FontFace(emphasis="BOLD", color=(15, 23, 42), fill_color=(241, 245, 249))
        tot_r = table.row()
        tot_r.cell("TOTAL", style=tot_face)
        tot_r.cell(_fmt_money(total_billed), style=tot_face)
        tot_r.cell(_fmt_money(approved_amount), style=tot_face)
        tot_r.cell(_fmt_money(disputed_amount), style=tot_face)
        tot_r.cell(_fmt_money(needs_proof_amount), style=tot_face)
        withheld_status_text = f"WITHHELD {_fmt_money(not_approved_amount)}"
        tot_r.cell(_clean_pdf_text(withheld_status_text), style=tot_face)
        remit_sub = f"Payable: {_fmt_money(approved_amount)} (Immediate Remittance)"
        tot_r.cell(_clean_pdf_text(remit_sub), style=tot_face)

    pdf.ln(4)

    # SECTION 5: REAL-WORLD REQUIRED DOCUMENTS CHECKLIST
    # Build complete document list including any items from audit_data
    docs_to_request: List[str] = []
    for doc in documents_needed:
        if doc and doc not in docs_to_request:
            docs_to_request.append(doc)

    # Add standard drayage dispute verification items based on audited charges
    has_linehaul_dispute = any(
        (l.get("type") == "linehaul_fsc" and l.get("status") != "APPROVE")
        for l in (raw_lines if isinstance(raw_lines, list) else [])
    )
    has_chassis_dispute = any(
        (l.get("type") == "chassis" and l.get("status") != "APPROVE")
        for l in (raw_lines if isinstance(raw_lines, list) else [])
    )
    has_storage_dispute = any(
        (l.get("type") == "storage" and l.get("status") != "APPROVE")
        for l in (raw_lines if isinstance(raw_lines, list) else [])
    )
    has_prepull_dispute = any(
        (l.get("type") == "prepull" and l.get("status") != "APPROVE")
        for l in (raw_lines if isinstance(raw_lines, list) else [])
    )
    has_detention_dispute = any(
        (l.get("type") == "detention" and l.get("status") != "APPROVE")
        for l in (raw_lines if isinstance(raw_lines, list) else [])
    )

    std_docs = [
        ("Signed Proof of Delivery (POD) with clear consignee delivery timestamp", has_linehaul_dispute or not docs_to_request),
        ("Marine / Rail Terminal Equipment Interchange Receipts (TIR / J1 / EIR) with out-gate/in-gate times", has_chassis_dispute or not docs_to_request),
        ("Carrier Yard In-Gate & Out-Gate Timestamp Tickets / Facility GPS Logs", has_storage_dispute),
        ("Written Broker Dispatch Pre-pull & Yard Hold Authorization", has_prepull_dispute),
        ("Driver Detention Timesheet signed by warehouse clerk with in/out timestamps", has_detention_dispute),
    ]

    for title, condition in std_docs:
        if condition and title not in docs_to_request:
            docs_to_request.append(title)

    if not docs_to_request:
        docs_to_request = [
            "Signed Proof of Delivery (POD) with clear consignee signature and delivery timestamp",
            "Marine / Rail Terminal Equipment Interchange Receipts (TIR / J1 / EIR)",
            "Written Broker Authorization for accessorial charges",
        ]

    # Render Checklist
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 5, "REAL-WORLD REQUIRED DOCUMENTS CHECKLIST", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(
        0,
        4,
        "To release withheld balances, the carrier must submit verified copies of the following documentary proof:",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(1)

    for item_doc in docs_to_request[:6]:  # Limit to clean top items
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(180, 83, 9)  # Amber
        pdf.cell(8, 4.5, "[  ] ", align="R")
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 4.5, _clean_pdf_text(item_doc), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # SECTION 6: REMITTANCE INSTRUCTIONS & AUTHORIZED AP SIGNATURE SECTION
    box_rem_y = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, box_rem_y, 195, 32, "DF")

    pdf.set_xy(13, box_rem_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(189, 4, "REMITTANCE INSTRUCTIONS & AUDIT AUTHORIZATION", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(13)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(71, 85, 105)
    remittance_msg = (
        f"Approved charges totaling {_fmt_money(approved_amount)} have been released for immediate remittance per "
        f"contractual terms. Withheld charges totaling {_fmt_money(not_approved_amount)} are disputed or pending proof. "
        f"Submit supporting documentation to disputes@premierfreightlogistics.com within 30 days of this notice. "
        f"Uncontested debit adjustments will become final under UIIA Section G.1."
    )
    pdf.multi_cell(189, 3.8, _clean_pdf_text(remittance_msg))
    pdf.ln(2)

    pdf.set_x(13)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(90, 4, "Accounts Payable Authorized Signature: ___________________________", new_x="RIGHT")
    pdf.cell(90, 4, f"Audit Date: {_clean_pdf_text(audit_date)}", align="R", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
