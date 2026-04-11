# 🧪 Ejemplos cURL - Bancolombia API

Scripts listos para probar cada endpoint de la API REST.

## 🚀 Requisitos Previos

1. **Servidor API ejecutándose:**
   ```bash
   # Desde la raíz del proyecto
   cd mcp
   python api_server.py
   ```

2. **(Opcional) jq instalado** para formato JSON bonito:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install jq
   
   # macOS
   brew install jq
   
   # Windows (WSL)
   sudo apt-get install jq
   ```

---

## 📋 Scripts Disponibles

### 1. Health Check
```bash
bash 01_health_check.sh
```
Verifica que el servidor esté funcionando.

### 2. Búsqueda: Seguros
```bash
bash 02_search_seguros.sh
```
Busca información sobre seguros de Bancolombia.

### 3. Búsqueda: Consumidor Financiero
```bash
bash 03_search_consumidor.sh
```
Busca información sobre derechos del consumidor financiero.

### 4. Búsqueda con Filtro
```bash
bash 04_search_filtered.sh
```
Búsqueda filtrada solo en la categoría "seguros".

### 5. Obtener Artículo: Créditos
```bash
bash 05_get_article_creditos.sh
```
Recupera el artículo completo de créditos por URL.

### 6. Obtener Artículo: Seguros
```bash
bash 06_get_article_seguros.sh
```
Recupera el artículo completo de seguros por URL.

### 7. Listar Categorías
```bash
bash 07_list_categories.sh
```
Lista todas las categorías disponibles (~47).

### 8. Estadísticas
```bash
bash 08_get_stats.sh
```
Muestra estadísticas de la base de conocimiento.

---

## 🎯 Ejecución Rápida

### Ejecutar Todos los Tests
```bash
for script in *.sh; do
  echo ""
  echo "════════════════════════════════════════"
  bash "$script"
  sleep 2
done
```

### Ejecutar Script Individual
```bash
# Dar permisos de ejecución (primera vez)
chmod +x *.sh

# Ejecutar
./01_health_check.sh
```

---

## 🔧 Sin jq (JSON sin formato)

Si no tienes `jq` instalado, los scripts igual funcionan pero el JSON se verá en una sola línea.

**Alternativa:** Edita cada script y elimina `| jq '.'`

**Ejemplo:**
```bash
# Original
curl ... | jq '.'

# Sin jq
curl ...
```

---

## 🐛 Troubleshooting

### Error: "Failed to connect to localhost"
```bash
# El servidor API no está ejecutándose
cd mcp
python api_server.py
```

### Error: "bash: jq: command not found"
```bash
# Instalar jq o quitar "| jq '.'" de los scripts
sudo apt-get install jq
```

### Error: "Permission denied"
```bash
# Dar permisos de ejecución
chmod +x *.sh
```

---

## 📊 Output Esperado

### Health Check
```json
{
  "service": "Bancolombia Knowledge API",
  "status": "operational",
  "version": "1.0.0"
}
```

### Search
```json
{
  "query": "...",
  "total_results": 3,
  "documents": [
    {
      "rank": 1,
      "similarity_score": 0.638,
      "title": "...",
      "url": "...",
      "content": "..."
    }
  ]
}
```

### Stats
```json
{
  "total_documents": 94,
  "num_categories": 47,
  "embedding_dimension": 384,
  "distance_metric": "cosine"
}
```

---

## 💡 Tips

1. **Ver solo campos específicos con jq:**
   ```bash
   curl http://localhost:8000/stats | jq '.total_documents'
   ```

2. **Guardar respuesta en archivo:**
   ```bash
   bash 08_get_stats.sh > stats_output.json
   ```

3. **Ver tiempo de respuesta:**
   ```bash
   curl -w "\nTiempo: %{time_total}s\n" http://localhost:8000/stats
   ```

4. **Probar endpoint personalizado:**
   ```bash
   curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"query": "TU_PREGUNTA_AQUÍ", "n_results": 5}' | jq '.'
   ```

---

**Autor:** Danilo Gómez  
**Fecha:** 2026-04-10
<!-- Commented by GitHub Copilot -->
