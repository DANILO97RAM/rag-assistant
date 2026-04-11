# Servidor MCP - Bancolombia Knowledge Base

Microservicio independiente que implementa el **Model Context Protocol (MCP)** para exponer la base de conocimiento de Bancolombia como herramientas consumibles por agentes conversacionales.

---

## 🎯 Propósito

Cumple con los requisitos de la **Sección 3.4** de la prueba técnica:
- ✅ Implementación con **FastMCP** (Python)
- ✅ Transporte **stdio** (obligatorio)
- ✅ 3 Tools obligatorias
- ✅ 1 Resource obligatorio
- ✅ Validación de parámetros
- ✅ Manejo de errores

---

## 📋 Tools Disponibles

### 1. `search_knowledge_base`

Ejecuta búsqueda semántica contra ChromaDB con embeddings Sentence Transformers.

**Parámetros:**
```python
{
  "query": str,           # Consulta en lenguaje natural (requerido)
  "n_results": int,       # Número de resultados (default: 5, max: 10)
  "category": str | None  # Filtro opcional por categoría
}
```

**Retorno:**
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

**Ejemplo de uso:**
```bash
# Búsqueda simple
search_knowledge_base(query="¿Qué créditos hay disponibles?")

# Búsqueda con filtro
search_knowledge_base(query="información sobre seguros", category="seguros", n_results=3)
```

---

### 2. `get_article_by_url`

Recupera todos los chunks de un artículo específico mediante su URL.

**Parámetros:**
```python
{
  "url": str  # URL completa de bancolombia.com (requerido)
}
```

**Retorno:**
```json
{
  "url": "https://www.bancolombia.com/personas/creditos",
  "total_chunks": 2,
  "title": "Créditos Bancolombia",
  "category": "creditos",
  "chunks": [
    {
      "content": "Créditos Bancolombia para todas tus necesidades...",
      "chunk_index": 0,
      "word_count": 437
    }
  ]
}
```

**Validación:**
- URL debe iniciar con `https://www.bancolombia.com`
- Retorna error si no se encuentra el artículo

---

### 3. `list_categories`

Lista todas las categorías disponibles en la base de conocimiento.

**Parámetros:** Ninguno

**Retorno:**
```json
{
  "total_categories": 47,
  "categories": [
    "a-la-mano",
    "creditos",
    "seguros",
    "inversiones",
    ...
  ]
}
```

---

## 📊 Resource Disponible

### `knowledge-base://stats`

Expone estadísticas actuales de la base de conocimiento.

**URI:** `knowledge-base://stats`

**Retorno (texto):**
```
📊 ESTADÍSTICAS BASE DE CONOCIMIENTO BANCOLOMBIA

✅ Estado: Operativa
📚 Total documentos: 94
📁 Categorías: 47
🔢 Dimensión embeddings: 384
📏 Métrica de distancia: cosine
📅 Última actualización: 2026-04-09T02:19:08
🌐 Fuente: https://www.bancolombia.com/personas

Categorías disponibles:
  • a-la-mano
  • creditos
  • seguros
  ...
```

---

## 🚀 Instalación y Ejecución

### Prerrequisitos

```bash
# Desde la raíz del proyecto
pip install fastmcp chromadb sentence-transformers

# Asegurar que ChromaDB esté indexado
python src/main.py --index-chromadb
```

### Ejecución Local (stdio)

```bash
# Desde la raíz del proyecto
cd mcp
python main.py
```

**Salida esperada:**
```
🚀 Iniciando Bancolombia MCP Server
📦 Versión: 1.0.0
🔌 Transporte: stdio
📂 ChromaDB path: /path/to/data/chroma_db
✅ Base de conocimiento lista: 94 documentos
```

### Variables de Entorno

```bash
# Opcional: Cambiar ruta de ChromaDB
export CHROMA_PATH=/custom/path/to/chroma_db
python main.py
```

---

## 🧪 Pruebas

### Prueba Manual con MCP Inspector

```bash
# Instalar MCP Inspector (herramienta oficial)
npm install -g @modelcontextprotocol/inspector

# Ejecutar inspector
mcp-inspector python mcp/main.py
```

### Prueba con Script Python

