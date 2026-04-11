# Plan de Implementación: ChromaDB + Servidor MCP

## 📅 Fecha: 9 de abril de 2026
## 🎯 Objetivo: Base de datos vectorial + servidor MCP para RAG

---

## 📚 ¿Qué es ChromaDB?

**ChromaDB** es una base de datos vectorial open-source diseñada específicamente para aplicaciones de IA. Piensa en ella como una base de datos tradicional, pero en lugar de buscar por exactitud (SQL: `WHERE nombre = "Juan"`), busca por **similitud semántica**.

### Conceptos clave:

```
📦 ChromaDB
  └─ 📂 Collection (colección)
      ├─ 🔢 Embeddings (vectores numéricos de 384 dimensiones)
      ├─ 📝 Documents (texto original)
      ├─ 🏷️ Metadatas (URL, título, categoría, etc.)
      └─ 🆔 IDs (identificadores únicos)
```

**Ejemplo de consulta:**
- **SQL tradicional**: "dame todos los artículos de la categoría 'tarjetas'"
- **ChromaDB**: "dame los 5 chunks más similares a '¿cómo solicitar una tarjeta de crédito?'"

---

## 🎯 ¿Por qué ChromaDB para este proyecto?

| Criterio | ChromaDB | Alternativas |
|----------|----------|--------------|
| **Instalación** | ✅ `pip install chromadb` | Pinecone (requiere cuenta), Weaviate (complejo) |
| **Persistencia** | ✅ Local (carpeta `data/chroma_db/`) | Pinecone (cloud), pgvector (PostgreSQL) |
| **Costo** | ✅ $0 (100% gratis) | Pinecone (tier gratuito limitado) |
| **Documentación** | ✅ Excelente para Python | Qdrant (buena), FAISS (básica) |
| **Metadatos** | ✅ Filtering nativo | FAISS (no soporta) |
| **Ideal para** | ✅ Prototipos y datasets <100K | Pinecone (producción masiva) |

**Decisión:** ChromaDB es perfecto para nuestra prueba técnica (96 chunks, desarrollo local, $0 costo).

---

