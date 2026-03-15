import { describe, it, expect, vi, beforeEach } from "vitest";
import { DocumentApiClient, DocumentApiError } from "../src/client.js";

describe("DocumentApiClient", () => {
  let client: DocumentApiClient;

  beforeEach(() => {
    client = new DocumentApiClient("http://localhost:7571");
    vi.restoreAllMocks();
  });

  // @TestID 4a713c7d-2d49-4f62-aa8e-b86ef5366fd8
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify searchDocuments constructs the correct POST URL
  it("constructs correct URL for searchDocuments", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ query: "test", results: [] }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await client.searchDocuments("test query");

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:7571/api/search",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "test query" }),
      }),
    );
  });

  // @TestID f0227a42-7276-4c3f-90ee-b9e272307301
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify listDocuments constructs URL with pagination query params
  it("constructs correct URL for listDocuments with pagination", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0 }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await client.listDocuments(2, 10);

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:7571/api/documents?page=2&page_size=10",
      undefined,
    );
  });

  // @TestID 4f26462f-4805-40a7-8cbb-d898e8b72c09
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify readDocument constructs the correct file URL
  it("constructs correct URL for readDocument", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve("file content"),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await client.readDocument("abc-123");

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:7571/api/documents/abc-123/file",
      expect.anything(),
    );
    expect(result).toBe("file content");
  });

  // @TestID 3aa8a269-8bec-490b-b68f-54f39a9ff037
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify fetch network errors are wrapped in DocumentApiError
  it("wraps fetch errors in DocumentApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Connection refused")),
    );

    await expect(client.searchDocuments("test")).rejects.toThrow(
      DocumentApiError,
    );
  });

  // @TestID 07963e54-e067-48f7-ae30-c07b94dfd6c2
  // @SystemName Document MCP Server
  // @TestType Unit
  // @TestDescription Verify non-ok HTTP responses are wrapped in DocumentApiError
  it("wraps non-ok responses in DocumentApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      }),
    );

    await expect(client.listDocuments()).rejects.toThrow(DocumentApiError);
  });
});
