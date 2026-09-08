# DocuMind

A local RAG application with a Python FastAPI backend and an Angular frontend.

## First-time setup

### Backend environment

Create `backend/.env` from the example and add your xAI API key:

```powershell
cd backend
Copy-Item .env.example .env
notepad .env
```

Set this value in `.env`:

```text
XAI_API_KEY=your-xai-api-key
```

Do not commit `.env` or share the API key.

## Run both applications

Use two terminals.

### Terminal 1: backend

```powershell
cd E:\Srikanth\Srikanth\Learning\Agentic_Learining\Project_1\DocuMind\backend
uv sync
uv run uvicorn app.main:app --reload
```

Backend URLs:

- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Documents: http://127.0.0.1:8000/documents

### Terminal 2: frontend

```powershell
cd E:\Srikanth\Srikanth\Learning\Agentic_Learining\Project_1\DocuMind\frontend
npm install
npm start
```

Open the application at http://localhost:4200.

The frontend uploads PDFs, lists existing documents, and sends session-aware chat requests to the backend.
