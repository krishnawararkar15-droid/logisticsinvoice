"""Generate Midwest Intermodal Carrier Invoice 2 PDF."""
from pathlib import Path
from fpdf import FPDF

class InvoicePDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 17)
        self.set_text_color(24, 43, 73)
        self.cell(120, 9, 'MIDWEST INTERMODAL FREIGHT LLC', new_x="RIGHT", new_y="TOP")
        
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(74, 85, 104)
        self.cell(70, 9, 'INVOICE', align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(113, 128, 150)
        self.cell(120, 5, '4800 S Central Ave, Suite 210 | Chicago, IL 60638', new_x="RIGHT", new_y="TOP")
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(43, 108, 176)
        self.cell(70, 5, 'INV-2026-1055', align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(113, 128, 150)
        self.cell(120, 5, 'MC# 741920 | USDOT# 3109482 | SCAC: MWIE | ap@midwestintermodal.com', new_x="RIGHT", new_y="TOP")
        self.cell(70, 5, 'Date: June 28, 2026', align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.6)
        self.line(10, 32, 200, 32)
        self.ln(7)

def build_pdf_2():
    pdf = InvoicePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Bill To & Load Details Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, 36, 92, 40, 'DF')
    pdf.rect(108, 36, 92, 40, 'DF')

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
    pdf.cell(85, 4.5, 'Container #: MSKU 782014-9 (40ft High Cube)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(112)
    pdf.cell(85, 4.5, 'Ocean BOL / Booking: MAEU 29104820 | Seal: 881920', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(112)
    pdf.cell(85, 4.5, 'Rail Terminal: BNSF LPC (Elwood, IL) | Chassis: DCLI 40-77192', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(112)
    pdf.cell(85, 4.5, 'Consignee / Destination: Amazon MDW2, Joliet IL', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(112)
    pdf.cell(85, 4.5, 'Ramp Out-Gate: 2026-06-25 14:00 | Empty In: 2026-06-27 11:00', new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(82)

    # Line Items Table Header
    pdf.set_fill_color(30, 64, 175)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(80, 8, '  ITEM DESCRIPTION', fill=True)
    pdf.cell(30, 8, 'CHARGE TYPE', align='C', fill=True)
    pdf.cell(20, 8, 'QTY', align='C', fill=True)
    pdf.cell(30, 8, 'RATE', align='R', fill=True)
    pdf.cell(30, 8, 'AMOUNT ($)  ', align='R', fill=True)
    pdf.ln(8)

    items = [
        ("Base Drayage Linehaul + Fuel Surcharge", "linehaul_fsc", "1", "$1,450.00", "$1,450.00"),
        ("Intermodal Chassis Usage Fee", "chassis", "3 Days", "$45.00/day", "$135.00"),
        ("Facility Driver Detention Waiting Time", "detention", "4 Hours", "$75.00/hr", "$300.00"),
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
    pdf.cell(30, 7, '$1,975.00  ', align='R')
    pdf.ln(7)

    pdf.set_x(120)
    pdf.set_fill_color(239, 246, 255)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(40, 9, 'TOTAL DUE:', align='R', fill=True)
    pdf.cell(30, 9, '$1,975.00  ', align='R', fill=True)
    pdf.ln(16)

    # Payment Remittance Footer
    pdf.set_text_color(113, 128, 150)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(190, 4, 'Payment Terms: Net 30 Days. Direct ACH Remittance: Chase Bank | Routing: 071000013 | Acct: 9920194812', align='C')
    pdf.ln(4)
    pdf.cell(190, 4, 'For drayage billing inquiries or POD confirmation, contact AP@midwestintermodal.com referencing INV-2026-1055.', align='C')

    output_path = Path("sample_data/midwest_carrier_invoice_2.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    print("Created:", output_path)

if __name__ == "__main__":
    build_pdf_2()
