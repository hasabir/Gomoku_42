# System variables
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
NAME := Gomoku

# Default target
.DEFAULT_GOAL := all

#==============================================================================
# PHONY targets
#==============================================================================

.PHONY: all
all: $(NAME) ## Build the executable (alias for Gomoku)

.PHONY: $(NAME)
$(NAME): venv install ## Create the executable
	@echo "Creating executable $(NAME)..."
	@echo "#!/bin/bash" > $(NAME)
	@echo "$(BIN)/python3 gomoku.py \"\$$@\"" >> $(NAME)
	@chmod +x $(NAME)
	@echo "Executable $(NAME) created successfully!"

.PHONY: venv
venv: ## Create a virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Run 'source $(VENV)/bin/activate' to use it."

.PHONY: install
install: venv ## Install dependencies
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(BIN)/pip install -r requirements-dev.txt; fi

.PHONY: clean
clean: ## Remove python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "Cache files removed."

.PHONY: fclean
fclean: clean ## Remove virtual environment and executable
	rm -rf $(VENV)
	rm -f $(NAME)
	@echo "Virtual environment and executable removed."

.PHONY: re
re: fclean all ## Rebuild everything from scratch

.PHONY: run
run: ## Run the application
	$(BIN)/python3 gomoku.py

.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@echo "  all               Build the executable (default)"
	@echo "  $(NAME)           Create the executable"
	@echo "  venv              Create a virtual environment"
	@echo "  install           Install dependencies"
	@echo "  clean             Remove python cache files"
	@echo "  fclean            Remove virtual environment and executable"
	@echo "  re                Rebuild everything from scratch"
	@echo "  run               Run the application"
	@echo "  help              Show this help message"