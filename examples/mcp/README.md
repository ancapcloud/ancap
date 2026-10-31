# ANCAP MCP examples

## ChatGPT (hosted remote)

Server URL (Streamable HTTP):

```text
https://ancap.cloud/api/v1/mcp
```

In ChatGPT → Plugins → Add custom MCP server, paste the URL. Use **No authentication**
for discovery. Pass your `ancap_…` key as tool argument `api_key` on paid tools.
Create a key at https://ancap.cloud/developers/connect.

Legacy SSE: `https://ancap.cloud/api/v1/mcp/sse`

Docs: https://ancap.cloud/mcp

## Cursor / Claude Desktop (local stdio)

```bash
export ANCAP_API_KEY=ancap_your_key_here
export ANCAP_API_BASE=https://ancap.cloud/api/v1
python ../../mcp-server/ancap_mcp_server.py
```

Configure in Cursor / Claude Desktop MCP settings as a stdio server pointing to the script above.

Tools: token snapshot, risk report, payment links, invoices, claim codes, payment scanner parse, workflow runs.
