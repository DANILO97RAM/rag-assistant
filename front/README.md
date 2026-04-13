# 🏦 Frontend Streamlit - Asistente Virtual Bancolombia

Interfaz de chat conversacional donde el usuario escribe cualquier pregunta y el **agente conversacional** decide automáticamente qué tool MCP usar para responder.

**Arquitectura:** Frontend → Agente Conversacional → API REST → MCP Server → ChromaDB

---

## 🎯 Características

- ✅ **Chat único simplificado**: No hay modos - el agente decide qué hacer
- ✅ **Agente integrado**: Usa `BancolombiaAgent` como cliente MCP
- ✅ **Razonamiento automático**: El agente analiza la pregunta y elige el tool correcto
- ✅ **Memoria conversacional**: Mantiene historial de la sesión
- ✅ **Transparencia de tools**: Muestra qué tool MCP usó en cada respuesta
- ✅ **Fuentes citadas**: URLs clickeables en búsquedas
- ✅ **Sidebar informativo**: Estadísticas de la base de conocimiento

---

## 🤖 Inteligencia del Agente

El agente analiza tu pregunta y decide automáticamente:

| Tu pregunta | Tool MCP que usará |
|-------------|-------------------|
| "¿Qué seguros ofrece Bancolombia?" | `search_knowledge_base` |
| "https://www.bancolombia.com/personas/creditos" | `get_article_by_url` |
| "¿Qué categorías hay?" | `list_categories` |
| "¿Cuántos documentos hay?" | `knowledge-base://stats` |

**No necesitas seleccionar nada** - solo pregunta naturalmente.

---

## 🚀 Inicio Rápido

```bash
# 1. Levantar servicios backend
make docker-up  # ChromaDB (puerto 8000)
make db-index   # Indexar documentos
make mcp-up     # API REST (puerto 8001)

# 2. Ejecutar frontend
make frontend-up
```

**Se abrirá en:** http://localhost:8501

---

## 💬 Ejemplos de Uso

El agente entiende diferentes tipos de preguntas y usa el tool correcto automáticamente:

### Ejemplo 1: Búsqueda semántica

**Usuario:** `¿Qué seguros ofrece Bancolombia?`

**Asistente:**
```
📚 Encontré 3 documentos relevantes:
🔧 Tool MCP: search_knowledge_base

1. Seguros Bancolombia [Score: 0.64]
   Categoría: seguros
   
   Seguros Bancolombia Protege tu salud y la de quien...
   
   Ver artículo completo
```

### Ejemplo 2: Consulta por URL

**Usuario:** `https://www.bancolombia.com/personas/creditos`

**Asistente:**
```
📄 Créditos Bancolombia
🔧 Tool MCP: get_article_by_url

Categoría: creditos
Total chunks: 2
URL: https://www.bancolombia.com/personas/creditos

---

Sección 1
[Contenido completo...]
Palabras: 450
```

### Ejemplo 3: Listar categorías

**Usuario:** `¿Qué categorías hay disponibles?`

**Asistente:**
```
📂 Categorías Disponibles
🔧 Tool MCP: list_categories

Total: 47

[Muestra categorías en 2 columnas]
```

### Ejemplo 4: Estadísticas

**Usuario:** `¿Cuántos documentos hay indexados?`

**Asistente:**
```
📊 Estadísticas de la Base de Conocimiento
🔧 Resource MCP: knowledge-base://stats

Estado: operational
Total documentos: 94
Categorías: 47
Dimensión embeddings: 384
Métrica: cosine
```

---

## 🔧 Configuración

### Número de resultados

En el sidebar puedes ajustar cuántos documentos retorna el agente en búsquedas semánticas:
- 2 (rápido, menos contexto)
- 3 (balanceado - default)
- 5 (exhaustivo, más contexto)

### Limpiar historial

El botón "🗑️ Limpiar historial" borra todos los mensajes de la sesión actual.

---

## 🐛 Troubleshooting

### Error: "Error al comunicarse con el agente"

**Causa:** El agente no puede conectarse con la API REST

**Solución:**
```bash
# 1. Verificar que ChromaDB esté corriendo
docker ps | grep chroma

# 2. Levantar API REST
make mcp-up

# 3. Probar API manualmente
curl http://localhost:8001/
```

---

### Error: "Connection refused"

**Causa:** La API REST no está ejecutándose

**Solución:**
```bash
# Verificar puerto 8001
lsof -i :8001

# Si está ocupado, matar proceso
kill <PID>

# Levantar API
make mcp-up
```

---

### El agente no responde

**Solución:**
1. Click en "🗑️ Limpiar historial" en el sidebar
2. Verificar que el API REST esté corriendo
3. Intentar pregunta simple: "hola"

---

## 📦 Dependencias

```
streamlit>=1.30.0
requests>=2.31.0
```

Instalación: ya estan cubiertas en el entorno virtual creado con `make setup`. Para instalar manualmente:

---

## 🎨 Personalización

### Cambiar timeout del agente

Edita `agent/conversational_agent.py`:
```python
timeout=10  # Cambiar a 15 o 20 segundos
```

### Cambiar número de caracteres en preview

Edita `front/app.py`:
```python
content_preview = doc['content'][:300]  # Cambiar 300
```

### Cambiar opciones de resultados

Edita `front/app.py`:
```python
n_results = st.selectbox(
    "Número de resultados:",
    options=[2, 3, 5, 10],  # Agregar más opciones
    index=0
)
```

---

## 📄 Arquitectura del Código

```python
front/app.py (240 líneas)

├── Imports y configuración (líneas 1-25)
│   └── Importa BancolombiaAgent
├── Sidebar (líneas 26-80)
│   ├── Selector de resultados
│   ├── Botón limpiar historial
│   └── Estadísticas (API REST directo)
├── Main (líneas 81-230)
│   ├── Header con ayuda
│   ├── Inicialización del agente
│   ├── Historial de mensajes
│   └── Chat input único
│       ├── Llamada a agent.ask()
│       └── Formateo de respuestas
└── Footer (líneas 231-240)
```

---

## 🧪 Testing Manual

### Test 1: Búsqueda semántica

```
Usuario: ¿Qué seguros ofrece Bancolombia?

Verificar:
✅ Respuesta muestra documentos
✅ Muestra "Tool MCP: search_knowledge_base"
✅ URLs son clickeables
✅ Scores de similitud visibles
```

### Test 2: Consulta por URL

```
Usuario: https://www.bancolombia.com/personas/creditos

Verificar:
✅ Respuesta muestra contenido completo del artículo
✅ Muestra "Tool MCP: get_article_by_url"
✅ Muestra todos los chunks
```

### Test 3: Categorías

```
Usuario: ¿Qué categorías hay?

Verificar:
✅ Muestra lista completa de categorías
✅ Muestra "Tool MCP: list_categories"
✅ Total de categorías correcto (47)
```

### Test 4: Estadísticas

```
Usuario: ¿Cuántos documentos hay indexados?

Verificar:
✅ Muestra métricas completas
✅ Muestra "Resource MCP: knowledge-base://stats"
✅ Datos actualizados
```

### Test 5: Manejo de errores

```
1. Apagar API REST (Ctrl+C en terminal MCP)
2. Hacer pregunta en el frontend
3. Verificar: mensaje de error claro con sugerencia
```

---

## 📚 Recursos

- [Documentación principal](../README.md)
- [Agente conversacional](../agent/README.md)
- [API REST Swagger](http://localhost:8001/docs)
- [Documentación Streamlit](https://docs.streamlit.io)

---

## 👨‍💻 Autor

Danilo Ramirez Gomez  
Fecha: 12 de abril de 2026