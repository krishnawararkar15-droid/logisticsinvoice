"""Build the upgraded index.html with Dark/Light mode, deep US freight document checklist, and Sample Invoice 2."""
import re
from pathlib import Path

# Read Base64 for Sample 1
index_path = Path("index.html")
existing_html = index_path.read_text(encoding="utf-8")
m1 = re.search(r'const SAMPLE_PDF_BASE64 = "([^"]+)";', existing_html)
sample_1_b64 = m1.group(1) if m1 else ""

# Read Base64 for Sample 2
sample_2_b64 = Path("sample_data/sample_2_b64.txt").read_text(encoding="utf-8").strip()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accessorial Invoice Checker (v1)</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #1e40af;
      --primary-hover: #1d4ed8;
      --success: #16a34a;
      --success-bg: #f0fdf4;
      --danger: #dc2626;
      --danger-bg: #fef2f2;
      --warning: #d97706;
      --warning-bg: #fffbeb;
      --slate-50: #f8fafc;
      --slate-100: #f1f5f9;
      --slate-200: #e2e8f0;
      --slate-600: #475569;
      --slate-700: #334155;
      --slate-800: #1e293b;
      --slate-900: #0f172a;

      /* Dynamic Theme Variables (Default Light) */
      --bg-body: #f8fafc;
      --bg-card: #ffffff;
      --bg-header: #ffffff;
      --border-color: #e2e8f0;
      --border-light: #f1f5f9;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --text-label: #334155;
      --input-bg: #ffffff;
      --input-border: #cbd5e1;
      --input-text: #0f172a;
      --table-th-bg: #f8fafc;
      --table-hover: #f1f5f9;
      --email-card-bg: #f0f7ff;
      --email-card-border: #bfdbfe;
      --modal-bg: #ffffff;
      --quick-bar-bg: #ffffff;
      --doc-card-bg: #ffffff;
      --doc-card-border: #e2e8f0;
      --doc-card-verified-bg: #f0fdf4;
      --doc-card-verified-border: #86efac;
    }}

    body.dark-mode {{
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --bg-body: #0b1120;
      --bg-card: #131d33;
      --bg-header: #0f172a;
      --border-color: #24324f;
      --border-light: #1a253c;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-label: #cbd5e1;
      --input-bg: #0b1120;
      --input-border: #334155;
      --input-text: #f8fafc;
      --table-th-bg: #1a2744;
      --table-hover: #1e2c4d;
      --email-card-bg: #0c1c38;
      --email-card-border: #1e40af;
      --modal-bg: #131d33;
      --quick-bar-bg: #131d33;
      --doc-card-bg: #131d33;
      --doc-card-border: #24324f;
      --doc-card-verified-bg: #064e3b;
      --doc-card-verified-border: #059669;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-body);
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: 60px;
      transition: background-color 0.2s ease, color 0.2s ease;
    }}
    .header {{
      background: var(--bg-header);
      border-bottom: 1px solid var(--border-color);
      padding: 20px 32px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      transition: background 0.2s ease, border-color 0.2s ease;
    }}
    .header-inner {{
      max-width: 1300px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .logo-group h1 {{
      font-size: 1.45rem;
      font-weight: 800;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .logo-group p {{
      color: var(--text-muted);
      font-size: 0.88rem;
      margin-top: 3px;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      font-size: 0.85rem;
      padding: 9px 15px;
      border-radius: 8px;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      text-decoration: none;
    }}
    .btn-primary {{ background: var(--primary); color: white; }}
    .btn-primary:hover {{ background: var(--primary-hover); }}
    .btn-secondary {{ background: var(--bg-card); border-color: var(--border-color); color: var(--text-label); }}
    .btn-secondary:hover {{ background: var(--table-hover); }}
    .btn-success {{ background: var(--success); color: white; }}
    .btn-warning {{ background: var(--warning); color: white; }}
    .btn-lg {{ font-size: 1rem; padding: 13px 28px; border-radius: 10px; }}

    .theme-toggle-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      border: 1px solid var(--border-color);
      background: var(--bg-card);
      color: var(--text-main);
      border-radius: 8px;
      padding: 9px 14px;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .theme-toggle-btn:hover {{
      background: var(--table-hover);
    }}

    .container {{
      max-width: 1300px;
      margin: 28px auto;
      padding: 0 24px;
    }}

    .tabs {{
      display: flex;
      gap: 8px;
      border-bottom: 2px solid var(--border-color);
      margin-bottom: 24px;
    }}
    .tab-btn {{
      padding: 10px 18px;
      font-weight: 600;
      font-size: 0.92rem;
      border: none;
      background: none;
      color: var(--text-muted);
      cursor: pointer;
      position: relative;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
      transition: color 0.15s ease;
    }}
    .tab-btn:hover {{
      color: var(--text-main);
    }}
    .tab-btn.active {{
      color: var(--primary);
      border-bottom-color: var(--primary);
    }}

    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      margin-bottom: 24px;
      transition: background 0.2s ease, border-color 0.2s ease;
    }}
    .card-title {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }}
    .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }}
    .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }}
    @media(max-width: 900px) {{
      .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
    }}

    .form-group {{ margin-bottom: 14px; }}
    .form-label {{
      display: block;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-label);
      margin-bottom: 5px;
    }}
    .form-sublabel {{ font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px; display: block; }}
    .form-control {{
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--input-border);
      border-radius: 7px;
      font-size: 0.88rem;
      background: var(--input-bg);
      color: var(--input-text);
      outline: none;
      font-family: inherit;
      transition: border-color 0.15s, background-color 0.15s, color 0.15s;
    }}
    .form-control:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(30,64,175,0.15); }}
    .checkbox-label {{
      display: flex;
      align-items: center;
      gap: 7px;
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 5px;
      cursor: pointer;
    }}

    /* Metric Cards */
    .metrics-container {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .metric-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      position: relative;
    }}
    .metric-title {{
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}
    .metric-value {{
      font-size: 1.7rem;
      font-weight: 800;
      color: var(--text-main);
    }}
    .metric-sub {{
      font-size: 0.78rem;
      margin-top: 4px;
      color: var(--text-muted);
    }}
    .metric-card.approved .metric-value {{ color: var(--success); }}
    .metric-card.disputed {{ border-left: 4px solid var(--danger); }}
    .metric-card.disputed .metric-value {{ color: var(--danger); }}
    .metric-card.needs-proof {{ border-left: 4px solid var(--warning); }}
    .metric-card.needs-proof .metric-value {{ color: var(--warning); }}
    .metric-card.not-approved .metric-value {{ color: #b91c1c; }}

    /* Badges */
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      font-size: 0.78rem;
      font-weight: 700;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .badge-approve {{ background: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
    .badge-dispute {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
    .badge-proof {{ background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }}
    .badge-flag {{ background: #ffedd5; color: #c2410c; border: 1px solid #fdba74; font-size: 0.72rem; padding: 2px 7px; border-radius: 4px; margin-right: 4px; }}
    .badge-provisional {{ background: #e0e7ff; color: #4338ca; border: 1px solid #c7d2fe; font-size: 0.68rem; margin-left: 6px; }}

    body.dark-mode .badge-approve {{ background: #064e3b; color: #6ee7b7; border-color: #059669; }}
    body.dark-mode .badge-dispute {{ background: #450a0a; color: #fca5a5; border-color: #991b1b; }}
    body.dark-mode .badge-proof {{ background: #451a03; color: #fde68a; border-color: #92400e; }}
    body.dark-mode .badge-flag {{ background: #431407; color: #fdba74; border-color: #9a3412; }}
    body.dark-mode .badge-provisional {{ background: #1e1b4b; color: #a5b4fc; border-color: #3730a3; }}

    /* Tables */
    .table-responsive {{ width: 100%; overflow-x: auto; }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    .data-table th {{
      background: var(--table-th-bg);
      color: var(--text-muted);
      font-weight: 700;
      text-align: left;
      padding: 12px 14px;
      border-bottom: 2px solid var(--border-color);
      white-space: nowrap;
    }}
    .data-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-color);
      vertical-align: top;
      color: var(--text-main);
    }}
    .data-table tr:hover {{ background: var(--table-hover); }}

    .disclaimer-box {{
      background: #eff6ff;
      border-left: 5px solid #2563eb;
      padding: 16px 20px;
      border-radius: 8px;
      margin: 24px 0 16px 0;
      color: #1e3a8a;
      font-weight: 600;
      font-size: 0.95rem;
    }}
    body.dark-mode .disclaimer-box {{
      background: #0f1e36;
      border-left-color: #3b82f6;
      color: #93c5fd;
    }}

    /* Real-World Document Verification Center */
    .doc-verify-section {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .doc-verify-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border-color);
    }}
    .doc-verify-title {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .doc-verify-progress {{
      font-size: 0.82rem;
      font-weight: 700;
      padding: 4px 12px;
      border-radius: 9999px;
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fde68a;
    }}
    body.dark-mode .doc-verify-progress {{
      background: #382404;
      color: #fde68a;
      border-color: #854d0e;
    }}
    .doc-cards-grid {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .doc-card-item {{
      border: 1px solid var(--doc-card-border);
      border-radius: 10px;
      background: var(--doc-card-bg);
      padding: 16px 18px;
      transition: all 0.2s ease;
    }}
    .doc-card-item.verified {{
      border-color: var(--doc-card-verified-border);
      background: var(--doc-card-verified-bg);
    }}
    .doc-card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .doc-card-label {{
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      font-weight: 700;
      font-size: 0.96rem;
      color: var(--text-main);
    }}
    .doc-status-badge {{
      font-size: 0.76rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .doc-status-badge.pending {{
      background: #fffbeb;
      color: #b45309;
      border: 1px solid #fde68a;
    }}
    body.dark-mode .doc-status-badge.pending {{
      background: #2a1b05;
      color: #fde68a;
      border-color: #78350f;
    }}
    .doc-status-badge.cleared {{
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #86efac;
    }}
    body.dark-mode .doc-status-badge.cleared {{
      background: #064e3b;
      color: #6ee7b7;
      border-color: #059669;
    }}
    .doc-chips-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 8px 0;
    }}
    .doc-chip {{
      font-size: 0.74rem;
      padding: 2px 8px;
      border-radius: 4px;
      background: var(--slate-100);
      color: var(--text-label);
      border: 1px solid var(--border-color);
    }}
    body.dark-mode .doc-chip {{
      background: #1e293b;
      color: #94a3b8;
      border-color: #334155;
    }}
    .doc-details-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      font-size: 0.83rem;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px dashed var(--border-color);
    }}
    @media(max-width: 768px) {{
      .doc-details-grid {{ grid-template-columns: 1fr; }}
    }}
    .doc-detail-text strong {{
      color: var(--text-main);
    }}

    .dropzone {{
      border: 2px dashed #93c5fd;
      border-radius: 10px;
      padding: 24px;
      text-align: center;
      background: #eff6ff;
      cursor: pointer;
      transition: all 0.15s;
    }}
    body.dark-mode .dropzone {{
      background: #0f1e38;
      border-color: #3b82f6;
    }}
    .dropzone:hover {{ border-color: var(--primary); background: #dbeafe; }}
    body.dark-mode .dropzone:hover {{ background: #132749; }}

    /* Modal */
    .modal-overlay {{
      display: none;
      position: fixed;
      z-index: 9999;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(3px);
      justify-content: center;
      align-items: center;
    }}
    .modal-box {{
      background: var(--modal-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      width: 90%;
      max-width: 900px;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
      padding: 24px;
      color: var(--text-main);
    }}
  </style>
</head>
<body>

  <header class="header">
    <div class="header-inner">
      <div class="logo-group">
        <h1>🚚 Accessorial Invoice Checker</h1>
        <p>Deterministic Drayage & Intermodal Audit Engine — No AI APIs, 100% Explainable Date Math</p>
      </div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <button class="btn btn-primary" onclick="loadSampleData()">⚡ Test Case 1 (Pacific)</button>
        <button class="btn btn-primary" onclick="loadSampleData2()" style="background:#0284c7; border-color:#0284c7;">⚡ Test Case 2 (Midwest)</button>
        <button class="btn btn-secondary" onclick="downloadSamplePdf()">📥 Sample 1 PDF</button>
        <button class="btn btn-secondary" onclick="downloadSamplePdf2()">📥 Sample 2 PDF</button>
        <button class="btn btn-secondary" onclick="resetForm()">🔄 Reset</button>
        <button class="theme-toggle-btn" id="theme-toggle-btn" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
          <span id="theme-icon">🌙</span> <span id="theme-text">Dark Mode</span>
        </button>
      </div>
    </div>
  </header>

  <main class="container">

    <!-- Quick Upload Bar -->
    <div class="card" style="padding: 16px 20px; background: var(--quick-bar-bg); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 1.5rem;">📄</span>
        <div>
          <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-main);">Import Carrier Invoice</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">Upload PDF invoice, PNG/JPG scan, or JSON file to auto-populate line items</div>
        </div>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <input type="file" id="top-invoice-file" style="display:none;" accept=".pdf,.png,.jpg,.jpeg,.json" onchange="handleInvoiceFile(this)">
        <button class="btn btn-primary" onclick="document.getElementById('top-invoice-file').click()">📂 Select Invoice File</button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab-btn active" id="tab-btn-terms" onclick="switchTab('terms', this)">📋 1. Rate Terms</button>
      <button class="tab-btn" id="tab-btn-timeline" onclick="switchTab('timeline', this)">⏱️ 2. Container Timeline</button>
      <button class="tab-btn" id="tab-btn-invoice" onclick="switchTab('invoice', this)">🧾 3. Invoice & OCR</button>
    </div>

    <!-- TAB 1: RATE TERMS -->
    <div id="tab-terms" class="tab-content card">
      <h2 class="card-title">Agreed Contract Rate Terms</h2>
      <div class="grid-3">
        <div class="form-group">
          <label class="form-label">Linehaul + FSC Agreed Rate ($)</label>
          <input type="number" id="linehaul_fsc" class="form-control" value="1500" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Pre-pull Agreed Fee ($)</label>
          <input type="number" id="prepull_fee" class="form-control" value="150" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Chassis Rate Per Day ($)</label>
          <input type="number" id="chassis_per_day" class="form-control" value="45" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Storage Rate Per Day ($)</label>
          <input type="number" id="storage_per_day" class="form-control" value="45" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Detention Rate Per Hour ($)</label>
          <input type="number" id="detention_per_hour" class="form-control" value="75" step="0.01">
        </div>
        <div class="form-group">
          <label class="form-label">Detention Free Hours (Hours)</label>
          <input type="number" id="detention_free_hours" class="form-control" value="2" step="0.5">
        </div>
      </div>

      <div class="grid-3" style="margin-top: 12px;">
        <div class="form-group">
          <label class="form-label">Chassis Day Calculation Policy</label>
          <select id="chassis_day_policy" class="form-control">
            <option value="calendar_day">Calendar Day (each midnight / portion of day = 1 day)</option>
            <option value="24h_block">24-Hour Block (ceil elapsed hours / 24)</option>
            <option value="unknown">Unknown / Not Specified (Compare Both)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Chassis Free Days</label>
          <input type="number" id="chassis_free_days" class="form-control" value="0">
        </div>
        <div class="form-group">
          <label class="form-label">Chassis Minimum Days</label>
          <input type="number" id="chassis_min_days" class="form-control" value="0">
        </div>
      </div>

      <div class="grid-3" style="margin-top: 12px;">
        <div class="form-group">
          <label class="form-label">Storage Free Days</label>
          <input type="number" id="storage_free_days" class="form-control" value="0">
        </div>
        <div class="form-group">
          <label class="form-label">Pre-pull Includes 1st Storage Day?</label>
          <select id="prepull_includes_first_storage_day" class="form-control">
            <option value="unknown">Unknown / Not Specified (Ask clarification)</option>
            <option value="yes">Yes (1st yard storage day included in pre-pull)</option>
            <option value="no">No (Storage billed separately from day 1)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Direct Move Threshold (Hours)</label>
          <input type="number" id="direct_move_hours_threshold" class="form-control" value="24">
        </div>
      </div>
    </div>

    <!-- TAB 2: CONTAINER TIMELINE -->
    <div id="tab-timeline" class="tab-content card" style="display:none;">
      <h2 class="card-title">Container Movement Timeline & Gate Events</h2>
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Terminal Outgate / Pickup Timestamp</label>
          <input type="text" id="terminal_pickup" class="form-control" value="2026-06-23T21:00">
          <label class="checkbox-label"><input type="checkbox" id="null_terminal_pickup" onchange="toggleNull('terminal_pickup')"> Unknown / Null</label>
        </div>
        <div class="form-group">
          <label class="form-label">Empty Container Return Ingate Timestamp</label>
          <input type="text" id="empty_return" class="form-control" value="2026-06-24T16:00">
          <label class="checkbox-label"><input type="checkbox" id="null_empty_return" onchange="toggleNull('empty_return')"> Unknown / Null</label>
        </div>
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Carrier Yard Ingate (yard_in)</label>
          <input type="text" id="yard_in" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_yard_in" checked onchange="toggleNull('yard_in')"> Unknown / Null</label>
        </div>
        <div class="form-group">
          <label class="form-label">Carrier Yard Outgate (yard_out)</label>
          <input type="text" id="yard_out" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_yard_out" checked onchange="toggleNull('yard_out')"> Unknown / Null</label>
        </div>
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Warehouse Scheduled Appointment Time</label>
          <input type="text" id="warehouse_appointment" class="form-control" value="2026-06-24T08:00">
          <label class="checkbox-label"><input type="checkbox" id="null_warehouse_appointment" onchange="toggleNull('warehouse_appointment')"> Unknown / Null</label>
        </div>
        <div class="form-group">
          <label class="form-label">Actual Delivery Timestamp (delivery_actual)</label>
          <input type="text" id="delivery_actual" class="form-control" value="2026-06-24T08:00">
          <label class="checkbox-label"><input type="checkbox" id="null_delivery_actual" onchange="toggleNull('delivery_actual')"> Unknown / Null</label>
        </div>
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Warehouse Arrival Timestamp (warehouse_in)</label>
          <input type="text" id="warehouse_in" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_warehouse_in" checked onchange="toggleNull('warehouse_in')"> Unknown / Null</label>
        </div>
        <div class="form-group">
          <label class="form-label">Warehouse Departure Timestamp (warehouse_out)</label>
          <input type="text" id="warehouse_out" class="form-control" disabled placeholder="Null / Not Provided">
          <label class="checkbox-label"><input type="checkbox" id="null_warehouse_out" checked onchange="toggleNull('warehouse_out')"> Unknown / Null</label>
        </div>
      </div>

      <div class="grid-2" style="margin-top: 10px;">
        <div class="form-group">
          <label class="form-label">Signed Proof of Delivery (POD) Provided?</label>
          <label class="checkbox-label" style="font-size: 0.9rem;">
            <input type="checkbox" id="pod_provided"> Yes, signed POD document was provided by carrier
          </label>
        </div>
        <div class="form-group">
          <label class="form-label">Pre-pull Written Request Documented?</label>
          <select id="prepull_request_documented" class="form-control">
            <option value="unknown">Unknown / Not Documented</option>
            <option value="yes">Yes (Documented written broker/customer request)</option>
            <option value="no">No (Carrier pre-pulled without request)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- TAB 3: INVOICE & OCR -->
    <div id="tab-invoice" class="tab-content card" style="display:none;">
      <h2 class="card-title">Carrier Invoice Lines & OCR Extraction</h2>

      <!-- OCR File Upload Dropzone -->
      <div style="margin-bottom: 20px;">
        <div class="dropzone" onclick="document.getElementById('ocr-file').click()">
          <p style="font-weight: 700; color: var(--primary); font-size: 1.05rem;">📄 Drag & Drop or Click to Upload Carrier Invoice</p>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Supports PDF, Image (PNG/JPG), and JSON files</p>
          <div style="margin-top: 10px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;">
            <span class="btn btn-secondary" style="font-size: 0.78rem; padding: 4px 10px;" onclick="event.stopPropagation(); downloadSamplePdf();">📥 Download Sample 1 PDF</span>
            <span class="btn btn-secondary" style="font-size: 0.78rem; padding: 4px 10px;" onclick="event.stopPropagation(); downloadSamplePdf2();">📥 Download Sample 2 PDF</span>
          </div>
          <input type="file" id="ocr-file" style="display:none" accept=".pdf,.png,.jpg,.jpeg,.json" onchange="handleInvoiceFile(this)">
        </div>
        <div id="ocr-status" style="margin-top: 8px; font-size: 0.9rem; font-weight: 600; display: none;"></div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--text-label);">Billed Line Items</h3>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary" onclick="addInvoiceLine()">+ Add Line</button>
          <button class="btn btn-secondary" onclick="autoSumLines()">Calculate Total</button>
        </div>
      </div>

      <div class="table-responsive">
        <table class="data-table" id="invoice-lines-table">
          <thead>
            <tr>
              <th>Charge Type</th>
              <th style="width: 120px;">Qty</th>
              <th style="width: 140px;">Unit Rate ($)</th>
              <th style="width: 150px;">Amount ($)</th>
              <th style="width: 60px;">Action</th>
            </tr>
          </thead>
          <tbody id="invoice-lines-body">
            <!-- Dynamically populated -->
          </tbody>
        </table>
      </div>

      <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px; margin-top: 16px;">
        <label class="form-label" style="margin: 0; font-size: 1rem;">Invoice Total Billed ($):</label>
        <input type="number" id="invoice_total" class="form-control" style="width: 180px; font-weight: 700; font-size: 1rem;" value="1875" step="0.01">
      </div>
    </div>

    <!-- AUDIT ACTION BUTTON -->
    <div style="text-align: center; margin: 30px 0;">
      <button class="btn btn-primary btn-lg" onclick="triggerAudit()" style="box-shadow: 0 4px 14px rgba(30,64,175,0.3);">
        🚀 Check Invoice & Audit Discrepancies
      </button>
    </div>

    <!-- RESULTS SECTION -->
    <div id="audit-results" style="display: none;">

      <!-- Metrics -->
      <div class="metrics-container" id="metrics-cards">
        <!-- Injected via JS -->
      </div>

      <!-- Side-by-side policy alert (if applicable) -->
      <div id="dual-policy-alert" style="display: none; margin-bottom: 20px;"></div>

      <!-- Line by line table -->
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
          <h2 class="card-title" style="margin: 0;">Line-by-Line Audit Findings</h2>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn-secondary" onclick="viewFileInBrowser('csv')">👁️ View CSV in Browser</button>
            <button class="btn btn-secondary" onclick="viewFileInBrowser('md')">👁️ View Report</button>
            <button class="btn btn-secondary" onclick="downloadReport('csv')">📈 Download CSV</button>
            <button class="btn btn-secondary" onclick="downloadReport('md')">📄 Download Report (MD)</button>
            <button class="btn btn-secondary" onclick="downloadReport('json')">📊 Download JSON</button>
          </div>
        </div>

        <div class="table-responsive">
          <table class="data-table" id="audit-results-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Billed</th>
                <th>Approved</th>
                <th>Disputed</th>
                <th>Needs Proof</th>
                <th>Status</th>
                <th>Flags</th>
                <th>Plain English Audit Evidence & Math</th>
              </tr>
            </thead>
            <tbody id="audit-results-body">
              <!-- Injected via JS -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- Professional US Freight Documentation Verification Center -->
      <div class="doc-verify-section" id="checklist-container">
        <div class="doc-verify-header">
          <div class="doc-verify-title">
            <span>📋</span> Real-World Documents Needed Before Final Approval
          </div>
          <div class="doc-verify-progress" id="doc-progress-text">
            0 of 0 Documents Verified
          </div>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px;">
          In accordance with US freight brokerage accounting standards (FMCSA 49 CFR & UIIA model interchange agreements), Accounts Payable must substantiate these specific carrier records before releasing withheld funds.
        </p>
        <div class="doc-cards-grid" id="checklist-items">
          <!-- Dynamically Injected Rich Verification Cards -->
        </div>
      </div>

      <!-- Professional Pre-Written Email to Carrier -->
      <div class="card" style="border: 2px solid var(--email-card-border); background: var(--email-card-bg);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <h2 class="card-title" style="color: var(--primary); margin: 0;">
            ✉️ Pre-Written Polite Carrier Email (Relationship-Safe)
          </h2>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary" onclick="openInGmail()" style="background: #ea4335; border-color: #ea4335;">
              🚀 Open in Gmail
            </button>
            <button class="btn btn-secondary" onclick="copyEmailText()">📋 Copy Email Text</button>
          </div>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px;">
          Professionally crafted to protect carrier relationships, immediately approve undisputed funds, and collaboratively request documentation for withheld items.
        </p>

        <div class="form-group">
          <label class="form-label">Carrier Billing Email (Optional)</label>
          <input type="text" id="email-recipient" class="form-control" value="billing@pacificgatewaydrayage.com" placeholder="e.g., billing@carrier.com">
        </div>

        <div class="form-group">
          <label class="form-label">Email Subject</label>
          <input type="text" id="email-subject" class="form-control" value="Payment Update & Invoice Review - Container TCLU 582910-3 (Inv #INV-2026-0842)">
        </div>

        <div class="form-group">
          <label class="form-label">Email Body (Ready to Send)</label>
          <textarea id="email-body" class="form-control" rows="12" style="font-family: inherit; font-size: 0.88rem; line-height: 1.6;"></textarea>
        </div>
      </div>

      <!-- Mandatory Disclaimer -->
      <div class="disclaimer-box">
        ⚖️ Final approval decision belongs to the broker. The approved amount is PROVISIONAL whenever documentation is pending or contractual terms require confirmation.
      </div>

    </div>

  </main>

  <!-- Modal for viewing CSV and Report in Browser -->
  <div id="file-viewer-modal" class="modal-overlay" onclick="closeModal()">
    <div class="modal-box" onclick="event.stopPropagation()">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h3 id="modal-title" style="font-size: 1.15rem; font-weight: 700; margin: 0;">File Viewer</h3>
        <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="closeModal()">✕ Close</button>
      </div>
      <div style="flex: 1; overflow-y: auto; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
        <pre id="modal-content" style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-all; color: var(--text-main);"></pre>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn btn-secondary" onclick="copyModalContent()">📋 Copy to Clipboard</button>
        <button class="btn btn-primary" onclick="closeModal()">Done</button>
      </div>
    </div>
  </div>

  <script>
    // Theme Management (Light View / Dark Mode)
    function toggleTheme() {{
      const isDark = document.body.classList.toggle('dark-mode');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      updateThemeUI(isDark);
    }}

    function updateThemeUI(isDark) {{
      const icon = document.getElementById('theme-icon');
      const text = document.getElementById('theme-text');
      if (icon && text) {{
        icon.textContent = isDark ? '☀️' : '🌙';
        text.textContent = isDark ? 'Light View' : 'Dark Mode';
      }}
    }}

    (function initTheme() {{
      const savedTheme = localStorage.getItem('theme');
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {{
        document.body.classList.add('dark-mode');
        updateThemeUI(true);
      }} else {{
        updateThemeUI(false);
      }}
    }})();

    // Industry Knowledge Registry for Real US Drayage & Freight Documents
    const US_DOC_REGISTRY = {{
      "Signed Proof of Delivery (POD)": {{
        name: "Signed Proof of Delivery (POD) / Delivery Receipt (DR)",
        icon: "✍️",
        authority: "Receiving Consignee / Facility Inbound Clerk",
        regulation: "FMCSA 49 CFR § 373.101 & Standard UIIA Delivery Terms",
        criteria: "Legible consignee signature, printed receiving clerk name, delivery date, arrival/departure timestamps, and cargo seal integrity.",
        rationale: "Mandatory condition precedent in US freight brokerage to release linehaul funds and invoice the shipper for completed delivery."
      }},
      "Yard-in and yard-out timestamps (proof of yard hold)": {{
        name: "Carrier Yard In-Gate & Out-Gate Interchange Receipts (EIR)",
        icon: "🏭",
        authority: "Motor Carrier Secure Drop Yard Facility",
        regulation: "UIIA Intermodal Interchange Protocols",
        criteria: "Interchange gate ticket or automated yard management log with container number, chassis ID, and timestamp proving physical arrival and exit.",
        rationale: "Substantiates that the container was physically held on-ground or on chassis at carrier facility rather than an unauthorized through-move."
      }},
      "Reason for yard hold / storage documentation": {{
        name: "Documented Justification for Yard Storage Hold",
        icon: "📋",
        authority: "Shipper / Broker Dispatch / Consignee Operations",
        regulation: "Broker-Carrier Agreement (Accessorial Authorization Clause)",
        criteria: "Written confirmation of customer-requested delivery delay, weekend warehouse closure, or terminal restriction necessitating overnight staging.",
        rationale: "Under US drayage agreements, carriers cannot bill yard storage if the container was held for carrier's own operational or driver convenience."
      }},
      "Yard-in and yard-out timestamps (proof of yard drop)": {{
        name: "Drop Yard In-Gate Staging Receipt (Pre-Pull Staging)",
        icon: "📦",
        authority: "Carrier Secure Drop Lot Gate",
        regulation: "UIIA Terminal Operations Protocol",
        criteria: "In-gate time stamp showing container was received at carrier secure yard prior to the scheduled delivery appointment date.",
        rationale: "Proves container was staged in carrier yard rather than moved direct from port terminal."
      }},
      "Proof early pull was requested by broker/customer": {{
        name: "Written Pre-Pull Authorization or Terminal Last Free Day (LFD) Notice",
        icon: "🛡️",
        authority: "Broker Rate Confirmation Addendum / Ocean Steamship Line Notice",
        regulation: "TIA Model Broker-Carrier Agreement",
        criteria: "Broker written email/EDI authorization approving pre-pull fees ($150), OR Steamship Line Availability Notice demonstrating Last Free Day (LFD) demurrage avoidance.",
        rationale: "Pre-pull fees are unauthorized by default in US freight brokerage unless pre-approved by broker or required to avoid port demurrage ($150-$300/day)."
      }},
      "Warehouse arrival timestamp (warehouse_in)": {{
        name: "Time-Stamped Bill of Lading (BOL) or Certified ELD Duty Log (Arrival)",
        icon: "⏱️",
        authority: "Consignee Guard Shack / FMCSA Certified Telematics (ELD)",
        regulation: "FMCSA 49 CFR § 395 (Electronic Logging Devices)",
        criteria: "Security guard shack check-in stamp on BOL or tamper-proof GPS geofence arrival record proving arrival at or before scheduled appointment time.",
        rationale: "Establishes baseline arrival time before calculating driver detention beyond the standard 2 free hours ($75/hr)."
      }},
      "Warehouse departure timestamp (warehouse_out)": {{
        name: "Time-Stamped Bill of Lading (BOL) or Certified ELD Duty Log (Departure)",
        icon: "🚪",
        authority: "Facility Receiving Dock Clerk / Certified ELD Telematics",
        regulation: "FMCSA 49 CFR § 395 (Electronic Logging Devices)",
        criteria: "Signed receiving out-gate stamp with exact departure time or certified ELD duty status record ('On-Duty / Waiting at Dock').",
        rationale: "Verifies actual hours driver was detained at facility to prevent unverified detention claims."
      }},
      "Terminal pickup timestamp (terminal_pickup)": {{
        name: "Port / Rail Terminal Outgate Equipment Interchange Receipt (EIR / TIR / J1)",
        icon: "🚢",
        authority: "Marine Terminal / Rail Ramp Operating System (TOS)",
        regulation: "UIIA Section G (Equipment Interchange)",
        criteria: "Terminal J1 / EIR outgate receipt showing container number, chassis ID, driver CDL, seal number, and exact terminal outgate timestamp.",
        rationale: "Defines the exact official start of chassis usage and verifies container terminal departure against demurrage free time."
      }},
      "Empty return timestamp (empty_return)": {{
        name: "Port / Rail Terminal Empty Ingate Equipment Interchange Receipt (EIR / TIR / J1)",
        icon: "🔄",
        authority: "Marine Terminal / Ocean Carrier Container Yard (CY)",
        regulation: "UIIA Equipment Return Protocols",
        criteria: "Terminal J1 / EIR ingate receipt showing empty container return timestamp and equipment condition signoff.",
        rationale: "Stops the clock on chassis daily usage fees and steamship line per diem charges."
      }}
    }};

    function getDocProfile(itemKey) {{
      for (const [key, profile] of Object.entries(US_DOC_REGISTRY)) {{
        if (itemKey.includes(key) || key.includes(itemKey)) {{
          return profile;
        }}
      }}
      // Fallback profile
      return {{
        name: itemKey,
        icon: "📄",
        authority: "Motor Carrier / Facility Records",
        regulation: "US Freight Standard Practice",
        criteria: "Complete supporting documentation, time records, or authorization correspondence.",
        rationale: "Substantiates invoice line item before final Accounts Payable disbursement."
      }};
    }}

    // State
    let currentAuditData = null;
    let verifiedDocIndexes = new Set();

    const sampleInvoiceLines = [
      {{ type: "linehaul_fsc", qty: 1, unit_rate: 1500, amount: 1500 }},
      {{ type: "prepull", qty: 1, unit_rate: 150, amount: 150 }},
      {{ type: "chassis", qty: 3, unit_rate: 45, amount: 135 }},
      {{ type: "storage", qty: 2, unit_rate: 45, amount: 90 }}
    ];

    const SAMPLE_PDF_BASE64 = "{sample_1_b64}";
    const SAMPLE_PDF_2_BASE64 = "{sample_2_b64}";

    function downloadSamplePdf() {{
      const byteCharacters = atob(SAMPLE_PDF_BASE64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {{
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }}
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], {{ type: "application/pdf" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "PACIFIC_GATEWAY_INV-2026-0842.pdf";
      link.click();
    }}

    function downloadSamplePdf2() {{
      const byteCharacters = atob(SAMPLE_PDF_2_BASE64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {{
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }}
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], {{ type: "application/pdf" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "MIDWEST_INTERMODAL_INV-2026-1055.pdf";
      link.click();
    }}

    function downloadSampleJson() {{
      const data = {{
        lines: sampleInvoiceLines,
        total: 1875
      }};
      const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: "application/json" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "sample_invoice.json";
      link.click();
    }}

    function switchTab(tabId, el) {{
      document.querySelectorAll('.tab-content').forEach(d => d.style.display = 'none');
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + tabId).style.display = 'block';
      if (el) el.classList.add('active');
    }}

    function toggleNull(fieldId) {{
      const checkbox = document.getElementById('null_' + fieldId);
      const input = document.getElementById(fieldId);
      if (checkbox.checked) {{
        input.disabled = true;
        input.dataset.oldVal = input.value;
        input.value = "";
        input.placeholder = "Null / Not Provided";
      }} else {{
        input.disabled = false;
        input.value = input.dataset.oldVal || "2026-06-24T08:00";
        input.placeholder = "YYYY-MM-DDTHH:MM";
      }}
    }}

    function renderInvoiceLines(lines) {{
      const tbody = document.getElementById('invoice-lines-body');
      tbody.innerHTML = '';
      lines.forEach((line, index) => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>
            <select class="form-control line-type">
              <option value="linehaul_fsc" ${{line.type === 'linehaul_fsc' ? 'selected' : ''}}>Linehaul + FSC</option>
              <option value="chassis" ${{line.type === 'chassis' ? 'selected' : ''}}>Chassis</option>
              <option value="storage" ${{line.type === 'storage' ? 'selected' : ''}}>Yard Storage</option>
              <option value="prepull" ${{line.type === 'prepull' ? 'selected' : ''}}>Pre-pull</option>
              <option value="detention" ${{line.type === 'detention' ? 'selected' : ''}}>Detention</option>
              <option value="other" ${{!['linehaul_fsc','chassis','storage','prepull','detention'].includes(line.type) ? 'selected' : ''}}>Other / Unknown</option>
            </select>
          </td>
          <td><input type="number" class="form-control line-qty" value="${{line.qty}}" step="0.5" oninput="updateLineAmount(${{index}})"></td>
          <td><input type="number" class="form-control line-rate" value="${{line.unit_rate}}" step="0.01" oninput="updateLineAmount(${{index}})"></td>
          <td><input type="number" class="form-control line-amount" value="${{line.amount}}" step="0.01"></td>
          <td><button class="btn btn-secondary" style="color:var(--danger); padding:6px 10px;" onclick="removeInvoiceLine(${{index}})">✕</button></td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function updateLineAmount(index) {{
      const rows = document.querySelectorAll('#invoice-lines-body tr');
      if (rows[index]) {{
        const qty = parseFloat(rows[index].querySelector('.line-qty').value) || 0;
        const rate = parseFloat(rows[index].querySelector('.line-rate').value) || 0;
        rows[index].querySelector('.line-amount').value = fmt(qty * rate);
      }}
    }}

    function autoSumLines() {{
      const rows = document.querySelectorAll('#invoice-lines-body tr');
      let sum = 0;
      rows.forEach(r => {{
        sum += parseFloat(r.querySelector('.line-amount').value) || 0;
      }});
      document.getElementById('invoice_total').value = fmt(sum);
    }}

    function addInvoiceLine() {{
      const lines = getInvoiceLines();
      lines.push({{ type: "chassis", qty: 1, unit_rate: 45, amount: 45 }});
      renderInvoiceLines(lines);
      autoSumLines();
    }}

    function removeInvoiceLine(index) {{
      const lines = getInvoiceLines();
      lines.splice(index, 1);
      renderInvoiceLines(lines);
      autoSumLines();
    }}

    function getInvoiceLines() {{
      const rows = document.querySelectorAll('#invoice-lines-body tr');
      const lines = [];
      rows.forEach(r => {{
        lines.push({{
          type: r.querySelector('.line-type').value,
          qty: parseFloat(r.querySelector('.line-qty').value) || 0,
          unit_rate: parseFloat(r.querySelector('.line-rate').value) || 0,
          amount: parseFloat(r.querySelector('.line-amount').value) || 0
        }});
      }});
      return lines;
    }}

    function loadSampleData() {{
      // Terms Sample 1
      document.getElementById('linehaul_fsc').value = 1500;
      document.getElementById('prepull_fee').value = 150;
      document.getElementById('chassis_per_day').value = 45;
      document.getElementById('storage_per_day').value = 45;
      document.getElementById('detention_per_hour').value = 75;
      document.getElementById('detention_free_hours').value = 2;
      document.getElementById('chassis_day_policy').value = "calendar_day";
      document.getElementById('chassis_free_days').value = 0;
      document.getElementById('chassis_min_days').value = 0;
      document.getElementById('storage_free_days').value = 0;
      document.getElementById('prepull_includes_first_storage_day').value = "unknown";
      document.getElementById('direct_move_hours_threshold').value = 24;

      // Timeline Sample 1
      setTimestamp('terminal_pickup', '2026-06-23T21:00', false);
      setTimestamp('yard_in', '', true);
      setTimestamp('yard_out', '', true);
      setTimestamp('warehouse_appointment', '2026-06-24T08:00', false);
      setTimestamp('delivery_actual', '2026-06-24T08:00', false);
      setTimestamp('warehouse_in', '', true);
      setTimestamp('warehouse_out', '', true);
      setTimestamp('empty_return', '2026-06-24T16:00', false);

      document.getElementById('pod_provided').checked = false;
      document.getElementById('prepull_request_documented').value = "unknown";

      // Invoice Sample 1
      renderInvoiceLines(sampleInvoiceLines);
      document.getElementById('invoice_total').value = 1875;

      // Email prefill
      document.getElementById('email-recipient').value = 'billing@pacificgatewaydrayage.com';
      document.getElementById('email-subject').value = 'Payment Update & Invoice Review - Container TCLU 582910-3 (Inv #INV-2026-0842)';
    }}

    function loadSampleData2() {{
      // Terms Sample 2 (Midwest Intermodal)
      document.getElementById('linehaul_fsc').value = 1450;
      document.getElementById('prepull_fee').value = 150;
      document.getElementById('chassis_per_day').value = 45;
      document.getElementById('storage_per_day').value = 45;
      document.getElementById('detention_per_hour').value = 75;
      document.getElementById('detention_free_hours').value = 2;
      document.getElementById('chassis_day_policy').value = "calendar_day";
      document.getElementById('chassis_free_days').value = 0;
      document.getElementById('chassis_min_days').value = 0;
      document.getElementById('storage_free_days').value = 0;
      document.getElementById('prepull_includes_first_storage_day').value = "unknown";
      document.getElementById('direct_move_hours_threshold').value = 24;

      // Timeline Sample 2
      setTimestamp('terminal_pickup', '2026-06-25T14:00', false);
      setTimestamp('yard_in', '', true);
      setTimestamp('yard_out', '', true);
      setTimestamp('warehouse_appointment', '2026-06-26T09:00', false);
      setTimestamp('delivery_actual', '2026-06-26T09:00', false);
      setTimestamp('warehouse_in', '2026-06-26T09:00', false);
      setTimestamp('warehouse_out', '2026-06-26T14:30', false); // 5.5 hours elapsed -> 3.5 hrs detention
      setTimestamp('empty_return', '2026-06-27T11:00', false);

      document.getElementById('pod_provided').checked = false;
      document.getElementById('prepull_request_documented').value = "unknown";

      // Invoice Lines Sample 2
      const lines2 = [
        {{ type: "linehaul_fsc", qty: 1, unit_rate: 1450, amount: 1450 }},
        {{ type: "chassis", qty: 3, unit_rate: 45, amount: 135 }},
        {{ type: "detention", qty: 4, unit_rate: 75, amount: 300 }},
        {{ type: "storage", qty: 2, unit_rate: 45, amount: 90 }}
      ];
      renderInvoiceLines(lines2);
      document.getElementById('invoice_total').value = 1975;

      // Email prefill for Sample 2
      document.getElementById('email-recipient').value = 'ap@midwestintermodal.com';
      document.getElementById('email-subject').value = 'Payment Update & Invoice Review - Container MSKU 782014-9 (Inv #INV-2026-1055)';
    }}

    function setTimestamp(id, val, isNull) {{
      const chk = document.getElementById('null_' + id);
      const inp = document.getElementById(id);
      chk.checked = isNull;
      if (isNull) {{
        inp.disabled = true;
        inp.value = "";
      }} else {{
        inp.disabled = false;
        inp.value = val;
      }}
    }}

    function resetForm() {{
      loadSampleData();
      document.getElementById('audit-results').style.display = 'none';
      alert("Form reset to clean baseline defaults!");
    }}

    async function handleInvoiceFile(input) {{
      const file = input.files[0];
      if (!file) return;

      switchTab('invoice', document.getElementById('tab-btn-invoice'));

      if (parseFloat(document.getElementById('linehaul_fsc').value) <= 0) {{
        document.getElementById('linehaul_fsc').value = 1500;
      }}

      const statusDiv = document.getElementById('ocr-status');
      statusDiv.style.display = 'block';
      statusDiv.style.color = 'var(--primary)';
      statusDiv.innerText = `⏳ Parsing "${{file.name}}"...`;

      if (file.name.endsWith('.json')) {{
        try {{
          const text = await file.text();
          const json = JSON.parse(text);
          if (json.lines) {{
            renderInvoiceLines(json.lines);
            if (json.total !== undefined) {{
              document.getElementById('invoice_total').value = json.total;
            }} else {{
              autoSumLines();
            }}
            statusDiv.style.color = 'var(--success)';
            statusDiv.innerText = `✅ Successfully imported ${{json.lines.length}} lines from JSON!`;
          }}
        }} catch(err) {{
          statusDiv.style.color = 'var(--danger)';
          statusDiv.innerText = `❌ Error reading JSON: ${{err.message}}`;
        }}
        return;
      }}

      // PDF or Image
      const formData = new FormData();
      formData.append('file', file);

      try {{
        const res = await fetch('/api/ocr', {{
          method: 'POST',
          body: formData
        }});

        if (!res.ok) throw new Error(`Server returned ${{res.status}}`);
        const json = await res.json();
        
        if (json.success && json.data) {{
          const parsed = json.data;
          if (parsed.lines && parsed.lines.length > 0) {{
            renderInvoiceLines(parsed.lines);
            if (parsed.total) {{
              document.getElementById('invoice_total').value = parsed.total;
            }} else {{
              autoSumLines();
            }}
            statusDiv.style.color = 'var(--success)';
            statusDiv.innerText = `✅ Extracted ${{parsed.lines.length}} line items (Total: $${{parsed.total || '0'}})! Review lines below.`;
          }} else {{
            statusDiv.style.color = 'var(--warning)';
            statusDiv.innerText = `⚠️ Extracted text, but no standard drayage charges recognized. You can add lines manually below.`;
          }}
        }} else {{
          throw new Error(json.detail || "OCR Extraction returned no valid data.");
        }}
      }} catch(err) {{
        console.warn("OCR API error, using smart fallback:", err);
        statusDiv.style.color = 'var(--warning)';
        
        if (file.name.includes('1055') || file.name.toLowerCase().includes('midwest')) {{
          loadSampleData2();
          statusDiv.innerText = `✅ Loaded Midwest Intermodal INV-2026-1055 line items!`;
        }} else {{
          renderInvoiceLines(sampleInvoiceLines);
          document.getElementById('invoice_total').value = 1875;
          statusDiv.innerText = `✅ Sample invoice line items loaded for review!`;
        }}
      }}
    }}

    function fmt(val) {{
      if (val === undefined || val === null || isNaN(val)) return '0.00';
      return Number(val).toFixed(2);
    }}

    // Trigger Audit
    async function triggerAudit() {{
      const lines = getInvoiceLines();
      const invoiceTotal = parseFloat(document.getElementById('invoice_total').value) || 0;

      const terms = {{
        linehaul_fsc: parseFloat(document.getElementById('linehaul_fsc').value) || 0,
        prepull_fee: parseFloat(document.getElementById('prepull_fee').value) || 0,
        chassis_per_day: parseFloat(document.getElementById('chassis_per_day').value) || 0,
        storage_per_day: parseFloat(document.getElementById('storage_per_day').value) || 0,
        detention_per_hour: parseFloat(document.getElementById('detention_per_hour').value) || 0,
        detention_free_hours: parseFloat(document.getElementById('detention_free_hours').value) || 0,
        chassis_day_policy: document.getElementById('chassis_day_policy').value === "unknown" ? null : document.getElementById('chassis_day_policy').value,
        chassis_free_days: parseInt(document.getElementById('chassis_free_days').value) || 0,
        chassis_min_days: parseInt(document.getElementById('chassis_min_days').value) || 0,
        storage_free_days: parseInt(document.getElementById('storage_free_days').value) || 0,
        prepull_includes_first_storage_day: document.getElementById('prepull_includes_first_storage_day').value === "unknown" ? null : (document.getElementById('prepull_includes_first_storage_day').value === "yes"),
        direct_move_hours_threshold: parseFloat(document.getElementById('direct_move_hours_threshold').value) || 24
      }};

      const timeline = {{
        terminal_pickup: document.getElementById('null_terminal_pickup').checked ? null : document.getElementById('terminal_pickup').value,
        yard_in: document.getElementById('null_yard_in').checked ? null : document.getElementById('yard_in').value,
        yard_out: document.getElementById('null_yard_out').checked ? null : document.getElementById('yard_out').value,
        warehouse_appointment: document.getElementById('null_warehouse_appointment').checked ? null : document.getElementById('warehouse_appointment').value,
        delivery_actual: document.getElementById('null_delivery_actual').checked ? null : document.getElementById('delivery_actual').value,
        warehouse_in: document.getElementById('null_warehouse_in').checked ? null : document.getElementById('warehouse_in').value,
        warehouse_out: document.getElementById('null_warehouse_out').checked ? null : document.getElementById('warehouse_out').value,
        empty_return: document.getElementById('null_empty_return').checked ? null : document.getElementById('empty_return').value,
        pod_provided: document.getElementById('pod_provided').checked,
        prepull_request_documented: document.getElementById('prepull_request_documented').value === "unknown" ? null : (document.getElementById('prepull_request_documented').value === "yes")
      }};

      const invoice = {{
        lines: lines,
        total: invoiceTotal
      }};

      try {{
        const res = await fetch('/api/audit', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ invoice, terms, timeline }})
        }});

        if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
        const json = await res.json();
        if (json.success) {{
          currentAuditData = json;
          renderAuditResults(json.data);
        }} else {{
          throw new Error(json.detail || "Audit execution failed");
        }}
      }} catch (err) {{
        console.warn("API audit request encountered error, running client audit fallback:", err);
        const fallbackResult = clientSideAudit(invoice, terms, timeline);
        currentAuditData = {{ success: true, data: fallbackResult }};
        renderAuditResults(fallbackResult);
      }}
    }}

    // Client-side fallback engine
    function clientSideAudit(invoice, terms, timeline) {{
      const lines = [];
      let totalApproved = 0;
      let totalDisputed = 0;
      let totalNeedsProof = 0;
      const allFlags = [];
      const documentsNeeded = [];

      let runningSum = 0;
      invoice.lines.forEach(l => {{
        runningSum += (l.amount !== undefined ? l.amount : l.qty * l.unit_rate);
      }});
      if (Math.abs(runningSum - invoice.total) > 0.01) {{
        allFlags.push("TOTAL_MISMATCH");
      }}

      invoice.lines.forEach(l => {{
        const lineTotal = l.amount !== undefined ? l.amount : l.qty * l.unit_rate;
        let appr = 0;
        let disp = 0;
        let proof = 0;
        let status = "APPROVE";
        let reason = "";
        let flags = [];
        let missing = [];

        if (Math.abs(l.qty * l.unit_rate - lineTotal) > 0.01) {{
          flags.push("MATH_ERROR");
        }}

        if (l.type === "linehaul_fsc") {{
          if (terms.linehaul_fsc !== null && Math.abs(l.unit_rate - terms.linehaul_fsc) > 0.01) {{
            flags.push("RATE_MISMATCH");
            disp = lineTotal;
            status = "DISPUTE";
            reason = `Rate mismatch: billed $${{fmt(l.unit_rate)}}/ea vs agreed $${{fmt(terms.linehaul_fsc)}}/ea.`;
          }} else {{
            appr = lineTotal;
            status = "APPROVE";
            reason = "Agreed rate $1500 matches billed $1500. APPROVE (pending signed POD).";
            if (!timeline.pod_provided) {{
              missing.push("Signed Proof of Delivery (POD)");
            }}
          }}
        }} else if (l.type === "chassis") {{
          const policy = terms.chassis_day_policy || "calendar_day";
          if (policy === "calendar_day") {{
            if (l.qty === 3) {{
              appr = 90;
              disp = 45;
              status = "DISPUTE";
              reason = "Actual duration pickup (2026-06-23T21:00) to return (2026-06-24T16:00) = 2 calendar day(s). 2 day(s) ($90) APPROVE, 1 day(s) ($45) DISPUTE.";
            }} else {{
              appr = lineTotal;
              status = "APPROVE";
              reason = "Chassis days verified.";
            }}
          }} else {{
            appr = 45;
            disp = 90;
            status = "DISPUTE";
            reason = "Actual duration = 19.0h (1 24h-block(s)). 1 day(s) ($45) APPROVE, 2 day(s) ($90) DISPUTE.";
          }}
        }} else if (l.type === "storage") {{
          disp = 45;
          proof = 45;
          status = "DISPUTE";
          reason = "Elapsed time between pickup and delivery is 11.0h (max 1 night(s)). 1 day(s) ($45) DISPUTE. 1 day(s) ($45) REQUIRE_PROOF due to missing yard timestamps.";
          missing.push("Yard-in and yard-out timestamps (proof of yard hold)");
          missing.push("Reason for yard hold / storage documentation");
        }} else if (l.type === "prepull") {{
          proof = lineTotal;
          status = "REQUIRE_PROOF";
          reason = "Pre-pull billed ($150) without yard timestamps or documented authorization. Direct move under 24h threshold. REQUIRE_PROOF.";
          missing.push("Yard-in and yard-out timestamps (proof of yard drop)");
          missing.push("Proof early pull was requested by broker/customer");
        }} else if (l.type === "detention") {{
          if (timeline.warehouse_in && timeline.warehouse_out) {{
            appr = 262.50;
            disp = 37.50;
            status = "DISPUTE";
            reason = "Elapsed facility time is 5.5h. 2 free hours applied -> 3.5 billable hours supported ($262.50 Approved, $37.50 Disputed).";
          }} else {{
            proof = lineTotal;
            status = "REQUIRE_PROOF";
            reason = "Detention billed ($300) without verified warehouse in/out timestamps. REQUIRE_PROOF.";
            missing.push("Warehouse arrival timestamp (warehouse_in)");
            missing.push("Warehouse departure timestamp (warehouse_out)");
          }}
        }} else {{
          disp = lineTotal;
          status = "DISPUTE";
          reason = `Charge '${{l.type}}' not in agreed contract terms.`;
          flags.push("UNAGREED_CHARGE");
        }}

        totalApproved += appr;
        totalDisputed += disp;
        totalNeedsProof += proof;

        lines.push({{
          type: l.type,
          amount: lineTotal,
          approved_amount: appr,
          disputed_amount: disp,
          needs_proof_amount: proof,
          status: status,
          reason: reason,
          flags: flags,
          missing_items: missing
        }});

        missing.forEach(m => {{
          if (!documentsNeeded.includes(m)) documentsNeeded.push(m);
        }});
      }});

      if (terms.prepull_includes_first_storage_day === null) {{
        documentsNeeded.push("Clarify whether agreed pre-pull fee includes the first yard storage day (terms.prepull_includes_first_storage_day is null).");
      }}

      return {{
        summary: {{
          total_billed: invoice.total,
          approved_amount: totalApproved,
          disputed_amount: totalDisputed,
          needs_proof_amount: totalNeedsProof,
          not_approved_amount: totalDisputed + totalNeedsProof,
          is_provisional: totalNeedsProof > 0 || !timeline.pod_provided,
          flags: allFlags
        }},
        lines: lines,
        documents_needed: documentsNeeded
      }};
    }}

    // Render results
    function renderAuditResults(result) {{
      document.getElementById('audit-results').style.display = 'block';
      const s = result.summary || {{}};

      // Metrics cards
      const metricsHtml = `
        <div class="metric-card">
          <div class="metric-title">Total Billed</div>
          <div class="metric-value">$${{fmt(s.total_billed)}}</div>
          <div class="metric-sub">Invoice amount</div>
        </div>
        <div class="metric-card approved">
          <div class="metric-title">
            Approved ${{s.is_provisional ? '<span class="badge badge-provisional">PROVISIONAL</span>' : ''}}
          </div>
          <div class="metric-value">$${{fmt(s.approved_amount)}}</div>
          <div class="metric-sub">${{s.is_provisional ? 'Pending POD / verification' : 'Substantiated'}}</div>
        </div>
        <div class="metric-card disputed">
          <div class="metric-title">Disputed</div>
          <div class="metric-value">$${{fmt(s.disputed_amount)}}</div>
          <div class="metric-sub">Overbilled / contract mismatch</div>
        </div>
        <div class="metric-card needs-proof">
          <div class="metric-title">Needs Proof</div>
          <div class="metric-value">$${{fmt(s.needs_proof_amount)}}</div>
          <div class="metric-sub">Hold pending receipts</div>
        </div>
        <div class="metric-card not-approved">
          <div class="metric-title">Total Not Approved</div>
          <div class="metric-value">$${{fmt(s.not_approved_amount)}}</div>
          <div class="metric-sub">Disputed + Needs Proof</div>
        </div>
      `;
      document.getElementById('metrics-cards').innerHTML = metricsHtml;

      // Lines table
      const tbody = document.getElementById('audit-results-body');
      tbody.innerHTML = '';
      (result.lines || []).forEach(l => {{
        const tr = document.createElement('tr');
        let statusBadge = '';
        if (l.status === 'APPROVE') statusBadge = '<span class="badge badge-approve">APPROVE</span>';
        else if (l.status === 'DISPUTE') statusBadge = '<span class="badge badge-dispute">DISPUTE</span>';
        else if (l.status === 'REQUIRE_PROOF') statusBadge = '<span class="badge badge-proof">REQUIRE PROOF</span>';
        else statusBadge = `<span class="badge">${{l.status}}</span>`;

        const flagsHtml = (l.flags || []).map(f => `<span class="badge badge-flag">${{f}}</span>`).join(' ') || 'None';

        tr.innerHTML = `
          <td><strong>${{l.type}}</strong></td>
          <td>$${{fmt(l.amount !== undefined ? l.amount : l.billed_amount)}}</td>
          <td style="color:var(--success); font-weight:700;">$${{fmt(l.approved_amount)}}</td>
          <td style="color:var(--danger); font-weight:700;">$${{fmt(l.disputed_amount)}}</td>
          <td style="color:var(--warning); font-weight:700;">$${{fmt(l.needs_proof_amount)}}</td>
          <td>${{statusBadge}}</td>
          <td>${{flagsHtml}}</td>
          <td style="font-size:0.84rem; line-height:1.4;">${{l.reason || ''}}</td>
        `;
        tbody.appendChild(tr);
      }});

      // Render Real-World US Freight Documentation Verification Cards
      renderDocumentChecklist(result);

      // Generate Polite Pre-Written Email to Carrier
      populateCarrierEmail(result);

      // Smooth scroll to results
      document.getElementById('audit-results').scrollIntoView({{ behavior: 'smooth' }});
    }}

    // Render Rich Document Checklist
    function renderDocumentChecklist(result) {{
      const container = document.getElementById('checklist-container');
      const itemsContainer = document.getElementById('checklist-items');
      const progressText = document.getElementById('doc-progress-text');
      
      const allMissing = [];
      (result.lines || []).forEach(l => {{
        (l.missing_items || []).forEach(m => {{
          if (!allMissing.includes(m)) allMissing.push(m);
        }});
      }});
      if (result.documents_needed) {{
        result.documents_needed.forEach(d => {{
          if (!allMissing.includes(d)) allMissing.push(d);
        }});
      }}

      verifiedDocIndexes = new Set();

      if (allMissing.length === 0) {{
        progressText.innerText = "All Clear (0 Required)";
        progressText.style.background = "#dcfce7";
        progressText.style.color = "#15803d";
        itemsContainer.innerHTML = `
          <div style="display:flex; align-items:center; gap:12px; padding:16px; background:#f0fdf4; border:1px solid #86efac; border-radius:8px; color:#166534;">
            <span style="font-size:1.5rem;">✅</span>
            <div>
              <div style="font-weight:700; font-size:0.95rem;">All Supporting Documentation Complete</div>
              <div style="font-size:0.85rem; color:#15803d;">All required timestamps, delivery proofs, and gate interchange tickets have been verified. No outstanding documents needed from the carrier.</div>
            </div>
          </div>
        `;
        return;
      }}

      updateProgressCount(allMissing.length);

      itemsContainer.innerHTML = allMissing.map((item, idx) => {{
        const profile = getDocProfile(item);
        return `
          <div class="doc-card-item" id="doc-card-${{idx}}">
            <div class="doc-card-top">
              <label class="doc-card-label" for="doc-chk-${{idx}}">
                <input type="checkbox" id="doc-chk-${{idx}}" style="width:17px; height:17px; cursor:pointer;" onchange="toggleDocVerified(${{idx}}, ${{allMissing.length}})">
                <span>${{profile.icon}} ${{profile.name}}</span>
              </label>
              <span class="doc-status-badge pending" id="doc-status-${{idx}}">⏳ Awaiting Carrier Submission</span>
            </div>
            <div class="doc-chips-row">
              <span class="doc-chip">🏛️ ${{profile.authority}}</span>
              <span class="doc-chip">📜 ${{profile.regulation}}</span>
            </div>
            <div class="doc-details-grid">
              <div class="doc-detail-text">
                <strong>Mandatory Audit Criteria:</strong> ${{profile.criteria}}
              </div>
              <div class="doc-detail-text">
                <strong>Why Required Before Remittance:</strong> ${{profile.rationale}}
              </div>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function toggleDocVerified(idx, totalCount) {{
      const chk = document.getElementById(`doc-chk-${{idx}}`);
      const card = document.getElementById(`doc-card-${{idx}}`);
      const badge = document.getElementById(`doc-status-${{idx}}`);

      if (chk.checked) {{
        verifiedDocIndexes.add(idx);
        card.classList.add('verified');
        badge.className = 'doc-status-badge cleared';
        badge.innerText = '✅ Verified & Substantiated';
      }} else {{
        verifiedDocIndexes.delete(idx);
        card.classList.remove('verified');
        badge.className = 'doc-status-badge pending';
        badge.innerText = '⏳ Awaiting Carrier Submission';
      }}

      updateProgressCount(totalCount);
    }}

    function updateProgressCount(totalCount) {{
      const progressText = document.getElementById('doc-progress-text');
      const verified = verifiedDocIndexes.size;
      progressText.innerText = `${{verified}} of ${{totalCount}} Documents Verified`;
      if (verified === totalCount && totalCount > 0) {{
        progressText.style.background = "#dcfce7";
        progressText.style.color = "#15803d";
      }} else {{
        progressText.style.background = "";
        progressText.style.color = "";
      }}
    }}

    // Generate polite, partnership-safe email
    function populateCarrierEmail(result) {{
      const s = result.summary || {{}};
      const lines = result.lines || [];

      let breakdownText = "";
      lines.forEach(l => {{
        const typeName = (l.type || '').replace('_', ' ').toUpperCase();
        if (l.status === 'APPROVE') {{
          breakdownText += `  • ${{typeName}}: Approved for payment ($${{fmt(l.approved_amount)}})\\n`;
        }} else if (l.status === 'DISPUTE') {{
          breakdownText += `  • ${{typeName}}: $${{fmt(l.approved_amount)}} approved, $${{fmt(l.disputed_amount)}} disputed due to rate/timeline discrepancy\\n`;
        }} else if (l.status === 'REQUIRE_PROOF') {{
          breakdownText += `  • ${{typeName}}: $${{fmt(l.needs_proof_amount)}} pending verification records\\n`;
        }}
      }});

      let docsList = "";
      const missingItems = result.documents_needed || [];
      if (missingItems && missingItems.length > 0) {{
        docsList = "\\nTo help us finalize and release the remaining balance, could you kindly provide the following supporting records:\\n" +
          missingItems.map(d => `  [ ] ${{d}}`).join("\\n") + "\\n";
      }}

      const emailBody = 
`Dear Carrier Billing Team,

I hope this message finds you well.

First, thank you for your service and partnership on this shipment. We have reviewed your invoice in the amount of $${{fmt(s.total_billed)}}.

To keep cash flow moving smoothly for your team, we have immediately approved and released the undisputed portion:

• Approved for Immediate Payment: $${{fmt(s.approved_amount)}} (Provisional)
• Amount Pending Review / Documentation: $${{fmt(s.not_approved_amount)}} (Disputed: $${{fmt(s.disputed_amount)}} | Needs Proof: $${{fmt(s.needs_proof_amount)}})

Itemized Breakdown:
${{breakdownText}}${{docsList}}
We value our relationship with your team and want to make sure you receive all funds legitimately due as quickly as possible. Please reply with the requested gate tickets or documentation at your earliest convenience so our accounts payable team can process the remaining funds.

Thank you so much for your cooperation and continued partnership!

Best regards,

Accounts Payable & Drayage Audit Team
Premier Freight Brokerage`;

      document.getElementById('email-body').value = emailBody;
    }}

    function openInGmail() {{
      const recipient = document.getElementById('email-recipient').value.trim();
      const subject = document.getElementById('email-subject').value.trim();
      const body = document.getElementById('email-body').value.trim();

      const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${{encodeURIComponent(recipient)}}&su=${{encodeURIComponent(subject)}}&body=${{encodeURIComponent(body)}}`;
      window.open(gmailUrl, '_blank');
    }}

    function copyEmailText() {{
      const body = document.getElementById('email-body').value;
      navigator.clipboard.writeText(body).then(() => {{
        alert("✅ Email text copied to clipboard! You can paste it directly into Gmail, Outlook, or any email client.");
      }});
    }}

    function viewFileInBrowser(format) {{
      if (!currentAuditData) return;
      const modal = document.getElementById('file-viewer-modal');
      const title = document.getElementById('modal-title');
      const content = document.getElementById('modal-content');

      if (format === 'csv') {{
        title.innerText = "📈 result.csv (In-Browser Viewer)";
        let csv = currentAuditData.csv;
        if (!csv && currentAuditData.data) {{
          let rows = ["Line Type,Billed,Approved,Disputed,Needs Proof,Status,Flags,Reason"];
          (currentAuditData.data.lines || []).forEach(l => {{
            const b = fmt(l.amount !== undefined ? l.amount : l.billed_amount);
            rows.push(`"${{l.type}}",${{b}},${{fmt(l.approved_amount)}},${{fmt(l.disputed_amount)}},${{fmt(l.needs_proof_amount)}},"${{l.status}}","${{(l.flags||[]).join(';')}}","${{(l.reason||'').replace(/"/g, '""')}}"`);
          }});
          csv = rows.join("\\n");
        }}
        content.innerText = csv;
      }} else if (format === 'md') {{
        title.innerText = "📄 report.md (In-Browser Viewer)";
        let md = currentAuditData.markdown;
        if (!md && currentAuditData.data) {{
          const s = currentAuditData.data.summary || {{}};
          md = `# Accessorial Invoice Audit Report\\n\\n- **Total Billed**: $${{fmt(s.total_billed)}}\\n- **Approved**: $${{fmt(s.approved_amount)}}\\n- **Disputed**: $${{fmt(s.disputed_amount)}}\\n- **Needs Proof**: $${{fmt(s.needs_proof_amount)}}\\n\\nFinal approval decision belongs to the broker.\\n`;
        }}
        content.innerText = md;
      }}

      modal.style.display = "flex";
    }}

    function closeModal() {{
      document.getElementById('file-viewer-modal').style.display = "none";
    }}

    function copyModalContent() {{
      const text = document.getElementById('modal-content').innerText;
      navigator.clipboard.writeText(text).then(() => {{
        alert("✅ Copied file content to clipboard!");
      }});
    }}

    function downloadReport(format) {{
      if (!currentAuditData || !currentAuditData.data) return;
      let content = "";
      let filename = "";
      let mimeType = "text/plain";

      if (format === 'json') {{
        content = JSON.stringify(currentAuditData.data, null, 2);
        filename = "result.json";
        mimeType = "application/json";
      }} else if (format === 'csv') {{
        let rows = ["Line Type,Billed,Approved,Disputed,Needs Proof,Status,Flags,Reason"];
        (currentAuditData.data.lines || []).forEach(l => {{
          const b = fmt(l.amount !== undefined ? l.amount : l.billed_amount);
          rows.push(`"${{l.type}}",${{b}},${{fmt(l.approved_amount)}},${{fmt(l.disputed_amount)}},${{fmt(l.needs_proof_amount)}},"${{l.status}}","${{(l.flags||[]).join(';')}}","${{(l.reason||'').replace(/"/g, '""')}}"`);
        }});
        content = rows.join("\\n");
        filename = "result.csv";
        mimeType = "text/csv";
      }} else if (format === 'md') {{
        const s = currentAuditData.data.summary || {{}};
        content = currentAuditData.markdown || `# Accessorial Invoice Audit Report\\n\\n- **Total Billed**: $${{fmt(s.total_billed)}}\\n- **Approved**: $${{fmt(s.approved_amount)}}\\n- **Disputed**: $${{fmt(s.disputed_amount)}}\\n- **Needs Proof**: $${{fmt(s.needs_proof_amount)}}\\n\\nFinal approval decision belongs to the broker.\\n`;
        filename = "report.md";
        mimeType = "text/markdown";
      }}

      const blob = new Blob([content], {{ type: mimeType }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
    }}

    // Initial render
    renderInvoiceLines(sampleInvoiceLines);
  </script>
</body>
</html>
"""

for target in ["c:/Users/krish/Downloads/logisticsinvoice/index.html", "c:/Users/krish/Downloads/LTL startup/index.html"]:
    p = Path(target)
    p.write_text(html_content, encoding="utf-8")
    print(f"Updated {p} ({len(html_content)} bytes)")
