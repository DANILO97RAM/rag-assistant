"""
Script para evaluar diferentes estrategias de chunking.

Prueba múltiples combinaciones de chunk_size y chunk_overlap
para determinar la configuración óptima.

Uso:
    python tests/evaluate_chunking_strategies.py
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.logger import setup_logging
from main import load_chunks_from_disk, SCRAPED_PAGES_FILE, DATA_DIR
from core.chunker import Chunker
from core.cleaner import TextCleaner

# Configuraciones a evaluar
CHUNKING_STRATEGIES = [
    {"chunk_size": 512, "chunk_overlap": 64, "name": "512/64 (pequeño)"},
    {"chunk_size": 512, "chunk_overlap": 128, "name": "512/128 (pequeño, overlap alto)"},
    {"chunk_size": 1024, "chunk_overlap": 128, "name": "1024/128 (actual)"},
    {"chunk_size": 1024, "chunk_overlap": 256, "name": "1024/256 (overlap alto)"},
    {"chunk_size": 2048, "chunk_overlap": 256, "name": "2048/256 (grande)"},
]


def analyze_chunks(df: pd.DataFrame, strategy_name: str) -> dict:
    """Analiza estadísticas de un DataFrame de chunks"""
    df_temp = df.copy()
    df_temp['word_count'] = df_temp['texto'].apply(lambda x: len(str(x).split()))
    df_temp['char_count'] = df_temp['texto'].apply(lambda x: len(str(x)))
    
    stats = df_temp['word_count'].describe()
    
    return {
        "strategy": strategy_name,
        "total_chunks": len(df),
        "mean_words": round(stats['mean'], 1),
        "median_words": round(stats['50%'], 1),
        "p75_words": round(stats['75%'], 1),
        "max_words": round(stats['max'], 1),
        "mean_chars": round(df_temp['char_count'].mean(), 1),
    }


def main():
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🔬 Evaluando diferentes estrategias de chunking")
    
    # Cargar páginas scrapeadas
    if not SCRAPED_PAGES_FILE.exists():
        logger.error(f"❌ No se encontró {SCRAPED_PAGES_FILE}")
        logger.error("💡 Ejecuta primero: python src/main.py")
        return
    
    logger.info(f"📂 Cargando páginas desde {SCRAPED_PAGES_FILE}")
    df_pages = pd.read_parquet(SCRAPED_PAGES_FILE)
    logger.info(f"✅ {len(df_pages)} páginas cargadas")
    
    # Limpiar datos (solo una vez)
    logger.info("🧹 Limpiando texto...")
    cleaner = TextCleaner(df_pages, logger=logger)
    df_clean = cleaner.transform()
    
    # Evaluar cada estrategia
    results = []
    
    for strategy in CHUNKING_STRATEGIES:
        logger.info(f"\n📊 Evaluando: {strategy['name']}")
        logger.info(f"   chunk_size={strategy['chunk_size']}, overlap={strategy['chunk_overlap']}")
        
        # Crear chunker con esta configuración
        chunker = Chunker(
            chunk_size=strategy['chunk_size'],
            chunk_overlap=strategy['chunk_overlap'],
            logger=logger
        )
        
        # Generar chunks
        df_chunks = chunker.get_chunks(df_clean)
        
        # Analizar
        stats = analyze_chunks(df_chunks, strategy['name'])
        results.append(stats)
        
        logger.info(f"   ✅ Chunks generados: {stats['total_chunks']}")
        logger.info(f"   📈 Promedio palabras: {stats['mean_words']}")
        logger.info(f"   📊 P75 palabras: {stats['p75_words']}")
    
    # Mostrar tabla comparativa
    logger.info("\n" + "="*80)
    logger.info("📊 TABLA COMPARATIVA DE ESTRATEGIAS")
    logger.info("="*80)
    
    df_results = pd.DataFrame(results)
    
    # Formatear tabla
    print("\n")
    print(df_results.to_string(index=False))
    print("\n")
    
    # Guardar resultados
    output_file = DATA_DIR / "chunking_evaluation.csv"
    df_results.to_csv(output_file, index=False)
    logger.info(f"💾 Resultados guardados en {output_file}")
    
    # Recomendación
    logger.info("\n" + "="*80)
    logger.info("💡 RECOMENDACIONES")
    logger.info("="*80)
    
    # Encontrar balance óptimo
    # Criterios: chunks no muy pequeños (>400 palabras promedio), no demasiados chunks
    df_results['score'] = (
        (df_results['mean_words'] / df_results['mean_words'].max()) * 0.4 +  # 40% peso a tamaño promedio
        (1 - df_results['total_chunks'] / df_results['total_chunks'].max()) * 0.3 +  # 30% peso a menos chunks
        (df_results['p75_words'] / df_results['p75_words'].max()) * 0.3  # 30% peso a P75
    )
    
    best_idx = df_results['score'].idxmax()
    best_strategy = df_results.loc[best_idx]
    
    logger.info(f"\n🏆 Mejor estrategia según análisis: {best_strategy['strategy']}")
    logger.info(f"   - Total chunks: {best_strategy['total_chunks']}")
    logger.info(f"   - Promedio palabras: {best_strategy['mean_words']}")
    logger.info(f"   - P75: {best_strategy['p75_words']}")
    
    logger.info("\n📝 Interpretación:")
    logger.info("   - Menos chunks = mejor para rendimiento y costos de embedding")
    logger.info("   - Promedio ~400-700 palabras = buen balance para RAG")
    logger.info("   - P75 cercano al chunk_size = buen aprovechamiento")
    logger.info("   - Overlap 128-256 tokens = mantiene contexto entre chunks")
    
    logger.info("\n✅ Evaluación completada")


if __name__ == "__main__":
    main()