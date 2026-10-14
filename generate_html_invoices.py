"""
Generate high-fidelity HTML companion invoices for all 4 distinct invoices.
Enables opening invoices directly in Chrome/Edge as an interactive, printable page.
"""

from pathlib import Path
from generate_four_distinct_invoices import invoices

downloads = Path(r"C:\Users\krish\Downloads")
sample_dir = Path("sample_data")
brain_dir = Path(r"C:\Users\krish\.gemini\antigravity\brain\05d6ad1f-097c-4505-acf5-c0509f452813")

downloads.mkdir(parents=True, exist_ok=True)
sample_dir.mkdir(parents=True, exist_ok=True)
brain_dir.mkdir(parents=True, exist_ok=True)

for inv in invoices:
    slug = inv["id_slug"]
    lines_html = ""
    for i, l in enumerate(inv["lines"], 1):
        lines_html += f"""
        <tr>
          <td style="text-align:center; color:#64748b;">{i}</td>
          <td><strong>{l['description']}</strong></td>
          <td style="text-align:center;"><span style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-weight:600; font-size:11px;">{l['type']}</span></td>
          <td style="text-align:center;">{l['qty_str']}</td>
          <td style="text-align:right;">${l['unit_rate']:,.2f}</td>
          <td style="text-align:right; font-weight:700;">${l['amount']:,.2f}</td>
        </tr>"""

    m = inv["milestones"]
    b = inv["bill_to"]
    r = inv["remit_to"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{inv['carrier_name']} - Invoice {inv['invoice_id']}</title>
  <style>
    @page {{ size: letter; margin: 12mm; }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      background: #f1f5f9;
      margin: 0;
      padding: 24px;
      font-size: 13px;
      line-height: 1.5;
    }}
    .sheet {{
      max-width: 820px;
      margin: 0 auto;
      background: #ffffff;
      padding: 36px 40px;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }}
    .top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #cbd5e1;
      padding-bottom: 16px;
      margin-bottom: 20px;
    }}
    .carrier-title {{
      font-size: 20px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.01em;
      margin: 0 0 4px 0;
    }}
    .carrier-sub {{
      font-size: 11px;
      color: #475569;
      font-weight: 600;
      margin: 0 0 2px 0;
    }}
    .carrier-meta {{
      font-size: 11px;
      color: #64748b;
      margin: 0;
    }}
    .invoice-title-block {{
      text-align: right;
    }}
    .invoice-title {{
      font-size: 28px;
      font-weight: 900;
      color: #1e293b;
      margin: 0;
      line-height: 1;
    }}
    .original-billing {{
      font-size: 11px;
      color: #64748b;
      font-weight: 600;
      margin: 4px 0 2px 0;
    }}
    .terms-text {{
      font-size: 11px;
      color: #64748b;
      margin: 0;
    }}
    .remit-banner {{
      font-size: 11px;
      color: #1e40af;
      font-weight: 700;
    }}
    .metadata-strip {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 14px;
      margin-bottom: 20px;
      gap: 8px;
    }}
    .meta-col label {{
      display: block;
      font-size: 10px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 3px;
    }}
    .meta-col div {{
      font-size: 12px;
      font-weight: 700;
      color: #0f172a;
    }}
    .two-box-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 20px;
    }}
    .party-box {{
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 12px 14px;
      background: #ffffff;
    }}
    .party-title {{
      font-size: 11px;
      font-weight: 800;
      color: #475569;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin: 0 0 6px 0;
    }}
    .party-name {{
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      margin: 0 0 3px 0;
    }}
    .party-line {{
      font-size: 11.5px;
      color: #475569;
      margin: 0 0 2px 0;
    }}
    .milestones-card {{
      border: 1px solid #bfdbfe;
      border-radius: 6px;
      background: #f8fafc;
      padding: 12px 14px;
      margin-bottom: 20px;
    }}
    .milestones-title {{
      font-size: 11px;
      font-weight: 800;
      color: #1e40af;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin: 0 0 8px 0;
    }}
    .milestones-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .milestone-item label {{
      display: block;
      font-size: 9.5px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      margin-bottom: 2px;
    }}
    .milestone-item div {{
      font-size: 11.5px;
      font-weight: 600;
      color: #0f172a;
    }}
    .milestone-item .time-val {{
      font-family: monospace;
      font-size: 11.5px;
      font-weight: 700;
      color: #1e40af;
    }}
    table.invoice-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }}
    table.invoice-table th {{
      background: #1e293b;
      color: #ffffff;
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding: 8px 10px;
      text-align: left;
    }}
    table.invoice-table td {{
      padding: 9px 10px;
      border-bottom: 1px solid #e2e8f0;
      font-size: 12px;
    }}
    table.invoice-table tr:nth-child(even) td {{
      background: #f8fafc;
    }}
    .totals-area {{
      display: flex;
      justify-content: flex-end;
      margin-bottom: 24px;
    }}
    .totals-box {{
      width: 280px;
    }}
    .total-row {{
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
      font-size: 12px;
      color: #475569;
    }}
    .total-row.grand {{
      border-top: 2px solid #0f172a;
      margin-top: 4px;
      padding-top: 6px;
      font-size: 16px;
      font-weight: 900;
      color: #0f172a;
    }}
    .total-row.grand .amount {{
      color: #1e40af;
    }}
    .disclaimer-box {{
      border-top: 1px solid #cbd5e1;
      padding-top: 12px;
      font-size: 10px;
      color: #64748b;
      line-height: 1.45;
    }}
    .footer-bar {{
      margin-top: 12px;
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      font-weight: 600;
      color: #94a3b8;
    }}
    @media print {{
      body {{ background: transparent; padding: 0; }}
      .sheet {{ box-shadow: none; padding: 0; }}
      .no-print {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <div style="max-width:820px; margin:0 auto 16px auto; display:flex; justify-content:space-between; align-items:center;" class="no-print">
    <div style="font-size:12px; color:#475569;">
      📄 <strong>Carrier Drayage Invoice Document</strong> &bull; Total: <strong style="color:#1e40af;">${inv['total']:,.2f}</strong>
    </div>
    <div>
      <button onclick="window.print()" style="padding:6px 14px; background:#1e40af; color:#fff; border:none; border-radius:4px; font-weight:600; cursor:pointer;">🖨️ Print / Save PDF</button>
    </div>
  </div>

  <div class="sheet">
    <div class="top-bar">
      <div>
        <h1 class="carrier-title">{inv['carrier_name'].upper()}</h1>
        <p class="carrier-sub">SCAC: {inv['scac']} &nbsp;|&nbsp; USDOT# {inv['dot']} &nbsp;|&nbsp; MC# {inv['mc']} &nbsp;|&nbsp; UIIA CERTIFIED</p>
        <p class="carrier-meta">{inv['address']} &nbsp;|&nbsp; Tel: {inv['phone']}</p>
        <p class="carrier-meta">Billing Dept: {inv['email']}</p>
      </div>
      <div class="invoice-title-block">
        <div class="invoice-title">INVOICE</div>
        <div class="original-billing">ORIGINAL FREIGHT BILLING</div>
        <div class="terms-text">Terms: {inv['terms']}</div>
        <div class="remit-banner">Electronic Remittance Required</div>
      </div>
    </div>

    <div class="metadata-strip">
      <div class="meta-col">
        <label>Invoice Number</label>
        <div>{inv['invoice_id']}</div>
      </div>
      <div class="meta-col">
        <label>Invoice Date</label>
        <div>{inv['invoice_date']}</div>
      </div>
      <div class="meta-col">
        <label>Bill of Lading</label>
        <div>{inv['bol_no']}</div>
      </div>
      <div class="meta-col">
        <label>Container Number</label>
        <div style="color:#1e40af;">{inv['container_no']}</div>
      </div>
      <div class="meta-col">
        <label>Chassis Number</label>
        <div>{inv['chassis_no']}</div>
      </div>
    </div>

    <div class="two-box-grid">
      <div class="party-box">
        <div class="party-title">Bill To (Freight Brokerage):</div>
        <div class="party-name">{b['name']}</div>
        <div class="party-line">{b['attn']}</div>
        <div class="party-line">{b['addr']}</div>
        <div class="party-line">{b['city']}</div>
        <div class="party-line">Email: {b['email']} &nbsp;|&nbsp; Ref: {b['ref']}</div>
      </div>
      <div class="party-box">
        <div class="party-title">Remit Payment To:</div>
        <div class="party-name">{r['name']}</div>
        <div class="party-line">{r['addr']}</div>
        <div class="party-line">{r['bank']}</div>
        <div class="party-line">Routing: {r['routing']} &nbsp;|&nbsp; Account: {r['account']}</div>
        <div class="party-line">Inquiries: {r.get('email', inv['email'])}</div>
      </div>
    </div>

    <div class="milestones-card">
      <div class="milestones-title">Shipment Details &amp; Container Intermodal Milestones</div>
      <div class="milestones-grid" style="margin-bottom:10px;">
        <div class="milestone-item">
          <label>Port Terminal / Origin</label>
          <div>{m['terminal']}</div>
        </div>
        <div class="milestone-item">
          <label>Delivery Facility / Consignee</label>
          <div>{m['delivery_facility']}</div>
        </div>
        <div class="milestone-item">
          <label>Carrier Drop Yard</label>
          <div>{m['drop_lot']}</div>
        </div>
        <div class="milestone-item">
          <label>Empty Return Depot</label>
          <div>{m['return_depot']}</div>
        </div>
      </div>
      <div class="milestones-grid">
        <div class="milestone-item">
          <label>Terminal Out-Gate (Pickup)</label>
          <div class="time-val">{m['pickup_time']}</div>
        </div>
        <div class="milestone-item">
          <label>Delivery Appointment</label>
          <div class="time-val">{m['appt_time']}</div>
        </div>
        <div class="milestone-item">
          <label>Actual Delivery / Drop</label>
          <div class="time-val">{m['delivery_time']}</div>
        </div>
        <div class="milestone-item">
          <label>Empty Returned to Port</label>
          <div class="time-val">{m['return_time']}</div>
        </div>
      </div>
    </div>

    <table class="invoice-table">
      <thead>
        <tr>
          <th style="width:30px; text-align:center;">#</th>
          <th>Description</th>
          <th style="width:100px; text-align:center;">Charge Code</th>
          <th style="width:90px; text-align:center;">Qty / Units</th>
          <th style="width:90px; text-align:right;">Rate</th>
          <th style="width:100px; text-align:right;">Amount ($)</th>
        </tr>
      </thead>
      <tbody>
        {lines_html}
      </tbody>
    </table>

    <div class="totals-area">
      <div class="totals-box">
        <div class="total-row">
          <span>Subtotal:</span>
          <span>${inv['total']:,.2f}</span>
        </div>
        <div class="total-row grand">
          <span>TOTAL AMOUNT DUE:</span>
          <span class="amount">${inv['total']:,.2f}</span>
        </div>
      </div>
    </div>

    <div class="disclaimer-box">
      <strong>AUDIT &amp; CONTRACTUAL COMPLIANCE STATEMENT:</strong><br>
      All container drayage, per diem, chassis, storage, and accessorial movements billed herein are rendered under the standard terms of the Uniform Intermodal Interchange Agreement (UIIA) and Broker-Carrier Agreement Confirmation {b['ref']}. Proof of Delivery (POD) signed by consignee receiving clerk and marine terminal interchange gate receipts (EIR) are maintained in carrier digital archive. Payment is due within 30 days of invoice transmission. For accessorial disputes or formal debit memos, contact {r.get('email', inv['email'])} referencing Invoice # {inv['invoice_id']} within 10 business days.
    </div>

    <div class="footer-bar">
      <span>{inv['carrier_name']} &nbsp;|&nbsp; MC# {inv['mc']} &nbsp;|&nbsp; USDOT# {inv['dot']} &nbsp;|&nbsp; SCAC: {inv['scac']}</span>
      <span>Page 1 of 1 &nbsp;|&nbsp; Generated by Intermodal EDI System</span>
    </div>
  </div>
</body>
</html>"""

    (downloads / f"{slug}.html").write_text(html, encoding="utf-8")
    (sample_dir / f"{slug}.html").write_text(html, encoding="utf-8")
    (brain_dir / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"Generated HTML: {downloads / f'{slug}.html'}")
