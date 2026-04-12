#!/usr/bin/env python3
"""
Frontend Streamlit - Asistente Virtual Bancolombia

Interfaz de chat para consultar la base de conocimiento de Bancolombia.
Conecta con la API REST (puerto 8001) para realizar búsquedas semánticas.


Ejecución:
    make frontend-up
"""

import streamlit as st
import requests
from typing import Dict, List

# Configuración de la API
API_BASE_URL = "http://localhost:8001"

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Asistente Bancolombia",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SIDEBAR - ESTADÍSTICAS Y CONFIGURACIÓN
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Selector de número de resultados
    n_results = st.selectbox(
        "Número de resultados:",
        options=[2, 3, 5],
        index=0,  # 2 por defecto
        help="Cantidad de documentos a mostrar por búsqueda"
    )
    
    # Botón limpiar historial
    if st.button("🗑️ Limpiar historial", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Estadísticas de la base de conocimiento
    st.title("📊 Estadísticas de la BD")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            
            st.metric("Total Documentos", stats["total_documents"])
            st.metric("Categorías", stats["num_categories"])
            st.metric("Dimensión Embeddings", f"{stats['embedding_dimension']}D")
            st.metric("Métrica Distancia", stats["distance_metric"])
        else:
            st.warning("⚠️ No se pudieron cargar estadísticas")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ API no disponible")
        st.caption("Ejecuta: `make mcp-up`")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ============================================================================
# MAIN - INTERFAZ DE CHAT
# ============================================================================

st.title("🏦 Asistente Virtual Bancolombia")
st.caption("Consulta información sobre productos y servicios de Bancolombia")

# Inicializar historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar modo de consulta
if "query_mode" not in st.session_state:
    st.session_state.query_mode = "pregunta"

# Selector de modo de consulta
st.subheader("Modo de consulta")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Búsqueda por pregunta", use_container_width=True, 
                 type="primary" if st.session_state.query_mode == "pregunta" else "secondary"):
        st.session_state.query_mode = "pregunta"
        st.rerun()

with col2:
    if st.button("Consulta por URL", use_container_width=True,
                 type="primary" if st.session_state.query_mode == "url" else "secondary"):
        st.session_state.query_mode = "url"
        st.rerun()

with col3:
    if st.button("Ver categorías", use_container_width=True,
                 type="primary" if st.session_state.query_mode == "categorias" else "secondary"):
        st.session_state.query_mode = "categorias"
        st.rerun()

with col4:
    if st.button("Ver estadísticas", use_container_width=True,
                 type="primary" if st.session_state.query_mode == "stats" else "secondary"):
        st.session_state.query_mode = "stats"
        st.rerun()

st.divider()

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# ============================================================================
# MODO 1: BÚSQUEDA POR PREGUNTA
# ============================================================================

