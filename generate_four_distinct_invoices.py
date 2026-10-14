"""
Generate 4 completely distinct carrier drayage test invoices.
Each has unique carriers, containers, line items, and financial totals:

1. PDF:  Carrier_Invoice_1_PacificCrest.pdf       -> Total: $2,115.00
2. PNG:  Carrier_Invoice_2_MidwestExpress.png       -> Total: $2,025.00
3. JPG:  Carrier_Invoice_3_GulfCoastDrayage.jpg     -> Total: $2,040.00
4. JSON: Carrier_Invoice_4_AtlanticIntermodal.json  -> Total: $2,390.00
"""

import json
from pathlib import Path
from fpdf import FPDF
import pypdfium2 as pdfium

class StyledInvoicePDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(auto=True, margin=10)

def build_pdf_document(data: dict) -> FPDF:
    pdf = StyledInvoicePDF()
    pdf.add_page()
    
    # Header
    pdf.set_xy(12, 12)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(115, 7, data['carrier_name'].upper(), new_x="RIGHT", new_y="TOP")
    
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(75, 7, 'INVOICE', align='R', new_x="LMARGIN", new_y="NEXT")
    
    # Subheader
    pdf.set_xy(12, 19)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(115, 4.5, f"SCAC: {data['scac']}  |  USDOT# {data['dot']}  |  MC# {data['mc']}  |  UIIA CERTIFIED", new_x="RIGHT", new_y="TOP")
    
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(75, 4.5, 'ORIGINAL FREIGHT BILLING', align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(12, 23.5)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(115, 4, f"{data['address']}  |  Tel: {data['phone']}", new_x="RIGHT", new_y="TOP")
    pdf.cell(75, 4, f"Terms: {data['terms']}", align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(12, 27.5)
    pdf.cell(115, 4, f"Billing Dept: {data['email']}", new_x="RIGHT", new_y="TOP")
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(75, 4, 'Electronic Remittance Required', align='R', new_x="LMARGIN", new_y="NEXT")
    
    # Line divider
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.5)
    pdf.line(12, 33, 204, 33)
    
    # Metadata strip
    pdf.set_xy(12, 36)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 36, 192, 16, 'DF')
    
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
    pdf.cell(38, 5, data['invoice_id'])
    pdf.cell(38, 5, data['invoice_date'])
    pdf.cell(38, 5, data['bol_no'])
    pdf.set_text_color(30, 64, 175)
    pdf.cell(40, 5, data['container_no'])
    pdf.set_text_color(15, 23, 42)
    pdf.cell(38, 5, data['chassis_no'])
    
    # Bill To & Remit To
    box_y = 56
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(12, box_y, 93, 34, 'DF')
    pdf.set_xy(16, box_y + 3)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 4, 'BILL TO (FREIGHT BROKERAGE):', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 4.5, data['bill_to']['name'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 3.8, data['bill_to']['attn'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.cell(85, 3.8, data['bill_to']['addr'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.cell(85, 3.8, data['bill_to']['city'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.cell(85, 3.8, f"Email: {data['bill_to']['email']}  |  Ref: {data['bill_to']['ref']}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.rect(111, box_y, 93, 34, 'DF')
    pdf.set_xy(115, box_y + 3)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 4, 'REMIT PAYMENT TO:', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 4.5, data['remit_to']['name'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 3.8, data['remit_to']['addr'], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.cell(85, 3.8, f"ACH / Wire Bank: {data['remit_to']['bank']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.cell(85, 3.8, f"Routing: {data['remit_to']['routing']}  |  Account: {data['remit_to']['account']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(115)
    pdf.cell(85, 3.8, f"Remittance Inquiries: {data['remit_to']['email']}", new_x="LMARGIN", new_y="NEXT")
    
    # Milestone Panel
    mile_y = 94
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(12, mile_y, 192, 28, 'DF')
    pdf.set_xy(16, mile_y + 2.5)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(184, 4, 'SHIPMENT DETAILS & CONTAINER INTERMODAL MILESTONES', new_x="LMARGIN", new_y="NEXT")
    
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
    pdf.cell(48, 4, data['milestones']['terminal'])
    pdf.cell(50, 4, data['milestones']['delivery_facility'])
    pdf.cell(45, 4, data['milestones']['drop_lot'])
    pdf.cell(41, 4, data['milestones']['return_depot'])
    
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
    pdf.cell(48, 4, data['milestones']['pickup_time'])
    pdf.cell(50, 4, data['milestones']['appt_time'])
    pdf.cell(45, 4, data['milestones']['delivery_time'])
    pdf.cell(41, 4, data['milestones']['return_time'])
    
    # Line items table
    table_y = 127
    pdf.set_xy(12, table_y)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 8)
    
    pdf.cell(8, 7.5, '#', align='C', fill=True)
    pdf.cell(86, 7.5, '  DESCRIPTION', fill=True)
    pdf.cell(28, 7.5, 'CHARGE CODE', align='C', fill=True)
    pdf.cell(22, 7.5, 'QTY / UNITS', align='C', fill=True)
    pdf.cell(24, 7.5, 'RATE', align='R', fill=True)
    pdf.cell(24, 7.5, 'AMOUNT ($)  ', align='R', fill=True)
    pdf.ln(7.5)
    
    current_y = table_y + 7.5
    for idx, item in enumerate(data['lines'], 1):
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(30, 41, 59)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(8, 8, str(idx), align='C', border='B', fill=True)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(86, 8, f"  {item['description']}", border='B', fill=True)
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(28, 8, item['type'], align='C', border='B', fill=True)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(22, 8, str(item['qty_str']), align='C', border='B', fill=True)
        pdf.cell(24, 8, f"${item['unit_rate']:,.2f}", align='R', border='B', fill=True)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(24, 8, f"${item['amount']:,.2f}  ", align='R', border='B', fill=True)
        pdf.ln(8)
        current_y += 8
        
    # Subtotal
    pdf.set_xy(12, current_y + 2)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(144, 6, '', align='R')
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(24, 6, 'SUBTOTAL:', align='R')
    pdf.set_text_color(15, 23, 42)
    pdf.cell(24, 6, f"${data['total']:,.2f}  ", align='R')
    
    # Total Due Block
    total_y = current_y + 10
    pdf.set_xy(108, total_y)
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(108, total_y, 96, 14, 'F')
    
    pdf.set_xy(112, total_y + 3)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(46, 8, 'TOTAL AMOUNT DUE:', align='L')
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(42, 8, f"${data['total']:,.2f}  ", align='R')
    
    # Audit Notice
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
        f"All container drayage, per diem, chassis, storage, and accessorial movements billed herein are rendered "
        f"under the standard terms of the Uniform Intermodal Interchange Agreement (UIIA) and Broker-Carrier "
        f"Agreement Confirmation {data['bill_to']['ref']}. Proof of Delivery (POD) signed by consignee receiving clerk "
        f"and marine terminal interchange gate receipts (EIR) are maintained in carrier digital archive. "
        f"Payment is due within 30 days of invoice transmission. For accessorial disputes or formal debit memos, "
        f"contact {data['email']} referencing Invoice # {data['invoice_id']} within 10 business days."
    )
    pdf.multi_cell(184, 3.3, notice_text)
    
    # Footer
    pdf.set_xy(12, 260)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(12, 260, 204, 260)
    
    pdf.set_xy(12, 262)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(96, 4, f"{data['carrier_name']}  |  MC# {data['mc']}  |  USDOT# {data['dot']}  |  SCAC: {data['scac']}", align='L')
    pdf.cell(96, 4, 'Page 1 of 1  |  Generated by Intermodal EDI System', align='R')
    
    return pdf

# -------------------------------------------------------------------------
# FOUR DISTINCT INVOICE SPECIFICATIONS
# -------------------------------------------------------------------------

invoices = [
    # 1. PACIFIC CREST INTERMODAL (PDF) -> Total $2,115.00
    {
        "id_slug": "Carrier_Invoice_1_PacificCrest",
        "carrier_name": "Pacific Crest Intermodal LLC",
        "scac": "PCIL", "dot": "2948190", "mc": "892341",
        "address": "2100 Ocean Blvd, Suite 450, Long Beach, CA 90802",
        "phone": "(562) 555-0194", "email": "billing@pacificcrestintermodal.com",
        "terms": "Net 30 Days",
        "invoice_id": "INV-2026-9482", "invoice_date": "June 25, 2026",
        "bol_no": "MEDU 91823901", "container_no": "TCLU 582910-3 (40HC)",
        "chassis_no": "DCLI 40-77192",
        "bill_to": {
            "name": "Apex Freight Logistics LLC",
            "attn": "Attn: Drayage Accounts Payable & Carrier Audit",
            "addr": "500 N Michigan Ave, Suite 1400",
            "city": "Chicago, IL 60611",
            "email": "ap@apexfreight.com",
            "ref": "Rate Con LD-88210"
        },
        "remit_to": {
            "name": "Pacific Crest Intermodal LLC - Remittance Dept",
            "addr": "P.O. Box 48920, Long Beach, CA 90802",
            "bank": "Wells Fargo Bank, N.A.",
            "routing": "12100024", "account": "8849201948",
            "email": "accounting@pacificcrestintermodal.com"
        },
        "milestones": {
            "terminal": "Port of Long Beach (Pier 400)",
            "delivery_facility": "Inland Logistics Center, Ontario CA",
            "drop_lot": "PCIL Secure Lot #4, Carson CA",
            "return_depot": "LBCT Empty Depot 3",
            "pickup_time": "2026-06-23  21:00",
            "appt_time": "2026-06-24  08:00",
            "delivery_time": "2026-06-24  08:00",
            "return_time": "2026-06-25  17:00"
        },
        "lines": [
            { "type": "linehaul_fsc", "description": "Base Container Drayage Linehaul + Fuel Surcharge (FSC)", "qty": 1, "qty_str": "1 Flat", "unit_rate": 1650.0, "amount": 1650.0 },
            { "type": "prepull", "description": "Terminal Pre-Pull (Port Out-Gate to Carrier Yard Hold)", "qty": 1, "qty_str": "1 Move", "unit_rate": 175.0, "amount": 175.0 },
            { "type": "chassis", "description": "Intermodal Tri-Axle Chassis Usage Fee (Daily Rental)", "qty": 4, "qty_str": "4 Days", "unit_rate": 45.0, "amount": 180.0 },
            { "type": "storage", "description": "Carrier Secure Yard Storage Fee", "qty": 2, "qty_str": "2 Days", "unit_rate": 55.0, "amount": 110.0 }
        ],
        "total": 2115.0
    },

    # 2. MIDWEST INTERMODAL EXPRESS (PNG) -> Total $2,025.00
    {
        "id_slug": "Carrier_Invoice_2_MidwestExpress",
        "carrier_name": "Midwest Intermodal Express LLC",
        "scac": "MWEP", "dot": "3109482", "mc": "741920",
        "address": "4800 S Central Ave, Suite 210, Chicago, IL 60638",
        "phone": "(312) 555-0821", "email": "ap@midwestintermodalexpress.com",
        "terms": "Net 30 Days",
        "invoice_id": "INV-2026-5120", "invoice_date": "June 28, 2026",
        "bol_no": "MAEU 29104820", "container_no": "MSKU 782014-9 (40HC)",
        "chassis_no": "TRAC 40-99210",
        "bill_to": {
            "name": "Apex Freight Logistics LLC",
            "attn": "Attn: Intermodal Accounts Payable",
            "addr": "500 N Michigan Ave, Suite 1400",
            "city": "Chicago, IL 60611",
            "email": "ap@apexfreight.com",
            "ref": "Rate Con MW-77190"
        },
        "remit_to": {
            "name": "Midwest Intermodal Express LLC",
            "addr": "P.O. Box 91024, Chicago, IL 60638",
            "bank": "JPMorgan Chase Bank, N.A.",
            "routing": "071000013", "account": "9920194812",
            "email": "billing@midwestintermodalexpress.com"
        },
        "milestones": {
            "terminal": "BNSF LPC Intermodal Rail Ramp (Elwood IL)",
            "delivery_facility": "Amazon MDW2 Fulfillment Center, Joliet IL",
            "drop_lot": "Central Chicago Staging Yard, Cicero IL",
            "return_depot": "BNSF Logistics Park Chicago Empty Lot",
            "pickup_time": "2026-06-25  14:00",
            "appt_time": "2026-06-26  09:00",
            "delivery_time": "2026-06-26  13:00",
            "return_time": "2026-06-27  11:00"
        },
        "lines": [
            { "type": "linehaul_fsc", "description": "Intermodal Rail Ramp Base Drayage Linehaul", "qty": 1, "qty_str": "1 Flat", "unit_rate": 1400.0, "amount": 1400.0 },
            { "type": "linehaul_fsc", "description": "Standard Fuel Surcharge (DOE Index 22.8%)", "qty": 1, "qty_str": "1 Calc", "unit_rate": 320.0, "amount": 320.0 },
            { "type": "chassis", "description": "Pool Chassis Daily Usage Fee", "qty": 2, "qty_str": "2 Days", "unit_rate": 40.0, "amount": 80.0 },
            { "type": "detention", "description": "Consignee Facility Driver Detention (Waiting Time)", "qty": 3, "qty_str": "3 Hours", "unit_rate": 75.0, "amount": 225.0 }
        ],
        "total": 2025.0
    },

    # 3. GULF COAST DRAYAGE & LOGISTICS (JPG) -> Total $2,040.00
    {
        "id_slug": "Carrier_Invoice_3_GulfCoastDrayage",
        "carrier_name": "Gulf Coast Drayage & Logistics Inc",
        "scac": "GCDL", "dot": "2810941", "mc": "951820",
        "address": "8500 Highway 225, Suite 100, Houston, TX 77017",
        "phone": "(713) 555-0348", "email": "billing@gulfcoastdrayage.com",
        "terms": "Net 30 Days",
        "invoice_id": "INV-2026-3840", "invoice_date": "July 02, 2026",
        "bol_no": "CMDU 88192014", "container_no": "CMAU 492018-7 (40HC)",
        "chassis_no": "FLEXI 40-19280",
        "bill_to": {
            "name": "Apex Freight Logistics LLC",
            "attn": "Attn: Houston Port Accounts Payable",
            "addr": "500 N Michigan Ave, Suite 1400",
            "city": "Chicago, IL 60611",
            "email": "ap@apexfreight.com",
            "ref": "Rate Con GC-49102"
        },
        "remit_to": {
            "name": "Gulf Coast Drayage & Logistics Inc",
            "addr": "P.O. Box 77102, Houston, TX 77251",
            "bank": "Bank of America, N.A.",
            "routing": "111000012", "account": "4491028471",
            "email": "ap@gulfcoastdrayage.com"
        },
        "milestones": {
            "terminal": "Port of Houston (Barbours Cut Container Terminal)",
            "delivery_facility": "Pasadena Petrochemical Distribution Center, TX",
            "drop_lot": "GCDL Secure Yard #2, La Porte TX",
            "return_depot": "Barbours Cut Empty Container Depot",
            "pickup_time": "2026-06-28  10:00",
            "appt_time": "2026-06-29  08:00",
            "delivery_time": "2026-06-29  09:30",
            "return_time": "2026-07-02  16:00"
        },
        "lines": [
            { "type": "linehaul_fsc", "description": "Houston Port Container Drayage Base Rate", "qty": 1, "qty_str": "1 Move", "unit_rate": 1280.0, "amount": 1280.0 },
            { "type": "linehaul_fsc", "description": "Mandatory Port Fuel Surcharge (FSC)", "qty": 1, "qty_str": "1 Flat", "unit_rate": 245.0, "amount": 245.0 },
            { "type": "prepull", "description": "Terminal Congestion Pre-Pull Move to Carrier Lot", "qty": 1, "qty_str": "1 Move", "unit_rate": 140.0, "amount": 140.0 },
            { "type": "storage", "description": "Overnight Carrier Yard Storage Fee", "qty": 3, "qty_str": "3 Days", "unit_rate": 50.0, "amount": 150.0 },
            { "type": "chassis", "description": "Intermodal Chassis Rental (Per Diem)", "qty": 5, "qty_str": "5 Days", "unit_rate": 45.0, "amount": 225.0 }
        ],
        "total": 2040.0
    },

    # 4. ATLANTIC INTERMODAL TRANSPORT (JSON) -> Total $2,390.00
    {
        "id_slug": "Carrier_Invoice_4_AtlanticIntermodal",
        "carrier_name": "Atlantic Intermodal Transport LLC",
        "scac": "AITL", "dot": "2591823", "mc": "681920",
        "address": "1200 Port Terminal Blvd, Suite 300, Elizabeth, NJ 07201",
        "phone": "(908) 555-0912", "email": "billing@atlanticintermodal.com",
        "terms": "Net 30 Days",
        "invoice_id": "INV-2026-7291", "invoice_date": "July 05, 2026",
        "bol_no": "ONEY 55192801", "container_no": "ONEU 391028-4 (40HC)",
        "chassis_no": "MILE 40-55102",
        "bill_to": {
            "name": "Apex Freight Logistics LLC",
            "attn": "Attn: Northeast Drayage Audit",
            "addr": "500 N Michigan Ave, Suite 1400",
            "city": "Chicago, IL 60611",
            "email": "ap@apexfreight.com",
            "ref": "Rate Con NY-88201"
        },
        "remit_to": {
            "name": "Atlantic Intermodal Transport LLC",
            "addr": "P.O. Box 39201, Newark, NJ 07102",
            "bank": "Citibank, N.A.",
            "routing": "021000089", "account": "7719204819",
            "email": "accounting@atlanticintermodal.com"
        },
        "milestones": {
            "terminal": "Port of NY/NJ (Maher Terminals, Elizabeth NJ)",
            "delivery_facility": "Northeast Fulfillment Hub, Allentown PA",
            "drop_lot": "AITL Elizabeth Staging Yard #1",
            "return_depot": "Maher Terminals Empty Return Depot",
            "pickup_time": "2026-07-01  18:00",
            "appt_time": "2026-07-02  07:00",
            "delivery_time": "2026-07-02  11:00",
            "return_time": "2026-07-04  15:00"
        },
        "lines": [
            { "type": "linehaul_fsc", "description": "All-In Container Linehaul + Fuel Surcharge (FSC)", "qty": 1, "qty_str": "1 Flat", "unit_rate": 1850.0, "amount": 1850.0 },
            { "type": "prepull", "description": "Terminal Pre-Pull (Port Out-Gate to Staging Lot)", "qty": 1, "qty_str": "1 Move", "unit_rate": 160.0, "amount": 160.0 },
            { "type": "chassis", "description": "Tri-Axle Container Chassis Usage", "qty": 3, "qty_str": "3 Days", "unit_rate": 50.0, "amount": 150.0 },
            { "type": "detention", "description": "Receiver Unloading Driver Detention (Waiting Time)", "qty": 2, "qty_str": "2 Hours", "unit_rate": 85.0, "amount": 170.0 },
            { "type": "storage", "description": "Yard Storage Hold (Weekend Facility Closure)", "qty": 1, "qty_str": "1 Day", "unit_rate": 60.0, "amount": 60.0 }
        ],
        "total": 2390.0
    }
]

def generate_all():
    downloads = Path(r"C:\Users\krish\Downloads")
    sample_dir = Path("sample_data")
    brain_dir = Path(r"C:\Users\krish\.gemini\antigravity\brain\05d6ad1f-097c-4505-acf5-c0509f452813")
    
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    for inv in invoices:
        slug = inv["id_slug"]
        pdf = build_pdf_document(inv)
        
        # Save PDF
        pdf_path = downloads / f"{slug}.pdf"
        pdf.output(str(pdf_path))
        pdf.output(str(sample_dir / f"{slug}.pdf"))
        pdf.output(str(brain_dir / f"{slug}.pdf"))
        print(f"Generated PDF:  {pdf_path} (Total: ${inv['total']:,.2f})")
        
        # Render high-res PNG & JPG via pypdfium2 (crisp 216 DPI)
        doc = pdfium.PdfDocument(str(pdf_path))
        page = doc[0]
        pil_image = page.render(scale=3).to_pil()
        
        png_path = downloads / f"{slug}.png"
        pil_image.save(png_path, "PNG")
        pil_image.save(sample_dir / f"{slug}.png", "PNG")
        pil_image.save(brain_dir / f"{slug}.png", "PNG")
        print(f"Generated PNG:  {png_path}")
        
        jpg_path = downloads / f"{slug}.jpg"
        pil_image.convert("RGB").save(jpg_path, "JPEG", quality=95)
        pil_image.convert("RGB").save(sample_dir / f"{slug}.jpg", "JPEG", quality=95)
        pil_image.convert("RGB").save(brain_dir / f"{slug}.jpg", "JPEG", quality=95)
        print(f"Generated JPG:  {jpg_path}")
        
        # Save JSON
        json_path = downloads / f"{slug}.json"
        clean_json = {
            "invoice_id": inv["invoice_id"],
            "carrier_name": inv["carrier_name"],
            "container_no": inv["container_no"],
            "bol_no": inv["bol_no"],
            "chassis_no": inv["chassis_no"],
            "timeline": {
                "terminal_pickup": inv["milestones"]["pickup_time"].replace("  ", "T"),
                "yard_in": None,
                "yard_out": None,
                "warehouse_appointment": inv["milestones"]["appt_time"].replace("  ", "T"),
                "delivery_actual": inv["milestones"]["delivery_time"].replace("  ", "T"),
                "warehouse_in": None,
                "warehouse_out": None,
                "empty_return": inv["milestones"]["return_time"].replace("  ", "T"),
                "pod_provided": False,
                "prepull_request_documented": None
            },
            "lines": [
                {
                    "type": l["type"],
                    "description": l["description"],
                    "qty": l["qty"],
                    "unit_rate": l["unit_rate"],
                    "amount": l["amount"]
                }
                for l in inv["lines"]
            ],
            "total": inv["total"]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(clean_json, f, indent=2)
        with open(sample_dir / f"{slug}.json", "w", encoding="utf-8") as f:
            json.dump(clean_json, f, indent=2)
        print(f"Generated JSON: {json_path}")

if __name__ == "__main__":
    generate_all()
