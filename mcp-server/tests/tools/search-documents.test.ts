import { describe, it, expect, vi } from "vitest";
import { createSearchDocumentsHandler } from "../../src/tools/search-documents.js";
import type { DocumentApiClient } from "../../src/client.js";

describe("search_documents tool", () => {
  // @TestID 455f2b15-d737-441c-8ee5-abdbd94c26de
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify search returns JSON with chunks and metadata
  it("returns JSON response with chunks and metadata", async () => {
    const mockClient = {
      searchDocuments: vi.fn().mockResolvedValue({
        query: "test",
        results: [
          {
            document_id: "doc-1",
            filename: "test.txt",
            content_type: "text/plain",
            status: "embedded",
            created_at: "2025-01-01T00:00:00Z",
            chunks: [
              {
                chunk_id: "chunk-1",
                chunk_index: 0,
                content: "test content",
                relevance_score: 0.95,
              },
            ],
          },
        ],
      }),
    } as unknown as DocumentApiClient;

    const handler = createSearchDocumentsHandler(mockClient);
    const result = await handler({ query: "test" });

    expect(result.content[0].type).toBe("text");
    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.results).toHaveLength(1);
    expect(parsed.results[0].filename).toBe("test.txt");
    expect(parsed.results[0].chunks[0].relevance_score).toBe(0.95);
  });

  // @TestID 4f0adbf6-393d-40a7-9453-d48a4f23fd91
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify search with no matches returns empty results array
  it("returns empty results", async () => {
    const mockClient = {
      searchDocuments: vi.fn().mockResolvedValue({
        query: "nothing",
        results: [],
      }),
    } as unknown as DocumentApiClient;

    const handler = createSearchDocumentsHandler(mockClient);
    const result = await handler({ query: "nothing" });

    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.results).toHaveLength(0);
  });
});
