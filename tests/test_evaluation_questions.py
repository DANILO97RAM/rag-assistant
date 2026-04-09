"""
Script de prueba para el dataset de evaluación.

Valida que las preguntas estén bien formadas y carga el JSON correctamente.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

QUESTIONS_FILE = Path(__file__).parent.parent / "data" / "evaluation_questions.json"


def load_questions():
    """Carga el dataset de preguntas de evaluación"""
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def validate_questions(data):
    """Valida la estructura del dataset"""
    errors = []
    
    # Validar metadata
    if "metadata" not in data:
        errors.append("Falta sección 'metadata'")
    
    if "questions" not in data:
        errors.append("Falta sección 'questions'")
        return errors
    
    questions = data["questions"]
    
    # Validar cada pregunta
    required_fields = ["id", "question", "topic", "expected_keywords", "difficulty"]
    
    for i, q in enumerate(questions, 1):
        missing = [field for field in required_fields if field not in q]
        if missing:
            errors.append(f"Pregunta {i}: Faltan campos {missing}")
        
        # Validar IDs únicos
        if q.get("id") != i:
            errors.append(f"Pregunta {i}: ID inconsistente ({q.get('id')})")
        
        # Validar dificultad
        if q.get("difficulty") not in ["easy", "medium", "hard"]:
            errors.append(f"Pregunta {i}: Dificultad inválida")
    
    # Validar que hay 20 preguntas
    if len(questions) != 20:
        errors.append(f"Se esperaban 20 preguntas, hay {len(questions)}")
    
    return errors


def show_summary(data):
    """Muestra resumen del dataset"""
    metadata = data.get("metadata", {})
    questions = data.get("questions", [])
    
    print("\n" + "="*80)
    print("📊 RESUMEN DEL DATASET DE EVALUACIÓN")
    print("="*80)
    print(f"\nTotal de preguntas: {len(questions)}")
    print(f"Versión: {metadata.get('version', 'N/A')}")
    print(f"Fecha: {metadata.get('created_date', 'N/A')}")
    
    # Contar por tópico
    topics = {}
    difficulties = {}
    
    for q in questions:
        topic = q.get("topic", "unknown")
        topics[topic] = topics.get(topic, 0) + 1
        
        diff = q.get("difficulty", "unknown")
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print("\n📂 Distribución por tópico:")
    for topic, count in sorted(topics.items(), key=lambda x: -x[1]):
        print(f"   - {topic}: {count}")
    
    print("\n📈 Distribución por dificultad:")
    for diff, count in sorted(difficulties.items(), key=lambda x: -x[1]):
        print(f"   - {diff}: {count}")
    
    print("\n📋 Primeras 5 preguntas:")
    for q in questions[:5]:
        print(f"\n   {q['id']}. {q['question']}")
        print(f"      Tópico: {q['topic']} | Dificultad: {q['difficulty']}")
    
    print("\n" + "="*80)


def main():
    print(f"🔍 Validando dataset de evaluación: {QUESTIONS_FILE}")
    
    if not QUESTIONS_FILE.exists():
        print(f"❌ Error: No se encontró {QUESTIONS_FILE}")
        return
    
    # Cargar
    try:
        data = load_questions()
        print("✅ JSON cargado correctamente")
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        return
    
    # Validar
    errors = validate_questions(data)
    
    if errors:
        print("\n❌ Se encontraron errores:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Dataset válido, sin errores")
    
    # Mostrar resumen
    show_summary(data)
    
    print("\n💡 Uso sugerido:")
    print("   1. Implementar sistema RAG completo")
    print("   2. Ejecutar cada pregunta contra el sistema")
    print("   3. Comparar fuentes retornadas con 'expected_sources'")
    print("   4. Verificar que 'expected_keywords' aparezcan en chunks recuperados")
    print("   5. Calcular métricas: precisión, recall, MRR")


if __name__ == "__main__":
    main()
# Script de validación del dataset de evaluación
