"""
Validación de ChromaDB con queries REALISTAS basadas en contenido disponible.

Basado en análisis de contenido:
- Seguros: 1465 palabras ✅
- Consumidor financiero: 2473 palabras ✅
- Preferencial: 1865 palabras ✅
- A la mano: 1544 palabras ✅
- Créditos: 798 palabras ✅
- Inversiones: 842 palabras ✅
"""

import sys
from pathlib import Path

# Agregar src al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from services.database import ChromaDBService


def print_results(query: str, results: list, query_num: int):
    """Imprime resultados formateados."""
    print(f"\n{'─' * 60}")
    print(f"🔍 Query {query_num}: {query}")
    print('─' * 60)
    
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        distance = result.get('distance', 0.0)
        similarity = 1 - distance  # Convertir distancia a similaridad
        
        print(f"\n   [{i}] Score: {similarity:.3f} | Distancia: {distance:.3f}")
        print(f"       URL: {metadata.get('url', 'N/A')}")
        print(f"       Título: {metadata.get('title', 'N/A')}")
        print(f"       Categoría: {metadata.get('category', 'N/A')}")
        print(f"       Palabras: {metadata.get('word_count', 'N/A')}")
        
        # Mostrar preview del texto
        text = result['document'][:150] + '...'
        print(f"       Texto: {text}")


def main():
    print('🔍 VALIDACIÓN CON QUERIES REALISTAS')
    print('=' * 60)
    
    # Conectar a ChromaDB
    db = ChromaDBService()
    db.create_collection()
    
    # Estadísticas
    stats = db.get_stats()
    print(f"\n📊 Estadísticas:")
    print(f"   Total documentos: {stats['total_documents']}")
    print(f"   Categorías: {stats['num_categories']}")
    print(f"   Última actualización: {stats['fecha_ultima_actualizacion']}\n")
    
    # Queries basadas en contenido real disponible
    queries = [
        "¿Qué seguros ofrece Bancolombia?",                    # Seguros: 1465 palabras ✅
        "¿Qué es el consumidor financiero?",                   # Cons. Financiero: 2473 palabras ✅
        "¿Qué beneficios tiene la banca preferencial?",        # Preferencial: 1865 palabras ✅
        "¿Qué es A la mano de Bancolombia?",                   # A la mano: 1544 palabras ✅
        "¿Qué tipos de créditos hay disponibles?",             # Créditos: 798 palabras ✅
        "¿Cómo puedo invertir mi dinero?",                     # Inversiones: 842 palabras ✅
        "¿Quién es el defensor del consumidor financiero?",    # Defensor: 2372 palabras ✅
    ]
    
    # Ejecutar queries
    for i, query in enumerate(queries, 1):
        results = db.search(query, n_results=3)
        print_results(query, results, i)
    
    print(f"\n{'=' * 60}")
    print('✅ Validación completada')
    print()
    
    # Prueba de filtrado por categoría
    print(f"\n🔍 Prueba de Filtrado por Categoría: 'seguros'")
    print('=' * 60)
    
    seguros_query = "información sobre seguros"
    seguros_results = db.search(seguros_query, n_results=3, where={"category": "seguros"})
    
    print(f"\n✅ Encontrados {len(seguros_results)} resultados para categoría 'seguros':\n")
    
    for i, result in enumerate(seguros_results, 1):
        metadata = result['metadata']
        distance = result.get('distance', 0.0)
        similarity = 1 - distance
        
        print(f"   [{i}] Chunk {metadata.get('chunk_index', 'N/A')}")
        print(f"       Score: {similarity:.3f}")
        print(f"       Palabras: {metadata.get('word_count', 'N/A')}")
        print(f"       Texto: {result['document'][:120]}...\n")
    
    # Listado de categorías
    print(f"\n📁 Categorías Disponibles (Top 15)")
    print('=' * 60)
    
    categories = db.get_categories()
    print(f"\n✅ Total categorías: {len(categories)}\n")
    
    # Mostrar top 15
    for i, cat in enumerate(categories[:15], 1):
        print(f"   {i:2}. {cat}")
    
    if len(categories) > 15:
        print(f"\n   ... y {len(categories) - 15} más")
    
    print()


if __name__ == "__main__":
    main()
