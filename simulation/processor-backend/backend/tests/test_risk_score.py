# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

"""
Unit Tests cho Risk Score Calculation
======================================
Kiểm tra logic tính điểm rủi ro (risk score) cho báo cáo từ cộng đồng.

Chạy tests:
    cd simulation/processor-backend/backend
    pytest tests/ -v
"""

import pytest
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import calculate_crowd_risk_score


class TestRiskScoreCalculation:
    """Test class cho calculate_crowd_risk_score function."""
    
    # ========================================
    # Basic Risk Score Tests
    # ========================================
    
    def test_risk_score_low_water_level(self):
        """Mức nước thấp -> Risk score thấp"""
        score, level, factors = calculate_crowd_risk_score(water_level=0.1)
        assert score < 0.35
        assert level == "Low"
    
    def test_risk_score_moderate_water_level(self):
        """Mức nước trung bình -> Risk score trung bình"""
        score, level, factors = calculate_crowd_risk_score(water_level=0.4)
        assert 0.35 <= score <= 0.55
        assert level in ["Low", "Moderate"]
    
    def test_risk_score_high_water_level(self):
        """Mức nước cao -> Risk score cao"""
        score, level, factors = calculate_crowd_risk_score(water_level=0.9)
        assert score > 0.5
        assert level in ["High", "Severe"]
    
    def test_risk_score_severe_water_level(self):
        """Mức nước rất cao -> Risk score rất cao"""
        score, level, factors = calculate_crowd_risk_score(water_level=1.5)
        assert score > 0.65
        assert level in ["High", "Severe"]
    
    # ========================================
    # Description/Text Tests
    # ========================================
    
    def test_risk_score_with_danger_keywords_vietnamese(self):
        """Keywords nguy hiểm tiếng Việt tăng risk score"""
        # Không có keywords
        score1, _, _ = calculate_crowd_risk_score(
            water_level=0.3, 
            description="Đường có nước"
        )
        
        # Có keywords nguy hiểm
        score2, _, _ = calculate_crowd_risk_score(
            water_level=0.3,
            description="Ngập sâu, rất nguy hiểm, xe không qua được"
        )
        
        assert score2 > score1
    
    def test_risk_score_with_danger_keywords_english(self):
        """Keywords nguy hiểm tiếng Anh tăng risk score"""
        score1, _, _ = calculate_crowd_risk_score(
            water_level=0.3,
            description="Some water on the road"
        )
        
        score2, _, _ = calculate_crowd_risk_score(
            water_level=0.3,
            description="Severe flooding, very dangerous, emergency"
        )
        
        assert score2 > score1
    
    def test_risk_score_long_description_higher(self):
        """Mô tả dài hơn -> risk score cao hơn (có nhiều thông tin)"""
        score1, _, _ = calculate_crowd_risk_score(
            water_level=0.3,
            description="Ngập"
        )
        
        score2, _, _ = calculate_crowd_risk_score(
            water_level=0.3,
            description="Đường Nguyễn Hữu Cảnh ngập khá sâu, nước chảy mạnh, xe máy khó di chuyển"
        )
        
        assert score2 > score1
    
    # ========================================
    # Photo Evidence Tests
    # ========================================
    
    def test_risk_score_with_photos(self):
        """Có ảnh -> tăng độ tin cậy và risk score"""
        score1, _, factors1 = calculate_crowd_risk_score(
            water_level=0.4,
            photos=[]
        )
        
        score2, _, factors2 = calculate_crowd_risk_score(
            water_level=0.4,
            photos=["photo1.jpg", "photo2.jpg"]
        )
        
        assert score2 > score1
        assert factors2["photoFactor"] > factors1["photoFactor"]
    
    def test_risk_score_photo_factor_caps(self):
        """Photo factor có giới hạn tối đa"""
        _, _, factors = calculate_crowd_risk_score(
            water_level=0.4,
            photos=["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg", "p5.jpg", "p6.jpg"]
        )
        
        # Photo factor max = 1.0
        assert factors["photoFactor"] <= 1.0
    
    # ========================================
    # Verified Status Tests
    # ========================================
    
    def test_risk_score_verified_higher(self):
        """Báo cáo đã xác minh -> risk score cao hơn"""
        score1, _, _ = calculate_crowd_risk_score(
            water_level=0.4,
            verified=False
        )
        
        score2, _, _ = calculate_crowd_risk_score(
            water_level=0.4,
            verified=True
        )
        
        assert score2 > score1
    
    # ========================================
    # Risk Level Classification Tests
    # ========================================
    
    def test_risk_level_low(self):
        """Risk level = Low khi score <= 0.35"""
        score, level, _ = calculate_crowd_risk_score(water_level=0.05)
        assert level == "Low"
    
    def test_risk_level_moderate(self):
        """Risk level = Moderate khi 0.35 < score <= 0.55"""
        # Tạo điều kiện để score nằm trong khoảng 0.35-0.55
        score, level, _ = calculate_crowd_risk_score(
            water_level=0.35,
            description="Có nước trên đường, cần lưu ý khi di chuyển",
            photos=["photo.jpg"]
        )
        # Score should be around 0.4-0.5
        if 0.35 < score <= 0.55:
            assert level == "Moderate"
    
    def test_risk_level_high(self):
        """Risk level = High khi 0.55 < score <= 0.75"""
        score, level, _ = calculate_crowd_risk_score(
            water_level=0.6,
            description="Ngập nghiêm trọng, nguy hiểm",
            photos=["p1.jpg", "p2.jpg"],
            verified=True
        )
        assert level in ["High", "Severe"]
    
    def test_risk_level_severe(self):
        """Risk level = Severe khi score > 0.75"""
        score, level, _ = calculate_crowd_risk_score(
            water_level=1.2,
            description="Ngập rất sâu, cực kỳ nguy hiểm, cần cứu hộ khẩn cấp",
            photos=["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg"],
            verified=True
        )
        assert level == "Severe"
    
    # ========================================
    # Factors Dictionary Tests
    # ========================================
    
    def test_factors_contain_all_keys(self):
        """Kiểm tra factors dict có đầy đủ keys"""
        _, _, factors = calculate_crowd_risk_score(water_level=0.5)
        
        required_keys = [
            "waterLevelFactor",
            "textSeverityFactor", 
            "photoFactor",
            "verifiedFactor",
            "keywordMatches"
        ]
        
        for key in required_keys:
            assert key in factors
    
    def test_factors_values_in_range(self):
        """Kiểm tra các factor values nằm trong khoảng hợp lệ"""
        _, _, factors = calculate_crowd_risk_score(
            water_level=0.5,
            description="Test ngập",
            photos=["p.jpg"],
            verified=True
        )
        
        assert 0 <= factors["waterLevelFactor"] <= 1
        assert 0 <= factors["textSeverityFactor"] <= 1
        assert 0 <= factors["photoFactor"] <= 1
        assert factors["keywordMatches"] >= 0
    
    # ========================================
    # Score Bounds Tests
    # ========================================
    
    def test_score_bounds_minimum(self):
        """Risk score không âm"""
        score, _, _ = calculate_crowd_risk_score(water_level=0)
        assert score >= 0
    
    def test_score_bounds_maximum(self):
        """Risk score không vượt quá 1"""
        score, _, _ = calculate_crowd_risk_score(
            water_level=5.0,  # Rất cao
            description="nguy hiểm nghiêm trọng ngập sâu khẩn cấp cứu hộ",
            photos=["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg", "p5.jpg"],
            verified=True
        )
        assert score <= 1.0


