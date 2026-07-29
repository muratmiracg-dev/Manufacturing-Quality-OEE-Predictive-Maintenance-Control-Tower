.PHONY: install quality test pipeline api audit

install:
	python -m pip install -e ".[dev,postgres]"

quality:
	ruff check .
	ruff format --check .

test:
	pytest --cov=manufacturing_ct --cov-report=term-missing --cov-report=xml

pipeline:
	python -m manufacturing_ct.pipeline --config configs/base.yaml

api:
	uvicorn manufacturing_ct.api:app --host 0.0.0.0 --port 8000

audit:
	pip-audit -r requirements.txt

