# RAG Assistant - Bancolombia

Sistema de recuperación y generación aumentada (RAG) para consultas sobre productos y servicios de Bancolombia. Implementa scraping web, procesamiento de texto, embeddings semánticos, búsqueda vectorial y servidor MCP para integración con agentes conversacionales.

---

## 🎯 Características Principales

- ✅ **Web Scraping Inteligente**: Crawling BFS con renderizado JavaScript (Playwright)
- ✅ **Procesamiento de Texto**: Limpieza, normalización y chunking semántico
- ✅ **Embeddings de Alta Calidad**: Sentence Transformers (384 dimensiones)
- ✅ **Base de Datos Vectorial**: ChromaDB con persistencia local y cosine similarity
- ✅ **Búsqueda Semántica**: Retrieval con metadatos y filtrado por categorías
- ✅ **API MCP**: Exposición de herramientas mediante Model Context Protocol
- ✅ **Testing Completo**: 6 tests unitarios + validación con queries realistas

---

## 📊 Métricas del Sistema

| Métrica | Valor |
|---------|-------|
| Páginas scrapeadas | 50 |
| Chunks generados | 94 |
| Categorías detectadas | 47 |
| Dimensión embeddings | 384 |
| Precisión promedio | 0.645 |
| Queries con score >0.70 | 29% |

Ver reporte completo: [docs/CHROMADB_VALIDATION_REPORT.md](docs/CHROMADB_VALIDATION_REPORT.md)

---

## 🛠️ Stack Tecnológico

### Framework & Lenguaje
- **Python 3.12.3** (compatible desde 3.11+)
- **Pandas 3.0.2** - Procesamiento de datos
- **Pydantic** - Validación de esquemas

### Web Scraping
- **Playwright 1.49.1** - Browser automation con renderizado JavaScript
- **BeautifulSoup4 4.12.3** - Parsing HTML
- **Técnica**: BFS crawling con profundidad 2, concurrencia 8

### Procesamiento de Texto
- **LangChain 0.3.17** - Framework para procesamiento RAG
- **RecursiveCharacterTextSplitter** - Chunking semántico
  - Chunk size: 1024 tokens
  - Overlap: 128 tokens
- **tiktoken 0.9.0** - Tokenizador (cl100k_base)

### Embeddings & Búsqueda Vectorial
- **Sentence Transformers 3.3.1** - Generación de embeddings
  - Modelo: `all-MiniLM-L6-v2`
  - Dimensiones: 384
  - Velocidad: ~60-120 batches/segundo
- **ChromaDB 1.5.7** - Base de datos vectorial
  - Modo: Persistent (local storage)
  - Distancia: Cosine similarity
  - Indexación: HNSW
- **PyTorch 2.5.1** - Backend para inference

### Testing
- **pytest 9.0.3** - Framework de testing
- **pytest-asyncio** - Tests asíncronos
- Cobertura: 6 tests unitarios + validación realista

---

## 📁 Arquitectura del Proyecto

```
rag-assistant/
├── src/
│   ├── config/
│   │   ├── config.json              # Configuración del sistema
│   │   └── logger.py                # Logging centralizado
│   ├── core/
│   │   ├── scrapper.py              # Playwright crawler (BFS)
│   │   ├── cleaner.py               # Limpieza y normalización HTML
│   │   ├── chunker.py               # RecursiveCharacterTextSplitter
│   │   ├── embedder.py              # Sentence Transformers wrapper
│   │   └── processor.py             # Orquestador limpieza + chunking
│   ├── services/
│   │   ├── database.py              # ChromaDB service
│   └── main.py                      # CLI principal
├── tests/
│   ├── test_chromadb.py                    # Tests unitarios ChromaDB
│   └── test_chromadb_realistic_queries.py  # Validación con queries
├── scripts/
│   └── analyze_content.py           # Análisis de contenido scrapeado
├── data/
│   ├── scraped_pages.parquet        # 50 páginas (raw)
│   ├── chunks.parquet               # 94 chunks procesados
│   ├── embeddings_sentence-transformers.parquet  # 94 vectores 384D
│   └── chroma_db/                   # Base de datos ChromaDB
├── docs/
│   └── prueba-tecnica.md            # Reporte de validación completo
├── requirements.txt                 # Dependencias Python
└── Makefile                         # Comandos de automatización
```