## 🏗️ Arquitectura de Nuestra Solución

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE ACTUAL (✅ COMPLETADO)          │
├─────────────────────────────────────────────────────────────┤
│ Scraper → Cleaner → Chunker → Embedder                     │
│  50 pgs    limpio    96 chunks  384 dims (Sentence Trans.) │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              CHROMADB (🔨 LO QUE VAMOS A IMPLEMENTAR)       │
├─────────────────────────────────────────────────────────────┤
│ • Crear colección "bancolombia_knowledge"                   │
│ • Indexar 96 chunks con embeddings + metadatos             │
│ • Métodos: add(), query(), get_by_url(), list_categories() │
│ • Persistencia: data/chroma_db/                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                SERVIDOR MCP (⏭️ SIGUIENTE PASO)             │
├─────────────────────────────────────────────────────────────┤
│ FastMCP (Python) expone:                                    │
│ • Tool: search_knowledge_base(query) → ChromaDB.query()    │
│ • Tool: get_article_by_url(url) → ChromaDB.get(where=...)  │
│ • Tool: list_categories() → ChromaDB.get() unique cats     │
│ • Resource: knowledge-base://stats → metadatos de DB       │
└─────────────────────────────────────────────────────────────┘
```

---

## ❓ Decisiones a Tomar (NECESITO TU INPUT)

### 🔹 Decisión 1: Modo de persistencia

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **A) Persistente** | Los datos se guardan en `data/chroma_db/` | ✅ No se pierde al reiniciar<br>✅ Ideal para desarrollo | ❌ Ocupa ~1-2 MB en disco |
| **B) En-memoria** | Los datos solo existen en RAM | ✅ Más rápido<br>✅ No deja archivos | ❌ Se pierde al cerrar programa |

**Mi recomendación:** **Opción A (persistente)** porque:
- Evitas regenerar embeddings cada vez que inicias el servidor MCP
- Cumple con criterio de la prueba "almacenamiento vectorial"
- Permite debugging fácil (puedes inspeccionar la DB)

**¿Estás de acuerdo o prefieres en-memoria?**

---

### 🔹 Decisión 2: Función de distancia (similarity metric)

ChromaDB soporta 3 funciones para medir similitud entre vectores:

| Función | Descripción | Mejor para | Fórmula |
|---------|-------------|------------|---------|
| **cosine** | Ángulo entre vectores | Textos de longitud variable | 1 - (A·B)/(‖A‖‖B‖) |
| **l2 (euclidean)** | Distancia euclidiana | Vectores normalizados | √Σ(A-B)² |
| **ip (inner product)** | Producto punto | Embeddings ya normalizados | A·B |

**Mi recomendación:** **cosine** porque:
- Es el estándar para retrieval semántico
- Sentence Transformers normaliza los embeddings (L2 norm = 1)
- Independiente de la magnitud del vector

**¿Usamos cosine o tienes preferencia por otra?**

---

### 🔹 Decisión 3: Estructura de datos en ChromaDB

#### 🤔 ¿Dónde van los chunks? - Explicación detallada

**Pregunta frecuente:** "No veo los chunks en los metadatos, ¿dónde están?"

**Respuesta:** Los chunks NO van en metadatos. Van en el campo `documents` de ChromaDB.

ChromaDB tiene **4 campos principales** por cada registro:

```python
# Estructura de UN registro en ChromaDB
{
    "id": "a1b2c3d4...",                    # 🆔 ID único (hash SHA256)
    "document": "Texto del chunk...",        # 📝 EL CHUNK (el contenido)
    "embedding": [0.123, -0.456, ...],       # 🔢 Vector de 384 dimensiones
    "metadata": {                            # 🏷️ INFORMACIÓN ADICIONAL
        "url": "https://...",
        "title": "...",
        "category": "...",
        # etc.
    }
}
```

**Analogía con SQL:**
```sql
-- ChromaDB es como esta tabla:
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,                    -- Hash SHA256
    document TEXT,                          -- ← EL CHUNK ESTÁ AQUÍ
    embedding VECTOR(384),                  -- Vector numérico
    metadata_url TEXT,                      -- Metadatos como columnas separadas
    metadata_title TEXT,
    metadata_category TEXT
);
```

#### 📊 Flujo de datos completo:

```
SCRAPER (scraped_pages.parquet)
├─ id: hash(url)
├─ metadata: {"url": "...", "title": "...", "category": "...", "fecha_extraccion": "..."}
└─ texto: "Contenido completo de la página (5000 palabras)"
            ↓
         CHUNKER
            ↓
CHUNKS (chunks.parquet)
├─ id: hash(url + chunk_index)
├─ metadata: {"url": "...", "title": "...", "category": "...", ...}
└─ texto: "Fragmento de 452 palabras"  ← UN CHUNK
            ↓
         EMBEDDER
            ↓
EMBEDDINGS (embeddings.parquet)
├─ chunk_id
└─ embedding: [0.123, -0.456, ..., 0.789]  (384 números)
            ↓
         CHROMADB
            ↓
CHROMADB (data/chroma_db/)
├─ id: hash SHA256 de (title + "\n" + texto_chunk)
├─ document: "Fragmento de 452 palabras"  ← EL CHUNK
├─ embedding: [0.123, -0.456, ..., 0.789]
└─ metadata: {
      "url": "https://www.bancolombia.com/personas/productos/tarjetas-credito",
      "title": "Tarjetas de Crédito",
      "category": "productos",
      "fecha_extraccion": "2026-04-09T14:30:00",
      "chunk_index": 0,
      "total_chunks": 3,
      "word_count": 452,
      "source_page_id": "abc123"
   }
