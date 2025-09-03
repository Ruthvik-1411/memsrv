"""Fast api entry point will be defined here"""
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from memsrv.api.routes import memory
from memsrv.utils.logger import get_logger
from memsrv.core.memory_service import MemoryService
from memsrv.llms.providers.gemini import GeminiModel
from memsrv.embeddings.providers.gemini import GeminiEmbedding
from memsrv.llms.base_config import BaseLLMConfig
from config import LLM_SERVICE, DB_SERVICE, EMBEDDING_SERVICE, CONNECTION_STRING

load_dotenv()
logger = get_logger(__name__)

def get_llm_instance():
    if LLM_SERVICE == "gemini":
        config = BaseLLMConfig(model_name="gemini-2.0-flash")
        return GeminiModel(config)
    raise ValueError(f"Unsupported LLM provider: {LLM_SERVICE}")

def get_db_instance():
    if DB_SERVICE == "chroma":
        from memsrv.db.adapters.chroma import ChromaDBAdapter
        return ChromaDBAdapter(persist_dir="./chroma_db")
    elif DB_SERVICE == "postgres":
        from memsrv.db.adapters.postgres import PostgresDBAdapter
        return PostgresDBAdapter(connection_string=CONNECTION_STRING)
    raise ValueError(f"Unsupported DB provider: {DB_SERVICE}")

def get_embedding_instance():
    if EMBEDDING_SERVICE == "gemini":
        return GeminiEmbedding(model_name="gemini-embedding-001")
    raise ValueError(f"Unsupported Embedding provider: {EMBEDDING_SERVICE}")

llm_instance = get_llm_instance()
db_instance = get_db_instance()
embedding_instance = get_embedding_instance()

memory_service_instance = MemoryService(
    llm=llm_instance,
    db_adapter=db_instance,
    embedder=embedding_instance
)

app = FastAPI(
    title="Memory Service API",
    version="1.0.0",
    description="A self-hosted memory service for LLMs and AI agents",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware for some fastapi endpoints"""
    start_time = time.perf_counter()

    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Client: {client_host}")

    response = await call_next(request)

    method = request.method
    route = request.scope.get("route")
    route_path = route.path if route else "unknown"

    logger.info(f"Received request: {method} {route_path}")

    process_time = time.perf_counter() - start_time
    
    logger.info(f"Request processed in {process_time:2f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

app.include_router(memory.create_memory_router(memory_service_instance), prefix="/api/v1")
