# PDF Text Extraction Microservice

A minimal FastAPI service that extracts text from PDFs using PyMuPDF. Designed for Render's free tier (512 MB RAM).

## Local Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`.

## Deploy on Render

1. Push this repo to GitHub.
2. In Render, click **New > Blueprint** and connect the repo.
3. Render reads `render.yaml` and creates the service automatically.
4. (Optional) Set the `API_KEY` environment variable in the Render dashboard to require authentication.

The free tier cold-starts after ~15 minutes of inactivity — first request after idle takes a few seconds.

## API Usage

### Extract text — multipart file upload

```bash
curl -X POST https://your-pdf-service.onrender.com/extract \
  -H "x-api-key: YOUR_KEY" \
  -F "file=@document.pdf"
```

### Extract text — raw binary body

```bash
curl -X POST https://your-pdf-service.onrender.com/extract \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/pdf" \
  --data-binary @document.pdf
```

### Sample response

```json
{
  "text": "Page 1 content here\nPage 2 content here",
  "pages": 2,
  "chars": 39
}
```

If the PDF contains only scanned images:

```json
{
  "text": "",
  "pages": 1,
  "chars": 0,
  "warning": "No extractable text found; PDF may be image-based and require OCR."
}
```

### Health check

```bash
curl https://your-pdf-service.onrender.com/health
# {"status":"ok"}
```
