"""
Función principal del programa.
Llama al scraping, limpia el df, genera chunks y carga la base de conocimiento.
"""

import logging
import argparse
from pathlib import Path
import pandas as pd

from config.logger import setup_logging
from core.scrapper import run_scrapping
from core.cleaner import TextCleaner
from core.chunker import Chunker

SCRAPING_URL = "https://www.bancolombia.com/personas"
SCRAPING_DEPTH = 2
SCRAPING_MAX_PAGES = 50
SCRAPING_CONCURRENCY = 8
CHUNKS_SIZE = 1024
CHUNKS_OVERLAP = 128

DATA_DIR = Path("data")
CHUNKS_FILE = DATA_DIR / "chunks.parquet"
SCRAPED_PAGES_FILE = DATA_DIR / "scraped_pages.parquet"
EMBEDDINGS_FILE = DATA_DIR / "embeddings_sentence-transformers.parquet"  # Usar el archivo correcto (con guion)


def run(url, depth, max_pages, concurrency, save_chunks=True, force_scrape=False):
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🚀 Pipeline iniciado")

    # Crear directorio de datos si no existe
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Fase 1: Scraping (o cargar desde disco)
    if not force_scrape and SCRAPED_PAGES_FILE.exists():
        logger.info(f"📂 Cargando páginas scrapeadas desde {SCRAPED_PAGES_FILE}")
        df = pd.read_parquet(SCRAPED_PAGES_FILE)
        logger.info(f"✅ {len(df)} páginas cargadas desde disco")
    else:
        logger.info("📡 Fase 1: Web Scraping")
        df = run_scrapping(
            url=url,
            depth=depth,
            max_pages=max_pages,
            concurrency=concurrency,
        )
        if df is None:
            logger.warning("No se generó DataFrame. Pipeline detenido.")
            return None

        logger.info(f"✅ Scraping completado: {len(df)} páginas")
        
        # Guardar páginas scrapeadas
        logger.info(f"💾 Guardando páginas scrapeadas en {SCRAPED_PAGES_FILE}")
        df.to_parquet(SCRAPED_PAGES_FILE, index=False)
        logger.info(f"✅ Páginas guardadas exitosamente")

    # Fase 2: Limpieza
    logger.info("🧹 Fase 2: Limpieza de texto")
    cleaner = TextCleaner(df, logger=logger)
    df = cleaner.transform()
    logger.info(f"✅ Limpieza completada")

    # Fase 3: Chunking (ahora con overlap=128)
    logger.info(F"✂️  Fase 3: Chunking (chunk_size={CHUNKS_SIZE}, overlap={CHUNKS_OVERLAP})")
    chunker = Chunker(logger=logger, chunk_size=int(CHUNKS_SIZE), chunk_overlap=int(CHUNKS_OVERLAP))
    df = chunker.get_chunks(df)
    logger.info(f"✅ Chunks generados: {len(df)}")

    # Guardar chunks en disco
    if save_chunks:
        logger.info(f"💾 Guardando chunks en {CHUNKS_FILE}")
        df.to_parquet(CHUNKS_FILE, index=False)
        logger.info(f"✅ Chunks guardados exitosamente")
        
        # Validación estadística
        if "texto" in df.columns:
            df_temp = df.copy()
            df_temp['word_count'] = df_temp['texto'].apply(lambda x: len(str(x).split()))
            stats = df_temp['word_count'].describe()
            logger.info(
                f"📊 Estadísticas de palabras por chunk:\n"
                f"   - Media: {stats['mean']:.1f}\n"
                f"   - P50 (mediana): {stats['50%']:.1f}\n"
                f"   - P75: {stats['75%']:.1f}\n"
                f"   - Máximo: {stats['max']:.1f}"
            )

    logger.info("🎉 Pipeline completado exitosamente")
    return df

