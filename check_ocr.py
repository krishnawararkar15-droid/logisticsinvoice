"""
Standalone test script to verify src/ocr.py parsing and extraction logic.
"""

import sys
import tempfile
from pathlib import Path

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.ocr import (
    extract_text,
    extract_text_pdfplumber,
    load_review_data,
    parse_invoice_text,
    save_for_review,
)


def test_standard_carrier_invoice():
    print("\n--- Test 1: Standard Carrier Invoice Text ---")
    sample_text = """
    PACIFIC INTERMODAL DRAYAGE CORP
    Invoice #: INV-2026-8819
    Date: 10/12/2026
    Container: MSCU-4091823 (40ft High Cube)
    Bill To: Krishna Freight Broker

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
    print("Parsed result:")
    for item in result["lines"]:
        print(
            f"  [{item['type']}] {item['description']} -> "
            f"Qty: {item['qty']}, Rate: ${item['unit_rate']}, Amount: ${item['amount']}"
        )
    print(f"Total: ${result['total']}")

    assert len(result["lines"]) == 6, f"Expected 6 lines, got {len(result['lines'])}"
    types = [item["type"] for item in result["lines"]]
    assert types == [
        "linehaul_fsc",
        "linehaul_fsc",
        "prepull",
        "chassis",
        "storage",
        "detention",
    ], f"Unexpected line types: {types}"

    # Check line details
    chassis_item = next(item for item in result["lines"] if item["type"] == "chassis")
    assert chassis_item["qty"] == 3.0, f"Expected chassis qty 3, got {chassis_item['qty']}"
    assert chassis_item["unit_rate"] == 45.0
    assert chassis_item["amount"] == 135.0

    detention_item = next(item for item in result["lines"] if item["type"] == "detention")
    assert detention_item["qty"] == 2.5
    assert detention_item["unit_rate"] == 85.0
    assert detention_item["amount"] == 212.5

    assert result["total"] == 2132.50, f"Expected total 2132.50, got {result['total']}"
    print("[PASS] Test 1 Passed!")


def test_tabular_ocr_output():
    print("\n--- Test 2: Tabular / OCR Columnar Output ---")
    sample_text = """
    HARBOR FREIGHT LOGISTICS
    PRO# 9948123   BOL# 771239
    CONTAINER: TGHU982134

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
    print("Parsed result:")
    for item in result["lines"]:
        print(
            f"  [{item['type']}] {item['description']} -> "
            f"Qty: {item['qty']}, Rate: ${item['unit_rate']}, Amount: ${item['amount']}"
        )
    print(f"Total: ${result['total']}")

    assert len(result["lines"]) == 6, f"Expected 6 lines, got {len(result['lines'])}"
    types = [item["type"] for item in result["lines"]]
    assert "linehaul_fsc" in types
    assert "prepull" in types
    assert "chassis" in types
    assert "storage" in types
    assert "detention" in types

    per_diem = next(item for item in result["lines"] if item["type"] == "storage")
    assert per_diem["qty"] == 4.0
    assert per_diem["unit_rate"] == 50.0
    assert per_diem["amount"] == 200.0

    waiting = next(item for item in result["lines"] if item["type"] == "detention")
    assert waiting["qty"] == 3.0
    assert waiting["unit_rate"] == 75.0
    assert waiting["amount"] == 225.0

    assert result["total"] == 2340.00
    print("[PASS] Test 2 Passed!")


def test_alternative_wording_and_labeled_fields():
    print("\n--- Test 3: Alternative Drayage Terms & Labeled Fields ---")
    sample_text = """
    CONTAINER EXPRESS CORP
    INVOICE NUMBER: CE-55219
    DATE: 2026-09-18

    Drayage / Ocean Freight: $1,100.00
    FSC (Fuel): $190.00
    Early Pull Service: $100.00
    Chassis Usage: Qty: 2, Rate: $40.00, Total: $80.00
    Yard Hold Demurrage: 3 days x $60.00 = $180.00
    Driver Wait at Terminal: 2 hours at $70.00 = $140.00

    BALANCE DUE: $1,790.00
    """

    result = parse_invoice_text(sample_text)
    print("Parsed result:")
    for item in result["lines"]:
        print(
            f"  [{item['type']}] {item['description']} -> "
            f"Qty: {item['qty']}, Rate: ${item['unit_rate']}, Amount: ${item['amount']}"
        )
    print(f"Total: ${result['total']}")

    assert len(result["lines"]) == 6
    assert result["total"] == 1790.00

    prepull = next(item for item in result["lines"] if item["type"] == "prepull")
    assert prepull["amount"] == 100.0

    chassis = next(item for item in result["lines"] if item["type"] == "chassis")
    assert chassis["qty"] == 2.0
    assert chassis["unit_rate"] == 40.0
    assert chassis["amount"] == 80.0

    storage = next(item for item in result["lines"] if item["type"] == "storage")
    assert storage["qty"] == 3.0
    assert storage["unit_rate"] == 60.0
    assert storage["amount"] == 180.0

    detention = next(item for item in result["lines"] if item["type"] == "detention")
    assert detention["qty"] == 2.0
    assert detention["unit_rate"] == 70.0
    assert detention["amount"] == 140.0

    print("[PASS] Test 3 Passed!")


