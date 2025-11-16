import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import axios from "axios";
import { config } from "dotenv";
import { privateKeyToAccount } from "viem/accounts";
import { withPaymentInterceptor } from "x402-axios";
import z from "zod";
import { readFileSync } from "fs";
import { extname } from "path";
config();
const privateKey = process.env.PRIVATE_KEY;
const merchantUrl = "http://localhost:3000";
const escrowAgentUrl = "http://localhost:8000";
if (!privateKey || !merchantUrl) {
  throw new Error("Missing environment variables");
}
export const products = [
  {
    id: "shirt",
    title: "Locus Shirt",
    price: 1e-3,
    image: "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTA5L3JtMzYzLWIwOC1tb2NrdXAtam9iMTAwMy1sOGVobWoyZy5qcGc.jpg"
  },
  {
    id: "hoodie",
    title: "Locus Hoodie",
    price: 2e-3,
    image: "https://i.postimg.cc/TP8gtP2W/Screenshot-2025-11-15-at-1-36-07-PM.png"
  }
];
const account = privateKeyToAccount(privateKey);
const client = withPaymentInterceptor(axios.create({ baseURL: merchantUrl }), account);
const server = new McpServer({
  name: "Coinchase",
  version: "1.0.0"
});
function getMediaTypeFromExtension(filepath) {
  const ext = extname(filepath).toLowerCase();
  const mimeTypes = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp"
  };
  return mimeTypes[ext] || "image/jpeg";
}
function fileToBase64(filepath) {
  const fileBuffer = readFileSync(filepath);
  const base64Data = fileBuffer.toString("base64");
  const mediaType = getMediaTypeFromExtension(filepath);
  return { data: base64Data, mediaType };
}
server.tool(
  "purchase-product",
  "Purchase a product from the store by its ID",
  {
    productId: z.string().describe("The ID of the product to purchase (e.g., 'hoodie', 'shirt')")
  },
  async (params) => {
    const { productId } = params;
    const res = await client.get(`${merchantUrl}/buy/${productId}`);
    const product = products.find((p) => p.id === productId);
    return {
      content: [{ type: "text", text: `Purchased product: ${productId} for $${product?.price}` }]
    };
  }
);
server.tool("get-products", "Get the products in the store", {}, async () => {
  const res = await axios.get(merchantUrl + "/api/products");
  return {
    content: [{ type: "text", text: JSON.stringify(res.data) }]
  };
});
server.tool(
  "chargeback",
  "Create a chargeback for a given product. You can optionally include image file paths as evidence.",
  {
    productId: z.string().describe("The ID of the product to be disputed"),
    disputeDescription: z.string().describe("A description of the dispute or the reply to an existing dispute"),
    imagePaths: z.array(z.string()).optional().describe(
      "Optional array of file paths to images supporting the dispute (e.g., photos of damaged product)"
    ),
    sessionId: z.string().optional().describe("The session ID of an existing dispute if replying to an existing dispute")
  },
  async (params) => {
    const { productId, disputeDescription, sessionId, imagePaths } = params;
    const product = products.find((p) => p.id === productId);
    const productAmount = product?.price;
    let images;
    if (imagePaths && imagePaths.length > 0) {
      try {
        images = imagePaths.map((filepath) => fileToBase64(filepath));
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error reading image files: ${error instanceof Error ? error.message : String(error)}`
            }
          ]
        };
      }
    }
    const requestBody = {
      dispute_description: disputeDescription,
      transaction_id: "TXN-20241101-A7B3",
      amount: productAmount,
      address: account.address,
      sessionId
    };
    if (images) {
      requestBody.images = images;
    }
    const res = await axios.post(escrowAgentUrl + "/dispute/analyze", requestBody);
    const data = res.data;
    return {
      content: [{ type: "text", text: JSON.stringify(data) }]
    };
  }
);
const transport = new StdioServerTransport();
await server.connect(transport);
