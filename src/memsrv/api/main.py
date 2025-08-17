"""Fast api entry point will be defined here"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from memsrv.api.routes import memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Memory Service API",
    version="1.0.0",
    description="A self-hosted memory service for LLMs and AI agents"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory.router, prefix="/api/v1")

# uvicorn memsrv.api.main:app --reload --host 0.0.0.0 --port 8090