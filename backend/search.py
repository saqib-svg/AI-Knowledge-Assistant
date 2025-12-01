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
                        "embedding": {"type": "dense_vector", "dims": 384}, # Assuming 384 dim embeddings
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

def search_documents(query_embedding, top_k=3):
    if es_client is None:
        print("Elasticsearch client not available, returning empty results")
        return []
    response = es_client.search(
        index=INDEX_NAME,
        query={
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_embedding}
                }
            }
        },
        size=top_k
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]