def load_chunks_from_disk():
    """Carga chunks guardados en disco"""
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de chunks en {CHUNKS_FILE}. "
            "Ejecuta el pipeline primero."
        )
    
    logger = logging.getLogger(__name__)
    logger.info(f"📂 Cargando chunks desde {CHUNKS_FILE}")
    df = pd.read_parquet(CHUNKS_FILE)
    logger.info(f"✅ {len(df)} chunks cargados")
    return df


def index_to_chromadb(reset: bool = False):
    """Indexa chunks y embeddings en ChromaDB.
    
    Args:
        reset: Si True, borra la colección existente y crea una nueva
    """
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Iniciando indexación en ChromaDB")
    
    # Verificar que existan los archivos necesarios
    if not CHUNKS_FILE.exists():
        logger.error(f"❌ No se encontró {CHUNKS_FILE}")
        logger.error("   Ejecuta primero: python src/main.py")
        return False
    
    if not EMBEDDINGS_FILE.exists():
        logger.error(f"❌ No se encontró {EMBEDDINGS_FILE}")
        logger.error("   Ejecuta primero el script de embeddings")
        return False
    
    # Cargar datos
    logger.info(f"📂 Cargando chunks desde {CHUNKS_FILE}")
    chunks_df = pd.read_parquet(CHUNKS_FILE)
    logger.info(f"✅ {len(chunks_df)} chunks cargados")
    
    logger.info(f"📂 Cargando embeddings desde {EMBEDDINGS_FILE}")
    embeddings_df = pd.read_parquet(EMBEDDINGS_FILE)
    logger.info(f"✅ {len(embeddings_df)} embeddings cargados")
    
    # Crear servicio de ChromaDB
    from services.database import ChromaDBService
    
    db = ChromaDBService()
    db.create_collection(reset=reset)
    
    # Indexar documentos
    try:
        num_indexed = db.add_documents(chunks_df, embeddings_df)
        logger.info(f"✅ {num_indexed} documentos indexados en ChromaDB")
        
        # Mostrar estadísticas
        stats = db.get_stats()
        logger.info(f"📊 Estadísticas de ChromaDB:")
        logger.info(f"   - Total documentos: {stats['total_documents']}")
        logger.info(f"   - Categorías: {stats['num_categories']}")
        logger.info(f"   - Dimensiones: {stats['embedding_dimension']}")
        logger.info(f"   - Métrica: {stats['distance_metric']}")
        logger.info(f"   - Última actualización: {stats['fecha_ultima_actualizacion']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error indexando en ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_pipeline_and_save_embeddings():
    parser = argparse.ArgumentParser(description="RAG Assistant Pipeline")
    parser.add_argument("--url", default=SCRAPING_URL, help="URL para scraping")
    parser.add_argument("--depth", type=int, default=SCRAPING_DEPTH, help="Profundidad de scraping")
    parser.add_argument("--max-pages", type=int, default=SCRAPING_MAX_PAGES, help="Máximo de páginas")
    parser.add_argument("--concurrency", type=int, default=SCRAPING_CONCURRENCY, help="Concurrencia")
    parser.add_argument("--no-save", action="store_true", help="No guardar chunks en disco")
    parser.add_argument("--force-scrape", action="store_true", help="Forzar scraping aunque exista archivo guardado")
    parser.add_argument("--index-chromadb", action="store_true", help="Indexar chunks en ChromaDB")
    parser.add_argument("--reset-chromadb", action="store_true", help="Resetear ChromaDB antes de indexar")
    
    args = parser.parse_args()
    
    # Si se solicita indexar en ChromaDB
    if args.index_chromadb:
        success = index_to_chromadb(reset=args.reset_chromadb)
        if success:
            print("\n✅ Indexación completada exitosamente")
        else:
            print("\n❌ La indexación falló")
        return
    
    # De lo contrario, ejecutar pipeline normal
    run(
        args.url, 
        args.depth, 
        args.max_pages, 
        args.concurrency,
        save_chunks=not args.no_save,
        force_scrape=args.force_scrape
    )
if __name__ == "__main__":
    
    run_pipeline_and_save_embeddings()

    # load_chunks_from_disk()