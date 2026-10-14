"""
RateGuard AI - Rate Confirmation (Rate Con) & Contract Term Parser Module.

Provides:
- extract_ratecon_text(file_input, filename=None) -> str:
    Smart text extractor for Rate Con documents (PDF, image, text) using
    local pdfplumber or OCR.Space API from src.ocr.
- parse_ratecon_text(raw_text: str) -> dict:
    Deterministic regex parser extracting agreed rate terms and load metadata.
- parse_ratecon_file(file_input, filename=None) -> dict:
    End-to-end wrapper from file to structured terms dictionary.
"""

from __future__ import annotations

import io
import logging
import os
import re
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Union

from src.ocr import (
    PDFPLUMBER_AVAILABLE,
    extract_text,
    extract_text_ocr_space,
    extract_text_pdfplumber,
)

logger = logging.getLogger("rateguard.ratecon")


def _is_pdf_data(file_input: Any, filename: Optional[str] = None) -> bool:
    """Check if input represents a PDF by extension or header bytes."""
    if filename and filename.lower().endswith(".pdf"):
        return True
    if isinstance(file_input, (str, Path)) and str(file_input).lower().endswith(".pdf"):
        return True
    if isinstance(file_input, (bytes, bytearray)) and bytes(file_input).startswith(b"%PDF"):
        return True
    if hasattr(file_input, "name") and isinstance(file_input.name, str):
        return file_input.name.lower().endswith(".pdf")
    return False


def extract_ratecon_text(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    filename: Optional[str] = None,
) -> str:
    """
    Extract raw text from a Rate Confirmation document (PDF, image, or text).
    
    Prefers local digital extraction via pdfplumber for PDFs for speed and reliability,
    falling back to OCR.Space API as appropriate.
    """
    # 1. Plain text string already passed (not a file path on disk)
    if isinstance(file_input, str):
        if not os.path.exists(file_input) and ("\n" in file_input or " " in file_input):
            return file_input.strip()

    # 2. Path or file path string
    if isinstance(file_input, (str, Path)) and os.path.exists(file_input):
        path = Path(file_input)
        suffix = path.suffix.lower()
        if suffix in (".txt", ".json", ".md", ".csv"):
            return path.read_text(encoding="utf-8", errors="replace").strip()
        if suffix == ".pdf":
            if PDFPLUMBER_AVAILABLE:
                try:
                    text = extract_text_pdfplumber(path)
                    if text and len(text.strip()) > 10:
                        return text.strip()
                except Exception as exc:
                    logger.warning("Local pdfplumber extraction failed on %s: %s", path, exc)
            return extract_text(path).strip()
        # Images (.png, .jpg, etc.)
        return extract_text(path).strip()

    # 3. Bytes / bytearray
    if isinstance(file_input, (bytes, bytearray)):
        raw_bytes = bytes(file_input)
        if _is_pdf_data(raw_bytes, filename=filename):
            if PDFPLUMBER_AVAILABLE:
                try:
                    text = extract_text_pdfplumber(raw_bytes)
                    if text and len(text.strip()) > 10:
                        return text.strip()
                except Exception as exc:
                    logger.warning("Local pdfplumber extraction failed on bytes: %s", exc)
            return extract_text(raw_bytes).strip()
        
        # Check if plain text bytes
        try:
            decoded = raw_bytes.decode("utf-8")
            if any(k in decoded.lower() for k in ("rate", "load", "carrier", "order", "bol", "chassis")):
                return decoded.strip()
        except UnicodeDecodeError:
            pass
        return extract_text(raw_bytes).strip()

    # 4. File-like object (e.g. io.BytesIO or UploadFile)
    if hasattr(file_input, "read"):
        if hasattr(file_input, "seek"):
            file_input.seek(0)
        content = file_input.read()
        if isinstance(content, str):
            return content.strip()
        return extract_ratecon_text(content, filename=filename or getattr(file_input, "name", None))

    # Fallback to standard OCR extractor
    return extract_text(file_input).strip()


