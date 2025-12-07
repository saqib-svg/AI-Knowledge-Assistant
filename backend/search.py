from elasticsearch import Elasticsearch
import os

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
INDEX_NAME = "documents"

try:
    es_client = Elasticsearch(ES_HOST)
except Exception as e:
    print(f"Warning: Could not connect to Elasticsearch at {ES_HOST}: {e}")
    es_client = None

def create_index():
    if es_client is None:
        print("Elasticsearch client not available, skipping index creation")
        return
    try:
        if not es_client.indices.exists(index=INDEX_NAME):
            es_client.indices.create(
                index=INDEX_NAME,
                mappings={
                    "properties": {
                        "content": {"type": "text"},
                        "embedding": {"type": "dense_vector", "dims": 384, "element_type": "float"}, # Assuming 384 dim embeddings
                        "metadata": {"type": "object"}
                    }
                }
            )
    except Exception as e:
        print(f"Error creating index: {e}")

def index_document(doc_id, content, embedding, metadata):
    if es_client is None:
        print("Elasticsearch client not available, skipping document indexing")
        return
    es_client.index(
        index=INDEX_NAME,
        id=doc_id,
        document={
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }
    )

<<<<<<< Updated upstream
def search_documents(query_embedding, allowed_ids=None, top_k=3):
    """Search documents by vector. If `allowed_ids` is provided, restrict search to those ES document ids."""
    if es_client is None:
        print("Elasticsearch client not available, returning empty results")
        return []

    if allowed_ids is not None and len(allowed_ids) == 0:
        return []

    # Build base script_score query
    script_score = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {"query_vector": query_embedding}
            }
        }
    }

    if allowed_ids:
        # Restrict to allowed ids using a bool filter inside the script_score query
        script_score["script_score"]["query"] = {"bool": {"filter": {"terms": {"_id": allowed_ids}}}}

    response = es_client.search(
        index=INDEX_NAME,
        query=script_score,
=======
def search_documents(query_embedding, top_k=3, doc_ids=None):
    """
    Search for documents by embedding similarity.
    
    Args:
        query_embedding: The query embedding vector
        top_k: Number of results to return
        doc_ids: Optional list of doc_ids to filter by
    """
    if es_client is None:
        print("Elasticsearch client not available, returning empty results")
        return []
    
    # Build the query - filter by doc_ids if provided
    if doc_ids and len(doc_ids) > 0:
        base_query = {
            "bool": {
                "filter": [
                    {"terms": {"metadata.doc_id": doc_ids}}
                ]
            }
        }
    else:
        base_query = {"match_all": {}}
    
    response = es_client.search(
        index=INDEX_NAME,
        query={
            "script_score": {
                "query": base_query,
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_embedding}
                }
            }
        },
>>>>>>> Stashed changes
        size=top_k
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]