def test_review_save_and_load():
    print("\n--- Test 4: Review File Save & Load ---")
    sample_text = """
    Linehaul: $1000.00
    Pre-pull: $150.00
    Total: $1150.00
    """
    data = parse_invoice_text(sample_text)

    with tempfile.TemporaryDirectory() as tmpdir:
        review_path = Path(tmpdir) / "test_review.json"
        saved = save_for_review(data, review_path)
        assert Path(saved).exists()

        loaded = load_review_data(saved)
        assert loaded["total"] == 1150.0
        assert len(loaded["lines"]) == 2
        assert loaded["lines"][0]["type"] == "linehaul_fsc"
        assert loaded["lines"][1]["type"] == "prepull"
        print(f"Saved and loaded successfully from: {saved}")

    print("[PASS] Test 4 Passed!")


def test_pdfplumber_local_extraction():
    print("\n--- Test 5: Local PDF Extraction via pdfplumber ---")
    sample_pdf = WORKSPACE_ROOT / "generated-pdfs" / "acme-imports" / "recovery_agreement_01012c4e.pdf"
    if sample_pdf.exists():
        extracted = extract_text_pdfplumber(sample_pdf)
        print(f"Extracted {len(extracted)} chars from {sample_pdf.name}")
        assert len(extracted) > 100
        assert "RateGuard AI" in extracted or "RATEGUARD" in extracted
        print("[PASS] Test 5 Passed!")
    else:
        print("Skipped Test 5: sample PDF not found.")


def test_fallback_robustness():
    print("\n--- Test 6: Fallback and Error Handling Robustness ---")
    sample_pdf = WORKSPACE_ROOT / "generated-pdfs" / "acme-imports" / "recovery_agreement_01012c4e.pdf"
    if sample_pdf.exists():
        # Passing an invalid API key should fail OCR.Space and fall back to pdfplumber
        extracted = extract_text(
            sample_pdf,
            api_key="INVALID_KEY_FOR_TESTING",
            fallback_to_pdfplumber=True,
        )
        print(f"Fallback extracted {len(extracted)} characters.")
        assert len(extracted) > 100
        print("[PASS] Test 6 Passed!")
    else:
        print("Skipped Test 6: sample PDF not found.")


def test_edge_cases():
    print("\n--- Test 7: Edge Cases (Empty, Multiline Wraps, Variants) ---")
    # Empty and whitespace
    assert parse_invoice_text("")["lines"] == []
    assert parse_invoice_text("   \n\t  ")["lines"] == []
    assert parse_invoice_text("")["total"] == 0.0

    # Complex drayage terms
    complex_invoice = """
    CONTAINER MOVE RECORD
    Ocean Freight Drayage: $1,400.00
    Fuel Charge: $250.00
    Early-Pull Service: $115.00
    Chassis Per Diem (4 days @ $45.00): $180.00
    Yard Hold Fee (2 days @ $60.00): $120.00
    Driver Wait Time (1.5 hrs @ $80.00/hr): $120.00
    Invoice Total: $2,185.00
    """
    res = parse_invoice_text(complex_invoice)
    print(f"Parsed {len(res['lines'])} lines from complex invoice:")
    for item in res["lines"]:
        print(
            f"  [{item['type']}] {item['description']} "
            f"(qty={item['qty']}, rate=${item['unit_rate']}, amount=${item['amount']})"
        )
    assert res["total"] == 2185.00
    assert len(res["lines"]) == 6
    print("[PASS] Test 7 Passed!")


if __name__ == "__main__":
    test_standard_carrier_invoice()
    test_tabular_ocr_output()
    test_alternative_wording_and_labeled_fields()
    test_review_save_and_load()
    test_pdfplumber_local_extraction()
    test_fallback_robustness()
    test_edge_cases()
    print("\n==========================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("==========================================")
