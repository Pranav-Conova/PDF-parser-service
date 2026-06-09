import os
from io import BytesIO

from dotenv import load_dotenv

load_dotenv()

import fitz
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

app = FastAPI(title="PDF Text Extraction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_KEY")


def _check_api_key(key: str | None) -> None:
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _extract(pdf_bytes: bytes) -> dict:
    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit.")

    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Quick magic-byte check (%PDF-)
    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        raise HTTPException(status_code=422, detail="Could not open PDF — file may be corrupt.")

    pages = doc.page_count
    texts = []
    for page in doc:
        texts.append(page.get_text())
    doc.close()

    full_text = "\n".join(texts)
    result: dict = {"text": full_text, "pages": pages, "chars": len(full_text)}

    if not full_text.strip():
        result["warning"] = (
            "No extractable text found; PDF may be image-based and require OCR."
        )

    return result


@app.get("/")
def root():
    return {
        "service": "PDF Text Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "POST /extract": "Upload a PDF to extract text (multipart or raw binary).",
            "GET /health": "Health check.",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(
    request: Request,
    file: UploadFile | None = File(None),
    x_api_key: str | None = Header(None),
):
    _check_api_key(x_api_key)

    content_type = request.headers.get("content-type", "")

    # Multipart upload
    if file and file.filename:
        pdf_bytes = await file.read()
        return _extract(pdf_bytes)

    # Raw binary body (Content-Type: application/pdf)
    if "application/pdf" in content_type or (not file or not file.filename):
        pdf_bytes = await request.body()
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="No file provided.")
        return _extract(pdf_bytes)

    raise HTTPException(status_code=400, detail="No file provided.")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )
