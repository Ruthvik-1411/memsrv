"""Postgres with pgvector implementation"""
# pylint: disable=too-many-positional-arguments, too-many-locals, signature-differs, line-too-long
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import text, exc
from sqlalchemy.ext.asyncio import create_async_engine
from memsrv.utils.logger import get_logger
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.db.utils import serialize_items
from memsrv.models.response import QueryResponse

logger = get_logger(__name__)

# TODO: Refactor for SQL Injection vulnerability
class PostgresDBAdapter(VectorDBAdapter):
    """Implements the DB adapter for postgres database using sql alchemy"""
    def __init__(self, **kwargs):
        """Initializes the adapter using SQLalchemy connection string"""
        super().__init__(**kwargs)
        if not self.connection_string:
            raise ValueError("Connection string missing, either set it as env var or pass it.")

        logger.info(f"Using connection {self.connection_string} for postgres.")

        # The engine is created once and manages the connection pool.
        self.engine = create_async_engine(self.connection_string)

    async def setup_database(self):
        """Ensures the pgvector extension is enabled in the database and tables are created."""
        try:
            async with self.engine.begin() as conn:
                # Use .begin() to ensure the command is committed
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension is enabled.")

            logger.info("Creating table with the index")

            await self.create_collection(collection_name=self.collection_name)
            return self
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to connect to PostgreSQL or enable extension: {e}")
            raise ConnectionError("Could not set up the database connection.") from e

    def _format_filters(self, filters: Dict[str, Any] = None ) -> str:
        """Formats filter dict to sql where statements"""
        if filters:
            where_clauses = [f"{key} = :{key}" for key in filters]
            where_sql = " WHERE " + " AND ".join(where_clauses)

            return where_sql
        return ""

    def _parse_row(self, row) -> dict:
        """Helper to parse a single SQLAlchemy row into a dict with ISO-formatted datetimes."""
        return {
            "id": row['id'],
            "document": row['document'],
            "metadata": {
                "user_id": row['user_id'],
                "app_id": row['app_id'],
                "session_id": row['session_id'],
                "agent_name": row['agent_name'],
                "event_timestamp": row['event_timestamp'].isoformat(),
                "created_at": row['created_at'].isoformat(),
                "updated_at": row['updated_at'].isoformat(),
            },
            "distance": row.get("similarity", None)
        }

    # TODO: Use metadata and config when setting postgres index/db
    async def create_collection(self, collection_name, metadata=None, config=None):
        """
        Creates a new table for memories and an IVFFlat index for fast vector search.
        This method is idempotent and uses a transaction.
        """
        # TODO: for postgres get the vector size, idx_name and column names from config/metadata
        vector_size = self.embedding_dim
        index_name = f"{collection_name}_embedding_idx"
        index_exists = False

        async with self.engine.begin() as conn:
            logger.info(f"Initializing collection '{collection_name}'...")
            # TODO: Table columns should be inferred from metadata datamodel
            await conn.execute(text(
                f"""
                CREATE TABLE IF NOT EXISTS {collection_name} (
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

            result = await conn.execute(text(
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
                conn = await self.engine.connect()
                await conn.execution_options(isolation_level="AUTOCOMMIT")

                try:

                    logger.info(f"Creating index '{index_name}' on {collection_name}.embedding... This may take a moment.")
                    await conn.execute(text(
                        f"""
                        CREATE INDEX CONCURRENTLY {index_name} ON {collection_name}
                        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                        """
                    ))
                finally:
                    await conn.close()
                logger.info(f"Index '{index_name}' created successfully.")
                return True
            except exc.DBAPIError as e:
                # Catch a potential race condition where another process creates the index
                # after our check but before this command runs.
                if "already exists" in str(e).lower():
                    logger.warning(f"Index '{index_name}' was created by another process. Continuing.")
                else:
                    raise ValueError(e) from e

    async def add(self, items):

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
                "event_timestamp": datetime.fromisoformat(serialized_items["metadatas"][i]["event_timestamp"]),
                "created_at": datetime.fromisoformat(serialized_items["metadatas"][i]["created_at"]),
                "updated_at": datetime.fromisoformat(serialized_items["metadatas"][i]["updated_at"])
            }
            for i in range(len(items))
        ]
        # Adds a list of memory items using a single transactional bulk insert.
        # Use named parameters for clarity and safety
        insert_stmt = text(f"""
            INSERT INTO {self.collection_name} (
                id, document, embedding, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at
            ) VALUES (
                :id, :document, :embedding, :user_id, :app_id, :session_id, :agent_name, :event_timestamp, :created_at, :updated_at
            )
            ON CONFLICT (id) DO UPDATE SET
                document = EXCLUDED.document,
                embedding = EXCLUDED.embedding,
                updated_at = NOW();
        """)

        try:
            async with self.engine.begin() as conn:
                await conn.execute(insert_stmt, data_to_insert)

            logger.info(f"Successfully added/updated {len(items)} items in collection '{self.collection_name}'.")
            return [item.id for item in items]
        except exc.DBAPIError as e:
            if "datetime" in str(e).lower():
                logger.warning("Invalid datetime format supplied for one or more fields, please provide in isoformat.")
            else:
                logger.error(f"An unexpected database error occurred: {e}")
            raise ValueError(e) from e

    async def get_by_ids(self, ids):

        query = text(f"""SELECT id, document, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at
            FROM {self.collection_name}
            WHERE id = ANY(:ids);
        """)

        result_ids, documents, metadatas = [], [], []

        try:
            async with self.engine.connect() as conn:
                result_proxy = await conn.execute(query, {"ids": ids})
                for row in result_proxy.mappings():
                    parsed_row = self._parse_row(row)
                    result_ids.append(parsed_row["id"])
                    documents.append(parsed_row["document"])
                    metadatas.append(parsed_row["metadata"])

            return QueryResponse(
                ids=[result_ids],
                documents=[documents],
                metadatas=[metadatas]
            )
        except exc.DBAPIError as e:
            logger.error(f"Failed to get records by IDs: {e}")
            raise ValueError("Database error occurred") from e

    async def query_by_filter(self, filters, limit):

        params = {"limit": limit}
        params.update(filters)

        where_sql = self._format_filters(filters=filters)

        query_str = f"SELECT id, document, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at FROM {self.collection_name}"
        if where_sql:
            query_str += where_sql

        query_str += " ORDER BY updated_at DESC LIMIT :limit;"

        query = text(query_str)

        ids, documents, metadatas = [], [], []
        try:
            async with self.engine.connect() as conn:
                result_proxy = await conn.execute(query, params)
                # .mappings() allows dict-like access
                for row in result_proxy.mappings():
                    parsed_row = self._parse_row(row)
                    ids.append(parsed_row["id"])
                    documents.append(parsed_row["document"])
                    metadatas.append(parsed_row["metadata"])

            return QueryResponse(
                ids=[ids],
                documents=[documents],
                metadatas=[metadatas]
            )
        except exc.DBAPIError as e:
            logger.error(f"An unexpected database error occurred: {e}")
            raise ValueError(e) from e

    async def query_by_similarity(self,
                                  query_embeddings,
                                  query_texts=None,
                                  filters=None,
                                  top_k=20):

        where_sql = self._format_filters(filters=filters)

        # Similarity search, converting cosine distance to a similarity score.
        query_str = f"SELECT id, document, user_id, app_id, session_id, agent_name, event_timestamp, created_at, updated_at, 1 - (embedding <=> :embedding) AS similarity FROM {self.collection_name}"
        if where_sql:
            query_str += where_sql
        query_str += " ORDER BY similarity DESC LIMIT :top_k;"

        query = text(query_str)

        ids, documents, metadatas, distances = [], [], [], []
        try:
            # FIXME: Use a CTE and ROW_NUMBER() to perform all queries in a single round-trip
            # This would be much more efficient than looping and sending one query per embedding.
            async with self.engine.connect() as conn:
                for embedding in query_embeddings:

                    params = {"embedding": str(embedding), "top_k": top_k}
                    if filters:
                        params.update(filters)

                    result_proxy = await conn.execute(query, params)
                    # We return same format for API compatibility
                    result_ids = []
                    result_documents = []
                    result_metadatas = []
                    result_distances = []

                    for row in result_proxy.mappings():
                        parsed_row = self._parse_row(row)
                        result_ids.append(parsed_row["id"])
                        result_documents.append(parsed_row["document"])
                        result_metadatas.append(parsed_row["metadata"])
                        result_distances.append(parsed_row["distance"])

                    ids.append(result_ids)
                    documents.append(result_documents)
                    metadatas.append(result_metadatas)
                    distances.append(result_distances)

            return QueryResponse(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                distances=distances
            )
        except exc.DBAPIError as e:
            logger.error(f"An unexpected database error occurred: {e}")
            raise ValueError(e) from e

    async def update(self, items):

        data_to_update = [
            {
                "id": item.id,
                "document": item.document,
                "embedding": str(item.embedding),
                "updated_at": datetime.fromisoformat(item.updated_at),
            }
            for item in items
        ]

        update_stmt = text(f"""
            UPDATE {self.collection_name}
            SET
                document = :document,
                embedding = :embedding,
                updated_at = :updated_at
            WHERE id = :id;
        """)

        try:
            async with self.engine.begin() as conn:
                await conn.execute(update_stmt, data_to_update)

            logger.info(f"Successfully updated {len(items)} items in collection '{self.collection_name}'.")
            return [item.id for item in items]
        except exc.DBAPIError as e:
            logger.error(f"An unexpected database error occurred: {e}")
            raise ValueError(e) from e

    async def delete(self, fact_ids):

        delete_stmt = text(f"""
            DELETE FROM {self.collection_name}
            WHERE id = ANY(:ids);
        """)

        try:
            async with self.engine.begin() as conn:
                await conn.execute(delete_stmt, {"ids": fact_ids})

            logger.info(f"Successfully deleted {len(fact_ids)} items from collection '{self.collection_name}'.")
            return fact_ids
        except exc.DBAPIError as e:
            logger.error(f"An unexpected database error occurred: {e}")
            raise ValueError(e) from e
