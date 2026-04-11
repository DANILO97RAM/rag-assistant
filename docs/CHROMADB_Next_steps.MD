# Próximos Pasos: Implementación de ChromaDB

## 🎯 Resumen Ejecutivo

Después de que termine el scraping, implementaremos ChromaDB en **4 fases (~50-60 min)**:

---

## 📋 Checklist de Pasos

### ✅ **Fase 0: Prerequisitos** (COMPLETADO)
- [x] Scraping ejecutándose → generará `scraped_pages.parquet` con `fecha_extraccion`
- [x] Decisiones confirmadas: local, cosine, SHA256, metadatos completos
- [x] Plan documentado en `CHROMADB_PLAN.md`

---

### 🔨 **Fase 1: Setup de ChromaDB** (~15-20 min)

#### 1.1. Instalar ChromaDB
```bash
pip install chromadb
```

#### 1.2. Crear servicio de base de datos vectorial
**Archivo:** `src/services/database.py`

**Clase:** `ChromaDBService`

**Métodos a implementar:**
```python
class ChromaDBService:
    def __init__(self, persist_directory: str = "data/chroma_db")
        # Inicializar cliente persistente con distancia cosine
    
    def create_collection(self)
        # Crear colección "bancolombia_knowledge"
    
    def add_documents(self, chunks_df, embeddings_df)
        # Indexar chunks con embeddings + metadatos
        # Genera ID con SHA256(title + "\n" + texto)
    
    def search(self, query: str, n_results: int = 5)
        # Búsqueda semántica
    
    def get_by_url(self, url: str)
        # Filtrar chunks por URL
    
    def get_categories(self)
        # Listar categorías únicas
    
    def get_stats(self)
        # Estadísticas de la DB
```

**Detalles técnicos:**
- Cliente persistente: `chromadb.PersistentClient(path="data/chroma_db")`
- Colección: `distance="cosine"`
- Batch insert: procesar 96 chunks de una vez
- Metadatos: extraer desde `chunks.parquet` + calcular adicionales

---

### 🔨 **Fase 2: Integración en Pipeline** (~10 min)

#### 2.1. Modificar `src/main.py`

Agregar nuevo comando para indexar ChromaDB:

```bash
python src/main.py --index-chromadb
```

**Flujo:**
1. Cargar `data/chunks.parquet` (96 chunks)
2. Cargar `data/embeddings.parquet` (384 dims)
3. Preparar metadatos desde chunks (parsear JSON de metadata)
4. Calcular campos adicionales: chunk_index, total_chunks, word_count
5. Generar IDs con SHA256
6. Llamar a `ChromaDBService.add_documents()`
7. Verificar persistencia en `data/chroma_db/`

---

### 🧪 **Fase 3: Testing** (~15 min)

#### 3.1. Crear `tests/test_chromadb.py`

**5 tests unitarios:**

```python
def test_create_collection():
    """Verifica creación de colección con config correcta"""
    assert collection.name == "bancolombia_knowledge"
    assert collection.metadata["hnsw:space"] == "cosine"

def test_add_documents():
    """Verifica que se indexaron 96 chunks"""
    assert collection.count() == 96

def test_search_semantic():
    """Búsqueda semántica retorna resultados relevantes"""
    results = db.search("tarjeta de crédito", n_results=5)
    assert len(results) == 5
    assert results[0]["distance"] < 0.5  # alta similitud
    assert "tarjeta" in results[0]["document"].lower()

def test_get_by_url():
    """Filtrado por URL funciona correctamente"""
    url = "https://www.bancolombia.com/personas/productos/tarjetas-credito"
    results = db.get_by_url(url)
    assert all(r["metadata"]["url"] == url for r in results)

def test_get_categories():
    """Lista categorías únicas"""
    categories = db.get_categories()
    assert "productos" in categories
    assert len(categories) > 0
```

#### 3.2. Ejecutar tests
```bash
pytest tests/test_chromadb.py -v
```

**Resultado esperado:** 5/5 tests passing ✅

---

### ✅ **Fase 4: Validación Manual** (~10 min)

#### 4.1. Crear `scripts/test_chromadb_queries.py`

Script interactivo para probar búsquedas:

