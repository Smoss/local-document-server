import { z } from "zod";
import type { DocumentApiClient } from "../client.js";

export const readDocumentSchema = {
  document_id: z.string().describe("The document ID to read"),
};

export function createReadDocumentHandler(client: DocumentApiClient) {
  return async (args: { document_id: string }) => {
    try {
      const content = await client.readDocument(args.document_id);
      return {
        content: [{ type: "text" as const, text: content }],
      };
    } catch (error) {
      return {
        content: [
          { type: "text" as const, text: `Error reading document: ${(error as Error).message}` },
        ],
        isError: true,
      };
    }
  };
}
