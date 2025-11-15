import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import axios from "axios";
import { config } from "dotenv";
import { privateKeyToAccount } from "viem/accounts";
import { withPaymentInterceptor } from "x402-axios";
config();
const privateKey = process.env.PRIVATE_KEY;
const baseURL = "http://localhost:3000";
if (!privateKey || !baseURL) {
  throw new Error("Missing environment variables");
}
const account = privateKeyToAccount(privateKey);
const client = withPaymentInterceptor(axios.create({ baseURL }), account);
const server = new McpServer({
  name: "x402 MCP Client Demo",
  version: "1.0.0"
});
server.tool("purchase-product", "Get the products in the store", {}, async () => {
  const res = await client.get(baseURL + "/buy/hoodie");
  return {
    content: [{ type: "text", text: "Purchased" }]
  };
});
server.tool("get-products", "Get the products in the store", {}, async () => {
  const res = await axios.get(baseURL + "/api/products");
  return {
    content: [{ type: "text", text: JSON.stringify(res.data) }]
  };
});
const transport = new StdioServerTransport();
await server.connect(transport);
