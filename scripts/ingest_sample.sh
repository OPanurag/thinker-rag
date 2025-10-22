#!/bin/bash
# Read the content of the file and escape it for JSON
CONTENT=$(cat sample_data/about_rag.txt | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

# Remove the leading and trailing quotes that python adds
CONTENT="${CONTENT:1:-1}"

# Create the JSON payload and send the request
curl -X POST http://localhost:8000/ingest-text \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"$CONTENT\"}"