---

## 🔄 Pipeline de Procesamiento

### 1. Web Scraping
```python
# Configuración
URL_BASE = "https://www.bancolombia.com/personas"
PROFUNDIDAD = 2
MAX_PÁGINAS = 50
CONCURRENCIA = 10
```

**Técnica:** Crawling BFS (Breadth-First Search)
- Renderizado JavaScript con Playwright
- Extracción de título, categoría, y contenido HTML
- Normalización de URLs y deduplicación
- Guardado en `data/scraped_pages.parquet`

**Resultado:** 50 páginas, 47 categorías únicas

### 2. Limpieza de Texto
- Eliminación de scripts, estilos y metadatos
- Normalización de espacios en blanco
- Preservación de estructura semántica
- Extracción de metadata (URL, título, categoría, fecha)

### 3. Chunking Semántico
```python
# Configuración
CHUNK_SIZE = 1024 tokens
OVERLAP = 128 tokens
TOKENIZER = "cl100k_base" (GPT-4 tokenizer)
```

**Técnica:** RecursiveCharacterTextSplitter (LangChain)
- Separadores: `\n\n`, `\n`, `. `, ` `
- Evita cortes en medio de oraciones
- Overlap para preservar contexto entre chunks

**Resultado:** 94 chunks con distribución:
- Media: ~437 palabras/chunk
- Mediana: ~359 palabras/chunk
- Máximo: ~751 palabras/chunk

### 4. Generación de Embeddings
```python
# Modelo
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSIONS = 384
BATCH_SIZE = 100
```

**Proceso:**
1. Concatenación: `title + "\n" + texto`
2. Encoding con Sentence Transformers
3. Normalización L2
4. Guardado en formato Parquet

**Performance:**
- Velocidad: 60-120 batches/segundo
- Tamaño embeddings: ~145KB (94 vectores × 384D × float32)

### 5. Indexación en ChromaDB
```python
# Configuración
PERSIST_DIRECTORY = "data/chroma_db"
DISTANCE_METRIC = "cosine"
COLLECTION_NAME = "bancolombia_knowledge"
```

**Características:**
- IDs determinísticos: SHA256(title + index + texto)[:16]
- Metadata rica: url, title, category, fecha_extraccion, chunk_index, word_count
- Indexación HNSW para búsqueda eficiente
- Persistencia local (sin servidor externo)

**Estadísticas:**
- Total documentos: 94
- Categorías: 47
- Distancia: cosine (0.0 = idéntico, 1.0 = opuesto)

---

## 🚀 Instalación y Uso

### Prerrequisitos

- Python 3.11+ (recomendado 3.12.3)
- pip o conda
- 2GB RAM mínimo
- 500MB espacio en disco

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/DANILO97RAM/rag-assistant.git
cd rag-assistant

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium
```

### Comandos Makefile

```bash
# Ver todos los comandos
make help

# Ejecutar pipeline completo (scraping + limpieza + chunking)
make run

# Solo scraping (50 páginas)
make scraper

# Generar embeddings
make embeddings

# Indexar en ChromaDB
make db_index

# Resetear ChromaDB y re-indexar
make db_reset

# Ejecutar tests
make test

# Validación con queries realistas
make db_queries_test

# Análisis de contenido
make analyze_content
```

### Uso Manual

```bash
# Pipeline completo
python src/main.py

# Scraping forzado (ignorar caché)
python src/main.py --force-scrape

# Indexar en ChromaDB
python src/main.py --index-chromadb

# Resetear ChromaDB
python src/main.py --index-chromadb --reset-chromadb

# Solo cargar chunks (sin scraping)
python -c "from src.main import load_chunks_from_disk; load_chunks_from_disk()"
```

---

## 🧪 Testing y Validación

### Tests Unitarios

```bash
# Ejecutar todos los tests
pytest tests/test_chromadb.py -v

