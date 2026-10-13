"""Vercel Serverless Function for /api/batch-audit."""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.batch import batch_audit_invoices

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


class BatchAuditPayload(BaseModel):
    invoices: List[Dict[str, Any]]
    terms: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None


@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
async def batch_audit_endpoint(
    request: Request, payload: Optional[BatchAuditPayload] = None
):
    if request.method == "OPTIONS":
        return {"ok": True}
    if request.method == "GET":
        return {"status": "ok", "endpoint": "batch-audit"}

    try:
        body = payload
        if body is None:
            raw = await request.json()
            body = BatchAuditPayload(**raw)

        terms = body.terms or {}
        timeline = body.timeline or {}
        result = batch_audit_invoices(body.invoices, terms, timeline)
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
