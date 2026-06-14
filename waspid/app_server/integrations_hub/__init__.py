# Waspid AI OS
"""Integration Hub: connections, tool registry, and tool execution.

One interface for every external system. Each provider in the registry
declares its credential kind and its tools, and each tool declares how
it executes:

- ``server``  — Waspid executes the REST call directly (implemented in
  ``tool_executors.py``), used by workflow actions and the execute API.
- ``sandbox`` — the credential is exported to the agent's sandbox
  (Settings → Secrets) and the agent calls the provider's API itself.
- ``mcp``     — connect the provider's MCP server under Settings → MCP.
"""
