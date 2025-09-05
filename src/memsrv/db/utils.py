"""Common utils for db adapters"""
from typing import List, Dict, Any
from memsrv.models.memory import MemoryInDB

def serialize_items(items: List[MemoryInDB], include_system_fields: bool = True) -> Dict[str, Any]:
    """Converts a list of MemoryInDB into structured arrays for DB adapters."""
    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for item in items:
        ids.append(item.id)
        documents.append(item.document)
        embeddings.append(item.embedding)

        metadata_dict = item.metadata.model_dump()
        if include_system_fields:
            metadata_dict["created_at"] = item.created_at
            metadata_dict["updated_at"] = item.updated_at

        metadatas.append(metadata_dict)

    return {
        "ids": ids,
        "documents": documents,
        "embeddings": embeddings,
        "metadatas": metadatas,
    }
