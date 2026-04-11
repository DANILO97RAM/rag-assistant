#!/bin/bash
# Búsqueda Semántica - Consumidor Financiero

echo "🔍 Búsqueda: ¿Qué es el consumidor financiero?"
echo "==============================================="
echo ""

curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "query": "¿Qué es el consumidor financiero?",
    "n_results": 5
  }' \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Deberías ver documentos sobre derechos del consumidor"
# Commented by GitHub Copilot
