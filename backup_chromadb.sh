#!/bin/bash
# Backup de ChromaDB data

BACKUP_DIR="backups/chromadb_$(date +%Y%m%d_%H%M%S)"

echo "📦 Creando backup de ChromaDB..."

# Crear directorio de backup
mkdir -p "$BACKUP_DIR"

# Copiar datos de ChromaDB
if [ -d "chroma_data" ]; then
    cp -r chroma_data "$BACKUP_DIR/"
    echo "✅ Backup creado en: $BACKUP_DIR"
    
    # Comprimir
    tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
    rm -rf "$BACKUP_DIR"
    
    echo "📦 Backup comprimido: $BACKUP_DIR.tar.gz"
    echo "📊 Tamaño: $(du -h "$BACKUP_DIR.tar.gz" | cut -f1)"
else
    echo "❌ No se encontró directorio chroma_data"
    exit 1
fi

# Mantener solo últimos 5 backups
cd backups
ls -t chromadb_*.tar.gz | tail -n +6 | xargs -r rm
echo "🗑️  Backups antiguos eliminados (manteniendo últimos 5)"

