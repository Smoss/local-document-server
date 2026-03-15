---
name: local-document-server
description: Use the local-document-server MCP server to search, read, and list documents stored in the document server. Use when the user asks to find, search, read, or browse documents, or when they use /local-document-server.
---

# Local Document Server MCP

MCP server exposing document management tools over SSE.

## Connection

SSE endpoint: `http://localhost:{MCP_PORT}/sse` (default port `30527`)

## Tools

### `search_documents`

Semantic search across all stored documents.

- **Input**: `{ query: string }`
- **Output**: Results grouped by document, each with matching chunks and relevance scores

Use this to find documents related to a topic or question. Results are ranked by cosine similarity against document chunk embeddings.

### `read_document`

Read a document's full content by ID.

- **Input**: `{ document_id: string }` (UUID)
- **Output**: Document content as text

Use document IDs from `search_documents` or `list_documents` results.

### `list_documents`

List all documents with pagination.

- **Input**: `{ page?: number, page_size?: number }`
- **Output**: Paginated list with document metadata (id, filename, content_type, status, created_at)

## Setup & Running

```bash
make install      # Install Python + Node dependencies
make db           # Start PostgreSQL with pgvector (port 5438)
make serve        # Start FastAPI backend (port 7571)
make mcp-start    # Start MCP server (port 30527)
```

All three services (db, backend, MCP) must be running for the MCP tools to work.

## Testing

```bash
make test         # All tests (Python + MCP)
make test-py      # Python backend tests only (uses test DB on port 7730)
make test-mcp     # MCP server tests only
```

## Key Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_PORT` | `30527` | MCP server port |
| `DOCUMENT_API_BASE_URL` | `http://localhost:7571` | FastAPI backend URL |
| `DATABASE_URL` | `postgresql+psycopg://docserver:docserver@localhost:5438/docserver` | PostgreSQL connection |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama embedding service |
| `OLLAMA_MODEL` | `nomic-embed-text` | Embedding model |
| `CHUNK_SIZE` | `512` | Words per document chunk |
| `CHUNK_OVERLAP` | `50` | Word overlap between chunks |
| `SEARCH_SIMILARITY_THRESHOLD` | `0.3` | Minimum cosine similarity for search results |
| `SEARCH_MAX_RESULTS` | `20` | Maximum search results returned |

## Uploading Documents

Documents are uploaded via the FastAPI backend directly (not through MCP):

```bash
curl -X POST http://localhost:7571/api/documents -F "file=@path/to/file.txt"
```

The backend extracts text, chunks it, generates embeddings via Ollama, and stores everything in PostgreSQL with pgvector. Documents are then searchable through the MCP tools.
