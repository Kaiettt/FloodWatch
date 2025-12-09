# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

"""
Unit Tests cho Severity Calculation
====================================
Kiểm tra logic tính mức độ nghiêm trọng (severity) của ngập lụt.

Chạy tests:
    cd simulation/processor-backend/backend
    pytest tests/ -v
"""

import pytest
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import compute_flood_severity


class TestSeverityCalculation:
    """Test class cho compute_flood_severity function."""
    
    # ========================================
    # Basic Severity Tests (Water Level Only)
    # ========================================
    
    def test_severity_low_under_10cm(self):
        """Mức nước < 10cm -> Low"""
        assert compute_flood_severity(0.05) == "Low"
        assert compute_flood_severity(0.1) == "Low"
    
    def test_severity_low_under_20cm(self):
        """Mức nước 10-20cm -> Low"""
        assert compute_flood_severity(0.15) == "Low"
        assert compute_flood_severity(0.19) == "Low"
    
    def test_severity_moderate_20_to_50cm(self):
        """Mức nước 20-50cm -> Moderate"""
        assert compute_flood_severity(0.2) == "Moderate"
        assert compute_flood_severity(0.3) == "Moderate"
        assert compute_flood_severity(0.49) == "Moderate"
    
    def test_severity_high_50_to_100cm(self):
        """Mức nước 50-100cm -> High"""
        assert compute_flood_severity(0.5) == "High"
        assert compute_flood_severity(0.7) == "High"
        assert compute_flood_severity(0.99) == "High"
    
    def test_severity_severe_over_100cm(self):
        """Mức nước > 100cm -> Severe"""
        assert compute_flood_severity(1.0) == "Severe"
        assert compute_flood_severity(1.5) == "Severe"
        assert compute_flood_severity(2.0) == "Severe"
    
    # ========================================
    # Edge Cases
    # ========================================
    
    def test_severity_zero_water_level(self):
        """Mức nước = 0 -> Low"""
        assert compute_flood_severity(0) == "Low"
        assert compute_flood_severity(0.0) == "Low"
    
    def test_severity_boundary_values(self):
        """Test các giá trị biên"""
        # Boundary: 0.2m
        assert compute_flood_severity(0.199) == "Low"
        assert compute_flood_severity(0.2) == "Moderate"
        
        # Boundary: 0.5m
        assert compute_flood_severity(0.499) == "Moderate"
        assert compute_flood_severity(0.5) == "High"
        
        # Boundary: 1.0m
        assert compute_flood_severity(0.999) == "High"
        assert compute_flood_severity(1.0) == "Severe"
    
    # ========================================
    # Threshold Tests
    # ========================================
    
    def test_severity_with_threshold_upgrade(self):
        """Khi vượt ngưỡng cảnh báo địa phương, nâng severity"""
        # Mức nước 0.3m (bình thường = Moderate)
        # Nhưng threshold = 0.25m -> nâng lên High
        result = compute_flood_severity(0.3, threshold=0.25)
        assert result == "High"
    
    def test_severity_threshold_no_effect_on_high(self):
        """Threshold không ảnh hưởng khi đã High/Severe"""
        # Mức nước 0.6m đã là High, threshold không thay đổi
        assert compute_flood_severity(0.6, threshold=0.5) == "High"
        assert compute_flood_severity(1.2, threshold=0.5) == "Severe"
    
    def test_severity_threshold_zero_or_none(self):
        """Threshold = 0 hoặc None không ảnh hưởng"""
        assert compute_flood_severity(0.3, threshold=0) == "Moderate"
        assert compute_flood_severity(0.3, threshold=None) == "Moderate"
    
    # ========================================
    # Trend Tests (Xu hướng tăng)
    # ========================================
    
    def test_severity_with_rising_trend(self):
        """Xu hướng tăng > 5cm/h -> nâng 1 bậc severity"""
        # Mức nước 0.3m = Moderate, nhưng đang tăng 6cm/h
        result = compute_flood_severity(0.3, trend=0.06)
        assert result == "High"
    
    def test_severity_with_fast_rising_trend(self):
        """Xu hướng tăng > 10cm/h -> có thể nâng 2 bậc"""
        # Mức nước 0.15m = Low, nhưng đang tăng 12cm/h
        result = compute_flood_severity(0.15, trend=0.12)
        assert result == "Moderate"  # Low -> Moderate (nâng 1 bậc do > 5cm/h)
    
    def test_severity_trend_no_effect_when_severe(self):
        """Trend không nâng quá Severe"""
        # Đã Severe, trend không thể nâng thêm
        assert compute_flood_severity(1.5, trend=0.15) == "Severe"
    
    def test_severity_small_trend_no_effect(self):
        """Trend < 5cm/h không ảnh hưởng"""
        assert compute_flood_severity(0.3, trend=0.03) == "Moderate"
        assert compute_flood_severity(0.3, trend=0.04) == "Moderate"
    
    # ========================================
    # Combined Tests (Threshold + Trend)
    # ========================================
    
    def test_severity_combined_factors(self):
        """Test kết hợp threshold và trend"""
        # Mức nước 0.25m (Low/Moderate boundary)
        # + Threshold 0.2m (vượt ngưỡng)
        # + Trend 0.08 (tăng nhanh)
        result = compute_flood_severity(0.25, threshold=0.2, trend=0.08)
        # Moderate (từ threshold) -> High (từ trend)
        assert result == "High"


class TestSeverityFromLevel:
    """Test backward compatibility function."""
    
    def test_severity_from_level_wrapper(self):
        """Test wrapper function hoạt động đúng"""
        from app.main import severity_from_level
        
        assert severity_from_level(0.1, 0.5) == "Low"
        assert severity_from_level(0.3, 0.5) == "Moderate"
        assert severity_from_level(0.6, 0.5) == "High"
        assert severity_from_level(1.2, 0.5) == "Severe"


# ========================================
# Run tests directly
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

