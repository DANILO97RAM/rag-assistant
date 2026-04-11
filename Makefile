PYTHON_BIN=python3.12

activate-venv:
	source venv/bin/activate
	
setup:
	$(PYTHON_BIN) -m venv venv
	./venv/bin/pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
	sudo ./venv/bin/playwright install-deps chromium

main:
	./venv/bin/python src/main.py --depth 2 --max-pages 50 --concurrency 10

main-force:
	./venv/bin/python src/main.py --depth 2 --max-pages 50 --concurrency 10 --force-scrape

# Comando completo: scraping + embeddings + ChromaDB indexación
full-pipeline:

# Reiniciar servicios Docker (útil después de cambios en docker-compose.yaml)
docker-restart:
	docker compose down
	docker compose up -d

# Ver logs de servicios Docker
docker-logs:
	docker compose logs -f

# Ver estado de servicios Docker
docker-status:
	docker ps --filter "name=chromadb" --filter "name=n8n"

# Detener y limpiar TODO (incluyendo volúmenes)
docker-clean:
	docker compose down -v
	rm -rf n8n_data/ || true

# ============================================================================
# n8n + MCP Setup
# ============================================================================

# Instalar dependencias Python en contenedor n8n
n8n-setup:
	@echo "🔧 Instalando dependencias Python en n8n..."
	@docker exec n8n apk add --no-cache python3 py3-pip || true
	@docker exec n8n pip3 install --break-system-packages chromadb==0.5.7 sentence-transformers==3.0.0 fastmcp==0.2.1 python-dotenv==1.0.0 pandas numpy
	@echo "✅ Dependencias instaladas en n8n"
	@echo "📝 Configura MCP Client en n8n:"
	@echo "   Transport: Standard I/O"
	@echo "   Command: python3"
	@echo "   Args: /workspace/mcp/main.py"

# Test rápido del MCP desde n8n
n8n-test-mcp:
	@echo "🧪 Probando MCP server desde n8n..."
	@docker exec n8n python3 /workspace/mcp/main.py --help || echo "MCP ejecutable en n8n"

# Ver logs de n8n
n8n-logs:
	docker logs n8n -f --tail 100

# ============================================================================
# ChromaDB Backup & Restore
# ============================================================================

# Crear backup de ChromaDB
backup:
	@echo "📦 Creando backup de ChromaDB..."
	@mkdir -p backups
	@tar -czf backups/chromadb_$$(date +%Y%m%d_%H%M%S).tar.gz chroma_data/
	@echo "✅ Backup creado en backups/"
	@ls -lh backups/ | tail -1

# Restaurar último backup
restore:
	@echo "📂 Restaurando último backup..."
	@LATEST=$$(ls -t backups/chromadb_*.tar.gz 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "❌ No se encontraron backups"; \
		exit 1; \
	fi; \
	echo "Restaurando: $$LATEST"; \
	rm -rf chroma_data/; \
	tar -xzf $$LATEST; \
	echo "✅ Backup restaurado"

# Verificar estado de ChromaDB
chroma-check:
	@echo "🔍 Verificando ChromaDB..."
	@docker ps | grep chromadb || echo "❌ ChromaDB no está corriendo"
	@curl -s http://localhost:9000/stats | python3 -m json.tool || echo "❌ Error conectando a API"
	@ls -lh chroma_data/ 2>/dev/null || echo "⚠️  No existe directorio chroma_data/"

# Diagnóstico completo del sistema
diagnose:
	@chmod +x diagnose.sh
	@./diagnose.sh
	@echo "🚀 Ejecutando pipeline completo..."
	./venv/bin/python src/main.py --depth 2 --max-pages 50 --concurrency 10 --force-scrape
	@echo "🔢 Generando embeddings..."
	./venv/bin/python tests/generate_embeddings.py --provider sentence-transformers
	@echo "📊 Indexando en ChromaDB..."
	./venv/bin/python src/main.py --index-chromadb --reset-chromadb
	@echo "✅ Pipeline completo finalizado"
	
docker-up:
	docker compose up -d

clean:
	rm -rf venv venv
	find . -type d -name "__pycache__" -exec rm -rf {} +

test-embeddings:
	./venv/bin/pip install pytest --quiet || true
	./venv/bin/pytest tests/test_embedder.py -v

generate-embeddings-sentence:
	./venv/bin/python tests/generate_embeddings.py --provider sentence-transformers

generate-embeddings-gemini:
	./venv/bin/python tests/generate_embeddings.py --provider gemini --api-key $GEMINI_API_KEY

test-evaluate-chunk-strategy:
	./venv/bin/python tests/evaluate_chunking_strategies.py

test-compare-embeddings-20-samples:
	./venv/bin/python  tests/compare_embeddings.py --gemini-key $GEMINI_API_KEY --sample-size 20

update-requirements:
	./venv/bin/pip install --upgrade -r requirements.txt

db_unit-test:
	cd tests 
	./venv/bin/pytest tests/test_chromadb.py -v -s

db_queries_test:
	./venv/bin/python tests/test_chromadb_queries.py -v -s

inspect_scrapping:
	./venv/bin/python scripts/inspect_scrapping.py 

test_queries_from_scrapping:
	./venv/bin/python tests/test_chromadb_realistic_queries.py

# ============================================================================
# SERVIDOR MCP
# ============================================================================

mcp_server:
	cd mcp && ../venv/bin/python main.py

mcp_test:
	cd mcp && ../venv/bin/python test_server.py

mcp_install:
	./venv/bin/pip install fastmcp --quiet

# ============================================================================
# API REST (para Postman/HTTP)
# ============================================================================

api_server:
	cd mcp && ../venv/bin/python api_server.py

api_install:
	./venv/bin/pip install fastapi uvicorn --quiet

api_test:
	curl http://localhost:8000/ && echo "" && curl http://localhost:8000/stats

# ============================================================================
# Indexación ChromaDB
# ============================================================================

db_index:
	./venv/bin/python src/main.py --index-chromadb

db_reset:
	./venv/bin/python src/main.py --index-chromadb --reset-chromadb

# ============================================================================
# Análisis de contenido
# ============================================================================

analyze_content:
	./venv/bin/python scripts/analyze_content.py
	./venv/bin/python tests/test_realistic_queries.py -v -s

# scrapper:
# 	./venv/bin/python src/core/scrapper.py --depth 2 --max-pages 50 --concurrency 10

# clean_json_crawled:
# 	find . -type f -name "crawled_*.json" -delete