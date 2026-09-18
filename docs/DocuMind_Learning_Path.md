# DocuMind: Learn Before You Build

This is a beginner-friendly path for understanding the ideas used in DocuMind before running the complete application.

The project is a local Retrieval-Augmented Generation (RAG) application:

- **Frontend:** Angular and TypeScript
- **Backend:** Python and FastAPI
- **Document processing:** PDF loading and text splitting
- **Search:** embeddings and ChromaDB vector search
- **Answer generation:** LangChain and xAI Grok
- **Conversation memory:** a session ID and chat history

## How to use this file

Read one lesson at a time. Run the small code examples first, answer the checkpoint questions, and only then read the matching project files.

This Markdown file uses the Jupytext percent format. It can be opened as a notebook in VS Code or converted with Jupytext. A matching `.ipynb` file is included beside it for direct notebook use.

> Do not put a real API key in a notebook or commit it to Git.

## Learning map

1. Python and project structure
2. HTTP, APIs, and JSON
3. FastAPI routes
4. Files, PDFs, pages, and chunks
5. Embeddings and semantic search
6. RAG: retrieve, then generate
7. Chat history and sessions
8. Angular components and services
9. Full request flow
10. Run and extend DocuMind

---

# %% [markdown]
## Lesson 1: Python and project structure

### Goal

Understand how a Python application is split into modules and how a function turns input into output.

### Key idea

A module is a Python file. A package is a directory of related modules. DocuMind's backend starts at `backend/app/main.py`, sends API work to `backend/app/api/routes.py`, and keeps RAG logic in `backend/app/core/rag.py`.

# %%
name = "learner"
project = "DocuMind"

print(f"Hello, {name}!")
print(f"You are learning {project}.")

# %% [markdown]
### Exercise

Write a function called `describe_project` that accepts a project name and returns a sentence describing it.

### Checkpoint

- What is the difference between a file and a module?
- Which file creates the FastAPI application?
- Which file owns the RAG chain?

### Project connection

Read:

- `backend/app/main.py`
- `backend/app/api/routes.py`
- `backend/app/core/rag.py`

---

# %% [markdown]
## Lesson 2: HTTP, APIs, and JSON

### Goal

Understand how a frontend asks a backend to do work.

### Key idea

An API is a contract. A client sends an HTTP request containing a method, URL, headers, and sometimes a body. The server returns a status code and a response body, often JSON.

Common methods in DocuMind:

| Method | Meaning | DocuMind example |
| --- | --- | --- |
| GET | Read data | `/health`, `/documents` |
| POST | Create or process data | `/upload`, `/chat` |
| DELETE | Remove data | `/sessions/{session_id}` |

# %%
health_response = {"status": "ok"}
chat_response = {"answer": "The answer would be here."}

print(health_response["status"])
print(chat_response["answer"])

# %% [markdown]
### Exercise

Create a dictionary representing an upload response with these fields: `message`, `files`, and `chunks_indexed`.

### Checkpoint

- What does a `200` response mean?
- Why is `/chat` a `POST` endpoint rather than a `GET` endpoint?
- What information does the frontend need from a chat response?

### Project connection

Open the routes in `backend/app/api/routes.py`. Notice that each decorator such as `@router.get` or `@router.post` defines part of the API contract.

---

# %% [markdown]
## Lesson 3: FastAPI routes

### Goal

See how Python functions become web endpoints.

### Key idea

FastAPI reads type annotations and function parameters to validate incoming data and generate interactive documentation. The project exposes Swagger documentation at `/docs`.

A minimal route looks like this:

```python
@router.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello"}
```

# %%
# This is a plain Python version of an API route.
def health_check() -> dict[str, str]:
    return {"status": "ok"}

print(health_check())

# %% [markdown]
### Exercise

Design a route contract for `GET /documents`. What JSON should it return when there are no files?

### Checkpoint

- What does `UploadFile` represent?
- Why does the upload endpoint reject non-PDF files?
- What status code should an empty chat message receive?

### Project connection

Trace these functions in `backend/app/api/routes.py`:

1. `health_check`
2. `list_documents`
3. `upload_files`
4. `chat`
5. `clear_session`

---

# %% [markdown]
## Lesson 4: Files, PDFs, pages, and chunks

### Goal

Understand why a PDF is converted into smaller text pieces before search.

### Key idea

A document is too large and unstructured to send wholesale for every question. DocuMind loads PDF pages, then splits their text into overlapping chunks.

The current settings are:

- `chunk_size=1000`
- `chunk_overlap=200`

Overlap helps preserve meaning when an important sentence crosses a chunk boundary.

