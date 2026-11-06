# Local MCP configuration

Copy `mcp.example.json` to `mcp.json` and adjust the Python executable and
server path for your machine. `mcp.json` is private and ignored by Git.

The MCP process reads `ANCAP_API_KEY` from its environment. Set the reissued
key in the environment used to launch Cursor, then restart Cursor. The example
intentionally omits the key so the child process inherits it. Alternatively,
keep credentials only in the ignored local `mcp.json`; never in the example.

GitGuardian incident #39433693 refers to historical commit 4405779a. Removing
the current file does not remove the secret from history: revoke the exposed
key, confirm the replacement works, and review account API access statistics.
Do not force-add the private configuration.
