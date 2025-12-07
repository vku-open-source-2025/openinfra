"""
AI Agent Service using LangChain and Google Gemini
Provides intelligent querying of infrastructure data and API assistance
"""
import os
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AIAgentService:
    """AI Agent for infrastructure data querying and API assistance"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, AI agent will not work")
            self.llm = None
            return
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.api_key,
            temperature=0.7,
        )
        
        self.system_prompt = """Bạn là trợ lý AI cho hệ thống OpenInfra - Quản lý hạ tầng GIS thông minh.

Nhiệm vụ của bạn:
1. Trả lời câu hỏi về dữ liệu hạ tầng (assets, sensors, incidents)
2. Hướng dẫn sử dụng API với JSON-LD format
3. Cung cấp code examples khi được yêu cầu

API Endpoints chính (base URL: https://api.openinfra.space/api/v1):
- GET /assets - Lấy danh sách tài sản hạ tầng
- GET /assets/{id} - Chi tiết tài sản
- GET /iot/sensors - Danh sách cảm biến IoT
- GET /iot/sensors/{id}/data - Dữ liệu cảm biến (query params: from_time, to_time, limit)
- GET /incidents - Danh sách sự cố
- GET /linked-data/assets - Assets dạng JSON-LD (Linked Data format)
- GET /linked-data/sensors - Sensors dạng JSON-LD

Khi cung cấp code examples, hãy dùng Python, cURL và JavaScript.
Luôn trả lời bằng tiếng Việt, thân thiện và chi tiết.

Dữ liệu hiện có trong hệ thống sẽ được cung cấp dựa trên câu hỏi của người dùng."""
    
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
            # Analyze query and get relevant data
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
