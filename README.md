# Local Document Server

Local document management with semantic search, exposed to AI agents via MCP.

## Architecture

```
┌────────┐     SSE      ┌────────────┐    HTTP     ┌─────────┐
│ Client ├─────────────►│ MCP Server ├────────────►│ FastAPI │
└────────┘  (port 30527)└────────────┘ (port 7571) └────┬────┘
                                                        │
                                              ┌─────────┴─────────┐
                                              │                   │
                                         ┌────▼─────┐      ┌─────▼────┐
                                         │PostgreSQL│      │  Ollama  │
                                         │+ pgvector│      │embeddings│
                                         └──────────┘      └──────────┘
```

## Prerequisites

- Python 3.13+
- Node.js
- Docker
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) (optional — required for semantic search)

## Quick Start

```bash
cp .env.example .env          # configure environment
make install                  # install Python + Node dependencies
make db                       # start PostgreSQL with pgvector
ollama pull nomic-embed-text-v2-moe:latest  # download embedding model (optional)
make serve                    # start FastAPI on port 7571
make mcp-start                # start MCP server on port 30527 (separate terminal)
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://docserver:docserver@localhost:5438/docserver` | PostgreSQL connection string |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `nomic-embed-text` | Embedding model name |
| `EMBEDDING_DIM` | `768` | Embedding vector dimensions |
| `UPLOAD_DIR` | `./storage` | File storage directory |
| `CHUNK_SIZE` | `512` | Words per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap in words between chunks |
| `SEARCH_SIMILARITY_THRESHOLD` | `0.3` | Minimum cosine similarity for search results |
| `SEARCH_MAX_RESULTS` | `20` | Maximum search results returned |
| `MCP_PORT` | `30527` | MCP server port |
| `DOCUMENT_API_BASE_URL` | `http://localhost:7571` | FastAPI URL used by the MCP server (set when running on a different host) |

## MCP Server

The MCP server exposes document operations to AI agents over SSE.

**Connection URL:** `http://localhost:30527/sse`

### Tools

| Tool | Description |
|---|---|
| `search_documents` | Search documents by semantic similarity |
| `read_document` | Read a document's content by ID |
| `list_documents` | List all documents with pagination |

### Client Configuration

```json
{
  "mcpServers": {
    "doc-server": {
      "url": "http://localhost:30527/sse"
    }
  }
}
```

## API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/documents` | Upload a document |
| `GET` | `/api/documents` | List documents (paginated) |
| `GET` | `/api/documents/{id}/file` | Download original file |
| `GET` | `/api/documents/{id}/chunks` | Get document chunks |
| `POST` | `/api/search` | Semantic search across documents |
| `GET` | `/health` | Health check |

## Testing

```bash
make test       # run all tests
make test-py    # Python tests only (starts isolated test DB on port 7730)
make test-mcp   # MCP server tests only
```

Tests use an isolated PostgreSQL instance so they don't affect your dev database.

## Telemetry

No dependencies in this project send telemetry.
