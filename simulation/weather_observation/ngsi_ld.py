# ngsi_ld.py
import json

def normalize_to_ngsi_ld(weather_data, lat, lon):
    # Trích xuất các thông tin từ dữ liệu API
    rainfall = weather_data.get('rain', {}).get('1h', 0)  # Lượng mưa trong 1h, mặc định 0 nếu không có
    temperature = weather_data['main']['temp']  # Nhiệt độ hiện tại
    humidity = weather_data['main']['humidity']  # Độ ẩm không khí
    forecast = weather_data['weather'][0]['description']  # Dự báo thời tiết
    
    # Chuẩn hóa thành NGSI-LD JSON
    ngsi_ld_data = {
        "id": f"Weather-{weather_data['id']}",  # ID duy nhất cho mỗi bản ghi thời tiết
        "type": "WeatherObservation",  # Kiểu entity là WeatherObservation
        "timestamp": weather_data['dt'],  # Thời gian dữ liệu (timestamp UNIX)
        "rainfall": rainfall,  # Lượng mưa trong 1h
        "temperature": temperature,  # Nhiệt độ
        "humidity": humidity,  # Độ ẩm
        "forecast": forecast,  # Dự báo thời tiết
        "location": {  # Vị trí (tọa độ)
            "type": "Point",
            "coordinates": [lon, lat]
        }
    }
    
    return ngsi_ld_data
