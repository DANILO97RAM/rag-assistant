"""
Tests unitarios para el módulo Embedder.
"""

import pytest
import pandas as pd
import json
from pathlib import Path
import sys

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.embedder import (
    Embedder,
    SentenceTransformerModel,
    create_embedder
)


# Fixtures
@pytest.fixture
def sample_chunks_df():
    """DataFrame de ejemplo con chunks"""
    data = {
        "id": [1, 2, 3],
        "metadata": [
            json.dumps({"title": "Créditos Hipotecarios", "url": "https://example.com/1", "category": "credito"}),
            json.dumps({"title": "Cuenta de Ahorros", "url": "https://example.com/2", "category": "ahorro"}),
            json.dumps({"title": "Tarjetas de Crédito", "url": "https://example.com/3", "category": "tarjetas"}),
        ],
        "texto": [
            "Bancolombia ofrece créditos hipotecarios con tasas competitivas desde el 9% anual.",
            "Abre tu cuenta de ahorros 100% digital sin costo de apertura.",
            "Tarjetas de crédito con hasta 50 días sin intereses y millas de viaje.",
        ]
    }
    return pd.DataFrame(data)


@pytest.fixture
def embedder_sentence_transformers():
    """Embedder con Sentence Transformers (local, no requiere API key)"""
    model = SentenceTransformerModel(model_name="all-MiniLM-L6-v2")
    return Embedder(embedding_model=model, batch_size=2)


# Tests
class TestEmbedder:
    
    def test_prepare_text_concatenates_title_and_text(self, embedder_sentence_transformers, sample_chunks_df):
        """Verifica que se concatene title + texto correctamente"""
        row = sample_chunks_df.iloc[0]
        prepared_text = embedder_sentence_transformers._prepare_text_for_embedding(row)
        
        assert "Créditos Hipotecarios" in prepared_text
        assert "Bancolombia ofrece créditos" in prepared_text
        assert "\n" in prepared_text  # Separador
    
    def test_extract_title_from_metadata(self, embedder_sentence_transformers):
        """Verifica extracción de título desde metadata JSON"""
        metadata = json.dumps({"title": "Test Title", "url": "https://test.com"})
        title = embedder_sentence_transformers._extract_title_from_metadata(metadata)
        
        assert title == "Test Title"
    
    def test_extract_title_handles_missing_title(self, embedder_sentence_transformers):
        """Verifica manejo de metadata sin título"""
        metadata = json.dumps({"url": "https://test.com"})
        title = embedder_sentence_transformers._extract_title_from_metadata(metadata)
        
        assert title == ""
    
    def test_generate_embeddings_returns_correct_shape(self, embedder_sentence_transformers, sample_chunks_df):
        """Verifica que se generen embeddings con la forma correcta"""
        result_df = embedder_sentence_transformers.generate_embeddings(sample_chunks_df)
        
        # Debe tener columna 'embedding'
        assert "embedding" in result_df.columns
        
        # Debe tener el mismo número de filas
        assert len(result_df) == len(sample_chunks_df)
        
        # Cada embedding debe ser una lista de floats
        assert isinstance(result_df["embedding"].iloc[0], list)
        assert all(isinstance(x, float) for x in result_df["embedding"].iloc[0])
    
    def test_generate_embeddings_correct_dimension(self, embedder_sentence_transformers, sample_chunks_df):
        """Verifica que los embeddings tengan la dimensión correcta"""
        result_df = embedder_sentence_transformers.generate_embeddings(sample_chunks_df)
        
        # all-MiniLM-L6-v2 tiene 384 dimensiones
        expected_dim = 384
        assert len(result_df["embedding"].iloc[0]) == expected_dim
    
    def test_generate_embeddings_empty_dataframe(self, embedder_sentence_transformers):
        """Verifica manejo de DataFrame vacío"""
        empty_df = pd.DataFrame(columns=["id", "metadata", "texto"])
        result_df = embedder_sentence_transformers.generate_embeddings(empty_df)
        
        assert len(result_df) == 0
    
    def test_generate_embeddings_missing_columns_raises_error(self, embedder_sentence_transformers):
        """Verifica que lance error si faltan columnas requeridas"""
        invalid_df = pd.DataFrame({"id": [1, 2], "texto": ["text1", "text2"]})
        
        with pytest.raises(ValueError, match="Faltan columnas requeridas"):
            embedder_sentence_transformers.generate_embeddings(invalid_df)
    
    def test_get_embedding_stats(self, embedder_sentence_transformers, sample_chunks_df):
        """Verifica que las estadísticas se calculen correctamente"""
        result_df = embedder_sentence_transformers.generate_embeddings(sample_chunks_df)
        stats = embedder_sentence_transformers.get_embedding_stats(result_df)
        
        assert stats["total_embeddings"] == 3
        assert stats["embedding_dimension"] == 384
        assert stats["model_name"] == "all-MiniLM-L6-v2"
    
    def test_factory_creates_sentence_transformer_embedder(self):
        """Verifica que la factory function cree un embedder correctamente"""
        embedder = create_embedder(provider="sentence-transformers")
        
        assert isinstance(embedder, Embedder)
        assert embedder.embedding_model.get_model_name() == "all-MiniLM-L6-v2"
    
    def test_factory_invalid_provider_raises_error(self):
        """Verifica que lance error con provider inválido"""
        with pytest.raises(ValueError, match="no soportado"):
            create_embedder(provider="invalid_provider")
    
    def test_batch_processing(self, sample_chunks_df):
        """Verifica que el procesamiento por batches funcione"""
        model = SentenceTransformerModel(model_name="all-MiniLM-L6-v2")
        embedder = Embedder(embedding_model=model, batch_size=2)  # Batch pequeño
        
        result_df = embedder.generate_embeddings(sample_chunks_df)
        
        # Debe procesar todos los chunks incluso con batch_size pequeño
        assert len(result_df) == 3
        assert "embedding" in result_df.columns


# Test de integración (opcional, requiere modelo descargado)
@pytest.mark.integration
class TestEmbedderIntegration:
    
    def test_end_to_end_embedding_pipeline(self, sample_chunks_df, tmp_path):
        """Test de integración completo: generar embeddings y guardar"""
        # Crear embedder
        embedder = create_embedder(provider="sentence-transformers")
        
        # Generar embeddings
        result_df = embedder.generate_embeddings(sample_chunks_df)
        
        # Guardar en disco
        output_file = tmp_path / "embeddings.parquet"
        result_df.to_parquet(output_file, index=False)
        
        # Verificar que se guardó correctamente
        assert output_file.exists()
        
        # Cargar y verificar
        loaded_df = pd.read_parquet(output_file)
        assert len(loaded_df) == len(sample_chunks_df)
        assert "embedding" in loaded_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
# Tests completos para el módulo Embedder