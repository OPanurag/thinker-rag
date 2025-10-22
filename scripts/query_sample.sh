#!/bin/bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
-d '{"query":"What is OpenAI?"}'
