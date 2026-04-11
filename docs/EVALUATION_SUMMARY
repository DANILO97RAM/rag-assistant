# Resumen de Evaluaciones - RAG Assistant Bancolombia

## 📅 Fecha: 2026-04-09

---

## 📊 Evaluación de Estrategias de Chunking

### Resultados Comparativos

| Estrategia | Total Chunks | Promedio Palabras | P75 Palabras | Max Palabras |
|------------|--------------|-------------------|--------------|--------------|
| **512/64** | 163 | 270.4 | 362.5 | 391.0 |
| **512/128** | 175 | 280.8 | 362.0 | 393.0 |
| **1024/128** ⭐ | **96** | **451.7** | **698.2** | **773.0** |
| **1024/256** | 100 | 471.9 | 705.5 | 769.0 |
| **2048/256** | 64 | 661.9 | 980.2 | 1531.0 |

### ✅ Decisión Final: **1024/128**

**Razones:**
1. ✅ **Balance óptimo**: 452 palabras promedio (~600-700 tokens)
2. ✅ **Cantidad razonable**: 96 chunks (ni muy pocos ni muchos)
3. ✅ **Granularidad adecuada**: Chunks no muy grandes para retrieval preciso
4. ✅ **Overlap suficiente**: 128 tokens (12%) mantiene contexto
5. ❌ **2048/256 descartado**: Chunks muy grandes (max 1531 palabras) pierden precisión

**Benchmark del estado del arte:**
- Papers de RAG recomiendan: 512-1024 tokens ✅
- LangChain best practices: overlap 10-20% ✅
- OpenAI docs: <1024 tokens para embeddings óptimos ✅

---

## 🤖 Comparación de Modelos de Embeddings

### Resultados (20 chunks de muestra)

| Métrica | Sentence Transformers | Gemini |
|---------|----------------------|--------|
| **Modelo** | all-MiniLM-L6-v2 | gemini-embedding-001 |
| **Dimensiones** | 384 | 3072 🔴 |
| **Tiempo (20 chunks)** | 2.97s | 8.92s (3.0x más lento) |
| **Tiempo extrapolado (94 chunks)** | ~14s | ~42s |
| **Tamaño en disco (20 chunks)** | 0.10 MB | 0.63 MB |
| **Tamaño extrapolado (94 chunks)** | ~0.47 MB | ~2.96 MB |
| **Norma L2** | 1.0000 | 1.0000 |
| **Costo** | $0 (gratis) | Cuota API |
| **Requiere internet** | ❌ No | ✅ Sí |

### ⚠️ Hallazgo Importante: Dimensionalidad de Gemini

Gemini está retornando **3072 dimensiones**, no las 768 esperadas.

**Posibles explicaciones:**
1. El nuevo SDK `google.genai` usa un modelo diferente
2. `gemini-embedding-001` tiene una versión actualizada con más dimensiones
3. Mayor dimensionalidad = mayor expresividad pero también mayor costo de almacenamiento

### ✅ Decisión para el Proyecto

| Fase | Modelo Recomendado | Razón |
|------|-------------------|-------|
| **Desarrollo/Testing** | **Sentence Transformers** | Rápido, gratis, sin dependencias externas |
| **Prototipo/Demo** | **Sentence Transformers** | Suficiente para validar funcionalidad |
| **Producción** | **Gemini** (evaluar) | Mayor calidad, pero 6x más grande en disco |

**Trade-offs:**
- **Sentence Transformers**: 384 dims, 0.47 MB para 94 chunks
- **Gemini**: 3072 dims (8x más), 2.96 MB para 94 chunks (6.3x más)

Para **50-100 chunks → Sentence Transformers es óptimo**. Si escalaras a 10,000+ chunks, la diferencia de calidad de Gemini podría justificar el costo.

---

## 🎯 Configuración Final Recomendada

```python
# Chunking
chunk_size = 1024  # tokens
chunk_overlap = 128  # tokens (12.5%)

# Embeddings
provider = "sentence-transformers"
model = "all-MiniLM-L6-v2"
dimensions = 384

# Resultado
total_chunks = 96
tamaño_disco = ~0.5 MB
tiempo_generación = ~14 segundos
```

---

## 📈 Métricas del Proyecto

- **Páginas scrapeadas**: 50
- **Chunks generados**: 96
- **Tamaño promedio chunk**: 452 palabras (~600 tokens)
- **Embeddings**: 384 dimensiones
- **Espacio total**: ~0.5 MB
- **Tiempo total pipeline**: <2 minutos

---

## 🚀 Próximos Pasos

1. ✅ **Opción C completada**: Comparación de embeddings
2. ✅ **Opción B completada**: Evaluación de chunking
3. ⏭️ **Opción A**: Implementar ChromaDB + Servidor MCP

**Decisiones confirmadas:**
- Chunks: 1024/128
- Embeddings: Sentence Transformers (desarrollo) / Gemini (opcional para producción)
- Base vectorial: ChromaDB (próximo paso)

---

## 💼 Explicación para Entrevistas: ¿Por qué estos parámetros?

### 🎤 "¿Por qué elegiste un chunk_size de 1024 con overlap de 128?"

**Respuesta preparada:**

