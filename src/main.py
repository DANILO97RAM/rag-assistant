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
# from core.embedder import create_embedder
# from services.database import load_knowledge_base

SCRAPING_URL = "https://www.bancolombia.com/personas"
SCRAPING_DEPTH = 2
SCRAPING_MAX_PAGES = 50
SCRAPING_CONCURRENCY = 8
CHUNKS_SIZE = 1024
CHUNKS_OVERLAP = 128

# Paths para persistencia
DATA_DIR = Path("data")
CHUNKS_FILE = DATA_DIR / "chunks.parquet"
SCRAPED_PAGES_FILE = DATA_DIR / "scraped_pages.parquet"


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


def run_pipeline_and_save_embeddings():
    parser = argparse.ArgumentParser(description="RAG Assistant Pipeline")
    parser.add_argument("--url", default=SCRAPING_URL, help="URL para scraping")
    parser.add_argument("--depth", type=int, default=SCRAPING_DEPTH, help="Profundidad de scraping")
    parser.add_argument("--max-pages", type=int, default=SCRAPING_MAX_PAGES, help="Máximo de páginas")
    parser.add_argument("--concurrency", type=int, default=SCRAPING_CONCURRENCY, help="Concurrencia")
    parser.add_argument("--no-save", action="store_true", help="No guardar chunks en disco")
    parser.add_argument("--force-scrape", action="store_true", help="Forzar scraping aunque exista archivo guardado")
    
    args = parser.parse_args()
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