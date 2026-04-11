#!/usr/bin/env python3
"""
Script de inicio rápido para servidores Bancolombia Knowledge Base.

Permite seleccionar entre:
1. Servidor MCP (stdio) - Para agentes conversacionales
2. API REST (HTTP) - Para Postman, curl, navegador
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("\n" + "=" * 60)
    print("🚀 BANCOLOMBIA KNOWLEDGE BASE - SERVIDOR")
    print("=" * 60)
    print("\nSelecciona el tipo de servidor:\n")
    print("  1. Servidor MCP (stdio)")
    print("     → Para agentes conversacionales (Claude, GPT, etc.)")
    print("     → Transporte: stdin/stdout")
    print("     → Protocolo: JSON-RPC 2.0")
    print()
    print("  2. API REST (HTTP)")
    print("     → Para Postman, Insomnia, curl")
    print("     → Puerto: 8000")
    print("     → Documentación: http://localhost:8000/docs")
    print()
    print("  3. Ambos (en terminales separadas)")
    print()
    
    choice = input("Opción [1-3]: ").strip()
    
    project_root = Path(__file__).parent
    mcp_dir = project_root / "mcp"
    
    if choice == "1":
        print("\n🚀 Iniciando Servidor MCP...")
        print("Presiona Ctrl+C para detener.\n")
        subprocess.run(
            [sys.executable, "main.py"],
            cwd=mcp_dir
        )
    
    elif choice == "2":
        print("\n🚀 Iniciando API REST...")
        print("📖 Documentación: http://localhost:8000/docs")
        print("Presiona Ctrl+C para detener.\n")
        subprocess.run(
            [sys.executable, "api_server.py"],
            cwd=mcp_dir
        )
    
    elif choice == "3":
        print("\n⚠️  Necesitas ejecutar en terminales separadas:")
        print("\n  Terminal 1:")
        print("    cd mcp && python main.py")
        print("\n  Terminal 2:")
        print("    cd mcp && python api_server.py")
        print()
    
    else:
        print("\n❌ Opción inválida")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido")
        sys.exit(0)
# Commented by GitHub Copilot
