# FloodWatch API Docs (v3.2.0)

Tài liệu tóm tắt các API trong `backend/app/main.py`. Mặc định chạy với FastAPI, có sẵn Swagger tại `/docs` và Redoc tại `/redoc`.

- Base URL: `http://<host>:<port>` (ví dụ khi docker-compose: `http://localhost:8000`)
- Auth: Chưa bật auth, mọi endpoint công khai. Nếu public, nên thêm reverse proxy + rate limit.
- Định dạng: JSON UTF-8, trừ upload `/report` (form-data) và WebSocket.
- CORS: cấu hình qua env `CORS_ORIGINS` (mặc định `*`).

## Health & Root
- `GET /` — Thông tin service, version, danh sách endpoint chính.
- `GET /health` — Kiểm tra Orion-LD và CrateDB. Trả về `status` (healthy/degraded/unhealthy) kèm trạng thái từng service.
  - Response mẫu:
    ```json
    {
      "status": "healthy",
      "orion_ld": "connected",
      "cratedb": "connected",
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```

## Dashboard
- `GET /api/dashboard/stats`
  - Query: `lat?`, `lng?`, `radius?` (km, 0.1–100) để lọc theo bán kính.
  - Trả về tổng điểm, severe/high/medium/low, `avgWaterLevel`, đếm sensor/community, `lastUpdated`, thông tin filter.
  - Request mẫu: `GET /api/dashboard/stats?lat=10.7626&lng=106.6601&radius=5`
  - Response mẫu (rút gọn):
    ```json
    {
      "total": 42,
      "severe": 3,
      "high": 7,
      "medium": 12,
      "low": 20,
      "avgWaterLevel": 0.42,
      "sensorCount": 15,
      "communityCount": 27,
      "lastUpdated": "2025-01-01T10:00:00Z",
      "filter": { "lat": 10.7626, "lng": 106.6601, "radius_km": 5.0 }
    }
    ```
- `GET /api/dashboard/districts`
  - Không tham số. Trả về thống kê theo quận: `total`, `severe`, `high`, `avgWaterLevel`, sắp xếp quận ngập nặng trước.
  - Response mẫu (rút gọn):
    ```json
    {
      "districts": [
        { "district": "Binh Thanh", "total": 5, "severe": 1, "high": 2, "avgWaterLevel": 0.55 }
      ],
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```

## Flood Data
- `GET /api/flood/nearby`
  - Query: `lat`*, `lng`*, `radius` (km, mặc định 5, 0.1–100), `limit` (1–500).
  - Trả về danh sách ngập từ crowd + sensor trong bán kính, kèm `distance_km`, `total_crowd`, `total_sensor`.
  - Request mẫu: `GET /api/flood/nearby?lat=10.7626&lng=106.6601&radius=3&limit=50`
  - Response mẫu (rút gọn):
    ```json
    {
      "center": { "lat": 10.7626, "lng": 106.6601 },
      "radius_km": 3,
      "crowd_reports": [
        { "lat": 10.77, "lng": 106.67, "riskLevel": "High", "waterlevel": 0.6, "distance_km": 1.2 }
      ],
      "sensor_data": [
        { "zoneid": "q1-01", "severity": "Moderate", "waterlevel": 0.35, "distance_km": 0.8 }
      ],
      "total_crowd": 1,
      "total_sensor": 1,
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```

## Ingest NGSI-LD (dành cho Orion-LD notifications)
- `POST /flood/sensor`
  - Body JSON (notification Orion-LD, lấy `data[0]`): yêu cầu `id`, `waterLevel.value`, `location`, tùy chọn `district`, `alertThreshold.value`, `waterTrend.value`, `zoneId.value`, `zoneName.value`.
  - Server tính `severity`, tạo entity `FloodRiskSensor` qua Orion-LD. Trả về `entity_id`, `severity`.
  - Request mẫu:
    ```json
    {
      "data": [{
        "id": "urn:ngsi-ld:WaterLevelObserved:1",
        "waterLevel": { "value": 0.72, "observedAt": "2025-01-01T09:59:00Z" },
        "alertThreshold": { "value": 0.5 },
        "waterTrend": { "value": 0.08 },
        "district": { "value": "Quan 1" },
        "zoneId": { "value": "q1-01" },
        "zoneName": { "value": "Ben Nghe" },
        "location": { "type": "GeoProperty", "value": { "type": "Point", "coordinates": [106.7, 10.77] } }
      }]
    }
    ```
  - Response mẫu:
    ```json
    { "status": "success", "entity_id": "urn:ngsi-ld:FloodRiskSensor:...", "severity": "High" }
    ```
