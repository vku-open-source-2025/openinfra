"""
OpenInfra MCP Server
Exposes Open Data API documentation via Model Context Protocol (read-only)
Compatible with GitHub Copilot, Claude Desktop, Cursor
"""

import os
import json
import httpx
from fastmcp import FastMCP

# Configuration
OPENINFRA_API_URL = os.getenv("OPENINFRA_API_URL", "http://localhost:8000")

# Create MCP server
mcp = FastMCP(
    name="OpenInfra Open Data",
    instructions="""
    You are an AI assistant for OpenInfra Open Data API.

    This MCP server provides documentation for the PUBLIC Open Data API only.
    It includes infrastructure assets (GeoJSON) and IoT sensor data (NGSI-LD format).

    NGSI-LD is the ETSI standard for context information management.

    Available tools:
    - get_opendata_endpoints - List all Open Data API endpoints
    - get_opendata_docs - Open Data API documentation
    - get_iot_docs - IoT Sensors NGSI-LD API documentation

    License: OGL (Open Government Licence)
    """,
)

# ==================== TOOLS (Open Data Documentation Only) ====================


@mcp.tool()
async def get_opendata_endpoints() -> str:
    """
    Get a list of all public Open Data API endpoints.
    Returns only the publicly accessible endpoints for open infrastructure data.
    """
    endpoints = [
        # Open Data endpoints
        {
            "method": "GET",
            "path": "/api/opendata/assets",
            "summary": "Get infrastructure assets in GeoJSON-LD format",
            "params": ["skip", "limit", "feature_type", "feature_code"],
        },
        {
            "method": "GET",
            "path": "/api/opendata/assets/{id}",
            "summary": "Get asset details by ID",
        },
        {
            "method": "GET",
            "path": "/api/opendata/feature-types",
            "summary": "Get list of asset types and counts",
        },
        {
            "method": "GET",
            "path": "/api/opendata/license",
            "summary": "Get data usage license information",
        },
        {
            "method": "GET",
            "path": "/api/opendata/stats",
            "summary": "Get dataset statistics",
        },
        # IoT public endpoints
        {
            "method": "GET",
            "path": "/api/v1/iot/sensors",
            "summary": "Get list of IoT sensors",
            "params": ["skip", "limit", "sensor_type", "status"],
        },
        {
            "method": "GET",
            "path": "/api/v1/iot/sensors/{id}",
            "summary": "Get sensor details by ID",
        },
        {
            "method": "GET",
            "path": "/api/v1/iot/sensors/{id}/data",
            "summary": "Get sensor readings",
            "params": ["from_time", "to_time", "limit"],
        },
    ]

    return json.dumps(
        {
            "title": "OpenInfra Open Data API",
            "description": "Public API for accessing infrastructure and IoT sensor data",
            "license": "OGL (Open Government Licence)",
            "base_url": "https://openinfra.space",
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
async def get_opendata_docs() -> str:
    """
    Get Open Data API documentation.
    Returns detailed documentation for accessing public infrastructure data in GeoJSON format.
    """
    return json.dumps(
        {
            "title": "OpenInfra Open Data API",
            "description": "Open Data API provides public infrastructure data in GeoJSON format following open standards",
            "license": "OGL (Open Government Licence)",
            "base_url": "https://openinfra.space/api/opendata",
            "data_format": "GeoJSON",
            "endpoints": [
                {
                    "path": "/api/opendata/assets",
                    "method": "GET",
                    "description": "Get list of infrastructure assets in GeoJSON format",
                    "params": [
                        {
                            "name": "skip",
                            "type": "int",
                            "description": "Number of records to skip (pagination)",
                        },
                        {
                            "name": "limit",
                            "type": "int",
                            "description": "Maximum records to return (default: 100)",
                        },
                        {
                            "name": "feature_type",
                            "type": "string",
                            "description": "Filter by asset type",
                        },
                        {
                            "name": "feature_code",
                            "type": "string",
                            "description": "Filter by feature code",
                        },
                    ],
                    "example": "/api/opendata/assets?limit=10&feature_type=power_station",
                },
                {
                    "path": "/api/opendata/assets/{id}",
                    "method": "GET",
                    "description": "Get detailed information about a specific asset by its ID",
                },
                {
                    "path": "/api/opendata/feature-types",
                    "method": "GET",
                    "description": "Get list of all asset types with counts",
                },
                {
                    "path": "/api/opendata/license",
                    "method": "GET",
                    "description": "Get data usage license information",
                },
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
async def get_iot_docs() -> str:
    """
    Get IoT Sensors NGSI-LD API documentation.
    Returns documentation for accessing IoT sensor data in NGSI-LD format.
    """
    return json.dumps(
        {
            "title": "OpenInfra IoT Sensors NGSI-LD API",
            "description": "Public API for accessing IoT sensor data in NGSI-LD format (ETSI standard). Regular IoT API at /api/v1/iot provides simple JSON. NGSI-LD format (semantic interoperability) at /api/v1/ld",
            "license": "OGL (Open Government Licence)",
            "base_url_standard": "https://openinfra.space/api/v1/iot",
            "base_url_ngsi_ld": "https://openinfra.space/api/v1/ld",
            "format": "NGSI-LD (ETSI CIM standard)",
            "endpoints": [
                {
                    "path": "/api/v1/iot/sensors",
                    "method": "GET",
                    "description": "Get list of IoT sensors (standard JSON format)",
                    "params": [
                        {
                            "name": "skip",
                            "type": "int",
                            "description": "Number of records to skip",
                        },
                        {
                            "name": "limit",
                            "type": "int",
                            "description": "Maximum records to return",
                        },
                        {
                            "name": "sensor_type",
                            "type": "string",
                            "description": "Filter by sensor type (water_level, temperature, etc.)",
                        },
                        {
                            "name": "status",
                            "type": "string",
                            "description": "Filter by status (online, offline)",
                        },
                    ],
                },
                {
                    "path": "/api/v1/iot/sensors/{id}",
                    "method": "GET",
                    "description": "Get detailed sensor information by ID (standard JSON)",
                },
                {
                    "path": "/api/v1/iot/sensors/{id}/data",
                    "method": "GET",
                    "description": "Get historical sensor readings (standard JSON)",
                    "params": [
                        {
                            "name": "from_time",
                            "type": "datetime",
                            "description": "Start time (ISO 8601)",
                        },
                        {
                            "name": "to_time",
                            "type": "datetime",
                            "description": "End time (ISO 8601)",
                        },
                        {
                            "name": "limit",
                            "type": "int",
                            "description": "Maximum readings to return",
                        },
                    ],
                },
                {
                    "path": "/api/v1/ld/sensors",
                    "method": "GET",
                    "description": "Get list of sensors in NGSI-LD format (semantic web compatible)",
                    "format": "NGSI-LD",
                    "params": ["skip", "limit", "asset_id", "sensor_type", "status"],
                },
                {
                    "path": "/api/v1/ld/sensors/{sensor_id}",
                    "method": "GET",
                    "description": "Get single sensor in NGSI-LD format",
                    "format": "NGSI-LD",
                },
                {
                    "path": "/api/v1/ld/sensors/{sensor_id}/observations",
                    "method": "GET",
                    "description": "Get sensor observations in NGSI-LD format",
                    "format": "NGSI-LD",
                    "params": ["from_time", "to_time", "limit"],
                },
                {
                    "path": "/api/v1/ld/observations",
                    "method": "GET",
                    "description": "Get all recent observations in NGSI-LD format",
                    "format": "NGSI-LD",
                    "params": ["hours", "asset_id", "sensor_type", "limit"],
                },
                {
                    "path": "/api/v1/ld/context",
                    "method": "GET",
                    "description": "Get NGSI-LD context document",
                    "format": "NGSI-LD",
                },
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    # Run with SSE transport for HTTP access
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
