# rag-assistant

Un asistente virtual para el sitio de personas de Bancolombia basado en arquitectura RAG (Retrieval-Augmented Generation), expuesto mediante servidor MCP (Model Context Protocol). El sistema integra scraping de contenido, procesamiento de datos, generación de embeddings, almacenamiento vectorial y un agente conversacional.

## Requisitos

- **Python**: 3.11 mínimo (probado con Python 3.12)

## Arquitectura

```
src/
├── config/              # Configuración, constantes y logging
│   └── logger.py        # Logging centralizado
├── core/                # Lógica de dominio
│   ├── scraper.py       # Scraping con Playwright
│   ├── cleaner.py       # Normalización de texto
│   ├── chunker.py       # Segmentación de chunks
│   ├── processor.py     # Orquestación limpieza + chunking
│   └── embedder.py      # Generación de embeddings
├── services/            # Adaptadores externos
│   ├── database.py      # PostgreSQL + pgvector
│   └── mcp_server.py    # Servidor FastMCP
└── main.py              # Orquestador del pipeline
```

### Componentes Principales

| Módulo | Responsabilidad |
|--------|-----------------|
| **main.py** | Punto de entrada único; orquesta scraping, limpieza, chunking e indexación |
| **scraper.py** | Crawling BFS de 50+ páginas con renderizado dinámico |
| **cleaner.py** | Normalización y eliminación de ruido HTML |
| **chunker.py** | Segmentación recursiva (ADR-006) para optimizar contexto semántico |
| **database.py** | Persistencia en PostgreSQL + pgvector |
| **mcp_server.py** | Exposición de herramientas (search_knowledge_base, list_categories) |

## Pipeline de Datos

1. **Adquisición**: Crawling concurrente con respeto a robots.txt
2. **Procesamiento**: Transformación a DataFrames para limpieza y segmentación
3. **Indexación**: Generación de embeddings y almacenamiento vectorial
4. **Exposición**: Servidor MCP consume la base de datos

## Ejecución

```bash
# Configurar entorno e instalar dependencias
make setup

# Ejecutar scraping (50 páginas por defecto)
make scraper

# Iniciar pipeline completo
make run
```
