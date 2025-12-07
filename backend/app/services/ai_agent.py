"""
AI Agent Service using LangChain and Google Gemini
Provides intelligent querying of infrastructure data and API assistance
With real API calling tools
"""
import os
import json
import asyncio
import logging
import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Define available API endpoints with their schemas
API_ENDPOINTS = {
    "opendata_assets": {
        "path": "/api/opendata/assets",
        "method": "GET",
        "description": "Lấy danh sách tất cả tài sản hạ tầng (assets) dạng JSON-LD GeoJSON",
        "params": {
            "skip": {"type": "int", "default": 0, "description": "Số bản ghi bỏ qua"},
            "limit": {"type": "int", "default": 100, "description": "Số bản ghi tối đa (1-1000)"},
            "feature_type": {"type": "str", "default": None, "description": "Lọc theo loại (vd: Trạm điện)"},
            "feature_code": {"type": "str", "default": None, "description": "Lọc theo mã (vd: tram_dien)"}
        }
    },
    "opendata_feature_types": {
        "path": "/api/opendata/feature-types",
        "method": "GET",
        "description": "Lấy danh sách các loại tài sản và số lượng của mỗi loại",
        "params": {}
    },
    "opendata_asset_detail": {
        "path": "/api/opendata/assets/{asset_id}",
        "method": "GET",
        "description": "Lấy chi tiết một tài sản theo ID",
        "params": {
            "asset_id": {"type": "str", "required": True, "description": "ID của tài sản"}
        }
    },
    "v1_assets": {
        "path": "/api/v1/assets",
        "method": "GET",
        "description": "Lấy danh sách assets từ API v1",
        "params": {
            "skip": {"type": "int", "default": 0, "description": "Số bản ghi bỏ qua"},
            "limit": {"type": "int", "default": 50, "description": "Số bản ghi tối đa"},
            "feature_type": {"type": "str", "default": None, "description": "Lọc theo loại"}
        }
    },
    "v1_sensors": {
        "path": "/api/v1/iot/sensors",
        "method": "GET",
        "description": "Lấy danh sách cảm biến IoT",
        "params": {
            "skip": {"type": "int", "default": 0, "description": "Số bản ghi bỏ qua"},
            "limit": {"type": "int", "default": 50, "description": "Số bản ghi tối đa"},
            "sensor_type": {"type": "str", "default": None, "description": "Loại cảm biến"},
            "status": {"type": "str", "default": None, "description": "Trạng thái (online/offline)"}
        }
    },
    "v1_incidents": {
        "path": "/api/v1/incidents",
        "method": "GET",
        "description": "Lấy danh sách sự cố hạ tầng",
        "params": {
            "skip": {"type": "int", "default": 0, "description": "Số bản ghi bỏ qua"},
            "limit": {"type": "int", "default": 50, "description": "Số bản ghi tối đa"},
            "status": {"type": "str", "default": None, "description": "Trạng thái (open/in_progress/resolved)"},
            "severity": {"type": "str", "default": None, "description": "Mức độ (low/medium/high/critical)"}
        }
    }
}


class AIAgentService:
    """AI Agent for infrastructure data querying and API assistance with real API calling"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, AI agent will not work")
            self.llm = None
            return
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.7,
        )
        
        self.system_prompt = """You are the OpenInfra AI Assistant - an intelligent helper for the OpenInfra smart infrastructure management system.

## Your Capabilities

1. **Call real APIs** - Use call_api tool to interact with endpoints
2. **List APIs** - Use list_available_apis to see available endpoints
3. **Answer questions** about infrastructure data (assets, sensors, incidents)
4. **Guide API usage** with JSON-LD format examples
5. **Provide code examples** when requested

## MCP Server Guidance

When users ask about MCP (Model Context Protocol), provide this information:

**Connection URL:** `https://mcp.openinfra.space/sse`

**Supported Clients:**
- Claude Desktop
- GitHub Copilot (VS Code)  
- Cursor
- Any MCP 2.0+ compatible client

**Client Configurations:**

For Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

For GitHub Copilot (VS Code `settings.json`):
```json
{
  "github.copilot.chat.mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}
```

**Available Tools via MCP:**
- `get_feature_types` - Get infrastructure types
- `get_assets` - Query assets with filters
- `get_sensors` - Query IoT sensors
- `call_api` - Call any API endpoint
- `list_endpoints` - List all endpoints

