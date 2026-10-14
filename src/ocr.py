"""
RateGuard AI - Drayage & Accessorial Invoice OCR and Text Extraction Module.

Provides:
- extract_text: OCR extraction via OCR.Space API with fallback to pdfplumber.
- extract_text_ocr_space: Direct OCR.Space API client.
- extract_text_pdfplumber: Local digital PDF extractor via pdfplumber.
- parse_invoice_text: Smart drayage & accessorial charge parser.
- save_for_review / load_review_data: Review helpers for human-in-the-loop audit.
- process_invoice: End-to-end wrapper for invoice files.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union

import requests

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger("rateguard.ocr")

OCR_SPACE_API_URL = "https://api.ocr.space/parse/image"
DEFAULT_OCR_SPACE_API_KEY = "K81108510188957"

# Standard drayage accessorial categories
CHARGE_CATEGORIES = (
    "linehaul_fsc",
    "prepull",
    "chassis",
    "storage",
    "detention",
)

# Ordered classification rules
# Priority: detention -> chassis -> prepull -> storage -> linehaul_fsc
CLASSIFICATION_RULES = [
    (
        "detention",
        re.compile(
            r"\b(?:detention|driver[\s-]*wait(?:ing)?|wait(?:ing)?[\s-]*time|driver[\s-]*layover|layover)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "chassis",
        re.compile(
            r"\b(?:chassis|tri[\s-]*axle)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "prepull",
        re.compile(
            r"\b(?:pre[\s-]*pull|early[\s-]*pull|drop[\s-]*yard)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "storage",
        re.compile(
            r"\b(?:yard[\s-]*storage|yard[\s-]*hold|storage|per[\s-]*diem|demurrage)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "linehaul_fsc",
        re.compile(
            r"\b(?:line[\s-]*haul|freight|base[\s-]*rate|base[\s-]*charge|drayage|ocean[\s-]*freight|fsc|fuel(?:[\s-]*(?:surcharge|charge))?)\b",
            re.IGNORECASE,
        ),
    ),
]

SUMMARY_LINE_PATTERN = re.compile(
    r"^\s*(?:invoice\s*total|total\s*(?:due|amount|charges?|drayage|freight)?|grand\s*total|net\s*total|amount\s*due|balance\s*due|subtotal\b|total\s*:\s*\$?)",
    re.IGNORECASE,
)

HEADER_LINE_PATTERN = re.compile(
    r"^\s*(?:item\s*#?|description|charge\s*description|qty|quantity|unit\s*price|rate|amount|extended)\b",
    re.IGNORECASE,
)


def _is_pdf_input(file_input: Union[str, Path, bytes, bytearray, BinaryIO]) -> bool:
    """Detect whether the provided input is a PDF file."""
    if isinstance(file_input, (str, Path)):
        return str(file_input).lower().endswith(".pdf")
    if isinstance(file_input, (bytes, bytearray)):
        return bytes(file_input).startswith(b"%PDF")
    if hasattr(file_input, "name") and isinstance(file_input.name, str):
        return file_input.name.lower().endswith(".pdf")
    return False


def _prepare_payload(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    filename: Optional[str] = None,
) -> Tuple[str, bytes, str]:
    """
    Extract filename, bytes, and MIME type for API multipart upload.
    Supports PDF, PNG, JPG, JPEG, WEBP, TIFF, BMP, JFIF, TXT, JSON.
    """
    inferred_name = filename
    if isinstance(file_input, (str, Path)):
        path = Path(file_input)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_input}")
        inferred_name = inferred_name or path.name
        with open(path, "rb") as f:
            file_bytes = f.read()
    elif isinstance(file_input, (bytes, bytearray)):
        file_bytes = bytes(file_input)
        if not inferred_name:
            if file_bytes.startswith(b"%PDF"):
                inferred_name = "document.pdf"
            elif file_bytes.startswith(b"\x89PNG"):
                inferred_name = "image.png"
            elif file_bytes.startswith(b"\xff\xd8"):
                inferred_name = "image.jpg"
            elif file_bytes.startswith(b"RIFF") and len(file_bytes) > 12 and file_bytes[8:12] == b"WEBP":
                inferred_name = "image.webp"
            elif file_bytes.startswith(b"BM"):
                inferred_name = "image.bmp"
            elif file_bytes.startswith(b"II*\x00") or file_bytes.startswith(b"MM\x00*"):
                inferred_name = "image.tiff"
            else:
                inferred_name = "document.pdf"
    elif hasattr(file_input, "read"):
        inferred_name = inferred_name or getattr(file_input, "name", "document.pdf")
        if hasattr(file_input, "seek"):
            file_input.seek(0)
        content = file_input.read()
        if isinstance(content, str):
            content = content.encode("utf-8")
        file_bytes = content
    else:
        raise TypeError(f"Unsupported file_input type: {type(file_input)}")

    final_name = inferred_name or "document.pdf"
    ext = Path(final_name).suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".jfif": "image/jpeg",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".gif": "image/gif",
        ".txt": "text/plain",
        ".json": "application/json",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")
    return final_name, file_bytes, mime_type


def extract_text_ocr_space(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    api_key: Optional[str] = None,
    timeout: int = 30,
    filename: Optional[str] = None,
) -> str:
    """
    Extract text from an invoice file using the OCR.Space API.
    Supports all image formats (PNG, JPG, WEBP, TIFF, BMP) and PDF.
    """
    effective_key = (
        api_key
        or os.environ.get("OCR_SPACE_API_KEY")
        or DEFAULT_OCR_SPACE_API_KEY
    )

    final_name, file_bytes, mime_type = _prepare_payload(file_input, filename=filename)

    files = {
        "file": (final_name, file_bytes, mime_type)
    }
    data = {
        "apikey": effective_key,
        "isTable": True,
        "OCREngine": 2,
        "scale": True,
    }

    response = requests.post(
        OCR_SPACE_API_URL,
        files=files,
        data=data,
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OCR.Space API returned HTTP {response.status_code}: {response.text}"
        )

    result = response.json()
    if result.get("IsErroredOnProcessing"):
        err = result.get("ErrorMessage") or "Unknown OCR.Space error"
        if isinstance(err, list):
            err = "; ".join(err)
        raise RuntimeError(f"OCR.Space error: {err}")

    parsed_results = result.get("ParsedResults", [])
    if not parsed_results:
        raise RuntimeError("OCR.Space returned no parsed results.")

    # Collect parsed text from results
    texts: List[str] = []
    for item in parsed_results:
        pt = item.get("ParsedText", "")
        if pt:
            texts.append(pt)

    if not texts:
        return parsed_results[0].get("ParsedText", "").strip()

    return "\n".join(texts).strip()


def extract_text_pdfplumber(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO]
) -> str:
    """
    Extract digital text from a PDF file using pdfplumber locally.

    Args:
        file_input: Path, bytes, or file-like object representing a PDF.

    Returns:
        Extracted raw text string.
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError(
            "pdfplumber is not installed. Please install it with 'pip install pdfplumber'."
        )

    if isinstance(file_input, (bytes, bytearray)):
        stream: Any = io.BytesIO(file_input)
    elif hasattr(file_input, "read"):
        content = file_input.read()
        if hasattr(file_input, "seek"):
            file_input.seek(0)
        if isinstance(content, str):
            content = content.encode("utf-8")
        stream = io.BytesIO(content)
    else:
        path = Path(file_input)
        if not path.is_file():
            raise FileNotFoundError(f"PDF file not found: {file_input}")
        stream = str(path)

    extracted_pages: List[str] = []
    with pdfplumber.open(stream) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                extracted_pages.append(t)

    return "\n".join(extracted_pages).strip()


