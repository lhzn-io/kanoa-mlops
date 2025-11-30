.PHONY: setup lint test clean help

help:
	@echo "Available commands:"
	@echo "  setup   - Create conda environment and install dependencies"
	@echo "  lint    - Run linting checks (flake8, mypy, shellcheck)"
	@echo "  test    - Run smoke tests"
	@echo "  clean   - Remove temporary files"

setup:
	conda env create -f environment.yml || conda env update -f environment.yml

lint:
	@echo "Running python linting..."
	flake8 examples/
	mypy examples/
	@echo "Running shell linting (if installed)..."
	-shellcheck scripts/*.sh

test:
	@echo "Running smoke tests..."
	python examples/quickstart-molmo.py --help
	python examples/quickstart-gemma3.py --help

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
