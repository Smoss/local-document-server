import { describe, it, expect, vi } from "vitest";
import { createUpdateDocumentHandler } from "../../src/tools/update-document.js";
import { DocumentApiError } from "../../src/client.js";
import type { DocumentApiClient } from "../../src/client.js";

describe("update_document tool", () => {
  // @TestID 0561bb67-0b99-4ea3-b68c-86ee2d512f69
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify update_document forwards params to API client and returns response
  it("forwards document_id and content to the API client and returns the response", async () => {
    const mockClient = {
      updateDocument: vi.fn().mockResolvedValue({
        id: "doc-123",
        filename: "test.txt",
        content_type: "text/plain",
        status: "pending_embedding",
        content: "updated text",
        updated_at: "2026-03-15T00:00:00Z",
      }),
    } as unknown as DocumentApiClient;

    const handler = createUpdateDocumentHandler(mockClient);
    const result = await handler({
      document_id: "doc-123",
      content: "updated text",
    });

    expect(mockClient.updateDocument).toHaveBeenCalledWith(
      "doc-123",
      "updated text",
      undefined,
    );
    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.id).toBe("doc-123");
    expect(parsed.content).toBe("updated text");
    expect(result).not.toHaveProperty("isError");
  });

  // @TestID 40d21c9e-3045-44c6-b054-a7990ee866e2
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify update_document returns isError when API is unreachable
  it("returns isError true when the Document API is unreachable", async () => {
    const mockClient = {
      updateDocument: vi
        .fn()
        .mockRejectedValue(
          new DocumentApiError("Failed to connect to document API"),
        ),
    } as unknown as DocumentApiClient;

    const handler = createUpdateDocumentHandler(mockClient);
    const result = await handler({
      document_id: "doc-123",
      content: "new content",
    });

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("Error updating document");
  });
});
