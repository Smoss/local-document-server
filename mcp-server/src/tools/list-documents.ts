import { z } from "zod";
import type { DocumentApiClient } from "../client.js";

export const listDocumentsSchema = {
  page: z.number().optional().describe("Page number (default 1)"),
  page_size: z.number().optional().describe("Items per page (default 20)"),
};

export function createListDocumentsHandler(client: DocumentApiClient) {
  return async (args: { page?: number; page_size?: number }) => {
    try {
      const results = await client.listDocuments(args.page, args.page_size);
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
            text: `Error listing documents: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  };
}
