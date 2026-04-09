"""
Embedder: Genera embeddings de chunks concatenando los header metadata.title + texto del df previamente limpiado y chunked. 
Soporta múltiples proveedores de embeddings (Google Gemini, OpenAI, Sentence Transformers). 

Para este caso, usaremos Gemini como modelo principal, pero se puede configurar fácilmente para usar otros modelos.
Retorna un DataFrame con los embeddings generados.

Diseñado para trabajar con ChromaDB y modelos de embedding configurables.
Aunque puede ser adapatado para otros proveedores, se recomienda usar Gemini para obtener mejores resultados en español 
y su generosa cuota gratuita.

"""

import json
import logging
import pandas as pd
from typing import Optional, List
from abc import ABC, abstractmethod


class BaseEmbeddingModel(ABC):
    """Interfaz para diferentes proveedores de embeddings"""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Retorna la dimensionalidad de los embeddings"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        pass


class GeminiEmbeddingModel(BaseEmbeddingModel):
    """Modelo de embeddings usando Google Gemini"""
    
    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004"):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai no está instalado. "
                "Ejecuta: pip install google-generativeai"
            )
        
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.dimension = 768  # text-embedding-004 tiene 768 dimensiones
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import google.generativeai as genai
        
        embeddings = []
        # Gemini permite batch embedding
        for text in texts:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        
        return embeddings
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_model_name(self) -> str:
        return self.model_name


class SentenceTransformerModel(BaseEmbeddingModel):
    """Modelo de embeddings usando Sentence Transformers (local, gratuito)"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers no está instalado. "
                "Ejecuta: pip install sentence-transformers"
            )
        
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_model_name(self) -> str:
        return self.model_name


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """Modelo de embeddings usando OpenAI"""
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai no está instalado. "
                "Ejecuta: pip install openai"
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        
        # Dimensiones según modelo
        dimensions_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        self.dimension = dimensions_map.get(model_name, 1536)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # OpenAI permite hasta 2048 textos por batch
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_model_name(self) -> str:
        return self.model_name


class Embedder:
    """
    Clase para generar embeddings de chunks.
    
    Concatena metadata.title + '\n' + texto antes de generar el embedding.
    Retorna un DataFrame con los embeddings y metadata.
    """
    
    def __init__(
        self,
        embedding_model: BaseEmbeddingModel,
        batch_size: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        Args:
            embedding_model: Instancia de un modelo de embeddings
            batch_size: Tamaño del batch para procesamiento
            logger: Logger opcional
        """
        self.embedding_model = embedding_model
        self.batch_size = batch_size
        self.logger = logger or logging.getLogger(__name__)
        self.tag = "[Embedder]"
    
    def _extract_title_from_metadata(self, metadata_str: str) -> str:
        """Extrae el título del JSON de metadata"""
        try:
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            return metadata.get("title", "")
        except Exception as e:
            self.logger.warning(f"{self.tag} Error extrayendo título de metadata: {e}")
            return ""
    
    def _prepare_text_for_embedding(self, row: pd.Series) -> str:
        """
        Concatena metadata.title + '\n' + texto para embedding.
        
        Args:
            row: Fila del DataFrame con columnas 'metadata' y 'texto'
        
        Returns:
            String concatenado listo para embedding
        """
        title = self._extract_title_from_metadata(row.get("metadata", ""))
        texto = row.get("texto", "")
        
        # Concatenar título + texto
        if title:
            return f"{title}\n{texto}"
        return texto
    
    def generate_embeddings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera embeddings para cada chunk del DataFrame.
        
        Args:
            df: DataFrame con columnas 'id', 'metadata', 'texto'
        
        Returns:
            DataFrame con columna adicional 'embedding' (List[float])
        """
        if df.empty:
            self.logger.warning(f"{self.tag} DataFrame vacío, no se generan embeddings")
            return df
        
        # Validar columnas requeridas
        required_cols = {"id", "metadata", "texto"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"{self.tag} Faltan columnas requeridas: {missing_cols}"
            )
        
        self.logger.info(
            f"{self.tag} Iniciando generación de embeddings para {len(df)} chunks"
        )
        self.logger.info(
            f"{self.tag} Modelo: {self.embedding_model.get_model_name()}, "
            f"Dimensión: {self.embedding_model.get_dimension()}"
        )
        
        df = df.copy()
        
        # Preparar textos para embedding (título + texto)
        self.logger.debug(f"{self.tag} Preparando textos (title + texto)...")
        texts_to_embed = df.apply(self._prepare_text_for_embedding, axis=1).tolist()
        
        # Generar embeddings en batches
        all_embeddings = []
        total_batches = (len(texts_to_embed) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(texts_to_embed), self.batch_size):
            batch_num = i // self.batch_size + 1
            batch = texts_to_embed[i:i + self.batch_size]
            
            self.logger.info(
                f"{self.tag} Procesando batch {batch_num}/{total_batches} "
                f"({len(batch)} textos)"
            )
            
            try:
                batch_embeddings = self.embedding_model.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                self.logger.error(
                    f"{self.tag} Error en batch {batch_num}: {e}"
                )
                raise
        
        # Agregar embeddings al DataFrame
        df["embedding"] = all_embeddings
        
        self.logger.info(
            f"{self.tag} ✅ Embeddings generados exitosamente: {len(df)} chunks"
        )
        
        return df
    
    def get_embedding_stats(self, df: pd.DataFrame) -> dict:
        """Retorna estadísticas sobre los embeddings generados"""
        if "embedding" not in df.columns:
            return {"error": "No hay embeddings en el DataFrame"}
        
        return {
            "total_embeddings": len(df),
            "embedding_dimension": len(df["embedding"].iloc[0]) if len(df) > 0 else 0,
            "model_name": self.embedding_model.get_model_name(),
            "model_dimension": self.embedding_model.get_dimension(),
        }


# Factory function para facilitar creación de embedders
def create_embedder(
    provider: str = "sentence-transformers",
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    batch_size: int = 100,
    logger: Optional[logging.Logger] = None
) -> Embedder:
    """
    Factory function para crear un Embedder con el provider especificado.
    
    Args:
        provider: "gemini", "openai", o "sentence-transformers"
        api_key: API key para providers comerciales
        model_name: Nombre del modelo (usa defaults si es None)
        batch_size: Tamaño del batch
        logger: Logger opcional
    
    Returns:
        Instancia de Embedder configurada
    """
    provider = provider.lower()
    
    if provider == "gemini":
        if not api_key:
            raise ValueError("API key requerida para Gemini")
        model = GeminiEmbeddingModel(
            api_key=api_key,
            model_name=model_name or "models/text-embedding-004"
        )
    
    elif provider == "openai":
        if not api_key:
            raise ValueError("API key requerida para OpenAI")
        model = OpenAIEmbeddingModel(
            api_key=api_key,
            model_name=model_name or "text-embedding-3-small"
        )
    
    elif provider == "sentence-transformers":
        model = SentenceTransformerModel(
            model_name=model_name or "all-MiniLM-L6-v2"
        )
    
    else:
        raise ValueError(
            f"Provider '{provider}' no soportado. "
            f"Usa: 'gemini', 'openai', o 'sentence-transformers'"
        )
    
    return Embedder(
        embedding_model=model,
        batch_size=batch_size,
        logger=logger
    )
# Implementación completa del Embedder con soporte multi-provider
