"""config file which selects llms, vector DBs"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class MemoryConfig(BaseSettings):
    """Simple config class for all services used"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM setup
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-2.0-flash"

    GOOGLE_API_KEY: Optional[str]

    # Embedding setup
    EMBEDDING_PROVIDER: str = "google"
    EMBEDDING_MODEL: str = "gemini-embedding-001"

    # DB setup
    DB_PROVIDER: str = "chroma"
    DB_COLLECTION_NAME: str = "memories"

    # Chroma
    DB_PERSIST_DIR: Optional[str] = ""

    # Postgres
    DATABASE_USER: Optional[str]
    DATABASE_PASSWORD: Optional[str]
    DATABASE_NAME: Optional[str]
    DATABASE_HOST: Optional[str] = "127.0.0.1"
    DATABASE_PORT: Optional[str] = "5432"

    @property
    def llm_api_key(self) -> str:
        """Reads the api key based on provider"""
        if self.LLM_PROVIDER == "gemini":
            return self.GOOGLE_API_KEY
        return None

    @property
    def connection_string(self) -> Optional[str]:
        """Constructs the connection string for postgres"""
        if self.DB_PROVIDER == "postgres":
            return (
                f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
                f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            )
        return None

    @property
    def db_config(self) -> dict:
        """Prepares the config for db"""      
        return {
            "connection_string": self.connection_string,
            "persist_dir": self.DB_PERSIST_DIR,
            "collection_name": self.DB_COLLECTION_NAME
        }

memory_config = MemoryConfig()
