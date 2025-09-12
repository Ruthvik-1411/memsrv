"""config file which selects llms, vector DBs"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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
    def LLM_API_KEY(self) -> str:
        """Reads the api key based on provider"""
        if self.LLM_PROVIDER == "gemini":
            return self.GOOGLE_API_KEY
        else:
            return None
    
    @property
    def CONNECTION_STRING(self) -> Optional[str]:
        """Constructs the connection string for postgres"""
        if self.DB_PROVIDER == "postgres":
            return (
                f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
                f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            )
        return None

    @property
    def DB_CONFIG(self) -> dict:
        """Prepares the config for db"""      
        return {
            "connection_string": self.CONNECTION_STRING,
            "persist_dir": self.DB_PERSIST_DIR,
            "collection_name": self.DB_COLLECTION_NAME
        }

memory_config = MemoryConfig()
