.PHONY: install install-dev test lint typecheck build clean

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e .[dev]

test:
	pytest

lint:
	ruff check src tests examples

typecheck:
	mypy src/

build:
	python -m build

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache src/*.egg-info src/*/*.egg-info
