.PHONY: help install dev db db-stop db-test db-test-stop test test-py test-mcp \
        serve mcp-build mcp-start clean lint

help:                          ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────
install:                       ## Install all dependencies (Python + Node)
	uv sync --all-extras
	cd mcp-server && npm install

# ── Database ─────────────────────────────────────────────────────────────
db:                            ## Start dev PostgreSQL + pgvector
	docker compose up -d
	@echo "Waiting for PostgreSQL..."
	@docker compose exec db pg_isready -U docserver -q --timeout=30

db-stop:                       ## Stop dev database
	docker compose down

db-test:                       ## Start test PostgreSQL + pgvector (port 7730)
	docker compose -f docker-compose.test.yml up -d
	@echo "Waiting for test PostgreSQL..."
	@until docker compose -f docker-compose.test.yml exec test-db pg_isready -U docserver -q 2>/dev/null; do sleep 1; done

db-test-stop:                  ## Stop test database
	docker compose -f docker-compose.test.yml down

# ── Run ──────────────────────────────────────────────────────────────────
serve: db                      ## Start the FastAPI server (auto-starts db)
	uv run uvicorn doc_server.main:app --reload --host 0.0.0.0 --port 7571

# ── MCP Server ───────────────────────────────────────────────────────────
mcp-build:                     ## Build the MCP server
	cd mcp-server && npm run build

mcp-start: mcp-build           ## Start the MCP server (SSE)
	cd mcp-server && node dist/index.js

# ── Tests ────────────────────────────────────────────────────────────────
test: test-py test-mcp         ## Run all tests

test-py: db-test               ## Run Python tests (auto-starts test db)
	uv run pytest -v

test-mcp:                      ## Run MCP server tests
	cd mcp-server && npm test

# ── Cleanup ──────────────────────────────────────────────────────────────
clean:                         ## Stop all containers, remove volumes
	docker compose down -v
	docker compose -f docker-compose.test.yml down -v
	rm -rf mcp-server/dist
	rm -rf storage/*
