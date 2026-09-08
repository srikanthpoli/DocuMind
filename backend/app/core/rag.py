import os  # Reads environment variables such as XAI_API_KEY.
import logging
import shutil
from pathlib import Path  # Handles filesystem paths safely on Windows and other systems.

from fastapi import HTTPException  # Converts configuration failures into HTTP 500 responses.
from dotenv import load_dotenv  # Loads values from the local .env file.
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory  # Stores messages for one chat session.
from langchain_community.embeddings import HuggingFaceEmbeddings  # Converts text into numerical vectors.
from langchain_community.vectorstores import Chroma  # Stores and searches document vectors.
from langchain_core.chat_history import BaseChatMessageHistory  # Common type for chat-history objects.
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # Builds prompts with history slots.
from langchain_core.runnables.history import RunnableWithMessageHistory  # Adds history support to a chain.
from langchain_xai import ChatXAI  # Connects LangChain to xAI's Grok language model.

logger = logging.getLogger(__name__)

# Read XAI_API_KEY from backend/.env regardless of the terminal's current directory.
# This runs during module import, before the RAG chain needs the key.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)
logger.info("Environment configuration loaded")

# Store uploaded PDFs and the persistent ChromaDB data locally.
# These relative paths are resolved from the directory where the server is started.
UPLOAD_DIR = Path("./uploaded_docs")
CHROMA_DIR = Path("./chroma_db")
# Create both directories if they do not exist yet.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
logger.info("Document directories ready: uploads=%s, chroma=%s", UPLOAD_DIR, CHROMA_DIR)

# Use the sentence-transformer model to convert document text and questions into vectors.
# Similar meanings produce nearby vectors, which allows semantic document search.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
logger.info("Embedding model initialized: all-MiniLM-L6-v2")
# Start these resources lazily and reuse them across requests.
# The vector store is persistent on disk; the chain and session history are in memory.
vector_store: Chroma | None = None
rag_chain: RunnableWithMessageHistory | None = None
session_store: dict[str, BaseChatMessageHistory] = {}


# Open the persistent vector store when it is first needed.
def get_vector_store() -> Chroma:
    """Return the shared ChromaDB instance, creating it on the first request."""
    global vector_store
    if vector_store is None:
        logger.info("Opening ChromaDB vector store at %s", CHROMA_DIR)
        # Reopen existing vectors from CHROMA_DIR or create an empty collection.
        vector_store = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings,
        )
        logger.info("ChromaDB vector store ready")
    return vector_store


def clear_uploaded_documents() -> int:
    """Delete all uploaded files and recreate the upload directory."""
    deleted_files = sum(1 for path in UPLOAD_DIR.rglob("*") if path.is_file())
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Cleared uploaded documents: files=%d", deleted_files)
    return deleted_files


def clear_chroma_database() -> int:
    """Delete all persisted ChromaDB files and reset the cached store."""
    global vector_store
    deleted_files = sum(1 for path in CHROMA_DIR.rglob("*") if path.is_file())
    vector_store = None
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Cleared ChromaDB: files=%d", deleted_files)
    return deleted_files


# Return the existing conversation history or create a new session history.
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Return the conversation history belonging to one client session."""
    if session_id not in session_store:
        # A new session starts with no previous user or assistant messages.
        session_store[session_id] = ChatMessageHistory()
        logger.info("Created chat history for session %s", session_id)
    return session_store[session_id]


# Build the conversational retrieval chain once and reuse it for later chats.
def get_rag_chain() -> RunnableWithMessageHistory:
    """Create and cache the complete conversational retrieval pipeline."""
    global rag_chain
    if rag_chain is not None:
        # Avoid rebuilding the model, retriever, and prompts for every chat request.
        logger.debug("Reusing cached RAG chain")
        return rag_chain

    # ChatXAI needs this key to authenticate requests to the xAI API.
    xai_api_key = os.environ.get("XAI_API_KEY")
    if not xai_api_key:
        logger.error("XAI_API_KEY is missing; cannot create RAG chain")
        raise HTTPException(
            status_code=500,
            detail="XAI_API_KEY is not configured.",
        )

    # The LLM generates question rewrites and final answers.
    llm = ChatXAI(
        model="grok-3-mini",
        xai_api_key=xai_api_key,
    )
    logger.info("xAI chat model initialized: grok-3-mini")

    # This prompt turns a follow-up such as "What about its author?"
    # into a standalone question using the previous conversation.
    contextualize_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Rewrite the latest user question as a standalone question using the chat history."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    # The retriever searches ChromaDB using the rewritten standalone question.
    history_aware_retriever = create_history_aware_retriever(
        llm,
        get_vector_store().as_retriever(),
        contextualize_prompt,
    )

    # This prompt tells the LLM to answer from retrieved context instead of guessing.
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer the question using only the provided context. "
                "If the answer is not in the context, say you do not know.\n\n{context}",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    # Put all retrieved document chunks into the {context} prompt variable.
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    # Connect question rewriting, retrieval, and document answering in sequence.
    retrieval_chain = create_retrieval_chain(
        history_aware_retriever,
        question_answer_chain,
    )
    # Wrap the chain so each session gets its own conversation history.
    rag_chain = RunnableWithMessageHistory(
        retrieval_chain,
        get_session_history,
        input_messages_key="input",  # The current user question.
        history_messages_key="chat_history",  # The prompt history placeholder name.
        output_messages_key="answer",  # The answer returned by the retrieval chain.
    )
    logger.info("Conversational RAG chain ready")
    return rag_chain
