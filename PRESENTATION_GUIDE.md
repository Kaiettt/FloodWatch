# 🎤 Hướng dẫn Thuyết trình & Demo - FloodWatch OLP 2025

> **Mục tiêu:** Tạo bài thuyết trình ấn tượng, demo dễ xem, thể hiện đầy đủ giá trị dự án  
> **Thời gian:** 7-10 phút (thuyết trình) + 3-5 phút (Q&A)  
> **Đối tượng:** Ban giám khảo cuộc thi mã nguồn mở

---

## 🎯 Tư duy từ góc độ Giám khảo

### **Giám khảo muốn thấy gì?**

1. ✅ **Ý tưởng rõ ràng** - Vấn đề gì? Giải pháp gì? Tại sao hay?
2. ✅ **Demo hoạt động** - Code chạy được, không chỉ slides
3. ✅ **Giá trị thực tế** - Giải quyết bài toán thật, không phải toy project
4. ✅ **Kỹ thuật tốt** - Code quality, architecture, best practices
5. ✅ **Mở rộng được** - Cộng đồng có thể đóng góp, sử dụng
6. ✅ **Presentation tốt** - Nói rõ ràng, tự tin, trả lời được câu hỏi

### **Giám khảo KHÔNG muốn thấy gì?**

❌ **Chỉ có slides** - không có demo code  
❌ **Demo lỗi** - code không chạy được  
❌ **Nói quá kỹ thuật** - không ai hiểu  
❌ **Quá dài dòng** - mất thời gian  
❌ **Không trả lời được** - không hiểu dự án của mình  

---

## 📋 Cấu trúc Bài Thuyết trình (7-10 phút)

### **Phần 1: Hook - Vấn đề thực tế (1 phút)**

#### 🎬 Script:
> "Xin chào ban giám khảo. Tôi xin phép bắt đầu với một câu hỏi: **Có bao giờ bạn bị kẹt xe vì ngập lụt ở TP.HCM không?**"
> 
> *[Pause 2 giây - để giám khảo suy nghĩ]*
> 
> "Theo thống kê, TP.HCM có **hơn 200 điểm ngập** mỗi mùa mưa. Người dân phải **mất hàng giờ** để di chuyển, gây thiệt hại kinh tế lớn. **Vấn đề:** Chúng ta không biết điểm nào đang ngập, mức độ ra sao, và khi nào sẽ ngập."
> 
> "Hôm nay, tôi xin giới thiệu **FloodWatch** - hệ thống giám sát ngập lụt thời gian thực sử dụng công nghệ **FIWARE/NGSI-LD** - chuẩn Smart City châu Âu."

#### 🎨 Visual:
- **Slide 1:** Ảnh ngập lụt TP.HCM (số liệu: 200+ điểm ngập)
- **Slide 2:** Vấn đề: "Không biết điểm nào ngập? Mức độ? Khi nào?"

**Mục tiêu:** Thu hút sự chú ý, tạo context thực tế

---

### **Phần 2: Giải pháp - Ý tưởng độc đáo (2 phút)**

#### 🎬 Script:
> "FloodWatch giải quyết vấn đề này bằng **3 ý tưởng độc đáo:**"
> 
> **"Ý tưởng 1: Sử dụng chuẩn FIWARE/NGSI-LD"**
> "Thay vì REST API đơn giản, chúng tôi sử dụng **FIWARE/NGSI-LD** - chuẩn Smart City được sử dụng tại hơn 200 thành phố châu Âu. Điều này giúp hệ thống **dễ tích hợp**, **mở rộng**, và **tuân thủ chuẩn quốc tế**."
> 
> **"Ý tưởng 2: 15 Polygon Zones thực tế"**
> "Thay vì dùng vòng tròn đơn giản, chúng tôi tạo **15 polygon zones** dựa trên dữ liệu ngập thực tế từ Sở GTVT TP.HCM. Mỗi zone có tham số riêng: độ nhạy triều cường, độ nhạy mưa, tốc độ thoát nước."
> 
> **"Ý tưởng 3: AI-Powered Risk Scoring"**
> "Chúng tôi kết hợp dữ liệu từ **4 nguồn**: Sensors IoT, CCTV cameras, báo cáo người dân, và dự báo thời tiết. AI phân tích và đưa ra **risk score** thông minh, hỗ trợ keywords tiếng Việt như 'nguy hiểm', 'ngập sâu', 'kẹt xe'."

