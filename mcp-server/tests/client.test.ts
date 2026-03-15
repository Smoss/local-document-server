import { describe, it, expect, vi, beforeEach } from "vitest";
import { DocumentApiClient, DocumentApiError } from "../src/client.js";

describe("DocumentApiClient", () => {
  let client: DocumentApiClient;

  beforeEach(() => {
    client = new DocumentApiClient("http://localhost:7571");
    vi.restoreAllMocks();
  });

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

  it("wraps fetch errors in DocumentApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Connection refused")),
    );

    await expect(client.searchDocuments("test")).rejects.toThrow(
      DocumentApiError,
    );
  });

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
