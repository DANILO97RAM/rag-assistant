"""
Script interactivo para validar búsquedas en ChromaDB.

Prueba queries reales y muestra resultados con scores y metadatos.
Útil para validar la calidad del retrieval semántico.
"""

import sys
from pathlib import Path

# Agregar src al path (funciona tanto desde tests/ como tests/db/)
current_file = Path(__file__).resolve()
project_root = current_file.parent
while project_root.name in ["tests", "db"] and project_root.parent != project_root:
    project_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))

from services.database import ChromaDBService


def test_queries():
    """Ejecuta queries de prueba y muestra resultados"""
    
    print("🔍 Validación de Búsquedas en ChromaDB")
    print("=" * 60)
    
    # Inicializar servicio
    db = ChromaDBService()
    db.create_collection()
    
    # Verificar que haya datos
    stats = db.get_stats()
    print(f"\n📊 Estadísticas:")
    print(f"   Total documentos: {stats['total_documents']}")
    print(f"   Categorías: {stats['categories']}")
    print(f"   Última actualización: {stats['fecha_ultima_actualizacion']}")
    
    if stats['total_documents'] == 0:
        print("\n⚠️ No hay documentos indexados.")
        print("   Ejecuta: python src/main.py --index-chromadb")
        return
    
    # Queries de prueba
    queries = [
        "¿Cómo solicitar una tarjeta de crédito?",
        "Requisitos para crédito hipotecario",
        "Tasas de interés de cuentas de ahorro",
        "¿Qué seguros ofrece Bancolombia?",
        "Cómo hacer transferencias internacionales",
        "Beneficios de la cuenta de ahorros",
        "¿Qué necesito para un crédito de libre inversión?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'─' * 60}")
        print(f"🔍 Query {i}: {query}")
        print(f"{'─' * 60}")
        
        try:
            results = db.search(query, n_results=3)
            
            if not results:
                print("   ⚠️ Sin resultados")
                continue
            
            for j, result in enumerate(results, 1):
                score = result.get('distance', 0)
                # Convertir distancia a similitud (1 - distancia)
                similarity = 1 - score if score else 0
                
                print(f"\n   [{j}] Score: {similarity:.3f} | Distancia: {score:.3f}")
                print(f"       URL: {result['metadata']['url']}")
                print(f"       Título: {result['metadata']['title']}")
                print(f"       Categoría: {result['metadata']['category']}")
                print(f"       Palabras: {result['metadata']['word_count']}")
                
                # Mostrar snippet del texto
                texto = result['document']
                snippet = texto[:200] + "..." if len(texto) > 200 else texto
                print(f"       Texto: {snippet}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'=' * 60}")
    print("✅ Validación completada")


def test_url_filtering():
    """Prueba filtrado por URL"""
    print("\n\n🔗 Prueba de Filtrado por URL")
    print("=" * 60)
    
    db = ChromaDBService()
    db.create_collection()
    
    # Obtener una URL de ejemplo
    results = db.search("tarjeta", n_results=1)
    if not results:
        print("⚠️ No hay datos para probar")
        return
    
    url = results[0]['metadata']['url']
    print(f"\n📎 Buscando chunks de: {url}")
    
    chunks = db.get_by_url(url)
    print(f"\n✅ Encontrados {len(chunks)} chunks para esta URL:")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n   [{i}] Chunk {chunk['metadata']['chunk_index']}")
        print(f"       Palabras: {chunk['metadata']['word_count']}")
        texto_preview = chunk['document'][:150] + "..."
        print(f"       Texto: {texto_preview}")


def test_categories():
    """Prueba listado de categorías"""
    print("\n\n📁 Categorías Disponibles")
    print("=" * 60)
    
    db = ChromaDBService()
    db.create_collection()
    
    categories = db.get_categories()
    
    print(f"\n✅ Total categorías: {len(categories)}")
    for cat in categories:
        print(f"   • {cat}")


if __name__ == "__main__":
    test_queries()
    test_url_filtering()
    test_categories()
