"""
Script para comparar embeddings de diferentes providers.

Genera embeddings con Sentence Transformers y Gemini,
luego compara dimensionalidad, tiempo de ejecución y estadísticas.

Uso:
    python tests/compare_embeddings.py --gemini-key $GEMINI_API_KEY
    python tests/compare_embeddings.py --gemini-key $GEMINI_API_KEY --sample-size 20
"""

import argparse
import logging
import sys
import time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import os

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.logger import setup_logging
from main import load_chunks_from_disk, DATA_DIR
from core.embedder import create_embedder

load_dotenv()

def generate_embeddings_with_provider(
    df: pd.DataFrame, 
    provider: str, 
    api_key: str = None,
    logger = None
) -> tuple:
    """Genera embeddings y mide tiempo"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🤖 Generando embeddings con: {provider.upper()}")
    logger.info(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        embedder = create_embedder(
            provider=provider,
            api_key=api_key,
            batch_size=100,
            logger=logger
        )
        
        df_result = embedder.generate_embeddings(df)
        stats = embedder.get_embedding_stats(df_result)
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")
        logger.info(f"📊 Estadísticas:")
        for key, value in stats.items():
            logger.info(f"   - {key}: {value}")
        
        return df_result, stats, elapsed_time
    
    except Exception as e:
        logger.error(f"❌ Error con {provider}: {e}")
        return None, None, None


def compare_embeddings_quality(
    df_sentence: pd.DataFrame,
    df_gemini: pd.DataFrame,
    logger
):
    """Compara calidad de embeddings (análisis básico)"""
    logger.info(f"\n{'='*80}")
    logger.info("🔍 COMPARACIÓN DE EMBEDDINGS")
    logger.info(f"{'='*80}")
    
    # Tamaño de embeddings
    st_size = len(df_sentence["embedding"].iloc[0])
    gemini_size = len(df_gemini["embedding"].iloc[0])
    
    logger.info(f"\n📏 Dimensionalidad:")
    logger.info(f"   - Sentence Transformers: {st_size} dims")
    logger.info(f"   - Gemini: {gemini_size} dims")
    logger.info(f"   - Diferencia: {gemini_size - st_size} dims (Gemini tiene {gemini_size/st_size:.1f}x más)")
    
    # Comparar primeras normas L2 (magnitud de vectores)
    import numpy as np
    
    st_norms = [np.linalg.norm(emb) for emb in df_sentence["embedding"].head(10)]
    gemini_norms = [np.linalg.norm(emb) for emb in df_gemini["embedding"].head(10)]
    
    logger.info(f"\n📊 Norma L2 promedio (primeros 10 chunks):")
    logger.info(f"   - Sentence Transformers: {np.mean(st_norms):.4f}")
    logger.info(f"   - Gemini: {np.mean(gemini_norms):.4f}")
    
    # Comparación de tamaño en disco
    st_file = DATA_DIR / "embeddings_sentence_transformers.parquet"
    gemini_file = DATA_DIR / "embeddings_gemini.parquet"
    
    df_sentence.to_parquet(st_file, index=False)
    df_gemini.to_parquet(gemini_file, index=False)
    
    st_size_mb = st_file.stat().st_size / (1024 * 1024)
    gemini_size_mb = gemini_file.stat().st_size / (1024 * 1024)
    
    logger.info(f"\n💾 Tamaño en disco:")
    logger.info(f"   - Sentence Transformers: {st_size_mb:.2f} MB")
    logger.info(f"   - Gemini: {gemini_size_mb:.2f} MB")
    logger.info(f"   - Diferencia: {gemini_size_mb - st_size_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="Comparar embeddings de diferentes providers")
    parser.add_argument("--gemini-key", help="API key de Gemini (o usa GEMINI_API_KEY en .env)")
    parser.add_argument("--sample-size", type=int, help="Número de chunks a procesar (usa todos si no se especifica)")
    
    args = parser.parse_args()
    
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Iniciando comparación de embeddings")
    
    # Cargar chunks
    try:
        df_chunks = load_chunks_from_disk()
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        logger.error("💡 Ejecuta primero: python src/main.py")
        return
    
    # Tomar muestra si se especifica
    if args.sample_size:
        df_chunks = df_chunks.head(args.sample_size)
        logger.info(f"📊 Usando muestra de {args.sample_size} chunks")
    
    # API key de Gemini
    gemini_key = args.gemini_key or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("❌ Falta API key de Gemini")
        logger.error("💡 Usa --gemini-key TU_KEY o configura GEMINI_API_KEY en .env")
        return
    
    # Generar con Sentence Transformers
    df_st, stats_st, time_st = generate_embeddings_with_provider(
        df_chunks.copy(),
        "sentence-transformers",
        logger=logger
    )
    
    if df_st is None:
        return
    
    # Generar con Gemini
    df_gemini, stats_gemini, time_gemini = generate_embeddings_with_provider(
        df_chunks.copy(),
        "gemini",
        api_key=gemini_key,
        logger=logger
    )
    
    if df_gemini is None:
        return
    
    # Comparar resultados
    logger.info(f"\n{'='*80}")
    logger.info("⚡ COMPARACIÓN DE RENDIMIENTO")
    logger.info(f"{'='*80}")
    logger.info(f"\n⏱️  Tiempo de ejecución:")
    logger.info(f"   - Sentence Transformers: {time_st:.2f} s")
    logger.info(f"   - Gemini: {time_gemini:.2f} s")
    logger.info(f"   - Diferencia: {abs(time_gemini - time_st):.2f} s")
    
    if time_st < time_gemini:
        logger.info(f"   ⚡ Sentence Transformers es {time_gemini/time_st:.1f}x más rápido (local)")
    else:
        logger.info(f"   ⚡ Gemini es {time_st/time_gemini:.1f}x más rápido")
    
    # Comparar calidad
    compare_embeddings_quality(df_st, df_gemini, logger)
    
    # Recomendación
    logger.info(f"\n{'='*80}")
    logger.info("💡 RECOMENDACIÓN")
    logger.info(f"{'='*80}")
    logger.info("\n📊 Sentence Transformers (384 dims):")
    logger.info("   ✅ Rápido (local, sin latencia de red)")
    logger.info("   ✅ Gratuito (sin límites de API)")
    logger.info("   ✅ Menor tamaño en disco")
    logger.info("   ⚠️  Menor dimensionalidad (menos expresivo)")
    
    logger.info("\n🌟 Gemini (768 dims):")
    logger.info("   ✅ Mayor dimensionalidad (más expresivo)")
    logger.info("   ✅ Mejor para español (entrenado multilingüe)")
    logger.info("   ✅ Más preciso en retrieval (según benchmarks)")
    logger.info("   ⚠️  Requiere API key y conexión a internet")
    logger.info("   ⚠️  Límites de cuota gratuita")
    logger.info("   ⚠️  Mayor tamaño en disco")
    
    logger.info("\n🎯 Para este proyecto (Bancolombia):")
    logger.info("   - Desarrollo/Testing: Sentence Transformers")
    logger.info("   - Producción: Gemini (mejor calidad para español)")
    
    logger.info("\n✅ Comparación completada")
    logger.info(f"\n📁 Archivos generados:")
    logger.info(f"   - {DATA_DIR}/embeddings_sentence_transformers.parquet")
    logger.info(f"   - {DATA_DIR}/embeddings_gemini.parquet")


if __name__ == "__main__":
    main()
# Script de comparación de embeddings
