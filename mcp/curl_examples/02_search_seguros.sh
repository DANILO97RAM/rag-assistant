#!/bin/bash
# Búsqueda Semántica - Seguros

echo "🔍 Búsqueda: ¿Qué seguros ofrece Bancolombia?"
echo "=============================================="
echo ""

curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "query": "¿Qué seguros ofrece Bancolombia?",
    "n_results": 3
  }' \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Deberías ver 3 documentos relacionados con seguros"
# Commented by GitHub Copilot
