"""
OpenInfra MCP Server
Exposes API documentation and tools via Model Context Protocol
"""
import os
import json
import httpx
from fastmcp import FastMCP

# Configuration
OPENINFRA_API_URL = os.getenv("OPENINFRA_API_URL", "http://localhost:8000")

# Create MCP server
mcp = FastMCP(
    name="OpenInfra API",
    instructions="""
    Bạn là trợ lý AI cho hệ thống OpenInfra - Quản lý hạ tầng GIS thông minh.
    
    Sử dụng các resources để xem API documentation:
    - openapi://spec - OpenAPI specification đầy đủ
    - docs://endpoints - Danh sách tất cả endpoints
    
    Sử dụng các tools để tương tác với API:
    - call_api - Gọi API endpoint
    - list_endpoints - Liệt kê endpoints
    """
)

# HTTP client for API calls
http_client = httpx.AsyncClient(base_url=OPENINFRA_API_URL, timeout=30.0)


# ==================== RESOURCES ====================

@mcp.resource("openapi://spec")
async def get_openapi_spec() -> str:
    """Get the full OpenAPI specification for OpenInfra API"""
    try:
        response = await http_client.get("/openapi.json")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("docs://endpoints")
async def get_endpoints_list() -> str:
    """Get a list of all available API endpoints with descriptions"""
    try:
        response = await http_client.get("/openapi.json")
        response.raise_for_status()
        spec = response.json()
        
        endpoints = []
        paths = spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "tags": details.get("tags", [])
                    })
        
        return json.dumps({
            "total_endpoints": len(endpoints),
            "endpoints": endpoints
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("docs://opendata")
async def get_opendata_docs() -> str:
    """Get Open Data API documentation (JSON-LD format)"""
    return json.dumps({
        "title": "OpenInfra Open Data API",
        "description": "Open Data API cung cấp dữ liệu hạ tầng công cộng dạng JSON-LD",
        "license": "ODC-BY (Open Data Commons Attribution License)",
        "base_url": f"{OPENINFRA_API_URL}/api/opendata",
        "endpoints": [
            {
                "path": "/api/opendata/assets",
                "method": "GET",
                "description": "Lấy danh sách tài sản hạ tầng dạng GeoJSON-LD",
                "params": ["skip", "limit", "feature_type", "feature_code"]
            },
            {
                "path": "/api/opendata/assets/{id}",
                "method": "GET", 
                "description": "Lấy chi tiết một tài sản theo ID"
            },
            {
                "path": "/api/opendata/feature-types",
                "method": "GET",
                "description": "Lấy danh sách các loại tài sản và số lượng"
            },
            {
                "path": "/api/opendata/license",
                "method": "GET",
                "description": "Thông tin giấy phép sử dụng dữ liệu"
            }
        ]
    }, indent=2, ensure_ascii=False)


@mcp.resource("docs://iot")
async def get_iot_docs() -> str:
    """Get IoT Sensors API documentation"""
    return json.dumps({
        "title": "OpenInfra IoT Sensors API",
        "description": "API quản lý cảm biến IoT và dữ liệu sensor",
        "base_url": f"{OPENINFRA_API_URL}/api/v1/iot",
        "endpoints": [
            {
                "path": "/api/v1/iot/sensors",
                "method": "GET",
                "description": "Lấy danh sách cảm biến",
                "params": ["skip", "limit", "sensor_type", "status"]
            },
            {
                "path": "/api/v1/iot/sensors/{id}",
                "method": "GET",
                "description": "Lấy chi tiết cảm biến"
            },
            {
                "path": "/api/v1/iot/sensors/{id}/data",
                "method": "GET",
                "description": "Lấy dữ liệu đo của cảm biến",
                "params": ["from_time", "to_time", "limit"]
            }
        ]
    }, indent=2, ensure_ascii=False)


# ==================== TOOLS ====================

@mcp.tool()
async def list_endpoints(tag: str = None) -> str:
    """
    Liệt kê tất cả API endpoints có sẵn
    
    Args:
        tag: Lọc theo tag (optional), ví dụ: "Assets", "IoT", "Open Data"
    
    Returns:
        Danh sách endpoints với method, path và mô tả
    """
    try:
        response = await http_client.get("/openapi.json")
        response.raise_for_status()
        spec = response.json()
        
        endpoints = []
        paths = spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    tags = details.get("tags", [])
                    if tag and tag.lower() not in [t.lower() for t in tags]:
                        continue
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "tags": tags
                    })
        
        return json.dumps({
            "filter": tag,
            "count": len(endpoints),
            "endpoints": endpoints
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def call_api(
    method: str,
    path: str,
    params: dict = None
) -> str:
    """
    Gọi API endpoint của OpenInfra
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: Đường dẫn API, ví dụ: /api/opendata/assets
        params: Query parameters hoặc request body (optional)
    
    Returns:
        Kết quả từ API dạng JSON
    """
    try:
        method = method.upper()
        
        if method == "GET":
            response = await http_client.get(path, params=params)
        elif method == "POST":
            response = await http_client.post(path, json=params)
        elif method == "PUT":
            response = await http_client.put(path, json=params)
        elif method == "DELETE":
            response = await http_client.delete(path, params=params)
        else:
            return json.dumps({"error": f"Unsupported method: {method}"})
        
        response.raise_for_status()
        
        # Truncate large responses
        data = response.json()
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        if len(data_str) > 5000:
            data_str = data_str[:5000] + "\n... (truncated)"
        
        return json.dumps({
            "success": True,
            "status_code": response.status_code,
            "url": str(response.url),
            "data": data
        }, ensure_ascii=False, indent=2)
        
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "success": False,
            "status_code": e.response.status_code,
            "error": e.response.text
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
async def get_feature_types() -> str:
    """
    Lấy danh sách các loại tài sản hạ tầng và số lượng
    
    Returns:
        Danh sách feature types với count
    """
    try:
        response = await http_client.get("/api/opendata/feature-types")
        response.raise_for_status()
        data = response.json()
        
        items = data.get("itemListElement", [])
        result = []
        for item in items:
            result.append({
                "type": item.get("feature_type", ""),
                "code": item.get("feature_code", ""),
                "count": item.get("count", 0)
            })
        
        return json.dumps({
            "total_types": len(result),
            "types": result
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_assets(
    limit: int = 10,
    feature_type: str = None,
    skip: int = 0
) -> str:
    """
    Lấy danh sách tài sản hạ tầng
    
    Args:
        limit: Số lượng tối đa (mặc định 10)
        feature_type: Lọc theo loại tài sản (optional)
        skip: Số bản ghi bỏ qua (mặc định 0)
    
    Returns:
        Danh sách assets dạng GeoJSON
    """
    try:
        params = {"limit": limit, "skip": skip}
        if feature_type:
            params["feature_type"] = feature_type
            
        response = await http_client.get("/api/opendata/assets", params=params)
        response.raise_for_status()
        data = response.json()
        
        features = data.get("features", [])
        
        return json.dumps({
            "total": data.get("totalCount", len(features)),
            "returned": len(features),
            "features": features
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_sensors(
    limit: int = 10,
    sensor_type: str = None,
    status: str = None
) -> str:
    """
    Lấy danh sách cảm biến IoT
    
    Args:
        limit: Số lượng tối đa (mặc định 10)
        sensor_type: Loại cảm biến (optional), ví dụ: water_level, temperature
        status: Trạng thái (optional): online, offline
    
    Returns:
        Danh sách sensors
    """
    try:
        params = {"limit": limit}
        if sensor_type:
            params["sensor_type"] = sensor_type
        if status:
            params["status"] = status
            
        response = await http_client.get("/api/v1/iot/sensors", params=params)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "count": len(data) if isinstance(data, list) else data.get("count", 0),
            "sensors": data if isinstance(data, list) else data.get("items", [])
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # Run with SSE transport for HTTP access
    # Bind to 0.0.0.0 to allow external access in Docker
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
