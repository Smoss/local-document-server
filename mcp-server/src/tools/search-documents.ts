import { z } from "zod";
import type { DocumentApiClient } from "../client.js";

export const searchDocumentsSchema = {
  query: z.string().describe("Search query text"),
};

export function createSearchDocumentsHandler(client: DocumentApiClient) {
  return async (args: { query: string }) => {
    try {
      const results = await client.searchDocuments(args.query);
      return {
        content: [
          { type: "text" as const, text: JSON.stringify(results, null, 2) },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Error searching documents: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  };
}
