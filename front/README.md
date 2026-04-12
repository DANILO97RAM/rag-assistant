# 🏦 Frontend Streamlit - Asistente Virtual Bancolombia

Interfaz de chat para consultar la base de conocimiento de Bancolombia mediante la API REST. 

**Consume las 3 tools y 1 resource del servidor MCP:**
- Tool: `search_knowledge_base` (búsqueda semántica)
- Tool: `get_article_by_url` (consulta por URL)
- Tool: `list_categories` (listar categorías)
- Resource: `knowledge-base://stats` (estadísticas)

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
# Desde la raíz del proyecto
pip install streamlit requests
```

### 2. Levantar servicios backend

```bash
# Levantar ChromaDB (Docker)
make docker-up

# Levantar API REST (puerto 8001)
make mcp-up
```

### 3. Ejecutar frontend

```bash
# Opción 1: Comando directo
streamlit run front/app.py

# Opción 2: Con Makefile
make frontend
```

El frontend se abrirá en: **http://localhost:8501**

---

## ✨ Características

### 4 Modos de Consulta

El frontend expone los 4 endpoints de la API REST (que a su vez consumen las tools y resources del servidor MCP):

**1. Búsqueda por pregunta** (Tool: `search_knowledge_base`)
- Input de texto libre en lenguaje natural
- Endpoint: `POST /search`
- Retorna documentos rankeados con scores de similitud
- Selector de número de resultados (2, 3, 5)
- Muestra: título, categoría, score, preview de contenido, URL

**2. Consulta por URL** (Tool: `get_article_by_url`)
- Input: URL completa de artículo de Bancolombia
- Endpoint: `GET /article?url=...`
- Retorna todos los chunks del artículo
- Muestra: título, categoría, total de chunks, contenido completo

**3. Ver categorías** (Tool: `list_categories`)
- Botón: "Listar categorías"
- Endpoint: `GET /categories`
- Retorna lista completa de 47 categorías disponibles
- Muestra: lista numerada ordenada alfabéticamente

**4. Ver estadísticas** (Resource: `knowledge-base://stats`)
- Botón: "Mostrar estadísticas"
- Endpoint: `GET /stats`
- Retorna métricas de la base de conocimiento
- Muestra: total docs, categorías, dimensión embeddings, métrica distancia, fecha actualización

### Configuración (Sidebar)
- Selector de número de resultados (solo aplica a modo 1)
- Botón "Limpiar historial"
- Preview de estadísticas en tiempo real

### Historial de Conversación
- Persistente durante la sesión
- Muestra interacciones en todos los modos
- Se mantiene al cambiar entre modos
- Se limpia con botón dedicado

---

## 📸 Ejemplos de Uso

### Modo 1: Búsqueda por pregunta

**Input:**
```
Usuario: ¿Qué seguros ofrece Bancolombia?
```

**Output:**
```
Encontré 3 documentos relevantes:

1. Bancolombia Corresponsal Bancario [Score: 0.64]
   Categoría: corresponsal-bancario
   
   Bancolombia Corresponsal Bancario Personas Productos...
   
   Ver artículo completo
   
---

2. Seguros Bancolombia [Score: 0.58]
   ...
```

### Modo 2: Consulta por URL

**Input:**
```
URL: https://www.bancolombia.com/personas/creditos
```

**Output:**
```
Créditos Bancolombia

Categoría: creditos
Total de chunks: 2
URL: https://www.bancolombia.com/personas/creditos

---

Chunk 1
[contenido completo del chunk 1]
Palabras: 450

---

Chunk 2
[contenido completo del chunk 2]
Palabras: 380
```

### Modo 3: Ver categorías

**Output:**
```
Categorías disponibles
Total: 47

---

1. a-la-mano
2. ahorro
3. banco
4. beneficios
...
47. trabajadores-independientes
```

### Modo 4: Ver estadísticas

**Output:**
```
Estadísticas de la Base de Conocimiento

Estado: operational
Total de documentos: 94
Número de categorías: 47
Dimensión de embeddings: 384
Métrica de distancia: cosine
Fecha de última actualización: 2026-04-12
Fuente: https://www.bancolombia.com/personas

---

Categorías principales
1. a-la-mano
2. ahorro
...
20. seguros
```

---

## 🔧 Configuración

### Variables de Entorno

El frontend usa estas URLs por defecto:
- **API REST:** `http://localhost:8001`

Para cambiar la URL, edita `front/app.py`:
```python
API_BASE_URL = "http://localhost:8001"  # Cambiar aquí
```

---

## 🐛 Troubleshooting

### Error: "API no disponible"

**Causa:** La API REST no está ejecutándose

**Solución:**
```bash
# Verificar que ChromaDB esté corriendo
docker-compose ps

# Levantar API REST
make mcp-up

# O manualmente
cd mcp
python api_server.py
```

---

### Error: "No se pudieron cargar estadísticas"

**Causa:** El endpoint `/stats` no responde

**Solución:**
```bash
# Probar endpoint manualmente
curl http://localhost:8001/stats

# Si no responde, revisar logs de la API
```

---

### El historial no se limpia

**Solución:**
- Click en "🗑️ Limpiar historial" en el sidebar
- La página se recargará automáticamente

---

## 📦 Dependencias

```
streamlit==1.56.0
requests==2.33.1
```

Instalación:
```bash
pip install -r requirements.txt  # Desde la raíz del proyecto
```

---

## 🎨 Personalización

### Cambiar número de caracteres en preview

Edita en `app.py` línea ~115:
```python
content_preview = doc['content'][:300]  # Cambiar 300
```

### Cambiar opciones de resultados

Edita en `app.py` línea ~31:
```python
n_results = st.selectbox(
    "Número de resultados:",
    options=[2, 3, 5],
    index=0
)
```

---

## 📄 Estructura del Código

```python
front/app.py

├── Configuración de página (líneas 1-30)
├── Sidebar
│   ├── Selector de resultados
│   ├── Botón limpiar
│   └── Estadísticas (llamada a /stats)
├── Main
│   ├── Historial de mensajes
│   ├── Input del usuario
│   └── Búsqueda en API (llamada a /search)
└── Footer
```

---

## 🧪 Testing

### Pruebas manuales realizadas

1. **Búsqueda exitosa:**
   - Pregunta: "¿Qué seguros ofrece Bancolombia?"
   - Verificar: 3 resultados con URLs

2. **Cambiar número de resultados:**
   - Seleccionar 5 en sidebar
   - Nueva búsqueda debe mostrar 5 resultados

3. **Limpiar historial:**
   - Hacer varias preguntas
   - Click en "Limpiar historial"
   - Verificar: chat vacío

4. **Estadísticas:**
   - Verificar sidebar muestra: total docs, categorías, dimensión

5. **Manejo de errores:**
   - Apagar API REST (`Ctrl+C` en terminal)
   - Intentar búsqueda
   - Verificar: mensaje de error amigable
 
---

## 📚 Recursos

- [Documentación Streamlit](https://docs.streamlit.io)
- [API REST Swagger](http://localhost:8001/docs)
- [Postman Collection](../mcp/Bancolombia_API.postman_collection.json)
