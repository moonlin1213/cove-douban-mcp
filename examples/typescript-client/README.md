# Generic TypeScript client

Use the official MCP TypeScript SDK with an stdio transport. The exact import
paths may vary by SDK major version; consult that SDK's current documentation.

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "cove-douban-mcp",
  args: ["serve", "--transport", "stdio"],
});

const client = new Client({ name: "example-client", version: "0.1.0" });
await client.connect(transport);

const tools = await client.listTools();
console.log(tools.tools.map((tool) => tool.name));

const status = await client.callTool({
  name: "douban_status",
  arguments: {},
});
console.log(status);
```