class TestCoordinateValidation:
    """Test coordinate validation function."""
    
    def test_validate_coordinates_vietnam(self):
        """Tọa độ trong Việt Nam -> valid"""
        from app.main import validate_coordinates
        
        # TP.HCM
        assert validate_coordinates(10.762622, 106.660172) == True
        
        # Hà Nội
        assert validate_coordinates(21.0285, 105.8542) == True
        
        # Đà Nẵng
        assert validate_coordinates(16.0544, 108.2022) == True
    
    def test_validate_coordinates_outside_vietnam(self):
        """Tọa độ ngoài Việt Nam -> invalid"""
        from app.main import validate_coordinates
        
        # Singapore
        assert validate_coordinates(1.3521, 103.8198) == False
        
        # Tokyo
        assert validate_coordinates(35.6762, 139.6503) == False
    
    def test_validate_coordinates_null_values(self):
        """Tọa độ None -> invalid"""
        from app.main import validate_coordinates
        
        assert validate_coordinates(None, 106.66) == False
        assert validate_coordinates(10.76, None) == False
        assert validate_coordinates(None, None) == False
    
    def test_validate_coordinates_gps_default(self):
        """Tọa độ (0, 0) - GPS default -> invalid"""
        from app.main import validate_coordinates
        
        assert validate_coordinates(0.0, 0.0) == False


# ========================================
# Run tests directly
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

