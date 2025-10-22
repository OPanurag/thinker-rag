from fastapi import FastAPI
from api.routes import ingest, query
from storage.database import init_db

app = FastAPI(title="Thinker-RAG API")

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(ingest.router)
app.include_router(query.router)
