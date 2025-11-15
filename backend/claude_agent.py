import asyncio
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, tool, create_sdk_mcp_server

@tool("add","add two numbers",{"a":float, "b":float})
async def add(args):
    
    return {
        "content":[{
            "type":"text",
            "text":f"Sum: {args['a']+args['b']}"
        }]
    }

calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add]
)

options = ClaudeAgentOptions(
    mcp_servers={'calc':calculator},
    allowed_tools=['mcp__calc__add']
)


async def main():
    async with ClaudeSDKClient(options) as client:
        await client.query("whats 5583+3821?")
        async for message in client.receive_response():
            print(message)


asyncio.run(main())