def extract_text(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    api_key: Optional[str] = None,
    timeout: int = 30,
    fallback_to_pdfplumber: bool = True,
    filename: Optional[str] = None,
) -> str:
    """
    Primary extraction entry point.
    Supports PDF and all image formats (PNG, JPG, JPEG, WEBP, TIFF, BMP).
    If digital PDF, extracts locally via pdfplumber for instant speed and accuracy.
    If scanned PDF or image, uses OCR.Space API.
    """
    is_pdf = _is_pdf_input(file_input) or (bool(filename and filename.lower().endswith(".pdf")))

    # Fast-path for digital PDFs: extract text instantly without network latency
    if is_pdf and PDFPLUMBER_AVAILABLE:
        try:
            pdf_text = extract_text_pdfplumber(file_input)
            if pdf_text and len(pdf_text.strip()) > 30:
                logger.info("Instantly extracted %d chars via local pdfplumber", len(pdf_text))
                return pdf_text
        except Exception as exc:
            logger.debug("Fast-path pdfplumber extraction note: %s", exc)

    # Scanned PDF or Image: run OCR.Space API
    try:
        return extract_text_ocr_space(file_input, api_key=api_key, timeout=timeout, filename=filename)
    except Exception as exc:
        logger.warning("OCR.Space API extraction failed: %s", exc)
        if fallback_to_pdfplumber and is_pdf and PDFPLUMBER_AVAILABLE:
            logger.info("Falling back to local pdfplumber extraction.")
            return extract_text_pdfplumber(file_input)
        raise


