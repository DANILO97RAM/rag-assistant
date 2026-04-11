# 🐳 Docker Compose - RAG Assistant

Servicios containerizados para el proyecto RAG Assistant de Bancolombia.

---

## 📦 Servicios Incluidos

### 1. **ChromaDB** (Puerto 8000)
Base de datos vectorial para embeddings y búsqueda semántica.

- **Imagen:** `chromadb/chroma:latest`
- **Puerto:** 8000
- **Volumen:** `./chroma_data` → persistencia de datos
- **Propósito:** Almacenar y buscar vectores de 384 dimensiones

### 2. **n8n** (Puerto 5678)
Plataforma de automatización de workflows (self-hosted).

- **Imagen:** `docker.n8n.io/n8nio/n8n:latest`
- **Puerto:** 5678
- **Volumen:** `./n8n_data` → persistencia de workflows
- **Credenciales por defecto:**
  - Usuario: `admin`
  - Contraseña: `admin123`
- **Propósito:** Automatizar procesos, integrar APIs, crear workflows

---

## 🚀 Uso Rápido

### Iniciar Todos los Servicios

```bash
docker-compose up -d
```

**Salida esperada:**
```
Creating network "rag-assistant_rag-network" with driver "bridge"
Creating chromadb ... done
Creating n8n      ... done
```

### Verificar Estado

```bash
docker-compose ps
```

**Deberías ver:**
```
  Name                Command               State           Ports
------------------------------------------------------------------------
chromadb   uvicorn chromadb.app:app ...   Up      0.0.0.0:8000->8000/tcp
n8n        tini -- /docker-entrypoin ...   Up      0.0.0.0:5678->5678/tcp
```

### Detener Servicios

```bash
docker-compose down
```

### Detener y Eliminar Volúmenes

```bash
docker-compose down -v
```

---

## 🔗 Acceso a Servicios

### ChromaDB API
```
http://localhost:8000
```

**Test rápido:**
```bash
curl http://localhost:8000/api/v1/heartbeat
```

### n8n UI
```
http://localhost:5678
```

**Credenciales:**
- Usuario: `admin`
- Contraseña: `admin123`

---

## 📊 Volúmenes de Datos

Los datos se persisten en:

```
rag-assistant/
├── chroma_data/          # Base de datos ChromaDB
│   └── chroma/
└── n8n_data/             # Workflows y configuración n8n
    ├── .n8n/
    └── workflows/
```

⚠️ **Importante:** Estos directorios están en `.gitignore` y NO se suben al repositorio.

---

## 🌐 Red Docker

Todos los servicios están en la red `rag-network`:

- **Comunicación interna:** Los containers pueden comunicarse entre sí
- **ChromaDB desde n8n:** `http://chromadb:8000`
- **API REST desde n8n:** `http://host.docker.internal:9000`

---

## 🔧 Configuración Avanzada

### Cambiar Credenciales n8n

Editar en `docker-compose.yaml`:

```yaml
environment:
  - N8N_BASIC_AUTH_USER=tu_usuario
  - N8N_BASIC_AUTH_PASSWORD=tu_password_seguro
```

Luego:
```bash
docker-compose up -d --force-recreate n8n
```

### Cambiar Puertos

Si tienes conflictos de puertos:

```yaml
services:
  chromadb:
    ports:
      - "8001:8000"  # Cambia el puerto externo
```

### Recursos de Memoria

Limitar memoria para n8n:

```yaml
n8n:
  deploy:
    resources:
      limits:
        memory: 1G
```

---

## 🧪 Testing ChromaDB desde Python

```python
import chromadb

# Conectar a ChromaDB Docker
client = chromadb.HttpClient(host="localhost", port=8000)

# Heartbeat
client.heartbeat()  # Devuelve timestamp si funciona

# Listar colecciones
collections = client.list_collections()
print(f"Colecciones: {len(collections)}")
```

---

## 🔄 Workflows n8n Útiles

### 1. Indexar Documentos Automáticamente

Crear workflow en n8n que:
1. Detecta nuevos archbos en carpeta
2. Procesa con ETL pipeline
3. Indexa en ChromaDB

### 2. API Webhook para Búsquedas

1. Webhook trigger (`/webhook/search`)
2. HTTP Request a API REST (puerto 9000)
3. Formatear respuesta

### 3. Backup Automático ChromaDB

1. Schedule trigger (diario)
2. Exec command: `docker exec chromadb ...`
3. Upload a S3/Drive

---

## 🐛 Troubleshooting

### Error: "Port 8000 already in use"

```bash
# Ver qué está usando el puerto
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Cambiar puerto en docker-compose.yaml
ports:
  - "8001:8000"
```

### Error: "Cannot connect to Docker daemon"

```bash
# Verificar Docker está corriendo
docker ps

# Si no, iniciar Docker Desktop o servicio
sudo systemctl start docker  # Linux
```

### ChromaDB vacío después de reiniciar

Asegúrate de que los volúmenes estén mapeados:

```bash
docker-compose down
docker volume ls  # Ver volúmenes
docker-compose up -d  # Recrear con volúmenes
```

### n8n muestra error de autenticación

Verificar variables de entorno:

```bash
docker-compose exec n8n env | grep N8N_BASIC_AUTH
```

---

## 📚 Documentación Oficial

- **ChromaDB:** https://docs.trychroma.com/
- **n8n:** https://docs.n8n.io/
- **Docker Compose:** https://docs.docker.com/compose/

---

## 🔗 Integración con el Proyecto

### Flujo Completo

```
1. Scraping (Playwright)
   ↓
2. Procesamiento ETL (src/main.py)
   ↓
3. Embeddings (Sentence Transformers)
   ↓
4. ChromaDB Docker (puerto 8000) ← Indexación
   ↓
5. API REST (puerto 9000) ← Búsquedas
   ↓
6. n8n Workflows ← Automatización
```

### Ejemplo: Indexar Datos

```bash
# 1. Iniciar Docker
docker-compose up -d

# 2. Ejecutar ETL e indexar en ChromaDB Docker
python src/main.py --index-chromadb --reset-chromadb

# 3. Iniciar API REST
cd mcp && python api_server.py

# 4. Configurar workflow en n8n
open http://localhost:5678
```

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-10
<!-- Commented by GitHub Copilot -->
