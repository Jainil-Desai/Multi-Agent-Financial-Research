from chromadb.utils import embedding_functions
from app.config import settings

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.openai_api_key,
    model_name=settings.embedding_model,
)
