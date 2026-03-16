import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import type { Request, Response } from "express";

import { config } from "./config.js";
import { createMcpDocServer } from "./server.js";

const app = createMcpExpressApp();

const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (_req: Request, res: Response) => {
  const transport = new SSEServerTransport("/messages", res);
  transports.set(transport.sessionId, transport);

  transport.onclose = () => {
    transports.delete(transport.sessionId);
  };

  const server = createMcpDocServer();
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

const httpServer = app.listen(config.mcpPort, () => {
  console.log(
    `MCP SSE server listening on http://localhost:${config.mcpPort}/sse`,
  );
});

async function shutdown() {
  for (const transport of transports.values()) {
    await transport.close();
  }
  transports.clear();
  httpServer.close();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