- `POST /flood/crowd`
  - Body JSON (NGSI-LD hoặc raw) cần `id`, `location`, `waterLevel`; tùy chọn `verified`, `description`, `photos`, `address`, `timestamp`.
  - Server tính `riskScore`, `riskLevel`, gửi Orion-LD entity `FloodRiskCrowd`. Trả về `entity_id`, `risk_score`, `risk_level`, `factors`.
  - Request mẫu:
    ```json
    {
      "id": "crowd-123",
      "waterLevel": { "value": 0.55 },
      "verified": { "value": true },
      "description": { "value": "Ngập tới nửa bánh xe, kẹt xe nặng" },
      "photos": { "value": ["https://.../img1.png"] },
      "location": { "type": "GeoProperty", "value": { "type": "Point", "coordinates": [106.69, 10.76] } },
      "timestamp": { "value": "2025-01-01T10:00:00Z" }
    }
    ```
  - Response mẫu:
    ```json
    {
      "status": "success",
      "entity_id": "urn:ngsi-ld:FloodRiskCrowd:...",
      "risk_score": 0.71,
      "risk_level": "High",
      "factors": { "waterLevelFactor": 0.64, "textSeverityFactor": 0.7, "photoFactor": 0.25, "verifiedFactor": 0.15, "keywordMatches": 2 }
    }
    ```

## Reports (báo cáo người dân)
- `POST /report`
  - Form-data: `description`* (text), `reporterId`*, `latitude?`, `longitude?`, `water_level? (0–20)`, `images[]` (jpg/png/webp/gif, <=10MB/ảnh).
  - Lưu ảnh vào `/static/uploads`, tạo entity qua `create_crowd_report_entity`. Trả về `id`, `image_urls`, `waterLevel`.
  - cURL mẫu:
    ```
    curl -X POST http://localhost:8000/report ^
      -F "description=Ngập 40cm, xe máy khó qua" ^
      -F "reporterId=user_123" ^
      -F "latitude=10.7626" ^
      -F "longitude=106.6601" ^
      -F "water_level=0.4" ^
      -F "images=@C:\path\to\photo.jpg"
    ```
  - Response mẫu:
    ```json
    {
      "id": "urn:ngsi-ld:FloodRiskCrowd:...",
      "status": "created",
      "image_urls": ["http://localhost:8000/static/uploads/photo.jpg"],
      "waterLevel": 0.4
    }
    ```
- `GET /api/reports/recent`
  - Query: `limit` (1–100, default 20), `hours` (1–168, default 24).
  - Trả về danh sách báo cáo cộng đồng mới nhất, gồm lat/lng, waterLevel, riskScore/Level, address, confidence, reportedAt.
  - Response mẫu (rút gọn):
    ```json
    {
      "reports": [
        {
          "id": "urn:ngsi-ld:FloodRiskCrowd:...",
          "lat": 10.77,
          "lng": 106.67,
          "waterLevel": 0.6,
          "riskScore": 0.74,
          "riskLevel": "High",
          "address": "Nguyen Huu Canh, Binh Thanh",
          "confidence": "Verified",
          "reportedAt": "2025-01-01T09:50:00Z",
          "type": "community"
        }
      ],
      "total": 1,
      "hours": 24,
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```
- `GET /api/reports/{report_id}`
  - Trả về chi tiết một báo cáo: vị trí, waterLevel, riskScore/Level, address, confidence, factors, reportedAt.
  - Response mẫu (rút gọn):
    ```json
    {
      "id": "urn:ngsi-ld:FloodRiskCrowd:...",
      "lat": 10.77,
      "lng": 106.67,
      "waterLevel": 0.6,
      "riskScore": 0.74,
      "riskLevel": "High",
      "address": "Nguyen Huu Canh",
      "confidence": "Verified",
      "factors": { "waterLevelFactor": 0.7, "textSeverityFactor": 0.7 },
      "reportedAt": "2025-01-01T09:50:00Z",
      "type": "community"
    }
    ```

## WebSocket
- `GET /ws/map`
  - Nhận: JSON message.
    - `{ "type": "init", "lat?", "lng?", "radius?" }` → gửi snapshot crowd + sensor (có thể lọc bán kính).
    - `{ "type": "poll" }` → gửi các bản ghi mới (crowd/sensor) kể từ lần cuối.
  - Trả về: `snapshot` hoặc `update` chứa mảng `crowd`, `sensor`, `timestamp`.
  - Tin nhắn trả về mẫu (rút gọn):
    ```json
    {
      "type": "snapshot",
      "crowd": [{ "lat": 10.77, "lng": 106.67, "risklevel": "High" }],
      "sensor": [{ "zoneid": "q1-01", "waterlevel": 0.35, "severity": "Moderate" }],
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```

