"""Unit test suite for Rate Confirmation parser (src/ratecon.py).

Covers:
- parse_ratecon_text with full Rate Con document text (all accessorial terms & metadata).
- parse_ratecon_text with alternative charge formats (separate Linehaul + FSC, all-in, flat rate).
- parse_ratecon_text with partial or minimal text (graceful fallbacks).
- extract_ratecon_text with raw text, bytes, and file paths.
- parse_ratecon_file end-to-end with text files and digital PDFs.
"""

import io
from pathlib import Path
import pytest
from fpdf import FPDF

from src.ratecon import (
    extract_ratecon_text,
    parse_ratecon_file,
    parse_ratecon_text,
)


SAMPLE_RATECON_TEXT = """
======================================================================
PACIFIC GATEWAY DRAYAGE - RATE CONFIRMATION & WORK ORDER
======================================================================
Carrier: Pacific Gateway Drayage LLC
MC/DOT: MC# 892341 / DOT# 2948190
Load ID: RC-2026-0842
Order No: ORD-99120
BOL Ref: MEDU 91823901
Container #: TCLU 582910-3
Equipment: 40ft High Cube Container

ORIGIN / DESTINATION:
Port of Los Angeles Pier 400 to Ontario Regional Depot, CA

AGREED RATES & ACCESSORIAL TARIFF TERMS:
- Linehaul / Base Rate: $1,200.00
- Fuel Surcharge (FSC): $300.00
- Intermodal Chassis: $45.00/day
- Yard Storage / Hold: $45.00/day
- Driver Detention Rate: $75.00/hour (2 hours free time included)
- Terminal Pre-pull Fee: $150.00
- Chassis Policy: calendar_day

Special Instructions:
Carrier must obtain written broker authorization prior to pre-pull or yard hold.
Signed POD and EIR tickets required for final payment release.
"""


def test_parse_ratecon_text_comprehensive():
    """Verify complete extraction of all terms and metadata from standard Rate Con."""
    result = parse_ratecon_text(SAMPLE_RATECON_TEXT)

    assert "terms" in result
    assert "metadata" in result
    assert "raw_text" in result

    terms = result["terms"]
    assert terms["linehaul_fsc"] == 1500.0  # 1200 base + 300 fsc
    assert terms["chassis_per_day"] == 45.0
    assert terms["storage_per_day"] == 45.0
    assert terms["detention_per_hour"] == 75.0
    assert terms["detention_free_hours"] == 2.0
    assert terms["prepull_fee"] == 150.0
    assert terms["chassis_day_policy"] == "calendar_day"

    meta = result["metadata"]
    assert meta["carrier_name"] == "Pacific Gateway Drayage LLC"
    assert meta["load_id"] == "RC-2026-0842"
    assert meta["order_no"] == "ORD-99120"
    assert meta["bol_no"] == "MEDU 91823901"
    assert meta["container_no"] == "TCLU 582910-3"


def test_parse_ratecon_text_all_in_and_flat():
    """Verify parsing when rate is specified as All-In or Total Flat."""
    text = """
    RATE CONFIRMATION
    Carrier Name: Midwest Intermodal Freight LLC
    Confirmation #: LD-77291
    Purchase Order: PO-3341
    Bill of Lading #: MAEU 29104820
    Container: MSKU 782014-9

    Agreed Terms:
    All-In Rate: $1,650.00
    Chassis per day: $45
    Storage / day: $50
    Detention: $85/hr (2 free hrs)
    Prepull: $175
    """
    result = parse_ratecon_text(text)
    terms = result["terms"]
    meta = result["metadata"]

    assert terms["linehaul_fsc"] == 1650.0
    assert terms["chassis_per_day"] == 45.0
    assert terms["storage_per_day"] == 50.0
    assert terms["detention_per_hour"] == 85.0
    assert terms["detention_free_hours"] == 2.0
    assert terms["prepull_fee"] == 175.0

    assert meta["carrier_name"] == "Midwest Intermodal Freight LLC"
    assert meta["load_id"] == "LD-77291"
    assert meta["order_no"] == "PO-3341"
    assert meta["bol_no"] == "MAEU 29104820"
    assert "MSKU" in meta["container_no"]


def test_parse_ratecon_text_minimal_and_empty():
    """Verify that empty or minimal text does not crash and yields None for missing fields."""
    result = parse_ratecon_text("")
    assert result["terms"]["linehaul_fsc"] is None
    assert result["terms"]["prepull_fee"] is None
    assert result["terms"]["chassis_per_day"] is None
    assert result["metadata"]["carrier_name"] is None
    assert result["metadata"]["load_id"] is None


def test_extract_ratecon_text_string():
    """Verify extract_ratecon_text handles plain text strings directly."""
    raw = "Rate Confirmation\nCarrier: Test Carrier LLC\nAgreed Rate: $1400"
    extracted = extract_ratecon_text(raw)
    assert "Agreed Rate: $1400" in extracted


def test_extract_ratecon_text_bytes():
    """Verify extract_ratecon_text decodes UTF-8 bytes."""
    raw = "Carrier: Test Drayage\nLinehaul: $1500".encode("utf-8")
    extracted = extract_ratecon_text(raw)
    assert "Linehaul: $1500" in extracted


def test_parse_ratecon_file_with_text_file(tmp_path: Path):
    """Verify parse_ratecon_file works with a text file on disk."""
    file_path = tmp_path / "ratecon.txt"
    file_path.write_text(SAMPLE_RATECON_TEXT, encoding="utf-8")

    result = parse_ratecon_file(file_path)
    assert result["terms"]["linehaul_fsc"] == 1500.0
    assert result["metadata"]["carrier_name"] == "Pacific Gateway Drayage LLC"


def test_parse_ratecon_file_with_pdf(tmp_path: Path):
    """Verify parse_ratecon_file works with an end-to-end digital PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in SAMPLE_RATECON_TEXT.strip().split("\n"):
        clean_line = line.replace("=", "-").strip()
        if clean_line:
            pdf.cell(0, 5, clean_line[:80], new_x="LMARGIN", new_y="NEXT")

    pdf_path = tmp_path / "ratecon.pdf"
    pdf.output(str(pdf_path))

    result = parse_ratecon_file(pdf_path)
    assert result["terms"]["chassis_per_day"] == 45.0
    assert result["terms"]["prepull_fee"] == 150.0
    assert result["metadata"]["container_no"] is not None
