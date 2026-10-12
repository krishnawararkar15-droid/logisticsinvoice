"""Generate a realistic carrier drayage invoice PDF."""
from fpdf import FPDF
from pathlib import Path

class InvoicePDF(FPDF):
    def header(self):
        # Company Header
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(26, 54, 93) # Navy blue
        self.cell(120, 9, 'PACIFIC GATEWAY DRAYAGE LLC', new_x="RIGHT", new_y="TOP")
        
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(74, 85, 104)
        self.cell(70, 9, 'INVOICE', align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(113, 128, 150)
        self.cell(120, 5, '1240 Harbor Scenic Way, Suite 300 | Long Beach, CA 90802', new_x="RIGHT", new_y="TOP")
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(43, 108, 176)
        self.cell(70, 5, 'INV-2026-0842', align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(113, 128, 150)
        self.cell(120, 5, 'MC# 892341 | DOT# 2948190 | dispatch@pacificdrayage.com', new_x="RIGHT", new_y="TOP")
        self.cell(70, 5, 'Date: June 25, 2026', align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.6)
        self.line(10, 32, 200, 32)
        self.ln(7)

pdf = InvoicePDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Bill To & Load Details Box
pdf.set_fill_color(248, 250, 252)
pdf.set_draw_color(226, 232, 240)
pdf.rect(10, 36, 92, 38, 'DF')
pdf.rect(108, 36, 92, 38, 'DF')

# Left Box: Bill To
pdf.set_xy(14, 39)
pdf.set_font('Helvetica', 'B', 9)
pdf.set_text_color(74, 85, 104)
pdf.cell(85, 5, 'BILL TO (FREIGHT BROKER):', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(14)
pdf.set_font('Helvetica', 'B', 10)
pdf.set_text_color(26, 32, 44)
pdf.cell(85, 5, 'Apex Freight Logistics LLC', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(14)
pdf.set_font('Helvetica', '', 9)
pdf.set_text_color(113, 128, 150)
pdf.cell(85, 4.5, 'Attn: Accounts Payable / Drayage Audit', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(14)
pdf.cell(85, 4.5, '500 N Michigan Ave, Suite 1400', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(14)
pdf.cell(85, 4.5, 'Chicago, IL 60611', new_x="LMARGIN", new_y="NEXT")

# Right Box: Shipment Details
pdf.set_xy(112, 39)
pdf.set_font('Helvetica', 'B', 9)
pdf.set_text_color(74, 85, 104)
pdf.cell(85, 5, 'CONTAINER & SHIPMENT DETAILS:', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('Helvetica', '', 8.5)
pdf.set_text_color(45, 55, 72)
pdf.set_x(112)
pdf.cell(85, 4.5, 'Container #: TCLU 582910-3 (40ft High Cube)', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(112)
pdf.cell(85, 4.5, 'Bill of Lading: MEDU 91823901 | BOL Ref: 77291-B', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(112)
pdf.cell(85, 4.5, 'Port Terminal: Port of Los Angeles (Pier 400)', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(112)
pdf.cell(85, 4.5, 'Delivery Point: Ontario Regional Depot, Ontario CA', new_x="LMARGIN", new_y="NEXT")
pdf.set_x(112)
pdf.cell(85, 4.5, 'Terminal Out-Gate: 2026-06-23 21:00 | Empty In: 2026-06-24 16:00', new_x="LMARGIN", new_y="NEXT")

pdf.set_y(80)

# Line Items Table Header
pdf.set_fill_color(30, 64, 175) # Primary blue
pdf.set_text_color(255, 255, 255)
pdf.set_font('Helvetica', 'B', 9)
pdf.cell(80, 8, '  ITEM DESCRIPTION', fill=True)
pdf.cell(30, 8, 'CHARGE TYPE', align='C', fill=True)
pdf.cell(20, 8, 'QTY', align='C', fill=True)
pdf.cell(30, 8, 'RATE', align='R', fill=True)
pdf.cell(30, 8, 'AMOUNT ($)  ', align='R', fill=True)
pdf.ln(8)

# Table Rows
items = [
    ("Standard Container Drayage Linehaul + FSC", "linehaul_fsc", "1", "$1,500.00", "$1,500.00"),
    ("Terminal Pre-pull to Carrier Yard Hold", "prepull", "1", "$150.00", "$150.00"),
    ("Chassis Usage / Daily Rental Charge", "chassis", "3 Days", "$45.00/day", "$135.00"),
    ("Secure Carrier Yard Storage Fee", "storage", "2 Days", "$45.00/day", "$90.00"),
]

pdf.set_text_color(45, 55, 72)
pdf.set_font('Helvetica', '', 8.5)
pdf.set_draw_color(226, 232, 240)

for idx, (desc, ctype, qty, rate, amt) in enumerate(items):
    fill = (idx % 2 == 1)
    if fill:
        pdf.set_fill_color(248, 250, 252)
    else:
        pdf.set_fill_color(255, 255, 255)
        
    pdf.cell(80, 8, f"  {desc}", border='B', fill=True)
    pdf.cell(30, 8, ctype, align='C', border='B', fill=True)
    pdf.cell(20, 8, qty, align='C', border='B', fill=True)
    pdf.cell(30, 8, rate, align='R', border='B', fill=True)
    pdf.cell(30, 8, f"{amt}  ", align='R', border='B', fill=True)
    pdf.ln(8)

pdf.ln(5)

# Total Box
pdf.set_x(120)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(40, 7, 'Subtotal:', align='R')
pdf.cell(30, 7, '$1,875.00  ', align='R')
pdf.ln(7)

pdf.set_x(120)
pdf.set_fill_color(239, 246, 255) # Light blue accent
pdf.set_font('Helvetica', 'B', 12)
pdf.set_text_color(30, 64, 175)
pdf.cell(40, 9, 'TOTAL DUE:', align='R', fill=True)
pdf.cell(30, 9, '$1,875.00  ', align='R', fill=True)
pdf.ln(16)

# Payment Remittance Footer
pdf.set_text_color(113, 128, 150)
pdf.set_font('Helvetica', '', 8)
pdf.cell(190, 4, 'Payment Terms: Net 30 Days. Remit ACH/Wire payment to: Wells Fargo Bank | Routing: 12100024 | Acct: 8849201948', align='C')
pdf.ln(4)
pdf.cell(190, 4, 'For drayage disputes or container tracking inquiries, contact AP@pacificdrayage.com referencing INV-2026-0842.', align='C')

output_path = Path("sample_data/sample_carrier_invoice.pdf")
output_path.parent.mkdir(parents=True, exist_ok=True)
pdf.output(str(output_path))
print("Created:", output_path)
