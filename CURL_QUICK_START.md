# 🚀 GUÍA RÁPIDA - API REST Bancolombia

## ✅ Testing Validado

✅ **API completamente funcional y probada con Postman**
✅ **94 documentos** indexados en ChromaDB
✅ **4 endpoints REST** disponibles
✅ **Swagger UI** integrado para documentación interactiva

---

## 🎯 Inicio Rápido (2 pasos)

### 1️⃣ Iniciar el Servidor API

```bash
# Opción A: Con Makefile
make api_server

# Opción B: Manual
cd mcp
python api_server.py
```

**Deberías ver:**
```
🚀 Iniciando Bancolombia API REST
📦 Versión: 1.0.0
✅ Base lista: 94 documentos
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 2️⃣ Probar la API

**Opción A: Postman (Recomendado)**
1. Abrir Postman
2. Click en **Import**
3. Seleccionar: `mcp/Bancolombia_API.postman_collection.json`
4. ¡Listo! Ya tienes 8 requests configurados

**Opción B: Insomnia**
- Importar la colección JSON
- Los endpoints son compatibles

**Opción C: Navegador**
- Abrir: `http://localhost:8000/docs`
- Swagger UI con todos los endpoints
- Probar directamente desde el navegador

---

## 📋 Endpoints Disponibles

| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/` | GET | Health check | ✅ Probado |
| `/search` | POST | Búsqueda semántica | ✅ Probado |
| `/article` | GET | Obtener artículo por URL | ✅ Probado |
| `/categories` | GET | Listar todas las categorías | ✅ Probado |
| `/stats` | GET | Estadísticas de la base | ✅ Probado |
| `/docs` | GET | Swagger UI (documentación) | ✅ Disponible |

---

## 🎨 Ejemplos de Respuestas

### 1️⃣ Health Check
**Request:** `GET http://localhost:8000/`

**Response:**
```json
{
  "service": "Bancolombia Knowledge API",
  "status": "operational",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 2️⃣ Búsqueda Semántica
**Request:** `POST http://localhost:8000/search`
```json
{
  "query": "¿Qué seguros ofrece Bancolombia?",
  "n_results": 3
}
```

**Response:**
```json
{
  "query": "¿Qué seguros ofrece Bancolombia?",
  "total_results": 3,
  "documents": [
    {
      "rank": 1,
      "similarity_score": 0.638,
      "title": "Seguros Bancolombia",
      "url": "https://www.bancolombia.com/personas/seguros",
      "content": "Seguros Bancolombia Protege tu salud...",
      "category": "seguros",
      "word_count": 738
    }
  ]
}
```

### 3️⃣ Obtener Artículo
**Request:** `GET http://localhost:8000/article?url=https://www.bancolombia.com/personas/creditos`

**Response:**
```json
{
  "url": "https://www.bancolombia.com/personas/creditos",
  "total_chunks": 2,
  "title": "Créditos Bancolombia",
  "category": "creditos",
  "chunks": [...]
}
```

### 4️⃣ Estadísticas
**Request:** `GET http://localhost:8000/stats`

**Response:**
```json
{
  "status": "operational",
  "total_documents": 94,
  "num_categories": 47,
  "embedding_dimension": 384,
  "distance_metric": "cosine",
  "fecha_ultima_actualizacion": "2026-04-09T02:19:08"
}
```

---

## � Búsquedas Personalizadas en Postman

### Modificar Query de Búsqueda

1. Abrir request `Search - Seguros` en Postman
2. En la pestaña **Body**, modificar el JSON:

```json
{
  "query": "TU PREGUNTA AQUÍ",
  "n_results": 5,
  "category": "creditos"  // opcional
}
```

3. Click en **Send**

### Buscar Artículo por URL

1. Abrir request `Get Article - Créditos`
2. En la pestaña **Params**, cambiar el valor de `url`:

```
url = https://www.bancolombia.com/personas/TU_URL_AQUÍ
```

### Filtrar por Categoría

Categorías disponibles (47 total):
- `creditos`, `seguros`, `a-la-mano`, `pagos`, `consumidor-financiero`
- [Ver lista completa: GET `/categories`]

---

## 💡 Tips de Postman

### Guardar Respuestas

1. Ejecutar request
2. En la pestaña **Response**, click en **Save Response**
3. Elegir **Save to a file**

### Usar Variables

1. Click en el engranaje (⚙️) > **Manage Environments**
2. Crear variable:
   - `base_url` = `http://localhost:8000`
3. Usar en requests: `{{base_url}}/search`

### Ver Tiempo de Respuesta

En Postman, después de cada request verás:
- **Status:** 200 OK
- **Time:** 45ms ⏱️
- **Size:** 2.1KB

### Tests Automáticos

En la pestaña **Tests** de cada request, agregar:

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has documents", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.documents).to.be.an('array');
});
```

---

## 🐛 Troubleshooting

### ❌ "Connection refused" en Postman

**Problema:** El servidor API no está ejecutándose.

**Solución:**
```bash
cd mcp
python api_server.py
```

**Verificar:** Deberías ver `Uvicorn running on http://0.0.0.0:8000`

---

### ❌ HTTP 500 - "ChromaDB collection not found"

**Problema:** Base de datos vacía o no indexada.

**Solución:**
```bash
# Indexar datos primero
python src/main.py --index-chromadb
```

**Verificar:** Ejecutar `GET /stats` debería mostrar 94 documentos.

---

### ❌ "ModuleNotFoundError: No module named 'fastapi'"

**Problema:** Dependencias no instaladas.

**Solución:**
```bash
pip install fastapi uvicorn
# O con Makefile
make api_install
```

---

### ❌ Responses lentas (>500ms)

**Posibles causas:**
- Primera búsqueda (carga del modelo): Normal
- ChromaDB en disco: Esperado
- Queries complejas: Normal

**Normal:** 40-150ms por búsqueda después de la primera

---

## 📚 Documentación Completa

- **API REST README:** [mcp/API_REST_README.md](../API_REST_README.md)
- **Scripts cURL README:** [mcp/curl_examples/README.md](README.md)
- **MCP Server README:** [mcp/README.md](../README.md)

---

## 🎯 Siguiente Paso

Una vez que hayas probado todos los endpoints con cURL y funcionen correctamente:

1. ✅ **Instalar Postman/Insomnia** (cuando quieras)
2. ✅ **Importar colección Postman:** `mcp/Bancolombia_API.postman_collection.json`
3. ✅ **Pasar al siguiente componente:** Agente Conversacional (Sección 3.5)

**Por ahora, con cURL tienes TODO lo que necesitas para testear la API.** 🎉

---

**Creado:** 2026-04-10  
**Autor:** Danilo Gómez
<!-- Commented by GitHub Copilot -->