def extract_text_from_file(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    **kwargs: Any,
) -> str:
    """Alias for extract_text."""
    return extract_text(file_input, **kwargs)


NON_ITEM_PATTERN = re.compile(
    r"(?:"
    r"\b(?:broker|bill\s*to|shipment\s*details|remit|wire|routing|acct|account|bank|"
    r"suite|street|avenue|blvd|way|attn|payable|"
    r"scac|usdot|certified|edi\s*system|"
    r"terminal\s*out-gate|terminal\s*in-gate|actual\s*delivery|appointment|"
    r"compliance|governed|movements\s*billed|herein|rendered\s*under|standard\s*terms|"
    r"interchange\s*and\s*facilities|agreement\s*\(uiia\)|statement:|page\s*\d+\s*of\s*\d+|"
    r"chassis\s*(?:number|#|id)|carrier\s*drop|drop\s*yard\s*:|"
    r"port\s*terminal|delivery\s*facility|return\s*depot|consignee|"
    r"remittance\s*dept|p\.?o\.?\s*box|logistics\s*llc|freight\s*logistics|"
    r"invoice\s*number|invoice\s*date|"
    r"container\s*#|container\s*no|tclu|msku|medu|cma|cosu|oneu|phone|tel|email|fax|date:|terms:)\b|"
    r"\bmc[\s#:]|\bdot[\s#:]"
    r")",
    re.IGNORECASE,
)






def _classify_line(line_text: str) -> Optional[str]:
    """Determine the drayage charge type for a single line."""
    lower = line_text.lower().strip()

    # Skip lines that are purely summary/total lines
    if SUMMARY_LINE_PATTERN.search(lower):
        return None

    # Skip header row lines
    if HEADER_LINE_PATTERN.search(lower):
        return None

    # Skip address, shipment metadata, or remittance lines
    if NON_ITEM_PATTERN.search(lower):
        return None

    for category, pattern in CLASSIFICATION_RULES:
        if pattern.search(lower):
            return category

    return None



