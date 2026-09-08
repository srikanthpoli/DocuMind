import logging
import os
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import AuthenticationError
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.rag import (
    UPLOAD_DIR,
    clear_chroma_database,
    clear_uploaded_documents,
    get_rag_chain,
    get_vector_store,
    session_store,
)

router = APIRouter(tags=["DocuMind"])
logger = logging.getLogger(__name__)
LOG_REQUEST_BODIES = os.getenv("LOG_REQUEST_BODIES", "false").lower() == "true"


# Confirm that the API server is running.
@router.get(
    "/health",
    summary="Check API health",
    description="Returns a successful response when the backend is running.",
)
def health_check() -> dict[str, str]:
    logger.debug("Health check requested")
    return {"status": "ok"}


@router.get(
    "/documents",
    summary="List uploaded PDF documents",
    description="Returns the PDF filenames currently stored in the uploaded_docs folder.",
)
def list_documents() -> dict[str, int | list[str]]:
    """Return the existing uploaded PDFs so clients can restore their document list."""
    files = sorted(
        path.name
        for path in UPLOAD_DIR.glob("*.pdf")
        if path.is_file()
    )
    logger.info("Listed uploaded documents: files=%d", len(files))
    return {"files": files, "count": len(files)}


# Save uploaded PDF files and index their chunks in ChromaDB.
@router.post(
    "/upload",
    summary="Upload and index PDF files",
    description=(
        "Uploads one or more PDF files, extracts their text, splits it into chunks, "
        "and stores the chunks in the ChromaDB vector store."
    ),
)
async def upload_files(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    started_at = perf_counter()
    logger.info("Upload started: %d file(s)", len(files))
    logger.info(
        "Upload POST fields: filenames=%s",
        [uploaded_file.filename for uploaded_file in files],
    )
    saved_files: list[str] = []
    for uploaded_file in files:
        # Keep only the filename so an upload cannot write outside the upload directory.
        filename = Path(uploaded_file.filename or "").name
        if not filename:
            continue
        if Path(filename).suffix.lower() != ".pdf":
            logger.warning("Rejected non-PDF upload: %s", filename)
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        destination = UPLOAD_DIR / filename
        destination.write_bytes(await uploaded_file.read())
        saved_files.append(filename)
        logger.info("Saved uploaded PDF: %s", filename)

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid files were uploaded.")

    # Load all PDF documents currently stored in the upload directory.
    loader = DirectoryLoader(
        str(UPLOAD_DIR),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=False,
    )
    documents = loader.load()
    if not documents:
        logger.warning("No PDF pages found in upload directory")
        raise HTTPException(status_code=400, detail="No PDF documents found to index.")

    # Split documents into overlapping chunks for more reliable retrieval.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    get_vector_store().add_documents(chunks)
    elapsed = perf_counter() - started_at
    logger.info(
        "Upload indexed: files=%d, pages=%d, chunks=%d, duration=%.2fs",
        len(saved_files),
        len(documents),
        len(chunks),
        elapsed,
    )

    return {
        "message": "Files uploaded and indexed successfully.",
        "files": saved_files,
        "chunks_indexed": len(chunks),
    }


# Answer a question using document retrieval and the session's chat history.
@router.post(
    "/chat",
    summary="Ask a question about uploaded PDFs",
    description=(
        "Uses the session ID to preserve conversation history and retrieves relevant "
        "PDF chunks before generating an answer with xAI Grok."
    ),
)
async def chat(session_id: str = Form(...), message: str = Form(...)) -> dict[str, str]:
    logger.info("Chat request started for session %s", session_id)
    if LOG_REQUEST_BODIES:
        logger.warning(
            "Chat POST body: session_id=%s message=%s",
            session_id,
            message,
        )
    else:
        logger.info(
            "Chat POST fields: session_id=%s message_length=%d",
            session_id,
            len(message),
        )
    if not message.strip():
        logger.warning("Rejected empty chat message for session %s", session_id)
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # The session ID lets RunnableWithMessageHistory preserve this conversation.
    try:
        result = get_rag_chain().invoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}},
        )
    except AuthenticationError:
        logger.error("xAI rejected the configured API key")
        raise HTTPException(
            status_code=502,
            detail="xAI rejected the API key. Replace XAI_API_KEY in backend/.env.",
        ) from None
    logger.info("Chat response generated for session %s", session_id)
    return {"answer": result["answer"]}


@router.delete(
    "/sessions/{session_id}",
    summary="Clear a chat session",
    description="Deletes the in-memory conversation history for the specified session.",
)
def clear_session(session_id: str) -> dict[str, str | bool]:
    """End a session by removing its conversation history."""
    if session_id in session_store:
        del session_store[session_id]
        logger.info("Cleared chat history for session %s", session_id)
        return {"session_id": session_id, "cleared": True}

    logger.info("Clear requested for unknown session %s", session_id)
    return {"session_id": session_id, "cleared": False}


@router.delete(
    "/storage/uploaded-docs",
    summary="Clear uploaded PDF files",
    description="Deletes every uploaded PDF from the local uploaded_docs folder.",
)
def clear_uploaded_docs() -> dict[str, int | str]:
    """Delete uploaded documents without changing ChromaDB or chat sessions."""
    deleted_files = clear_uploaded_documents()
    return {"message": "Uploaded documents cleared.", "deleted_files": deleted_files}


@router.delete(
    "/storage/chroma-db",
    summary="Clear ChromaDB",
    description="Deletes all persisted document vectors from the local chroma_db folder.",
)
def clear_chroma() -> dict[str, int | str]:
    """Delete indexed vectors without changing uploaded files or chat sessions."""
    deleted_files = clear_chroma_database()
    return {"message": "ChromaDB cleared.", "deleted_files": deleted_files}
