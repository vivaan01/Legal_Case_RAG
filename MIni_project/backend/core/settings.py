from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	app_name: str = Field("Legal Case RAG (Adaptive + Tools) - Ollama", alias="APP_NAME")
	ollama_model: str = Field("mistral:7b", alias="OLLAMA_MODEL")
	ollama_embed_model: str = Field("nomic-embed-text", alias="OLLAMA_EMBED_MODEL")
	ollama_base_url: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")

	data_dir: Path = Field(Path("data"), alias="DATA_DIR")
	redis_host: str = Field("localhost", alias="REDIS_HOST")
	redis_port: int = Field(6379, alias="REDIS_PORT")

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"
		arbitrary_types_allowed = True


@lru_cache
def get_settings() -> Settings:
	settings = Settings()
	settings.data_dir.mkdir(parents=True, exist_ok=True)
	return settings


