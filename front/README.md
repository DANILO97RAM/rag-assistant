# 🏦 Frontend Streamlit - Asistente Virtual Bancolombia

Interfaz de chat para consultar la base de conocimiento de Bancolombia mediante la API REST.

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

### Chat Interactivo
- ✅ Input de texto para preguntas en lenguaje natural
- ✅ Historial de conversación completo
- ✅ Indicador de carga "Buscando información..."

### Configuración
- ✅ Selector de número de resultados (3, 5, 7)
- ✅ Botón "Limpiar historial"

### Resultados de Búsqueda
- ✅ Título del documento
- ✅ Score de similitud (0.0 - 1.0)
- ✅ Categoría
- ✅ Preview del contenido (primeros 300 caracteres)
- ✅ URL clickeable al artículo original

### Estadísticas (Sidebar)
- ✅ Total de documentos indexados
- ✅ Número de categorías
- ✅ Dimensión de embeddings
- ✅ Lista de categorías disponibles

---

## 📸 Ejemplo de Uso

### Pregunta
```
Usuario: ¿Qué seguros ofrece Bancolombia?
```

### Respuesta
```
Encontré 3 documentos relevantes:

1. Bancolombia Corresponsal Bancario [Score: 0.64]
   Categoría: corresponsal-bancario
   
   Bancolombia Corresponsal Bancario Personas Productos...
   
   📎 Ver artículo completo
   
---

2. Seguros Bancolombia [Score: 0.58]
   ...
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
    options=[3, 5, 7, 10],  # Agregar más opciones
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

### Pruebas manuales recomendadas

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

---

## 🤝 Contribución

Para mejorar el frontend:

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/mejora-frontend`
3. Editar `front/app.py`
4. Probar cambios: `streamlit run front/app.py`
5. Commit: `git commit -am 'feat: mejora en frontend'`
6. Push y crear Pull Request

---

## 📄 Licencia

Parte de la prueba técnica Bancolombia - Uso educativo

---

**Autor:** Danilo Gómez  
**Fecha:** 12 de abril de 2026  
**Repositorio:** github.com/DANILO97RAM/rag-assistant

<!-- Código generado por GitHub Copilot -->
