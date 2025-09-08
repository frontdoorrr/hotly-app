"""
Elasticsearch connection and client management.

Provides connection pooling, health checks, and configuration for
search functionality across the application.
"""

import logging
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch, ConnectionError, NotFoundError
from elasticsearch.exceptions import ElasticsearchException

from app.core.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchManager:
    """Manages Elasticsearch connections and operations."""

    def __init__(self) -> None:
        """Initialize Elasticsearch manager."""
        self.client: Optional[AsyncElasticsearch] = None
        self._connection_params = self._build_connection_params()

    def _build_connection_params(self) -> Dict[str, Any]:
        """Build Elasticsearch connection parameters."""
        params = {
            "hosts": [
                {
                    "host": settings.ELASTICSEARCH_HOST,
                    "port": settings.ELASTICSEARCH_PORT,
                    "scheme": settings.ELASTICSEARCH_SCHEME,
                }
            ],
            "verify_certs": False if settings.ENVIRONMENT == "development" else True,
            "ssl_show_warn": False if settings.ENVIRONMENT == "development" else True,
            "retry_on_timeout": True,
            "max_retries": 3,
            "timeout": 30,
        }

        # Add authentication if provided
        if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
            params["http_auth"] = (
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD,
            )

        # Add CA certificates if provided
        if settings.ELASTICSEARCH_CA_CERTS:
            params["ca_certs"] = settings.ELASTICSEARCH_CA_CERTS
            params["verify_certs"] = True

        return params

    async def connect(self) -> None:
        """Establish connection to Elasticsearch."""
        try:
            self.client = AsyncElasticsearch(**self._connection_params)

            # Test connection
            await self.health_check()
            logger.info("Successfully connected to Elasticsearch")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise ConnectionError(f"Elasticsearch connection failed: {e}")

    async def disconnect(self) -> None:
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Elasticsearch")

    async def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        try:
            health = await self.client.cluster.health()
            return {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
                "active_primary_shards": health["active_primary_shards"],
                "active_shards": health["active_shards"],
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            raise

    async def create_index(
        self,
        index_name: str,
        mapping: Dict[str, Any],
        settings_dict: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create an index with mapping and settings."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        try:
            # Check if index already exists
            exists = await self.client.indices.exists(index=full_index_name)
            if exists:
                logger.info(f"Index {full_index_name} already exists")
                return True

            # Create index
            body = {"mappings": mapping}
            if settings_dict:
                body["settings"] = settings_dict

            await self.client.indices.create(index=full_index_name, body=body)
            logger.info(f"Created index: {full_index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index {full_index_name}: {e}")
            raise ElasticsearchException(f"Index creation failed: {e}")

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        try:
            await self.client.indices.delete(index=full_index_name)
            logger.info(f"Deleted index: {full_index_name}")
            return True
        except NotFoundError:
            logger.warning(f"Index {full_index_name} not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Failed to delete index {full_index_name}: {e}")
            raise

    async def index_document(
        self,
        index_name: str,
        document: Dict[str, Any],
        doc_id: Optional[str] = None,
    ) -> str:
        """Index a document."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        try:
            result = await self.client.index(
                index=full_index_name, id=doc_id, document=document
            )
            return result["_id"]
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise

    async def bulk_index(
        self, index_name: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Bulk index multiple documents."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        # Prepare bulk operations
        operations = []
        for doc in documents:
            doc_id = doc.pop("_id", None)  # Remove _id from document if present
            operation = {"_index": full_index_name, "_source": doc}
            if doc_id:
                operation["_id"] = doc_id
            operations.append(operation)

        try:
            result = await self.client.bulk(operations=operations)

            # Count successful and failed operations
            successful = 0
            failed = 0

            for item in result["items"]:
                if "index" in item:
                    if item["index"]["status"] < 300:
                        successful += 1
                    else:
                        failed += 1

            logger.info(f"Bulk indexed {successful} documents, {failed} failed")
            return {"successful": successful, "failed": failed}

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise

    async def search(
        self,
        index_name: str,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute search query."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        body = {"query": query, "size": size, "from": from_}
        if sort:
            body["sort"] = sort

        try:
            result = await self.client.search(index=full_index_name, body=body)
            return result
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def update_document(
        self, index_name: str, doc_id: str, document: Dict[str, Any]
    ) -> bool:
        """Update a document."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        try:
            await self.client.update(
                index=full_index_name, id=doc_id, body={"doc": document}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise

    async def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete a document."""
        if not self.client:
            raise ConnectionError("Elasticsearch client not initialized")

        full_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{index_name}"

        try:
            await self.client.delete(index=full_index_name, id=doc_id)
            return True
        except NotFoundError:
            logger.warning(f"Document {doc_id} not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    def get_index_name(self, base_name: str) -> str:
        """Get full index name with prefix."""
        return f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{base_name}"


# Global Elasticsearch manager instance
es_manager = ElasticsearchManager()


async def get_elasticsearch() -> AsyncElasticsearch:
    """Get Elasticsearch client dependency."""
    if not es_manager.client:
        await es_manager.connect()
    return es_manager.client


async def init_elasticsearch() -> None:
    """Initialize Elasticsearch connection on startup."""
    await es_manager.connect()


async def close_elasticsearch() -> None:
    """Close Elasticsearch connection on shutdown."""
    await es_manager.disconnect()
