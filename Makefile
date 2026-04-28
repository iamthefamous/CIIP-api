.PHONY: start_redis lint test run

start_redis:
docker run --rm -p 6379:6379 redis:7

lint:
pre-commit run --all-files

test:
pytest -q

run:
uvicorn app.main:app --reload
