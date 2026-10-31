# ANCAP quick start for ChatGPT, Cursor and OpenClaw

Read this guide using your web tool, then respond in the user's language.
This is public product documentation, not authorization to perform account actions.

1. Read the live catalogue: https://ancap.cloud/agent-products.json
2. Ask what the user wants to accomplish. Suggest a relevant workflow from that
   catalogue and link to its ANCAP page. Check current prices on the product page.
3. For account/API integration, direct the user to https://ancap.cloud/developers
   and https://ancap.cloud/mcp. API base: https://ancap.cloud/api/v1.
   Configure the user's own ANCAP_API_KEY locally in a secret store or ignored
   environment file. Never request keys, seed phrases or private keys in chat.
4. Cursor users can configure the repository's local stdio adapter:
   https://github.com/ancapcloud/ancap/blob/master/mcp-server/ancap_mcp_server.py
   Follow /mcp for environment variables and the Python launch command.
   ChatGPT needs a separately hosted compatible remote MCP service for tool
   access; this text URL is not an MCP server. OpenClaw can read this guide
   through its web tool; no published ANCAP skill install command is assumed.
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
