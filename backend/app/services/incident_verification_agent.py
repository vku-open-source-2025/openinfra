"""
AI Agent for Incident Verification
An intelligent agent that can autonomously verify incidents by:
- Accessing IoT sensor data from asset_id
- Analyzing sensor readings for anomalies
- Checking for duplicates
- Verifying spam/legitimacy
- Making autonomous decisions based on context
"""
import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from google import genai
from google.genai import types

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.domain.models.incident import Incident
from app.domain.services.duplicate_detection_service import DuplicateDetectionService
from app.services.ai_verification_service import AIVerificationService
from app.domain.services.iot_service import IoTService
from app.domain.repositories.incident_repository import IncidentRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class IncidentVerificationAgent:
    """AI Agent for autonomous incident verification with tool access."""
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        incident_repository: IncidentRepository,
        duplicate_detection_service: Optional[DuplicateDetectionService] = None,
        iot_service: Optional[IoTService] = None,
        verification_service: Optional[AIVerificationService] = None
    ):
        self.db = db
        self.incident_repository = incident_repository
        self.duplicate_detection_service = duplicate_detection_service
        self.iot_service = iot_service
        self.verification_service = verification_service or AIVerificationService()
        
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, incident verification agent will not work")
            self.client = None
            return
        
        # Initialize Gemini client with function calling support
        self.client = genai.Client(api_key=self.api_key)
        # Use stable model for production reliability (function calling supported)
        # Can switch to live model if needed via config
        self.model = settings.GEMINI_CHAT_MODEL_STABLE
        
        # Create tools (function definitions for Gemini)
        self.tools = self._create_tool_definitions()
        
        # Create agent prompt
        self.system_prompt = """You are an AI Incident Verification Agent for OpenInfra infrastructure management system.

Your role is to autonomously verify incident reports by:
1. Analyzing the incident details (title, description, category, severity)
2. Checking IoT sensor data from the asset (if asset_id is provided)
3. Detecting potential duplicates
4. Verifying legitimacy (spam detection)
5. Making a final verification decision

## Decision Making Process

You should follow this workflow:
1. **Initial Analysis**: Review incident details
2. **IoT Data Check**: If asset_id exists, fetch and analyze sensor data
3. **Duplicate Detection**: Check for similar incidents
4. **Spam Verification**: Verify if the report is legitimate
5. **Final Decision**: Based on all evidence, make a verification decision

## Tools Available

- `get_asset_iot_data`: Get all IoT sensor data for an asset
- `analyze_sensor_readings`: Analyze sensor readings for anomalies
- `check_duplicates`: Check for duplicate incidents
- `verify_spam`: Verify if incident is spam/legitimate

## Output Format

After verification, provide:
- **verification_status**: "verified" | "to_be_verified" | "rejected"
- **confidence_score**: 0.0-1.0
- **reason**: Detailed explanation of your decision
- **evidence**: List of evidence gathered (IoT data, duplicates, etc.)
- **recommendations**: Any recommendations for next steps

Always respond in Vietnamese if the incident description is in Vietnamese, otherwise use English."""

    def _create_tool_definitions(self) -> List[Dict]:
        """Create tool definitions for Gemini function calling."""
        return [
            {
                "name": "get_asset_iot_data",
                "description": "Lấy dữ liệu IoT từ asset (sensors, readings, alerts). Sử dụng tool này khi incident có asset_id để kiểm tra dữ liệu cảm biến.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "ID của asset cần lấy dữ liệu IoT"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Số giờ dữ liệu cần lấy (mặc định 24 giờ)",
                            "default": 24
                        }
                    },
                    "required": ["asset_id"]
                }
            },
            {
                "name": "analyze_sensor_readings",
                "description": "Phân tích sensor readings để tìm anomalies và patterns. Sử dụng sau khi có dữ liệu từ get_asset_iot_data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sensor_readings_json": {
                            "type": "string",
                            "description": "JSON string chứa sensor readings từ get_asset_iot_data"
                        }
                    },
                    "required": ["sensor_readings_json"]
                }
            },
            {
                "name": "check_duplicates",
                "description": "Kiểm tra các incident trùng lặp. Luôn luôn gọi tool này để kiểm tra duplicate.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "incident_id": {
                            "type": "string",
                            "description": "ID của incident cần kiểm tra duplicate"
                        }
                    },
                    "required": ["incident_id"]
                }
            },
            {
                "name": "verify_spam",
                "description": "Kiểm tra xem incident có phải spam hay không. Luôn luôn gọi tool này để verify legitimacy.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Tiêu đề của incident"},
                        "description": {"type": "string", "description": "Mô tả chi tiết"},
                        "category": {"type": "string", "description": "Loại incident"},
                        "severity": {"type": "string", "description": "Mức độ nghiêm trọng"},
                        "asset_type": {"type": "string", "description": "Loại asset (optional)"},
                        "asset_name": {"type": "string", "description": "Tên asset (optional)"},
                        "image_url": {"type": "string", "description": "URL hình ảnh (optional)"}
                    },
                    "required": ["title", "description", "category", "severity"]
                }
            }
        ]
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool function."""
        
        if tool_name == "get_asset_iot_data":
            return await self._get_asset_iot_data(
                asset_id=arguments.get("asset_id"),
                hours=arguments.get("hours", 24)
            )
        
        elif tool_name == "analyze_sensor_readings":
            return await self._analyze_sensor_readings(
                sensor_readings_json=arguments.get("sensor_readings_json")
            )
        
        elif tool_name == "check_duplicates":
            return await self._check_duplicates(
                incident_id=arguments.get("incident_id")
            )
        
        elif tool_name == "verify_spam":
            return await self._verify_spam(
                title=arguments.get("title"),
                description=arguments.get("description"),
                category=arguments.get("category"),
                severity=arguments.get("severity"),
                asset_type=arguments.get("asset_type"),
                asset_name=arguments.get("asset_name"),
                image_url=arguments.get("image_url")
            )
        
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    async def _get_asset_iot_data(self, asset_id: str, hours: int = 24) -> str:
            """Lấy dữ liệu IoT từ asset (sensors, readings, alerts).
            
            Args:
                asset_id: ID của asset cần lấy dữ liệu
                hours: Số giờ dữ liệu cần lấy (mặc định 24 giờ)
            
            Returns:
                JSON string chứa thông tin sensors, readings, và alerts
            """
            try:
                if not self.iot_service:
                    return json.dumps({"error": "IoT service not available"})
                
                # Get sensors for this asset
                sensors = await self.iot_service.list_sensors(0, 100, asset_id=asset_id)
                
                if not sensors:
                    return json.dumps({
                        "asset_id": asset_id,
                        "sensors": [],
                        "readings": [],
                        "alerts": [],
                        "summary": {"total_sensors": 0, "total_readings": 0, "active_alerts": 0},
                        "message": "No sensors found for this asset"
                    })
                
                # Get readings for all sensors
                from_time = datetime.utcnow() - timedelta(hours=hours)
                to_time = datetime.utcnow()
                
                all_readings = []
                for sensor in sensors:
                    try:
                        readings = await self.iot_service.get_sensor_readings(
                            str(sensor.id), from_time, to_time, limit=200
                        )
                        all_readings.extend(readings)
                    except Exception as e:
                        logger.warning(f"Error getting readings for sensor {sensor.id}: {e}")
                
                # Sort by timestamp
                all_readings.sort(key=lambda r: r.timestamp if r.timestamp else datetime.min, reverse=True)
                
                result = {
                    "asset_id": asset_id,
                    "sensors": [
                        {
                            "id": str(s.id),
                            "sensor_code": s.sensor_code,
                            "sensor_type": s.sensor_type.value if hasattr(s.sensor_type, 'value') else str(s.sensor_type),
                            "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
                            "measurement_unit": s.measurement_unit,
                            "last_seen": s.last_seen.isoformat() if s.last_seen else None,
                            "last_reading": s.last_reading.dict() if s.last_reading else None
                        }
                        for s in sensors
                    ],
                    "readings": [
                        {
                            "sensor_id": str(r.sensor_id),
                            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                            "value": r.value,
                            "unit": r.unit,
                            "status": r.status.value if hasattr(r.status, 'value') else str(r.status)
                        }
                        for r in all_readings[:200]  # Limit to 200 most recent
                    ],
                    "summary": {
                        "total_sensors": len(sensors),
                        "total_readings": len(all_readings),
                        "online_sensors": len([s for s in sensors if s.status.value == "online" if hasattr(s.status, 'value') else str(s.status) == "online"]),
                        "time_range_hours": hours
                    }
                }
                
                return json.dumps(result, ensure_ascii=False, default=str)
                
            except Exception as e:
                logger.error(f"Error getting IoT data for asset {asset_id}: {e}")
                return json.dumps({"error": str(e)})
        
    async def _analyze_sensor_readings(self, sensor_readings_json: str) -> str:
            """Phân tích sensor readings để tìm anomalies và patterns.
            
            Args:
                sensor_readings_json: JSON string chứa sensor readings từ get_asset_iot_data
            
            Returns:
                Phân tích về anomalies, trends, và patterns
            """
            try:
                data = json.loads(sensor_readings_json)
                readings = data.get("readings", [])
                
                if not readings:
                    return json.dumps({
                        "analysis": "No readings available",
                        "anomalies": [],
                        "trends": []
                    })
                
                # Group readings by sensor
                by_sensor = {}
                for reading in readings:
                    sensor_id = reading.get("sensor_id")
                    if sensor_id not in by_sensor:
                        by_sensor[sensor_id] = []
                    by_sensor[sensor_id].append(reading)
                
                analysis = {
                    "total_readings": len(readings),
                    "sensors_analyzed": len(by_sensor),
                    "anomalies": [],
                    "trends": [],
                    "statistics": {}
                }
                
                # Analyze each sensor
                for sensor_id, sensor_readings in by_sensor.items():
                    if not sensor_readings:
                        continue
                    
                    values = [r.get("value", 0) for r in sensor_readings if r.get("value") is not None]
                    if not values:
                        continue
                    
                    # Calculate statistics
                    values_sorted = sorted(values)
                    stats = {
                        "sensor_id": sensor_id,
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "median": values_sorted[len(values_sorted) // 2] if values_sorted else 0
                    }
                    
                    # Detect anomalies (values significantly different from average)
                    threshold = stats["avg"] * 0.3  # 30% deviation
                    anomalies = [
                        r for r in sensor_readings
                        if r.get("value") is not None and abs(r.get("value") - stats["avg"]) > threshold
                    ]
                    
                    if anomalies:
                        analysis["anomalies"].append({
                            "sensor_id": sensor_id,
                            "count": len(anomalies),
                            "anomaly_values": [a.get("value") for a in anomalies[:5]]
                        })
                    
                    # Detect trends (increasing/decreasing)
                    if len(values) >= 3:
                        recent_avg = sum(values[-3:]) / 3
                        earlier_avg = sum(values[:3]) / 3 if len(values) >= 6 else recent_avg
                        trend = "increasing" if recent_avg > earlier_avg * 1.1 else "decreasing" if recent_avg < earlier_avg * 0.9 else "stable"
                        analysis["trends"].append({
                            "sensor_id": sensor_id,
                            "trend": trend,
                            "recent_avg": recent_avg,
                            "earlier_avg": earlier_avg
                        })
                    
                    analysis["statistics"][sensor_id] = stats
                
                return json.dumps(analysis, ensure_ascii=False, default=str)
                
            except Exception as e:
                logger.error(f"Error analyzing sensor readings: {e}")
                return json.dumps({"error": str(e)})
        
    async def _check_duplicates(self, incident_id: str) -> str:
            """Kiểm tra các incident trùng lặp.
            
            Args:
                incident_id: ID của incident cần kiểm tra
            
            Returns:
                Danh sách các duplicate incidents với similarity scores
            """
            try:
                if not self.duplicate_detection_service:
                    return json.dumps({"error": "Duplicate detection service not available"})
                
                incident = await self.incident_repository.find_by_id(incident_id)
                if not incident:
                    return json.dumps({"error": f"Incident {incident_id} not found"})
                
                duplicates = await self.duplicate_detection_service.detect_duplicates(incident)
                
                result = {
                    "incident_id": incident_id,
                    "duplicates_found": len(duplicates),
                    "duplicates": [
                        {
                            "incident_id": dup.incident_id,
                            "similarity_score": dup.similarity_score,
                            "match_reasons": dup.match_reasons
                        }
                        for dup in duplicates
                    ]
                }
                
                return json.dumps(result, ensure_ascii=False, default=str)
                
            except Exception as e:
                logger.error(f"Error checking duplicates for incident {incident_id}: {e}")
                return json.dumps({"error": str(e)})
        
    async def _verify_spam(
            title: str,
            description: str,
            category: str,
            severity: str,
            asset_type: Optional[str] = None,
            asset_name: Optional[str] = None,
            image_url: Optional[str] = None
        ) -> str:
            """Kiểm tra xem incident có phải spam hay không.
            
            Args:
                title: Tiêu đề của incident
                description: Mô tả chi tiết
                category: Loại incident
                severity: Mức độ nghiêm trọng
                asset_type: Loại asset (optional)
                asset_name: Tên asset (optional)
                image_url: URL hình ảnh (optional)
            
            Returns:
                Kết quả verification với confidence score
            """
            try:
                result = await self.verification_service.verify_incident_report(
                    incident_title=title,
                    incident_description=description,
                    incident_category=category,
                    incident_severity=severity,
                    asset_type=asset_type,
                    asset_name=asset_name,
                    image_url=image_url
                )
                
                return json.dumps(result, ensure_ascii=False, default=str)
                
            except Exception as e:
                logger.error(f"Error verifying spam: {e}")
                return json.dumps({"error": str(e)})
    
    async def verify_incident(
        self,
        incident: Incident,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Autonomously verify an incident using AI agent with tools.
        
        Args:
            incident: Incident to verify
            max_iterations: Maximum number of tool calls (default 10)
        
        Returns:
            Verification result with status, confidence, reason, and evidence
        """
        if not self.client:
            return {
                "verification_status": "failed",
                "confidence_score": None,
                "reason": "AI agent not configured. Please set GEMINI_API_KEY.",
                "evidence": [],
                "recommendations": []
            }
        
        try:
            # Build initial prompt
            prompt_parts = [
                f"Verify this incident report:\n\n",
                f"**Incident ID**: {incident.id}\n",
                f"**Incident Number**: {incident.incident_number}\n",
                f"**Title**: {incident.title}\n",
                f"**Description**: {incident.description}\n",
                f"**Category**: {incident.category.value if incident.category else 'N/A'}\n",
                f"**Severity**: {incident.severity.value if incident.severity else 'N/A'}\n",
            ]
            
            if incident.asset_id:
                prompt_parts.append(f"**Asset ID**: {incident.asset_id}\n")
                prompt_parts.append(f"\n**IMPORTANT**: This incident is linked to asset {incident.asset_id}. ")
                prompt_parts.append("You MUST use get_asset_iot_data tool to check IoT sensor data.\n")
            
            if incident.photos:
                prompt_parts.append(f"\n**Photos**: {len(incident.photos)} photo(s) attached\n")
                if incident.photos:
                    prompt_parts.append(f"**Photo URLs**: {', '.join(incident.photos[:3])}\n")
            
            prompt_parts.append(
                "\n\nPlease verify this incident by:\n"
                "1. If asset_id exists, use get_asset_iot_data to check IoT sensor data\n"
                "2. Use check_duplicates to check for duplicate incidents\n"
                "3. Use verify_spam to verify legitimacy\n"
                "4. Based on all evidence, make a final decision\n\n"
                "After gathering all evidence, provide your verification result in JSON format:\n"
                '{\n'
                '  "verification_status": "verified" | "to_be_verified" | "rejected",\n'
                '  "confidence_score": 0.0-1.0,\n'
                '  "reason": "Detailed explanation",\n'
                '  "evidence": ["list of evidence gathered"],\n'
                '  "recommendations": ["recommendations for next steps"]\n'
                '}'
            )
            
            # Simplified approach: Agent decides what to check and we execute sequentially
            # Build comprehensive prompt with tool descriptions
            tools_description = "\n\n## Available Tools:\n\n"
            for tool in self.tools:
                tools_description += f"### {tool['name']}\n"
                tools_description += f"{tool['description']}\n"
                tools_description += f"Parameters: {json.dumps(tool['parameters'], indent=2)}\n\n"
            
            full_prompt = self.system_prompt + tools_description + "\n\n" + "".join(prompt_parts)
            full_prompt += "\n\nIMPORTANT: You can request to use tools by saying 'USE_TOOL: tool_name' followed by parameters in JSON format."
            full_prompt += "\nAfter I execute the tool, I will provide the results and you can continue analysis."
            full_prompt += "\nWhen you have all the information, provide your final verification result in JSON format."
            
            # Collect evidence
            evidence = []
            
            # Step 1: Check IoT data if asset_id exists
            iot_data = None
            if incident.asset_id:
                logger.info(f"Agent checking IoT data for asset {incident.asset_id}")
                iot_data_str = await self._get_asset_iot_data(incident.asset_id, hours=24)
                iot_data = json.loads(iot_data_str)
                evidence.append(f"IoT data checked: {iot_data.get('summary', {}).get('total_sensors', 0)} sensors, {iot_data.get('summary', {}).get('total_readings', 0)} readings")
            
            # Step 2: Check duplicates
            duplicates_data = None
            if self.duplicate_detection_service:
                logger.info(f"Agent checking duplicates for incident {incident.id}")
                duplicates_str = await self._check_duplicates(str(incident.id))
                duplicates_data = json.loads(duplicates_str)
                if duplicates_data.get("duplicates_found", 0) > 0:
                    evidence.append(f"Found {duplicates_data['duplicates_found']} potential duplicates")
            
            # Step 3: Verify spam
            spam_result = None
            logger.info(f"Agent verifying spam for incident {incident.id}")
            spam_str = await self._verify_spam(
                title=incident.title or "",
                description=incident.description or "",
                category=incident.category.value if incident.category else "other",
                severity=incident.severity.value if incident.severity else "medium",
                asset_type=None,  # Could be populated from asset
                asset_name=None,
                image_url=incident.photos[0] if incident.photos else None
            )
            spam_result = json.loads(spam_str)
            evidence.append(f"Spam verification: {spam_result.get('verification_status', 'unknown')} (confidence: {spam_result.get('confidence_score', 0)})")
            
            # Step 4: Build context for final decision
            context_parts = [
                "## Incident Information:",
                f"- Title: {incident.title}",
                f"- Description: {incident.description}",
                f"- Category: {incident.category.value if incident.category else 'N/A'}",
                f"- Severity: {incident.severity.value if incident.severity else 'N/A'}",
            ]
            
            if iot_data:
                context_parts.append("\n## IoT Sensor Data:")
                context_parts.append(json.dumps(iot_data.get("summary", {}), indent=2))
                if iot_data.get("sensors"):
                    context_parts.append(f"\nSensors: {len(iot_data['sensors'])} sensors found")
                    # Analyze readings if available
                    if iot_data.get("readings"):
                        analysis_str = await self._analyze_sensor_readings(iot_data_str)
                        analysis = json.loads(analysis_str)
                        context_parts.append(f"\nSensor Analysis: {json.dumps(analysis, indent=2)}")
            
            if duplicates_data:
                context_parts.append("\n## Duplicate Detection:")
                context_parts.append(json.dumps(duplicates_data, indent=2))
            
            if spam_result:
                context_parts.append("\n## Spam Verification:")
                context_parts.append(json.dumps(spam_result, indent=2))
            
            context_parts.append("\n\n## Your Task:")
            context_parts.append("Based on all the evidence above, provide your final verification decision in JSON format:")
            context_parts.append('{\n  "verification_status": "verified" | "to_be_verified" | "rejected",\n  "confidence_score": 0.0-1.0,\n  "reason": "Detailed explanation",\n  "evidence": ["list of evidence"],\n  "recommendations": ["recommendations"]\n}')
            
            final_prompt = "\n".join(context_parts)
            
            # Call Gemini for final decision
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=final_prompt
                    )
                )
                
                # Extract response
                output = ""
                if response and hasattr(response, 'text'):
                    output = response.text
                elif response and hasattr(response, 'candidates') and response.candidates:
                    if response.candidates[0].content and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'text') and part.text:
                                output += part.text
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}")
                output = f"Error generating response: {str(e)}"
            
            # Parse result
            verification_result = self._parse_agent_output(output, incident)
            
            # Add evidence
            verification_result["evidence"] = evidence
            
            logger.info(
                f"Agent verification completed for incident {incident.id}: "
                f"status={verification_result.get('verification_status')}, "
                f"score={verification_result.get('confidence_score')}"
            )
            
            return verification_result
            
            # If max iterations reached without final response
            return {
                "verification_status": "to_be_verified",
                "confidence_score": 0.5,
                "reason": f"Agent reached max iterations ({max_iterations}) without final decision",
                "evidence": [],
                "recommendations": ["Manual review recommended"]
            }
            
        except Exception as e:
            logger.error(f"Error in agent verification for incident {incident.id}: {e}", exc_info=True)
            return {
                "verification_status": "failed",
                "confidence_score": None,
                "reason": f"Agent verification failed: {str(e)}",
                "evidence": [],
                "recommendations": []
            }
    
    def _parse_agent_output(self, output: str, incident: Incident) -> Dict[str, Any]:
        """Parse agent output and extract verification result."""
        # Try to find JSON in output
        import re
        
        # Look for JSON block
        json_match = re.search(r'\{[^{}]*"verification_status"[^{}]*\}', output, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result
            except:
                pass
        
        # Fallback: extract information from text
        result = {
            "verification_status": "to_be_verified",
            "confidence_score": 0.5,
            "reason": output[:500],  # First 500 chars
            "evidence": [],
            "recommendations": []
        }
        
        # Try to extract confidence score
        score_match = re.search(r'(?:confidence|score)[:\s]+([0-9.]+)', output, re.IGNORECASE)
        if score_match:
            try:
                score = float(score_match.group(1))
                if score > 1:
                    score = score / 100  # Normalize percentage
                result["confidence_score"] = max(0.0, min(1.0, score))
            except:
                pass
        
        # Determine status based on keywords
        output_lower = output.lower()
        if any(word in output_lower for word in ["verified", "legitimate", "valid", "confirmed"]):
            result["verification_status"] = "verified"
        elif any(word in output_lower for word in ["spam", "fake", "invalid", "reject"]):
            result["verification_status"] = "rejected"
        
        return result
