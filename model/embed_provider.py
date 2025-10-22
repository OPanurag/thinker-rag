import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_embedding(text: str):
    response = client.models.embed_content(model=EMBED_MODEL, content=text)
    return response.embeddings[0].embedding

def embed_batch(texts: list[str]):
    response = client.models.embed_content(model=EMBED_MODEL, content=texts)
    return [e.embedding for e in response.embeddings]
