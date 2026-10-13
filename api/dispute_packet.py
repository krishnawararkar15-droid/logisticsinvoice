"""Vercel Serverless Function for /api/dispute-packet."""
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

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


class DisputePacketPayload(BaseModel):
    audit_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
async def dispute_packet_endpoint(
    request: Request, payload: Optional[DisputePacketPayload] = None
):
    if request.method == "OPTIONS":
        return {"ok": True}
    if request.method == "GET":
        return {"status": "ok", "endpoint": "dispute-packet"}

    try:
        try:
            from src.dispute_pdf import generate_dispute_packet_pdf
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="Dispute packet PDF generator module (src.dispute_pdf) is not available",
            )

        body = payload
        if body is None:
            raw = await request.json()
            body = DisputePacketPayload(**raw)

        metadata = body.metadata or {}
        sig = inspect.signature(generate_dispute_packet_pdf)
        if "metadata" in sig.parameters:
            pdf_bytes = generate_dispute_packet_pdf(body.audit_data, metadata=metadata)
        else:
            try:
                pdf_bytes = generate_dispute_packet_pdf(body.audit_data, metadata)
            except TypeError:
                pdf_bytes = generate_dispute_packet_pdf(body.audit_data)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Dispute_Packet.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Dispute packet generation failed: {str(e)}"
        )
