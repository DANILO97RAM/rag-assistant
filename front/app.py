#!/usr/bin/env python3
"""
Frontend Streamlit - Asistente Virtual Bancolombia

Interfaz de chat para consultar la base de conocimiento de Bancolombia.
Conecta con el agente conversacional que consume el servidor MCP.


Ejecución:
    make frontend-up
"""

import streamlit as st
import requests
import sys
import os
from typing import Dict, List

# Agregar raíz del proyecto al path para importar el agente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.conversational_agent import BancolombiaAgent

# Configuración de la API (usada por sidebar para stats rápidas)
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
            st.metric("Dimensión Embeddings", f"{stats['embedding_dimension']}")
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
st.caption("💬 Haz cualquier pregunta - el agente decidirá cómo responder")

# Info sobre capacidades
with st.expander("ℹ️ ¿Qué puedo preguntar?"):
    st.markdown("""
    El agente conversacional puede ayudarte con:
    
    - 🔍 **Búsquedas generales**: "Qué seguros ofrece el banco?"
    - 🔗 **Consultas por URL**: "Información de https://www.bancolombia.com/personas/creditos"
    - 📂 **Categorías**: "¿Qué categorías hay disponibles?"
    - 📊 **Estadísticas**: "¿Cuántos documentos hay indexados?"
    
    El agente analizará tu pregunta y usará la herramienta MCP adecuada automáticamente.
    """)

st.divider()

# Inicializar historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar agente conversacional (Cliente MCP)
if "agent" not in st.session_state:
    st.session_state.agent = BancolombiaAgent(api_url=API_BASE_URL)

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# ============================================================================
# CHAT ÚNICO - El agente decide qué tool MCP usar
# ============================================================================

if prompt := st.chat_input("Escribe tu pregunta o URL aquí..."):
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Respuesta del agente
    with st.chat_message("assistant"):
        with st.spinner("🤖 El agente está analizando tu consulta..."):
            try:
                # El agente decide automáticamente qué tool usar
                respuesta = st.session_state.agent.ask(prompt, n_results=n_results)
                
                # Formatear respuesta según el tipo
                if respuesta.get("error"):
                    # Error del agente
                    answer = f"❌ **Error:** {respuesta['message']}\n\n"
                    if "suggestion" in respuesta:
                        answer += f"💡 **Sugerencia:** {respuesta['suggestion']}"
                
                elif respuesta.get("success"):
                    tool_used = respuesta.get("tool") or respuesta.get("resource", "unknown")
                    
                    # Búsqueda semántica (search_knowledge_base)
                    if "documents" in respuesta:
                        if respuesta["total_results"] == 0:
                            answer = "No encontré información sobre esa consulta.\n\n"
                            answer += "Intenta reformular tu pregunta o consulta sobre:\n"
                            answer += "- Seguros\n- Créditos\n- Inversiones\n- Productos bancarios"
                        else:
                            answer = f"📚 Encontré **{respuesta['total_results']} documentos** relevantes:\n\n"
                            answer += f"*🔧 Tool MCP: `{tool_used}`*\n\n"
                            
                            for doc in respuesta["documents"]:
                                score_badge = f"<span style='background-color: #FFD700; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;'>Score: {doc['similarity_score']:.2f}</span>"
                                answer += f"### {doc['rank']}. {doc['title']} {score_badge}\n\n"
                                answer += f"**Categoría:** {doc['category']}\n\n"
                                
                                content_preview = doc['content'][:300]
                                if len(doc['content']) > 300:
                                    content_preview += "..."
                                answer += f"{content_preview}\n\n"
                                answer += f"[Ver artículo completo]({doc['url']})\n\n"
                                answer += "---\n\n"
                    
                    # Artículo por URL (get_article_by_url)
                    elif "chunks" in respuesta:
                        answer = f"## 📄 {respuesta['title']}\n\n"
                        answer += f"*🔧 Tool MCP: `{tool_used}`*\n\n"
                        answer += f"**Categoría:** {respuesta['category']}\n\n"
                        answer += f"**Total chunks:** {len(respuesta['chunks'])}\n\n"
                        answer += f"**URL:** {respuesta['url']}\n\n"
                        answer += "---\n\n"
                        
                        for i, chunk in enumerate(respuesta['chunks'], 1):
                            answer += f"### Sección {i}\n\n"
                            answer += f"{chunk['content']}\n\n"
                            answer += f"*Palabras: {chunk['word_count']}*\n\n"
                            answer += "---\n\n"
                    
                    # Categorías (list_categories)
                    elif "categories" in respuesta:
                        answer = f"## 📂 Categorías Disponibles\n\n"
                        answer += f"*🔧 Tool MCP: `{tool_used}`*\n\n"
                        answer += f"**Total:** {respuesta['total_categories']}\n\n"
                        answer += "---\n\n"
                        
                        # Mostrar en columnas
                        cats = respuesta['categories']
                        mid = len(cats) // 2
                        col1_cats = cats[:mid]
                        col2_cats = cats[mid:]
                        
                        cols = st.columns(2)
                        with cols[0]:
                            for i, cat in enumerate(col1_cats, 1):
                                st.write(f"{i}. {cat}")
                        with cols[1]:
                            for i, cat in enumerate(col2_cats, mid + 1):
                                st.write(f"{i}. {cat}")
                        
                        answer = f"Listadas {respuesta['total_categories']} categorías arriba ↑"
                    
                    # Estadísticas (knowledge-base://stats)
                    elif "stats" in respuesta:
                        data = respuesta['stats']
                        answer = "## 📊 Estadísticas de la Base de Conocimiento\n\n"
                        answer += f"*🔧 Resource MCP: `{respuesta['resource']}`*\n\n"
                        answer += f"**Estado:** {data['status']}\n\n"
                        answer += f"**Total documentos:** {data['total_documents']}\n\n"
                        answer += f"**Categorías:** {data['num_categories']}\n\n"
                        answer += f"**Dimensión embeddings:** {data['embedding_dimension']}\n\n"
                        answer += f"**Métrica:** {data['distance_metric']}\n\n"
                        answer += f"**Última actualización:** {data['fecha_ultima_actualizacion']}\n\n"
                        answer += f"**Fuente:** {data['source']}\n\n"
                    
                    else:
                        answer = f"Respuesta del agente: {respuesta}"
                
                else:
                    answer = f"❌ Respuesta inesperada del agente: {respuesta}"
                
                st.markdown(answer, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                    
            except Exception as e:
                error_msg = f"❌ Error al comunicarse con el agente: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("👨‍💻 By Danilo Ramirez Gomez | Base de conocimiento: bancolombia.com/personas")
