"""Actual end points will be defined here"""
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Query, HTTPException

from memsrv.core.memory_service import MemoryService
from memsrv.utils.logger import get_logger
from memsrv.models.request import MemoryCreateRequest, MemoryGenerateRequest, MemoryUpdateRequest
from memsrv.models.response import MemoriesActionResponse, MemoryResponse, GetMemoriesResponse

logger = get_logger(__name__)

def create_memory_router(memory_service: MemoryService):
    """Create a router for all memory service endpoints"""
    router = APIRouter(tags=["Memory"])

    @router.post("/memories/generate", response_model=MemoriesActionResponse)
    async def generate_memories(request: MemoryGenerateRequest):
        """
        Extracts facts from a conversation and saves them with metadata.
        """
        messages = request.messages
        metadata = request.metadata
        # We consolidate and store memories by default, pass False flag to skip consolidation
        response = await memory_service.add_memories_from_conversation(messages=messages,
                                                                       metadata=metadata)
        if response:
            return {
                "message": f"Successfully added {len(response)} memories.",
                "info": response
            }

        return {
            "message": "No new memories were generated from the conversation.",
            "info": []
        }

    @router.get("/memories", response_model=GetMemoriesResponse)
    async def retrieve_memories_by_metadata(
        user_id: Optional[str] = Query(None),
        session_id: Optional[str] = Query(None),
        app_id: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=50)
    ) -> GetMemoriesResponse:
        """Get memories by metadata filters only.
        e.g, /memories?user_id=u123&session_id=s123
        """
        filters: Dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if session_id:
            filters["session_id"] = session_id
        if app_id:
            filters["app_id"] = app_id

        # We can get the collection name from params as well, but for future

        memories = await memory_service.search_by_metadata(filters=filters,
                                                            limit=limit)
        return GetMemoriesResponse(memories=memories)

    @router.get("/memories/similar", response_model=GetMemoriesResponse)
    async def retrieve_memories_by_similarity(
        query: str,
        user_id: Optional[str] = Query(None),
        session_id: Optional[str] = Query(None),
        app_id: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=50)
    ) -> GetMemoriesResponse:
        """Get memories by metadata filters and similarity match.
        e.g, /memories?query=What is my name?&user_id=u123&session_id=s123
        """
        filters: Dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if session_id:
            filters["session_id"] = session_id
        if app_id:
            filters["app_id"] = app_id

        memories = await memory_service.search_similar_memories(query_texts=query,
                                                                filters=filters,
                                                                limit=limit)
        return GetMemoriesResponse(memories=memories)

    @router.post("/memories/create", response_model=MemoriesActionResponse)
    async def create_memories(request: MemoryCreateRequest):
        """Create a memory directly"""
        # We consolidate and store memories by default, pass False flag to skip consolidation
        response = await memory_service.create_raw_memories(data=request)

        return {
            "message": f"Successfully created {len(response)} memories.",
            "info": response
        }

    @router.post("/memories/get_by_ids", response_model=GetMemoriesResponse)
    async def get_memories_by_ids(ids: List[str]):
        """Get multiple memories by a list of IDs."""
        results = await memory_service.get_memories_by_ids(memory_ids=ids)
        memories = []
        for i in range(len(results.ids[0])):
            memories.append(
                MemoryResponse(
                    id=results.ids[0][i],
                    document=results.documents[0][i],
                    metadata=results.metadatas[0][i],
                    created_at=results.metadatas[0][i].get("created_at"),
                    updated_at=results.metadatas[0][i].get("updated_at")
                )
            )
        return GetMemoriesResponse(memories=memories)

    @router.put("/memories/update", response_model=MemoriesActionResponse)
    async def update_memories(items: List[MemoryUpdateRequest]):
        """Updates memories for given items"""
        response, error_status = await memory_service.update_raw_memories(update_items=items)

        message = f"Successfully updated {len(response)} memories."
        if error_status:
            message = "Partially updated memories. One or more updates failed."
        return {
            "message": message,
            "info": response
        }

    @router.delete("/memories/delete_by_id", response_model=MemoriesActionResponse)
    async def delete_memories_by_id(ids: List[str]):
        """Deletes memories from database for given ids"""
        response, error_status = await memory_service.delete_raw_memories_by_id(memory_ids=ids)

        message = f"Successfully deleted {len(response)} memories."
        if error_status:
            message = "Partially deleted memories. One or more deletes failed."
        return {
            "message": message,
            "info": response
        }

    return router
