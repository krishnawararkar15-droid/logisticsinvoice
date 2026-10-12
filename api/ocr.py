"""Vercel Serverless Function for /api/ocr."""
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.ocr import process_invoice

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


@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
async def ocr_endpoint(request: Request, file: UploadFile = File(None)):
    if request.method == "OPTIONS":
        return {"ok": True}
    if request.method == "GET":
        return {"status": "ok", "endpoint": "ocr"}

    try:
        if file is None:
            form = await request.form()
            file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        file_bytes = await file.read()
        parsed = process_invoice(file_bytes, filename=getattr(file, "filename", "invoice.pdf"))
        return {"success": True, "data": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Extraction failed: {str(e)}")
