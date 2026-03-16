import { z } from "zod";
import type { DocumentApiClient } from "../client.js";

export const addDocumentSchema = {
  content: z.string().describe("The text content of the document"),
  filename: z.string().describe("Filename for the document"),
  content_type: z
    .string()
    .optional()
    .describe("MIME type (defaults to text/plain)"),
};

export function createAddDocumentHandler(client: DocumentApiClient) {
  return async (args: {
    content: string;
    filename: string;
    content_type?: string;
  }) => {
    try {
      const result = await client.addDocument(
        args.content,
        args.filename,
        args.content_type,
      );
      return {
        content: [
          { type: "text" as const, text: JSON.stringify(result, null, 2) },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Error adding document: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  };
}
