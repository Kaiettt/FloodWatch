# 🚨 Khắc Phục Lỗi "Already Exists" Subscription

## ❌ Vấn Đề

Khi chạy Docker containers, bạn thấy warning:
```
⚠ Already exists: urn:ngsi-ld:Subscription:FloodRiskRain
```

## 🔍 Nguyên Nhân

Subscription này đã được tạo từ lần chạy trước và vẫn còn lưu trong Orion-LD Context Broker. Khi script chạy lại, nó cố gắng tạo subscription mới với cùng ID → bị conflict.

## ✅ Giải Pháp

### Cách 1: Tự Động Xử Lý (KHUYÊN DÙNG)

Script đã được cập nhật để **tự động xóa và tạo lại** subscription khi phát hiện conflict!

**Không cần làm gì cả** - script sẽ tự động:
1. Phát hiện subscription đã tồn tại
2. Xóa subscription cũ
3. Tạo lại subscription mới

### Cách 2: Xóa Thủ Công Tất Cả Subscriptions

Nếu muốn reset hoàn toàn:

```powershell
# Chạy script xóa tất cả
python fix_subscriptions.py
```

Script sẽ:
- ✅ Liệt kê tất cả subscriptions hiện có
- ✅ Cho phép bạn xác nhận trước khi xóa
- ✅ Xóa từng subscription một
- ✅ Hướng dẫn tạo lại

Sau đó khởi động lại subscription container:
```powershell
docker restart floodwatch-subscription
```

### Cách 3: Xóa Bằng API

```powershell
# Lấy danh sách subscriptions
curl http://localhost:1026/ngsi-ld/v1/subscriptions

# Xóa một subscription cụ thể
curl -X DELETE "http://localhost:1026/ngsi-ld/v1/subscriptions/urn:ngsi-ld:Subscription:FloodRiskRain"
```

### Cách 4: Dọn Dẹp Database Hoàn Toàn

Nếu muốn xóa sạch mọi thứ:

```powershell
# Stop tất cả containers
docker-compose down -v

# Xóa volumes (bao gồm cả database)
docker volume prune

# Khởi động lại
docker-compose up -d
```

⚠️ **Lưu ý**: Cách này sẽ xóa TẤT CẢ dữ liệu trong MongoDB và CrateDB!

---

## 📊 Kiểm Tra Subscriptions

### Xem tất cả subscriptions:
```powershell
curl http://localhost:1026/ngsi-ld/v1/subscriptions | python -m json.tool
```

### Đếm số lượng subscriptions:
```powershell
curl -s http://localhost:1026/ngsi-ld/v1/subscriptions | python -c "import sys, json; data=json.load(sys.stdin); print(f'Total: {len(data)} subscriptions')"
```

### Xem chi tiết một subscription:
```powershell
curl "http://localhost:1026/ngsi-ld/v1/subscriptions/urn:ngsi-ld:Subscription:FloodRiskRain" | python -m json.tool
```

---

## 🎯 Subscriptions Trong FloodWatch

Hệ thống FloodWatch có **10 subscriptions**:

### Gửi đến FastAPI Backend (3):
1. ✅ `WaterLevelObserved` → `/flood/sensor`
2. ✅ `CrowdReport` → `/flood/crowd`
3. ✅ `WeatherObserved` → `/weather/notify`

### Gửi đến QuantumLeap (7):
4. ✅ `WaterLevelObserved-QL` → CrateDB
5. ✅ `CrowdReport-QL` → CrateDB
6. ✅ `CameraStream` → CrateDB
7. ✅ `FloodRiskSensor` → CrateDB
8. ✅ `FloodRiskCrowd` → CrateDB
9. ✅ `WeatherObserved` → CrateDB
10. ✅ `FloodRiskRain` → CrateDB ⚠️ (cái này hay bị conflict)

---

## 🛠️ Troubleshooting

### Vấn đề: Subscription vẫn không được tạo
**Kiểm tra:**
```powershell
# Container subscription có chạy không?
docker ps | findstr subscription

# Xem logs
docker logs floodwatch-subscription

# Orion-LD có sẵn không?
curl http://localhost:1026/version
```

### Vấn đề: Script báo lỗi connection
**Nguyên nhân:** Orion-LD chưa sẵn sàng

**Giải pháp:**
```powershell
# Chờ vài giây rồi thử lại
timeout /t 10
python fix_subscriptions.py
```

### Vấn đề: Không xóa được subscription
**Giải pháp:** Restart Orion-LD
```powershell
docker restart orion-ld
timeout /t 5
python fix_subscriptions.py
```

---

## 📝 Cập Nhật Mới

**subscription_main.py** đã được cập nhật với logic:
```python
if res.status_code == 409:  # Already exists
    print(f"⚠ Already exists: {sub['id']} - Deleting and recreating...")
    if delete_subscription(sub["id"]):
        # Retry creating after deletion
        res = requests.post(ORION_URL, json=payload, headers=headers)
        if res.status_code in (200, 201):
            print(f"✔ Subscription recreated: {sub['id']}")
```

**Lợi ích:**
- ✅ Tự động sửa conflict
- ✅ Không cần can thiệp thủ công
- ✅ Đảm bảo subscription luôn đúng cấu hình

---

## 🚀 Quy Trình Khuyến Nghị

1. **Khởi động Docker:**
   ```powershell
   docker-compose up -d
   ```

2. **Chờ tất cả services sẵn sàng:**
   ```powershell
   docker ps
   # Đợi đến khi tất cả đều "Up" và "healthy"
   ```

3. **Kiểm tra subscriptions:**
   ```powershell
   docker logs floodwatch-subscription
   # Nên thấy "✔ Subscription created" hoặc "✔ Subscription recreated"
   ```

4. **Nếu có lỗi, chạy script sửa:**
   ```powershell
   python fix_subscriptions.py
   docker restart floodwatch-subscription
   ```

5. **Test hệ thống:**
   ```powershell
   # Test API
   curl http://localhost:8000/health
   
   # Test Orion
   curl http://localhost:1026/ngsi-ld/v1/entities?limit=5
   ```

---

**✅ Hoàn Thành!** Bây giờ hệ thống của bạn sẽ tự động xử lý subscription conflicts! 🎉
