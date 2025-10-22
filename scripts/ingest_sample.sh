#!/bin/bash
TEXT=$(cat sample_data/about_rag.txt)
JSON="{\"content\":\"$TEXT\"}"
echo $JSON | curl -X POST http://localhost:8000/ingest-text -H "Content-Type: application/json" -d @-
