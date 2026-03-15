import { describe, it, expect, vi } from "vitest";
import { createReadDocumentHandler } from "../../src/tools/read-document.js";
import type { DocumentApiClient } from "../../src/client.js";

describe("read_document tool", () => {
  it("returns document content as text", async () => {
    const mockClient = {
      readDocument: vi.fn().mockResolvedValue("Hello, world!"),
    } as unknown as DocumentApiClient;

    const handler = createReadDocumentHandler(mockClient);
    const result = await handler({ document_id: "doc-1" });

    expect(result.content[0].text).toBe("Hello, world!");
    expect(mockClient.readDocument).toHaveBeenCalledWith("doc-1");
  });
});
