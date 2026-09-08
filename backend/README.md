# DocuMind Backend

Requires Python 3.14.7. uv manages the Python runtime locally for this project.

Python API service for uploading and querying PDF documents.

The `/upload` endpoint accepts PDF files only.

## Environment variables

Copy `.env.example` to `.env` and replace the placeholder with your xAI API key:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```text
XAI_API_KEY=your-real-xai-api-key
```

## Run

From this `backend` folder:

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

Backend URLs:

- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Documents: http://127.0.0.1:8000/documents

The backend uses xAI Grok through `XAI_API_KEY`. Restart Uvicorn after changing `.env`.
