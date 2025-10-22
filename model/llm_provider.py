import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are a factual AI assistant with RAG (Retrieval-Augmented Generation) capabilities. Your goal is to provide accurate, grounded answers based ONLY on the given context.

Instructions:
1. Only use information present in the provided context chunks.
2. If the context doesn't contain enough information, say "I don't have enough information to answer that question."
3. Always support your answers with citations from the context.
4. Return your response in a strict JSON format:
{
    "answer": "Your detailed answer here, with inline citations like [1] or [2]",
    "confidence": 0-1 score based on context relevance,
    "sources": [
        {
            "url": "source_url",
            "chunk_index": numeric_index,
            "relevance": 0-1 score,
            "quote": "exact quote from the chunk that supports the answer"
        }
    ]
}
"""

def generate_answer(question: str, context_chunks: list[dict], max_tokens=1024):
    # Format context with unique identifiers
    context_text = "\n\n".join(
        [f"[{i}] Source: {c.get('url')}\nContent: {c.get('text')}" 
         for i, c in enumerate(context_chunks)]
    )
    
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context_text}\n\nQUESTION: {question}\n\nProvide a structured JSON response:"
    
    try:
        resp = client.generate_text(model=LLM_MODEL, 
                                  prompt=prompt,
                                  max_output_tokens=max_tokens,
                                  temperature=0.1)
        
        # Try to extract JSON from response
        import json
        try:
            result = json.loads(resp.text)
            return result
        except json.JSONDecodeError:
            # Fallback if response is not valid JSON
            return {
                "answer": "Error: Could not generate a valid structured response.",
                "confidence": 0,
                "sources": []
            }
            
    except Exception as e:
        return {
            "answer": f"Error generating response: {str(e)}",
            "confidence": 0,
            "sources": []
        }
