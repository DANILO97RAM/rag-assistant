"""
Script de ejemplo para generar embeddings desde chunks guardados.

Uso:
    python generate_embeddings.py --provider sentence-transformers
    python generate_embeddings.py --provider gemini --api-key $GEMINI_API_KEY
"""

import argparse
import logging
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.logger import setup_logging
from main import load_chunks_from_disk, DATA_DIR
from core.embedder import create_embedder

# Cargar variables de entorno
load_dotenv()



def main():
    parser = argparse.ArgumentParser(description="Generar embeddings desde chunks")
    parser.add_argument(
        "--provider",
        choices=["sentence-transformers", "gemini", "openai"],
        default=os.getenv("EMBEDDING_PROVIDER", "sentence-transformers"),
        help="Provider de embeddings"
    )
    parser.add_argument("--api-key", help="API key (sobrescribe .env)")
    parser.add_argument("--model", help="Nombre del modelo (sobrescribe defaults)")
    parser.add_argument("--batch-size", type=int, default=100, help="Tamaño del batch")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Iniciando generación de embeddings")
    
    # Cargar chunks desde disco
    try:
        df_chunks = load_chunks_from_disk()
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        logger.error("💡 Ejecuta primero: python src/main.py")
        return
    
    # Obtener API key
    api_key = args.api_key
    if not api_key and args.provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
    elif not api_key and args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
    
    # Crear embedder
    try:
        logger.info(f"🤖 Creando embedder con provider: {args.provider}")
        embedder = create_embedder(
            provider=args.provider,
            api_key=api_key,
            model_name=args.model,
            batch_size=args.batch_size,
            logger=logger
        )
    except ValueError as e:
        logger.error(f"❌ Error creando embedder: {e}")
        return
    
    # Generar embeddings
    try:
        df_with_embeddings = embedder.generate_embeddings(df_chunks)
    except Exception as e:
        logger.error(f"❌ Error generando embeddings: {e}")
        raise
    
    # Guardar en disco
    EMBEDDINGS_FILE = DATA_DIR / f"embeddings_{args.provider}.parquet"
    logger.info(f"💾 Guardando embeddings en {EMBEDDINGS_FILE}")
    df_with_embeddings.to_parquet(EMBEDDINGS_FILE, index=False)
    
    # Mostrar estadísticas
    stats = embedder.get_embedding_stats(df_with_embeddings)
    logger.info("📊 Estadísticas de embeddings:")
    for key, value in stats.items():
        logger.info(f"   - {key}: {value}")
    
    logger.info(f"✅ Embeddings generados y guardados exitosamente")


if __name__ == "__main__":
    main()
