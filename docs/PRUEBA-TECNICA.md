# PRUEBA TÉCNICA — PROCESO DE SELECCIÓN 59034
**Bancolombia · Tecnología e IA TI**
**Fecha límite: Domingo 12 de abril del 2026, 11:59 pm**
**Nivel: Semi Senior · Medellín**

---

## 1. Contexto

Bancolombia busca fortalecer su equipo de Inteligencia Artificial con ingenieros capaces de diseñar, construir y desplegar soluciones de IA generativa n producción. Esta prueba técnica evalúa su capacidad para construir un sistema RAG (Retrieval-Augmented Generation) end-to-end, desde la adquisición de datos hasta la interacción con el usuario final a través de un agente conversacional.

> **Importante:** Esta prueba no busca una solución perfecta ni un producto terminado.
> Busca entender cómo piensa, diseña, implementa y documenta soluciones técnicas.
> Valoramos las decisiones de arquitectura tanto como el código funcional.

---

## 2. Objetivo

Construir un **asistente virtual del Grupo Bancolombia** que responda preguntas sobre productos, servicios y contenido publicado en la sección de personas del sitio web, utilizando una arquitectura RAG con un agente conversacional accesible mediante una interfaz de chat.

---

## 3. Alcance de la Solución

### 3.1. Adquisición de datos (Web Scraping / Crawling)

Implementar un proceso automatizado que:
- Recorra `https://www.bancolombia.com/personas` y descubra los links internos de artículos, productos y páginas informativas.
- Descargue el contenido textual de cada página encontrada.
- Almacene los datos crudos de forma estructurada con metadatos: URL de origen, título, fecha de extracción, categoría.

**Requisitos:**
- Mínimo **50 páginas/artículos** procesados.
- Documentar decisiones sobre: profundidad de crawling, manejo de contenido dinámico (JavaScript rendering) y estrategia de respeto a `robots.txt`.

---

### 3.2. Procesamiento y limpieza de datos

Implementar un pipeline de limpieza que:
- Elimine HTML, navegación, footers, banners y contenido no informativo.
- Extraiga el contenido relevante: texto principal, títulos, subtítulos.
- **Chunking**: aplique una estrategia de segmentación del texto adecuada para recuperación semántica.
  - Justificar: tamaño del chunk, overlap, método de segmentación.
- Genere un dataset limpio y listo para la etapa de embedding.

---

### 3.3. Generación de embeddings y almacenamiento vectorial

Implementar:
- Generación de embeddings a partir del texto limpio usando un modelo (abierto o comercial).
- Almacenamiento en base de datos vectorial: Pinecone, ChromaDB, Weaviate, Qdrant, OpenSearch, pgvector u otra.
- Indexación con metadatos: URL de origen, categoría, etc.

**Justificar:** elección del modelo de embeddings, dimensionalidad, base vectorial y estrategia de indexación.

---

### 3.4. Retrieval y Generación (RAG) — ⚠️ SERVIDOR MCP (OBLIGATORIO)

> El componente de recuperación y generación **DEBE implementarse como un servidor MCP** (Model Context Protocol).

MCP es un estándar abierto que permite exponer capacidades (tools, resources, prompts) de forma que cualquier cliente compatible pueda consumirlas.

#### Tools OBLIGATORIAS del servidor MCP

| Tool | Descripción |
|------|-------------|
| `search_knowledge_base` | Recibe una consulta en lenguaje natural, ejecuta búsqueda semántica contra la base vectorial y retorna los documentos más relevantes con metadatos (URL, título, score de relevancia). |
| `get_article_by_url` | Recibe una URL del sitio de Bancolombia y retorna el contenido completo del artículo indexado correspondiente. |
| `list_categories` | Retorna las categorías disponibles en la base de conocimiento. |

#### Resource OBLIGATORIO del servidor MCP

| Resource URI | Descripción |
|--------------|-------------|
| `knowledge-base://stats` | Expone estadísticas: número de documentos indexados, categorías disponibles, fecha de última actualización, modelo de embeddings utilizado. |

#### Requisitos técnicos del servidor MCP

- **SDK oficial**: `@modelcontextprotocol/sdk` con **FastMCP (Python)** o Java (Spring IA)
- **Transporte**: soporte obligatorio para `stdio`. SSE o Streamable HTTP es deseable pero opcional.
- Validación de parámetros en cada tool con descripciones claras.
- Manejo de errores: base vectorial no disponible, query sin resultados, timeouts.

**Flujo RAG:** búsqueda semántica → reranking opcional → retorno de documentos con fuentes (URLs).

**Modelos aceptados:** Claude, GPT, Gemini, Llama, Mistral, etc. (tier gratuito aceptado).

**Referencias:**
- https://modelcontextprotocol.io
- https://github.com/modelcontextprotocol

---

### 3.5. Agente conversacional (Cliente MCP)

