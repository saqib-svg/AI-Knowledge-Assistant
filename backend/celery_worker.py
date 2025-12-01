from celery import Celery
import os
from .llm import get_embedding
from .search import index_document

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

celery_app = Celery(
    "worker",
    broker=f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672//",
    backend=f"rpc://"
)

@celery_app.task(name="process_document")
def process_document(doc_id, content, filename):
    print(f"Processing document: {filename} ({doc_id})")
    
    # 1. Generate Embedding
    embedding = get_embedding(content)
    
    # 2. Index to Elasticsearch
    metadata = {"filename": filename}
    index_document(doc_id, content, embedding, metadata)
    
    return f"Document {filename} processed and indexed."
