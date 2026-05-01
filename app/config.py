from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    database_url: str = "sqlite+aiosqlite:///./data/finresearch.db"
    chroma_persist_dir: str = "./data/chroma"

    news_api_key: str = ""
    alpha_vantage_key: str = ""

    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 100

    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
