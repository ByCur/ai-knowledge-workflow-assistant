from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://aiassistant:"
        "aiassistant_password@localhost:5433/aiassistant"
    )

    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    embedding_model: str = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
    )
    ai_provider: str = "ollama"
    
    gemini_api_key: str = ""

    gemini_model: str = (
    "gemini-3.5-flash-lite"
    )

    ollama_url: str = ("http://host.docker.internal:11434")
    ollama_model: str = "llama3.2:3b"


settings = Settings()