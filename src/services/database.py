"""
Servicio de base de datos vectorial usando ChromaDB.

Proporciona funcionalidades para:
- Almacenamiento persistente de embeddings (mediante ChromaDB Server)
- Búsqueda semántica por similitud coseno
- Filtrado por metadatos (URL, categoría)
- Estadísticas de la base de conocimiento

Soporta dos modos:
1. **HTTP Client**: Conexión a ChromaDB Docker (producción/desarrollo)
2. **Persistent Client**: ChromaDB local embebido (testing, legacy)

ChromaDB es una base de datos vectorial open-source optimizada para
aplicaciones de IA y retrieval semántico.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import pandas as pd
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class ChromaDBService:
    """Servicio de base de datos vectorial con ChromaDB.
    
    Características:
    - Conexión HTTP a ChromaDB Server (Docker)
    - Distancia coseno para búsqueda semántica
    - Metadatos: url, title, category, fecha_extraccion, chunk_index, etc.
    - IDs determinísticos con SHA256
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        use_local: bool = False,
        persist_directory: str = "data/chroma_db"
    ):
        """Inicializa el servicio de ChromaDB.
        
        Args:
            host: Host del servidor ChromaDB (default: localhost, de .env)
            port: Puerto del servidor ChromaDB (default: 8000, de .env)
            use_local: Si True, usa PersistentClient local (testing)
            persist_directory: Directorio para modo local
        """
        # Configuración desde variables de entorno
        self.host = host or os.getenv("CHROMA_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMA_PORT", "8000"))
        self.use_local = use_local
        
        if self.use_local:
            # Modo local (testing/desarrollo sin Docker)
            self.persist_directory = Path(persist_directory)
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📦 [LOCAL] ChromaDB en {self.persist_directory}")
            
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        else:
            # Modo HTTP (producción con Docker)
            logger.info(f"🌐 [HTTP] Conectando a ChromaDB en {self.host}:{self.port}")
            
            try:
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                # Test de conexión
                self.client.heartbeat()
                logger.info(f"✅ Conexión exitosa a ChromaDB Server")
            except Exception as e:
                logger.error(f"❌ Error conectando a ChromaDB: {e}")
                logger.error(f"   Verifica que Docker esté ejecutándose: docker-compose up -d")
                raise
        
        self.collection_name = "bancolombia_knowledge"
        self.collection = None
        
    def create_collection(self, reset: bool = False) -> chromadb.Collection:
        """Crea o carga la colección de ChromaDB.
        
        Args:
            reset: Si True, elimina colección existente y crea nueva
        
        Returns:
            Colección de ChromaDB
        """
        if reset and self.collection_name in [c.name for c in self.client.list_collections()]:
            logger.warning(f"⚠️ Eliminando colección existente: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
        
        # Crear o cargar colección con distancia coseno
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Distancia coseno
        )
        
        logger.info(f"✅ Colección '{self.collection_name}' lista (documentos: {self.collection.count()})")
        return self.collection
    
    def _generate_chunk_id(self, title: str, texto: str, index: int) -> str:
        """Genera ID determinístico usando SHA256.
        
        Args:
            title: Título del artículo
            texto: Contenido del chunk
            index: Índice del chunk para garantizar unicidad
        
        Returns:
            Hash SHA256 de 16 caracteres
        """
        content = f"{title}\n{index}\n{texto}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def add_documents(
        self,
        chunks_df: pd.DataFrame,
        embeddings_df: pd.DataFrame
    ) -> int:
        """Indexa chunks con embeddings y metadatos en ChromaDB.
        
        Args:
            chunks_df: DataFrame con columnas [id, metadata, texto]
            embeddings_df: DataFrame con columnas [chunk_id, embedding]
        
        Returns:
            Número de documentos indexados
        """
        if self.collection is None:
            self.create_collection()
        
        logger.info(f"📥 Preparando {len(chunks_df)} chunks para indexación...")
        
        # Validar que tengamos el mismo número de chunks y embeddings
        if len(chunks_df) != len(embeddings_df):
            raise ValueError(
                f"Mismatch: {len(chunks_df)} chunks vs {len(embeddings_df)} embeddings"
            )
        
        # Preparar datos para ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for idx, (chunk_row, emb_row) in enumerate(zip(chunks_df.itertuples(), embeddings_df.itertuples())):
            # Parsear metadata JSON
            metadata_dict = json.loads(chunk_row.metadata)
            
            # Extraer información
            url = metadata_dict.get("url", "")
            title = metadata_dict.get("title", "")
            category = metadata_dict.get("category", "")
            fecha_extraccion = metadata_dict.get("fecha_extraccion", "")
            texto = chunk_row.texto
            
            # Generar ID determinístico (incluye índice para garantizar unicidad)
            chunk_id = self._generate_chunk_id(title, texto, idx)
            
            # Calcular metadatos adicionales
            word_count = len(texto.split())
            
            # Embedding (puede estar en columna 'embedding' o ser el objeto completo)
            if hasattr(emb_row, 'embedding'):
                embedding = emb_row.embedding
            else:
                # Si no hay columna 'embedding', asumir que es un array directo
                embedding = list(emb_row)[1:]  # Saltar el índice
            
            # Convertir a lista si es necesario
            if not isinstance(embedding, list):
                embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            # Construir metadata completa
            metadata = {
                "url": url,
                "title": title,
                "category": category,
                "fecha_extraccion": fecha_extraccion,
                "chunk_index": idx,
                "word_count": word_count,
                "source_page_id": str(chunk_row.id)
            }
            
            ids.append(chunk_id)
            documents.append(texto)
            embeddings.append(embedding)
            metadatas.append(metadata)
        
        # Insertar en batch
        logger.info(f"💾 Indexando {len(ids)} documentos en ChromaDB...")
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        logger.info(f"✅ {len(ids)} documentos indexados exitosamente")
        return len(ids)
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica en la base de conocimiento.
        
        Args:
            query: Consulta en lenguaje natural
            n_results: Número de resultados a retornar
            where: Filtro opcional por metadatos (ej: {"category": "productos"})
        
        Returns:
            Lista de documentos con metadatos y scores
        """
        if self.collection is None:
            self.create_collection()
        
        # Importar embedder para generar embedding del query
        from core.embedder import create_embedder
        
        # Usar Sentence Transformers (debe coincidir con los embeddings indexados)
        embedder = create_embedder("sentence-transformers")
        query_embedding = embedder.embedding_model.embed_documents([query])[0]
        
        # Buscar en ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Formatear resultados
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def get_by_url(self, url: str) -> List[Dict[str, Any]]:
        """Obtiene todos los chunks de una URL específica.
        
        Args:
            url: URL del artículo
        
        Returns:
            Lista de chunks con metadatos
        """
        if self.collection is None:
            self.create_collection()
        
        results = self.collection.get(
            where={"url": url}
        )
        
        formatted_results = []
        for i in range(len(results['ids'])):
            formatted_results.append({
                "id": results['ids'][i],
                "document": results['documents'][i],
                "metadata": results['metadatas'][i]
            })
        
        return formatted_results
    
    def get_categories(self) -> List[str]:
        """Lista todas las categorías únicas en la base de conocimiento.
        
        Returns:
            Lista de categorías únicas
        """
        if self.collection is None:
            self.create_collection()
        
        # Obtener todos los metadatos
        results = self.collection.get()
        
        # Extraer categorías únicas
        categories = set()
        for metadata in results['metadatas']:
            if 'category' in metadata and metadata['category']:
                categories.add(metadata['category'])
        
        return sorted(list(categories))
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de conocimiento.
        
        Returns:
            Diccionario con estadísticas
        """
        if self.collection is None:
            self.create_collection()
        
        count = self.collection.count()
        categories = self.get_categories()
        
        # Obtener fecha de última actualización (del primer documento)
        if count > 0:
            sample = self.collection.get(limit=1)
            fecha_extraccion = sample['metadatas'][0].get('fecha_extraccion', 'N/A')
        else:
            fecha_extraccion = 'N/A'
        
        return {
            "total_documents": count,
            "categories": categories,
            "num_categories": len(categories),
            "fecha_ultima_actualizacion": fecha_extraccion,
            "collection_name": self.collection_name,
            "embedding_dimension": 384,  # Sentence Transformers
            "distance_metric": "cosine"
        }
    
    def reset(self):
        """Elimina todos los datos de la colección."""
        if self.collection_name in [c.name for c in self.client.list_collections()]:
            self.client.delete_collection(self.collection_name)
            logger.info(f"🗑️ Colección '{self.collection_name}' eliminada")
        self.collection = None


# Función auxiliar para uso directo
def get_database(
    host: Optional[str] = None,
    port: Optional[int] = None,
    use_local: bool = False
) -> ChromaDBService:
    """Helper para obtener instancia de ChromaDBService.
    
    Args:
        host: Host de ChromaDB (None = usar .env)
        port: Puerto de ChromaDB (None = usar .env)
        use_local: Si True, usa PersistentClient local
    
    Returns:
        Instancia de ChromaDBService
    """
    return ChromaDBService(host=host, port=port, use_local=use_local)


if __name__ == "__main__":
    # Test básico de conexión
    print("🧪 Testing ChromaDBService...")
    db = ChromaDBService()  # Usa variables de entorno (.env)
    db.create_collection()
    stats = db.get_stats()
    print(f"✅ ChromaDBService funcionando")
    print(f"   Documentos: {stats['total_documents']}")
    print(f"   Categorías: {stats['num_categories']}")