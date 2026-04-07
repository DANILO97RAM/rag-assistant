# rag-assistant 

En este proyecto se implementa un asistente virtual para el sitio de personas de Bancolombia, utilizando una arquitectura RAG (Retrieval-Augmented Generation) y exponiendo sus capacidades a través de un servidor MCP (Model Context Protocol). El sistema incluye scraping de contenido, procesamiento y limpieza de datos, generación de embeddings, almacenamiento en una base vectorial, y un agente conversacional que responde consultas de los usuarios basándose en la información recuperada.

## Arquitectura y Diseño Modular

src/
├── config/             # Configuración y constantes 
├── core/               # lógica central del negocio
│   ├── scraper.py      # Lógica basada en Playwright
│   ├── processor.py    # Limpieza y Chunking
│   └── embedder.py     # Generación de vectores
├── services/           # Adaptadores externos
│   ├── database.py     # PostgreSQL + pgvector 
│   └── mcp_server.py   # El servidor FastMCP
└── main.py             # Orquestador del pipeline de ingesta

El proyecto sigue una estructura modular que aplica principios de Arquitectura Limpia para garantizar la separación de preocupaciones y la escalabilidad del sistema RAG.

### Organización del Proyecto

src/main.py: Punto de entrada único para el pipeline de datos. Orquesta secuencialmente el scraping, la limpieza, la generación de chunks y la carga vectorial

src/core/: Contiene la lógica de dominio y procesamiento de datos.
* scraper.py: Implementación de Playwright para manejo de contenido dinámico
* cleaner.py: Lógica de normalización y eliminación de ruido HTML
* chunker.py: Estrategia de segmentación recursiva (ADR-006) para optimizar el contexto semántico

src/services/: Adaptadores para servicios externos y protocolos.
* database.py: Gestión de persistencia en PostgreSQL + pgvector
* mcp_server.py: Servidor FastMCP que expone las herramientas obligatorias (search_knowledge_base, list_categories)

src/config/: Centralización de variables de entorno y constantes del sistema

## Flujo de Datos (Pipeline)
La arquitectura está diseñada como un flujo unidireccional:
Adquisición: Crawling de 50+ páginas con navegación BFS y respeto a robots.txt

Procesamiento: Transformación de datos crudos a DataFrames para limpieza y segmentación

Indexación: Generación de embeddings con XXX y almacenamiento vectorial

Exposición: El servidor MCP consume la base de datos para servir al agente conversacional