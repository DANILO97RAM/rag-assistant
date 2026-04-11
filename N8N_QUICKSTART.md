# 🎬 Quick Start: n8n + MCP Bancolombia

Guía rápida para configurar el agente en n8n en 5 minutos.

---

## 🚀 Setup Rápido

### 1. Crear Workflow en n8n

1. Abre n8n: http://localhost:5678
2. Login: `admin` / `admin123`
3. Crear nuevo workflow
4. Nombre: "Bancolombia Knowledge Assistant"

---

### 2. Agregar Nodos

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Webhook   │   →   │  AI Agent   │   →   │  Respond    │
│  (Trigger)  │       │ (MCP Tools) │       │ to Webhook  │
└─────────────┘       └─────────────┘       └─────────────┘
```

#### Nodo 1: Webhook (Trigger)

```yaml
Node: Webhook
Method: POST
Path: bancolombia-assistant
Response Code: 200
```

**Body esperado:**
```json
{
  "query": "¿Qué seguros ofrece Bancolombia?"
}
```

---

#### Nodo 2: AI Agent

```yaml
Node: AI Agent
Model: OpenAI GPT-4o / Anthropic Claude / Google Gemini
Temperature: 0.3
Max Tokens: 1000
```

**System Message (copy-paste):**

```
Eres un asistente virtual experto en productos y servicios de Bancolombia Colombia.

### Herramientas MCP Disponibles

1. **search_knowledge_base** - Búsqueda semántica (USA ESTO PRIMERO SIEMPRE)
   - query: Pregunta del usuario
   - n_results: Cantidad de resultados (5 default)
   - category: Filtro opcional (creditos, seguros, etc)

2. **get_article_by_url** - Recuperar artículo completo
   - url: URL del artículo de Bancolombia

3. **list_categories** - Listar temas disponibles

### Estrategia

1. Para CUALQUIER pregunta → Usa `search_knowledge_base` primero
2. Si similarity_score > 0.7 → Alta confianza
3. Si similarity_score < 0.4 → Pide aclaración
4. SIEMPRE cita fuentes con URLs

### Formato de Respuesta

[Respuesta basada en documentos]

📚 **Fuentes:**
- [Título](URL)

¿Necesitas más detalles?
```

**MCP Configuration:**
```yaml
Type: MCP Client
Server Command: python3
Server Args: /home/danilo97ram/rag-assistant/mcp/main.py
Environment:
  CHROMA_HOST: localhost
  CHROMA_PORT: 8000
```

**User Message:**
```
{{ $json.query }}
```

---

#### Nodo 3: Respond to Webhook

```yaml
Node: Respond to Webhook
Response Code: 200
Content-Type: application/json
```

**Response Body:**
```json
{
  "status": "success",
  "query": "{{ $('Webhook').item.json.query }}",
  "response": "{{ $json.output }}",
  "timestamp": "{{ $now }}"
}
```

---

## 🧪 Probar el Workflow

### Usando curl

```bash
# Test 1: Búsqueda simple
curl -X POST http://localhost:5678/webhook/bancolombia-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué seguros de vida tiene Bancolombia?"}'

# Test 2: Filtrado por categoría
curl -X POST http://localhost:5678/webhook/bancolombia-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Ver todas las categorías disponibles"}'

# Test 3: Pregunta específica
curl -X POST http://localhost:5678/webhook/bancolombia-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Requisitos para crédito hipotecario"}'
```

### Usando Postman/Insomnia

```http
POST http://localhost:5678/webhook/bancolombia-assistant
Content-Type: application/json

{
  "query": "¿Cómo puedo abrir una cuenta de ahorros?"
}
```

---

## 📊 Respuesta Esperada

```json
{
  "status": "success",
  "query": "¿Qué seguros de vida tiene Bancolombia?",
  "response": "Bancolombia ofrece varios seguros de vida:\n\n1. **Seguro de Vida Total:** Protección completa para ti y tu familia con coberturas por fallecimiento, invalidez y enfermedades graves.\n\n2. **Seguro Vida Plus:** Plan flexible con opciones de ahorro e inversión integradas.\n\n📚 **Fuentes:**\n- [Seguros de Vida Bancolombia](https://www.bancolombia.com/personas/seguros/vida)\n- [Protección Personal](https://www.bancolombia.com/personas/seguros/proteccion)\n\n¿Quieres conocer las coberturas de alguno en particular?",
  "timestamp": "2026-04-11T10:30:45Z"
}
```

---

## 🔄 Workflow Avanzado con Conversación

Si quieres mantener contexto de conversación:

```
┌─────────────┐
│   Webhook   │
└──────┬──────┘
       │
       v
