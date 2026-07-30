# Generic Python client

Use the official MCP Python SDK and connect to the installed command over
stdio. The server needs no OpenAI key or model-provider credential.

```python
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    parameters = StdioServerParameters(
        command="cove-douban-mcp",
        args=["serve", "--transport", "stdio"],
    )
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([tool.name for tool in tools.tools])
            result = await session.call_tool("douban_status", {})
            print(result.structuredContent)


asyncio.run(main())
```

