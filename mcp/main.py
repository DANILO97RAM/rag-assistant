#!/usr/bin/env python3
"""
Servidor MCP - Prueba Bancolombia Knowledge Base

Tools:
- search_knowledge_base: Búsqueda semántica en ChromaDB
- get_article_by_url: Recuperación por URL específica
- list_categories: Listado de categorías disponibles

Resource:
- knowledge-base://stats: Estadísticas de la base de datos

"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar src al path para importar ChromaDBService
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastmcp import FastMCP
from services.database import ChromaDBService

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización del servidor MCP
mcp = FastMCP(
    name="Bancolombia Knowledge Server",
    version="1.0.0"
)

# Conexión a ChromaDB Docker (HttpClient)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
logger.info(f"🔌 Conectando a ChromaDB Docker en {CHROMA_HOST}:{CHROMA_PORT}")

try:
    # Usar HttpClient para conectar al ChromaDB Docker
    db = ChromaDBService(use_local=False)
    logger.info("✅ ChromaDB conectado exitosamente")
except Exception as e:
    logger.error(f"❌ Error conectando a ChromaDB: {e}")
    raise


# ============================================================================
# TOOLS - Herramientas obligatorias según requisitos de prueba técnica
# ============================================================================

@mcp.tool()
def search_knowledge_base(
    query: str,
    n_results: int = 5,
    category: str | None = None
) -> Dict[str, Any]:
    """
    Ejecuta búsqueda semántica contra la base de conocimiento de Bancolombia.
    
    Args:
        query: Consulta en lenguaje natural
        n_results: Número de resultados a retornar (default: 5, max: 10)
        category: Filtro opcional por categoría (ej: 'creditos', 'seguros')
    
    Returns:
        Dict con resultados incluyendo documentos, metadatos, URLs y scores
    
    Example:
        >>> search_knowledge_base("¿Qué seguros ofrece Bancolombia?", n_results=3)
    """
    try:
        # Validación de parámetros
        if not query or len(query.strip()) == 0:
            return {
                "error": "Query vacía",
                "message": "Debe proporcionar una consulta válida"
            }
        
        if n_results < 1 or n_results > 10:
            n_results = 5
        
        # Preparar filtro por categoría si se proporciona
        where_filter = {"category": category} if category else None
        
        # Ejecutar búsqueda semántica
        results = db.search(
            query=query,
            n_results=n_results,
            where=where_filter
        )
        
        # Formatear respuesta para el agente
        formatted_results = {
            "query": query,
            "total_results": len(results),
            "documents": []
        }
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            similarity_score = 1 - result.get('distance', 0.0)
            
            formatted_results["documents"].append({
                "rank": i,
                "content": result['document'],
                "url": metadata.get('url', 'N/A'),
                "title": metadata.get('title', 'Sin título'),
                "category": metadata.get('category', 'Sin categoría'),
                "similarity_score": round(similarity_score, 3),
                "word_count": metadata.get('word_count', 0)
            })
        
        logger.info(f"🔍 Búsqueda ejecutada: '{query[:50]}...' → {len(results)} resultados")
        return formatted_results
        
    except Exception as e:
        logger.error(f"❌ Error en search_knowledge_base: {e}")
        return {
            "error": "Error en búsqueda",
            "message": str(e)
        }


@mcp.tool()
def get_article_by_url(url: str) -> Dict[str, Any]:
    """
    Recupera el contenido completo de un artículo mediante su URL.
    
    Args:
        url: URL completa del artículo de Bancolombia
    
    Returns:
        Dict con todos los chunks del artículo y sus metadatos
    
    Example:
        >>> get_article_by_url("https://www.bancolombia.com/personas/creditos")
    """
    try:
        # Validación de parámetros
        if not url or not url.startswith("https://www.bancolombia.com"):
            return {
                "error": "URL inválida",
                "message": "Debe ser una URL válida de bancolombia.com"
            }
        
        # Recuperar chunks por URL
        chunks = db.get_by_url(url)
        
        if not chunks:
            return {
                "error": "Artículo no encontrado",
                "message": f"No se encontraron documentos para la URL: {url}"
            }
        
        # Formatear respuesta
        result = {
            "url": url,
            "total_chunks": len(chunks),
            "title": chunks[0]['metadata'].get('title', 'Sin título') if chunks else None,
            "category": chunks[0]['metadata'].get('category', 'Sin categoría') if chunks else None,
            "chunks": []
        }
        
        for chunk in chunks:
            result["chunks"].append({
                "content": chunk['document'],
                "chunk_index": chunk['metadata'].get('chunk_index', 0),
                "word_count": chunk['metadata'].get('word_count', 0)
            })
        
        logger.info(f"📄 Artículo recuperado: {url} → {len(chunks)} chunks")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en get_article_by_url: {e}")
        return {
            "error": "Error recuperando artículo",
            "message": str(e)
        }


@mcp.tool()
def list_categories() -> Dict[str, Any]:
    """
    Lista todas las categorías disponibles en la base de conocimiento.
    
    Returns:
        Dict con lista de categorías y estadísticas por categoría
    
    Example:
        >>> list_categories()
    """
    try:
        # Obtener categorías
        categories = db.get_categories()
        
        result = {
            "total_categories": len(categories),
            "categories": sorted(categories)
        }
        
        logger.info(f"📁 Categorías listadas: {len(categories)} encontradas")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en list_categories: {e}")
        return {
            "error": "Error listando categorías",
            "message": str(e)
        }


# ============================================================================
# RESOURCE - Estadísticas de la base de conocimiento
# ============================================================================

@mcp.resource("knowledge-base://stats")
def get_kb_stats() -> str:
    """
    Expone estadísticas actuales de la base de conocimiento.
    
    Returns:
        JSON string con estadísticas completas
    """
    try:
        stats = db.get_stats()
        
        # Formatear como texto legible para el agente
        stats_text = f"""📊 ESTADÍSTICAS BASE DE CONOCIMIENTO BANCOLOMBIA

✅ Estado: Operativa
📚 Total documentos: {stats['total_documents']}
📁 Categorías: {stats['num_categories']}
🔢 Dimensión embeddings: {stats['embedding_dimension']}
📏 Métrica de distancia: {stats['distance_metric']}
📅 Última actualización: {stats['fecha_ultima_actualizacion']}
🌐 Fuente: https://www.bancolombia.com/personas

Categorías disponibles:
""" + "\n".join([f"  • {cat}" for cat in stats['categories'][:10]])
        
        if stats['num_categories'] > 10:
            stats_text += f"\n  ... y {stats['num_categories'] - 10} más"
        
        logger.info("📊 Estadísticas consultadas")
        return stats_text
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return f"Error: {str(e)}"


# ============================================================================
# PUNTO DE ENTRADA - Transporte stdio (obligatorio)
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 Iniciando Bancolombia MCP Server")
    logger.info(f"📦 Versión: 1.0.0")
    logger.info(f"🔌 Transporte: stdio")
    logger.info(f"📂 ChromaDB path: {CHROMA_PATH}")
    
    # Validar que ChromaDB tiene datos
    stats = db.get_stats()
    if stats['total_documents'] == 0:
        logger.warning("⚠️  Base de conocimiento vacía. Ejecuta primero: python src/main.py --index-chromadb")
    else:
        logger.info(f"✅ Base de conocimiento lista: {stats['total_documents']} documentos")
    
    # Iniciar servidor MCP con transporte stdio
    mcp.run(transport="stdio")
