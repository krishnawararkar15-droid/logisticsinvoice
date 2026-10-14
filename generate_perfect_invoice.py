"""
Generate a realistic, professional carrier drayage invoice.
Follows the visual layout of modern logistics bills (Vanguard / SwiftPath).
Outputs:
1. Vector PDF (.pdf)
2. High-res PNG image (.png)
3. High-res JPG image (.jpg)
4. Structured JSON (.json)
"""
import json
from pathlib import Path
from fpdf import FPDF
import pypdfium2 as pdfium

class PerfectInvoicePDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(auto=True, margin=10)

def create_invoice():
    pdf = PerfectInvoicePDF()
    pdf.add_page()
    
    # ----------------------------------------------------
    # 1. HEADER SECTION
    # ----------------------------------------------------
    # Carrier Title
    pdf.set_xy(12, 12)
    pdf.set_font('Helvetica', 'B', 17)
    pdf.set_text_color(15, 23, 42) # Slate 900
    pdf.cell(115, 7, 'PACIFIC CREST INTERMODAL LLC', new_x="RIGHT", new_y="TOP")
    
    # "INVOICE" Title right
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(75, 7, 'INVOICE', align='R', new_x="LMARGIN", new_y="NEXT")
    
    # Sub-header details
    pdf.set_xy(12, 19)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.cell(115, 4.5, 'SCAC: PCIL  |  USDOT# 2948190  |  MC# 892341  |  UIIA CERTIFIED', new_x="RIGHT", new_y="TOP")
    
    # Top-right metadata subtitle
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(75, 4.5, 'ORIGINAL FREIGHT BILLING', align='R', new_x="LMARGIN", new_y="NEXT")
    
    # Address & Contact
    pdf.set_xy(12, 23.5)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(115, 4, '2100 Ocean Blvd, Suite 450, Long Beach, CA 90802  |  Tel: (562) 555-0194', new_x="RIGHT", new_y="TOP")
    pdf.cell(75, 4, 'Terms: Net 30 Days', align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(12, 27.5)
    pdf.cell(115, 4, 'Billing Dept: billing@pacificcrestintermodal.com', new_x="RIGHT", new_y="TOP")
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(30, 64, 175) # Blue
    pdf.cell(75, 4, 'Electronic Remittance Required', align='R', new_x="LMARGIN", new_y="NEXT")
    
    # Horizontal divider rule
    pdf.set_draw_color(203, 213, 225) # Slate 300
    pdf.set_line_width(0.5)
    pdf.line(12, 33, 204, 33)
    
    # ----------------------------------------------------
    # 2. METADATA & BILL TO / REMIT TO BOXES
    # ----------------------------------------------------
    # Top info strip: Invoice #, Date, BOL, Container, Chassis
    pdf.set_xy(12, 36)
    pdf.set_fill_color(248, 250, 252) # Slate 50
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 36, 192, 16, 'DF')
    
    # Col 1: Invoice #
    pdf.set_xy(15, 38)
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(38, 3.5, 'INVOICE NUMBER')
    pdf.cell(38, 3.5, 'INVOICE DATE')
    pdf.cell(38, 3.5, 'BILL OF LADING (BOL)')
    pdf.cell(40, 3.5, 'CONTAINER NUMBER')
    pdf.cell(38, 3.5, 'CHASSIS NUMBER')
    
    pdf.set_xy(15, 43)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(38, 5, 'INV-2026-9482')
    pdf.cell(38, 5, 'June 25, 2026')
    pdf.cell(38, 5, 'MEDU 91823901')
    pdf.set_text_color(30, 64, 175)
    pdf.cell(40, 5, 'TCLU 582910-3 (40HC)')
    pdf.set_text_color(15, 23, 42)
    pdf.cell(38, 5, 'DCLI 40-77192')
    
    # Bill To & Remit To Boxes
    box_y = 56
    # Left: Bill To
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, box_y, 93, 34, 'DF')
    
    pdf.set_xy(16, box_y + 3)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 4, 'BILL TO (FREIGHT BROKERAGE):', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 4.5, 'Apex Freight Logistics LLC', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 3.8, 'Attn: Drayage Accounts Payable & Carrier Audit', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.cell(85, 3.8, '500 N Michigan Ave, Suite 1400', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.cell(85, 3.8, 'Chicago, IL 60611', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.cell(85, 3.8, 'Email: ap@apexfreight.com  |  Ref: Rate Con LD-88210', new_x="LMARGIN", new_y="NEXT")
    
    # Right: Remit To
    pdf.rect(111, box_y, 93, 34, 'DF')
    pdf.set_xy(115, box_y + 3)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 4, 'REMIT PAYMENT TO:', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 4.5, 'Pacific Crest Intermodal LLC - Remittance Dept', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 3.8, 'P.O. Box 48920, Long Beach, CA 90802', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.cell(85, 3.8, 'ACH / Wire Bank: Wells Fargo Bank, N.A.', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.cell(85, 3.8, 'Routing / ABA: 12100024  |  Account: 8849201948', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.cell(85, 3.8, 'Remittance Inquiries: accounting@pacificcrestintermodal.com', new_x="LMARGIN", new_y="NEXT")
    
    # ----------------------------------------------------
    # 3. CONTAINER SHIPMENT & TIMELINE MILESTONES (Shaded Panel)
    # ----------------------------------------------------
    mile_y = 94
    pdf.set_fill_color(241, 245, 249) # Slate 100
    pdf.rect(12, mile_y, 192, 28, 'DF')
    
    pdf.set_xy(16, mile_y + 2.5)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(184, 4, 'SHIPMENT DETAILS & CONTAINER INTERMODAL MILESTONES', new_x="LMARGIN", new_y="NEXT")
    
    # Milestone grid Row 1
    pdf.set_xy(16, mile_y + 8)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(48, 3.5, 'PORT TERMINAL / ORIGIN:')
    pdf.cell(50, 3.5, 'DELIVERY FACILITY / CONSIGNEE:')
    pdf.cell(45, 3.5, 'CARRIER DROP YARD:')
    pdf.cell(41, 3.5, 'EMPTY RETURN DEPOT:')
    
    pdf.set_xy(16, mile_y + 11.5)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(48, 4, 'Port of Long Beach (Pier 400)')
    pdf.cell(50, 4, 'Inland Logistics Center, Ontario CA')
    pdf.cell(45, 4, 'PCIL Secure Lot #4, Carson CA')
    pdf.cell(41, 4, 'LBCT Empty Depot 3')
    
    # Milestone grid Row 2: Timestamps
    pdf.set_xy(16, mile_y + 16.5)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(48, 3.5, 'TERMINAL OUT-GATE (PICKUP):')
    pdf.cell(50, 3.5, 'DELIVERY APPOINTMENT:')
    pdf.cell(45, 3.5, 'ACTUAL DELIVERY / DROP:')
    pdf.cell(41, 3.5, 'EMPTY RETURNED TO PORT:')
    
    pdf.set_xy(16, mile_y + 20)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(48, 4, '2026-06-23  21:00')
    pdf.cell(50, 4, '2026-06-24  08:00')
    pdf.cell(45, 4, '2026-06-24  08:00')
    pdf.cell(41, 4, '2026-06-24  16:00')
    
    # ----------------------------------------------------
    # 4. ITEMIZED CHARGES TABLE
    # ----------------------------------------------------
    table_y = 127
    pdf.set_xy(12, table_y)
    
    # Header Row
    pdf.set_fill_color(30, 41, 59) # Slate 800
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 8)
    
    # Col widths: 8, 86, 28, 22, 24, 24 = 192 mm
    pdf.cell(8, 7.5, '#', align='C', fill=True)
    pdf.cell(86, 7.5, '  DESCRIPTION', fill=True)
    pdf.cell(28, 7.5, 'CHARGE CODE', align='C', fill=True)
    pdf.cell(22, 7.5, 'QTY / UNITS', align='C', fill=True)
    pdf.cell(24, 7.5, 'RATE', align='R', fill=True)
    pdf.cell(24, 7.5, 'AMOUNT ($)  ', align='R', fill=True)
    pdf.ln(7.5)
    
    # Table rows
    rows = [
        ("1", "Base Container Drayage Linehaul + Fuel Surcharge (FSC)", "linehaul_fsc", "1 Flat", "$1,500.00", "$1,500.00"),
        ("2", "Terminal Pre-Pull (Port Out-Gate to Carrier Yard Hold)", "prepull", "1 Move", "$150.00", "$150.00"),
        ("3", "Intermodal Tri-Axle Chassis Usage Fee (Daily Rental)", "chassis", "3 Days", "$45.00/day", "$135.00"),
        ("4", "Carrier Secure Yard Storage Fee", "storage", "2 Days", "$45.00/day", "$90.00"),
    ]
    
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(30, 41, 59)
    pdf.set_draw_color(226, 232, 240)
    
    current_y = table_y + 7.5
    for item in rows:
        idx, desc, code, qty, rate, amt = item
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(8, 8, idx, align='C', border='B', fill=True)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(86, 8, f"  {desc}", border='B', fill=True)
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(28, 8, code, align='C', border='B', fill=True)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(22, 8, qty, align='C', border='B', fill=True)
        pdf.cell(24, 8, rate, align='R', border='B', fill=True)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(24, 8, f"{amt}  ", align='R', border='B', fill=True)
        pdf.ln(8)
        current_y += 8
        
    # Subtotal row
    pdf.set_xy(12, current_y + 2)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(144, 6, '', align='R')
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(24, 6, 'SUBTOTAL:', align='R')
    pdf.set_text_color(15, 23, 42)
    pdf.cell(24, 6, '$1,875.00  ', align='R')
    
    # ----------------------------------------------------
    # 5. TOTAL DUE CARD
    # ----------------------------------------------------
    total_y = current_y + 10
    pdf.set_xy(108, total_y)
    pdf.set_fill_color(15, 23, 42) # Slate 900
    pdf.rect(108, total_y, 96, 14, 'F')
    
    pdf.set_xy(112, total_y + 3)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(46, 8, 'TOTAL AMOUNT DUE:', align='L')
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(42, 8, '$1,875.00  ', align='R')
    
    # ----------------------------------------------------
    # 6. AUDIT COMPLIANCE & LEGAL NOTICE
    # ----------------------------------------------------
    notice_y = total_y + 20
    pdf.set_xy(12, notice_y)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, notice_y, 192, 26, 'DF')
    
    pdf.set_xy(16, notice_y + 2.5)
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(184, 3.5, 'AUDIT & CONTRACTUAL COMPLIANCE STATEMENT:', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(16)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(100, 116, 139)
    notice_text = (
        "All container drayage, per diem, chassis, storage, and accessorial movements billed herein are rendered "
        "under the standard terms of the Uniform Intermodal Interchange and Facilities Access Agreement (UIIA) and "
        "Broker-Carrier Agreement Confirmation LD-88210. Proof of Delivery (POD) signed by consignee receiving clerk "
        "and marine terminal interchange gate receipts (EIR) are archived in our electronic dispatch system. "
        "Payment is due within 30 days of invoice transmission. For accessorial disputes or formal debit memos, "
        "contact AP@pacificcrestintermodal.com referencing Invoice # INV-2026-9482 within 10 business days."
    )
    pdf.multi_cell(184, 3.3, notice_text)
    
    # ----------------------------------------------------
    # 7. PAGE FOOTER
    # ----------------------------------------------------
    pdf.set_xy(12, 260)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(12, 260, 204, 260)
    
    pdf.set_xy(12, 262)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(96, 4, 'Pacific Crest Intermodal LLC  |  MC# 892341  |  USDOT# 2948190  |  SCAC: PCIL', align='L')
    pdf.cell(96, 4, 'Page 1 of 1  |  Generated by Intermodal EDI System', align='R')
    
    return pdf

def generate_all_formats():
    pdf = create_invoice()
    
    # Target directories
    downloads_dir = Path(r"C:\Users\krish\Downloads")
    sample_dir = Path("sample_data")
    brain_dir = Path(r"C:\Users\krish\.gemini\antigravity\brain\05d6ad1f-097c-4505-acf5-c0509f452813")
    
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Output PDF
    pdf_path = downloads_dir / "Carrier_Invoice_INV-2026-9482.pdf"
    pdf.output(str(pdf_path))
    pdf.output(str(sample_dir / "Carrier_Invoice_INV-2026-9482.pdf"))
    pdf.output(str(brain_dir / "Carrier_Invoice_INV-2026-9482.pdf"))
    print("Created PDF:", pdf_path)
    
    # 2. Render high-res PNG & JPG via pypdfium2 (300 DPI)
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc[0]
    pil_image = page.render(scale=3).to_pil() # ~216 DPI (super crisp)
    
    png_path = downloads_dir / "Carrier_Invoice_INV-2026-9482.png"
    pil_image.save(png_path, "PNG")
    pil_image.save(sample_dir / "Carrier_Invoice_INV-2026-9482.png", "PNG")
    pil_image.save(brain_dir / "Carrier_Invoice_INV-2026-9482.png", "PNG")
    print("Created PNG:", png_path)
    
    jpg_path = downloads_dir / "Carrier_Invoice_INV-2026-9482.jpg"
    pil_image.convert("RGB").save(jpg_path, "JPEG", quality=95)
    pil_image.convert("RGB").save(sample_dir / "Carrier_Invoice_INV-2026-9482.jpg", "JPEG", quality=95)
    pil_image.convert("RGB").save(brain_dir / "Carrier_Invoice_INV-2026-9482.jpg", "JPEG", quality=95)
    print("Created JPG:", jpg_path)
    
    # 3. Output JSON format
    json_data = {
        "invoice_id": "INV-2026-9482",
        "carrier_name": "Pacific Crest Intermodal LLC",
        "carrier_mc": "MC# 892341",
        "carrier_dot": "USDOT# 2948190",
        "container_no": "TCLU 582910-3",
        "bol_no": "MEDU 91823901",
        "chassis_no": "DCLI 40-77192",
        "timeline": {
            "terminal_pickup": "2026-06-23T21:00",
            "yard_in": None,
            "yard_out": None,
            "warehouse_appointment": "2026-06-24T08:00",
            "delivery_actual": "2026-06-24T08:00",
            "warehouse_in": None,
            "warehouse_out": None,
            "empty_return": "2026-06-24T16:00",
            "pod_provided": False,
            "prepull_request_documented": None
        },
        "lines": [
            {
                "type": "linehaul_fsc",
                "description": "Base Container Drayage Linehaul + Fuel Surcharge (FSC)",
                "qty": 1,
                "unit_rate": 1500.0,
                "amount": 1500.0
            },
            {
                "type": "prepull",
                "description": "Terminal Pre-Pull (Port Out-Gate to Secure Carrier Yard Hold)",
                "qty": 1,
                "unit_rate": 150.0,
                "amount": 150.0
            },
            {
                "type": "chassis",
                "description": "Intermodal Tri-Axle Chassis Usage Fee (Daily Rental)",
                "qty": 3,
                "unit_rate": 45.0,
                "amount": 135.0
            },
            {
                "type": "storage",
                "description": "Carrier Secure Yard Storage Fee",
                "qty": 2,
                "unit_rate": 45.0,
                "amount": 90.0
            }
        ],
        "total": 1875.0
    }
    
    json_path = downloads_dir / "Carrier_Invoice_INV-2026-9482.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    with open(sample_dir / "Carrier_Invoice_INV-2026-9482.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print("Created JSON:", json_path)

if __name__ == "__main__":
    generate_all_formats()
