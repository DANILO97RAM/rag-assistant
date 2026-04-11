#!/bin/bash
# Búsqueda con Filtro de Categoría

echo "🔍 Búsqueda Filtrada: Seguros (solo categoría 'seguros')"
echo "========================================================="
echo ""

curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "query": "seguros de vida",
    "n_results": 3,
    "category": "seguros"
  }' \
  -w "\n\n✅ Status Code: %{http_code}\n" \
  -s | jq '.'

echo ""
echo "💡 Todos los resultados deberían tener category='seguros'"

