.DEFAULT_GOAL := help
PYTHON_BIN=python3.12

activate-venv:
	source venv/bin/activate
	
setup: ## Configura el entorno virtual e instala dependencias
	$(PYTHON_BIN) -m venv venv
	./venv/bin/pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
	sudo ./venv/bin/playwright install-deps chromium

main: ## Ejecuta el pipeline completo (scraping + limpieza + chunking)
	./venv/bin/$(PYTHON_BIN) src/main.py --depth 2 --max-pages 60 --concurrency 10

main-force: ## Ejecuta el pipeline completo (scraping + limpieza + chunking) forzando el scraping nuevamente
	./venv/bin/$(PYTHON_BIN) src/main.py --depth 2 --max-pages 60 --concurrency 10 --force-scrape

docker-restart: ## Reinicia los servicios Docker (ChromaDB y n8n)
	docker compose down
	docker compose up -d


docker-logs: ## Ver logs de servicios Docker
	docker compose logs -f
	docker compose logs -f

docker-status: ## Muestra el estado de los contenedores Docker relacionados (ChromaDB y n8n)
	docker ps --filter "name=chromadb" --filter "name=n8n"

docker-clean: ## Detiene y elimina contenedores, redes, volúmenes y datos asociados a n8n
	docker compose down -v
	rm -rf n8n_data/ || true

# Test rápido del MCP desde n8n
n8n-test-mcp:
	@echo "🧪 Probando MCP server desde n8n..."
	@docker exec n8n python3 /workspace/mcp/main.py --help || echo "⚠️  MCP requiere instalación (ejecuta: make n8n-setup)"

n8n-logs: ## Muestra los logs del contenedor n8n en tiempo real
	docker logs n8n -f --tail 100

diagnose: ## Ejecuta un diagnóstico completo del sistema, incluyendo pruebas de MCP, generación de embeddings y indexación en ChromaDB
	@chmod +x diagnose.sh
	@./diagnose.sh
	@echo "🚀 Ejecutando pipeline completo..."
	./venv/bin/$(PYTHON_BIN) src/main.py --depth 2 --max-pages 50 --concurrency 10 --force-scrape
	@echo "🔢 Generando embeddings..."
	./venv/bin/$(PYTHON_BIN) tests/generate_embeddings.py --provider sentence-transformers
	@echo "📊 Indexando en ChromaDB..."
	./venv/bin/$(PYTHON_BIN) src/main.py --index-chromadb --reset-chromadb
	@echo "✅ Pipeline completo finalizado"
	
docker-up:
	docker compose up -d

clean: ## Limpia el entorno de desarrollo (venv, __pycache__)

	rm -rf venv venv
	find . -type d -name "__pycache__" -exec rm -rf {} +

test-embeddings: ## Ejecuta los tests de embeddings
	./venv/bin/$(PYTHON_BIN) -m pip install pytest --quiet || true
	./venv/bin/$(PYTHON_BIN) -m pytest tests/test_embedder.py -v

generate-embeddings-sentence: ## Genera embeddings usando Sentence Transformers
	./venv/bin/$(PYTHON_BIN) tests/generate_embeddings.py --provider sentence-transformers

generate-embeddings-gemini: ## Genera embeddings usando Gemini
	./venv/bin/$(PYTHON_BIN) tests/generate_embeddings.py --provider gemini --api-key $GEMINI_API_KEY

test-evaluate-chunk-strategy: ## Evalúa estrategias de chunking
	./venv/bin/$(PYTHON_BIN) tests/evaluate_chunking_strategies.py

test-compare-embeddings-20-samples: ## Compara embeddings usando 20 muestras
	./venv/bin/$(PYTHON_BIN)  tests/compare_embeddings.py --gemini-key $GEMINI_API_KEY --sample-size 20

update-requirements: ## Actualiza las dependencias del proyecto
	./venv/bin/$(PYTHON_BIN) -m pip install --upgrade -r requirements.txt

db_unit-test: ## Ejecuta los tests unitarios de ChromaDB
	cd tests 
	./venv/bin/$(PYTHON_BIN) -m pytest tests/test_chromadb.py -v -s

db_queries_test: ## Ejecuta los tests de consultas de ChromaDB
	./venv/bin/$(PYTHON_BIN) -m pytest tests/test_chromadb_queries.py -v -s

inspect_scrapping: ## Inspecciona el scrapping realizado: ver contendio del scrapping y genera preguntas de ejemplo para evaluar la calidad del scrapping
	./venv/bin/$(PYTHON_BIN) scripts/inspect_scrapping.py 

test_queries_from_scrapping: ## Ejecuta los tests de consultas realistas desde el scrapping (Este test se ejecutó)
	./venv/bin/$(PYTHON_BIN) tests/test_chromadb_realistic_queries.py

# SERVIDOR MCP

mcp_server: ## Ejecuta el servidor MCP (transporte stdio, se expone en n8n a través de Docker en el puerto 8000)
	cd mcp && ../venv/bin/$(PYTHON_BIN) main.py

mcp_test: ## Ejecuta los tests del servidor MCP	
	cd mcp && ../venv/bin/$(PYTHON_BIN) test_server.py

mcp_install: ## Instala las dependencias del servidor MCP
	./venv/bin/$(PYTHON_BIN) -m pip install fastmcp --quiet

# API REST (para Postman/HTTP)

api_server: ## Ejecuta el servidor API REST (se expone en n8n a través de Docker en el puerto 8001)
	cd mcp && ../venv/bin/$(PYTHON_BIN) api_server.py

api_install: ## Instala las dependencias del servidor API

	./venv/bin/$(PYTHON_BIN) -m pip install fastapi uvicorn --quiet

api_test: ## Ejecuta los tests del servidor API REST > Muestra estadisticas del servidor API REST (puerto 8001)
	curl http://localhost:8001/ && echo "" && curl http://localhost:8001/stats

# Indexación ChromaDB

db_index: ## Ejecuta la indexación en ChromaDB (usa los chunks generados para crear los embeddings e indexarlos en ChromaDB)
	./venv/bin/$(PYTHON_BIN) src/main.py --index-chromadb

db_reset: ## Resetea la base de datos de ChromaDB (elimina toda la información indexada)
	./venv/bin/$(PYTHON_BIN) src/main.py --index-chromadb --reset-chromadb

# Análisis de contenido

analyze_content: ## Analiza el contenido scrappeado: muestra estadísticas del contenido scrappeado, calidad del scrapping y genera preguntas de ejemplo para evaluar la calidad del scrapping
	./venv/bin/$(PYTHON_BIN) scripts/analyze_content.py
	./venv/bin/$(PYTHON_BIN) -m pytest tests/test_realistic_queries.py -v -s
