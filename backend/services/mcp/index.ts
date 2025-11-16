/**
 * Need:
 * - MCP server to be able to verify token (SSE should be able to do this)
 * - Need client to be able to send header
 * - Each client application would need to implement a wallet type
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import axios from "axios";
import { config } from "dotenv";
import { Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { withPaymentInterceptor } from "x402-axios";
import z from "zod";

config();

const privateKey = process.env.PRIVATE_KEY as Hex;
const merchantUrl = "http://localhost:3000";
const escrowAgentUrl = "http://localhost:8000";

if (!privateKey || !merchantUrl) {
  throw new Error("Missing environment variables");
}

export const products = [
  {
    id: "shirt",
    title: "Locus Shirt",
    price: 0.001,
    image:
      "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTA5L3JtMzYzLWIwOC1tb2NrdXAtam9iMTAwMy1sOGVobWoyZy5qcGc.jpg",
  },
  {
    id: "hoodie",
    title: "Locus Hoodie",
    price: 0.002,
    image: "https://i.postimg.cc/TP8gtP2W/Screenshot-2025-11-15-at-1-36-07-PM.png",
  },
];

const account = privateKeyToAccount(privateKey);

const client = withPaymentInterceptor(axios.create({ baseURL: merchantUrl }), account);

const server = new McpServer({
  name: "Coinchase",
  version: "1.0.0",
});

server.tool(
  "purchase-product",
  "Purchase a product from the store by its ID",
  {
    productId: z.string().describe("The ID of the product to purchase (e.g., 'hoodie', 'shirt')"),
  },
  async params => {
    const { productId } = params;

    const res = await client.get(`${merchantUrl}/buy/${productId}`);

    const productsCall = await axios.get(merchantUrl + "/api/products");
    const products = productsCall.data.products;
    const product = products.find(p => p.id === productId);

    return {
      content: [{ type: "text", text: `Purchased product: ${productId} for $${product?.price}` }],
    };
  },
);

server.tool("get-products", "Get the products in the store", {}, async () => {
  const res = await axios.get(merchantUrl + "/api/products");

  return {
    content: [{ type: "text", text: JSON.stringify(res.data) }],
  };
});

server.tool(
  "chargeback",
  "Create a chargeback for a given product",
  {
    productId: z.string().describe("The ID of the product to be disputed"),
    disputeDescription: z
      .string()
      .describe("A description of the dispute or the reply to an existing dispute"),
    sessionId: z
      .string()
      .optional()
      .describe("The session ID of an existing dispute if replying to an existing dispute"),
  },
  async params => {
    const { productId, disputeDescription, sessionId } = params;

    const productsCall = await axios.get(merchantUrl + "/api/products");
    const products = productsCall.data.products;
    const product = products.find(p => p.id === productId);
    const productAmount = product?.price;

    const res = await axios.post(escrowAgentUrl + "/dispute/analyze", {
      dispute_description: disputeDescription,
      transaction_id: "TXN-20241101-A7B3",
      amount: productAmount,
      address: account.address,
      sessionId,
    });

    const data = res.data;

    return {
      content: [{ type: "text", text: JSON.stringify(data) }],
    };
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