# Ver output detallado
pytest tests/test_chromadb.py -v -s
```

**Tests implementados:**
1. ✅ `test_create_collection` - Creación de colección con cosine metric
2. ✅ `test_add_documents` - Indexación de 3 documentos de prueba
3. ✅ `test_search_semantic` - Búsqueda semántica con embeddings
4. ✅ `test_get_by_url` - Filtrado por URL
5. ✅ `test_get_categories` - Extracción de categorías únicas
6. ✅ `test_get_stats` - Estadísticas de la colección

**Resultado:** 6/6 tests passing ✅

### Validación con Queries Realistas

```bash
python tests/test_chromadb_realistic_queries.py
```

**Queries evaluadas:**
- ¿Qué seguros ofrece Bancolombia? (Score: 0.638)
- ¿Qué es el consumidor financiero? (Score: 0.723) ✨
- ¿Qué beneficios tiene la banca preferencial? (Score: 0.602)
- ¿Qué es A la mano de Bancolombia? (Score: 0.626)
- ¿Qué tipos de créditos hay disponibles? (Score: 0.654)
- ¿Cómo puedo invertir mi dinero? (Score: 0.553)
- ¿Quién es el defensor del consumidor financiero? (Score: 0.768) 🏆

**Interpretación de scores:**
- 0.70-1.00: Excelente precisión
- 0.60-0.70: Buena precisión
- 0.50-0.60: Precisión media
- <0.50: Baja precisión

Ver análisis completo: [docs/CHROMADB_VALIDATION_REPORT.md](docs/CHROMADB_VALIDATION_REPORT.md)

---

## 📚 API ChromaDB

### Inicialización

```python
from services.database import ChromaDBService

db = ChromaDBService(persist_directory="data/chroma_db")
db.create_collection()
```

### Búsqueda Semántica

```python
# Búsqueda simple
results = db.search(
    query="¿Qué seguros ofrece Bancolombia?",
    n_results=5
)

# Búsqueda con filtro por categoría
results = db.search(
    query="información sobre seguros",
    n_results=3,
    where={"category": "seguros"}
)

# Estructura de resultados
for result in results:
    print(f"Score: {1 - result['distance']:.3f}")
    print(f"Título: {result['metadata']['title']}")
    print(f"Categoría: {result['metadata']['category']}")
    print(f"Texto: {result['document'][:100]}...")
```

### Filtrado por URL

```python
chunks = db.get_by_url("https://www.bancolombia.com/personas/creditos")
print(f"Encontrados {len(chunks)} chunks para esta URL")
```

### Listado de Categorías

```python
categories = db.get_categories()
print(f"Categorías disponibles: {len(categories)}")
# ['a-la-mano', 'bancolombia', 'creditos', 'seguros', ...]
```

### Estadísticas

```python
stats = db.get_stats()
print(f"Total documentos: {stats['total_documents']}")
print(f"Categorías: {stats['num_categories']}")
print(f"Dimensión: {stats['embedding_dimension']}")
print(f"Métrica: {stats['distance_metric']}")
```

---

## � Servidor MCP (Model Context Protocol)

El sistema expone la base de conocimiento mediante un **servidor MCP** que cumple con los requisitos de la prueba técnica (Sección 3.4).

### Características

- ✅ **SDK Oficial**: FastMCP (Python)
- ✅ **Transporte**: stdio (obligatorio)
- ✅ **3 Tools**: search_knowledge_base, get_article_by_url, list_categories
- ✅ **1 Resource**: knowledge-base://stats
- ✅ **Validación**: Parámetros y manejo de errores

### Ejecución del Servidor

```bash
# Desde la raíz del proyecto
cd mcp
python main.py
```

### Tools Disponibles

#### 1. search_knowledge_base

Búsqueda semántica en la base de conocimiento:

```python
search_knowledge_base(
    query="¿Qué seguros ofrece Bancolombia?",
    n_results=5,
    category="seguros"  # opcional
)
```

**Retorna:**
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

#### 2. get_article_by_url

Recupera contenido completo de un artículo:

```python
get_article_by_url(url="https://www.bancolombia.com/personas/creditos")
```

**Retorna:**
```json
{
  "url": "https://www.bancolombia.com/personas/creditos",
  "total_chunks": 2,
  "title": "Créditos Bancolombia",
  "category": "creditos",
  "chunks": [...]
}
```

#### 3. list_categories

Lista todas las categorías disponibles:

```python
list_categories()
```

**Retorna:**
```json
{
  "total_categories": 47,
  "categories": ["a-la-mano", "creditos", "seguros", ...]
}
```

### Resource Disponible

**URI**: `knowledge-base://stats`

Expone estadísticas de la base de conocimiento:
- Total documentos indexados
- Número de categorías
- Dimensión de embeddings
- Métrica de distancia
- Fecha de última actualización