El agente actúa como cliente MCP y debe:
- Conectarse al servidor MCP e invocar las tools según la intención del usuario.
- Mantener **contexto de la conversación**: historial de mensajes.
- Decidir cuándo consultar la base de conocimiento vs. responder directamente.
- Manejar preguntas fuera de alcance.
- **Citar las fuentes (URLs)** retornadas por el servidor MCP en cada respuesta.
- Seguridad para el consumo del agente.
- Manejo de las diferentes tipologías de memoria: **corto, mediano y largo plazo**.

**Framework libre:** LangChain, LangGraph, CrewAI, Autogen, N8N, SDK de Anthropic con tool use, o implementación propia. La conexión con la base de conocimiento **DEBE** ser a través del protocolo MCP.

---

### 3.6. Frontend — Interfaz de chat

Implementar una interfaz de usuario tipo chat que:
- Permita al usuario escribir preguntas y recibir respuestas del agente.
- Muestre el **historial de la conversación**.
- Presente las **fuentes (URLs)** utilizadas para generar cada respuesta.
- Sea funcional y usable.

**Tecnologías aceptadas:** React, Next.js, Vue, Svelte, **Streamlit**, **Gradio** o cualquier framework.

---

## 4. Requisitos No Funcionales

| Requisito | Descripción |
|-----------|-------------|
| **Arquitectura limpia** | Separación de capas, inversión de dependencias, bajo acoplamiento. Se evalúa la estructura del proyecto, no solo que funcione. |
| **Diseño de la solución** | Diagrama de componentes: servicios, bases de datos, APIs, flujos de datos. (draw.io, Excalidraw, Mermaid, etc.) |
| **Documentación** | README.md profesional con descripción, diagrama, instrucciones de instalación, decisiones técnicas y limitaciones. |
| **CI/CD** | Pipeline CI con linting y/o tests al hacer push. Pipeline CD implementado o documentado. (GitHub Actions, GitLab CI, etc.) |
| **Repositorio Git** | Repositorio **público**. Historial de commits incremental (no un solo commit). |
| **Contenerización** | Ejecutable con `docker-compose up`. Dockerfile(s) para cada servicio. |
| **Variables de entorno** | API keys con variables de entorno. Incluir `.env.example` sin valores reales. |

---

## 5. Criterios de Evaluación

| Criterio | Peso | Qué se evalúa |
|----------|------|---------------|
| Diseño y arquitectura | **25%** | Diagrama de componentes, separación de responsabilidades, decisiones justificadas, escalabilidad. |
| Implementación RAG + MCP | **25%** | Pipeline completo funcionando. Servidor MCP con tools, resources y validación. Calidad de respuestas, citación de fuentes, manejo de errores. |
| Agente (cliente MCP) y frontend | **20%** | Agente conectado al MCP, invocación correcta de tools, manejo de contexto conversacional, interfaz de chat usable. |
| Calidad del código | **15%** | Código limpio y modular. Arquitectura limpia implementada. Manejo de errores. Testing unitario en componentes críticos. |
| DevOps y documentación | **15%** | CI/CD funcionando, Docker correcto, README profesional, instrucciones claras, decisiones documentadas. |

---

## 6. Entregables

1. **Repositorio Git público** con código fuente, Dockerfiles y CI/CD.
2. **README.md** completo.
3. **Diagrama de componentes**.
4. **Video demo de 3–5 minutos**: chat en acción con al menos 5 preguntas sobre productos/servicios de Bancolombia, mostrando fuentes.

---

## 7. Restricciones y Aclaraciones

| Punto | Detalle |
|-------|---------|
| Lenguaje | Libre. Python, TypeScript/JavaScript, Java, Go u otro. |
| Costos | Sin costos elevados. Usar tiers gratuitos. |
| **Prohibido** | Entregar solución con datos hardcodeados. **El sistema DEBE hacer retrieval real contra la base vectorial a través del MCP.** |
| Propiedad intelectual | El código es del candidato. |
| IA como herramienta | Puede usar Copilot, Claude, etc. Debe poder explicar cada decisión en entrevista. |

---

## 8. Cronograma

| Hito | Plazo |
|------|-------|
| Envío de la prueba | 1 de abril de 2026 |
| **Fecha límite de entrega** | **Domingo 12 de abril de 2026, 11:59 pm** |
| Revisión técnica | 4 días hábiles después de la entrega |
| Entrevista técnica | Por agendar tras revisión |

---

## 9. Preguntas Frecuentes

**¿Qué profundidad de crawling se espera?**
Mínimo 50 páginas procesadas. No es necesario agotar toda la sección `/personas`.

**¿Es obligatorio el servidor MCP?**
Sí. No se puede usar otra cosa para el RAG. MCP es un requisito obligatorio.

**¿Qué transporte debo usar para el servidor MCP?**
`stdio` es obligatorio. SSE o Streamable HTTP es valorado pero opcional.

**¿Puedo usar un LLM local?**
Sí. Documente requisitos de hardware e incluya alternativa con API.

**¿Se evalúa el diseño visual del frontend?**
No. Streamlit o Gradio son completamente aceptables.

**¿Qué pasa si el web scraping falla en algunas páginas?**
Es esperado. Documente qué páginas fallaron y por qué.