# %%
document = "FastAPI creates APIs. ChromaDB stores vectors. RAG retrieves useful context."
chunk_size = 30
chunk_overlap = 5

chunks = []
start = 0
while start < len(document):
    end = start + chunk_size
    chunks.append(document[start:end])
    start += chunk_size - chunk_overlap

for number, chunk in enumerate(chunks, start=1):
    print(number, repr(chunk))

# %% [markdown]
### Exercise

Change `chunk_size` and `chunk_overlap`. Observe how the number and contents of chunks change.

### Checkpoint

- Why not send the entire PDF to the language model every time?
- What problem does overlap help with?
- Where does DocuMind load PDFs from?

### Project connection

Read the upload flow in `backend/app/api/routes.py`:

1. Save the PDF in `uploaded_docs`.
2. Load all PDFs with `PyPDFLoader`.
3. Split pages with `RecursiveCharacterTextSplitter`.
4. Add chunks to the vector store.

---

# %% [markdown]
## Lesson 5: Embeddings and semantic search

### Goal

Understand how text becomes searchable by meaning rather than exact keywords.

### Key idea

An embedding is a list of numbers representing the meaning of text. Texts with similar meaning tend to have nearby vectors. A vector database stores these vectors and finds the closest ones to a question.

DocuMind uses `all-MiniLM-L6-v2` for embeddings and ChromaDB as the persistent vector store.

# %%
# A tiny, illustrative vector example. Real embeddings have many dimensions.
embeddings = {
    "cats are animals": [0.90, 0.10],
    "kittens are pets": [0.86, 0.14],
    "weather is rainy": [0.10, 0.90],
}

query = [0.88, 0.12]

def squared_distance(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right))

ranked = sorted(
    ((text, squared_distance(vector, query)) for text, vector in embeddings.items()),
    key=lambda item: item[1],
)
print(ranked)

# %% [markdown]
### Exercise

Add another sentence about animals and another sentence about weather. Which one ranks closest to the query?

### Checkpoint

- What is the difference between a keyword search and a semantic search?
- What is persisted in `chroma_db`?
- Why should the same embedding model be used for both documents and questions?

### Project connection

Read `get_vector_store()` and the `embeddings` definition in `backend/app/core/rag.py`.

---

# %% [markdown]
## Lesson 6: RAG: retrieve, then generate

### Goal

Understand the central DocuMind pipeline.

### Key idea

RAG means **Retrieval-Augmented Generation**:

1. Receive a question.
2. Retrieve relevant document chunks.
3. Put those chunks into a prompt as context.
4. Ask the language model to answer using that context.

This reduces the need for the model to guess from general knowledge. DocuMind's prompt explicitly says to answer only from the provided context and say it does not know when the context is insufficient.

