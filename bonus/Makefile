# System variables
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@echo "  help              Show this help message"
	@echo "  venv              Create a virtual environment"
	@echo "  install           Install production and development dependencies"
	@echo "  run               Run the application main script"
	@echo "  clean             Remove python cache files and build artifacts"


.PHONY: venv
venv: ## Create a virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Run 'source $(VENV)/bin/activate' to use it."

.PHONY: install
install: venv ## Install production and development dependencies
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(BIN)/pip install -r requirements-dev.txt; fi

.PHONY: run
run: ## Run the application main script
	$(BIN)/python3 gomoku.py




.PHONY: clean
clean: ## Remove python cache files and build artifacts
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