def _clean_str(val: Optional[str]) -> Optional[str]:
    """Strip whitespace and common delimiter artifacts."""
    if not val:
        return None
    cleaned = val.strip().strip("#:-,;|").strip()
    return cleaned if cleaned else None


def _to_float(val: Optional[str]) -> Optional[float]:
    """Parse monetary or numeric string into float."""
    if not val:
        return None
    val_clean = val.replace(",", "").replace("$", "").strip()
    try:
        return float(val_clean)
    except (ValueError, TypeError):
        return None


def parse_ratecon_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse agreed rate terms and load metadata from raw Rate Con text.

    Finds agreed terms:
    - linehaul_fsc: looks for "Linehaul", "Base Rate", "Freight", "Total Flat", "All-In", "Agreed Rate", "FSC" amounts.
    - chassis_per_day: looks for "Chassis", "Chassis per day", "$45/day", etc.
    - storage_per_day: looks for "Yard Storage", "Storage / day", "$45/day", etc.
    - detention_per_hour: looks for "Detention", "$75/hr", "$85/hour", etc.
    - detention_free_hours: looks for "2 hours free", "2 free hrs", etc.
    - prepull_fee: looks for "Pre-pull", "Prepull", "$150", etc.
    - load_id / order_no / bol_no / container_no
    - carrier_name

    Returns:
        dict: {"terms": {...}, "metadata": {...}, "raw_text": raw_text}
    """
    text = raw_text or ""

    # ---------------------------------------------------------
    # 1. METADATA EXTRACTION
    # ---------------------------------------------------------
    carrier_name: Optional[str] = None
    carrier_match = re.search(
        r"(?:^|\n)[ \t]*(?:carrier\s*(?:name|company)?\s*[:#]\s*|carrier:\s*)([^\n\r,;|]+)",
        text,
        re.IGNORECASE,
    )
    if carrier_match:
        carrier_name = _clean_str(carrier_match.group(1))

    load_id: Optional[str] = None
    load_match = re.search(
        r"(?:load\s*(?:id|#|no\.?|number|ref(?:erence)?)\s*[:#]?|load\s*[:#]|confirmation\s*(?:#|no\.?|id|number)\s*[:#]?|rate\s*con(?:firmation)?\s*(?:#|no\.?|id)\s*[:#]?)\s*([^\n\r,;|]+)",
        text,
        re.IGNORECASE,
    )
    if load_match:
        load_id = _clean_str(load_match.group(1))

    order_no: Optional[str] = None
    order_match = re.search(
        r"(?:order\s*(?:id|#|no\.?|number)\s*[:#]?|order\s*[:#]|po\s*(?:#|no\.?|number)?\s*[:#]?|purchase\s*order\s*(?:#|no\.?)?\s*[:#]?)\s*([^\n\r,;|]+)",
        text,
        re.IGNORECASE,
    )
    if order_match:
        order_no = _clean_str(order_match.group(1))

    bol_no: Optional[str] = None
    bol_match = re.search(
        r"(?:bol\s*(?:id|#|no\.?|number|ref(?:erence)?)\s*[:#]?|bol\s*[:#]|bill\s*of\s*lading\s*(?:id|#|no\.?|number|ref(?:erence)?)\s*[:#]?|bill\s*of\s*lading\s*[:#])\s*([^\n\r,;|]+)",
        text,
        re.IGNORECASE,
    )
    if bol_match:
        bol_no = _clean_str(bol_match.group(1))

    container_no: Optional[str] = None
    container_match = re.search(
        r"(?:container\s*(?:id|#|no\.?|number)?\s*[:#]?|equipment\s*(?:id|#|no\.?|number)?\s*[:#]?|cntr\s*(?:#|no\.?)?\s*[:#]?)\s*([A-Za-z]{4}\s*[-]?\s*[0-9]{6,7}(?:-[0-9])?)",
        text,
        re.IGNORECASE,
    )
    if container_match:
        container_no = _clean_str(container_match.group(1))
    else:
        # Fallback to standard 4-letter + 6/7-digit ISO container code
        iso_match = re.search(r"\b([A-Z]{4}\s+[0-9]{6,7}(?:-[0-9])?|[A-Z]{4}[0-9]{6,7}(?:-[0-9])?)\b", text)
        if iso_match:
            container_no = _clean_str(iso_match.group(1))

    # ---------------------------------------------------------
    # 2. TERMS EXTRACTION
    # ---------------------------------------------------------

    # A. Linehaul & FSC
    # Check for combined linehaul / all-in / flat rate
    linehaul_fsc: Optional[float] = None
    base_rate_val: Optional[float] = None
    fsc_val: Optional[float] = None

    # Search for base/linehaul/freight/all-in/total flat rate
    lh_match = re.search(
        r"(?:line[\s-]*haul(?:[\s/]*(?:base[\s-]*rate|fsc|rate|amount|fee))?|base[\s-]*rate|freight(?:[\s-]*charge|[\s-]*rate)?|agreed[\s-]*rate|all[\s-]*in(?:[\s-]*rate)?|total[\s-]*flat|flat[\s-]*rate)\s*[:=\-]?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
        text,
        re.IGNORECASE,
    )
    if lh_match:
        base_rate_val = _to_float(lh_match.group(1))

    # Search for separate FSC / fuel surcharge
    fsc_match = re.search(
        r"(?<!linehaul[\s+])\b(?:fsc|fuel(?:[\s-]*(?:surcharge|charge))?(?:[\s/]*(?:\(fsc\)|fsc))?)\s*[:=\-]?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
        text,
        re.IGNORECASE,
    )
    if fsc_match:
        fsc_val = _to_float(fsc_match.group(1))

    if base_rate_val is not None and fsc_val is not None:
        header_text = (lh_match.group(0) if lh_match else "").lower()
        if "all-in" not in header_text and "total" not in header_text and "+" not in header_text:
            linehaul_fsc = round(base_rate_val + fsc_val, 2)
        else:
            linehaul_fsc = base_rate_val
    elif base_rate_val is not None:
        linehaul_fsc = base_rate_val
    elif fsc_val is not None:
        linehaul_fsc = fsc_val

    # B. Chassis per day
    chassis_per_day: Optional[float] = None
    chassis_match = re.search(
        r"chassis[^\n\r$]*?\$?\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:/\s*(?:day|diem)|\s*per\s*(?:day|diem)|\s*daily|\b)",
        text,
        re.IGNORECASE,
    )
    if chassis_match:
        chassis_per_day = _to_float(chassis_match.group(1))
    else:
        # Pattern like "$45/day chassis"
        rev_ch_match = re.search(
            r"\$\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:/\s*(?:day|diem)|\s*per\s*(?:day|diem))[^\n\r]*?chassis",
            text,
            re.IGNORECASE,
        )
        if rev_ch_match:
            chassis_per_day = _to_float(rev_ch_match.group(1))

    # C. Storage per day
    storage_per_day: Optional[float] = None
    storage_match = re.search(
        r"(?:yard[\s-]*storage|storage|yard[\s-]*hold)[^\n\r$]*?\$?\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:/\s*(?:day|diem)|\s*per\s*(?:day|diem)|\s*daily|\b)",
        text,
        re.IGNORECASE,
    )
    if storage_match:
        storage_per_day = _to_float(storage_match.group(1))
    else:
        rev_st_match = re.search(
            r"\$\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:/\s*(?:day|diem)|\s*per\s*(?:day|diem))[^\n\r]*?(?:yard[\s-]*storage|storage)",
            text,
            re.IGNORECASE,
        )
        if rev_st_match:
            storage_per_day = _to_float(rev_st_match.group(1))

    # D. Detention per hour
    detention_per_hour: Optional[float] = None
    det_match = re.search(
        r"(?:detention(?:[\s-]*rate)?|waiting[\s-]*time|driver[\s-]*wait(?:ing)?)[^\n\r$]*?\$?\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:/\s*(?:hr|hour)|\s*per\s*(?:hr|hour)|\s*hourly|\b)",
        text,
        re.IGNORECASE,
    )
    if det_match:
        detention_per_hour = _to_float(det_match.group(1))
    else:
        rev_det_match = re.search(
            r"\$\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:/\s*(?:hr|hour)|\s*per\s*(?:hr|hour))[^\n\r]*?detention",
            text,
            re.IGNORECASE,
        )
        if rev_det_match:
            detention_per_hour = _to_float(rev_det_match.group(1))

    # E. Detention free hours
    detention_free_hours: Optional[float] = None
    fh_match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:hours?|hrs?)\s*free\b|([0-9]+(?:\.[0-9]+)?)\s*free\s*(?:hours?|hrs?)\b|free\s*(?:time|hours?|hrs?)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)|detention[^\n\r]*?([0-9]+(?:\.[0-9]+)?)\s*(?:hours?|hrs?)\s*free",
        text,
        re.IGNORECASE,
    )
    if fh_match:
        found_fh = next((g for g in fh_match.groups() if g is not None), None)
        if found_fh:
            detention_free_hours = _to_float(found_fh)

    # F. Pre-pull fee
    prepull_fee: Optional[float] = None
    prepull_match = re.search(
        r"(?:pre[\s-]*pull|early[\s-]*pull|drop[\s-]*yard)(?:[\s-]*fee)?[^\n\r$]*?\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        text,
        re.IGNORECASE,
    )
    if prepull_match:
        prepull_fee = _to_float(prepull_match.group(1))

    # G. Policy & Free Day hints if present
    chassis_day_policy: str = "calendar_day"
    if re.search(r"\b24[\s-]*hour[\s-]*block\b|\b24h\b", text, re.IGNORECASE):
        chassis_day_policy = "24h_block"

    chassis_free_days: int = 0
    cf_match = re.search(r"([0-9]+)\s*(?:free\s*chassis\s*days?|chassis\s*free\s*days?)", text, re.IGNORECASE)
    if cf_match:
        chassis_free_days = int(cf_match.group(1))

    storage_free_days: int = 0
    sf_match = re.search(r"([0-9]+)\s*(?:free\s*storage\s*days?|storage\s*free\s*days?)", text, re.IGNORECASE)
    if sf_match:
        storage_free_days = int(sf_match.group(1))

    terms: Dict[str, Any] = {
        "linehaul_fsc": linehaul_fsc,
        "prepull_fee": prepull_fee,
        "chassis_per_day": chassis_per_day,
        "storage_per_day": storage_per_day,
        "detention_per_hour": detention_per_hour,
        "detention_free_hours": detention_free_hours if detention_free_hours is not None else 2.0,
        "chassis_day_policy": chassis_day_policy,
        "chassis_free_days": chassis_free_days,
        "chassis_min_days": 0,
        "storage_free_days": storage_free_days,
        "prepull_includes_first_storage_day": None,
        "direct_move_hours_threshold": 24,
    }

    metadata: Dict[str, Optional[str]] = {
        "carrier_name": carrier_name,
        "load_id": load_id,
        "order_no": order_no,
        "bol_no": bol_no,
        "container_no": container_no,
    }

    return {
        "terms": terms,
        "metadata": metadata,
        "raw_text": raw_text,
    }


def parse_ratecon_file(
    file_input: Union[str, Path, bytes, bytearray, BinaryIO],
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    End-to-end wrapper: extracts text from ratecon document and parses terms and metadata.
    """
    raw_text = extract_ratecon_text(file_input, filename=filename)
    return parse_ratecon_text(raw_text)