```

#### ✅ Estructura FINAL de metadatos por chunk en ChromaDB:

Integraremos los metadatos del scraper + metadatos adicionales del chunking:

```python
{
    # === Del scraper (scraped_pages.parquet) ===
    "url": "https://www.bancolombia.com/personas/productos/tarjetas-credito",
    "title": "Tarjetas de Crédito",
    "category": "productos",
    "fecha_extraccion": "2026-04-09T14:30:00",  # ← NUEVO (requisito de la prueba)
    
    # === Del chunker (generado al procesar) ===
    "chunk_index": 0,           # Posición del chunk en el artículo (0, 1, 2...)
    "total_chunks": 3,          # Total de chunks de ese artículo
    "word_count": 452,          # Palabras en este chunk específico
    "source_page_id": "abc123"  # ID del registro en scraped_pages.parquet
}
```

**Confirmado:** Esta estructura cumple con los requisitos de la prueba técnica:
> "Almacene los datos crudos de forma estructurada con metadatos: URL de origen, título, fecha de extracción, categoría." ✅

---

### 🔹 Decisión 4: Estrategia de IDs

ChromaDB requiere IDs únicos para cada chunk.

| Opción | Ejemplo | Pros | Contras |
|--------|---------|------|---------|
| **UUID** | `550e8400-e29b-...` | ✅ Garantía de unicidad | ❌ No legible |
| **URL + índice** | `tarjetas-credito_chunk_0` | ✅ Legible<br>✅ Debuggeable | ❌ Requiere sanitización |
| **Hash SHA256** | `a1b2c3d4...` (16 chars) | ✅ Determinístico<br>✅ Reproducible | ✅ Garantía de unicidad |

**✅ Decisión confirmada:** **Hash SHA256 de `metadata.title + "\n" + texto_chunk`**

```python
import hashlib

def generate_chunk_id(metadata_title: str, texto_chunk: str) -> str:
    """Genera ID determinístico para el chunk usando SHA256"""
    content = f"{metadata_title}\n{texto_chunk}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

# Ejemplo:
title = "Tarjetas de Crédito"
chunk = "Las tarjetas de crédito Bancolombia ofrecen..."
chunk_id = generate_chunk_id(title, chunk)
# Resultado: "a1b2c3d4e5f6g7h8"
```

**Ventajas de este enfoque:**
- ✅ **Determinístico**: El mismo contenido siempre genera el mismo ID
- ✅ **Único**: SHA256 garantiza colisiones muy improbables
- ✅ **Reproducible**: Re-ejecutar el pipeline genera los mismos IDs
- ✅ **Compacto**: 16 caracteres (vs 36 de UUID)

---

## 📋 Paso a Paso de Implementación

### ✅ **Fase 1: Setup de ChromaDB** (15-20 min)

1. **Instalar ChromaDB:**
   ```bash
   pip install chromadb
   ```

2. **Crear `src/services/database.py`:**
   - Clase `ChromaDBService` con métodos:
     - `__init__()`: inicializar cliente persistente
     - `create_collection()`: crear colección con distancia cosine
     - `add_documents()`: indexar chunks en batch
     - `search()`: búsqueda semántica
     - `get_by_url()`: filtrar por metadata
     - `get_categories()`: listar categorías únicas
     - `get_stats()`: estadísticas de la DB

3. **Crear script `src/main.py` (ampliar):**
   - Cargar `data/chunks.parquet` y `data/embeddings.parquet`
   - Preparar metadatos desde chunks
   - Llamar a `ChromaDBService.add_documents()`
   - Guardar en `data/chroma_db/`

---

### ✅ **Fase 2: Indexación de Datos** (10 min)

4. **Ejecutar indexación:**
   ```bash
   python src/main.py --index-chromadb
   ```
   Esto tomará los 96 chunks + embeddings y los insertará en ChromaDB.

5. **Verificar persistencia:**
   - Revisar que existe `data/chroma_db/chroma.sqlite3`
   - Ver tamaño del directorio (~1-2 MB esperado)

---

### ✅ **Fase 3: Testing de Retrieval** (15 min)

6. **Crear `tests/test_chromadb.py`:**
   - Test 1: `test_add_documents()` → verifica que se indexaron 96 chunks
   - Test 2: `test_search_semantic()` → búsqueda de "tarjeta de crédito" retorna resultados relevantes
   - Test 3: `test_get_by_url()` → filtrado por URL funciona
   - Test 4: `test_get_categories()` → retorna categorías únicas
   - Test 5: `test_stats()` → estadísticas correctas

7. **Ejecutar tests:**
   ```bash
   pytest tests/test_chromadb.py -v
   ```

---

### ✅ **Fase 4: Validación Manual** (10 min)

8. **Crear `scripts/test_chromadb_queries.py`:**
   - Script interactivo para probar búsquedas:
   ```python
   query = "¿Cómo solicitar un crédito hipotecario?"
   results = db.search(query, n_results=5)
   for doc in results:
       print(f"Score: {doc['score']}")
       print(f"URL: {doc['metadata']['url']}")
       print(f"Texto: {doc['document'][:200]}...")
   ```

9. **Probar 5-7 queries típicas:**
   - Tarjetas de crédito
   - Cuentas de ahorro
   - Créditos hipotecarios
   - Seguros
   - Transferencias

---

## 📁 Estructura de Archivos (después de implementar)

```
rag-assistant/
├─ data/
│  ├─ scraped_pages.parquet        # ✅ Ya existe (50 páginas)
│  ├─ chunks.parquet                # ✅ Ya existe (96 chunks)
│  ├─ embeddings.parquet            # ✅ Ya existe (384 dims)
│  └─ chroma_db/                    # 🔨 NUEVO (ChromaDB persistente)
│     ├─ chroma.sqlite3             # Base de datos SQLite
│     └─ [archivos internos]
│
├─ src/
│  ├─ services/
│  │  └─ database.py                # 🔨 NUEVO (ChromaDBService)
│  └─ main.py                       # 🔨 MODIFICAR (agregar --index-chromadb)
│
├─ tests/
│  ├─ test_chromadb.py              # 🔨 NUEVO (5 unit tests)
│  └─ test_chromadb_queries.py      # 🔨 NUEVO (validación interactiva)
│
└─ docs/
   └─ CHROMADB_PLAN.md              # 📄 Este documento
