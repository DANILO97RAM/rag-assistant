# 🔧 Fix Setup - Comandos de Reparación

## Problema 1: Mismatch Chunks vs Embeddings ❌

**Error:** `Mismatch: 65 chunks vs 94 embeddings`

**Causa:** Los embeddings son de una ejecución anterior con más chunks.

**Solución:** Regenerar embeddings después del scraping.

---

## Problema 2: n8n Permisos ❌

**Error:** `EACCES: permission denied, open '/home/node/.n8n/config'`

**Causa:** El volumen Docker no tiene permisos correctos.

**Solución:** Usar named volume y configurar user correcto.

---

## 🚀 Comandos de Reparación

### Paso 1: Limpiar Docker y Volúmenes

```bash
# Detener servicios y limpiar volúmenes corruptos
docker compose down -v

# Limpiar directorio n8n local (si existe)
rm -rf n8n_data/
```

### Paso 2: Levantar Docker con Configuración Corregida

```bash
# Levantar servicios (n8n ahora usa named volume)
docker compose up -d

# Verificar que ambos estén corriendo
docker ps
```

**Deberías ver:**
```
CONTAINER ID   IMAGE              STATUS    PORTS
xxxxxxxx       chromadb/chroma    Up        0.0.0.0:8000->8000/tcp
xxxxxxxx       n8n:latest         Up        0.0.0.0:5678->5678/tcp
```

### Paso 3: Pipeline Completo Automatizado

```bash
# Opción A: Comando único que hace TODO
make full-pipeline
```

**Esto ejecuta:**
1. ✅ Scraping (--force-scrape para forzar nueva ejecución)
2. ✅ Generación de embeddings (sentence-transformers)
3. ✅ Indexación en ChromaDB Docker (--reset-chromadb)

**Opción B: Comandos manuales (paso a paso)**

```bash
# 1. Scraping
make main-force

# 2. Embeddings
make generate-embeddings-sentence

# 3. Indexar en ChromaDB
make db_reset
```

### Paso 4: Verificar n8n

```bash
# Abrir navegador
http://localhost:5678

# Login:
# Usuario: admin
# Password: admin123
```

Si n8n sigue sin funcionar, ver logs:

```bash
make docker-logs
# o
docker logs n8n -f
```

---

## 📊 Verificación Final

```bash
# Ver estado de servicios
make docker-status

# Debería mostrar:
# chromadb: Up
# n8n: Up
```

---

## 🔄 Flujo Correcto de Trabajo

De ahora en adelante, usa este flujo:

```bash
# 1. Levantar Docker primero
make docker-up

# 2. Pipeline completo (scraping + embeddings + indexación)
make full-pipeline

# 3. Iniciar API REST
make api_server
```

---

## 🆘 Si n8n Sigue Fallando

### Opción 1: Ver logs detallados

```bash
docker logs n8n --tail 100
```

### Opción 2: Entrar al contenedor

```bash
docker exec -it n8n /bin/sh

# Dentro del contenedor, verificar permisos:
ls -la /home/node/.n8n
whoami
id
```

### Opción 3: Reiniciar completamente

```bash
# Limpiar TODO
make docker-clean

# Levantar de nuevo
make docker-up

# Esperar 30 segundos
sleep 30

# Probar acceso
curl http://localhost:5678/healthz
```

---

## 📈 Nuevos Comandos Makefile

| Comando | Descripción |
|---------|-------------|
| `make full-pipeline` | ✨ **NUEVO** - Scraping + Embeddings + ChromaDB |
| `make docker-restart` | ✨ **NUEVO** - Reiniciar servicios Docker |
| `make docker-logs` | ✨ **NUEVO** - Ver logs en tiempo real |
| `make docker-status` | ✨ **NUEVO** - Estado de contenedores |
| `make docker-clean` | ✨ **NUEVO** - Limpiar TODO (⚠️ borra datos) |

---

## ✅ Checklist de Verificación

- [ ] `docker ps` muestra chromadb y n8n corriendo
- [ ] `curl http://localhost:8000/api/v2/heartbeat` responde OK
- [ ] `curl http://localhost:5678/healthz` responde OK
- [ ] `make full-pipeline` completa sin errores
- [ ] ChromaDB tiene 65 documentos indexados
- [ ] n8n UI accesible en http://localhost:5678

---

**Autor:** Danilo Gómez  
**Fecha:** 2026-04-11  
**Versión:** 1.0.0

