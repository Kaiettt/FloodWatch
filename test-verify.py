# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import cv2
import numpy as np
from typing import List
from ultralytics import YOLO

# Load YOLOv8 segmentation model
model = YOLO("yolov8n-seg.pt")  # segmentation model

# Reference heights in meters
REFERENCE_HEIGHTS = {
    "person": 1.9,
    "car": 1.5,
    "bus": 3.0,
    "motorcycle": 0.6
}

# COCO classes mapping
COCO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Max plausible flood height
MAX_WATER_HEIGHT_M = 2.0

def is_flood_image(image_path: str) -> bool:
    """
    Returns True if the image contains flood, False otherwise.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False

    preds = model.predict(img, verbose=False)[0]
    masks = preds.masks.data if hasattr(preds, "masks") else None

    objects_detected = []
    if masks is not None:
        for i, cls_id in enumerate(preds.boxes.cls):
            cls_id = int(cls_id)
            if cls_id in COCO_CLASSES:
                objects_detected.append({
                    "class": COCO_CLASSES[cls_id],
                    "box": preds.boxes.xyxy[i].cpu().numpy()
                })

    # Determine reference object
    reference_obj = None
    for ref_class in ["person", "bus", "car", "motorcycle"]:
        objs = [o for o in objects_detected if o["class"] == ref_class]
        if objs:
            reference_obj = max(objs, key=lambda o: o["box"][3]-o["box"][1])
            reference_height_m = REFERENCE_HEIGHTS[ref_class]
            break

    if reference_obj is None:
        return False  # Cannot estimate water without reference object

    ref_box = reference_obj["box"]
    ref_pixel_height = ref_box[3] - ref_box[1]

    # Waterline detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    foot_y = int(ref_box[3])
    water_rows = np.where(thresh[foot_y:, :] > 0)[0]

    if len(water_rows) > 0:
        water_pixel_height = water_rows[0]
        estimated_water_height_m = reference_height_m * (water_pixel_height / ref_pixel_height)
        if estimated_water_height_m > 0.05 and estimated_water_height_m <= MAX_WATER_HEIGHT_M:
            return True
    return False


# --- Example usage ---
if __name__ == "__main__":
    test_images = ["967d02b0-4b1b-11ef-93ae-c1821394f93d.jpg"]
    for img_path in test_images:
        flood = is_flood_image(img_path)
        print(f"{img_path}: Flood detected? {flood}")
