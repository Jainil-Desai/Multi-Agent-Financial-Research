import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.vector_store.chroma import get_collection, FILINGS_COLLECTION, NEWS_COLLECTION
from app.rag.embeddings import openai_ef
from app.config import settings

log = logging.getLogger("finresearch.retriever")


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def store_filing(ticker: str, accession: str, form_type: str, text: str) -> int:
    chunks = _splitter().split_text(text)
    if not chunks:
        return 0
    collection = get_collection(FILINGS_COLLECTION, embedding_function=openai_ef)
    ids = [f"{ticker}_{accession}_{i}" for i in range(len(chunks))]
    metadatas = [{"ticker": ticker, "accession": accession, "form_type": form_type, "chunk": i} for i in range(len(chunks))]
    collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
    log.info(f"[Retriever] Stored {len(chunks)} filing chunks for {ticker} {form_type}")
    return len(chunks)


def store_news(ticker: str, articles: list[dict]) -> int:
    if not articles:
        return 0
    texts = [f"{a['title']}. {a.get('content', '')}" for a in articles]
    texts = [t for t in texts if t.strip()]
    collection = get_collection(NEWS_COLLECTION, embedding_function=openai_ef)
    ids = [f"{ticker}_news_{a['id']}" for a in articles]
    metadatas = [{"ticker": ticker, "source": a.get("source", ""), "published_at": a.get("published_at", "")} for a in articles]
    collection.upsert(documents=texts, ids=ids, metadatas=metadatas)
    log.info(f"[Retriever] Stored {len(texts)} news chunks for {ticker}")
    return len(texts)


def query_filings(ticker: str, query: str, n_results: int = 5) -> list[str]:
    collection = get_collection(FILINGS_COLLECTION, embedding_function=openai_ef)
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"ticker": ticker},
    )
    return results["documents"][0] if results["documents"] else []


def query_news(ticker: str, query: str, n_results: int = 5) -> list[str]:
    collection = get_collection(NEWS_COLLECTION, embedding_function=openai_ef)
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"ticker": ticker},
    )
    return results["documents"][0] if results["documents"] else []
