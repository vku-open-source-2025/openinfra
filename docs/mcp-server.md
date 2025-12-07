# OpenInfra MCP Server Documentation

## Overview

OpenInfra provides a Model Context Protocol (MCP) server that allows AI assistants to access infrastructure data directly. This enables seamless integration with AI tools like Claude Desktop, Cursor, GitHub Copilot, and other MCP-compatible clients.

## Connection Details

| Property | Value |
|----------|-------|
| **Server URL** | `https://mcp.openinfra.space/sse` |
| **Transport** | SSE (Server-Sent Events) |
| **Protocol** | MCP 2.0+ |

## Available Resources

Resources provide read-only access to data:

| URI | Description |
|-----|-------------|
| `openapi://spec` | Full OpenAPI specification in JSON format |
| `docs://endpoints` | List of all available API endpoints |
| `docs://opendata` | Open Data API documentation |
| `docs://iot` | IoT Sensors API documentation |

## Available Tools

Tools allow you to interact with the API:

| Tool | Description | Parameters |
|------|-------------|------------|
| `call_api` | Call any OpenInfra API endpoint | `method`, `path`, `params` |
| `list_endpoints` | List all API endpoints | `tag` (optional) |
| `get_feature_types` | Get infrastructure types and counts | - |
| `get_assets` | Query infrastructure assets | `limit`, `feature_type`, `skip` |
| `get_sensors` | Query IoT sensors | `limit`, `sensor_type`, `status` |

## Client Configurations

### Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

**Configuration file locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### GitHub Copilot

Add to your VS Code settings (`settings.json`):

```json
{
  "github.copilot.chat.mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

Or add to your workspace `.vscode/settings.json` for project-specific configuration.

### Cursor

Add to Cursor's MCP configuration:

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

Once connected, you can ask your AI assistant:

1. **List infrastructure types:**
   > "What types of infrastructure are available in OpenInfra?"

2. **Query assets:**
   > "Show me 10 power stations from OpenInfra"

3. **Get sensor data:**
   > "List all online IoT sensors"

4. **Call specific API:**
   > "Call the OpenInfra API to get feature types"

## Troubleshooting

### Connection Issues

1. Verify the server is accessible:
   ```bash
   curl -N https://mcp.openinfra.space/sse
   ```

2. Check that your client supports SSE transport

3. Ensure no firewall is blocking the connection

### No Data Returned

- Verify the API endpoint exists by checking the OpenAPI spec
- Check parameter formats (e.g., dates should be ISO 8601)

## License

Data accessed through the MCP server is provided under the **ODC-BY (Open Data Commons Attribution)** license.