┌─────────────────────┐
│ Get Conversation ID │  ← Leer session_id del body
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│ Load Chat History   │  ← Cargar últimos 5 mensajes de Redis/Postgres
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│    AI Agent         │  ← Incluir chat_history en contexto
│   (MCP Tools)       │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Save Message       │  ← Guardar pregunta + respuesta
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Respond Webhook    │
└─────────────────────┘
```

**Body con conversación:**
```json
{
  "session_id": "user_123",
  "query": "¿Y cuánto cuesta?"
}
```

---

## 🎨 Integración con Canales

### Telegram Bot

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Telegram   │   →   │  AI Agent   │   →   │  Send       │
│  Trigger    │       │ (MCP Tools) │       │  Telegram   │
└─────────────┘       └─────────────┘       └─────────────┘
```

### WhatsApp (Twilio)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Webhook    │   →   │  AI Agent   │   →   │  Twilio     │
│ (Twilio)    │       │ (MCP Tools) │       │  Send SMS   │
└─────────────┘       └─────────────┘       └─────────────┘
```

### Web Chat (Socket.IO)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  WebSocket  │   →   │  AI Agent   │   →   │  WebSocket  │
│  Received   │       │ (MCP Tools) │       │  Send       │
└─────────────┘       └─────────────┘       └─────────────┘
```

---

## 🔍 Debugging

### Ver logs del MCP Server

```bash
# En la terminal donde corre n8n, verás logs del MCP:
🔍 Búsqueda ejecutada: 'seguros de vida...' → 5 resultados
📄 Artículo recuperado: https://... → 3 chunks
📁 Categorías listadas: 47 encontradas
```

### Ver ejecuciones en n8n

1. Click en "Executions" (panel izquierdo)
2. Ver cada ejecución con:
   - Input del usuario
   - Tools llamadas
   - Respuestas del MCP
   - Output final

---

## ⚡ Optimizaciones

### 1. Caché de Resultados (Redis)

```
Before AI Agent:
┌─────────────────────┐
│  Check Redis Cache  │  ← Buscar query en cache
└──────┬──────────────┘
       │ (si no existe)
       v
   [AI Agent]
       │
       v
┌─────────────────────┐
│  Save to Redis      │  ← Guardar respuesta (TTL: 1h)
└─────────────────────┘
```

### 2. Rate Limiting

```yaml
Node: Rate Limit
Type: Queue
Max: 10 requests per minute
Strategy: Fixed window
```

### 3. Analytics

Agregar nodo final:
```
┌─────────────────────┐
│  Write Analytics    │  ← Log query, response, timing, user_id
│    (Postgres)       │
└─────────────────────┘
```

---

## 📈 Monitoreo

### Métricas Clave

```javascript
// Nodo: Function (after AI Agent)
const startTime = $('Webhook').item.json.timestamp;
const endTime = Date.now();
const responseTime = endTime - new Date(startTime).getTime();

return {
  query: $('Webhook').item.json.query,
  response_length: $json.output.length,
  response_time_ms: responseTime,
  tools_used: $json.tool_calls?.length || 0,
  success: $json.output ? true : false
};
```

### Dashboard Recomendado (Grafana)

- Total queries por día
- Response time promedio
- Success rate
- Tools más usadas
- Categorías más consultadas

---

## 🆘 Troubleshooting

### Error: "MCP Server not responding"

```bash
# Verificar que el MCP server esté funcionando
cd ~/rag-assistant/mcp
python main.py

# Debería mostrar:
# ✅ ChromaDB conectado exitosamente
```

### Error: "No results found"

```bash
# Verificar que ChromaDB tenga datos
curl http://localhost:9000/stats

# Debería mostrar:
# {"total_documents": 65, ...}
```

### Error: "Connection refused to localhost:8000"

```bash
# Levantar ChromaDB Docker
docker-compose up -d

# Verificar que esté corriendo
docker ps | grep chromadb
```

---

## 🎓 Recursos Adicionales

- **Prompt completo:** Ver `N8N_AGENT_PROMPT.md`
- **API REST docs:** http://localhost:9000/docs
- **Postman collection:** `mcp/Bancolombia_API.postman_collection.json`
- **Docker guide:** `DOCKER_GUIDE.md`

---

**Next Steps:**
1. ✅ Crear workflow básico en n8n
2. ✅ Probar con curl/Postman
3. ⏳ Integrar con Telegram/WhatsApp
4. ⏳ Agregar persistencia de conversaciones
5. ⏳ Implementar analytics dashboard

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-11
<!-- Commented by GitHub Copilot -->
