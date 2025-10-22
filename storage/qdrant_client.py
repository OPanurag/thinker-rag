import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
EMBED_DIM = int(os.getenv("EMBED_DIM", 1536))
COLLECTION = os.getenv("QDRANT_COLLECTION", "thinker_collection")

client = QdrantClient(url=QDRANT_URL)

def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.recreate_collection(collection_name=COLLECTION,
                                   vectors={"size": EMBED_DIM, "distance": "Cosine"})

def qdrant_upsert(points: list):
    ensure_collection()
    client.upsert(collection_name=COLLECTION, points=points)

def qdrant_search(vector, top_k=5):
    ensure_collection()
    return client.search(collection_name=COLLECTION, query_vector=vector, limit=top_k)
