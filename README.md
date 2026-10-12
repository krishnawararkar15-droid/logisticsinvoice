# 🚚 Accessorial Invoice Checker (v1)

> **Automated Drayage & Accessorial Invoice Auditing for Freight Brokers**  
> Protect your brokerage from unexpected accessorial overbilling on chassis fees, yard storage, pre-pull charges, and driver detention.

---

## 🎯 What This Tool Does & How It Protects Brokers

Drayage invoices are notorious for hidden fees, unauthorized accessorials, and inflated day counts. Freight brokers frequently overpay by **5% to 15%** on container moves due to:
- **Excess Chassis Days**: Carriers billing 3 or 4 days when the container was out for only 1 or 2 days.
- **Unauthorized Pre-Pull Charges**: Billing a \$150 pre-pull fee for a direct move that never spent time in a staging yard.
- **Yard Storage Overcharges**: Stacking multiple storage days without accounting for agreed free days or dates of container arrival.
- **Detention Inaccuracies**: Charging driver detention without timestamps proving time spent beyond agreed free hours.
- **Missing Proof of Delivery (POD)**: Invoicing before providing a signed POD.

**Accessorial Invoice Checker** acts as your brokerage's automated financial defense:
1. **Compares invoices against contracted rate terms** (linehaul, chassis per-day rates, free time, detention allowances).
2. **Audits real container milestones** (terminal pickup, yard in/out, warehouse appointment, delivery, and empty return).
3. **Applies deterministic mathematical rules** — no hallucinations, no guesswork.
4. **Calculates three clear totals**:
   - 🟢 **Approved**: Verified charges that match terms and timestamps.
   - 🔴 **Disputed**: Provably incorrect or excessive charges with detailed mathematical evidence.
   - 🟡 **Needs Proof**: Charges held pending carrier documentation (yard receipts, signed PODs, authorization emails).
5. **Generates instant audit packets** (Markdown report, JSON data, and spreadsheet CSV) ready to email to the carrier.

> **Important Principle:** Final approval decision always belongs to the broker. This tool equips you with the exact math, timestamps, and documentation needed to push back with 100% confidence.

---

## 🔒 100% Free & Local Operation

- **0 Paid Services**: No subscriptions, no credits, no SaaS fees.
- **0 AI APIs**: Uses 100% deterministic local rules and logic. No OpenAI, Anthropic, or proprietary LLM API keys needed.
- **Local & Private**: All data processing stays entirely on your computer. Your rates, carrier names, and billing records never leave your machine.
- *(Optional Free OCR)*: Free OCR.space API and local `pdfplumber` are included for instant invoice PDF extraction.

---

## ⚡ Quick Start (1-Command Startup)

### 1. Requirements
Ensure Python 3.9+ is installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
Run this single command in your terminal:
```bash
streamlit run app.py
```
The application will automatically open in your web browser at `http://localhost:8501`.

---

## 🧪 How to Test Locally in 3 Clicks

1. **Open the App**: Launch `streamlit run app.py`.
2. **Load Sample Data**: Click the **"⚡ Load Sample Data (Test Case 1)"** button at the top.
   - This instantly populates:
     - Agreed Rate Terms (Linehaul \$1,500, Pre-pull \$150, Chassis \$45/day, Storage \$45/day).
     - Container Timeline (Terminal pickup June 23 at 21:00, Warehouse Delivery June 24 at 08:00, Empty Return June 24 at 16:00).
     - Carrier Invoice (\$1,875 total: Linehaul \$1,500 + Pre-pull \$150 + Chassis 3 days \$135 + Storage 2 days \$90).
3. **Run Audit**: Click the big **"🚀 Check Invoice & Audit Discrepancies"** button.
   - **Instant Results**:
     - **Billed:** \$1,875.00
     - **Approved (Provisional):** \$1,590.00
     - **Disputed:** \$90.00 (1 excess chassis day \$45 + 1 excess storage day \$45)
     - **Needs Proof:** \$195.00 (Pre-pull \$150 pending yard authorization + Storage \$45 pending clarification)
     - **Withheld from Carrier:** \$285.00
   - **Download Audit Reports**: Click to download `report.md`, `result.json`, or `result.csv`.

---

## 🧹 How to Delete Test Data

All audit reports and export files are saved in the `output/` folder. To delete all generated test data, simply remove the folder:

### On Windows (PowerShell):
```powershell
Remove-Item -Recurse -Force output
```

### On macOS / Linux:
```bash
rm -rf output
```

You can also delete any temporary test JSON or PDF files you uploaded at any time.

---

## 📂 Project Structure

```text
├── app.py              # Streamlit interactive web application
├── requirements.txt    # Minimal, free Python libraries
├── README.md           # This guide
├── sample_data/        # Benchmark sample dataset
│   ├── invoice.json    # Sample carrier invoice ($1,875)
│   ├── terms.json      # Sample agreed broker-carrier rate agreement
│   └── timeline.json   # Container milestones & timestamps
├── src/
│   ├── dates.py        # Date math (calendar days, 24h blocks, midnights)
│   ├── rules.py        # Deterministic audit engine
│   ├── report.py       # Markdown, JSON, and CSV report generators
│   └── ocr.py          # Free OCR.space & pdfplumber extraction
└── output/             # Generated audit reports (report.md, result.json, result.csv)
```

---

## ⚖️ Disclaimer
**Final approval decision belongs to the broker.**  
This software serves as an auditing assistant and calculation engine. Brokers should review carrier contracts and evidence before releasing final payment or issuing official billing disputes.