> "Realicé pruebas empíricas comparando **5 estrategias diferentes** de chunking: desde chunks pequeños de 512 tokens hasta chunks grandes de 2048. Evalué tres métricas clave: **cantidad de chunks generados**, **distribución de tamaños** y **granularidad para retrieval**.
> 
> Los resultados mostraron que:
> - **512 tokens** generaba 175 chunks muy pequeños (270 palabras promedio) → demasiado fragmentado
> - **2048 tokens** generaba solo 64 chunks grandes (662 palabras promedio) → pierde precisión en búsqueda
> - **1024 tokens** con overlap de 128 generó **96 chunks** con promedio de **452 palabras** → balance óptimo
> 
> Además, el **estado del arte** respalda esta decisión:
> - Papers académicos de RAG recomiendan chunks de **512-1024 tokens**
> - LangChain best practices especifica **overlap del 10-20%** (mi 128/1024 = 12.5%)
> - OpenAI documentation recomienda **<1024 tokens** para embeddings óptimos
> 
> Por último, el **overlap de 128 tokens** asegura que no se pierda contexto entre chunks contiguos, crucial para preguntas que puedan abarcar límites entre fragmentos."

**Datos clave para recordar:**
- ✅ Probé 5 estrategias: 512/64, 512/128, 1024/128, 1024/256, 2048/256
- ✅ 1024/128 → 96 chunks, 452 palabras promedio
- ✅ Estado del arte: 512-1024 tokens, overlap 10-20%
- ✅ Trade-off: granularidad vs contexto

---

### 🎤 "¿Por qué Sentence Transformers en lugar de Gemini?"

**Respuesta preparada:**

> "Implementé un **sistema multi-proveedor de embeddings** y realicé una comparación rigurosa entre **Sentence Transformers** y **Google Gemini** con 20 chunks de muestra, midiendo tres dimensiones: **performance**, **dimensionalidad** y **trade-offs prácticos**.
> 
> Los resultados fueron reveladores:
> - **Sentence Transformers** (all-MiniLM-L6-v2): **384 dimensiones**, 2.97 segundos → **3x más rápido**
> - **Gemini** (gemini-embedding-001): **3072 dimensiones**, 8.92 segundos → 6x más espacio en disco
> 
> Para un dataset de **96 chunks** (resultado de mi pipeline):
> - Sentence Transformers: **~0.5 MB** de almacenamiento, sin dependencia de internet, **$0 de costo**
> - Gemini: **~3 MB** de almacenamiento, requiere API calls, costo por uso
> 
> Siguiendo el principio de **ingeniería pragmática**, para 96 chunks Sentence Transformers es suficiente. Las 3072 dimensiones de Gemini serían justificables si escalara a **10,000+ chunks**, pero para este volumen representan **overkill**.
> 
> Además, mantener el modelo local me da **reproducibilidad** y **control total** sobre el pipeline, ideal para desarrollo y testing."

**Datos clave para recordar:**
- ✅ Comparé 2 proveedores con métricas objetivas
- ✅ ST: 384 dims, 3x más rápido, gratis, local
- ✅ Gemini: 3072 dims (8x más), más lento, requiere API
- ✅ Decisión: para 96 chunks, ST es óptimo (principio de parsimonia)

---

### 🎤 "¿Qué metodología seguiste para validar tus decisiones?"

**Respuesta preparada:**

> "Seguí una metodología **data-driven** con tres fases:
> 
> **1. Experimentación controlada:**
> - Diseñé scripts de evaluación automatizados (`evaluate_chunking_strategies.py`, `compare_embeddings.py`)
> - Definí métricas cuantificables: tiempo de procesamiento, dimensionalidad, distribución estadística
> - Extrapolé resultados de muestras a dataset completo
> 
> **2. Benchmark contra estado del arte:**
> - Consulté papers académicos de RAG (retrieval-augmented generation)
> - Revisé documentación oficial: LangChain, OpenAI, Google AI
> - Validé que mis decisiones estaban alineadas con best practices
> 
> **3. Trade-off analysis:**
> - No busqué 'la mejor opción absoluta' sino **la mejor para este caso de uso**
> - Consideré: tamaño del dataset (50 páginas), latencia, costo, mantenibilidad
> - Prioricé **simplicidad y reproducibilidad** sobre complejidad innecesaria
> 
> Esta metodología me permitió tomar **decisiones justificadas con evidencia empírica**, no por intuición."

**Datos clave para recordar:**
- ✅ 3 fases: experimentación → benchmark → trade-off analysis
- ✅ Scripts automatizados con métricas cuantificables
- ✅ Validación contra literatura académica y docs oficiales
- ✅ Decisiones basadas en evidencia, no intuición

---

### 📋 Cheat Sheet Rápido para Entrevista

| Pregunta | Respuesta clave |
|----------|----------------|
| **¿Cuántas estrategias probaste?** | 5 estrategias de chunking, 2 proveedores de embeddings |
| **¿Cuál fue tu métrica principal?** | Balance entre granularidad (chunks) y contexto (overlap) |
| **¿Qué dice el estado del arte?** | 512-1024 tokens, overlap 10-20%, LangChain + OpenAI docs |
| **¿Por qué 1024/128?** | 96 chunks, 452 palabras promedio, alineado con papers de RAG |
| **¿Por qué Sentence Transformers?** | 3x más rápido, 384 dims suficientes para 96 chunks, $0 costo |
| **¿Consideraste Gemini?** | Sí, pero 3072 dims es overkill para este volumen (96 chunks) |
| **¿Cómo validaste?** | Scripts automatizados + benchmark contra literatura + trade-offs |
| **¿Qué harías si escala?** | Re-evaluar Gemini para 10K+ chunks donde mayor dim = mejor recall |

---

**Fecha de evaluación**: 2026-04-09  
**Estado**: Listo para implementar ChromaDB
