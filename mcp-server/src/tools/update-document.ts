import { z } from "zod";
import type { DocumentApiClient } from "../client.js";

export const updateDocumentSchema = {
  document_id: z.string().describe("The UUID of the document to update"),
  content: z.string().describe("The new text content for the document"),
  filename: z
    .string()
    .optional()
    .describe("Optional new filename for the document"),
};

export function createUpdateDocumentHandler(client: DocumentApiClient) {
  return async (args: {
    document_id: string;
    content: string;
    filename?: string;
  }) => {
    try {
      const result = await client.updateDocument(
        args.document_id,
        args.content,
        args.filename,
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
            text: `Error updating document: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  };
}