if st.session_state.query_mode == "pregunta":
    if prompt := st.chat_input("¿Qué deseas saber sobre Bancolombia?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Buscando información..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/search",
                        json={"query": prompt, "n_results": n_results},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data["total_results"] == 0:
                            answer = "No encontré información sobre esa consulta.\n\n"
                            answer += "Intenta reformular tu pregunta o consulta sobre:\n"
                            answer += "- Seguros\n- Créditos\n- Inversiones\n- Productos bancarios"
                        else:
                            answer = f"Encontré **{data['total_results']} documentos** relevantes:\n\n"
                            
                            for doc in data["documents"]:
                                score_badge = f"<span style='background-color: #FFD700; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;'>Score: {doc['similarity_score']:.2f}</span>"
                                answer += f"### {doc['rank']}. {doc['title']} {score_badge}\n\n"
                                answer += f"**Categoría:** {doc['category']}\n\n"
                                
                                content_preview = doc['content'][:300]
                                if len(doc['content']) > 300:
                                    content_preview += "..."
                                answer += f"{content_preview}\n\n"
                                answer += f"[Ver artículo completo]({doc['url']})\n\n"
                                answer += "---\n\n"
                        
                        st.markdown(answer, unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"Error en la búsqueda (código {response.status_code})"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except requests.exceptions.ConnectionError:
                    error_msg = "No se pudo conectar con la API. Ejecuta: make mcp-up"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except requests.exceptions.Timeout:
                    error_msg = "La búsqueda tardó demasiado. Intenta con otra pregunta o reduce el número de resultados."
                    st.warning(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = f"Error inesperado: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ============================================================================
# MODO 2: CONSULTA POR URL
# ============================================================================

elif st.session_state.query_mode == "url":
    st.info("Ingresa la URL completa de un artículo de Bancolombia para ver su contenido completo.")
    
    url_input = st.text_input(
        "URL del artículo:",
        placeholder="https://www.bancolombia.com/personas/creditos",
        help="Debe ser una URL válida de bancolombia.com"
    )
    
    if st.button("Consultar artículo", type="primary"):
        if url_input:
            st.session_state.messages.append({"role": "user", "content": f"Consulta por URL: {url_input}"})
            
            with st.chat_message("user"):
                st.markdown(f"Consulta por URL: {url_input}")
            
            with st.chat_message("assistant"):
                with st.spinner("Recuperando artículo..."):
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/article",
                            params={"url": url_input},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            answer = f"## {data['title']}\n\n"
                            answer += f"**Categoría:** {data['category']}\n\n"
                            answer += f"**Total de chunks:** {data['total_chunks']}\n\n"
                            answer += f"**URL:** {data['url']}\n\n"
                            answer += "---\n\n"
                            
                            for i, chunk in enumerate(data['chunks'], 1):
                                answer += f"### Información {i}\n\n"
                                answer += f"{chunk['content']}\n\n"
                                answer += f"*Palabras: {chunk['word_count']}*\n\n"
                                answer += "---\n\n"
                            
                            st.markdown(answer, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        elif response.status_code == 404:
                            error_msg = f"No se encontró artículo para la URL: {url_input}"
                            st.warning(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        elif response.status_code == 400:
                            error_msg = "URL inválida. Debe ser de bancolombia.com"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        else:
                            error_msg = f"Error en la consulta (código {response.status_code})"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                            
                    except requests.exceptions.ConnectionError:
                        error_msg = "No se pudo conectar con la API. Ejecuta: make mcp-up"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = f"Error inesperado: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            st.warning("Por favor ingresa una URL")

# ============================================================================
# MODO 3: VER CATEGORÍAS
# ============================================================================

elif st.session_state.query_mode == "categorias":
    st.info("Lista de todas las categorías disponibles en la base de conocimiento.")
    
    if st.button("Listar categorías", type="primary"):
        st.session_state.messages.append({"role": "user", "content": "Listar categorías"})
        
        with st.chat_message("user"):
            st.markdown("Listar categorías")
        
        with st.chat_message("assistant"):
            with st.spinner("Recuperando categorías..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/categories", timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        answer = f"## Categorías disponibles\n\n"
                        answer += f"**Total:** {data['total_categories']}\n\n"
                        answer += "---\n\n"
                        
                        for i, category in enumerate(data['categories'], 1):
                            answer += f"{i}. {category}\n"
                        
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"Error obteniendo categorías (código {response.status_code})"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except requests.exceptions.ConnectionError:
                    error_msg = "No se pudo conectar con la API. Ejecuta: make mcp-up"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = f"Error inesperado: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ============================================================================
# MODO 4: VER ESTADÍSTICAS
# ============================================================================

elif st.session_state.query_mode == "stats":
    st.info("Estadísticas completas de la base de conocimiento.")
    
    if st.button("Mostrar estadísticas", type="primary"):
        st.session_state.messages.append({"role": "user", "content": "Mostrar estadísticas"})
        
        with st.chat_message("user"):
            st.markdown("Mostrar estadísticas")
        
        with st.chat_message("assistant"):
            with st.spinner("Recuperando estadísticas..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        answer = "## Estadísticas de la Base de Conocimiento\n\n"
                        answer += f"**Estado:** {data['status']}\n\n"
                        answer += f"**Total de documentos:** {data['total_documents']}\n\n"
                        answer += f"**Número de categorías:** {data['num_categories']}\n\n"
                        answer += f"**Dimensión de embeddings:** {data['embedding_dimension']}\n\n"
                        answer += f"**Métrica de distancia:** {data['distance_metric']}\n\n"
                        answer += f"**Fecha de última actualización:** {data['fecha_ultima_actualizacion']}\n\n"
                        answer += f"**Fuente:** {data['source']}\n\n"
                        answer += "---\n\n"
                        answer += "### Categorías principales\n\n"
                        
                        for i, category in enumerate(data['categories'][:20], 1):
                            answer += f"{i}. {category}\n"
                        
                        if data['num_categories'] > 20:
                            answer += f"\n... y {data['num_categories'] - 20} categorías más\n"
                        
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"Error obteniendo estadísticas (código {response.status_code})"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except requests.exceptions.ConnectionError:
                    error_msg = "No se pudo conectar con la API. Ejecuta: make mcp-up"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = f"Error inesperado: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("Asistente Virtual Bancolombia | Powered by RAG + ChromaDB + Streamlit | By Danilo Ramirez Gomez")
st.caption("Base de conocimiento: extraído de bancolombia.com/personas")
