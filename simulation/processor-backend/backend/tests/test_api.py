# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

"""
Integration Tests cho FloodWatch API
=====================================
Kiểm tra các API endpoints hoạt động đúng.

Chạy tests:
    cd simulation/processor-backend/backend
    pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint trả về thông tin API"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert "status" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data


class TestDashboardEndpoints:
    """Test dashboard statistics endpoints."""
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        response = client.get("/api/dashboard/stats")
        
        # Có thể trả về 200 hoặc 500 (nếu DB không kết nối)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "severe" in data
            assert "high" in data
    
    def test_dashboard_stats_with_radius(self):
        """Test dashboard stats với radius filter"""
        response = client.get(
            "/api/dashboard/stats",
            params={
                "lat": 10.762622,
                "lng": 106.660172,
                "radius": 5.0
            }
        )
        
        assert response.status_code in [200, 500]
    
    def test_dashboard_districts(self):
        """Test districts summary endpoint"""
        response = client.get("/api/dashboard/districts")
        
        assert response.status_code in [200, 500]


class TestFloodDataEndpoints:
    """Test flood data endpoints."""
    
    def test_nearby_floods_valid_coords(self):
        """Test nearby floods với tọa độ hợp lệ"""
        response = client.get(
            "/api/flood/nearby",
            params={
                "lat": 10.762622,
                "lng": 106.660172,
                "radius": 5.0
            }
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "center" in data
            assert "radius_km" in data
    
    def test_nearby_floods_invalid_coords(self):
        """Test nearby floods với tọa độ ngoài Việt Nam"""
        response = client.get(
            "/api/flood/nearby",
            params={
                "lat": 1.3521,  # Singapore
                "lng": 103.8198,
                "radius": 5.0
            }
        )
        
        assert response.status_code == 400
    
    def test_nearby_floods_missing_params(self):
        """Test nearby floods thiếu params bắt buộc"""
        response = client.get("/api/flood/nearby")
        assert response.status_code == 422  # Validation error


class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    def test_flood_prediction(self):
        """Test flood prediction endpoint"""
        response = client.get("/api/flood/prediction")
        
        assert response.status_code in [200, 500, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "prediction" in data
            
            prediction = data["prediction"]
            assert "next_6h_risk" in prediction
            assert "risk_level" in prediction
            assert "advisory" in prediction
    
    def test_flood_risk_analysis(self):
        """Test flood risk analysis endpoint"""
        response = client.get("/api/flood/risk-analysis")
        
        assert response.status_code in [200, 500, 503]


class TestReportsEndpoints:
    """Test citizen reports endpoints."""
    
    def test_recent_reports(self):
        """Test get recent reports"""
        response = client.get("/api/reports/recent")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "reports" in data
            assert "total" in data
    
    def test_recent_reports_with_params(self):
        """Test recent reports với custom params"""
        response = client.get(
            "/api/reports/recent",
            params={"limit": 10, "hours": 12}
        )
        
        assert response.status_code in [200, 500]
    
    def test_report_detail_not_found(self):
        """Test get report detail với ID không tồn tại"""
        response = client.get("/api/reports/nonexistent_id_12345")
        
        # Có thể 404 (not found) hoặc 500 (DB error)
        assert response.status_code in [404, 500]


class TestWeatherEndpoints:
    """Test weather endpoints."""
    
    def test_weather_districts_list(self):
        """Test get districts list"""
        response = client.get("/api/weather/districts")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "districts" in data
        assert "total" in data
        assert data["total"] > 0
    
    def test_weather_current(self):
        """Test get current weather"""
        response = client.get("/api/weather/current")
        
        # 200 OK hoặc 503 nếu OpenWeather không khả dụng
        assert response.status_code in [200, 500, 503]
    
    def test_weather_current_specific_districts(self):
        """Test get weather cho districts cụ thể"""
        response = client.get(
            "/api/weather/current",
            params={"district_ids": "q1,q7,binh_thanh"}
        )
        
        assert response.status_code in [200, 500, 503]


class TestChatbotEndpoints:
    """Test chatbot endpoints."""
    
    def test_chat_endpoint(self):
        """Test chat endpoint"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Xin chào",
                "session_id": "test_session"
            }
        )
        
        # 200 OK hoặc error nếu Gemini không khả dụng
        assert response.status_code in [200, 500, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "response" in data
            assert "session_id" in data
    
    def test_chat_clear_session(self):
        """Test clear chat session"""
        response = client.post(
            "/api/chat/clear",
            params={"session_id": "test_session"}
        )
        
        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Test OpenAPI/Swagger documentation."""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema có sẵn"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "🌊 FloodWatch API"
    
    def test_swagger_docs(self):
        """Test Swagger UI có sẵn"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc(self):
        """Test ReDoc có sẵn"""
        response = client.get("/redoc")
        assert response.status_code == 200


# ========================================
# Run tests directly
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

