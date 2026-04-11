#!/bin/bash
# Obtener Artículo por URL - Créditos

echo "📄 Obtener Artículo: Créditos Bancolombia"
echo "=========================================="
echo ""

curl -X GET "http://localhost:8000/article?url=https://www.bancolombia.com/personas/creditos" \
  -H "Accept: application/json" \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Deberías ver todos los chunks del artículo de créditos"

