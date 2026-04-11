# 🔧 Troubleshooting: ChromaDB Collection Not Found

Error común cuando ChromaDB no tiene datos indexados.

---

## ❌ Error

```
ERROR:__main__:❌ Error en búsqueda: Collection [UUID] does not exist.
INFO:     127.0.0.1:44352 - "POST /search HTTP/1.1" 500 Internal Server Error
```

---

## 🔍 Por Qué Sucedió

### Causa #1: ChromaDB Vacío (MÁS COMÚN)

**Síntoma:** Acabas de levantar Docker o ejecutaste `docker-compose down -v`

**Razón:** 
- ChromaDB Docker se reinició sin datos
- El flag `-v` elimina TODOS los volúmenes (incluyendo datos)
- Nunca se indexaron los datos

**Verificar:**
```bash
curl http://localhost:9000/stats
# Si muestra "total_documents": 0 → Este es el problema
```

**Solución:**
```bash
# Re-indexar desde cero
make full-pipeline

# Espera 2-3 minutos
# Verifica: curl http://localhost:9000/stats
```

---

### Causa #2: Volumen No Mapeado

**Síntoma:** Cada vez que reinicias Docker, pierdes los datos

**Razón:** El volumen de Docker no está correctamente configurado

**Verificar:**
```bash
# Ver configuración actual
cat docker-compose.yaml | grep -A 10 chromadb

# Debería mostrar:
# volumes:
#   - ./chroma_data:/chroma/chroma
```

**Solución:**
```bash
# Verificar que existe el directorio
ls -la chroma_data/

# Si no existe o está vacío:
make full-pipeline
```

---

### Causa #3: Paths Incorrectos en Código

**Síntoma:** Error al conectar desde Python local

**Razón:** El código está usando rutas locales en lugar de Docker

**Verificar:**
```python
# En database.py, línea ~40
# ✅ CORRECTO (Docker):
db = ChromaDBService(use_local=False)  # Usa HttpClient

# ❌ INCORRECTO (local):
db = ChromaDBService(use_local=True, persist_directory="data/chroma_db")
```

**Solución:**
- Asegúrate de usar `use_local=False` en producción
- Verifica que `.env` tenga: `CHROMA_HOST=localhost` y `CHROMA_PORT=8000`

---

## ✅ Solución Paso a Paso

### 1. Verificar Estado Actual

```bash
# Estado de Docker
docker ps | grep chromadb
# Debería mostrar: chromadb ... Up ...

# Estado de ChromaDB
curl http://localhost:9000/stats | python3 -m json.tool
# Debería mostrar total_documents > 0

# Archivos de datos
ls -lh chroma_data/
# Debería mostrar archivos .bin, .parquet
```

### 2. Si ChromaDB Está Vacío

```bash
# Opción A: Pipeline completo (scraping + embeddings + indexación)
make full-pipeline

# Opción B: Solo re-indexar (si ya tienes chunks/embeddings)
make db_reset
```

### 3. Si Perdiste Datos Permanentemente

```bash
# Restaurar último backup (si existe)
make restore

# O crear desde cero
make full-pipeline
```

### 4. Verificar que Funcionó

```bash
# 1. Ver estadísticas
curl http://localhost:9000/stats

# Debería mostrar:
# {
#   "total_documents": 65,
#   "total_categories": 47,
#   "collection_name": "bancolombia_knowledge"
# }

# 2. Probar búsqueda
curl -X POST http://localhost:9000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "seguros de vida"}'

# Debería retornar resultados con documentos
```

---

## 🛡️ Prevención

### 1. Nunca Elimines Volúmenes Sin Backup

```bash
# ❌ PELIGROSO - Elimina datos
docker-compose down -v
docker volume prune

# ✅ SEGURO - Mantiene datos
docker-compose down
docker-compose restart
docker-compose stop
```

### 2. Crear Backups Regulares

```bash
# Manual
make backup

# Automatizado (crontab)
# Cada día a las 2 AM:
# 0 2 * * * cd /ruta/al/proyecto && make backup
```

### 3. Verificar Health Check

```bash
# Comando útil para agregar a tu workflow
make chroma-check

# Debería mostrar:
# ✅ ChromaDB corriendo
# ✅ API responde
# ✅ Directorio de datos existe
```

### 4. Monitorear Logs

```bash
# Ver logs de ChromaDB
docker logs chromadb -f

# Ver logs de API REST
# (en otra terminal mientras corre)
make api_server

# Ver logs de n8n
make n8n-logs
```

---

## 📊 Comandos de Diagnóstico Completo

```bash
# Script de diagnóstico completo
echo "=== ChromaDB Diagnostic Report ==="
echo ""
echo "1. Docker Status:"
docker ps | grep -E "chromadb|n8n"
echo ""
echo "2. ChromaDB Stats:"
curl -s http://localhost:9000/stats | python3 -m json.tool
echo ""
echo "3. Data Directory:"
ls -lh chroma_data/ | head -10
echo ""
echo "4. ChromaDB Heartbeat:"
curl -s http://localhost:8000/api/v2/heartbeat
echo ""
echo "5. Disk Usage:"
du -sh chroma_data/
echo ""
echo "=== End Report ==="
```

Guarda esto como `diagnose.sh` y ejecuta cuando tengas problemas.

---

## 🔄 Flujo Correcto de Trabajo

```
1. Levantar Docker
   $ docker-compose up -d

2. Verificar estado
   $ make chroma-check

3. Si está vacío, indexar
   $ make full-pipeline

4. Backup preventivo
   $ make backup

5. Usar la aplicación
   $ make api_server
   
6. Al terminar el día
   $ docker-compose stop  (NO down -v)
```

---

## 🆘 Error Persiste

Si después de todo esto el error continúa:

### Opción Nuclear (Reset Total)

```bash
# 1. Backup de lo que tengas (por si acaso)
tar -czf emergency_backup.tar.gz chroma_data/ data/

# 2. Limpiar TODO
docker-compose down -v
rm -rf chroma_data/

# 3. Levantar desde cero
docker-compose up -d

# 4. Re-indexar
make full-pipeline

# 5. Verificar
make chroma-check
```

### Reportar Issue

Si nada funciona, reporta con:

```bash
# Información del sistema
uname -a
docker --version
docker-compose --version

# Logs
docker logs chromadb > chromadb.log
docker logs n8n > n8n.log

# Configuración
cat docker-compose.yaml
cat .env
```

---

## 📚 Referencias

- **ChromaDB Docs:** https://docs.trychroma.com/
- **Docker Volumes:** https://docs.docker.com/storage/volumes/
- **Makefile Comandos:** Ver `Makefile` en el proyecto
- **Setup Completo:** Ver `N8N_SETUP_COMPLETO.md`

---

**Autor:** Danilo Gómez  
**Versión:** 1.0.0  
**Fecha:** 2026-04-11

