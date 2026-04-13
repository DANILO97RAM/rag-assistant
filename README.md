# RAG Assistant - Bancolombia

**Prueba Técnica - Proceso de Selección 59034**

Sistema RAG (Retrieval-Augmented Generation) completo para consultas sobre productos y servicios de Bancolombia. Implementa web scraping, procesamiento de texto, base de datos vectorial, servidor MCP, agente conversacional y frontend de chat.

---

## 🎯 ¿Qué se implementó?

✅ **Requisito 3.1 - Web Scraping**: 50 páginas scrapeadas con Playwright (BFS, profundidad 2)  
✅ **Requisito 3.2 - Procesamiento de datos**: Limpieza HTML, chunking semántico (1024 tokens, overlap 128)  
✅ **Requisito 3.3 - Embeddings**: Sentence Transformers local + ChromaDB vectorial (94 documentos, 47 categorías)  
✅ **Requisito 3.4 - Servidor MCP**: FastMCP con 3 tools + 1 resource (stdio + API REST wrapper)  
✅ **Requisito 3.5 - Agente conversacional**: Cliente MCP con razonamiento sobre intención del usuario  
✅ **Requisito 3.6 - Frontend**: Streamlit chat con historial y citación de fuentes  
✅ **Requisito 4.0 - CI/CD**: GitHub Actions con lint, tests y validación de estructura  
✅ **Requisito 4.0 - Diagrama**: Ver [docs/DIAGRAMA_ARQUITECTURA.png](docs/DIAGRAMA_ARQUITECTURA.png) 
✅ **Requisito 4.0 - Docker**: `docker-compose.yml` para ChromaDB + scripts de automatización

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Lenguaje** | Python 3.12.3 |
| **Web Scraping** | Playwright 1.49.1 (BFS crawling, JavaScript rendering) |
| **Procesamiento de texto** | LangChain 0.3.17, BeautifulSoup4 4.12.3 |
| **Chunking** | RecursiveCharacterTextSplitter (1024 tokens, overlap 128) |
| **Embeddings** | Sentence Transformers 3.3.1 (`all-MiniLM-L6-v2`, 384D) vía **Hugging Face local** |
| **Base vectorial** | ChromaDB 1.5.7 (Docker, persistencia local, cosine similarity) |
| **Servidor MCP** | FastMCP 3.2.3 (stdio + wrapper API REST FastAPI) |
| **Agente** | Cliente MCP custom (razonamiento sobre intención) |
| **Frontend** | Streamlit 1.30+ (puerto 8501) |
| **Orquestación** | Docker Compose, Makefile |
| **CI/CD** | GitHub Actions (lint, tests, validación) |
| **Testing** | pytest 9.0.3 |

**Nota:** El proyecto usa **Hugging Face local** para embeddings sin API keys, pero incluye soporte alternativo para **Google Gemini** (configurar `GEMINI_API_KEY`).

---

## 📁 Arquitectura del Proyecto

```
rag-assistant/
├── .github/
│   └── workflows/
│       └── ci.yml                   # Pipeline CI/CD (lint, tests, validación)
├── agent/
│   ├── conversational_agent.py      # Cliente MCP con razonamiento
│   ├── __init__.py                  # Módulo exportable
│   └── README.md                    # Documentación del agente
├── front/
│   ├── app.py                       # Frontend Streamlit (chat único)
│   └── README.md                    # Guía de uso del frontend
├── mcp/
│   ├── main.py                      # Servidor MCP (FastMCP + stdio)
│   ├── api_server.py                # API REST wrapper (puerto 8001)
│   ├── test_server.py               # Tests del servidor MCP
│   └── README.md                    # Documentación MCP
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
│   │   └── database.py              # ChromaDB service
│   └── main.py                      # CLI principal (pipeline ETL)
├── tests/
│   ├── test_chromadb.py             # Tests unitarios ChromaDB
│   └── test_realistic_queries.py    # Validación con queries
├── scripts/
│   └── analyze_content.py           # Análisis de contenido scrapeado
├── data/ (Nota: Estos archivos se generan al ejecutar el pipeline ETL)
│   ├── scraped_pages.parquet        # 50 páginas (raw)
│   ├── chunks.parquet               # 94 chunks procesados
│   ├── embeddings_sentence-transformers.parquet  # 94 vectores 384
│   └── chroma_db/                   # Persistencia ChromaDB
├── docs/
│   ├── DIAGRAMA_ARQUITECTURA.png    # Diagrama visual arquitectura
│   ├── ARQUITECTURA_MCP.md          # Justificación técnica MCP
│   └── prueba-tecnica.md            # Especificación del proyecto
├── docker-compose.yml               # ChromaDB container (puerto 8000)
├── requirements.txt                 # Dependencias Python
├── Makefile                         # Comandos de automatización
└── README.md                        # Este archivo
```

---

## Inicio Rápido

### Prerrequisitos
- Ubuntu 20.04+ / Windows 10+ con WSL
- Python 3.11+ (recomendado 3.12.3)
- Docker y Docker Compose
- 3GB RAM mínimo

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/DANILO97RAM/rag-assistant.git
cd rag-assistant

# Instalar dependencias
make setup

# Activar entorno virtual
source venv/bin/activate
```

### Ejecución

#### Opción 1: Hugging Face Local (sin API key)
```bash
# Pipeline completo (scraping → limpieza → embeddings → indexación)
make etl

# Levantar servicios
make docker-up        # ChromaDB (puerto 8000)
make mcp-up          # Servidor MCP + API REST (puerto 8001)
make frontend-up     # Frontend Streamlit (puerto 8501)
```

#### Opción 2: Google Gemini (requiere API key)
```bash
# Configurar API key
export GEMINI_API_KEY=your_api_key_here

# Pipeline con Gemini
make etl-gemini

# Levantar servicios (igual que opción 1)
make docker-up && make mcp-up && make frontend-up
```
Nota: Si por alguna razon se baja el mcp, se debe volver a indexar el contenido, ya que el servidor MCP no tiene persistencia de datos. Para ello ejecutar la indexación manualmente: **make db-index**

```bash
**Acceder al chat:** `http://localhost:8501`
```
---

## 📐 Diseño de la Solución

**Diagrama de arquitectura:**
- [docs/DIAGRAMA_ARQUITECTURA.png](docs/DIAGRAMA_ARQUITECTURA.png) - Imagen estática

**Documentación técnica:**
- [docs/ARQUITECTURA_MCP.md](docs/ARQUITECTURA_MCP.md) - Justificación del enfoque MCP (stdio + wrapper HTTP)
- [agent/README.md](agent/README.md) - Agente conversacional y razonamiento
- [front/README.md](front/README.md) - Frontend Streamlit y modos de consulta
- [mcp/README.md](mcp/README.md) - Servidor MCP (tools, resources, testing)

---

## 🧪 Testing

El proyecto incluye tests automatizados en `tests/`:

```bash
# Tests unitarios de ChromaDB
pytest tests/test_chromadb.py -v
```

**Tests disponibles:**
- `test_chromadb.py` - Validación de base vectorial (creación, indexación, búsqueda, filtros)
- `test_realistic_queries.py` - Evaluación con preguntas reales de usuarios

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
- ChromaDB por la base de datos vectorial, cosita bien hecha, rápida, eficiente, fácil de usar y con un nombre genial.
