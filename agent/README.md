# Agente Conversacional

Cliente MCP que consume el servidor MCP via API REST y actúa como agente conversacional inteligente.

---

## Características

- Actúa como cliente del servidor MCP
- Razona sobre qué tool invocar según la intención del usuario
- Mantiene memoria conversacional en tres niveles
- Decide cuándo consultar la base vs responder directamente
- Cita fuentes automáticamente
- Maneja preguntas fuera de alcance

---

## Memoria Conversacional

### 1. Corto plazo
- Últimos 5 turnos de conversación
- Permite referencias: "lo anterior", "ese tema"

### 2. Mediano plazo
- Temas discutidos en la sesión actual
- Categorías mencionadas

### 3. Largo plazo
- Base de conocimiento en ChromaDB
- 94 documentos indexados
- Acceso via tools MCP

---

## Tools MCP Consumidas

El agente invoca las 3 tools del servidor MCP via API REST:

### 1. search_knowledge_base
- Endpoint: `POST /search`
- Uso: Búsqueda semántica en la base de conocimiento
- Decisión: Cuando el usuario hace una pregunta general

### 2. get_article_by_url
- Endpoint: `GET /article`
- Uso: Recuperar contenido completo de un artículo
- Decisión: Cuando el usuario proporciona una URL

### 3. list_categories
- Endpoint: `GET /categories`
- Uso: Listar categorías disponibles
- Decisión: Cuando el usuario pregunta por temas o categorías

### Resource: knowledge-base://stats
- Endpoint: `GET /stats`
- Uso: Estadísticas de la base de conocimiento
- Decisión: Cuando el usuario pregunta por métricas

---

## Uso

### Como CLI Standalone

```bash
# Levantar API REST del servidor MCP
make mcp-up

# Ejecutar agente
python agent/conversational_agent.py

# O con Makefile
make agent
```

**Salida:**
```
============================================================
Asistente Virtual Bancolombia
============================================================
Cliente MCP - Agente Conversacional
Escribe 'salir' para terminar

Tu: ¿Qué seguros ofrece Bancolombia?

[Procesando...]

Asistente:

Encontré 3 documentos relevantes:

1. Bancolombia Corresponsal Bancario (Score: 0.638)
   Categoría: corresponsal-bancario
   Bancolombia Corresponsal Bancario Personas Productos...
   Fuente: https://www.bancolombia.com/personas/...

...
```

### Como Librería Python

```python
from agent.conversational_agent import BancolombiaAgent

# Inicializar agente
agent = BancolombiaAgent(api_url="http://localhost:8001")

# Hacer pregunta
respuesta = agent.ask("¿Qué seguros ofrece Bancolombia?", n_results=3)

# Procesar respuesta
if respuesta.get("success"):
    for doc in respuesta["documents"]:
        print(f"- {doc['title']} (score: {doc['similarity_score']})")
        print(f"  URL: {doc['url']}")
```

---

## Flujo de Razonamiento

El agente sigue este proceso para cada pregunta:

```
1. Analizar intención del usuario
   ├─ ¿Contiene URL? → Intención: "url"
   ├─ ¿Pregunta por categorías? → Intención: "categorias"
   ├─ ¿Pregunta por estadísticas? → Intención: "estadisticas"
   ├─ ¿Referencia al contexto previo? → Intención: "contexto"
   └─ Por defecto → Intención: "busqueda"

2. Decidir qué tool MCP invocar
   ├─ Intención "url" → get_article_by_url
   ├─ Intención "categorias" → list_categories
   ├─ Intención "estadisticas" → GET /stats
   └─ Intención "busqueda" → search_knowledge_base

3. Invocar tool via API REST
   └─ POST /search, GET /article, GET /categories, GET /stats

4. Formatear respuesta con fuentes
   └─ Incluir URLs, scores, categorías

5. Actualizar memoria conversacional
   ├─ Guardar en historial corto plazo
   └─ Actualizar temas discutidos
```

---

## Ejemplos de Interacción

### Búsqueda semántica

```
Tu: ¿Qué seguros ofrece Bancolombia?

Asistente:
Encontré 3 documentos relevantes:
1. Bancolombia Corresponsal Bancario (Score: 0.64)
   ...
```

### Consulta por URL

```
Tu: Dame información de https://www.bancolombia.com/personas/creditos

Asistente:
Artículo: Créditos Bancolombia
Categoría: creditos
Total chunks: 2
...
```

### Listar categorías

```
Tu: ¿Qué categorías tienes?

Asistente:
Categorías disponibles (47):
1. a-la-mano
2. ahorro
3. banco
...
```

### Consulta de contexto

```
Tu: ¿Qué seguros ofrece Bancolombia?
Asistente: [Muestra 3 seguros]

Tu: Dame más detalles del primero

Asistente: [Usa contexto previo para entender "del primero"]
```

---

## Arquitectura

```
Usuario
  ↓
Agent CLI / Frontend
  ↓
BancolombiaAgent (Razonamiento + Memoria)
  ↓
API REST (puerto 8001)
  ↓
Servidor MCP
  ↓
ChromaDB (94 documentos)
```

---

## Manejo de Errores

### API no disponible

```python
{
    "error": True,
    "message": "Error al consultar el servidor MCP: Connection refused",
    "suggestion": "Verifica que el API REST esté ejecutándose (make mcp-up)"
}
```

### Sin resultados

```python
{
    "tool": "search_knowledge_base",
    "success": True,
    "total_results": 0,
    "documents": []
}
```

### URL inválida

```python
{
    "tool": "get_article_by_url",
    "success": False,
    "error": "No se encontró artículo para la URL: ..."
}
```

---

## Testing

```bash
# Test básico
python agent/conversational_agent.py

Tu: ¿Qué seguros hay?
# Debe retornar documentos con fuentes

Tu: salir
```

---

## Integración con Frontend

El frontend Streamlit puede importar el agente:

```python
# front/app.py
from agent.conversational_agent import BancolombiaAgent

agent = BancolombiaAgent()

# En lugar de requests.post(...)
respuesta = agent.ask(user_input, n_results=n_results)
```