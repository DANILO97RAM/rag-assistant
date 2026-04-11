# 🚀 RAG Assistant - Bancolombia

Asistente virtual basado en RAG (Retrieval-Augmented Generation) que responde preguntas sobre productos y servicios de Bancolombia.

## 📁 Estructura del Proyecto

```
rag-assistant/
├── src/
│   ├── core/
│   │   ├── scrapper.py      # Web scraping con Playwright
│   │   ├── cleaner.py       # Limpieza de texto
│   │   ├── chunker.py       # Segmentación de texto
│   │   └── embedder.py      # Generación de embeddings ✨
│   ├── services/
│   │   └── database.py      # ChromaDB (próximamente)
│   └── main.py              # Pipeline principal
├── tests/
│   ├── test_embedder.py     # Tests unitarios
│   └── generate_embeddings.py  # Script de embeddings
├── data/
│   ├── chunks.parquet       # Chunks procesados
│   └── embeddings.parquet   # Embeddings generados
└── requirements.txt
```

## 🔧 Instalación

### WSL 

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## ⚙️ Configuración

1. Copia el archivo de ejemplo de variables de entorno:
```bash
copy .env.example .env
```

2. Edita `.env` con tu configuración:
```env
# Para usar Gemini (recomendado si tienes plan Pro)
GEMINI_API_KEY=tu_api_key_aqui
EMBEDDING_PROVIDER=gemini

# O para usar modelos locales (gratuito, sin API key)
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## 🚀 Uso

### 1. Pipeline Completo (Scraping → Limpieza → Chunking)

```bash
python src/main.py
```

Esto generará:
- ✅ **50 páginas** scrapeadas de `bancolombia.com/personas`
- ✅ **~92 chunks** con overlap de 128 tokens
- ✅ Archivo `data/chunks.parquet` guardado

**Parámetros opcionales:**
```bash
python src/main.py --max-pages 100 --concurrency 10 --depth 3
```

### 2. Generar Embeddings

Con **Sentence Transformers** (local, gratis):
```bash
python tests/generate_embeddings.py --provider sentence-transformers
```

Con **Gemini** (requiere API key):
```bash
python tests/generate_embeddings.py --provider gemini --api-key TU_API_KEY
```

Con **OpenAI**:
```bash
python tests/generate_embeddings.py --provider openai --api-key TU_API_KEY --model text-embedding-3-small
```

### 3. Ejecutar Tests

```bash
# Instalar pytest
pip install pytest

# Ejecutar tests unitarios
pytest tests/test_embedder.py -v

# Ejecutar tests de integración
pytest tests/test_embedder.py -v -m integration
```

## 📊 Parámetros de Chunking

Configuración actual en [chunker.py](src/core/chunker.py):
- **chunk_size**: 1024 tokens (~750 palabras)
- **chunk_overlap**: 128 tokens (10-20% del tamaño)

### ¿Por qué más chunks que páginas?

Si scrapeaste **50 páginas** y obtuviste **92 chunks**:
- Páginas largas (>1024 tokens) se dividen en múltiples chunks
- Páginas cortas (<1024 tokens) generan 1 chunk

**Ejemplo:**
```
Página 1: 3000 tokens → 3 chunks (1024 + 1024 + 952)
Página 2: 800 tokens  → 1 chunk
Total: 2 páginas → 4 chunks
```

### Ajustar cantidad de chunks

Para **menos chunks** (chunks más grandes):
```python
# En chunker.py
chunk_size = 2048  # ← Aumentar
```

Para **más chunks** (chunks más pequeños):
```python
chunk_size = 512   # ← Reducir
```

## 🤖 Embeddings: Providers Disponibles

### 1. Sentence Transformers (Local, Gratuito)
- ✅ Sin costo
- ✅ Sin API key
- ✅ Funciona offline
- ❌ Menor calidad que modelos comerciales

**Modelos recomendados:**
- `all-MiniLM-L6-v2` (384 dims, rápido)
- `paraphrase-multilingual-mpnet-base-v2` (768 dims, multilingüe)

### 2. Google Gemini (Recomendado si pagas Pro)
- ✅ Incluido en plan Gemini Pro
- ✅ Alta calidad (768 dims)
- ❌ Requiere API key

**Modelo:** `models/text-embedding-004`

### 3. OpenAI
- ✅ Alta calidad
- ❌ Pago por uso (~$0.02 por 1M tokens)
- ❌ Requiere API key

**Modelos:**
- `text-embedding-3-small` (1536 dims, $0.02/1M)
- `text-embedding-3-large` (3072 dims, $0.13/1M)

## 📈 Validar Tamaño de Chunks

Después de generar chunks, revisa las estadísticas:

```python
import pandas as pd

df = pd.read_parquet("data/chunks.parquet")
df['word_count'] = df['texto'].apply(lambda x: len(str(x).split()))
print(df['word_count'].describe())
```

**Interpretación:**
- **P75 ~800 palabras** → chunk_size=1024 es adecuado ✅
- **P75 >1200 palabras** → considera aumentar chunk_size
- **P75 <500 palabras** → considera reducir chunk_size

## 🔍 Próximos Pasos

- [ ] Implementar `database.py` con ChromaDB
- [ ] Crear servidor MCP con tools obligatorias
- [ ] Implementar agente conversacional
- [ ] Frontend de chat
- [ ] CI/CD con GitHub Actions

## 📝 Notas Técnicas

### Concatenación para Embeddings

El [embedder.py](src/core/embedder.py) concatena `metadata.title + '\n' + texto`:

```python
"Créditos Hipotecarios\nBancolombia ofrece créditos con tasas desde 9%..."
```

Esto mejora la recuperación semántica incluyendo contexto del título.

### Persistencia

Los datos se guardan en formato **Parquet** (comprimido, eficiente):
- `data/chunks.parquet`: Chunks procesados
- `data/embeddings.parquet`: Chunks + embeddings

## 🐛 Troubleshooting

**Error: "No se encontró el archivo de chunks"**
```bash
# Ejecuta primero el pipeline completo
python src/main.py
```

**Error: "API key requerida para Gemini"**
```bash
# Verifica tu .env
echo $GEMINI_API_KEY  # En WSL
type .env             # En Windows CMD
```

**Playwright no funciona en WSL**
```bash
# Instala dependencias del sistema
sudo apt-get update
sudo apt-get install -y libglib2.0-0 libnss3 libnspr4
```

## 📄 Licencia

MIT

---

**Prueba Técnica - Bancolombia · Proceso 59034**
