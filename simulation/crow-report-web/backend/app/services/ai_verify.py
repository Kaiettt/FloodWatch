import os
import cv2
import numpy as np
import requests
from ultralytics import YOLO

# ----------------------------
# PATH MODELS
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/app
MODELS_DIR = os.path.join(BASE_DIR, "models")
OBJ_MODEL_PATH = os.path.join(MODELS_DIR, "yolov8x.pt")
SEG_MODEL_PATH = os.path.join(MODELS_DIR, "yolov8s-seg.pt")

os.makedirs(MODELS_DIR, exist_ok=True)

# ----------------------------
# GOOGLE DRIVE RAW LINKS
# ----------------------------
OBJ_MODEL_URL = "https://drive.google.com/uc?export=download&id=1uDrYV5t3jaVGocA2lgdMXZQtlJklw-h2"
SEG_MODEL_URL = "https://drive.google.com/uc?export=download&id=1dJy7AvwsIzfuRbI5v7Ku7QNEds8SgUd5"

# ----------------------------
# DOWNLOAD IF MISSING
# ----------------------------
def download_model(url, path):
    if not os.path.exists(path):
        session = requests.Session()
        r = session.get(url, stream=True)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

download_model(OBJ_MODEL_URL, OBJ_MODEL_PATH)
download_model(SEG_MODEL_URL, SEG_MODEL_PATH)

# ----------------------------
# LOAD YOLO MODELS
# ----------------------------
OBJ_MODEL = YOLO(OBJ_MODEL_PATH)
SEG_MODEL = YOLO(SEG_MODEL_PATH)

# ----------------------------
# PARAMETERS
# ----------------------------
TARGET_CLASSES = {0: "person", 1: "bicycle", 2: "car", 3: "motorbike", 5: "bus", 7: "truck"}
CONF_THRESHOLD = 0.35
FLOOD_RATIO_MIN = 0.15  # threshold flood ratio
MASK_THRESHOLD = 0.7    # threshold mask

CLASS_COLORS = {
    "person": (0, 255, 0),
    "bicycle": (255, 165, 0),
    "car": (0, 0, 255),
    "motorbike": (255, 0, 255),
    "bus": (0, 255, 255),
    "truck": (128, 0, 128)
}
FLOOD_COLOR = np.array([255, 0, 0], dtype=np.uint8)

# ----------------------------
# HELPERS
# ----------------------------
def preprocess_street_image(img):
    """
    Tăng contrast + Gaussian blur để cải thiện detection
    """
    img = cv2.convertScaleAbs(img, alpha=1.2, beta=8)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    return img

def filter_small_regions(mask, min_area=2000):
    """
    Loại bỏ các vùng nhỏ < min_area
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    clean_mask = np.zeros_like(mask)
    for i in range(1, num_labels):  # skip background
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            clean_mask[labels == i] = 255
    return clean_mask

# ----------------------------
# MAIN FUNCTION
# ----------------------------
def ai_verify_image(local_path: str) -> dict:
    """
    Nhận path ảnh, trả về dict:
    {
        "flood_detected": bool,
        "flood_ratio": float,
        "objects": list[{"label": str, "confidence": float, "box": [x1,y1,x2,y2]}]
    }
    """
    img = cv2.imread(local_path)
    if img is None:
        return {"error": "Cannot load image"}

    orig_img = img.copy()
    img = preprocess_street_image(img)
    h, w = img.shape[:2]

    # ----------------------------
    # OBJECT DETECTION
    # ----------------------------
    detected = []
    results = OBJ_MODEL(img)[0]
    for box in results.boxes:
        conf = float(box.conf[0]) if hasattr(box.conf, "__len__") else float(box.conf)
        cls = int(box.cls[0]) if hasattr(box.cls, "__len__") else int(box.cls)
        if conf < CONF_THRESHOLD or cls not in TARGET_CLASSES:
            continue
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        detected.append({
            "label": TARGET_CLASSES[cls],
            "confidence": round(conf, 3),
            "box": [x1, y1, x2, y2]
        })
        color = CLASS_COLORS[TARGET_CLASSES[cls]]
        cv2.rectangle(orig_img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(orig_img, f"{TARGET_CLASSES[cls]} {conf:.2f}", (x1, y1-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # ----------------------------
    # FLOOD SEGMENTATION
    # ----------------------------
    seg_results = SEG_MODEL(local_path)[0]
    flood_detected = False
    flood_ratio = 0.0

    if seg_results.masks is not None:
        # (N, H, W) boolean mask
        masks = seg_results.masks.data.cpu().numpy()
        combined = np.any(masks > MASK_THRESHOLD, axis=0).astype(np.uint8) * 255

        # Morphology mạnh hơn để loại bỏ noise
        kernel = np.ones((5, 5), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

        # Resize mask về kích thước ảnh gốc
        combined_resized = cv2.resize(combined, (w, h), interpolation=cv2.INTER_NEAREST)

        # Lọc vùng nhỏ
        clean_mask = filter_small_regions(combined_resized, min_area=2000)
        mask_bool = clean_mask > 0

        # ----------------------------
        # Cải tiến giảm false positive
        # 1. Loại bỏ vùng quá sáng/tối không phải nước
        gray = cv2.cvtColor(orig_img, cv2.COLOR_BGR2GRAY)
        mask_valid = (gray > 50) & (gray < 200)  # chỉ giữ vùng trung bình sáng
        mask_bool = mask_bool & mask_valid

        # 2. Chỉ kiểm tra nửa dưới ảnh
        mask_upper = np.zeros_like(mask_bool)
        mask_upper[int(h/2):, :] = mask_bool[int(h/2):, :]
        mask_bool = mask_upper

        # 3. Cập nhật flood ratio & detected
        flood_ratio = float(np.sum(mask_bool) / (h * w))
        flood_detected = flood_ratio >= FLOOD_RATIO_MIN

        # Overlay trực quan
        orig_img[mask_bool] = (
            0.3 * orig_img[mask_bool].astype(np.float32) +
            0.7 * FLOOD_COLOR.astype(np.float32)
        ).astype(np.uint8)

    return {
        "flood_detected": flood_detected,
        "flood_ratio": flood_ratio,
        "objects": detected
    }