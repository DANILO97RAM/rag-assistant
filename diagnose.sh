#!/bin/bash
# Script de diagnóstico para ChromaDB

set -e

echo "================================================"
echo "   ChromaDB Diagnostic Report"
echo "================================================"
echo ""

# 1. Docker Status
echo "1. 🐳 Docker Containers Status"
echo "--------------------------------"
if docker ps | grep -q chromadb; then
    echo "✅ ChromaDB container running"
    docker ps | grep chromadb | awk '{print "   Container ID:", $1, "| Status:", $7}'
else
    echo "❌ ChromaDB container NOT running"
    echo "   Execute: docker-compose up -d"
fi

if docker ps | grep -q n8n; then
    echo "✅ n8n container running"
else
    echo "⚠️  n8n container NOT running"
fi
echo ""

# 2. ChromaDB API Health
echo "2. 💓 ChromaDB API Health"
echo "--------------------------------"
if curl -s http://localhost:8000/api/v2/heartbeat > /dev/null 2>&1; then
    echo "✅ ChromaDB API responding (port 8000)"
    HEARTBEAT=$(curl -s http://localhost:8000/api/v2/heartbeat)
    echo "   Heartbeat: $HEARTBEAT"
else
    echo "❌ ChromaDB API not responding"
    echo "   Check: docker logs chromadb"
fi
echo ""

# 3. REST API Status
echo "3. 🌐 REST API Status (port 9000)"
echo "--------------------------------"
if curl -s http://localhost:9000/ > /dev/null 2>&1; then
    echo "✅ REST API responding"
    STATS=$(curl -s http://localhost:9000/stats)
    echo "   Stats: $STATS"
    
    # Extraer total_documents
    DOCS=$(echo $STATS | grep -oP '"total_documents":\s*\K\d+' || echo "0")
    if [ "$DOCS" -gt 0 ]; then
        echo "✅ ChromaDB has $DOCS documents indexed"
    else
        echo "⚠️  ChromaDB is EMPTY (0 documents)"
        echo "   Execute: make full-pipeline"
    fi
else
    echo "❌ REST API not responding"
    echo "   Start it: make api_server"
fi
echo ""

# 4. Data Directory
echo "4. 📂 Data Directory Status"
echo "--------------------------------"
if [ -d "chroma_data" ]; then
    echo "✅ chroma_data/ directory exists"
    DISK_USAGE=$(du -sh chroma_data/ 2>/dev/null | awk '{print $1}')
    FILE_COUNT=$(find chroma_data/ -type f 2>/dev/null | wc -l)
    echo "   Size: $DISK_USAGE"
    echo "   Files: $FILE_COUNT"
    
    if [ "$FILE_COUNT" -gt 0 ]; then
        echo "✅ Data files present"
    else
        echo "⚠️  Directory empty - needs indexing"
    fi
else
    echo "❌ chroma_data/ directory NOT found"
    echo "   Will be created on first indexing"
fi
echo ""

# 5. Parquet Files (chunks/embeddings)
echo "5. 📊 Source Data Files"
echo "--------------------------------"
if [ -f "data/chunks.parquet" ]; then
    CHUNK_SIZE=$(du -sh data/chunks.parquet | awk '{print $1}')
    echo "✅ chunks.parquet exists ($CHUNK_SIZE)"
else
    echo "❌ chunks.parquet NOT found"
    echo "   Execute: make main-force"
fi

if [ -f "data/embeddings_sentence-transformers.parquet" ]; then
    EMB_SIZE=$(du -sh data/embeddings_sentence-transformers.parquet | awk '{print $1}')
    echo "✅ embeddings.parquet exists ($EMB_SIZE)"
else
    echo "❌ embeddings.parquet NOT found"
    echo "   Execute: make generate-embeddings-sentence"
fi
echo ""

# 6. Environment Variables
echo "6. ⚙️  Environment Configuration"
echo "--------------------------------"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "   CHROMA_HOST: $(grep CHROMA_HOST .env | cut -d= -f2)"
    echo "   CHROMA_PORT: $(grep CHROMA_PORT .env | cut -d= -f2)"
    echo "   API_PORT: $(grep API_PORT .env | cut -d= -f2)"
else
    echo "⚠️  .env file NOT found"
    echo "   Copy from: .env.example"
fi
echo ""

# 7. Network Connectivity
echo "7. 🌐 Docker Network"
echo "--------------------------------"
if docker network inspect rag-assistant_rag-network > /dev/null 2>&1; then
    echo "✅ rag-network exists"
    CONTAINERS=$(docker network inspect rag-assistant_rag-network | grep -c '"Name": "chromadb"' || echo "0")
    echo "   Connected containers: $CONTAINERS"
else
    echo "⚠️  rag-network NOT found"
fi
echo ""

# 8. Backups
echo "8. 💾 Backups Available"
echo "--------------------------------"
if [ -d "backups" ]; then
    BACKUP_COUNT=$(ls -1 backups/chromadb_*.tar.gz 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        echo "✅ $BACKUP_COUNT backup(s) found"
        echo "   Latest:"
        ls -lht backups/chromadb_*.tar.gz 2>/dev/null | head -1 | awk '{print "   ", $9, "("$5")"}'
    else
        echo "⚠️  No backups found"
        echo "   Create one: make backup"
    fi
else
    echo "⚠️  backups/ directory not found"
fi
echo ""

# Summary
echo "================================================"
echo "   Summary & Recommendations"
echo "================================================"
echo ""

# Check overall health
if docker ps | grep -q chromadb && curl -s http://localhost:8000/api/v2/heartbeat > /dev/null 2>&1; then
    DOCS=$(curl -s http://localhost:9000/stats 2>/dev/null | grep -oP '"total_documents":\s*\K\d+' || echo "0")
    
    if [ "$DOCS" -gt 0 ]; then
        echo "✅ SYSTEM HEALTHY"
        echo "   ChromaDB is running with $DOCS documents indexed"
        echo ""
        echo "Next steps:"
        echo "   - Start API: make api_server"
        echo "   - Access n8n: http://localhost:5678"
        echo "   - Test search: curl -X POST http://localhost:9000/search -H 'Content-Type: application/json' -d '{\"query\":\"seguros\"}'"
    else
        echo "⚠️  SYSTEM RUNNING BUT EMPTY"
        echo "   ChromaDB is running but has NO documents"
        echo ""
        echo "To fix:"
        echo "   1. make full-pipeline"
        echo "   2. Wait 2-3 minutes"
        echo "   3. Verify: curl http://localhost:9000/stats"
    fi
else
    echo "❌ SYSTEM NOT READY"
    echo ""
    echo "To fix:"
    echo "   1. docker-compose up -d"
    echo "   2. make full-pipeline"
    echo "   3. make api_server"
fi

echo ""
echo "================================================"
echo "For more help, see: TROUBLESHOOTING_CHROMADB.md"
echo "================================================"

