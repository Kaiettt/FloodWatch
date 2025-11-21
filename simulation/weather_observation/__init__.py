import requests

from .ngsi_ld import normalize_to_ngsi_ld
API_KEY = '4cfeed8e0b19a6b8886060e9d27bfa82'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

def get_weather_data(lat, lon):
    url = f'{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()  # Trả về dữ liệu dưới dạng JSON
    else:
        print("Error fetching data from API")
        return None

def main():
    lat, lon = 10.762622, 106.660172  # Ví dụ tọa độ TP.HCM
    weather_data = get_weather_data(lat, lon)
    
    if weather_data:
        ngsi_ld_weather = normalize_to_ngsi_ld(weather_data, lat, lon)  # Chuẩn hóa dữ liệu
        print(ngsi_ld_weather)  # In ra kết quả NGSI-LD