"""config file which selects llms, vector DBs"""
import os
from dotenv import load_dotenv

load_dotenv()

LLM_SERVICE = "gemini"
DB_SERVICE = "chroma"
# DB_SERVICE = "postgres"
EMBEDDING_SERVICE = "gemini"

if DB_SERVICE == "postgres":
    db_user = os.getenv("DATABASE_USER")
    db_pswd = os.getenv("DATABASE_PASSWORD")
    db_name = os.getenv("DATABASE_NAME")
    db_host = os.getenv("DATABASE_HOST", "127.0.0.1")
    db_port = os.getenv("DATABASE_PORT", "5432")
    CONNECTION_STRING = f"postgresql+pg8000://{db_user}:{db_pswd}@{db_host}:{db_port}/{db_name}"
else:
    CONNECTION_STRING = ""