"""Postgres with pgvector implementation"""
import os
from typing import List, Dict, Any, Optional
import logging

from sqlalchemy import create_engine, text, exc
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.models.memory import DBMemoryItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            where_sql = "WHERE " + " AND ".join(where_clauses)

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
                    fact_id TEXT PRIMARY KEY,
                    fact TEXT,
                    embedding VECTOR({vector_size}),
                    user_id TEXT,
                    app_id TEXT,
                    session_id TEXT,
                    agent_name TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
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
        """Adds a list of memory items using a single transactional bulk insert."""
        if not items:
            return

        self._ensure_collection_exists(collection_name)
        
        # Prepare data for bulk insert
        data_to_insert = [
            {
                "id": item.id,
                "document": item.document,
                "embedding": str(item.embedding),
                "user_id": item.metadata.user_id,
                "app_id": item.metadata.app_id,
                "session_id": item.metadata.session_id,
                "agent_name": item.metadata.agent_name,
            }
            for item in items
        ]

        # Use named parameters for clarity and safety
        insert_stmt = text(f"""
            INSERT INTO {collection_name} (
                fact_id, fact, embedding, user_id, app_id, session_id, agent_name
            ) VALUES (
                :id, :document, :embedding, :user_id, :app_id, :session_id, :agent_name
            )
            ON CONFLICT (fact_id) DO UPDATE SET
                fact = EXCLUDED.fact,
                embedding = EXCLUDED.embedding;
        """)

        with self.engine.begin() as conn:
            conn.execute(insert_stmt, data_to_insert)
        
        logger.info(f"Successfully added/updated {len(items)} items in collection '{collection_name}'.")
        return [item.id for item in items]
    
    def update(self, collection_name, fact_id, items):
        raise ValueError("Update for postgres is still in progress")
    
    def delete(self, collection_name, fact_id):
        raise ValueError("Delete for postgres is still in progress")

    def query_by_filter(self, collection_name, filters, limit):
        """Queries memories from a collection using metadata filters."""
        params = {"limit": limit}
        params.update(filters)
        
        where_sql = self._format_filters(filters=filters)
        
        query_str = f"SELECT fact_id, fact, user_id, app_id, session_id, agent_name, created_at FROM {collection_name}"
        if where_sql:
            query_str += where_sql
        query_str += " ORDER BY created_at DESC LIMIT :limit;"
        
        query = text(query_str)
        
        results = {"ids": [], "documents": [], "metadatas": []}
        with self.engine.connect() as conn:
            result_proxy = conn.execute(query, params)
            # .mappings() allows dict-like access
            for row in result_proxy.mappings():
                results["ids"].append(row['fact_id'])
                results["documents"].append(row['fact'])
                results["metadatas"].append({
                    "user_id": row['user_id'], "app_id": row['app_id'], "session_id": row['session_id'],
                    "agent_name": row['agent_name'], "timestamp": row['created_at'].isoformat()
                })
        logger.info(results)
        return results

    def query_by_similarity(self, collection_name, query_embedding, query_text=None, filters=None, top_k=20):
        """Performs similarity search, converting cosine distance to a similarity score."""
        params = {"embedding": str(query_embedding), "top_k": top_k}
        params.update(filters)
        
        where_sql = self._format_filters(filters=filters)
        query_str = f"SELECT fact_id, fact, user_id, app_id, session_id, agent_name, created_at, 1 - (embedding <=> :embedding) AS similarity FROM {collection_name} "
        if where_sql:
            query_str += where_sql
        query_str += " ORDER BY similarity DESC LIMIT :top_k;"
        
        query = text(query_str)

        results = {"ids": [], "documents": [], "metadatas": [], "distances": []}
        with self.engine.connect() as conn:
            result_proxy = conn.execute(query, params)
            for row in result_proxy.mappings():
                results["ids"].append(row['fact_id'])
                results["documents"].append(row['fact'])
                results["metadatas"].append({
                    "user_id": row['user_id'], "app_id": row['app_id'], "session_id": row['session_id'],
                    "agent_name": row['agent_name'], "timestamp": row['created_at'].isoformat()
                })
                # We return similarity score but keep the key 'distances' for API compatibility
                results["distances"].append(row['similarity'])
        
        return results
