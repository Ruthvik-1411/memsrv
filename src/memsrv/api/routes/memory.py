"""Actual end points will be defined here"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Optional, Any
import logging
from memsrv.models.memory import MemoryItem, GetMemoriesResponseModel
from memsrv.core.service import MemoryService
from memsrv.models.memory import MemoryMetadata
from memsrv.db.adapters.chroma import ChromaDBAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Memory"])

# These will usually be initialized when the service starts
# We will keep using gemini and chroma for now, but they can be configured
memory_service = MemoryService(model_name="gemini-2.0-flash")
db = ChromaDBAdapter()

@router.post("/memories/generate")
def add_memory(messages: List[dict], metadata: MemoryMetadata):
    """
    Extracts facts from a conversation and saves them with metadata.
    """
    try:
        facts = memory_service.add_facts_from_conversation(messages, metadata)
        return {
            "message": f"Successfully added {len(facts)} memories to database.",
            "memories": facts
        }
    except Exception as e:
        logger.info(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories")
def retreive_by_metadata(
    user_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    app_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=50)
) -> GetMemoriesResponseModel:
    """Get memories by metadata filters only.
    Ex: /memories?user_id=u123&session_id=s123
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

        results = db.query_items(collection_name="memories", filters=filters, limit=limit)
        memories = []
        for i in range(len(results.get("ids", []))):
            memories.append(
                MemoryItem(
                    fact_id=results["ids"][i],
                    fact=results["documents"][i],
                    metadata=results["metadatas"][i]
                )
            )
        return GetMemoriesResponseModel(facts=memories)
    except Exception as e:
        logger.info(str(e))
        raise HTTPException(status_code=500, detail=str(e))