```

---

## 🧪 Tests que Implementaremos

### Unit Tests (`tests/test_chromadb.py`)

```python
def test_create_collection():
    """Verifica que la colección se crea correctamente"""
    assert collection.name == "bancolombia_knowledge"
    assert collection.metadata["distance"] == "cosine"

def test_add_documents():
    """Verifica que se indexan los 96 chunks"""
    assert collection.count() == 96

def test_search_semantic():
    """Búsqueda semántica retorna resultados relevantes"""
    results = db.search("tarjeta de crédito", n_results=5)
    assert len(results) == 5
    assert results[0]["score"] > 0.5  # alta similitud
    assert "tarjeta" in results[0]["document"].lower()

def test_get_by_url():
    """Filtrado por URL retorna solo chunks de esa página"""
    url = "https://www.bancolombia.com/personas/productos/tarjetas-credito"
    results = db.get_by_url(url)
    assert all(doc["metadata"]["url"] == url for doc in results)

def test_get_categories():
    """Lista categorías únicas correctamente"""
    categories = db.get_categories()
    assert "productos" in categories
    assert len(categories) > 0
```

---

## 🔗 Integración con Servidor MCP (siguiente paso)

Después de implementar ChromaDB, el servidor MCP será trivial:

```python
# src/services/mcp_server.py (próximo paso)
from mcp.server.fastmcp import FastMCP
from src.services.database import ChromaDBService

mcp = FastMCP("Bancolombia RAG")
db = ChromaDBService()

@mcp.tool()
def search_knowledge_base(query: str, n_results: int = 5):
    """Búsqueda semántica en base de conocimiento"""
    return db.search(query, n_results)

@mcp.tool()
def get_article_by_url(url: str):
    """Obtener artículo completo por URL"""
    return db.get_by_url(url)

@mcp.tool()
def list_categories():
    """Listar categorías disponibles"""
    return db.get_categories()

@mcp.resource("knowledge-base://stats")
def get_stats():
    """Estadísticas de la base de conocimiento"""
    return db.get_stats()
