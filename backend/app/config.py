"""Application configuration loaded from environment variables / .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent  # project root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Multimodal RAG QA"
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Storage
    upload_dir: Path = BASE_DIR / "data" / "uploads"
    extracted_images_dir: Path = BASE_DIR / "data" / "extracted_images"
    max_upload_mb: int = 50
    allowed_pdf_max_pages: int = 500

    # Qdrant
    qdrant_mode: str = "local"  # local | remote
    qdrant_path: Path = BASE_DIR / "data" / "qdrant_storage"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection_text: str = "mm_rag_text"
    qdrant_collection_images: str = "mm_rag_images"

    # Embedding models
    text_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    clip_model: str = "sentence-transformers/clip-ViT-B-32"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 16

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 80

    # Retrieval
    top_k_text: int = 5
    top_k_images: int = 5
    text_retrieval_weight: float = 0.6
    image_retrieval_weight: float = 0.4
    score_threshold: float = 0.0

    # LLM
    llm_provider: str = "ollama"  # ollama | openai_compatible
    llm_model: str = "llava:7b"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    llm_max_images: int = 3  # vision models often cap images/request (Groq qwen: 3)
    llm_timeout: int = 120
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str = ""
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "meta-llama/llama-3.2-11b-vision-preview"

    # Chat
    max_history_messages: int = 10

    @field_validator("upload_dir", "extracted_images_dir", "qdrant_path", mode="before")
    @classmethod
    def _expand_path(cls, v: str | Path) -> Path:
        p = Path(v).expanduser()
        if not p.is_absolute():
            p = (BASE_DIR / p).resolve()
        return p

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        for d in (self.upload_dir, self.extracted_images_dir):
            d.mkdir(parents=True, exist_ok=True)
        if self.qdrant_mode == "local":
            Path(self.qdrant_path).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
