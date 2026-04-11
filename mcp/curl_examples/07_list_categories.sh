#!/bin/bash
# Listar Todas las Categorías

echo "📋 Listar Categorías"
echo "===================="
echo ""

curl -X GET http://localhost:8000/categories \
  -H "Accept: application/json" \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Deberías ver ~47 categorías únicas"
# Commented by GitHub Copilot