## Weather (OpenWeather, có rate limit slowapi)
- `GET /api/weather/districts` — Danh sách 22 quận/huyện.
- `GET /api/weather/current?district_ids=q1,q7,...`
  - Nếu không truyền, trả về 6 quận chính. Gồm thời tiết hiện tại + forecast 5h.
  - Response mẫu (rút gọn):
    ```json
    {
      "success": true,
      "data": [
        { "district": "q1", "temp": 30.5, "humidity": 78, "isRaining": false, "forecast": [{ "pop": 0.2 }] }
      ],
      "total": 1,
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```
- `GET /api/weather/all` — Thời tiết 22 quận + `summary` (rainyDistricts, districtsWithRainForecast, avgHumidity).
- `GET /api/weather/{district_id}` — Thời tiết chi tiết 1 quận.
- `GET /api/weather/advice` — Gợi ý nhanh dựa trên thời tiết hiện tại.

## Chatbot (Gemini AI, rate limit 30/min)
- `POST /api/chat`
  - Body JSON: `{ "message": "...", "session_id": "optional" }`.
  - Trả về: `{ success, response, session_id, timestamp, error? }`. Bot tự thêm context thời tiết + ngập hiện tại.
  - Request mẫu:
    ```json
    { "message": "Hôm nay Quận 7 có mưa không?", "session_id": "user1" }
    ```
  - Response mẫu (rút gọn):
    ```json
    {
      "success": true,
      "response": "Hiện tại Quận 7 có mưa nhẹ, dự báo 2 giờ tới mưa tăng.",
      "session_id": "user1",
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```
- `POST /api/chat/clear?session_id=...` — Xóa lịch sử một session.
- `GET /api/chat/session/{session_id}` — Lấy thông tin session.

## Prediction
- `GET /api/flood/risk-analysis`
  - Phân tích rủi ro ngập bằng AI dựa trên thời tiết + dữ liệu ngập hiện tại. Trả về `analysis`, `weatherSummary`, `floodData`.
- `GET /api/flood/prediction`
  - Dự đoán nguy cơ ngập 6h tới. Trả về `prediction.next_6h_risk`, `risk_level`, `high_risk_zones` (các tuyến dễ ngập), `advisory` (khuyến nghị), `factors` (rain_probability, tidal_effect, current_flood_factor), `current_situation`.
  - Response mẫu (rút gọn):
    ```json
    {
      "success": true,
      "prediction": {
        "next_6h_risk": 0.63,
        "risk_level": "🟡 TRUNG BÌNH",
        "high_risk_zones": [
          { "id": "nguyen_huu_canh", "name": "Nguyễn Hữu Cảnh", "predicted_risk": 0.72 }
        ],
        "advisory": { "level": "🟡 TRUNG BÌNH", "message": "Có khả năng ngập cục bộ", "actions": ["Kiểm tra tình trạng đường"] },
        "factors": { "rain_probability": 0.5, "tidal_effect": 0.7, "current_flood_factor": 0.12 }
      },
      "timestamp": "2025-01-01T10:00:00Z"
    }
    ```

## Alerts (Gemini)
- `POST /api/alerts/enhance`
  - Query: `water_level`* (0–5), `location?`, `district?`, `severity?`, `trend?`.
  - Trả về mô tả cảnh báo sinh bởi AI.
  - Request mẫu: `POST /api/alerts/enhance?water_level=1.2&district=Quan%207&severity=Severe`
  - Response mẫu:
    ```json
    { "success": true, "description": "Mực nước 1.2m tại Quận 7, nguy cơ ngập nặng. Hạn chế di chuyển qua khu vực thấp.", "water_level": 1.2, "district": "Quan 7", "severity": "Severe" }
    ```
- `POST /api/alerts/enhance-batch`
  - Body JSON: `{ "alerts": [ ... ] }`.
  - Trả về danh sách `alerts` đã được tăng cường mô tả.
  - Request mẫu:
    ```json
    { "alerts": [{ "water_level": 0.8, "district": "Quan 12", "severity": "High" }] }
    ```
  - Response mẫu (rút gọn):
    ```json
    { "success": true, "alerts": [{ "water_level": 0.8, "district": "Quan 12", "description": "..." }], "total": 1 }
    ```

## Khác
- Static files: `/static/uploads/...`
- Rate limit: áp dụng cho chatbot qua slowapi.
- Cache: TTL cache 30s cho snapshot crowd/sensor; dùng lọc bán kính nếu truyền `lat/lng/radius`.

