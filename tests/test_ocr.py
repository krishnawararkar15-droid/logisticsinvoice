"""Unit tests for OCR text parsing and review persistence in src/ocr.py."""

from pathlib import Path

from src.ocr import (
    load_review_data,
    parse_invoice_text,
    save_for_review,
)


def test_parse_standard_drayage_invoice_text():
    sample_text = """
    PACIFIC INTERMODAL DRAYAGE CORP
    Invoice #: INV-2026-8819
    Date: 10/12/2026
    Container: MSCU-4091823

    CHARGES:
    Linehaul Base Rate: $1,250.00
    Fuel Surcharge (FSC): $235.00
    Pre-pull Fee: $150.00
    Chassis Usage: 3 Days @ $45.00/day = $135.00
    Yard Storage: 2 Days @ $75.00/day = $150.00
    Driver Detention: 2.5 hrs @ $85.00/hr = $212.50

    Subtotal: $2,132.50
    Invoice Total Due: $2,132.50
    """
    result = parse_invoice_text(sample_text)
    assert len(result["lines"]) == 6
    assert result["total"] == 2132.50

    types = [item["type"] for item in result["lines"]]
    assert types == [
        "linehaul_fsc",
        "linehaul_fsc",
        "prepull",
        "chassis",
        "storage",
        "detention",
    ]

    chassis = [line for line in result["lines"] if line["type"] == "chassis"][0]
    assert chassis["qty"] == 3.0
    assert chassis["unit_rate"] == 45.0
    assert chassis["amount"] == 135.0

    detention = [line for line in result["lines"] if line["type"] == "detention"][0]
    assert detention["qty"] == 2.5
    assert detention["unit_rate"] == 85.0
    assert detention["amount"] == 212.50


def test_parse_tabular_invoice_text():
    sample_text = """
    HARBOR FREIGHT LOGISTICS
    PRO# 9948123   BOL# 771239

    ITEM\tQTY\tRATE\tAMOUNT
    Base Freight Drayage\t1\t1400.00\t1400.00
    Fuel Surcharge\t1\t280.00\t280.00
    Drop Yard Charge\t1\t125.00\t125.00
    Chassis Split Fee\t1\t110.00\t110.00
    Per Diem Storage\t4\t50.00\t200.00
    Waiting Time Driver\t3\t75.00\t225.00

    TOTAL: $2,340.00
    """
    result = parse_invoice_text(sample_text)
    assert len(result["lines"]) == 6
    assert result["total"] == 2340.00

    storage = [line for line in result["lines"] if line["type"] == "storage"][0]
    assert storage["qty"] == 4.0
    assert storage["unit_rate"] == 50.0
    assert storage["amount"] == 200.0


def test_save_and_load_review_data(tmp_path):
    data = {
        "lines": [
            {"type": "linehaul_fsc", "qty": 1.0, "unit_rate": 1500.0, "amount": 1500.0},
            {"type": "prepull", "qty": 1.0, "unit_rate": 150.0, "amount": 150.0},
        ],
        "total": 1650.0,
        "raw_text": "Sample text",
    }
    review_path = tmp_path / "review.json"
    saved = save_for_review(data, review_path)
    assert Path(saved).exists()

    loaded = load_review_data(saved)
    assert loaded["total"] == 1650.0
    assert len(loaded["lines"]) == 2
    assert loaded["lines"][0]["type"] == "linehaul_fsc"


def test_process_invoice_multiple_formats():
    """Verify that process_invoice supports PDF and multi-format payload preparation."""
    from src.ocr import _prepare_payload, process_invoice

    # 1. Test PDF file extraction
    pdf_path = Path(__file__).resolve().parent.parent / "sample_data" / "Carrier_Invoice_INV-2026-9482.pdf"
    if pdf_path.exists():
        res = process_invoice(pdf_path, filename="Carrier_Invoice_INV-2026-9482.pdf")
        assert len(res["lines"]) == 4
        assert res["total"] == 1875.0
        types = [l["type"] for l in res["lines"]]
        assert "linehaul_fsc" in types
        assert "prepull" in types
        assert "chassis" in types
        assert "storage" in types

    # 2. Test payload preparation for various image extensions
    formats = [
        ("invoice.png", "image/png"),
        ("invoice.jpg", "image/jpeg"),
        ("invoice.jpeg", "image/jpeg"),
        ("invoice.webp", "image/webp"),
        ("invoice.bmp", "image/bmp"),
        ("invoice.tiff", "image/tiff"),
        ("invoice.tif", "image/tiff"),
        ("invoice.txt", "text/plain"),
        ("invoice.json", "application/json"),
    ]
    for fname, expected_mime in formats:
        name, bts, mime = _prepare_payload(b"dummy data", filename=fname)
        assert name == fname
        assert mime == expected_mime

