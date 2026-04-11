#!/usr/bin/env python3
"""
Script de prueba para validar el servidor MCP de Bancolombia.

Ejecuta llamadas de prueba a cada tool y resource para verificar que funcionen correctamente.
"""

import subprocess
import json
import sys
import time
from pathlib import Path

def test_mcp_server():
    """Prueba el servidor MCP con requests de ejemplo."""
    
    print("🧪 TESTING SERVIDOR MCP - BANCOLOMBIA\n")
    print("=" * 60)
    
    # Iniciar servidor MCP
    print("📡 Iniciando servidor MCP...")
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    # Esperar a que inicie
    time.sleep(2)
    
    tests = []
    
    # Test 1: search_knowledge_base
    print("\n\n📋 TEST 1: search_knowledge_base")
    print("-" * 60)
    test1 = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_knowledge_base",
            "arguments": {
                "query": "¿Qué es el consumidor financiero?",
                "n_results": 3
            }
        }
    }
    tests.append(("search_knowledge_base", test1))
    
    # Test 2: get_article_by_url
    print("\n\n📋 TEST 2: get_article_by_url")
    print("-" * 60)
    test2 = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_article_by_url",
            "arguments": {
                "url": "https://www.bancolombia.com/personas/creditos"
            }
        }
    }
    tests.append(("get_article_by_url", test2))
    
    # Test 3: list_categories
    print("\n\n📋 TEST 3: list_categories")
    print("-" * 60)
    test3 = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_categories",
            "arguments": {}
        }
    }
    tests.append(("list_categories", test3))
    
    # Ejecutar tests
    results = []
    for test_name, request in tests:
        try:
            # Enviar request
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json.encode())
            process.stdin.flush()
            
            # Leer respuesta
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode())
                
                print(f"✅ {test_name}: OK")
                if "result" in response:
                    result = response["result"]
                    if test_name == "search_knowledge_base":
                        print(f"   → {result.get('total_results', 0)} resultados encontrados")
                        if result.get('documents'):
                            print(f"   → Score top-1: {result['documents'][0].get('similarity_score', 0)}")
                    elif test_name == "get_article_by_url":
                        print(f"   → {result.get('total_chunks', 0)} chunks recuperados")
                    elif test_name == "list_categories":
                        print(f"   → {result.get('total_categories', 0)} categorías disponibles")
                    
                    results.append((test_name, True, None))
                elif "error" in response:
                    print(f"❌ {test_name}: Error - {response['error']}")
                    results.append((test_name, False, response['error']))
            else:
                print(f"❌ {test_name}: Sin respuesta")
                results.append((test_name, False, "Sin respuesta"))
                
        except Exception as e:
            print(f"❌ {test_name}: Exception - {str(e)}")
            results.append((test_name, False, str(e)))
    
    # Cleanup
    process.terminate()
    
    # Resumen
    print("\n\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else f"❌ FAIL: {error}"
        print(f"{test_name:30} {status}")
    
    print(f"\nResultado: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(test_mcp_server())