#### 🎨 Visual:
- **Slide 3:** Diagram kiến trúc FIWARE (Mermaid từ README)
- **Slide 4:** Bản đồ 15 polygon zones TP.HCM
- **Slide 5:** 4 nguồn dữ liệu (Sensors, CCTV, Reports, Weather)

**Mục tiêu:** Thể hiện tính nguyên gốc, sáng tạo

---

### **Phần 3: Kiến trúc - Công nghệ (1.5 phút)**

#### 🎬 Script:
> "Kiến trúc của FloodWatch gồm **4 tầng:**"
> 
> "**Tầng 1: Data Sources** - Sensors IoT, CCTV, Citizen Reports, Weather API"
> 
> "**Tầng 2: FIWARE Platform** - Orion-LD Context Broker, QuantumLeap Time-series API, CrateDB Database"
> 
> "**Tầng 3: Backend Services** - FastAPI với 20+ endpoints, AI Service (Gemini), Flood Risk Engine"
> 
> "**Tầng 4: Frontend/API** - REST API, WebSocket real-time, Swagger UI"
> 
> "Tất cả được **containerized** bằng Docker Compose - chỉ cần 1 lệnh để chạy toàn bộ hệ thống."

#### 🎨 Visual:
- **Slide 6:** Diagram Mermaid từ README (4 tầng rõ ràng)
- **Slide 7:** Tech Stack (bảng công nghệ)

**Mục tiêu:** Thể hiện kiến trúc chuyên nghiệp, dễ hiểu

---

### **Phần 4: Demo - Show Code Hoạt động (3 phút)**

> **⚠️ QUAN TRỌNG:** Đây là phần quan trọng nhất! Giám khảo muốn thấy code chạy được.

#### 🎬 Demo Script:

**Bước 1: Khởi động hệ thống (30 giây)**
```bash
# Mở terminal, chạy:
docker-compose up -d

# Giải thích:
"Tôi đang khởi động 8 services: Orion-LD, CrateDB, QuantumLeap, Backend API, và các simulators. 
Chỉ cần 1 lệnh, toàn bộ hệ thống sẽ chạy."
```

**Bước 2: Show Swagger UI (1 phút)**
```
1. Mở browser: http://localhost:8000/docs
2. Giải thích: "Đây là Swagger UI - tài liệu API tự động. 
   Giám khảo có thể xem tất cả 20+ endpoints, test trực tiếp."
3. Click vào endpoint: GET /api/dashboard/stats
4. Click "Try it out" → "Execute"
5. Show response JSON:
   {
     "total": 45,
     "severe": 5,
     "high": 12,
     "medium": 18,
     "low": 10,
     "avgWaterLevel": 0.35
   }
6. Giải thích: "Đây là dữ liệu thực tế từ hệ thống - 45 điểm ngập, 
   5 điểm severe, mức nước trung bình 35cm."
```

**Bước 3: Demo API thực tế (1 phút)**
```
1. Test endpoint: GET /api/flood/nearby
   - lat=10.762622 (Quận 1)
   - lng=106.660172
   - radius=5 (5km)
2. Show response: Danh sách điểm ngập trong 5km
3. Giải thích: "API này giúp mobile app tìm điểm ngập gần vị trí người dùng."
```

**Bước 4: Demo WebSocket Real-time (30 giây)**
```
1. Mở WebSocket test tool (hoặc Postman)
2. Connect: ws://localhost:8000/ws/map
3. Send: {"type": "init"}
4. Show response: {"type": "snapshot", "crowd": [...], "sensor": [...]}
5. Giải thích: "WebSocket cung cấp dữ liệu real-time - 
   frontend có thể cập nhật ngay khi có điểm ngập mới."
```

