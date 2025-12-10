# Incident Verification Agent

AI Agent tự động kiểm tra và xác minh incident reports với khả năng truy cập IoT data và đưa ra quyết định thông minh.

## Tổng quan

`IncidentVerificationAgent` là một AI agent sử dụng Google Gemini để tự động kiểm tra và xác minh các incident reports. Agent có thể:

1. **Truy cập IoT sensor data** từ asset_id
2. **Phân tích sensor readings** để tìm anomalies
3. **Kiểm tra duplicate incidents**
4. **Verify spam/legitimacy**
5. **Đưa ra quyết định verification** dựa trên tất cả evidence

## Cách hoạt động

### Workflow

1. **Initial Analysis**: Agent phân tích thông tin incident (title, description, category, severity)
2. **IoT Data Check**: Nếu incident có `asset_id`, agent tự động lấy và phân tích IoT sensor data
3. **Duplicate Detection**: Agent kiểm tra các incident trùng lặp
4. **Spam Verification**: Agent verify xem report có phải spam không
5. **Final Decision**: Dựa trên tất cả evidence, agent đưa ra quyết định verification

### Tools có sẵn

Agent có các tools sau:

- **`get_asset_iot_data`**: Lấy dữ liệu IoT từ asset (sensors, readings, alerts)
- **`analyze_sensor_readings`**: Phân tích sensor readings để tìm anomalies và patterns
- **`check_duplicates`**: Kiểm tra các incident trùng lặp
- **`verify_spam`**: Kiểm tra xem incident có phải spam hay không

## Sử dụng

### API Endpoint

```bash
POST /api/v1/incidents/{incident_id}/agent-verify
```

**Response:**
```json
{
  "status": "started",
  "message": "Agent verification started in background",
  "incident_id": "incident_id"
}
```

Verification chạy trong background và kết quả sẽ được cập nhật vào incident.

### Kết quả Verification

Agent trả về kết quả với format:

```json
{
  "verification_status": "verified" | "to_be_verified" | "rejected",
  "confidence_score": 0.0-1.0,
  "reason": "Detailed explanation",
  "evidence": ["list of evidence gathered"],
  "recommendations": ["recommendations for next steps"]
}
```

Kết quả này được lưu vào incident:
- `ai_verification_status`: verification_status
- `ai_confidence_score`: confidence_score
- `ai_verification_reason`: reason

### Ví dụ sử dụng

```python
from app.services.incident_verification_agent import IncidentVerificationAgent
from app.api.v1.dependencies import get_incident_verification_agent

# Get agent instance
agent = await get_incident_verification_agent()

# Get incident
incident = await incident_service.get_incident_by_id(incident_id)

# Run verification
result = await agent.verify_incident(incident)

print(f"Status: {result['verification_status']}")
print(f"Confidence: {result['confidence_score']}")
print(f"Reason: {result['reason']}")
print(f"Evidence: {result['evidence']}")
```

## Cấu hình

Agent sử dụng các services sau:

- `IncidentRepository`: Để truy cập incident data
- `DuplicateDetectionService`: Để kiểm tra duplicates
- `IoTService`: Để truy cập IoT sensor data
- `AIVerificationService`: Để verify spam

Tất cả được inject qua dependency injection trong `get_incident_verification_agent()`.

## Tích hợp vào Incident Creation

Để tự động chạy agent verification khi tạo incident mới, có thể thêm vào `create_incident`:

```python
# Trong create_incident endpoint
background_tasks.add_task(
    run_agent_verification,
    incident_id=str(incident.id),
    incident_service=incident_service
)

async def run_agent_verification(incident_id: str, incident_service: IncidentService):
    agent = await get_incident_verification_agent()
    incident = await incident_service.get_incident_by_id(incident_id)
    result = await agent.verify_incident(incident)
    # Update incident with result
    await incident_service.update_verification(...)
```

## Lưu ý

1. **API Key**: Cần set `GEMINI_API_KEY` environment variable
2. **Performance**: Agent verification có thể mất vài giây do cần gọi nhiều services
3. **Background Processing**: Nên chạy trong background task để không block request
4. **Error Handling**: Agent sẽ trả về `verification_status: "failed"` nếu có lỗi

## So sánh với AI Verification Service

| Feature | AI Verification Service | Incident Verification Agent |
|---------|------------------------|----------------------------|
| Spam Detection | ✅ | ✅ |
| IoT Data Access | ❌ | ✅ |
| Duplicate Detection | ❌ | ✅ |
| Autonomous Decision | ❌ | ✅ |
| Evidence Collection | ❌ | ✅ |
| Recommendations | ❌ | ✅ |

Agent là phiên bản nâng cao với khả năng tự quyết định và truy cập nhiều nguồn dữ liệu hơn.
