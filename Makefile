setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	sudo ./venv/bin/playwright install-deps chromium

scrapper:
	./venv/bin/python src/core/scrapper.py --depth 2 --max-pages 50 --concurrency 10

main:
	./venv/bin/python src/main.py
	
docker-up:
	docker compose up -d

clean:
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -rf {} +

clean_json_crawled:
	find . -type f -name "crawled_*.json" -delete