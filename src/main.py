"""
Función principal del programa.
Llama al scraping, limpia el df, genera chunks y carga la base de conocimiento.
"""

import logging
import argparse

from config.logger import setup_logging
from core.scrapper import run_scrapping
from core.cleaner import TextCleaner
from core.chunker import Chunker
# from core.services.database import load_knowledge_base

SCRAPING_URL = "https://www.bancolombia.com/personas"
SCRAPING_DEPTH = 2
SCRAPING_MAX_PAGES = 50
SCRAPING_CONCURRENCY = 8


def run(url, depth, max_pages, concurrency):
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Pipeline iniciado")

    df = run_scrapping(
        url=url,
        depth=depth,
        max_pages=max_pages,
        concurrency=concurrency,
    )
    if df is None:
        logger.warning("No se generó DataFrame. Pipeline detenido.")
        return

    cleaner = TextCleaner(df, logger=logger)
    df = cleaner.transform()

    chunker = Chunker(logger=logger)
    df = chunker.get_chunks(df)

    logger.info("Pipeline completado. Chunks generados: %d", len(df))
    # load_knowledge_base(df)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Assistant Pipeline")
    parser.add_argument("--url", default=SCRAPING_URL, help="URL para scraping")
    parser.add_argument("--depth", type=int, default=SCRAPING_DEPTH, help="Profundidad de scraping")
    parser.add_argument("--max-pages", type=int, default=SCRAPING_MAX_PAGES, help="Máximo de páginas")
    parser.add_argument("--concurrency", type=int, default=SCRAPING_CONCURRENCY, help="Concurrencia")
    
    args = parser.parse_args()
    run(args.url, args.depth, args.max_pages, args.concurrency)
# Parámetros configurables desde línea de comandos