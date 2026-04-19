"""
AI Agent Service using GitHub Copilot (OpenAI-compatible) or Google Gemini
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

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.infrastructure.external.ag05_context_service import AG05ContextService

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


class CopilotStreamLLM:
    """LLM wrapper for GitHub Copilot API (OpenAI-compatible) with async streaming."""

    COPILOT_API_URL = "https://api.githubcopilot.com"
    TOKEN_FILE = "/root/.config/github-copilot/token"
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, model: str = DEFAULT_MODEL, system_instruction: str = None):
        self.model = model
        self.system_instruction = system_instruction
        self._token: Optional[str] = None

    def _get_token(self) -> Optional[str]:
        """Read GitHub Copilot token from the mounted auth file."""
        if self._token:
            return self._token
        token = os.getenv("GITHUB_COPILOT_API_KEY", "").strip()
        if not token:
            try:
                path = os.getenv("COPILOT_TOKEN_FILE", self.TOKEN_FILE)
                with open(path, "r") as f:
                    token = f.read().strip()
            except Exception:
                pass
        self._token = token or None
        return self._token

    def _make_client(self):
        from openai import AsyncOpenAI
        token = self._get_token()
        if not token:
            return None, None
        client = AsyncOpenAI(
            api_key=token,
            base_url=self.COPILOT_API_URL,
            default_headers={
                "Editor-Version": "vscode/1.85.0",
                "Copilot-Integration-Id": "vscode-chat",
            },
        )
        return client, token

    def _build_oai_messages(self, messages: List[Any]) -> List[Dict]:
        oai_messages = []
        # Collect system content: base instruction + any SystemMessages (e.g. AG05 snippets)
        system_parts = []
        if self.system_instruction:
            system_parts.append(self.system_instruction)
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_parts.append(msg.content)
        if system_parts:
            oai_messages.append({"role": "system", "content": "\n\n---\n\n".join(system_parts)})
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue
            elif isinstance(msg, HumanMessage):
                oai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                oai_messages.append({"role": "assistant", "content": msg.content})
        return oai_messages

    async def astream(self, messages: List[Any]):
        client, token = self._make_client()
        if not client:
            yield AIMessage(content="[Copilot token not found]")
            return

        oai_messages = self._build_oai_messages(messages)

        stream = await client.chat.completions.create(
            model=self.model,
            messages=oai_messages,
            stream=True,
            temperature=0.7,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield AIMessage(content=delta)

    async def astream_with_tools(self, messages: List[Any], tools: List[Dict], tool_executor, on_tool_call=None):
        """Run agentic tool-calling loop then stream final response.

        Args:
            messages: LangChain message list
            tools: OpenAI tool schema list
            tool_executor: async callable(name, args_dict) -> str
            on_tool_call: optional async callable(name, args) called before execution (for progress events)
        """
        client, token = self._make_client()
        if not client:
            yield AIMessage(content="[Copilot token not found]")
            return

        oai_messages = self._build_oai_messages(messages)

        # Agentic loop (max 8 rounds to avoid runaway)
        for _round in range(8):
            response = await client.chat.completions.create(
                model=self.model,
                messages=oai_messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
            )
            choice = response.choices[0]
            msg = choice.message

            # No tool calls — we have the final non-streaming answer; re-request as stream
            if not msg.tool_calls:
                break

            # Append assistant message (with tool_calls) to history
            oai_messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in msg.tool_calls
                ],
            })

            # Execute each tool call
            for tc in msg.tool_calls:
                func_name = tc.function.name
                try:
                    func_args = json.loads(tc.function.arguments)
                except Exception:
                    func_args = {}

                if on_tool_call:
                    await on_tool_call(func_name, func_args)

                try:
                    result = await tool_executor(func_name, func_args)
                except Exception as exc:
                    result = f"Error executing {func_name}: {exc}"

                oai_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })

        # Stream final response
        stream = await client.chat.completions.create(
            model=self.model,
            messages=oai_messages,
            stream=True,
            temperature=0.7,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield AIMessage(content=delta)


class GeminiStreamLLM:
    """LLM wrapper for regular generateContent API with streaming - works with all models."""
    def __init__(self, api_key: str, model: str, system_instruction: str = None):
        from langchain_google_genai import ChatGoogleGenerativeAI
        self.model = model
        self.system_instruction = system_instruction
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7,
            streaming=True,
        )
        self.system_message = SystemMessage(content=system_instruction) if system_instruction else None

    async def astream(self, messages: List[Any]):
        langchain_messages = []
        if self.system_message:
            langchain_messages.append(self.system_message)
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue
            elif isinstance(msg, (HumanMessage, AIMessage)):
                langchain_messages.append(msg)
            else:
                langchain_messages.append(HumanMessage(content=str(msg.content)))
        async for chunk in self.llm.astream(langchain_messages):
            yield chunk


class AIAgentService:
    """AI Agent for infrastructure data querying and API assistance with real API calling"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        ag05_context_service: Optional[AG05ContextService] = None,
    ):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.ag05_context_service = ag05_context_service or AG05ContextService()

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

        # Provider selection: prefer Gemini if key set, else fall back to Copilot
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            model = settings.GEMINI_CHAT_MODEL_STABLE
            self.llm = GeminiStreamLLM(
                api_key=gemini_key,
                model=model,
                system_instruction=self.system_prompt,
            )
            logger.info(f"AI Agent using Gemini model: {model}")
        else:
            # Fall back to GitHub Copilot (OpenAI-compatible)
            copilot_llm = CopilotStreamLLM(
                model="gpt-4o",
                system_instruction=self.system_prompt,
            )
            token = copilot_llm._get_token()
            if token:
                self.llm = copilot_llm
                logger.info("AI Agent using GitHub Copilot (gpt-4o)")
            else:
                logger.warning("No AI provider configured (GEMINI_API_KEY or Copilot token missing)")
                self.llm = None


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

    async def _retrieve_ag05_snippets(
        self,
        query: str,
        max_snippets: int = 3,
    ) -> List[Dict[str, str]]:
        """Retrieve AG05 corpus snippets; return empty on any upstream issue."""
        if not self.ag05_context_service:
            return []

        query = (query or "").strip()
        if not query:
            return []

        try:
            return await self.ag05_context_service.retrieve_snippets(
                query,
                max_snippets=max_snippets,
            )
        except Exception as exc:
            logger.warning("AG05 retrieval failed for query '%s': %s", query, exc)
            return []

    @staticmethod
    def _format_ag05_snippets(snippets: List[Dict[str, str]]) -> str:
        """Format AG05 snippets with source IDs for chat context."""
        lines = []
        for snippet in snippets:
            source_id = str(snippet.get("source_id") or "AG05").strip()
            text = str(snippet.get("text") or "").strip()
            if text:
                lines.append(f"[{source_id}] {text}")
        return "\n".join(lines)
    
    # OpenAI function-calling tool schemas
    OPENAI_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "list_available_apis",
                "description": "Liệt kê tất cả API endpoints có sẵn trong hệ thống OpenInfra. Gọi tool này trước khi gọi call_api để biết endpoint nào tồn tại.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "call_api",
                "description": "Gọi một API endpoint thực sự và trả về dữ liệu JSON. Dùng list_available_apis trước để biết endpoint_key hợp lệ.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_key": {
                            "type": "string",
                            "description": "Tên endpoint key (vd: opendata_assets, opendata_feature_types, v1_sensors, v1_incidents)",
                        },
                        "skip": {"type": "integer", "default": 0, "description": "Số bản ghi bỏ qua"},
                        "limit": {"type": "integer", "default": 10, "description": "Số bản ghi tối đa"},
                        "feature_type": {"type": "string", "description": "Lọc theo loại tài sản"},
                        "feature_code": {"type": "string", "description": "Lọc theo mã tài sản"},
                        "sensor_type": {"type": "string", "description": "Lọc theo loại cảm biến"},
                        "status": {"type": "string", "description": "Lọc theo trạng thái"},
                        "severity": {"type": "string", "description": "Lọc theo mức độ"},
                        "asset_id": {"type": "string", "description": "ID tài sản"},
                    },
                    "required": ["endpoint_key"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_system_stats",
                "description": "Lấy thống kê tổng quan hệ thống: tổng số tài sản, cảm biến, sự cố từ database.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]

    async def _execute_tool(self, name: str, args: Dict) -> str:
        """Execute a named tool and return string result."""
        if name == "list_available_apis":
            result = []
            for key, endpoint in API_ENDPOINTS.items():
                params_desc = ", ".join([
                    f"{n}: {info['description']}"
                    for n, info in endpoint.get("params", {}).items()
                ])
                result.append(
                    f"- **{key}**: {endpoint['method']} {endpoint['path']}\n"
                    f"  Mô tả: {endpoint['description']}\n"
                    f"  Params: {params_desc or 'Không có'}"
                )
            return "\n\n".join(result)

        elif name == "call_api":
            endpoint_key = args.pop("endpoint_key", None)
            if not endpoint_key:
                return "Thiếu endpoint_key"
            api_result = await self._call_real_api(endpoint_key, args or {})
            if api_result.get("success"):
                data = api_result.get("data", {})
                data_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
                if len(data_str) > 4000:
                    data_str = data_str[:4000] + "\n... (đã cắt bớt)"
                endpoint_info = API_ENDPOINTS.get(endpoint_key, {})
                card = json.dumps({
                    "endpoint": endpoint_info.get("path", ""),
                    "method": endpoint_info.get("method", "GET"),
                    "description": endpoint_info.get("description", ""),
                    "url": api_result.get("url"),
                    "status": api_result.get("status_code"),
                }, ensure_ascii=False)
                return (
                    f"✅ API gọi thành công!\n"
                    f"URL: {api_result.get('url')}\n"
                    f"Status: {api_result.get('status_code')}\n\n"
                    f"Kết quả:\n```json\n{data_str}\n```\n\n"
                    f"API_CARD_DATA: {card}"
                )
            else:
                return f"❌ Lỗi: {api_result.get('error')}\nURL: {api_result.get('url')}"

        elif name == "get_system_stats":
            stats = await self._get_stats()
            return json.dumps(stats, ensure_ascii=False, indent=2, default=str)

        return f"Unknown tool: {name}"

    async def stream_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        asset_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from the agent using real tool calling."""

        if not self.llm:
            yield {"type": "error", "content": "AI agent not configured. Please set GEMINI_API_KEY or mount Copilot token."}
            yield {"type": "done"}
            return

        try:
            # Build messages
            messages = []

            # Add asset context if provided
            if asset_context:
                asset_info = (
                    f"🎯 **Asset đang được chọn:**\n"
                    f"- ID: {asset_context.get('asset_id', 'N/A')}\n"
                    f"- Loại: {asset_context.get('feature_type', 'N/A')}\n"
                    f"- Mã: {asset_context.get('feature_code', 'N/A')}\n"
                    f"- Geometry: {asset_context.get('geometry', {}).get('type', 'N/A') if asset_context.get('geometry') else 'N/A'}\n\n"
                    f"Người dùng đang hỏi về asset này. Dùng asset_id để tra thêm thông tin qua call_api."
                )
                messages.append(SystemMessage(content=asset_info))

            retrieval_query = query
            if asset_context:
                retrieval_query = (
                    f"{query}\nAsset context: "
                    f"{json.dumps(asset_context, ensure_ascii=False, default=str)}"
                )

            yield {"type": "tool_start", "tool": "retrieve_ag05_context", "input": query}
            ag05_snippets = await self._retrieve_ag05_snippets(retrieval_query, max_snippets=3)
            yield {
                "type": "tool_end",
                "output": f"Retrieved {len(ag05_snippets)} AG05 snippets",
            }

            ag05_context_message = self._format_ag05_snippets(ag05_snippets)
            if ag05_context_message:
                messages.append(
                    SystemMessage(
                        content=(
                            "AG05 vector corpus snippets (source IDs included). "
                            "Prefer these facts when relevant:\n"
                            f"{ag05_context_message}"
                        )
                    )
                )

            # Add chat history
            if chat_history:
                for msg in chat_history[-10:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=query))

            # Use tool-calling path for Copilot, plain streaming for Gemini
            if isinstance(self.llm, CopilotStreamLLM):
                async def on_tool_call(name, args):
                    yield_queue_item = {"type": "tool_start", "tool": name, "input": str(args)}
                    # Can't yield from callback directly; use a list to collect
                    pass

                full_response = ""
                pending_tool_events = []

                async def on_tool_call_cb(name, args):
                    pending_tool_events.append({"type": "tool_start", "tool": name, "input": str(args)})

                async def stream_gen():
                    nonlocal full_response
                    async for chunk in self.llm.astream_with_tools(
                        messages, self.OPENAI_TOOLS, self._execute_tool, on_tool_call=on_tool_call_cb
                    ):
                        # Flush any pending tool events first
                        while pending_tool_events:
                            yield pending_tool_events.pop(0)
                        if chunk.content:
                            full_response += chunk.content
                            yield {"type": "token", "content": chunk.content}
                    yield {"type": "final", "content": full_response}
                    yield {"type": "done"}

                async for event in stream_gen():
                    yield event

            else:
                # Gemini path: pre-fetch context then stream
                yield {"type": "tool_start", "tool": "analyze_query", "input": query}
                context_data = await self._analyze_query(query)
                yield {"type": "tool_end", "output": f"Found {len(context_data)} relevant data sources"}

                context_parts = []
                if ag05_context_message:
                    context_parts.append(f"📚 AG05 snippets:\n{ag05_context_message}")
                if "stats" in context_data:
                    context_parts.append(f"📊 Thống kê:\n{json.dumps(context_data['stats'], indent=2, ensure_ascii=False)}")
                if "assets" in context_data:
                    context_parts.append(f"🏗️ Tài sản mẫu:\n{json.dumps(context_data['assets'], indent=2, ensure_ascii=False, default=str)}")
                if "sensors" in context_data:
                    context_parts.append(f"📡 Cảm biến:\n{json.dumps(context_data['sensors'], indent=2, ensure_ascii=False, default=str)}")
                if "api_example" in context_data:
                    context_parts.append(f"💻 Code:\n{context_data['api_example']}")
                if "available_apis" in context_data:
                    context_parts.append(f"🔌 APIs:\n{context_data['available_apis']}")

                context_message = "\n\n".join(context_parts) if context_parts else "Không có dữ liệu context."

                user_message = f"Câu hỏi: {query}\n\nContext:\n{context_message}\n\nHãy trả lời dựa trên dữ liệu trên."
                # Replace last human message with enriched version
                if messages and isinstance(messages[-1], HumanMessage):
                    messages[-1] = HumanMessage(content=user_message)

                full_response = ""
                async for chunk in self.llm.astream(messages):
                    if chunk.content:
                        full_response += chunk.content
                        yield {"type": "token", "content": chunk.content}

                yield {"type": "final", "content": full_response}
                yield {"type": "done"}

        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            yield {"type": "error", "content": f"Lỗi: {str(e)}"}
            yield {"type": "done"}
    
    async def query(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None, asset_context: Optional[Dict[str, Any]] = None) -> str:
        """Non-streaming query"""
        
        if not self.llm:
            return "AI agent not configured. Please set GEMINI_API_KEY or mount Copilot token."
        
        try:
            # Collect all chunks
            full_response = ""
            async for chunk in self.stream_response(query, chat_history, asset_context):
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
