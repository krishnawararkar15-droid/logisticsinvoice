"""Vercel Serverless Function for /api/audit."""
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.report import build_csv_report, build_markdown_report
from src.rules import AuditResult, audit_invoice

app = FastAPI()
application = app
handler = app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditPayload(BaseModel):
    terms: Dict[str, Any]
    timeline: Dict[str, Any]
    invoice: Dict[str, Any]


@app.api_route("/api/audit", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
def audit_endpoint(payload: AuditPayload):
    try:
        terms = dict(payload.terms)
        if terms.get("chassis_day_policy") == "unknown":
            terms["chassis_day_policy"] = None
        if terms.get("prepull_includes_first_storage_day") == "unknown":
            terms["prepull_includes_first_storage_day"] = None
        elif terms.get("prepull_includes_first_storage_day") in ("yes", True):
            terms["prepull_includes_first_storage_day"] = True
        elif terms.get("prepull_includes_first_storage_day") in ("no", False):
            terms["prepull_includes_first_storage_day"] = False

        timeline = dict(payload.timeline)
        if timeline.get("prepull_request_documented") == "unknown":
            timeline["prepull_request_documented"] = None
        elif timeline.get("prepull_request_documented") in ("yes", True):
            timeline["prepull_request_documented"] = True
        elif timeline.get("prepull_request_documented") in ("no", False):
            timeline["prepull_request_documented"] = False

        result: AuditResult = audit_invoice(payload.invoice, terms, timeline)
        md_content = build_markdown_report(result)
        csv_content = build_csv_report(result)

        return {
            "success": True,
            "data": result.to_dict(),
            "markdown": md_content,
            "csv": csv_content,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
