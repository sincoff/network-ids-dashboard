.PHONY: install dev format lint deploy-local clean

# Variables
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Colors
CYAN := \033[0;36m
NC := \033[0m

$(VENV)/bin/activate: backend/requirements.txt
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	$(PIP) install ruff mypy

install: $(VENV)/bin/activate

dev: install
	@echo "$(CYAN)Starting local development server...$(NC)"
	@echo "NOTE: Packet sniffing requires sudo capabilities. You will be prompted for your password."
	sudo -E $(VENV)/bin/uvicorn backend.app.main:app --app-dir . --host 0.0.0.0 --port 8000 --reload

format: install
	@echo "$(CYAN)Formatting code...$(NC)"
	$(VENV)/bin/ruff format .
	$(VENV)/bin/ruff check --fix .

lint: install
	@echo "$(CYAN)Running linters and type checkers...$(NC)"
	$(VENV)/bin/ruff check .
	$(VENV)/bin/mypy backend/app

deploy-local:
	@echo "$(CYAN)Running production deployment script...$(NC)"
	sudo bash deploy/setup.sh

clean:
	@echo "$(CYAN)Cleaning up generated files...$(NC)"
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf backend/app/__pycache__
	rm -rf .ruff_cache
	rm -rf .mypy_cache
