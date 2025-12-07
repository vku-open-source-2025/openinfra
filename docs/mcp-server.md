# OpenInfra MCP Server Documentation

## Overview

OpenInfra provides a Model Context Protocol (MCP) server that exposes **Open Data API documentation** to AI assistants. This is a **read-only** server that provides information about publicly accessible endpoints only.

> **Note:** This server only exposes public Open Data endpoints. Internal/authenticated APIs are not accessible.

## Connection Details

| Property | Value |
|----------|-------|
| **Server URL** | `https://mcp.openinfra.space/sse` |
| **Transport** | SSE (Server-Sent Events) |
| **Protocol** | MCP 2.0+ |

## Available Tools

| Tool | Description |
|------|-------------|
| `get_opendata_endpoints` | List all public Open Data API endpoints |
| `get_opendata_docs` | Detailed Open Data API documentation |
| `get_iot_docs` | IoT Sensors API documentation |

## Client Configurations

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

### GitHub Copilot

Add to VS Code `settings.json`:

```json
{
  "github.copilot.chat.mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

### Cursor

Add to MCP configuration:

```json
{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

## Usage Examples

Once connected, ask your AI assistant:

> "What Open Data endpoints are available?"

> "How do I query infrastructure assets from OpenInfra?"

> "Show me the IoT sensor API documentation"

## License

Data accessed through the Open Data API is provided under the **ODC-BY (Open Data Commons Attribution)** license.