# %%
def build_prompt(question, retrieved_chunks):
    context = "\n\n".join(retrieved_chunks)
    return (
        "Answer using only this context. If the answer is not present, say you do not know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )

print(build_prompt("What is RAG?", ["RAG retrieves context before generation."]))

# %% [markdown]
### Exercise

Give the prompt a question whose answer is absent from the context. Explain why the safest answer is “I do not know.”

### Checkpoint

- Which component retrieves chunks?
- Which component generates the final answer?
- What could happen if the prompt did not constrain the model to the context?

### Project connection

Follow `get_rag_chain()` in `backend/app/core/rag.py`. Identify:

- `create_history_aware_retriever`
- `create_stuff_documents_chain`
- `create_retrieval_chain`
- `RunnableWithMessageHistory`

---

# %% [markdown]
## Lesson 7: Chat history and sessions

### Goal

Understand how a follow-up question can refer to an earlier message.

### Key idea

A session ID identifies one conversation. The backend keeps a separate `ChatMessageHistory` for each session ID. The frontend stores the ID in browser `sessionStorage`.

For example:

1. User: “Who wrote the document?”
2. User: “What else did they publish?”

The second question needs the first exchange to resolve “they.”

# %%
sessions = {}

sessions["session-a"] = [
    {"role": "user", "content": "Who wrote the document?"},
    {"role": "assistant", "content": "The document was written by Alex."},
]

sessions.setdefault("session-b", []).append(
    {"role": "user", "content": "This is a separate conversation."}
)

print(sessions)

# %% [markdown]
### Exercise

Create two session IDs and prove that adding a message to one does not change the other.

### Checkpoint

- Why should two browser sessions not share the same conversation history?
- What happens when `DELETE /sessions/{session_id}` is called?
- Is the current session history persistent after the backend restarts?

### Project connection

Read `get_session_history()` in `backend/app/core/rag.py` and `createSessionId()` in `frontend/src/app/app.component.ts`.

---

# %% [markdown]
## Lesson 8: Angular components and services

### Goal

Understand how the frontend is organized.

### Key idea

An Angular component owns UI state and a template. A service owns reusable communication or application logic. DocuMind uses:

- `UploadComponent` for selecting and uploading PDFs.
- `ChatbotComponent` for displaying messages and sending questions.
- `DocumentService` for document HTTP requests.
- `ChatService` for chat HTTP requests.
- `AppComponent` for the active session ID.

# %%
frontend_parts = {
    "component": "owns UI state and user events",
    "service": "calls backend APIs",
    "observable": "represents a future asynchronous result",
}

for name, meaning in frontend_parts.items():
    print(f"{name}: {meaning}")

# %% [markdown]
### Exercise

For each action, name the likely Angular owner:

- List documents when the page opens.
- Validate that a selected file is a PDF.
- Send a chat message.
- Start a new conversation.

### Checkpoint

- Why use `FormData` for a PDF upload?
- Why does the chat service send `session_id` and `message` together?
- What UI states exist while a chat message is being sent?

### Project connection

Read:

- `frontend/src/app/services/document.service.ts`
- `frontend/src/app/services/chat.service.ts`
- `frontend/src/app/components/upload/upload.component.ts`
- `frontend/src/app/components/chatbot/chatbot.component.ts`

---

# %% [markdown]
## Lesson 9: Trace one request end to end

### Goal

Connect every layer into one mental model.

### Upload flow

1. User selects a PDF in Angular.
2. `UploadComponent` validates the file type.
3. `DocumentService` sends `FormData` to `POST /upload`.
4. FastAPI saves the file.
5. `PyPDFLoader` extracts page text.
6. The splitter creates overlapping chunks.
7. The embedding model converts chunks to vectors.
8. ChromaDB persists the vectors.
9. The backend returns the number of indexed chunks.
10. Angular updates the upload status.

### Chat flow

1. User enters a question in Angular.
2. `ChatService` sends `session_id` and `message` to `POST /chat`.
3. FastAPI finds or creates that session's history.
4. The history-aware retriever rewrites follow-up questions.
5. ChromaDB retrieves relevant chunks.
6. The QA prompt combines context, history, and the question.
7. xAI Grok generates an answer.
8. The backend returns `{ "answer": "..." }`.
9. Angular renders the assistant message.

### Checkpoint

Draw this flow on paper without looking at the list. Then explain where each of these lives: browser, FastAPI process, local disk, vector store, and external model API.

---

# %% [markdown]
## Lesson 10: Run DocuMind

### Prerequisites

- Python `3.14.7`, matching `backend/pyproject.toml`
- Node.js and npm
- An xAI API key

### 1. Configure the backend

From PowerShell:

```powershell
cd E:\Srikanth\Srikanth\Learning\Agentic_Learining\Project_1\DocuMind\backend
Copy-Item .env.example .env
notepad .env
```

Set:

```text
XAI_API_KEY=your-xai-api-key
```

### 2. Start the backend

```powershell
cd E:\Srikanth\Srikanth\Learning\Agentic_Learining\Project_1\DocuMind\backend
uv sync
uv run uvicorn app.main:app --reload
```

Check:

- Health: `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`

### 3. Start the frontend in a second terminal

```powershell
cd E:\Srikanth\Srikanth\Learning\Agentic_Learining\Project_1\DocuMind\frontend
npm install
npm start
```

Open `http://localhost:4200`.

### 4. Test the application

1. Upload a small PDF with text you understand.
2. Wait for the indexed chunk count.
3. Ask a question whose answer is clearly in the PDF.
4. Ask a follow-up question using “it,” “they,” or “that.”
5. Start a new session and observe that the visible chat resets.
6. Ask a question not covered by the PDF and inspect whether the answer respects the context rule.

---

# %% [markdown]
## Final project challenge

Choose one small improvement and trace it from UI to backend:

- Allow multiple PDF selection in the UI.
- Add a source filename to each answer.
- Add a configurable retrieval count (`k`).
- Add tests for the health and document endpoints.
- Replace in-memory chat history with a persistent store.
- Add a loading indicator for PDF indexing.
- Add a backend endpoint that reports the number of indexed chunks.

Before editing, write down:

1. Which file owns the behavior?
2. What is the API contract?
3. What can fail?
4. What test or manual check will prove the change works?

## Concepts you should now be able to explain

- Python modules and application entry points
- HTTP methods, routes, status codes, and JSON
- FastAPI request validation
- PDF extraction and overlapping chunks
- Embeddings and vector similarity
- Retrieval-Augmented Generation
- Prompt context and grounding
- Session-based chat history
- Angular components, services, and observables
- The complete upload and chat request flows
