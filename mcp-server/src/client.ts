export class DocumentApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
  ) {
    super(message);
    this.name = "DocumentApiError";
  }
}

export class DocumentApiClient {
  constructor(private baseUrl: string) {}

  async searchDocuments(query: string, maxResults?: number): Promise<unknown> {
    const body: Record<string, unknown> = { query };
    if (maxResults !== undefined) body.max_results = maxResults;

    const response = await this.fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return response;
  }

  async readDocument(documentId: string): Promise<string> {
    const response = await this.fetch(
      `/api/documents/${documentId}/file`,
      {},
      true,
    );
    return response as string;
  }

  async listDocuments(page?: number, pageSize?: number): Promise<unknown> {
    const params = new URLSearchParams();
    if (page !== undefined) params.set("page", String(page));
    if (pageSize !== undefined) params.set("page_size", String(pageSize));

    const query = params.toString();
    const path = `/api/documents${query ? `?${query}` : ""}`;
    return this.fetch(path);
  }

  async addDocument(
    content: string,
    filename: string,
    contentType?: string,
  ): Promise<unknown> {
    const body: Record<string, unknown> = { content, filename };
    if (contentType !== undefined) body.content_type = contentType;

    return this.fetch("/api/documents/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  private async fetch(
    path: string,
    init?: RequestInit,
    text?: boolean,
  ): Promise<unknown> {
    let response: Response;
    try {
      response = await globalThis.fetch(`${this.baseUrl}${path}`, init);
    } catch (error) {
      throw new DocumentApiError(
        `Failed to connect to document API: ${(error as Error).message}`,
      );
    }

    if (!response.ok) {
      throw new DocumentApiError(
        `API returned ${response.status}: ${response.statusText}`,
        response.status,
      );
    }

    return text ? response.text() : response.json();
  }
}
