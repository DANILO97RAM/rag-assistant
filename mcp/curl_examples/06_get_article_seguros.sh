#!/bin/bash
# Obtener Artículo por URL - Seguros

echo "📄 Obtener Artículo: Seguros Bancolombia"
echo "========================================="
echo ""

curl -X GET "http://localhost:8000/article?url=https://www.bancolombia.com/personas/seguros" \
  -H "Accept: application/json" \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Deberías ver todos los chunks del artículo de seguros"

