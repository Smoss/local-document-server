export const config = {
  documentApiBaseUrl:
    process.env.DOCUMENT_API_BASE_URL || "http://localhost:7571",
  mcpPort: parseInt(process.env.MCP_PORT || "30527", 10),
};