```python
from src.services.database import ChromaDBService

db = ChromaDBService()

# Queries de prueba
queries = [
    "¿Cómo solicitar una tarjeta de crédito?",
    "Requisitos para crédito hipotecario",
    "Tasas de interés de cuentas de ahorro",
    "¿Qué seguros ofrece Bancolombia?",
    "Cómo hacer transferencias internacionales"
]

for query in queries:
    print(f"\n🔍 Query: {query}")
    results = db.search(query, n_results=3)
    
    for i, result in enumerate(results):
        print(f"\n  [{i+1}] Score: {result['distance']:.3f}")
        print(f"      URL: {result['metadata']['url']}")
        print(f"      Título: {result['metadata']['title']}")
        print(f"      Texto: {result['document'][:150]}...")
```

#### 4.2. Ejecutar validación
```bash
python scripts/test_chromadb_queries.py
```

**Verificar:**
- ✅ Resultados relevantes para cada query
- ✅ Scores de similitud razonables (< 0.5 para buenos matches)
- ✅ Metadatos correctos (URL, título, categoría)

---

## 📊 Entregables al Finalizar

Después de completar las 4 fases, tendrás:

```
rag-assistant/
├─ data/
│  ├─ scraped_pages.parquet        # ✅ 50 páginas (con fecha_extraccion)
│  ├─ chunks.parquet                # ✅ 96 chunks
│  ├─ embeddings.parquet            # ✅ 384 dims
│  └─ chroma_db/                    # 🆕 ChromaDB persistente
│     ├─ chroma.sqlite3             # Base de datos SQLite
│     └─ [índice vectorial]
│
├─ src/
│  └─ services/
│     └─ database.py                # 🆕 ChromaDBService
│
├─ tests/
│  └─ test_chromadb.py              # 🆕 5 unit tests
│
└─ scripts/
   └─ test_chromadb_queries.py      # 🆕 Validación interactiva
```

---

## ✅ Checklist de Validación Final

Antes de pasar al servidor MCP, verifica:

- [ ] `data/chroma_db/chroma.sqlite3` existe (~1-2 MB)
- [ ] `pytest tests/test_chromadb.py` → 5/5 passing
- [ ] `scripts/test_chromadb_queries.py` → resultados relevantes
- [ ] Búsqueda de "tarjeta de crédito" retorna chunks sobre tarjetas
- [ ] Filtro por URL retorna solo chunks de esa URL
- [ ] `db.get_stats()` muestra: 96 chunks, N categorías, fecha de última actualización

---

## 🔗 Después de ChromaDB: Servidor MCP

Una vez ChromaDB esté funcionando, el siguiente paso es:

**Implementar servidor MCP con FastMCP** que exponga:

```python
@mcp.tool()
def search_knowledge_base(query: str, n_results: int = 5):
    return db.search(query, n_results)  # ← ChromaDB ya implementado

@mcp.tool()
def get_article_by_url(url: str):
    return db.get_by_url(url)  # ← ChromaDB ya implementado

@mcp.tool()
def list_categories():
    return db.get_categories()  # ← ChromaDB ya implementado

@mcp.resource("knowledge-base://stats")
def get_stats():
    return db.get_stats()  # ← ChromaDB ya implementado
```

**Tiempo estimado MCP:** ~30-40 min (ChromaDB hace todo el trabajo pesado)

---

## 🚦 Estado Actual del Proyecto

| Componente | Estado | Notas |
|------------|--------|-------|
| **Scraping** | 🔄 Ejecutándose | Generando scraped_pages.parquet con fecha_extraccion |
| **Limpieza** | ✅ Listo | TextCleaner implementado y testeado |
| **Chunking** | ✅ Listo | 1024/128 validado como óptimo |
| **Embeddings** | ✅ Listo | Sentence Transformers 384 dims |
| **ChromaDB** | ⏭️ Siguiente | 4 fases (~50-60 min) |
| **Servidor MCP** | ⏸️ Pendiente | Después de ChromaDB |
| **Agente** | ⏸️ Pendiente | Después de MCP |
| **Frontend** | ⏸️ Pendiente | Después de Agente |

---

## 🎯 Acción Inmediata

**Espera a que termine el scraping**, luego ejecuta:

```bash
# 1. Verificar que se generaron los archivos
ls -lh data/*.parquet

# 2. Instalar ChromaDB
pip install chromadb

# 3. Avísame cuando esté listo y empezamos con Fase 1
```

---

**Tiempo total estimado hoy:** ~1.5-2 horas para completar ChromaDB + tests
