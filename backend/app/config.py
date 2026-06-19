from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase
    supabase_url: str
    supabase_publishable_key: str
    supabase_service_key: str

    # Database
    database_url: str
    database_url_direct: str

    # LLM / Embedding
    openai_api_key: str
    anthropic_api_key: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dims: int = 1536

    # Paths
    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data"
    scripts_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "scripts"
    outputs_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "outputs"
    templates_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "templates"
    converted_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "converted"

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177"]


settings = Settings()
