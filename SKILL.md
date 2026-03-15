---
name: local-document-server
description: Use the local-document-server MCP server to search, read, list, add, and update documents stored in the document server. Use when the user asks to find, search, read, browse, add, or edit documents, or when they use /local-document-server.
---

# Local Document Server MCP

MCP server exposing document management tools over SSE.

## Connection

SSE endpoint: `http://localhost:{MCP_PORT}/sse` (default port `30527`)

## Tools

### `search_documents`

Semantic search returning the top K most relevant documents with full content.

- **Input**: `{ query: string }`
- **Output**: Top K documents ranked by best chunk similarity. Each result includes full document `content` plus matching chunks (with `chunk_id`, `chunk_index`, `relevance_score` only — no chunk content).

Use this to find documents related to a topic or question. Documents are ranked by the cosine similarity of their best-matching chunk embedding. `SEARCH_MAX_RESULTS` controls the maximum number of documents returned (default 20).

### `read_document`

Read a document's full content by ID.

- **Input**: `{ document_id: string }` (UUID)
- **Output**: Document content as text

Use document IDs from `search_documents` or `list_documents` results.

### `list_documents`

List all documents with pagination.

- **Input**: `{ page?: number, page_size?: number }`
- **Output**: Paginated list with document metadata (id, filename, content_type, status, created_at)

### `add_document`

Add a new document by providing its text content directly (no file upload needed).

- **Input**: `{ content: string, filename: string, content_type?: string }`
- **Output**: Created document metadata

The `content_type` defaults to `text/plain` if omitted. The backend will chunk the content and generate embeddings automatically.

### `update_document`

Update an existing document's content (and optionally its filename).

- **Input**: `{ document_id: string, content: string, filename?: string }` (document_id is a UUID)
- **Output**: Updated document metadata

The backend re-chunks and re-embeds the new content automatically.

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
| `SEARCH_MAX_RESULTS` | `20` | Maximum documents returned by search |

## Adding Documents

Documents can be added two ways:

1. **Via MCP** — Use the `add_document` tool to provide text content directly
2. **Via REST API** — Upload a file to the FastAPI backend:
   ```bash
   curl -X POST http://localhost:7571/api/documents -F "file=@path/to/file.txt"
   ```

In both cases, the backend chunks the content, generates embeddings via Ollama, and stores everything in PostgreSQL with pgvector. Documents are then searchable through the MCP tools.