### Testing del Servidor MCP

```bash
# Ejecutar tests automatizados
cd mcp
python test_server.py
```

**Output esperado:**
```
🧪 TESTING SERVIDOR MCP - BANCOLOMBIA
============================================================

📋 TEST 1: search_knowledge_base
------------------------------------------------------------
✅ search_knowledge_base: OK
   → 3 resultados encontrados
   → Score top-1: 0.723

📋 TEST 2: get_article_by_url
------------------------------------------------------------
✅ get_article_by_url: OK
   → 2 chunks recuperados

📋 TEST 3: list_categories
------------------------------------------------------------
✅ list_categories: OK
   → 47 categorías disponibles

============================================================
📊 RESUMEN DE PRUEBAS
============================================================
Resultado: 3/3 tests pasados

🎉 ¡Todos los tests pasaron exitosamente!
```

### Integración con Agentes

El servidor MCP puede ser consumido por cualquier agente conversacional compatible:

**Claude Desktop:**
```json
{
  "mcpServers": {
    "bancolombia": {
      "command": "python",
      "args": ["/path/to/rag-assistant/mcp/main.py"],
      "env": {
        "CHROMA_PATH": "/path/to/data/chroma_db"
      }
    }
  }
}
```

**LangChain/Python:**
```python
import subprocess
import json

# Iniciar servidor MCP
process = subprocess.Popen(
    ["python", "mcp/main.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE
)

# Enviar request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search_knowledge_base",
        "arguments": {"query": "¿Qué créditos hay?"}
    }
}

process.stdin.write(json.dumps(request).encode() + b'\n')
response = json.loads(process.stdout.readline())
```

Ver documentación completa: [mcp/README.md](mcp/README.md)

---
## 🌐 API REST (Testing con Postman/Insomnia)

Para facilitar el testing y desarrollo, se incluye una **API REST** que expone la misma funcionalidad del servidor MCP mediante endpoints HTTP.

### Características

- ✅ **Framework**: FastAPI con Uvicorn
- ✅ **Puerto**: 8000 (configurable)
- ✅ **Documentación**: Swagger UI automática
- ✅ **CORS**: Habilitado para desarrollo
- ✅ **Validación**: Pydantic models
- ✅ **Estado**: ✅ Validado con Postman

### Inicio Rápido

```bash
# Instalar dependencias
pip install fastapi uvicorn
# O con Makefile
make api_install

# Iniciar servidor
cd mcp
python api_server.py
# O con Makefile
make api_server
```

**Output esperado:**
```
🚀 Iniciando Bancolombia API REST
📦 Versión: 1.0.0
✅ Base lista: 94 documentos
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Endpoints Disponibles

| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/` | GET | Health check | ✅ Probado |
| `/search` | POST | Búsqueda semántica | ✅ Probado |
| `/article` | GET | Obtener artículo por URL | ✅ Probado |
| `/categories` | GET | Listar categorías | ✅ Probado |
| `/stats` | GET | Estadísticas | ✅ Probado |
| `/docs` | GET | Swagger UI | ✅ Disponible |

### Testing con Postman

1. **Importar colección:**
   - Abrir Postman
   - Click en **Import**
   - Seleccionar: `mcp/Bancolombia_API.postman_collection.json`

2. **Ejecutar requests:**
   - La colección incluye 8 requests de ejemplo
   - Health check, búsquedas, artículos, categorías, stats

3. **Swagger UI (alternativa):**
   - Abrir navegador: `http://localhost:8000/docs`
   - Probar endpoints directamente desde la interfaz

### Ejemplo: Búsqueda Semántica

**Request:**
```bash
POST http://localhost:8000/search
Content-Type: application/json

{
  "query": "¿Qué seguros ofrece Bancolombia?",
  "n_results": 3,
  "category": "seguros"  // opcional
}
```

**Response:**
```json
{
  "query": "¿Qué seguros ofrece Bancolombia?",
  "total_results": 3,
  "documents": [
    {
      "rank": 1,
      "similarity_score": 0.638,
      "title": "Seguros Bancolombia",
      "url": "https://www.bancolombia.com/personas/seguros",
      "content": "Seguros Bancolombia Protege tu salud...",
      "category": "seguros",
      "word_count": 738
    }
  ]
}
```

