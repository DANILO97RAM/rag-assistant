# API REST - Bancolombia Knowledge Base

Servidor HTTP para testing con **Postman**, **Insomnia** o cualquier cliente HTTP.

Complementa al servidor MCP (stdio) proporcionando acceso vía REST a la misma base de conocimiento.

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
# Desde la raíz del proyecto
pip install fastapi uvicorn

# O con Makefile
make api_install
```

### 2. Ejecutar Servidor

```bash
# Opción 1: Con Makefile
make api_server

# Opción 2: Directo
cd mcp
python api_server.py
```

**Output esperado:**
```
🚀 Iniciando Bancolombia API REST
📦 Versión: 1.0.0
📂 ChromaDB path: /path/to/data/chroma_db
✅ Base lista: 94 documentos
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Abrir Documentación Interactiva

```
http://localhost:8000/docs
```

**Swagger UI** te permite probar todos los endpoints desde el navegador.

---

## 📋 Endpoints Disponibles

### 1. Health Check

```http
GET http://localhost:8000/
```

**Respuesta:**
```json
{
  "service": "Bancolombia Knowledge API",
  "status": "operational",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### 2. Búsqueda Semántica

```http
POST http://localhost:8000/search
Content-Type: application/json

{
  "query": "¿Qué seguros ofrece Bancolombia?",
  "n_results": 3,
  "category": "seguros"  // opcional
}
```

**Respuesta:**
```json
{
  "query": "¿Qué seguros ofrece Bancolombia?",
  "total_results": 3,
  "documents": [
    {
      "rank": 1,
      "content": "Seguros Bancolombia Protege tu salud...",
      "url": "https://www.bancolombia.com/personas/seguros",
      "title": "Seguros Bancolombia",
      "category": "seguros",
      "similarity_score": 0.638,
      "word_count": 738
    }
  ]
}
```

**Parámetros:**
- `query` (string, requerido): Consulta en lenguaje natural
- `n_results` (int, opcional): Número de resultados (default: 5, max: 10)
- `category` (string, opcional): Filtro por categoría

---

### 3. Obtener Artículo por URL

```http
GET http://localhost:8000/article?url=https://www.bancolombia.com/personas/creditos
```

**Respuesta:**
```json
{
  "url": "https://www.bancolombia.com/personas/creditos",
  "total_chunks": 2,
  "title": "Créditos Bancolombia",
  "category": "creditos",
  "chunks": [
    {
      "content": "Créditos Bancolombia para todas...",
      "chunk_index": 0,
      "word_count": 437
    }
  ]
}
```

**Parámetros:**
- `url` (string, requerido): URL completa de bancolombia.com

---

### 4. Listar Categorías

```http
GET http://localhost:8000/categories
```

**Respuesta:**
```json
{
  "total_categories": 47,
  "categories": [
    "a-la-mano",
    "bancolombia",
    "creditos",
    "seguros",
    ...
  ]
}
```

---

### 5. Estadísticas

```http
GET http://localhost:8000/stats
```

**Respuesta:**
```json
{
  "status": "operational",
  "total_documents": 94,
  "num_categories": 47,
  "embedding_dimension": 384,
  "distance_metric": "cosine",
  "fecha_ultima_actualizacion": "2026-04-09T02:19:08",
  "source": "https://www.bancolombia.com/personas",
  "categories": ["a-la-mano", "creditos", ...]
}
```

---

## 🧪 Testing con Postman

### Opción 1: Importar Colección

1. Abrir Postman
2. Click en **Import**
3. Seleccionar archivo: `mcp/Bancolombia_API.postman_collection.json`
4. La colección incluye 8 requests de ejemplo

### Opción 2: Crear Requests Manualmente

#### Request 1: Health Check
```
Method: GET
URL: http://localhost:8000/
```

#### Request 2: Search
```
Method: POST
URL: http://localhost:8000/search
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "query": "¿Qué es el consumidor financiero?",
  "n_results": 3
}
```

#### Request 3: Get Article
```
Method: GET
URL: http://localhost:8000/article?url=https://www.bancolombia.com/personas/creditos
```

#### Request 4: Categories
```
Method: GET
URL: http://localhost:8000/categories
```

#### Request 5: Stats
```
Method: GET
URL: http://localhost:8000/stats
```

---

## 🧪 Testing con cURL

```bash
# Health check
curl http://localhost:8000/

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué seguros ofrece Bancolombia?",
    "n_results": 3
  }'

# Get article
curl "http://localhost:8000/article?url=https://www.bancolombia.com/personas/creditos"

# Categories
curl http://localhost:8000/categories

# Stats
curl http://localhost:8000/stats
```

---

## 🐍 Testing con Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Health check
response = requests.get(f"{BASE_URL}/")
print(response.json())

# 2. Search
response = requests.post(f"{BASE_URL}/search", json={
    "query": "¿Qué seguros ofrece Bancolombia?",
    "n_results": 3
})
results = response.json()
print(f"Encontrados: {results['total_results']} resultados")
print(f"Top resultado: {results['documents'][0]['title']}")

# 3. Get article
response = requests.get(f"{BASE_URL}/article", params={
    "url": "https://www.bancolombia.com/personas/creditos"
})
article = response.json()
print(f"Chunks: {article['total_chunks']}")

# 4. Categories
response = requests.get(f"{BASE_URL}/categories")
categories = response.json()
print(f"Categorías: {categories['total_categories']}")

# 5. Stats
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print(f"Documentos: {stats['total_documents']}")
```

---

## 📊 Diferencias con Servidor MCP

| Característica | Servidor MCP | API REST |
|----------------|--------------|----------|
| **Transporte** | stdio (stdin/stdout) | HTTP |
| **Puerto** | N/A | 8000 |
| **Cliente** | Agentes MCP | Postman, curl, navegador |
| **Protocolo** | JSON-RPC 2.0 | REST |
| **Documentación** | MCP spec | Swagger UI |
| **Uso principal** | Agentes conversacionales | Testing, debugging |

**Ambos servidores:**
- ✅ Usan la misma base de datos (ChromaDB)
- ✅ Mismas funcionalidades (search, get_article, etc.)
- ✅ Pueden ejecutarse simultáneamente

---

## 🔧 Configuración Avanzada

### Cambiar Puerto

```bash
# En api_server.py, línea final:
uvicorn.run(app, host="0.0.0.0", port=9000)  # Cambiar a 9000
```

### Solo Localhost

```bash
# Para mayor seguridad (solo acceso local):
uvicorn.run(app, host="127.0.0.1", port=8000)
```

### Modo Producción

```bash
# Con múltiples workers
uvicorn mcp.api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🐛 Troubleshooting

### Error: "Address already in use"

```bash
# Buscar proceso en puerto 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Matar proceso
kill -9 <PID>  # Linux/Mac
taskkill /F /PID <PID>  # Windows

# O cambiar puerto en api_server.py
```

### Error: "chromadb module not found"

```bash
pip install -r requirements.txt
```

### Error: "Base de conocimiento vacía"

```bash
# Indexar datos en ChromaDB primero
python src/main.py --index-chromadb
```

---

## 📚 Documentación Adicional

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 🎯 Comandos Rápidos

```bash
# Instalar dependencias
make api_install

# Ejecutar servidor
make api_server

# Test rápido con curl
make api_test

# Abrir Swagger UI
xdg-open http://localhost:8000/docs  # Linux
open http://localhost:8000/docs      # Mac
start http://localhost:8000/docs     # Windows
```

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-10
<!-- Commented by GitHub Copilot -->
