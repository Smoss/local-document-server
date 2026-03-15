import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

import { DocumentApiClient } from "./client.js";
import { config } from "./config.js";
import {
  addDocumentSchema,
  createAddDocumentHandler,
  createListDocumentsHandler,
  createReadDocumentHandler,
  createSearchDocumentsHandler,
  createUpdateDocumentHandler,
  listDocumentsSchema,
  readDocumentSchema,
  searchDocumentsSchema,
  updateDocumentSchema,
} from "./tools/index.js";

export function createMcpDocServer(client?: DocumentApiClient): McpServer {
  const server = new McpServer({
    name: "doc-server-mcp",
    version: "0.1.0",
  });

  const apiClient = client ?? new DocumentApiClient(config.documentApiBaseUrl);

  server.tool(
    "search_documents",
    "Search documents by semantic similarity",
    searchDocumentsSchema,
    createSearchDocumentsHandler(apiClient),
  );

  server.tool(
    "read_document",
    "Read a document's content by ID",
    readDocumentSchema,
    createReadDocumentHandler(apiClient),
  );

  server.tool(
    "list_documents",
    "List all documents with pagination",
    listDocumentsSchema,
    createListDocumentsHandler(apiClient),
  );

  server.tool(
    "add_document",
    "Add a document by providing its text content",
    addDocumentSchema,
    createAddDocumentHandler(apiClient),
  );

  server.tool(
    "update_document",
    "Update a document's content",
    updateDocumentSchema,
    createUpdateDocumentHandler(apiClient),
  );

  return server;
}
