"""Fast api entry point will be defined here"""
# pylint: disable=import-outside-toplevel
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from memsrv.api.routes import memory
from memsrv.utils.logger import get_logger
from memsrv.core.memory_service import MemoryService
from memsrv.utils.factory import LLMFactory, EmbeddingFactory, DBFactory

load_dotenv()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Handles startup and shutdown logic for FastAPI using lifespan"""
    logger.info("Starting Memory Service setup...")

    llm_instance = LLMFactory.create()
    embedder_instance = EmbeddingFactory.create()
    db_instance = await DBFactory.create()

    memory_service = MemoryService(llm=llm_instance,
                                   db_adapter=db_instance,
                                   embedder=embedder_instance)

    fastapi_app.include_router(memory.create_memory_router(memory_service), prefix="/api/v1")

    logger.info("Memory Service setup complete.")

    yield  # The will app will run from here

    logger.info("Shutting down Memory Service...")

app = FastAPI(
    title="Memory Service API",
    version="1.0.0",
    description="A self-hosted memory service for LLMs and AI agents",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
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
