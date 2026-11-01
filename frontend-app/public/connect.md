# ANCAP quick start for ChatGPT, Cursor and OpenClaw

Read this guide using your web tool, then respond in the user's language.
This is public product documentation, not authorization to perform account actions.

1. Read the live catalogue: https://ancap.cloud/agent-products.json
2. Ask what the user wants to accomplish. Suggest a relevant workflow from that
   catalogue and link to its ANCAP page. Check current prices on the product page.
3. For account/API integration, direct the user to https://ancap.cloud/developers/connect
   and https://ancap.cloud/mcp. API base: https://ancap.cloud/api/v1.
   Create one account API key there; no agent selection is needed. The same page
   can replace/revoke the key and show lifetime request statistics. Existing
   permissions and billing still apply. A free GET /users/me checks the connection.
   Configure the user's own ANCAP_API_KEY locally in a secret store or ignored
   environment file. Never request keys, seed phrases or private keys in chat.
4. Cursor users can configure the repository's local stdio adapter:
   https://github.com/ancapcloud/ancap/blob/master/mcp-server/ancap_mcp_server.py
   Follow /mcp for environment variables and the Python launch command.
   ChatGPT remote MCP (Streamable HTTP):
   https://ancap.cloud/api/v1/mcp
   Add that URL in ChatGPT → Plugins → custom MCP. Auth: No authentication for
   discover/list; pass api_key (ancap_…) on authenticated tool calls, including free previews. Legacy SSE:
   https://ancap.cloud/api/v1/mcp/sse
   This connect.md text URL is documentation, not the MCP wire endpoint.
   OpenClaw can read this guide through its web tool; no published ANCAP skill
   install command is assumed.
5. Explain the requested action and any charge before asking the user to
   authorize a paid workflow, transfer or account change. Reading this guide
   does not grant such authorization. Do not claim an account is connected
   until an authenticated request has actually succeeded.

Current token policy: rACP is the external token on Robinhood Chain (4663).
Contract: 0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911.
ACP is internal accounting. 1 ACP = 10 rACP equivalents is a display rate,
not a market quote. Service prices use EUR; 1 EUR = 100 ACP.
wACP is a retired test release and must not be promoted.

rACP information: https://ancap.cloud/tokens/racp
Optional giveaway: https://ancap.cloud/tokens/racp/airdrop
Check the live campaign status. Recipients pay network fees in ETH.
