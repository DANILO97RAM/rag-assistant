#!/bin/bash
# Health Check - Verifica que el servidor esté funcionando

echo "📡 Health Check - Bancolombia API"
echo "=================================="
echo ""

curl -X GET http://localhost:8000/ \
  -H "Accept: application/json" \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Si ves 'operational', el servidor está funcionando correctamente"
# Commented by GitHub Copilot
