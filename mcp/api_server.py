#!/usr/bin/env python3
"""
API REST - Bancolombia Knowledge Base

Servidor HTTP para testing con Postman/Insomnia.
Expone las mismas funcionalidades que el servidor MCP pero vía REST.

Endpoints:
- POST /search - Búsqueda semántica
- GET /article - Obtener artículo por URL
- GET /categories - Listar categorías
- GET /stats - Estadísticas de la base de datos
"""

import sys
from pathlib import Path
from typing import List, Optional
import logging
import uvicorn

# Agregar src al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from services.database import ChromaDBService

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="Bancolombia Knowledge API",
    description="API REST para consultar la base de conocimiento de Bancolombia",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir requests desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar ChromaDB
CHROMA_PATH = str(project_root / "data" / "chroma_db")
logger.info(f"🔌 Conectando a ChromaDB en {CHROMA_PATH}")

try:
    db = ChromaDBService(persist_directory=CHROMA_PATH)
    db.create_collection()
    logger.info("✅ ChromaDB conectado exitosamente")
except Exception as e:
    logger.error(f"❌ Error conectando a ChromaDB: {e}")
    raise


# ============================================================================
# MODELOS PYDANTIC (Request/Response)
# ============================================================================

class SearchRequest(BaseModel):
    query: str = Field(..., description="Consulta en lenguaje natural", min_length=1)
    n_results: int = Field(5, description="Número de resultados", ge=1, le=10)
    category: Optional[str] = Field(None, description="Filtro por categoría")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "¿Qué seguros ofrece Bancolombia?",
                "n_results": 3,
                "category": "seguros"
            }
        }


class DocumentResult(BaseModel):
    rank: int
    content: str
    url: str
    title: str
    category: str
    similarity_score: float
    word_count: int


class SearchResponse(BaseModel):
    query: str
    total_results: int
    documents: List[DocumentResult]


class ChunkInfo(BaseModel):
    content: str
    chunk_index: int
    word_count: int


class ArticleResponse(BaseModel):
    url: str
    total_chunks: int
    title: str
    category: str
    chunks: List[ChunkInfo]


class CategoriesResponse(BaseModel):
    total_categories: int
    categories: List[str]


class StatsResponse(BaseModel):
    status: str
    total_documents: int
    num_categories: int
    embedding_dimension: int
    distance_metric: str
    fecha_ultima_actualizacion: str
    source: str
    categories: List[str]


# ============================================================================
# ENDPOINTS REST
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Bancolombia Knowledge API",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_knowledge_base(request: SearchRequest):
    """
    Ejecuta búsqueda semántica en la base de conocimiento.
    
    **Ejemplo de request:**
    ```json
    {
      "query": "¿Qué seguros ofrece Bancolombia?",
      "n_results": 3
    }
    ```
    """
    try:
        # Preparar filtro
        where_filter = {"category": request.category} if request.category else None
        
        # Ejecutar búsqueda
        results = db.search(
            query=request.query,
            n_results=request.n_results,
            where=where_filter
        )
        
        # Formatear respuesta
        documents = []
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            similarity_score = 1 - result.get('distance', 0.0)
            
            documents.append(DocumentResult(
                rank=i,
                content=result['document'],
                url=metadata.get('url', 'N/A'),
                title=metadata.get('title', 'Sin título'),
                category=metadata.get('category', 'Sin categoría'),
                similarity_score=round(similarity_score, 3),
                word_count=metadata.get('word_count', 0)
            ))
        
        logger.info(f"🔍 Búsqueda: '{request.query[:50]}...' → {len(results)} resultados")
        
        return SearchResponse(
            query=request.query,
            total_results=len(documents),
            documents=documents
        )
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/article", response_model=ArticleResponse, tags=["Articles"])
async def get_article_by_url(
    url: str = Query(..., description="URL completa del artículo de bancolombia.com")
):
    """
    Recupera el contenido completo de un artículo mediante su URL.
    
    **Ejemplo:**
    ```
    GET /article?url=https://www.bancolombia.com/personas/creditos
    ```
    """
    try:
        # Validación
        if not url.startswith("https://www.bancolombia.com"):
            raise HTTPException(
                status_code=400,
                detail="URL debe ser de bancolombia.com"
            )
        
        # Recuperar chunks
        chunks = db.get_by_url(url)
        
        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró artículo para URL: {url}"
            )
        
        # Formatear respuesta
        chunk_list = []
        for chunk in chunks:
            chunk_list.append(ChunkInfo(
                content=chunk['document'],
                chunk_index=chunk['metadata'].get('chunk_index', 0),
                word_count=chunk['metadata'].get('word_count', 0)
            ))
        
        logger.info(f"📄 Artículo recuperado: {url} → {len(chunks)} chunks")
        
        return ArticleResponse(
            url=url,
            total_chunks=len(chunks),
            title=chunks[0]['metadata'].get('title', 'Sin título'),
            category=chunks[0]['metadata'].get('category', 'Sin categoría'),
            chunks=chunk_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recuperando artículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories", response_model=CategoriesResponse, tags=["Categories"])
async def list_categories():
    """
    Lista todas las categorías disponibles en la base de conocimiento.
    
    **Ejemplo:**
    ```
    GET /categories
    ```
    """
    try:
        categories = db.get_categories()
        
        logger.info(f"📁 Categorías listadas: {len(categories)} encontradas")
        
        return CategoriesResponse(
            total_categories=len(categories),
            categories=sorted(categories)
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando categorías: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    """
    Obtiene estadísticas de la base de conocimiento.
    
    **Ejemplo:**
    ```
    GET /stats
    ```
    """
    try:
        stats = db.get_stats()
        
        logger.info("📊 Estadísticas consultadas")
        
        return StatsResponse(
            status="operational",
            total_documents=stats['total_documents'],
            num_categories=stats['num_categories'],
            embedding_dimension=stats['embedding_dimension'],
            distance_metric=stats['distance_metric'],
            fecha_ultima_actualizacion=stats['fecha_ultima_actualizacion'],
            source="https://www.bancolombia.com/personas",
            categories=stats['categories'][:20]  # Primeras 20
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 Iniciando Bancolombia API REST")
    logger.info(f"📦 Versión: 1.0.0")
    logger.info(f"📂 ChromaDB path: {CHROMA_PATH}")
    
    # Validar datos
    stats = db.get_stats()
    if stats['total_documents'] == 0:
        logger.warning("⚠️  Base de conocimiento vacía")
    else:
        logger.info(f"✅ Base lista: {stats['total_documents']} documentos")
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
# Commented by GitHub Copilot
