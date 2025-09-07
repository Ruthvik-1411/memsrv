"""Actual end points will be defined here"""
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Query, HTTPException

from memsrv.core.memory_service import MemoryService
from memsrv.utils.logger import get_logger
from memsrv.models.request import MemoryCreateRequest, MemoryGenerateRequest, MemoryUpdateRequest
from memsrv.models.response import MemoriesActionResponse, GetMemoriesResponse

logger = get_logger(__name__)

def create_memory_router(memory_service: MemoryService):
    """Create a router for all memory service endpoints"""
    router = APIRouter(tags=["Memory"])

    @router.post("/memories/generate", response_model=MemoriesActionResponse)
    async def generate_memories(request: MemoryGenerateRequest):
        """
        Extracts facts from a conversation and saves them with metadata.
        """
        try:
            messages = request.messages
            metadata = request.metadata
            # We consolidate and store memories by default, pass False flag to skip consolidation
            response = await memory_service.add_memories_from_conversation(messages, metadata)

            return {
                "message": f"Successfully added {len(response)} memories.",
                "info": response
            }
        except Exception as e:
            logger.exception(f"An error has occured when adding to memory: {str(e)}",
                             exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

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
        try:
            filters: Dict[str, Any] = {}
            if user_id:
                filters["user_id"] = user_id
            if session_id:
                filters["session_id"] = session_id
            if app_id:
                filters["app_id"] = app_id

            # We can get the collection name from params as well, but for future

            memories = await memory_service.search_by_metadata(filters=filters, limit=limit)
            return GetMemoriesResponse(memories=memories)
        except Exception as e:
            logger.exception(f"An error has occured when searching memory: {str(e)}",
                             exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

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
        try:
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
        except Exception as e:
            logger.exception(f"An error has occured when searching memory: {str(e)}",
                             exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.post("/memories/create", response_model=MemoriesActionResponse)
    async def create_memories(request: MemoryCreateRequest):
        """Create a memory directly"""
        try:
            # We consolidate and store memories by default, pass False flag to skip consolidation
            response = await memory_service.add_raw_memories(data=request)

            return {
                "message": f"Successfully created {len(response)} memories.",
                "info": response
            }
        except Exception as e:
            logger.exception(f"An error has occured when updating memory: {str(e)}",
                             exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.put("/memories/update", response_model=MemoriesActionResponse)
    async def update_memories(items: List[MemoryUpdateRequest]):
        """Updates memories for given items"""
        try:
            # TODO: Add check by id here before proceeding to update and extend the list
            response = await memory_service.update_memories(update_items=items)

            return {
                "message": f"Successfully updated {len(response)} memories.",
                "info": response
            }
        except Exception as e:
            logger.exception(f"An error has occured when updating memory: {str(e)}",
                             exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.delete("/memories/delete", response_model=MemoriesActionResponse)
    async def delete_memories(ids: List[str]):
        """Deletes memories from database for given ids"""
        try:
            # TODO: Add check by id here before proceeding to delete and extend the list
            response = await memory_service.delete_memories(memory_ids=ids)
            return {
                "message": f"Successfully deleted {len(response)} memories.",
                "info": response
            }
        except Exception as e:
            logger.exception(f"An error has occured when deleting memory: {str(e)}",
                             exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    return router
