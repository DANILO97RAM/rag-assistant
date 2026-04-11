# 🔧 Configuración n8n + MCP Server (Docker)

Guía para conectar n8n (en Docker) con el MCP Server de Bancolombia.

---

## ⚠️ Problema Actual

**Error:** "Could not connect to your MCP server - fetch failed"

**Causa:** Configuración incorrecta del transporte y networking Docker.

---

## ✅ Solución: Configuración Correcta en n8n

### Paso 1: Configurar el Nodo MCP Client

En n8n, en el nodo **MCP Client**, configura así:

```yaml
Server Transport: Standard I/O  ← ¡IMPORTANTE! (NO "HTTP Streamable")
Command: python3
Arguments (líneas separadas):
  /home/danilo97ram/rag-assistant/mcp/main.py

Environment Variables:
  CHROMA_HOST: chromadb  ← Nombre del contenedor (NO "localhost")
  CHROMA_PORT: 8000
```

### Paso 2: Actualizar docker-compose.yaml

El MCP necesita acceso al código y al network de ChromaDB. Actualiza tu `docker-compose.yaml`:

```yaml
services:
  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
      - ALLOW_RESET=TRUE
    restart: unless-stopped
    networks:
      - rag-network

  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n
    user: "1000:1000"
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - /home/danilo97ram/rag-assistant:/workspace  ← ¡NUEVO! Montar código
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin123
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - PYTHONPATH=/workspace/src  ← ¡NUEVO! Python path
      - CHROMA_HOST=chromadb       ← ¡NUEVO! ChromaDB hostname
      - CHROMA_PORT=8000           ← ¡NUEVO! ChromaDB port
    restart: unless-stopped
    networks:
      - rag-network
    depends_on:
      - chromadb

networks:
  rag-network:
    driver: bridge

volumes:
  chroma_data:
  n8n_data:
```

### Paso 3: Instalar Dependencias en n8n

El contenedor n8n necesita Python y las dependencias del proyecto:

```bash
# Entrar al contenedor n8n
docker exec -it n8n /bin/sh

# Dentro del contenedor:
apk add --no-cache python3 py3-pip

# Instalar dependencias del proyecto
cd /workspace
pip3 install -r requirements.txt --break-system-packages

# Verificar que funciona
python3 -c "from services.database import ChromaDBService; print('OK')"

# Salir
exit
```

### Paso 4: Reiniciar Docker

```bash
# Detener servicios
docker-compose down

# Levantar con nueva configuración
docker-compose up -d

# Verificar que ambos están en la misma red
docker network inspect rag-assistant_rag-network
```

---

## 🧪 Test Rápido

### Verificar que n8n puede ejecutar el MCP

```bash
# Entrar a n8n
docker exec -it n8n /bin/sh

# Probar que puede conectarse a ChromaDB
ping chromadb -c 2

# Probar que puede ejecutar el MCP server
cd /workspace
python3 mcp/main.py
# Debería mostrar: "✅ ChromaDB conectado exitosamente"
# Ctrl+C para salir

exit
```

---

## 🎯 Configuración Final en n8n UI

### Nodo: MCP Client

**Parameters:**
```
Server Transport: Standard I/O
Command: python3
Arguments:
  - /workspace/mcp/main.py
  
Environment Variables:
  CHROMA_HOST = chromadb
  CHROMA_PORT = 8000
  
Tools to Include: All
```

**¡NO uses `http://localhost:9000`!** Eso es para el API REST, no para MCP.

---

## 🔄 Alternativa Más Simple (SIN Docker para MCP)

Si no quieres modificar el docker-compose, usa el API REST en lugar de MCP:

### Opción B: Usar HTTP Request Nodes (sin MCP)

En lugar de usar MCP Client, usa nodos HTTP Request:

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   Webhook   │   →   │  HTTP Request   │   →   │  AI Agent   │
│  (Trigger)  │       │ (API REST 9000) │       │ (sin MCP)   │
└─────────────┘       └─────────────────┘       └─────────────┘
```

**HTTP Request Node:**
```yaml
Method: POST
URL: http://host.docker.internal:9000/search
Headers:
  Content-Type: application/json
Body:
  {
    "query": "{{ $json.query }}",
    "n_results": 5
  }
```

**Nota:** Usa `host.docker.internal` para acceder al host desde Docker (Windows/Mac). En Linux usa la IP del host.

---

## 📊 Resumen de Diferencias

| Aspecto | MCP Server (stdio) | API REST (HTTP) |
|---------|-------------------|-----------------|
| **Puerto** | N/A (stdio) | 9000 |
| **Transporte** | Standard I/O | HTTP |
| **Comando** | `python3 mcp/main.py` | N/A (ya corriendo) |
| **Desde n8n** | Requiere volumen montado | Solo HTTP request |
| **Tools** | Automáticas (MCP) | Manual (HTTP calls) |

---

## ⚡ Recomendación

Para desarrollo rápido, **usa la Opción B (API REST)** porque:
- ✅ Ya funciona localmente
- ✅ No requiere modificar docker-compose
- ✅ Acceso simple con `host.docker.internal`

Para producción con AI Agent natives, usa **MCP con docker-compose actualizado**.

---

## 🆘 Troubleshooting

### Error: "python3: command not found" en n8n

```bash
docker exec -it n8n apk add python3 py3-pip
```

### Error: "ModuleNotFoundError: No module named 'services'"

```bash
docker exec -it n8n pip3 install -r /workspace/requirements.txt --break-system-packages
```

### Error: "Connection refused to chromadb"

Verificar que están en la misma red:
```bash
docker network inspect rag-assistant_rag-network
```

### n8n reinicia y pierde dependencias Python

Crear Dockerfile customizado para n8n con dependencias pre-instaladas.

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-11
<!-- Commented by GitHub Copilot -->
