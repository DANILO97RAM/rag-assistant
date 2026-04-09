PYTHON_BIN=python3.12

setup:
	$(PYTHON_BIN) -m venv venv
	./venv/bin/pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
	sudo ./venv/bin/playwright install-deps chromium

main:
	./venv/bin/python src/main.py --depth 2 --max-pages 50 --concurrency 10
	
docker-up:
	docker compose up -d

clean:
	rm -rf venv venv
	find . -type d -name "__pycache__" -exec rm -rf {} +

test_embeddings:
	./venv/bin/pip install pytest --quiet || true
	./venv/bin/pytest tests/test_embedder.py -v

generate_embeddings_sentence:
	./venv/bin/python tests/generate_embeddings.py --provider sentence-transformers

generate_embeddings_gemini:
	./venv/bin/python tests/generate_embeddings.py --provider gemini --api-key $GEMINI_API_KEY

test_evaluate_chunk_strategy:
	./venv/bin/python tests/evaluate_chunking_strategies.py

test_compare_embeddings_20_samples:
	./venv/bin/python  tests/compare_embeddings.py --gemini-key $GEMINI_API_KEY --sample-size 20

test_eva
# scrapper:
# 	./venv/bin/python src/core/scrapper.py --depth 2 --max-pages 50 --concurrency 10

# clean_json_crawled:
# 	find . -type f -name "crawled_*.json" -delete