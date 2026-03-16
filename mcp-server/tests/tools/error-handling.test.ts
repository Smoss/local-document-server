import { describe, it, expect, vi } from "vitest";
import { DocumentApiError } from "../../src/client.js";
import { createSearchDocumentsHandler } from "../../src/tools/search-documents.js";
import { createReadDocumentHandler } from "../../src/tools/read-document.js";
import { createListDocumentsHandler } from "../../src/tools/list-documents.js";
import type { DocumentApiClient } from "../../src/client.js";

describe("error handling", () => {
  const apiError = new DocumentApiError("Connection refused");

  // @TestID 648b8819-5cba-408d-a191-bb190d356040
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify search_documents returns isError on API failure
  it("search_documents returns isError on failure", async () => {
    const mockClient = {
      searchDocuments: vi.fn().mockRejectedValue(apiError),
    } as unknown as DocumentApiClient;

    const handler = createSearchDocumentsHandler(mockClient);
    const result = await handler({ query: "test" });

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Connection refused");
  });

  // @TestID bd14a961-6fb5-40ab-b0c9-22f8d3c519a6
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify read_document returns isError on API failure
  it("read_document returns isError on failure", async () => {
    const mockClient = {
      readDocument: vi.fn().mockRejectedValue(apiError),
    } as unknown as DocumentApiClient;

    const handler = createReadDocumentHandler(mockClient);
    const result = await handler({ document_id: "bad-id" });

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Connection refused");
  });

  // @TestID 24219c0a-0bfe-48d0-ad52-66b5d1481cdf
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify list_documents returns isError on API failure
  it("list_documents returns isError on failure", async () => {
    const mockClient = {
      listDocuments: vi.fn().mockRejectedValue(apiError),
    } as unknown as DocumentApiClient;

    const handler = createListDocumentsHandler(mockClient);
    const result = await handler({});

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Connection refused");
  });
});
