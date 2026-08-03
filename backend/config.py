"""Central configuration for the SOWnia backend.

Uses pydantic-settings to load environment variables with validation
and type-safe defaults.
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google AI (Gemini)
    GOOGLE_API_KEY: str = ""

    # Hugging Face
    HF_TOKEN: str = ""
    HF_DATASET_REPO: str = "neelakantaganesh23/sownia-reviews"

    # LangSmith (Monitoring)
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "sownia"

    # App Config
    ENVIRONMENT: str = "development"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://your-vercel-app.vercel.app"

    # Backend URL
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MAX_FILE_SIZE_MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()
