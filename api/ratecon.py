"""Vercel Serverless Function for /api/ratecon."""
import inspect
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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


@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
async def ratecon_endpoint(request: Request, file: UploadFile = File(None)):
    if request.method == "OPTIONS":
        return {"ok": True}
    if request.method == "GET":
        return {"status": "ok", "endpoint": "ratecon"}

    try:
        try:
            from src.ratecon import parse_ratecon_file
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="Rate confirmation parser module (src.ratecon) is not available",
            )

        if file is None:
            form = await request.form()
            file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        file_bytes = await file.read()
        filename = getattr(file, "filename", "ratecon.pdf")
        sig = inspect.signature(parse_ratecon_file)
        if "filename" in sig.parameters:
            parsed = parse_ratecon_file(file_bytes, filename=filename)
        else:
            parsed = parse_ratecon_file(file_bytes)

        return {"success": True, "data": parsed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rate Con parsing failed: {str(e)}")
