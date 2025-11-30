from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from functools import wraps
import hashlib
import os
from PIL import Image, ExifTags
import imagehash
from typing import Dict, Tuple, Optional
import io

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# In-memory storage for image hashes (in production, use Redis or a database)
image_hashes = set()

def get_image_hash(image_data: bytes) -> str:
    """Generate a perceptual hash for an image."""
    try:
        image = Image.open(io.BytesIO(image_data))
        # Convert to grayscale and resize to ensure consistent hashing
        image = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
        img_hash = imagehash.average_hash(image)
        return str(img_hash)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing image: {str(e)}"
        )

def is_duplicate_image(image_data: bytes) -> bool:
    """Check if an image is a duplicate by comparing its hash with stored hashes."""
    img_hash = get_image_hash(image_data)
    if img_hash in image_hashes:
        return True
    image_hashes.add(img_hash)
    return False

def extract_gps_metadata(image_data: bytes) -> Optional[Dict[str, float]]:
    """Extract GPS metadata from image if available."""
    try:
        image = Image.open(io.BytesIO(image_data))
        exif_data = {}
        if hasattr(image, '_getexif') and image._getexif() is not None:
            exif_data = {
                ExifTags.TAGS[k]: v
                for k, v in image._getexif().items()
                if k in ExifTags.TAGS
            }
        
        if 'GPSInfo' not in exif_data:
            return None
            
        gps_info = {}
        for key in exif_data['GPSInfo'].keys():
            decode = ExifTags.GPSTAGS.get(key, key)
            gps_info[decode] = exif_data['GPSInfo'][key]

        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)

        lat = convert_to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef'] != 'N':
            lat = -lat

        lon = convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef'] != 'E':
            lon = -lon

        return {"latitude": lat, "longitude": lon}
        
    except Exception:
        return None
