#!/usr/bin/env python3
"""
Frontend Streamlit - Asistente Virtual Bancolombia

Interfaz de chat para consultar la base de conocimiento de Bancolombia.
Conecta con la API REST (puerto 8001) para realizar búsquedas semánticas.


Ejecución:
    streamlit run front/app.py || make frontend-up
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
    st.title("📊 Estadísticas")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            
            st.metric("Total Documentos", stats["total_documents"])
            st.metric("Categorías", stats["num_categories"])
            st.metric("Dimensión Embeddings", f"{stats['embedding_dimension']}D")
            st.metric("Métrica Distancia", stats["distance_metric"])
            
            with st.expander("🏷️ Ver categorías"):
                categories = stats.get("categories", [])
                for cat in categories[:10]:
                    st.text(f"• {cat}")
                if len(categories) > 10:
                    st.caption(f"... y {len(categories) - 10} más")
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

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Input del usuario
if prompt := st.chat_input("¿Qué deseas saber sobre Bancolombia?"):
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Buscar en la base de conocimiento
    with st.chat_message("assistant"):
        with st.spinner("🔍 Buscando información..."):
            try:
                # Llamar a la API REST
                response = requests.post(
                    f"{API_BASE_URL}/search",
                    json={
                        "query": prompt,
                        "n_results": n_results
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar si hay resultados
                    if data["total_results"] == 0:
                        answer = "❌ No encontré información sobre esa consulta.\n\n"
                        answer += "Intenta reformular tu pregunta o consulta sobre temas como:\n"
                        answer += "- Seguros\n- Créditos\n- Inversiones\n- Productos bancarios"
                    else:
                        # Formatear respuesta
                        answer = f"Encontré **{data['total_results']} documentos** relevantes:\n\n"
                        
                        for doc in data["documents"]:
                            # Título con score
                            score_badge = f"<span style='background-color: #FFD700; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;'>Score: {doc['similarity_score']:.2f}</span>"
                            answer += f"### {doc['rank']}. {doc['title']} {score_badge}\n\n"
                            
                            # Categoría
                            answer += f"**Categoría:** {doc['category']}\n\n"
                            
                            # Contenido truncado (primeros 300 caracteres)
                            content_preview = doc['content'][:300]
                            if len(doc['content']) > 300:
                                content_preview += "..."
                            answer += f"{content_preview}\n\n"
                            
                            # URL clickeable
                            answer += f"📎 [Ver artículo completo]({doc['url']})\n\n"
                            answer += "---\n\n"
                    
                    st.markdown(answer, unsafe_allow_html=True)
                    
                    # Guardar respuesta en historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                    
                else:
                    error_msg = f"❌ Error en la búsqueda (código {response.status_code})"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    
            except requests.exceptions.ConnectionError:
                error_msg = "❌ No se pudo conectar con la API.\n\nVerifica que esté ejecutándose:\n```\nmake mcp-up\n```"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                
            except requests.exceptions.Timeout:
                error_msg = "⏱️ La búsqueda tardó demasiado. Intenta de nuevo."
                st.warning(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                
            except Exception as e:
                error_msg = f"❌ Error inesperado: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("🤖 Asistente Virtual Bancolombia | Powered by RAG + ChromaDB + Streamlit | By Danilo Ramirez Gomez")
st.caption("Base de conocimiento: extraído de bancolombia.com/personas")

