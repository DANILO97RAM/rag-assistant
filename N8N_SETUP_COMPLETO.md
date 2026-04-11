# ⚡ Configuración Rápida: n8n + MCP en Docker

**Problema resuelto:** n8n (Docker) no puede conectarse al MCP server local.

**Solución:** Configurar n8n con acceso al código del proyecto y usar transporte `stdio`.

---

## 🚀 Pasos de Configuración (5 minutos)

### 1. Detener y Limpiar Docker

```bash
docker-compose down
```

### 2. Levantar con Nueva Configuración

El `docker-compose.yaml` ya está actualizado con:
- ✅ Volumen montado: `- .:/workspace`
- ✅ Variables de entorno para ChromaDB
- ✅ Dependencia de chromadb

```bash
docker-compose up -d
```

**Deberías ver:**
```
Creating chromadb ... done
Creating n8n      ... done
```

### 3. Instalar Dependencias Python en n8n

```bash
make n8n-setup
```

Este comando instala:
- Python 3
- chromadb==0.5.7
- sentence-transformers==3.0.0
- fastmcp==0.2.1
- python-dotenv
- pandas, numpy

**Tiempo:** ~2-3 minutos

### 4. Verificar que Funciona

```bash
# Test 1: Verificar que n8n puede acceder a ChromaDB
docker exec n8n ping chromadb -c 2

# Test 2: Verificar que puede ejecutar el MCP
docker exec n8n python3 /workspace/mcp/main.py
# Debería mostrar: "✅ ChromaDB conectado exitosamente"
# Ctrl+C para salir
```

---

## 📝 Configuración en n8n UI

### 1. Acceder a n8n

```
URL: http://localhost:5678
Usuario: admin
Password: admin123
```

### 2. Crear Workflow

1. Crear nuevo workflow
2. Agregar nodo **Webhook** (trigger)
3. Agregar nodo **AI Agent**
4. En AI Agent, agregar **MCP Client**

### 3. Configurar MCP Client

**¡IMPORTANTE!** Cambia de "HTTP Streamable" a "Standard I/O":

```yaml
Server Transport: Standard I/O  ← ¡Cambiar aquí!

Command: python3

Arguments (una por línea):
/workspace/mcp/main.py

Environment Variables (click "Add Environment Variable"):
Name: CHROMA_HOST    Value: chromadb
Name: CHROMA_PORT    Value: 8000

Tools to Include: All
```

### 4. Configurar AI Agent

**System Message** (copy-paste del archivo `N8N_PROMPT_MINIMAL.md`):

```
Eres un asistente virtual experto en productos y servicios de Bancolombia Colombia.

## Tools MCP Disponibles

1. **search_knowledge_base** (USA PRIMERO SIEMPRE)
   - query (str): Pregunta en lenguaje natural
   - n_results (int, opcional): 1-10, default 5
   - category (str, opcional): Filtrar por categoría

2. **get_article_by_url**
   - url (str): URL completa de Bancolombia

3. **list_categories** (sin parámetros)

## Estrategia

1. Para CUALQUIER consulta → Usa search_knowledge_base primero
2. SIEMPRE cita fuentes con URLs
3. NO inventes información

## Formato de Respuesta

[Respuesta basada en documentos]

📚 **Fuentes:**
- [Título](URL)

¿Necesitas más detalles?
```

**Model Settings:**
- Model: GPT-4o / Claude Sonnet / Gemini Pro
- Temperature: 0.3
- Max Tokens: 1000

**User Message:**
```
{{ $json.query }}
```

### 5. Agregar Nodo de Respuesta

Agregar **Respond to Webhook**:

```yaml
Response Code: 200
Content-Type: application/json

Response Body:
{
  "status": "success",
  "response": "{{ $json.output }}"
}
```

### 6. Guardar y Activar Workflow

1. Click **Save** (Ctrl+S)
2. Click **Active** (toggle ON)
3. Copiar URL del webhook

---

## 🧪 Probar el Workflow

### Desde la terminal

```bash
# Obtener la URL del webhook desde n8n
# Ejemplo: http://localhost:5678/webhook/bancolombia-assistant

curl -X POST http://localhost:5678/webhook/tu-path-aqui \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué seguros de vida tiene Bancolombia?"}'
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "response": "Bancolombia ofrece seguros de vida como:\n\n1. Seguro de Vida Total: ...\n\n📚 Fuentes:\n- [Seguros](https://...)"
}
```

---

## ✅ Checklist de Verificación

Antes de usar en producción, verifica:

- [ ] `docker ps` muestra chromadb y n8n corriendo
- [ ] `make n8n-setup` completó sin errores
- [ ] `docker exec n8n python3 /workspace/mcp/main.py` funciona
- [ ] n8n MCP Client configurado con "Standard I/O"
- [ ] Variables de entorno `CHROMA_HOST=chromadb` y `CHROMA_PORT=8000`
- [ ] Test curl retorna respuesta con fuentes citadas

---

## 🔍 Troubleshooting Común

### Error: "python3: not found"

```bash
docker exec n8n apk add python3 py3-pip
```

### Error: "ModuleNotFoundError: No module named 'chromadb'"

```bash
make n8n-setup
```

### Error: "Cannot connect to chromadb"

Verificar que están en la misma red:
```bash
docker network inspect rag-assistant_rag-network | grep -A 5 -E "chromadb|n8n"
```

Verificar variables de entorno en n8n:
```bash
docker exec n8n env | grep CHROMA
```

### n8n no encuentra el archivo `/workspace/mcp/main.py`

Verificar que el volumen está montado:
```bash
docker exec n8n ls -la /workspace/mcp/
```

Si no existe, reiniciar Docker:
```bash
docker-compose down
docker-compose up -d
```

### MCP tools no aparecen en n8n

1. Asegúrate de seleccionar "Standard I/O" (NO "HTTP Streamable")
2. Verifica que el comando y argumentos son correctos
3. Revisa logs de n8n: `docker logs n8n -f`

---

## 📊 Arquitectura Final

```
┌─────────────────────────────────────────────────┐
│              Docker Network (rag-network)       │
│                                                 │
│  ┌──────────┐         ┌──────────┐             │
│  │ ChromaDB │ ←────── │   n8n    │             │
│  │ :8000    │         │ :5678    │             │
│  └──────────┘         └─────┬────┘             │
│                             │                   │
│                        Ejecuta MCP              │
│                        via stdio                │
│                             │                   │
│                     ┌───────▼────────┐          │
│                     │  /workspace/   │          │
│                     │   mcp/main.py  │          │
│                     └────────────────┘          │
└─────────────────────────────────────────────────┘
          │                           │
          │                           │
     puerto 8000                  puerto 5678
          │                           │
          ▼                           ▼
    [localhost:8000]          [localhost:5678]
    (ChromaDB API)             (n8n UI)
```

---

## 🎯 Comandos Útiles

```bash
# Ver logs de n8n
make n8n-logs

# Reinstalar dependencias
make n8n-setup

# Ver estado de contenedores
make docker-status

# Reiniciar todo
make docker-restart

# Test completo del stack
make full-pipeline  # Indexar datos
make api_server     # Iniciar API REST
make n8n-logs       # Monitorear n8n
```

---

**¡Listo!** 🎉 Ahora tienes n8n funcionando con el MCP server de Bancolombia.

**Next Steps:**
- Probar con diferentes queries
- Integrar con Telegram/WhatsApp
- Agregar persistencia de conversaciones
- Implementar analytics

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-11