### Diferencias MCP vs REST API

| Característica | Servidor MCP | API REST |
|----------------|--------------|----------|
| **Transporte** | stdio (stdin/stdout) | HTTP |
| **Puerto** | N/A | 8000 |
| **Cliente** | Agentes MCP (Claude, GPT) | Postman, navegador, curl |
| **Protocolo** | JSON-RPC 2.0 | REST |
| **Documentación** | MCP spec | Swagger UI |
| **Uso principal** | Agentes conversacionales | Testing, debugging, desarrollo |

**Nota:** Ambos servidores usan la **misma base de datos ChromaDB** y exponen la misma funcionalidad.

### Documentación Completa

- **Guía rápida:** [CURL_QUICK_START.md](CURL_QUICK_START.md)
- **API REST completa:** [mcp/API_REST_README.md](mcp/API_REST_README.md)
- **Colección Postman:** [mcp/Bancolombia_API.postman_collection.json](mcp/Bancolombia_API.postman_collection.json)

---
## �📊 Limitaciones y Recomendaciones

### Limitaciones Actuales

1. **Contenido Limitado**: Solo 50 páginas scrapeadas
   - Falta información detallada de productos
   - No incluye requisitos, tasas, procedimientos específicos
   - Categorías con poco contenido (ej: pagos solo 312 palabras)

2. **Calidad de Retrieval**: Depende de contenido disponible
   - 29% queries con score >0.70 (excelente)
   - 43% queries con score 0.60-0.70 (bueno)
   - 29% queries con score <0.60 (mejorable)

3. **Scraping Superficial**: Profundidad 2 niveles
   - No captura páginas de productos detallados
   - Mucho contenido navegacional/informativo vs transaccional

### Recomendaciones de Mejora

#### Corto Plazo
- ✅ Implementar servidor MCP para exposición de API
- ✅ Documentar limitaciones de contenido en README
- ✅ Usar queries realistas en demos basadas en contenido disponible

#### Mediano Plazo
- 🔄 **Mejorar scraping**:
  - Incrementar a 150-200 páginas
  - Profundidad 3 niveles
  - Priorizar categorías con poco contenido
- 🔄 **Optimizar chunking**:
  - Revisar estrategia para páginas importantes
  - Aumentar overlap a 256 tokens en páginas clave
- 🔄 **Enriquecer metadatos**:
  - Agregar tags adicionales
  - Tipo de producto, audiencia objetivo

#### Largo Plazo
- 🚀 **Re-ranking**: Modelo de re-ranking post-retrieval
- 🚀 **Hybrid search**: Combinar búsqueda semántica + keyword-based (BM25)
- 🚀 **Evaluación continua**: Dataset gold-standard con queries y expected results
- 🚀 **Fine-tuning**: Entrenar modelo de embeddings específico para dominio bancario

---

## 📖 Documentación Adicional

- [docs/prueba-tecnica.md](docs/prueba-tecnica.md) - Especificación del proyecto
- [docs/scraping_report.md](docs/scraping_report.md) - Reporte detallado de scraping
- [docs/CHROMADB_PLAN.md](docs/CHROMADB_PLAN.md) - Plan de implementación ChromaDB
- [docs/CHROMADB_VALIDATION_REPORT.md](docs/CHROMADB_VALIDATION_REPORT.md) - Reporte de validación completo

---

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'feat: añadir nueva funcionalidad'`
4. Push a branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

**Estilo de commits:** Conventional Commits (feat, fix, docs, test, refactor)

---

## 📄 Licencia

Este proyecto es parte de una prueba técnica y está destinado únicamente para fines educativos y de evaluación.

---

## 👤 Autor

**Danilo Gómez**
- GitHub: [@DANILO97RAM](https://github.com/DANILO97RAM)

---

## 🙏 Agradecimientos

- Bancolombia por el contenido público
- LangChain por el framework RAG <3
- Sentence Transformers por los modelos de embeddings, craks, idolos, mastodontes, genios, dioses, semidioses, leyendas, mitos, bestias mitológicas, unicornios, dragones, fénix, quimeras, grifos, sirenas, centauros, minotauros, esfinges, cíclopes, gorgonas, harpías, sátiros, ninfas y demás criaturas fantásticas que hacen posible la magia de los embeddings.
- ChromaDB por la base de datos vectorial