```

---

## ✅ Checklist de Cumplimiento de Requisitos

Según [prueba-tecnica.md](prueba-tecnica.md):

| Requisito | Estado | Notas |
|-----------|--------|-------|
| **3.3 - Embeddings y almacenamiento vectorial** | 🔨 En progreso | ✅ Embeddings generados<br>🔨 ChromaDB por implementar |
| **3.3 - Justificar elección de base vectorial** | ✅ Listo | ChromaDB: gratis, local, Python-friendly, metadatos |
| **3.3 - Indexación con metadatos** | 🔨 En progreso | URL, categoría, título, chunk_index |
| **3.4 - Tools del servidor MCP** | ⏭️ Siguiente | ChromaDB proveerá los métodos necesarios |

---

## 🎯 Próximos Pasos Después de ChromaDB

1. ✅ **ChromaDB funcionando** (este paso)
2. ⏭️ **Servidor MCP con FastMCP** (tools + resource)
3. ⏭️ **Agente conversacional** (cliente MCP)
4. ⏭️ **Frontend de chat** (Streamlit/Gradio)
5. ⏭️ **Docker + CI/CD** (GitHub Actions)
6. ⏭️ **Video demo** (5 preguntas con fuentes)

---

---

## ✅ Decisiones CONFIRMADAS

Las 4 decisiones clave han sido validadas y están listas para implementar:

### ✅ **1. Persistencia: LOCAL (data/chroma_db/)**
- Los datos se guardan en `data/chroma_db/`
- No se pierden al reiniciar
- Ideal para desarrollo y cumple requisitos de la prueba

### ✅ **2. Función de Distancia: COSINE**
- Estándar para retrieval semántico
- Sentence Transformers normaliza embeddings (L2 norm = 1)
- Independiente de la magnitud del vector

### ✅ **3. Metadatos: ESTRUCTURA COMPLETA**
```python
{
    # Del scraper
    "url": "https://www.bancolombia.com/personas/productos/tarjetas-credito",
    "title": "Tarjetas de Crédito",
    "category": "productos",
    "fecha_extraccion": "2026-04-09T14:30:00",  # ✅ Agregado
    
    # Del chunker
    "chunk_index": 0,
    "total_chunks": 3,
    "word_count": 452,
    "source_page_id": "abc123"
}
```

### ✅ **4. IDs: HASH SHA256 de (title + "\n" + texto)**
- Determinístico y reproducible
- Garantía de unicidad
- 16 caracteres compactos

---

## 🤔 Preguntas para Validar Contigo

Antes de implementar, necesito tu confirmación en estas **4 decisiones clave**:

### ✋ **STOP - Responde antes de continuar:**

1. **Persistencia:** ¿Usamos modo persistente (`data/chroma_db/`) o en-memoria?  
   → Mi recomendación: **persistente**

2. **Función de distancia:** ¿Usamos `cosine`, `l2` o `ip`?  
   → Mi recomendación: **cosine**

3. **Metadatos:** ¿La estructura propuesta (URL, title, category, chunk_index, etc.) te parece completa?  
   → ¿Agregar/quitar algo?

4. **IDs de chunks:** ¿Usamos `url-sanitizada_chunk_0` o prefieres UUID?  
   → Mi recomendación: **URL + índice** (más debuggeable)

---

## 📊 Estimación de Tiempo

| Fase | Tiempo estimado |
|------|----------------|
| Setup de ChromaDB | 15-20 min |
| Indexación de datos | 10 min |
| Testing de retrieval | 15 min |
| Validación manual | 10 min |
| **TOTAL** | **~50-60 min** |

---

## 📝 Notas Finales

- ChromaDB es **mucho más simple** que otras bases vectoriales
- La mayoría del trabajo ya está hecho (embeddings listos)
- Solo es "conectar las piezas" entre `embeddings.parquet` y ChromaDB
- Después de esto, el servidor MCP será directo (FastMCP hace el trabajo pesado)

---

**¿Listo para empezar? Confirma las 4 decisiones y comenzamos con el código.** 🚀
