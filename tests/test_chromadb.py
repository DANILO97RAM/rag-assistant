"""
Tests para ChromaDBService.

Valida:
- Creación de colección
- Indexación de documentos
- Búsqueda semántica
- Filtrado por URL
- Listado de categorías
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import tempfile
import shutil

# Agregar src al path (funciona tanto desde tests/ como tests/db/)
project_root = Path(__file__).parent.parent
if project_root.name == "db":  # Si estamos en tests/db/
    project_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))

from services.database import ChromaDBService


@pytest.fixture
def sample_chunks_df():
    """DataFrame de ejemplo con chunks"""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "metadata": [
            '{"url": "https://www.bancolombia.com/personas/productos/tarjetas-credito", "title": "Tarjetas de Crédito", "category": "productos", "fecha_extraccion": "2026-04-09T14:30:00"}',
            '{"url": "https://www.bancolombia.com/personas/productos/tarjetas-credito", "title": "Tarjetas de Crédito", "category": "productos", "fecha_extraccion": "2026-04-09T14:30:00"}',
            '{"url": "https://www.bancolombia.com/personas/creditos/hipotecario", "title": "Crédito Hipotecario", "category": "creditos", "fecha_extraccion": "2026-04-09T14:30:00"}'
        ],
        "texto": [
            "Las tarjetas de crédito Bancolombia ofrecen beneficios exclusivos",
            "Solicita tu tarjeta de crédito en línea de forma rápida y segura",
            "El crédito hipotecario te permite comprar tu vivienda con tasas competitivas"
        ]
    })


@pytest.fixture
def sample_embeddings_df():
    """DataFrame de ejemplo con embeddings (384 dims)"""
    import numpy as np
    return pd.DataFrame({
        "chunk_id": [0, 1, 2],
        "embedding": [
            np.random.rand(384).tolist(),
            np.random.rand(384).tolist(),
            np.random.rand(384).tolist()
        ]
    })


@pytest.fixture
def db_service():
    """ChromaDBService para tests (con directorio temporal)"""
    # Usar directorio temporal del sistema (siempre tiene permisos de escritura)
    test_dir = Path(tempfile.mkdtemp(prefix="chromadb_test_"))
    
    db = ChromaDBService(persist_directory=str(test_dir))
    db.create_collection(reset=True)  # Limpiar antes de cada test
    
    yield db
    
    # Cleanup - eliminar directorio temporal
    db.reset()
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_create_collection(db_service):
    """Verifica que la colección se crea correctamente"""
    assert db_service.collection is not None
    assert db_service.collection.name == "bancolombia_knowledge"
    assert db_service.collection.metadata["hnsw:space"] == "cosine"
    print("✅ Test 1: Colección creada correctamente")


def test_add_documents(db_service, sample_chunks_df, sample_embeddings_df):
    """Verifica que se indexan los documentos"""
    num_indexed = db_service.add_documents(sample_chunks_df, sample_embeddings_df)
    assert num_indexed == 3
    assert db_service.collection.count() == 3
    print(f"✅ Test 2: {num_indexed} documentos indexados")


def test_search_semantic(db_service, sample_chunks_df, sample_embeddings_df):
    """Búsqueda semántica retorna resultados"""
    # Primero indexar datos
    db_service.add_documents(sample_chunks_df, sample_embeddings_df)
    
    # Buscar
    results = db_service.search("tarjeta de crédito", n_results=2)
    
    assert len(results) > 0
    assert len(results) <= 2
    assert "document" in results[0]
    assert "metadata" in results[0]
    assert "distance" in results[0]
    
    print(f"✅ Test 3: Búsqueda encontró {len(results)} resultados")
    print(f"   Primer resultado: {results[0]['document'][:50]}...")


def test_get_by_url(db_service, sample_chunks_df, sample_embeddings_df):
    """Filtrado por URL funciona correctamente"""
    # Indexar datos
    db_service.add_documents(sample_chunks_df, sample_embeddings_df)
    
    # Buscar por URL
    url = "https://www.bancolombia.com/personas/productos/tarjetas-credito"
    results = db_service.get_by_url(url)
    
    assert len(results) == 2  # Hay 2 chunks con esta URL
    assert all(r["metadata"]["url"] == url for r in results)
    
    print(f"✅ Test 4: Encontrados {len(results)} chunks para URL específica")


def test_get_categories(db_service, sample_chunks_df, sample_embeddings_df):
    """Lista categorías únicas"""
    # Indexar datos
    db_service.add_documents(sample_chunks_df, sample_embeddings_df)
    
    # Obtener categorías
    categories = db_service.get_categories()
    
    assert len(categories) == 2  # "productos" y "creditos"
    assert "productos" in categories
    assert "creditos" in categories
    
    print(f"✅ Test 5: {len(categories)} categorías encontradas: {categories}")


def test_get_stats(db_service, sample_chunks_df, sample_embeddings_df):
    """Estadísticas correctas"""
    # Indexar datos
    db_service.add_documents(sample_chunks_df, sample_embeddings_df)
    
    # Obtener stats
    stats = db_service.get_stats()
    
    assert stats["total_documents"] == 3
    assert stats["num_categories"] == 2
    assert stats["embedding_dimension"] == 384
    assert stats["distance_metric"] == "cosine"
    
    print(f"✅ Test 6: Estadísticas correctas")
    print(f"   Total docs: {stats['total_documents']}")
    print(f"   Categorías: {stats['num_categories']}")


if __name__ == "__main__":
    # Ejecutar tests manualmente
    pytest.main([__file__, "-v", "-s"])
