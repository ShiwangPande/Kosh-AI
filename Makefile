.PHONY: help build up down restart logs backend-logs worker-logs frontend-logs db-shell seed test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────────

build: ## Build all containers
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Tail all service logs
	docker compose logs -f --tail=50

backend-logs: ## Tail backend logs
	docker compose logs -f backend

worker-logs: ## Tail worker logs
	docker compose logs -f worker

frontend-logs: ## Tail frontend logs
	docker compose logs -f frontend

# ── Database ────────────────────────────────────────────────

db-shell: ## Open PostgreSQL shell
	docker compose exec db psql -U kosh -d kosh_ai

db-reset: ## Reset database (WARNING: destroys data)
	docker compose down -v
	docker compose up -d db
	sleep 3
	docker compose exec db psql -U kosh -d kosh_ai -f /docker-entrypoint-initdb.d/01_schema.sql

# ── Development ─────────────────────────────────────────────

seed: ## Seed database with sample data
	docker compose exec backend python -m scripts.seed_db

test: ## Run test requests
	python scripts/test_requests.py

install-backend: ## Install backend deps locally
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend deps locally
	cd frontend && npm install

dev-backend: ## Run backend locally (not in Docker)
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend locally (not in Docker)
	cd frontend && npm run dev

# ── Cleanup ─────────────────────────────────────────────────

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi all
	docker system prune -f
