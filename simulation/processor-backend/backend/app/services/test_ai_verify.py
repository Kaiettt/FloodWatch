# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import os
from ai_verify import ai_verify_image

# Đường dẫn folder uploads tương đối với file script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/services
UPLOADS_DIR = os.path.join(BASE_DIR, "../static/uploads")  # đi lên 1 cấp → static/uploads

# Lấy danh sách ảnh
image_files = [f for f in os.listdir(UPLOADS_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

print(f"Found {len(image_files)} images.")

for img_file in image_files:
    img_path = os.path.join(UPLOADS_DIR, img_file)
    print(f"\nProcessing: {img_file}")
    result = ai_verify_image(img_path)
    print(result)