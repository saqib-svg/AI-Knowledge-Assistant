from elasticsearch import Elasticsearch
import os
import logging

logger = logging.getLogger(__name__)

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
INDEX_NAME = "documents"

try:
    es_client = Elasticsearch(ES_HOST, request_timeout=30)
    # Test connection
    info = es_client.info()
    logger.info(f"✓ Connected to Elasticsearch: {info['version']['number']}")
except Exception as e:
    logger.error(f"⚠ Could not connect to Elasticsearch at {ES_HOST}: {e}")
    es_client = None

def create_index():
    if es_client is None:
        logger.warning("Elasticsearch client not available, skipping index creation")
        return
    try:
        if not es_client.indices.exists(index=INDEX_NAME):
            es_client.indices.create(
                index=INDEX_NAME,
                mappings={
                    "properties": {
                        "content": {"type": "text"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 384,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "metadata": {"type": "object"}
                    }
                }
            )
            logger.info(f"✓ Created Elasticsearch index: {INDEX_NAME}")
        else:
            logger.info(f"✓ Elasticsearch index already exists: {INDEX_NAME}")
    except Exception as e:
        logger.error(f"✗ Error creating index: {e}")
        import traceback
        logger.error(traceback.format_exc())

def index_document(doc_id, content, embedding, metadata):
    """Index a document with error handling"""
    if es_client is None:
        logger.error("Elasticsearch client not available, cannot index document")
        return False
    
    try:
        # Validate embedding
        if not embedding or not isinstance(embedding, list):
            logger.error(f"Invalid embedding for document {doc_id}")
            return False
        
        if len(embedding) != 384:
            logger.error(f"Embedding dimension mismatch for {doc_id}: expected 384, got {len(embedding)}")
            return False
        
        # Index the document
        response = es_client.index(
            index=INDEX_NAME,
            id=doc_id,
            document={
                "content": content,
                "embedding": embedding,
                "metadata": metadata
            },
            refresh=True  # Make it immediately searchable
        )
        
        logger.info(f"✓ Indexed document {doc_id}: {response['result']}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error indexing document {doc_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def search_documents(query_embedding, allowed_ids=None, top_k=3):
    """
    Search documents by vector with improved error handling
    """
    if es_client is None:
        logger.error("Elasticsearch client not available, returning empty results")
        return []

    try:
        # Validate query embedding
        if not query_embedding or not isinstance(query_embedding, list):
            logger.error("Invalid query embedding")
            return []
        
        if len(query_embedding) != 384:
            logger.error(f"Query embedding dimension mismatch: expected 384, got {len(query_embedding)}")
            return []
        
        # Build query with allowed_ids filter if provided
        if allowed_ids is not None and len(allowed_ids) == 0:
            logger.info("Empty allowed_ids list, returning no results")
            return []
        
        # Use knn search for better performance
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 100
        }
        
        # Add filter for allowed IDs if specified
        if allowed_ids:
            knn_query["filter"] = {
                "terms": {
                    "_id": allowed_ids
                }
            }
            logger.info(f"Searching with allowed_ids filter: {allowed_ids}")
        
        logger.info(f"Executing knn search with top_k={top_k}")
        response = es_client.search(
            index=INDEX_NAME,
            knn=knn_query,
            size=top_k
        )
        
        hits = response["hits"]["hits"]
        logger.info(f"Search returned {len(hits)} results")
        
        results = []
        for hit in hits:
            source = hit["_source"]
            results.append({
                "content": source.get("content", ""),
                "metadata": source.get("metadata", {}),
                "score": hit["_score"]
            })
            logger.info(f"  - Document score: {hit['_score']:.4f}, content length: {len(source.get('content', ''))}")
        
        return results
        
    except Exception as e:
        logger.error(f"✗ Error searching documents: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def delete_document(doc_id):
    """Delete a document from the index"""
    if es_client is None:
        logger.error("Elasticsearch client not available")
        return False
    
    try:
        response = es_client.delete(index=INDEX_NAME, id=doc_id)
        logger.info(f"✓ Deleted document {doc_id}: {response['result']}")
        return True
    except Exception as e:
        logger.error(f"✗ Error deleting document {doc_id}: {e}")
        return False

def check_document_exists(doc_id):
    """Check if a document exists in the index"""
    if es_client is None:
        return False
    
    try:
        return es_client.exists(index=INDEX_NAME, id=doc_id)
    except Exception as e:
        logger.error(f"Error checking document existence: {e}")
        return False