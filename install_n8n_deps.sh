#!/bin/bash
# Script para instalar dependencias Python en el contenedor n8n

set -e

echo "🔧 Instalando dependencias Python en n8n..."

# Verificar que n8n está corriendo
if ! docker ps | grep -q n8n; then
    echo "❌ Error: Contenedor n8n no está corriendo"
    echo "Ejecuta primero: docker-compose up -d"
    exit 1
fi

# Instalar Python y pip en n8n
echo "📦 Instalando Python 3..."
docker exec n8n apk add --no-cache python3 py3-pip || {
    echo "⚠️  Python ya está instalado o error al instalarlo"
}

# Instalar dependencias del proyecto
echo "📚 Instalando dependencias del proyecto..."
docker exec n8n pip3 install --break-system-packages \
    chromadb==0.5.7 \
    sentence-transformers==3.0.0 \
    fastmcp==0.2.1 \
    python-dotenv==1.0.0 \
    pandas \
    numpy

# Verificar instalación
echo "✅ Verificando instalación..."
docker exec n8n python3 -c "
import chromadb
import fastmcp
from sentence_transformers import SentenceTransformer
print('✅ Todas las dependencias instaladas correctamente')
"

echo ""
echo "🎉 Instalación completada"
echo ""
echo "📋 Próximos pasos:"
echo "1. Abre n8n: http://localhost:5678"
echo "2. Crea un nodo MCP Client"
echo "3. Configura:"
echo "   - Server Transport: Standard I/O"
echo "   - Command: python3"
echo "   - Arguments: /workspace/mcp/main.py"
echo "   - Environment: CHROMA_HOST=chromadb, CHROMA_PORT=8000"
echo ""

