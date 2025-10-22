from fastapi import APIRouter
from pydantic import BaseModel
from model.embed_provider import get_embedding
from storage.qdrant_client import qdrant_search
from model.llm_provider import generate_answer

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[dict]
    total_chunks: int
    query_time_ms: float

@router.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    import time
    start_time = time.time()
    
    # Get query embedding and search
    vec = get_embedding(req.query)
    hits = qdrant_search(vec, top_k=req.top_k)
    
    # Format context from hits
    context = []
    for h in hits:
        payload = h.payload
        context.append({
            "url": payload.get("url"),
            "chunk_index": payload.get("chunk_index"),
            "text": payload.get("text"),
            "score": h.score
        })
    
    # Generate answer using LLM
    llm_response = generate_answer(req.query, context)
    
    # Calculate query time
    query_time = (time.time() - start_time) * 1000
    
    # Build response
    response = {
        "answer": llm_response.get("answer", "Error generating response"),
        "confidence": llm_response.get("confidence", 0.0),
        "sources": llm_response.get("sources", []),
        "total_chunks": len(context),
        "query_time_ms": round(query_time, 2)
    }
    
    return response
