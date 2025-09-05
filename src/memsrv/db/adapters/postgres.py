"""Postgres with pgvector implementation"""
import os
from typing import Dict, Any, Optional

from sqlalchemy import create_engine, text, exc
from memsrv.utils.logger import get_logger
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.db.utils import serialize_items

logger = get_logger(__name__)

# TODO: Refactor for SQL Injection vulnerability
class PostgresDBAdapter(VectorDBAdapter):
    """Implements the DB adapter for postgres database using sql alchemy"""
    def __init__(self, connection_string: Optional[str] = None):
        """Initializes the adapter using SQLalchemy connection string"""
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("Connection string missing, either set it as env var or pass it.")
    
        # The engine is created once and manages the connection pool.
        self.engine = create_engine(self.connection_string)
        self._collections_cache = set()
        self._setup_database()
    
    def _setup_database(self):
        """Ensures the pgvector extension is enabled in the database."""
        try:
            with self.engine.begin() as conn:
                # Use .begin() to ensure the command is committed
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension is enabled.")
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to connect to PostgreSQL or enable extension: {e}")
            raise ConnectionError("Could not set up the database connection.") from e
    
    def _ensure_collection_exists(self, name: str):
        """Checks if a collection (table) has been initialized, and creates it if not."""
        if name not in self._collections_cache:
            self.create_collection(name)
            self._collections_cache.add(name)
    
    def _format_filters(self, filters: Dict[str, Any] = None ) -> str:
        """Formats filter dict to sql where statements"""
        if filters:
            where_clauses = [f"{key} = :{key}" for key in filters]
            where_sql = " WHERE " + " AND ".join(where_clauses)

            return where_sql
        return ""

    def create_collection(self, name, metadata=None):
        """
        Creates a new table for memories and an IVFFlat index for fast vector search.
        This method is idempotent and uses a transaction.
        """
        vector_size = 768
        index_name = f"{name}_embedding_idx"
        index_exists = False
        
        with self.engine.begin() as conn:
            logger.info(f"Initializing collection '{name}'...")
            # TODO: Table columns should be inferred from metadata datamodel
            conn.execute(text(
                f"""
                CREATE TABLE IF NOT EXISTS {name} (
                    id TEXT PRIMARY KEY,
                    document TEXT,
                    embedding VECTOR({vector_size}),
                    user_id TEXT,
                    app_id TEXT,
                    session_id TEXT,
                    agent_name TEXT,
                    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            ))

            result = conn.execute(text(
                f"""
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = '{index_name}' AND n.nspname = 'public';
                """
            ))
            if result.fetchone():
                index_exists = True
                logger.info(f"Index '{index_name}' already exists.")
        if not index_exists:
            try:
                # Use a connection with autocommit enabled for this specific command.
                with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                    logger.info(f"Creating index '{index_name}' on {name}.embedding... This may take a moment.")
                    conn.execute(text(
                        f"""
                        CREATE INDEX CONCURRENTLY {index_name} ON {name}
                        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                        """
                    ))
                logger.info(f"Index '{index_name}' created successfully.")
            except exc.DBAPIError as e:
                # Catch a potential race condition where another process creates the index
                # after our check but before this command runs.
                if "already exists" in str(e).lower():
                        logger.warning(f"Index '{index_name}' was created by another process. Continuing.")
                else:
                    raise ValueError(e)

    def add(self, collection_name, items):

        self._ensure_collection_exists(collection_name)
        serialized_items = serialize_items(items)
        
        # Prepare data for bulk insert
        data_to_insert = [
            {
                "id": serialized_items["ids"][i],
                "document": serialized_items["documents"][i],
                "embedding": str(serialized_items["embeddings"][i]),
                "user_id": serialized_items["metadatas"][i]["user_id"],
                "app_id": serialized_items["metadatas"][i]["app_id"],
                "session_id": serialized_items["metadatas"][i]["session_id"],
                "agent_name": serialized_items["metadatas"][i]["agent_name"],
                "event_timestamp": serialized_items["metadatas"][i]["event_timestamp"],
                "created_at": serialized_items["metadatas"][i]["created_at"],
                "updated_at": serialized_items["metadatas"][i]["updated_at"]
            }
            for i in range(len(items))
        ]
        # Adds a list of memory items using a single transactional bulk insert.
        # Use named parameters for clarity and safety
        insert_stmt = text(f"""
            INSERT INTO {collection_name} (
                id, document, embedding, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at
            ) VALUES (
                :id, :document, :embedding, :user_id, :app_id, :session_id, :agent_name, :event_timestamp, :created_at, :updated_at
            )
            ON CONFLICT (id) DO UPDATE SET
                document = EXCLUDED.document,
                embedding = EXCLUDED.embedding,
                updated_at = NOW();
        """)

        with self.engine.begin() as conn:
            conn.execute(insert_stmt, data_to_insert)
        
        logger.info(f"Successfully added/updated {len(items)} items in collection '{collection_name}'.")
        return [item.id for item in items]
    
    def get_by_ids(self, collection_name, ids):
        pass
        # return super().get_by_id(collection_name, id)

    def query_by_filter(self, collection_name, filters, limit):
        
        params = {"limit": limit}
        params.update(filters)
        
        where_sql = self._format_filters(filters=filters)
        
        query_str = f"SELECT id, document, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at FROM {collection_name}"
        if where_sql:
            query_str += where_sql

        query_str += " ORDER BY updated_at DESC LIMIT :limit;"
        
        query = text(query_str)
        
        results = {
            "ids": [],
            "documents": [],
            "metadatas": []
        }
        with self.engine.connect() as conn:
            result_proxy = conn.execute(query, params)
            # .mappings() allows dict-like access
            for row in result_proxy.mappings():
                results["ids"].append(row['id'])
                results["documents"].append(row['document'])
                results["metadatas"].append({
                    "user_id": row['user_id'],
                    "app_id": row['app_id'],
                    "session_id": row['session_id'],
                    "agent_name": row['agent_name'],
                    "event_timestamp": row["event_timestamp"].isoformat(),
                    "created_at": row['created_at'].isoformat(),
                    "updated_at": row['updated_at'].isoformat()
                })
        logger.info(results)
        return results

    def query_by_similarity(self, collection_name, query_embeddings, query_texts=None, filters=None, top_k=20):
        
        where_sql = self._format_filters(filters=filters)

        # Similarity search, converting cosine distance to a similarity score.
        query_str = f"SELECT id, document, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at, 1 - (embedding <=> :embedding) AS similarity FROM {collection_name}"
        if where_sql:
            query_str += where_sql
        query_str += " ORDER BY similarity DESC LIMIT :top_k;"
        
        query = text(query_str)

        results = {"ids": [], "documents": [], "metadatas": [], "distances": []}
        with self.engine.connect() as conn:
            for embedding in query_embeddings:
                
                params = {"embedding": str(embedding), "top_k": top_k}
                if filters:
                    params.update(filters)
                
                result_proxy = conn.execute(query, params)
                # We return same format for API compatibility
                ids = []
                documents = []
                metadatas = []
                distances = []
                
                for row in result_proxy.mappings():
                    ids.append(row['id'])
                    documents.append(row['document'])
                    metadatas.append({
                        "user_id": row['user_id'],
                        "app_id": row['app_id'],
                        "session_id": row['session_id'],
                        "agent_name": row['agent_name'],
                        "event_timestamp": row["event_timestamp"].isoformat(),
                        "created_at": row['created_at'].isoformat(),
                        "updated_at": row['updated_at'].isoformat()
                    })
                    distances.append(row['similarity'])
                
                results["ids"].append(ids)
                results["documents"].append(documents)
                results["metadatas"].append(metadatas)
                results["distances"].append(distances)
        
        return results

    def update(self, collection_name, items):
        
        self._ensure_collection_exists(collection_name)
        
        data_to_update = [
            {
                "id": item.id,
                "document": item.document,
                "embedding": str(item.embedding),
                "updated_at": item.updated_at,
            }
            for item in items
        ]

        update_stmt = text(f"""
            UPDATE {collection_name}
            SET
                document = :document,
                embedding = :embedding,
                updated_at = :updated_at
            WHERE id = :id;
        """)

        with self.engine.begin() as conn:
            conn.execute(update_stmt, data_to_update)

        logger.info(f"Successfully updated {len(items)} items in collection '{collection_name}'.")
        return [item.id for item in items]
    
    def delete(self, collection_name, fact_ids):

        self._ensure_collection_exists(collection_name)

        delete_stmt = text(f"""
            DELETE FROM {collection_name}
            WHERE id = ANY(:ids);
        """)

        with self.engine.begin() as conn:
            conn.execute(delete_stmt, {"ids": fact_ids})

        logger.info(f"Successfully deleted {len(fact_ids)} items from collection '{collection_name}'.")
        return fact_ids
