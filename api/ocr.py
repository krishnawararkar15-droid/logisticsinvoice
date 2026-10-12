"""Vercel Serverless Function for /api/ocr."""
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
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


@app.api_route("/api/ocr", methods=["POST", "OPTIONS"])
@app.api_route("/", methods=["POST", "OPTIONS"])
async def ocr_endpoint(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        parsed = process_invoice(file_bytes, filename=file.filename)
        return {"success": True, "data": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Extraction failed: {str(e)}")
