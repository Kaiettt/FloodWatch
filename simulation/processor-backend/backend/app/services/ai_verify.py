# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

from ultralytics import YOLO
import cv2
import numpy as np

# ----------------------------
# LOAD MODELS
# ----------------------------
obj_model = YOLO("yolov8x.pt")        # best object detection
seg_model = YOLO("yolov8s-seg.pt")    # flood segmentation

# ----------------------------
# PARAMETERS
# ----------------------------
TARGET_CLASSES = {0: "person", 1: "bicycle", 2: "car", 3: "motorbike", 5: "bus"}
CLASS_COLORS = {
    "person": (0, 255, 0),
    "bicycle": (255, 165, 0),
    "car": (0, 0, 255),
    "motorbike": (255, 0, 255),
    "bus": (0, 255, 255)
}
CONF_THRESHOLD = 0.5
FLOOD_RATIO_MIN = 0.03

# ----------------------------
# COMBINED DETECTION FUNCTION
# ----------------------------
def detect_flood_and_objects(file_obj=None, image_path=None):
    # Load image
    if file_obj:
        file_bytes = np.frombuffer(file_obj.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    elif image_path:
        img = cv2.imread(image_path)
    else:
        raise ValueError("Provide file_obj or image_path")
    
    if img is None:
        raise ValueError("Cannot read image")
    
    h, w = img.shape[:2]

    # ----------------------------
    # OBJECT DETECTION
    # ----------------------------
    detected_objects = []
    results = obj_model(img)[0]

    for box in results.boxes:
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        if conf >= CONF_THRESHOLD and cls in TARGET_CLASSES:
            label = TARGET_CLASSES[cls]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detected_objects.append({"label": label, "confidence": round(conf, 3), "bbox": [x1, y1, x2, y2]})
            
            # Draw box
            color = CLASS_COLORS[label]
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
            cv2.putText(img, f"{label} {conf:.2f}", (int(x1), int(y1)-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # ----------------------------
    # FLOOD SEGMENTATION
    # ----------------------------
    flood_detected = False
    flood_ratio = 0
    final_mask = None

    seg_results = seg_model(img)[0]
    if hasattr(seg_results, 'masks') and seg_results.masks is not None:
        raw_mask = seg_results.masks.data[0].cpu().numpy()
        raw_mask = cv2.resize(raw_mask, (w, h))
        mask = (raw_mask > 0.5).astype(np.uint8) * 255

        # Morphology
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        flood_ratio = np.sum(mask > 0) / mask.size
        if flood_ratio >= FLOOD_RATIO_MIN:
            flood_detected = True
            final_mask = mask
            # Overlay flood
            color = np.array([255, 0, 0], dtype=np.uint8)  # blue
            img[final_mask > 0] = (0.3*img[final_mask > 0].astype(np.float32) + 0.7*color.astype(np.float32)).astype(np.uint8)

    return flood_detected

