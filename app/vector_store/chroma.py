import os
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

os.makedirs(settings.chroma_persist_dir, exist_ok=True)

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection(name: str, embedding_function=None) -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=embedding_function,
    )


# Named collections used across agents
FILINGS_COLLECTION = "sec_filings"
NEWS_COLLECTION = "news_articles"