def _clean_description(line: str) -> str:
    """Produce a readable description from the raw line."""
    # Strip monetary amounts, equals signs, trailing colons/spaces
    cleaned = re.sub(r"[@xX]\s*\$?[0-9,.]+(?:/[a-z]+)?", " ", line)
    cleaned = re.sub(r"\$\s*[0-9,.]+", " ", cleaned)
    cleaned = re.sub(r"[:=]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or line.strip()


def _parse_line_values(line: str) -> Tuple[float, float, float]:
    """
    Parse (qty, unit_rate, amount) from a charge line.
    Handles:
    - 3 Days @ $45.00/day = $135.00
    - 2.5 hrs @ $85.00 $212.50
    - Qty: 2, Rate: 75.00, Amount: 150.00
    - Table format: 'Yard Storage  2  75.00  150.00'
    - Single charge: 'Pre-pull Fee  $150.00'
    """
    # Strategy 1: Explicit labeled fields (Qty: ..., Rate: ..., Amount: ...)
    qty_m = re.search(
        r"\b(?:qty|quantity|hours?|hrs?|days?|units?)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)",
        line,
        re.I,
    )
    rate_m = re.search(
        r"\b(?:unit\s*rate|unit\s*price|rate|price)\s*[:=]?\s*\$?\s*([0-9,]+(?:\.[0-9]+)?)",
        line,
        re.I,
    )
    amt_m = re.search(
        r"\b(?:amount|extended(?:\s*amount|\s*price)?|cost|total|charges?)\s*[:=]?\s*\$?\s*([0-9,]+(?:\.[0-9]+)?)",
        line,
        re.I,
    )

    labeled_hits = sum(1 for x in (qty_m, rate_m, amt_m) if x is not None)
    if labeled_hits >= 2:
        q = float(qty_m.group(1)) if qty_m else None
        r = float(rate_m.group(1).replace(",", "")) if rate_m else None
        a = float(amt_m.group(1).replace(",", "")) if amt_m else None

        if q is not None and r is not None and a is not None:
            return q, r, a
        if q is not None and r is not None:
            return q, r, round(q * r, 2)
        if q is not None and a is not None:
            r = round(a / q, 2) if q > 0 else a
            return q, r, a
        if r is not None and a is not None:
            q = round(a / r, 2) if r > 0 else 1.0
            return q, r, a

    # Strategy 2: Expressions with @, x, at
    at_pattern = re.compile(
        r"(?P<qty>[0-9]+(?:\.[0-9]+)?)\s*(?:hrs?|hours?|days?|ea|units?|moves?)?\s*(?:@|x|X|\bat\b)\s*\$?\s*(?P<rate>[0-9,]+(?:\.[0-9]+)?)(?:/(?:hr|hour|day|ea|unit))?(?:\s*(?:=|-|\$|:)?\s*\$?\s*(?P<amount>[0-9,]+(?:\.[0-9]+)?))?",
        re.I,
    )
    at_m = at_pattern.search(line)
    if at_m:
        q = float(at_m.group("qty"))
        r = float(at_m.group("rate").replace(",", ""))
        amt_str = at_m.group("amount")
        if amt_str:
            a = float(amt_str.replace(",", ""))
        else:
            # Check if there is an amount further along the line
            rest = line[at_m.end():]
            other_amts = re.findall(r"\$\s*([0-9,]+(?:\.[0-9]{2})?)", rest)
            if other_amts:
                a = float(other_amts[-1].replace(",", ""))
            else:
                a = round(q * r, 2)
        return q, r, a

    # Strategy 3: Tabular or columnar numbers
    # Clean out distracting non-amount numbers first
    cleaned = line
    # Strip dates (e.g. 10/12/2026, 2026-10-12)
    cleaned = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", cleaned)
    # Strip times (e.g. 14:30)
    cleaned = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", cleaned)
    # Strip percentages (e.g. 18.5%)
    cleaned = re.sub(r"\b\d+(?:\.\d+)?%", " ", cleaned)
    # Strip container lengths (e.g. 20ft, 40ft, 40', 53ft)
    cleaned = re.sub(r"\b(?:20|40|45|53)\s*(?:ft|'|foot|feet)\b", " ", cleaned, flags=re.I)
    # Strip tariff codes (e.g. Item 100-D)
    cleaned = re.sub(r"\bitem\s*[0-9]+-?[a-z]?\b", " ", cleaned, flags=re.I)
    # Strip PRO / Invoice labels with numbers (e.g. PRO# 991823)
    cleaned = re.sub(r"\b(?:pro|inv|invoice|po|bol|order)\s*#?\s*[0-9a-z-]+\b", " ", cleaned, flags=re.I)

    num_matches = re.findall(r"\$?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)", cleaned)
    nums: List[float] = []
    for token in num_matches:
        raw_num = token.replace(",", "")
        try:
            val = float(raw_num)
            nums.append(val)
        except ValueError:
            pass

    if len(nums) >= 3:
        n1, n2, n3 = nums[-3], nums[-2], nums[-1]
        if abs(n1 * n2 - n3) < 0.1:
            return n1, n2, n3
        if n1 <= 100 and n2 > 0:
            return n1, n2, n3
        return 1.0, n3, n3

    if len(nums) == 2:
        n1, n2 = nums[0], nums[1]
        if abs(n1 - n2) < 0.01:
            return 1.0, n1, n2
        if 0 < n1 <= 100 and n2 >= n1:
            return n1, round(n2 / n1, 2), n2
        if n1 > 0 and (n2 / n1).is_integer() and (n2 / n1) <= 100:
            return round(n2 / n1, 2), n1, n2
        return 1.0, n2, n2

    if len(nums) == 1:
        return 1.0, nums[0], nums[0]

    return 1.0, 0.0, 0.0


def _extract_invoice_total(raw_text: str, parsed_lines: List[Dict[str, Any]]) -> float:
    """
    Extract or calculate the invoice total.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Specific total patterns checked from bottom to top
    specific_patterns = [
        re.compile(
            r"(?:invoice\s*total|total\s*amount\s*due|amount\s*due|balance\s*due|grand\s*total|net\s*total|total\s*due|total\s*charges?)\s*[:=]?\s*\$?\s*([0-9,]+(?:\.[0-9]{2})?)",
            re.I,
        ),
        re.compile(
            r"^\s*total\s*[:=]?\s*\$?\s*([0-9,]+(?:\.[0-9]{2})?)",
            re.I,
        ),
        re.compile(
            r"\btotal\s*[:=]?\s*\$?\s*([0-9,]+(?:\.[0-9]{2})?)",
            re.I,
        ),
    ]

    for pat in specific_patterns:
        for line in reversed(lines):
            m = pat.search(line)
            if m:
                try:
                    val = float(m.group(1).replace(",", ""))
                    if val > 0:
                        return round(val, 2)
                except ValueError:
                    pass

    # Fall back to sum of lines
    computed = sum(float(item.get("amount", 0.0)) for item in parsed_lines)
    return round(computed, 2)


def parse_invoice_text(raw_text: str) -> Dict[str, Any]:
    """
    Smart parser for drayage carrier invoices.

    Searches for common drayage charge lines:
    - linehaul_fsc: Linehaul, Freight, Base rate, FSC, Fuel surcharge, Drayage
    - prepull: Pre-pull, Prepull, Early pull, Drop yard
    - chassis: Chassis, Chassis usage, Chassis split
    - storage: Storage, Yard storage, Per diem, Yard hold
    - detention: Detention, Driver wait, Waiting time

    Parses quantities, unit rates, and amounts.
    Extracts or computes invoice total.

    Returns:
        Structured dictionary:
        {
            "lines": [
                {
                    "type": str,
                    "description": str,
                    "qty": float,
                    "unit_rate": float,
                    "amount": float
                }
            ],
            "total": float,
            "raw_text": str
        }
    """
    raw_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    parsed_lines: List[Dict[str, Any]] = []

    idx = 0
    n = len(raw_lines)
    while idx < n:
        current_line = raw_lines[idx]

        # Check for summary lines (not line items)
        if SUMMARY_LINE_PATTERN.search(current_line):
            idx += 1
            continue

        category = _classify_line(current_line)
        if not category:
            idx += 1
            continue

        # Lookahead: if the current line has a charge category keyword but no amount,
        # and the next line has an amount without its own charge keyword, merge them.
        merged_line = current_line
        if idx + 1 < n:
            next_line = raw_lines[idx + 1]
            has_nums_cur = bool(re.search(r"\$?\s*[0-9]+(?:\.[0-9]{2})?", current_line))
            next_category = _classify_line(next_line)
            has_nums_next = bool(re.search(r"\$?\s*[0-9]+(?:\.[0-9]{2})?", next_line))

            if not has_nums_cur and has_nums_next and next_category is None:
                merged_line = f"{current_line} {next_line}"
                idx += 1

        qty, unit_rate, amount = _parse_line_values(merged_line)

        # Include if amount or rate > 0
        if amount > 0 or unit_rate > 0:
            parsed_lines.append(
                {
                    "type": category,
                    "description": _clean_description(merged_line),
                    "qty": round(float(qty), 2),
                    "unit_rate": round(float(unit_rate), 2),
                    "amount": round(float(amount), 2),
                }
            )

        idx += 1

    total = _extract_invoice_total(raw_text, parsed_lines)

    return {
        "lines": parsed_lines,
        "total": round(float(total), 2),
        "raw_text": raw_text,
    }


def process_invoice(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    api_key: Optional[str] = None,
    timeout: int = 30,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract text and parse structured drayage invoice data in one call.
    Accepts PDF, image (PNG, JPG, WEBP, TIFF, BMP), and plain text.
    """
    text = extract_text(file_input, api_key=api_key, timeout=timeout, filename=filename)
    return parse_invoice_text(text)


def save_for_review(parsed_data: Dict[str, Any], filepath: Union[str, Path]) -> str:
    """
    Save parsed invoice data to JSON for broker inspection and confirmation.

    Args:
        parsed_data: Dictionary returned by parse_invoice_text.
        filepath: Destination file path.

    Returns:
        Absolute file path where data was saved.
    """
    path = Path(filepath).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    logger.info("Saved review data to %s", path)
    return str(path)


def load_review_data(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Load reviewed invoice data from JSON.

    Args:
        filepath: Source JSON file path.

    Returns:
        Structured dictionary.
    """
    path = Path(filepath).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Review file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid review file format in {path}: expected dict, got {type(data)}"
        )

    return data
