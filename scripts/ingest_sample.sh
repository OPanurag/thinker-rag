#!/bin/bash
curl -X POST http://localhost:8000/ingest-url -H "Content-Type: application/json" \
-d '{"url":"https://en.wikipedia.org/wiki/OpenAI"}'