## API Test Requests

When user requests to TEST/CALL an API:
1. Use list_available_apis to see available APIs
2. Select the appropriate API based on user request
3. Use call_api with proper parameters
4. Return results with api_card block for interactive testing

## Response Format

- Describe what you did briefly
- Display important results
- Add ```api_card block with API info at the end

## Language Rule

ALWAYS respond in the SAME LANGUAGE the user uses. If they write in Vietnamese, respond in Vietnamese. If English, respond in English."""
    
    async def _call_real_api(self, endpoint_key: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Actually call a real API endpoint"""
        if endpoint_key not in API_ENDPOINTS:
            return {"error": f"API endpoint '{endpoint_key}' không tồn tại"}
        
        endpoint = API_ENDPOINTS[endpoint_key]
        path = endpoint["path"]
        
        # Handle path parameters
        if params:
            for key, value in params.items():
                if f"{{{key}}}" in path:
                    path = path.replace(f"{{{key}}}", str(value))
        
        # Build query params
        query_params = {}
        if params:
            for key, value in params.items():
                if f"{{{key}}}" not in endpoint["path"] and value is not None:
                    query_params[key] = value
        
        url = f"{API_BASE_URL}{path}"
        
        try:
            response = await self.http_client.get(url, params=query_params)
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "endpoint": endpoint_key,
                "url": str(response.url),
                "data": response.json()
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "url": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _get_tools(self):
        """Create tools for the agent"""
        
        async def list_available_apis() -> str:
            """Liệt kê tất cả API endpoints có sẵn trong hệ thống OpenInfra.
            Sử dụng tool này để biết có những API nào có thể gọi."""
            result = []
            for key, endpoint in API_ENDPOINTS.items():
                params_desc = ", ".join([
                    f"{name}: {info['description']}" 
                    for name, info in endpoint.get("params", {}).items()
                ])
                result.append(f"- **{key}**: {endpoint['method']} {endpoint['path']}\n  Mô tả: {endpoint['description']}\n  Params: {params_desc if params_desc else 'Không có'}")
            return "\n\n".join(result)
        
        async def call_api(endpoint_key: str, skip: int = 0, limit: int = 10, 
                          feature_type: str = None, feature_code: str = None,
                          sensor_type: str = None, status: str = None, 
                          severity: str = None, asset_id: str = None) -> str:
            """Gọi một API endpoint thực sự và trả về kết quả.
            
            Args:
                endpoint_key: Tên của API endpoint (vd: opendata_assets, opendata_feature_types, v1_sensors)
                skip: Số bản ghi bỏ qua (mặc định 0)
                limit: Số bản ghi tối đa trả về (mặc định 10)
                feature_type: Lọc theo loại tài sản
                feature_code: Lọc theo mã tài sản
                sensor_type: Lọc theo loại cảm biến
                status: Lọc theo trạng thái
                severity: Lọc theo mức độ nghiêm trọng
                asset_id: ID của tài sản (cho API chi tiết)
            
            Returns:
                Kết quả JSON từ API
            """
            params = {
                "skip": skip,
                "limit": limit,
                "feature_type": feature_type,
                "feature_code": feature_code,
                "sensor_type": sensor_type,
                "status": status,
                "severity": severity,
                "asset_id": asset_id
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            result = await self._call_real_api(endpoint_key, params)
            
            # Format result for LLM
            if result.get("success"):
                data = result.get("data", {})
                # Truncate data if too large
                data_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
                if len(data_str) > 3000:
                    data_str = data_str[:3000] + "\n... (đã cắt bớt)"
                
                return f"""✅ API gọi thành công!
URL: {result.get('url')}
Status: {result.get('status_code')}

Kết quả:
```json
{data_str}
```

API_CARD_DATA:
endpoint_key: {endpoint_key}
url: {result.get('url')}
params_used: {json.dumps(params, ensure_ascii=False)}"""
            else:
                return f"❌ Lỗi khi gọi API: {result.get('error')}\nURL: {result.get('url')}"
        
        # Create sync wrappers for tools
        def sync_list_apis() -> str:
            """Liệt kê tất cả API endpoints có sẵn trong hệ thống OpenInfra."""
            return asyncio.get_event_loop().run_until_complete(list_available_apis())
        
        def sync_call_api(endpoint_key: str, skip: int = 0, limit: int = 10,
                         feature_type: str = None, feature_code: str = None,
                         sensor_type: str = None, status: str = None,
                         severity: str = None, asset_id: str = None) -> str:
            """Gọi một API endpoint thực sự và trả về kết quả."""
            return asyncio.get_event_loop().run_until_complete(
                call_api(endpoint_key, skip, limit, feature_type, feature_code,
                        sensor_type, status, severity, asset_id)
            )
        
        # Store async versions for direct use
        self._async_list_apis = list_available_apis
        self._async_call_api = call_api
        
        return [
            tool(sync_list_apis),
            tool(sync_call_api)
        ]
    
    async def _query_assets(self, feature_type: str = None, limit: int = 5) -> List[Dict]:
        """Query assets from database"""
        query = {}
        if feature_type:
            query["feature_type"] = {"$regex": feature_type, "$options": "i"}
        
        cursor = self.db["assets"].find(query).limit(limit)
        assets = await cursor.to_list(length=limit)
        
        for asset in assets:
            asset["_id"] = str(asset["_id"])
            if "geometry" in asset:
                asset["geometry_type"] = asset["geometry"].get("type", "Unknown")
                del asset["geometry"]
        
        return assets
    
    async def _query_sensors(self, sensor_type: str = None, limit: int = 5) -> List[Dict]:
        """Query sensors from database"""
        query = {}
        if sensor_type:
            query["sensor_type"] = {"$regex": sensor_type, "$options": "i"}
        
        cursor = self.db["iot_sensors"].find(query).limit(limit)
        sensors = await cursor.to_list(length=limit)
        
        for sensor in sensors:
            sensor["_id"] = str(sensor["_id"])
        
        return sensors
    
    async def _query_sensor_readings(self, sensor_id: str, hours: int = 24, limit: int = 50) -> Dict:
        """Get sensor readings"""
        from_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor = self.db["sensor_readings"].find({
            "sensor_id": sensor_id,
            "timestamp": {"$gte": from_time}
        }).sort("timestamp", -1).limit(limit)
        
        readings = await cursor.to_list(length=limit)
        
        for r in readings:
            r["_id"] = str(r["_id"])
        
        if readings:
            values = [r["value"] for r in readings if "value" in r]
            if values:
                return {
                    "statistics": {
                        "count": len(values),
                        "min": round(min(values), 2),
                        "max": round(max(values), 2),
                        "avg": round(sum(values) / len(values), 2),
                        "latest": round(values[0], 2)
                    },
                    "sample_readings": readings[:5]
                }
        
        return {"readings": readings}
    
    async def _get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {
            "total_assets": await self.db["assets"].count_documents({}),
            "total_sensors": await self.db["iot_sensors"].count_documents({}),
            "online_sensors": await self.db["iot_sensors"].count_documents({"status": "online"}),
            "total_readings": await self.db["sensor_readings"].count_documents({}),
            "total_incidents": await self.db["incidents"].count_documents({}),
            "open_incidents": await self.db["incidents"].count_documents({"status": "open"}),
        }
        
        # Get asset types
        pipeline = [
            {"$group": {"_id": "$feature_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        asset_types = await self.db["assets"].aggregate(pipeline).to_list(length=5)
        stats["top_asset_types"] = {item["_id"]: item["count"] for item in asset_types}
        
        return stats
    
    def _generate_code_example(self, endpoint: str, method: str = "GET", params: Dict = None) -> str:
        """Generate API code examples"""
        base_url = "https://api.openinfra.space/api/v1"
        
        param_str = ""
        if params:
            param_str = "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        full_url = f"{base_url}{endpoint}{param_str}"
        
        python_code = f'''import requests

response = requests.get("{full_url}")
data = response.json()
print(data)'''

        curl_code = f'''curl -X {method} "{full_url}" -H "Accept: application/json"'''

        js_code = f'''const response = await fetch("{full_url}");
const data = await response.json();
console.log(data);'''

        return f"**Python:**\n```python\n{python_code}\n```\n\n**cURL:**\n```bash\n{curl_code}\n```\n\n**JavaScript:**\n```javascript\n{js_code}\n```"
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze user query and fetch relevant data"""
        query_lower = query.lower()
        context_data = {}
        
        # Check for API testing requests - let the agent handle this
        if any(word in query_lower for word in ["test api", "thử api", "gọi api", "call api", "feature-type", "feature type"]):
            context_data["is_api_test"] = True
            context_data["available_apis"] = await self._async_list_apis()
            return context_data
        
        # Check for statistics/overview requests
        if any(word in query_lower for word in ["thống kê", "tổng quan", "overview", "statistics", "bao nhiêu", "số lượng"]):
            context_data["stats"] = await self._get_stats()
        
        # Check for asset queries
        if any(word in query_lower for word in ["asset", "tài sản", "hạ tầng", "cống", "trạm", "đường"]):
            feature_type = None
            if "cống" in query_lower or "thoát nước" in query_lower:
                feature_type = "cong_thoat_nuoc"
            elif "trạm biến áp" in query_lower or "điện" in query_lower:
                feature_type = "tram_bien_ap"
            context_data["assets"] = await self._query_assets(feature_type, limit=5)
        
        # Check for sensor queries
        if any(word in query_lower for word in ["sensor", "cảm biến", "iot", "water level", "mực nước", "nhiệt độ"]):
            sensor_type = None
            if "water" in query_lower or "nước" in query_lower:
                sensor_type = "water_level"
            elif "nhiệt" in query_lower or "temp" in query_lower:
                sensor_type = "temperature"
            context_data["sensors"] = await self._query_sensors(sensor_type, limit=5)
        
        # Check for API documentation requests
        if any(word in query_lower for word in ["api", "endpoint", "code", "example", "cách dùng", "hướng dẫn"]):
            context_data["is_api_query"] = True
            
            # Generate relevant examples
            if "asset" in query_lower or "tài sản" in query_lower:
                context_data["api_example"] = self._generate_code_example("/assets", "GET", {"limit": "10"})
            elif "sensor" in query_lower or "cảm biến" in query_lower:
                context_data["api_example"] = self._generate_code_example("/iot/sensors", "GET")
            elif "data" in query_lower or "readings" in query_lower or "dữ liệu" in query_lower:
                context_data["api_example"] = self._generate_code_example(
                    "/iot/sensors/{sensor_id}/data", 
                    "GET", 
                    {"from_time": "2025-12-01T00:00:00Z", "to_time": "2025-12-07T23:59:59Z", "limit": "100"}
                )
            else:
                context_data["api_example"] = self._generate_code_example("/assets", "GET")
        
        return context_data
    
    async def stream_response(
        self, 
        query: str, 
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from the agent"""
        
        if not self.llm:
            yield {"type": "error", "content": "AI agent not configured. Please set GEMINI_API_KEY."}
            yield {"type": "done"}
            return
        
        try:
            # Check if this is an API test request
            query_lower = query.lower()
            is_api_test = any(word in query_lower for word in ["test api", "thử api", "gọi api", "call api", "feature-type", "feature type"])
            
            if is_api_test:
                # Use tool calling for API tests
                yield {"type": "tool_start", "tool": "analyzing_api_request", "input": query}
                
                # Determine which API to call based on query
                endpoint_key = None
                params = {}
                
                if "feature-type" in query_lower or "feature type" in query_lower or "loại" in query_lower:
                    endpoint_key = "opendata_feature_types"
                elif "sensor" in query_lower or "cảm biến" in query_lower:
                    endpoint_key = "v1_sensors"
                    params = {"limit": 10}
                elif "incident" in query_lower or "sự cố" in query_lower:
                    endpoint_key = "v1_incidents"
                    params = {"limit": 10}
                else:
                    endpoint_key = "opendata_assets"
                    params = {"limit": 5}
                
                yield {"type": "tool_end", "output": f"Đang gọi API: {endpoint_key}"}
                
                # Call the API
                yield {"type": "tool_start", "tool": "call_api", "input": endpoint_key}
                api_result = await self._call_real_api(endpoint_key, params)
                yield {"type": "tool_end", "output": f"API response received"}
                
                # Format response
                if api_result.get("success"):
                    data = api_result.get("data", {})
                    endpoint_info = API_ENDPOINTS.get(endpoint_key, {})
                    
                    # Create summary
                    summary = f"✅ **Đã gọi API thành công!**\n\n"
                    summary += f"**Endpoint:** `{endpoint_info.get('path', '')}`\n"
                    summary += f"**URL:** `{api_result.get('url')}`\n\n"
                    
                    # Analyze data
                    if isinstance(data, dict):
                        if "features" in data:
                            summary += f"📊 **Kết quả:** {len(data['features'])} features\n"
                            if "totalCount" in data:
                                summary += f"📈 **Tổng số:** {data['totalCount']}\n"
                        elif "itemListElement" in data:
                            items = data["itemListElement"]
                            summary += f"📊 **Số loại tài sản:** {len(items)}\n\n"
                            summary += "| Loại | Mã | Số lượng |\n|------|-----|----------|\n"
                            for item in items[:10]:
                                summary += f"| {item.get('feature_type', 'N/A')} | {item.get('feature_code', 'N/A')} | {item.get('count', 0)} |\n"
                    
                    # Add API card data
                    summary += f"\n\n---\n\n💡 **Bạn có thể chỉnh sửa params và gọi lại API:**\n\n"
                    summary += f"```api_card\n"
                    summary += json.dumps({
                        "endpoint": endpoint_info.get("path", ""),
                        "method": endpoint_info.get("method", "GET"),
                        "description": endpoint_info.get("description", ""),
                        "params": endpoint_info.get("params", {}),
                        "last_result": {
                            "url": api_result.get("url"),
                            "status": api_result.get("status_code"),
                            "data_preview": str(data)[:500] + "..." if len(str(data)) > 500 else data
                        }
                    }, ensure_ascii=False, indent=2)
                    summary += "\n```"
                    
                    yield {"type": "token", "content": summary}
                    yield {"type": "final", "content": summary}
                else:
                    error_msg = f"❌ **Lỗi khi gọi API:**\n\n{api_result.get('error')}\n\nURL: {api_result.get('url')}"
                    yield {"type": "token", "content": error_msg}
                    yield {"type": "final", "content": error_msg}
                
                yield {"type": "done"}
                return
            
            # Regular query handling
            yield {"type": "tool_start", "tool": "analyze_query", "input": query}
            context_data = await self._analyze_query(query)
            yield {"type": "tool_end", "output": f"Found {len(context_data)} relevant data sources"}
            
            # Build context message
            context_parts = []
            
            if "stats" in context_data:
                context_parts.append(f"📊 Thống kê hệ thống:\n{json.dumps(context_data['stats'], indent=2, ensure_ascii=False)}")
            
            if "assets" in context_data:
                context_parts.append(f"🏗️ Tài sản mẫu:\n{json.dumps(context_data['assets'], indent=2, ensure_ascii=False, default=str)}")
            
            if "sensors" in context_data:
                context_parts.append(f"📡 Cảm biến mẫu:\n{json.dumps(context_data['sensors'], indent=2, ensure_ascii=False, default=str)}")
            
            if "api_example" in context_data:
                context_parts.append(f"💻 Code example:\n{context_data['api_example']}")
            
            if "available_apis" in context_data:
                context_parts.append(f"🔌 API có sẵn:\n{context_data['available_apis']}")
            
            context_message = "\n\n".join(context_parts) if context_parts else "Không tìm thấy dữ liệu liên quan."
            
            # Build messages
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add chat history
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add current query with context
            user_message = f"""Câu hỏi: {query}

Dữ liệu context từ database:
{context_message}

Hãy trả lời dựa trên dữ liệu trên. Nếu người dùng hỏi về API, hãy cung cấp code examples."""
            
            messages.append(HumanMessage(content=user_message))
            
            # Stream response
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield {"type": "token", "content": chunk.content}
            
            yield {"type": "final", "content": full_response}
            yield {"type": "done"}
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            yield {"type": "error", "content": f"Lỗi: {str(e)}"}
            yield {"type": "done"}
    
    async def query(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Non-streaming query"""
        
        if not self.llm:
            return "AI agent not configured. Please set GEMINI_API_KEY."
        
        try:
            # Collect all chunks
            full_response = ""
            async for chunk in self.stream_response(query, chat_history):
                if chunk["type"] == "token":
                    full_response += chunk["content"]
                elif chunk["type"] == "final":
                    full_response = chunk["content"]
                elif chunk["type"] == "error":
                    return f"Error: {chunk['content']}"
            
            return full_response
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return f"Error: {str(e)}"
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
