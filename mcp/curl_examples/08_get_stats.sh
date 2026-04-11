#!/bin/bash
# Estadísticas de la Base de Conocimiento

echo "📊 Estadísticas ChromaDB"
echo "========================"
echo ""

curl -X GET http://localhost:8000/stats \
  -H "Accept: application/json" \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Deberías ver 94 documentos, 47 categorías, dimensión 384"
# Commented by GitHub Copilot
