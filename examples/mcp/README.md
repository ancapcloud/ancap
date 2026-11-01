# ANCAP MCP examples

## ChatGPT (hosted remote)

Server URL (Streamable HTTP):

```text
https://ancap.cloud/api/v1/mcp
```

In ChatGPT → Plugins → Add custom MCP server, paste the URL. Use **No authentication**
for discovery. Pass your `ancap_…` key as tool argument `api_key` on authenticated tools, including free previews. Only payment-link status is public.
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

The stdio script forwards JSON-RPC to the same hosted MCP endpoint; it requires
network access and has no separate function catalogue. Deploy backend changes
before using the updated adapter against production.

Smart Pay accepts `raw_text` (required), with optional `source`: paste, qr, ocr.
The remote endpoint also accepts historical `raw` calls for compatibility.
Invoice arguments include required `line_items` (description, unit_amount,
optional quantity and currency); schemas are generated from backend models.

Legacy SSE requires a single API worker or sticky routing: its bounded session
queues are process-local. Unknown/restarted sessions return 404; reconnect to
`/mcp/sse` and initialize again. Prefer stateless Streamable HTTP in production.

Verification and November release gates: `docs/RELEASE_NOVEMBER_2026.md`.
