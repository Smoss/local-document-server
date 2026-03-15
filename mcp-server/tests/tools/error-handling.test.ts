import { describe, it, expect, vi } from "vitest";
import { DocumentApiError } from "../../src/client.js";
import { createSearchDocumentsHandler } from "../../src/tools/search-documents.js";
import { createReadDocumentHandler } from "../../src/tools/read-document.js";
import { createListDocumentsHandler } from "../../src/tools/list-documents.js";
import type { DocumentApiClient } from "../../src/client.js";

describe("error handling", () => {
  const apiError = new DocumentApiError("Connection refused");

  it("search_documents returns isError on failure", async () => {
    const mockClient = {
      searchDocuments: vi.fn().mockRejectedValue(apiError),
    } as unknown as DocumentApiClient;

    const handler = createSearchDocumentsHandler(mockClient);
    const result = await handler({ query: "test" });

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Connection refused");
  });

  it("read_document returns isError on failure", async () => {
    const mockClient = {
      readDocument: vi.fn().mockRejectedValue(apiError),
    } as unknown as DocumentApiClient;

    const handler = createReadDocumentHandler(mockClient);
    const result = await handler({ document_id: "bad-id" });

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Connection refused");
  });

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