**Bước 5: Demo AI Chatbot (30 giây)**
```
1. Test endpoint: POST /api/chat
   {
     "message": "Hôm nay Quận 7 có mưa không?",
     "session_id": "demo"
   }
2. Show response: AI trả lời tiếng Việt
3. Giải thích: "AI chatbot tích hợp Gemini, hiểu tiếng Việt, 
   có thể tư vấn về thời tiết và ngập lụt."
```

#### 🎨 Visual:
- **Slide 8:** Screenshot Swagger UI
- **Slide 9:** Screenshot API response
- **Slide 10:** Screenshot WebSocket

**Mục tiêu:** Chứng minh code hoạt động, dễ sử dụng

---

### **Phần 5: Tính năng nổi bật (1 phút)**

#### 🎬 Script:
> "FloodWatch có **5 tính năng nổi bật:**"
> 
> "**1. 15 Polygon Zones** - Dữ liệu thực tế từ Sở GTVT, không phải demo"
> 
> "**2. AI Risk Scoring** - Phân tích thông minh từ 4 nguồn dữ liệu"
> 
> "**3. Flood Prediction** - Dự đoán nguy cơ ngập 6 giờ tới dựa trên weather + triều cường"
> 
> "**4. Real-time Updates** - WebSocket cập nhật ngay lập tức"
> 
> "**5. Citizen Reports** - Người dân có thể báo cáo ngập với ảnh"

#### 🎨 Visual:
- **Slide 11:** 5 tính năng (icon + mô tả ngắn)

**Mục tiêu:** Highlight giá trị độc đáo

---

### **Phần 6: Code Quality & Open Source (1 phút)**

#### 🎬 Script:
> "Về **chất lượng code:**"
> 
> "- **2000+ dòng code Python** với type hints, docstrings"
> "- **20+ test cases** với pytest"
> - **Docker Compose** - 1 lệnh chạy toàn bộ"
> - **Swagger UI** - API documentation tự động"
> 
> "Về **mã nguồn mở:**"
> 
> "- **MIT License** - tự do sử dụng, sửa đổi"
> - **README chi tiết** - 382 dòng hướng dẫn"
> - **API dễ tích hợp** - REST + WebSocket"
> - **Modular architecture** - dễ mở rộng, đóng góp"

#### 🎨 Visual:
- **Slide 12:** Code statistics (số dòng, tests, docs)
- **Slide 13:** Open source benefits (MIT, GitHub, Contributing)

**Mục tiêu:** Thể hiện code quality, khả năng mở rộng

---

### **Phần 7: Kết luận & Call to Action (30 giây)**

#### 🎬 Script:
> "Tóm lại, FloodWatch là hệ thống **giám sát ngập lụt thời gian thực** sử dụng công nghệ **FIWARE/NGSI-LD** - chuẩn Smart City quốc tế."
> 
> "Dự án **open source**, **dễ tích hợp**, và **sẵn sàng cho cộng đồng đóng góp**."
> 
> "Cảm ơn ban giám khảo đã lắng nghe. Tôi sẵn sàng trả lời câu hỏi."

#### 🎨 Visual:
- **Slide 14:** Tóm tắt (3 điểm chính)
- **Slide 15:** Thank you + GitHub link

**Mục tiêu:** Kết thúc mạnh mẽ, mời Q&A

---

## 🎨 Demo Strategy - "Thuần FE" để Giám khảo Dễ Xem

### **Vấn đề:** Giám khảo không muốn xem terminal, code phức tạp

### **Giải pháp: Tạo "Demo Dashboard" đơn giản**

#### **Option 1: Swagger UI (Tốt nhất - đã có sẵn)**

**Ưu điểm:**
- ✅ **Giao diện đẹp** - không phải terminal
- ✅ **Tương tác được** - click, test trực tiếp
- ✅ **Dễ hiểu** - giám khảo thấy rõ API hoạt động
- ✅ **Không cần code** - chỉ cần browser

