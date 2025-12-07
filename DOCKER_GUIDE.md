# 🐳 Hướng Dẫn Khắc Phục Lỗi Docker - FloodWatch

## 🔍 Vấn Đề Hiện Tại

1. **Docker không chạy** - Các lệnh Docker không trả về kết quả
2. **Subscription bị trùng** - Warning: `Already exists: urn:ngsi-ld:Subscription:FloodRiskRain`

---

## ✅ GIẢI PHÁP CHI TIẾT

### Bước 1: Khởi Động Docker Desktop

#### Windows:
1. Tìm **"Docker Desktop"** trong Start Menu
2. Click để mở ứng dụng
3. Chờ biểu tượng Docker ở **System Tray** (góc dưới bên phải) chuyển sang **màu xanh**
4. Khi biểu tượng màu xanh = Docker đã sẵn sàng ✓

#### Kiểm tra Docker đã chạy:
```powershell
docker --version
docker ps
```

Nếu lệnh trên trả về kết quả → Docker đã OK!

---

### Bước 2: Khởi Động FloodWatch Containers

#### 2.1. Dọn dẹp containers cũ (nếu có):
```powershell
cd E:\FloodWatch
docker-compose down
```

#### 2.2. Khởi động tất cả services:
```powershell
docker-compose up -d
```

#### 2.3. Kiểm tra trạng thái:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Kết quả mong đợi:** Tất cả 9 containers đều có status **"Up"**:
- ✅ mongodb
- ✅ orion-ld
- ✅ cratedb
- ✅ quantumleap
- ✅ redis
- ✅ floodwatch-api
- ✅ floodwatch-subscription
- ✅ floodwatch-weather-simulator
- ✅ floodwatch-water-simulator

---

### Bước 3: Sửa Lỗi Subscription Trùng Lặp

#### Vấn đề:
Warning `⚠ Already exists` xảy ra khi subscription đã tồn tại từ lần chạy trước.

#### Giải pháp tự động:
```powershell
# Chạy script sửa lỗi
python fix_subscriptions.py
```

Script sẽ:
1. Liệt kê tất cả subscriptions hiện có
2. Xóa chúng
3. Hướng dẫn bạn tạo lại

#### Sau khi xóa, tạo lại subscriptions:
```powershell
# Khởi động lại subscription container
docker restart floodwatch-subscription

# Kiểm tra logs
docker logs -f floodwatch-subscription
```

---

### Bước 4: Kiểm Tra Hoạt Động

#### 4.1. Test các endpoint:
```powershell
# Test Orion-LD
curl http://localhost:1026/version

# Test API Backend
curl http://localhost:8000/health

# Test QuantumLeap
curl http://localhost:8668/version
```

#### 4.2. Xem logs của từng service:
```powershell
# Backend API
docker logs floodwatch-api --tail 50

# Subscription Manager
docker logs floodwatch-subscription --tail 50

# Weather Simulator
docker logs floodwatch-weather-simulator --tail 50

# Water Level Simulator
docker logs floodwatch-water-simulator --tail 50
```

---

## 🎯 Container Không Chạy?

### Nếu 1 container không start được:

#### 1. Xem logs chi tiết:
```powershell
docker logs <container-name>
```

#### 2. Xem lỗi cụ thể:
```powershell
docker inspect <container-name>
```

#### 3. Khởi động lại container đó:
```powershell
docker restart <container-name>
```

#### 4. Rebuild nếu cần:
```powershell
docker-compose up -d --build <service-name>
```

---

## 🔧 Các Lệnh Hữu Ích

### Dọn dẹp hoàn toàn:
```powershell
# Stop và xóa tất cả
docker-compose down -v

# Xóa images cũ
docker image prune -a

# Khởi động lại từ đầu
docker-compose up -d --build
```

### Xem resource usage:
```powershell
docker stats
```

### Xem network:
```powershell
docker network ls
docker network inspect floodwatch_floodwatch-net
```

---

## 📊 Kiểm Tra Frontend

Sau khi tất cả containers đã chạy:

### 1. Khởi động Client:
```powershell
cd client
pnpm dev
```

### 2. Mở trình duyệt:
- Frontend: http://localhost:8082
- API Docs: http://localhost:8000/docs
- CrateDB: http://localhost:4200

---

## ⚠️ Lưu Ý Quan Trọng

1. **Docker Desktop phải luôn chạy** trước khi dùng `docker` commands
2. **Chờ MongoDB healthy** trước khi Orion-LD start (docker-compose đã config)
3. **Subscriptions cần được tạo SAU KHI** tất cả services đã sẵn sàng
4. **Nếu có lỗi port bị chiếm:**
   ```powershell
   # Tìm process đang dùng port
   netstat -ano | findstr :<port>
   
   # Kill process
   taskkill /PID <process-id> /F
   ```

---

## 🆘 Troubleshooting

### Vấn đề: "Error response from daemon: conflict"
**Giải pháp:**
```powershell
docker-compose down
docker-compose up -d
```

### Vấn đề: "Cannot connect to Docker daemon"
**Giải pháp:** Mở Docker Desktop và đợi nó khởi động

### Vấn đề: Container liên tục restart
**Giải pháp:** 
```powershell
docker logs <container-name>  # Xem lỗi gì
```

### Vấn đề: "Already exists" subscriptions
**Giải pháp:** Chạy `python fix_subscriptions.py`

---

## 📞 Cần Trợ Giúp?

Nếu vẫn gặp vấn đề, hãy cung cấp:
1. Output của: `docker ps -a`
2. Logs của container lỗi: `docker logs <container-name>`
3. Screenshot lỗi nếu có

---

**Chúc bạn thành công! 🚀**
