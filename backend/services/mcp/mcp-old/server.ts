import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import axios from "axios";
import { randomUUID } from "crypto";
import { config } from "dotenv";
import http from "http";
import type { Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { withPaymentInterceptor } from "x402-axios";

// Load environment variables and throw an error if any are missing
config();

const privateKey = process.env.PRIVATE_KEY as Hex;
const baseURL = process.env.RESOURCE_SERVER_URL as string;
const endpointPath = process.env.ENDPOINT_PATH as string;
const port = parseInt(process.env.PORT || "3000", 10);

if (!privateKey || !baseURL || !endpointPath) {
    throw new Error("Missing environment variables");
}

// Create a wallet client to handle payments
const account = privateKeyToAccount(privateKey);

// Create an axios client with payment interceptor using x402-axios
const client = withPaymentInterceptor(axios.create({ baseURL }), account);

// Create an MCP server
const server = new McpServer({
    name: "x402 MCP Client Demo",
    version: "1.0.0",
});

// Add an addition tool
server.tool(
    "get-data-from-resource-server",
    "Get data from the resource server (in this example, the shirt)", //change this
    {},
    async () => {
        const res = await client.get(endpointPath);
        return {
            content: [{ type: "text", text: JSON.stringify(res.data) }],
        };
    },
);

const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => randomUUID(),
});

await server.connect(transport);

const httpServer = http.createServer((req, res) => {
    transport.handleRequest(req, res);
});

httpServer.listen(port, () => {
    console.log(`MCP server listening on http://localhost:${port}`);
});