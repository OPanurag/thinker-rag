#!/bin/bash
CONTENT=$(cat /Users/anurag/VS Code/thinker-rag/sample_data/about_rag.txt)
curl -X POST http://localhost:8000/ingest-text -H "Content-Type: application/json" \
-d "{\"content\":\"$CONTENT\"}"
