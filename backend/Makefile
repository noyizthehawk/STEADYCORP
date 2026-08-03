# Common backend tasks. Run from backend/ with the venv active (or these call it).
VENV := .venv/bin

.PHONY: install run test lint fmt migrate upgrade downgrade

install:
	python3 -m venv .venv
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -r requirements.txt

run:
	$(VENV)/uvicorn app.main:app --reload

test:
	$(VENV)/pytest

lint:
	$(VENV)/ruff check app tests

fmt:
	$(VENV)/ruff format app tests
	$(VENV)/ruff check --fix app tests

# make migrate m="add drop and brick tables"
migrate:
	$(VENV)/alembic revision --autogenerate -m "$(m)"

upgrade:
	$(VENV)/alembic upgrade head

downgrade:
	$(VENV)/alembic downgrade -1
