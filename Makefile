PYTHON_BIN=python3.12

setup:
	$(PYTHON_BIN) -m venv venv
	./venv/bin/pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
	sudo ./venv/bin/playwright install-deps chromium

main:
	./venv/bin/python src/main.py --depth 2 --max-pages 50 --concurrency 10

main-force:
	./venv/bin/python src/main.py --depth 2 --max-pages 50 --concurrency 10 --force-scrape
	
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
	./venv/bin/python tests/db/test_chromadb.py -v -s

db_queries:
	./venv/bin/python tests/db/test_chromadb_queries.py -v -s
# scrapper:
# 	./venv/bin/python src/core/scrapper.py --depth 2 --max-pages 50 --concurrency 10

# clean_json_crawled:
# 	find . -type f -name "crawled_*.json" -delete