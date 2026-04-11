#!/bin/bash
# Ejecuta todos los tests de cURL en secuencia

echo "╔════════════════════════════════════════════════════════╗"
echo "║  🧪 BANCOLOMBIA API - SUITE DE TESTS COMPLETA         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "⏱️  Cada test espera 3 segundos antes del siguiente"
echo "🛑 Presiona Ctrl+C para cancelar en cualquier momento"
echo ""
sleep 2

# Array de scripts en orden
scripts=(
  "01_health_check.sh"
  "02_search_seguros.sh"
  "03_search_consumidor.sh"
  "04_search_filtered.sh"
  "05_get_article_creditos.sh"
  "06_get_article_seguros.sh"
  "07_list_categories.sh"
  "08_get_stats.sh"
)

# Contador
total=${#scripts[@]}
current=0

# Ejecutar cada script
for script in "${scripts[@]}"; do
  current=$((current + 1))
  
  echo ""
  echo "╔════════════════════════════════════════════════════════╗"
  echo "║  Test $current/$total: $script"
  echo "╚════════════════════════════════════════════════════════╝"
  echo ""
  
  if [ -f "$script" ]; then
    bash "$script"
  else
    echo "❌ Error: Script no encontrado: $script"
  fi
  
  # Pausa entre tests (excepto el último)
  if [ $current -lt $total ]; then
    echo ""
    echo "⏸️  Esperando 3 segundos..."
    sleep 3
  fi
done

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ TESTS COMPLETADOS ($total/$total)                     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