```python
import subprocess
import json

# Iniciar servidor MCP
process = subprocess.Popen(
    ["python", "mcp/main.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Enviar request para search_knowledge_base
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search_knowledge_base",
        "arguments": {
            "query": "¿Qué es el consumidor financiero?",
            "n_results": 3
        }
    }
}

process.stdin.write(json.dumps(request).encode() + b'\n')
process.stdin.flush()

# Leer respuesta
response = process.stdout.readline()
print(json.loads(response))
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                   AGENTE CONVERSACIONAL                 │
│              (Claude, GPT, Llama, etc.)                 │
│                                                         │
│  Usa MCP SDK para conectarse al servidor               │
└─────────────────┬───────────────────────────────────────┘
                  │ MCP Protocol (stdio)
                  │ JSON-RPC 2.0
┌─────────────────▼───────────────────────────────────────┐
│              SERVIDOR MCP (FastMCP)                     │
│                                                         │
│  Tools:                                                 │
│    • search_knowledge_base(query, n_results, category) │
│    • get_article_by_url(url)                           │
│    • list_categories()                                 │
│                                                         │
│  Resource:                                              │
│    • knowledge-base://stats                            │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│            ChromaDBService (services/database.py)       │
│                                                         │
│  • create_collection()                                 │
│  • search() - Búsqueda semántica                       │
│  • get_by_url() - Filtrado por URL                     │
│  • get_categories() - Extracción de categorías         │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                ChromaDB (Persistent)                    │
│                                                         │
│  • 94 documentos indexados                             │
│  • 47 categorías                                       │
│  • Embeddings 384D (Sentence Transformers)             │
│  • Cosine similarity                                   │
│  • HNSW indexing                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 Manejo de Errores

El servidor implementa validación y manejo de errores robusto:

### Errores de Validación

```json
{
  "error": "Query vacía",
  "message": "Debe proporcionar una consulta válida"
}
```

### Errores de ChromaDB

```json
{
  "error": "Base de datos no disponible",
  "message": "Error conectando a ChromaDB: [detalle]"
}
```

### Errores de Búsqueda

```json
{
  "error": "Artículo no encontrado",
  "message": "No se encontraron documentos para la URL: https://..."
}
```

---

## 📖 Protocolo MCP

El servidor implementa el **Model Context Protocol** estándar:

**Transporte:** stdio (JSON-RPC 2.0 sobre stdin/stdout)

**Formato de mensajes:**
```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_knowledge_base",
    "arguments": {
      "query": "¿Qué seguros ofrece Bancolombia?"
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "query": "¿Qué seguros ofrece Bancolombia?",
    "total_results": 3,
    "documents": [...]
  }
}
```

**Referencias:**
- [Model Context Protocol Docs](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)

---

## 🔧 Troubleshooting

### Error: "Base de conocimiento vacía"

```bash
# Solución: Indexar chunks en ChromaDB
python src/main.py --index-chromadb
```

### Error: "chromadb module not found"

```bash
# Solución: Instalar dependencias
pip install -r requirements.txt
```

### Error: "collection 'bancolombia_knowledge' not found"

```bash
# Solución: Verificar nombre de colección en src/services/database.py
# Debe ser: bancolombia_knowledge
```

---

## 📝 Logs

El servidor genera logs informativos en stderr:

```
🚀 Iniciando Bancolombia MCP Server
📦 Versión: 1.0.0
🔌 Transporte: stdio
🔗 Conectando a ChromaDB en /path/to/data/chroma_db
✅ ChromaDB conectado exitosamente
✅ Base de conocimiento lista: 94 documentos
🔍 Búsqueda ejecutada: '¿Qué seguros...' → 3 resultados
📄 Artículo recuperado: https://... → 2 chunks
📁 Categorías listadas: 47 encontradas
```

---

## 🎯 Cumplimiento de Requisitos

| Requisito | Estado | Implementación |
|-----------|--------|----------------|
| FastMCP SDK | ✅ | `from fastmcp import FastMCP` |
| Transporte stdio | ✅ | `mcp.run(transport="stdio")` |
| Tool: search_knowledge_base | ✅ | Línea 56-107 |
| Tool: get_article_by_url | ✅ | Línea 110-158 |
| Tool: list_categories | ✅ | Línea 161-185 |
| Resource: knowledge-base://stats | ✅ | Línea 188-217 |
| Validación de parámetros | ✅ | Checks en cada tool |
| Manejo de errores | ✅ | try/except con mensajes descriptivos |
| Metadatos (URL, score) | ✅ | Incluidos en respuestas |

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-10

