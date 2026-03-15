import { describe, it, expect, vi } from "vitest";
import { createListDocumentsHandler } from "../../src/tools/list-documents.js";
import type { DocumentApiClient } from "../../src/client.js";

describe("list_documents tool", () => {
  it("returns paginated document list", async () => {
    const mockClient = {
      listDocuments: vi.fn().mockResolvedValue({
        items: [
          { id: "doc-1", filename: "a.txt", content_type: "text/plain", status: "embedded", created_at: "2025-01-01" },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      }),
    } as unknown as DocumentApiClient;

    const handler = createListDocumentsHandler(mockClient);
    const result = await handler({});

    const parsed = JSON.parse(result.content[0].text);
    expect(parsed.items).toHaveLength(1);
    expect(parsed.total).toBe(1);
  });

  it("forwards pagination params", async () => {
    const mockClient = {
      listDocuments: vi.fn().mockResolvedValue({ items: [], total: 0, page: 3, page_size: 5 }),
    } as unknown as DocumentApiClient;

    const handler = createListDocumentsHandler(mockClient);
    await handler({ page: 3, page_size: 5 });

    expect(mockClient.listDocuments).toHaveBeenCalledWith(3, 5);
  });
});
