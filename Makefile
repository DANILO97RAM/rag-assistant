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