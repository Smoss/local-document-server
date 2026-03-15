import { describe, it, expect, beforeAll, afterAll, vi } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import type { Server } from "node:http";
import type { Express, Request, Response } from "express";

import { createMcpDocServer } from "../../src/server.js";
import type { DocumentApiClient } from "../../src/client.js";

let app: Express;
let httpServer: Server;
let baseUrl: string;
const transports = new Map<string, SSEServerTransport>();

const mockClient = {
  searchDocuments: vi.fn().mockResolvedValue({
    results: [{ chunk: "hello", score: 0.9 }],
  }),
  readDocument: vi.fn().mockResolvedValue("file content"),
  listDocuments: vi.fn().mockResolvedValue({
    items: [
      {
        id: "doc-1",
        filename: "a.txt",
        content_type: "text/plain",
        status: "embedded",
        created_at: "2025-01-01",
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  }),
} as unknown as DocumentApiClient;

beforeAll(async () => {
  app = createMcpExpressApp();

  app.get("/sse", async (_req: Request, res: Response) => {
    const transport = new SSEServerTransport("/messages", res);
    transports.set(transport.sessionId, transport);
    transport.onclose = () => transports.delete(transport.sessionId);
    const server = createMcpDocServer(mockClient);
    await server.connect(transport);
  });

  app.post("/messages", async (req: Request, res: Response) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (!transport) {
      res.status(400).json({ error: "Unknown session" });
      return;
    }
    await transport.handlePostMessage(req, res, req.body);
  });

  await new Promise<void>((resolve) => {
    httpServer = app.listen(0, () => {
      const addr = httpServer.address();
      const port = typeof addr === "object" && addr ? addr.port : 0;
      baseUrl = `http://127.0.0.1:${port}`;
      resolve();
    });
  });
});

afterAll(async () => {
  for (const t of transports.values()) await t.close();
  transports.clear();
  await new Promise<void>((resolve) => httpServer.close(() => resolve()));
});

describe("SSE transport", () => {
  it("lists all three tools via SSE", async () => {
    const transport = new SSEClientTransport(new URL(`${baseUrl}/sse`));
    const client = new Client({ name: "test-client", version: "0.1.0" });
    await client.connect(transport);

    const { tools } = await client.listTools();
    expect(tools).toHaveLength(3);

    const names = tools.map((t) => t.name).sort();
    expect(names).toEqual(["list_documents", "read_document", "search_documents"]);

    await client.close();
  });

  it("calls list_documents tool via SSE", async () => {
    const transport = new SSEClientTransport(new URL(`${baseUrl}/sse`));
    const client = new Client({ name: "test-client", version: "0.1.0" });
    await client.connect(transport);

    const result = await client.callTool({ name: "list_documents", arguments: {} });
    const content = result.content as Array<{ type: string; text: string }>;
    expect(result.isError).toBeFalsy();
    const parsed = JSON.parse(content[0].text);
    expect(parsed.items).toHaveLength(1);
    expect(parsed.items[0].id).toBe("doc-1");

    await client.close();
  });
});