**Cách demo:**
1. Mở Swagger UI: `http://localhost:8000/docs`
2. Click vào endpoint → "Try it out" → "Execute"
3. Show response JSON
4. Giải thích ý nghĩa dữ liệu

**Endpoints nên demo:**
- `GET /api/dashboard/stats` - Thống kê tổng quan
- `GET /api/flood/nearby` - Tìm điểm ngập
- `GET /api/flood/prediction` - Dự đoán nguy cơ
- `POST /api/chat` - AI Chatbot

---

#### **Option 2: Tạo Simple HTML Dashboard (Nếu có thời gian)**

**Tạo file:** `demo/dashboard.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>FloodWatch Demo Dashboard</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .card { border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 5px; }
        .stats { display: flex; gap: 20px; }
        .stat { text-align: center; }
        .number { font-size: 36px; font-weight: bold; color: #0066cc; }
        button { padding: 10px 20px; background: #0066cc; color: white; border: none; cursor: pointer; }
        button:hover { background: #0052a3; }
        #result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🌊 FloodWatch Demo Dashboard</h1>
    
    <div class="card">
        <h2>📊 Thống kê Tổng quan</h2>
        <button onclick="loadStats()">Tải Dữ liệu</button>
        <div id="stats-result"></div>
    </div>
    
    <div class="card">
        <h2>🔍 Tìm Điểm Ngập Gần</h2>
        <p>Vị trí: Quận 1 (10.762622, 106.660172)</p>
        <p>Bán kính: 5km</p>
        <button onclick="findNearby()">Tìm Kiếm</button>
        <div id="nearby-result"></div>
    </div>
    
    <div class="card">
        <h2>🔮 Dự đoán Nguy cơ Ngập</h2>
        <button onclick="predictFlood()">Dự đoán 6h tới</button>
        <div id="prediction-result"></div>
    </div>
    
    <div class="card">
        <h2>🤖 AI Chatbot</h2>
        <input type="text" id="chat-input" placeholder="Hỏi về thời tiết hoặc ngập lụt..." style="width: 300px; padding: 8px;">
        <button onclick="chat()">Gửi</button>
        <div id="chat-result"></div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000';
        
        async function loadStats() {
            const result = document.getElementById('stats-result');
            result.innerHTML = 'Đang tải...';
            
            try {
                const response = await fetch(`${API_BASE}/api/dashboard/stats`);
                const data = await response.json();
                
                result.innerHTML = `
                    <div class="stats">
                        <div class="stat">
                            <div class="number">${data.total}</div>
                            <div>Tổng điểm ngập</div>
                        </div>
                        <div class="stat">
                            <div class="number" style="color: #ef4444;">${data.severe}</div>
                            <div>Severe (Rất nguy hiểm)</div>
                        </div>
                        <div class="stat">
                            <div class="number" style="color: #f97316;">${data.high}</div>
                            <div>High (Nguy hiểm)</div>
                        </div>
                        <div class="stat">
                            <div class="number" style="color: #eab308;">${data.medium}</div>
                            <div>Moderate (Cần chú ý)</div>
                        </div>
                        <div class="stat">
                            <div class="number" style="color: #22c55e;">${data.low}</div>
                            <div>Low (An toàn)</div>
                        </div>
                    </div>
                    <p><strong>Mức nước trung bình:</strong> ${data.avgWaterLevel}m</p>
                    <p><strong>Cập nhật lúc:</strong> ${new Date(data.lastUpdated).toLocaleString('vi-VN')}</p>
                `;
            } catch (error) {
                result.innerHTML = `<p style="color: red;">Lỗi: ${error.message}</p>`;
            }
        }
        
        async function findNearby() {
            const result = document.getElementById('nearby-result');
            result.innerHTML = 'Đang tìm kiếm...';
            
            try {
                const response = await fetch(`${API_BASE}/api/flood/nearby?lat=10.762622&lng=106.660172&radius=5`);
                const data = await response.json();
                
                result.innerHTML = `
                    <p><strong>Tìm thấy:</strong> ${data.total_crowd + data.total_sensor} điểm ngập</p>
                    <p>- Báo cáo cộng đồng: ${data.total_crowd}</p>
                    <p>- Dữ liệu sensor: ${data.total_sensor}</p>
                    <details>
                        <summary>Xem chi tiết (${data.crowd_reports.length + data.sensor_data.length} điểm)</summary>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </details>
                `;
            } catch (error) {
                result.innerHTML = `<p style="color: red;">Lỗi: ${error.message}</p>`;
            }
        }
        
        async function predictFlood() {
            const result = document.getElementById('prediction-result');
            result.innerHTML = 'Đang dự đoán...';
            
            try {
                const response = await fetch(`${API_BASE}/api/flood/prediction`);
                const data = await response.json();
                
                const risk = data.prediction.next_6h_risk;
                const level = risk > 0.7 ? '🔴 CAO' : risk > 0.4 ? '🟡 TRUNG BÌNH' : '🟢 THẤP';
                
                result.innerHTML = `
                    <h3>Nguy cơ ngập 6 giờ tới: ${level}</h3>
                    <p><strong>Risk Score:</strong> ${(risk * 100).toFixed(1)}%</p>
                    <p><strong>Lời khuyên:</strong> ${data.prediction.advisory.message}</p>
                    <p><strong>Các vùng nguy cơ cao:</strong></p>
                    <ul>
                        ${data.prediction.high_risk_zones.slice(0, 5).map(z => 
                            `<li>${z.name} (${z.district}) - Risk: ${(z.predicted_risk * 100).toFixed(0)}%</li>`
                        ).join('')}
                    </ul>
                `;
            } catch (error) {
                result.innerHTML = `<p style="color: red;">Lỗi: ${error.message}</p>`;
            }
        }
        
        async function chat() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;
            
            const result = document.getElementById('chat-result');
            result.innerHTML = `Đang hỏi AI...`;
            
            try {
                const response = await fetch(`${API_BASE}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, session_id: 'demo' })
                });
                const data = await response.json();
                
                result.innerHTML = `
                    <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p><strong>Bạn hỏi:</strong> ${message}</p>
                        <p><strong>AI trả lời:</strong> ${data.response}</p>
                    </div>
                `;
                input.value = '';
            } catch (error) {
                result.innerHTML = `<p style="color: red;">Lỗi: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

**Cách sử dụng:**
1. Lưu file vào `demo/dashboard.html`
2. Mở bằng browser: `file:///path/to/demo/dashboard.html`
3. Đảm bảo API đang chạy: `docker-compose up -d`
4. Click các button để demo

**Ưu điểm:**
- ✅ **Giao diện đẹp** - không phải terminal
- ✅ **Dễ hiểu** - giám khảo thấy rõ tính năng
- ✅ **Tương tác được** - click button, xem kết quả
- ✅ **Không cần code** - chỉ cần browser

---

#### **Option 3: Postman Collection (Backup)**

**Nếu Swagger không chạy được:**
1. Tạo Postman Collection với các endpoints
2. Import vào Postman
3. Demo bằng Postman UI

---

## 🎯 Key Messages - Những Điểm Cần Nhấn Mạnh

### **1. FIWARE/NGSI-LD - Chuẩn Quốc tế**
> "FloodWatch sử dụng **FIWARE/NGSI-LD** - chuẩn Smart City được sử dụng tại hơn 200 thành phố châu Âu. Điều này giúp hệ thống **dễ tích hợp**, **mở rộng**, và **tuân thủ chuẩn quốc tế**."

### **2. Dữ liệu Thực tế**
> "15 polygon zones dựa trên **dữ liệu thực tế** từ Sở GTVT TP.HCM, không phải demo. Mỗi zone có tham số riêng: độ nhạy triều cường, độ nhạy mưa, tốc độ thoát nước."

### **3. AI Thông minh**
> "AI Risk Scoring kết hợp **4 nguồn dữ liệu**: Sensors, CCTV, Citizen Reports, Weather. Hỗ trợ **keywords tiếng Việt** như 'nguy hiểm', 'ngập sâu', 'kẹt xe'."

### **4. Hoàn thiện & Dễ sử dụng**
> "Backend API đầy đủ với **20+ endpoints**, **Swagger UI** tự động, **Docker Compose** - chỉ cần 1 lệnh để chạy toàn bộ hệ thống."

### **5. Open Source & Mở rộng**
> "MIT License, **README chi tiết**, **API dễ tích hợp**, **Modular architecture** - cộng đồng có thể dễ dàng đóng góp."

---

## ⏱️ Timing - Phân bổ Thời gian

| Phần | Thời gian | Ghi chú |
|------|-----------|---------|
| **Hook - Vấn đề** | 1 phút | Thu hút sự chú ý |
| **Giải pháp** | 2 phút | Ý tưởng độc đáo |
| **Kiến trúc** | 1.5 phút | Công nghệ |
| **Demo** | 3 phút | **QUAN TRỌNG NHẤT** |
| **Tính năng** | 1 phút | Highlight |
| **Code Quality** | 1 phút | Open source |
| **Kết luận** | 30 giây | Call to action |
| **TỔNG** | **10 phút** | + 3-5 phút Q&A |

**Lưu ý:**
- ⚠️ **Demo là phần quan trọng nhất** - dành nhiều thời gian
- ⚠️ **Không nói quá dài** - giữ trong 10 phút
- ⚠️ **Practice trước** - đảm bảo timing chính xác

---

## 🎨 Visual Aids - Slides

### **Slide Structure (15 slides)**

1. **Title Slide** - FloodWatch + Logo
2. **Vấn đề** - Ảnh ngập lụt + số liệu
3. **Giải pháp** - 3 ý tưởng độc đáo
4. **FIWARE/NGSI-LD** - Diagram kiến trúc
5. **15 Polygon Zones** - Bản đồ TP.HCM
6. **4 Nguồn Dữ liệu** - Diagram
7. **Kiến trúc** - Mermaid diagram
8. **Tech Stack** - Bảng công nghệ
9. **Demo - Swagger UI** - Screenshot
10. **Demo - API Response** - JSON example
11. **5 Tính năng** - Icon + mô tả
12. **Code Quality** - Statistics
13. **Open Source** - Benefits
14. **Tóm tắt** - 3 điểm chính
15. **Thank you** - GitHub link

### **Design Tips:**
- ✅ **Dùng màu sắc nhất quán** - FloodWatch brand colors
- ✅ **Ít text, nhiều hình** - visual > text
- ✅ **Font lớn** - dễ đọc từ xa
- ✅ **Icons** - dùng emoji hoặc icons

---

## 🎤 Presentation Tips

### **Do's (Nên làm):**
- ✅ **Demo thực tế** - chạy code live, không chỉ slides
- ✅ **Nói rõ ràng** - tốc độ vừa phải, dễ hiểu
- ✅ **Eye contact** - nhìn giám khảo
- ✅ **Tự tin** - thể hiện hiểu rõ dự án
- ✅ **Practice** - luyện tập 2-3 lần trước
- ✅ **Backup plan** - có plan B nếu demo lỗi

### **Don'ts (Không nên):**
- ❌ **Đọc slides** - nên giải thích tự nhiên
- ❌ **Quá kỹ thuật** - giải thích dễ hiểu
- ❌ **Quá dài** - giữ trong 10 phút
- ❌ **Bỏ qua demo** - phải có live demo
- ❌ **Không practice** - sẽ bị lúng túng

---

## 🎯 Q&A Preparation - Câu hỏi Thường gặp

### **Q1: "Tại sao dùng FIWARE/NGSI-LD?"**
**A:** "FIWARE/NGSI-LD là chuẩn Smart City quốc tế, được sử dụng tại hơn 200 thành phố châu Âu. Điều này giúp hệ thống dễ tích hợp với các hệ thống Smart City khác, tuân thủ chuẩn quốc tế, và có thể mở rộng dễ dàng."

### **Q2: "Làm sao đảm bảo dữ liệu chính xác?"**
**A:** "Chúng tôi kết hợp 4 nguồn dữ liệu: Sensors IoT (độ chính xác cao), CCTV cameras (xác thực bằng hình ảnh), Citizen Reports (báo cáo từ cộng đồng), và Weather API (dự báo). AI Risk Scoring phân tích và đưa ra risk score dựa trên độ tin cậy của từng nguồn."

### **Q3: "Làm sao mở rộng cho các thành phố khác?"**
**A:** "Hệ thống được thiết kế modular, dễ mở rộng. Chỉ cần thay đổi polygon zones và tọa độ trong file cấu hình. API và kiến trúc không thay đổi. Chúng tôi đã có documentation chi tiết trong README và POLYGON_FLOOD_ZONES_PLAN.md."

### **Q4: "Cộng đồng có thể đóng góp như thế nào?"**
**A:** "Dự án open source với MIT License. Cộng đồng có thể: (1) Thêm polygon zones mới, (2) Cải thiện AI Risk Scoring, (3) Tích hợp thêm data sources, (4) Xây dựng frontend, (5) Viết tests. Chúng tôi có Contributing Guide trong README."

### **Q5: "Làm sao đảm bảo bảo mật?"**
**A:** "Chúng tôi có: (1) Rate limiting - 30 requests/minute cho AI endpoints, (2) Input validation - kiểm tra tọa độ, file upload, (3) CORS configuration - bảo mật cross-origin, (4) Image validation - kiểm tra file type và size. API keys được lưu trong environment variables, không hardcode."

### **Q6: "Tại sao không có frontend?"**
**A:** "Chúng tôi tập trung vào backend API và kiến trúc - đây là phần core của dự án mã nguồn mở. Frontend có thể được xây dựng bởi cộng đồng hoặc tích hợp vào các ứng dụng khác. API đầy đủ với Swagger UI, dễ tích hợp."

---

## ✅ Checklist Trước Khi Thuyết trình

### **1 tuần trước:**
- [ ] Practice presentation 2-3 lần
- [ ] Chuẩn bị slides (15 slides)
- [ ] Test demo trên máy thuyết trình
- [ ] Chuẩn bị backup plan (nếu demo lỗi)

### **1 ngày trước:**
- [ ] Test Docker Compose chạy ổn định
- [ ] Test Swagger UI hoạt động
- [ ] Test các API endpoints
- [ ] Chuẩn bị Q&A answers

### **Trước khi thuyết trình:**
- [ ] Chạy `docker-compose up -d` (đợi 2-3 phút)
- [ ] Kiểm tra `/health` endpoint
- [ ] Kiểm tra Swagger UI tại `/docs`
- [ ] Chuẩn bị WebSocket test tool
- [ ] Chuẩn bị slides (PDF hoặc PowerPoint)
- [ ] Chuẩn bị laptop backup (nếu cần)

### **Trong khi thuyết trình:**
- [ ] Nói rõ ràng, tự tin
- [ ] Demo thực tế - không chỉ slides
- [ ] Highlight tính năng độc đáo
- [ ] Nhấn mạnh FIWARE/NGSI-LD
- [ ] Mời cộng đồng đóng góp

---

## 🎯 Kết luận

**Mục tiêu:** Tạo bài thuyết trình ấn tượng, demo dễ xem, thể hiện đầy đủ giá trị dự án.

**Key Points:**
1. ✅ **Hook mạnh** - vấn đề thực tế
2. ✅ **Ý tưởng rõ ràng** - 3 điểm độc đáo
3. ✅ **Demo thực tế** - Swagger UI, API, WebSocket
4. ✅ **Code quality** - tests, docs, Docker
5. ✅ **Open source** - MIT, dễ đóng góp

**Success Criteria:**
- ✅ Giám khảo hiểu rõ ý tưởng
- ✅ Demo hoạt động tốt
- ✅ Trả lời được câu hỏi
- ✅ Thể hiện giá trị thực tế

**Good luck! 🍀**

---

*Tài liệu này được tạo để hỗ trợ thuyết trình FloodWatch tại cuộc thi OLP 2025.*

*Cập nhật lần cuối: 2025-12-09*

