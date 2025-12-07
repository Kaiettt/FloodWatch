import os
import io
from uuid import uuid4
from typing import List, Tuple
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")

# ✅ File validation constants
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES = 5  # Maximum number of files per upload

def ensure_upload_dir():
    """Create upload directory if not exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file_extension(filename: str) -> str:
    """Validate and return file extension."""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400, 
            f"Invalid file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext

def save_files_local(files: List[UploadFile], base_url: str) -> List[str]:
    """
    Save uploaded files to local storage.
    Basic version without validation (backward compatible).
    """
    ensure_upload_dir()
    urls = []
    for f in files:
        ext = os.path.splitext(f.filename)[1] or ".jpg"
        filename = f"{uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as out:
            out.write(f.file.read())
        urls.append(f"{base_url}/static/uploads/{filename}")
    return urls

async def validate_and_save_files(
    files: List[UploadFile], 
    base_url: str
) -> Tuple[List[str], List[str]]:
    """
    ✅ NEW: Validate and save files with proper checks.
    
    Returns:
        Tuple of (successful_urls, error_messages)
    """
    ensure_upload_dir()
    
    # Check max files
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Too many files. Maximum allowed: {MAX_FILES}")
    
    urls = []
    errors = []
    
    for f in files:
        try:
            # 1. Validate extension
            ext = validate_file_extension(f.filename)
            
            # 2. Read content
            content = await f.read()
            
            # 3. Check size
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{f.filename}: File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")
                continue
            
            # 4. Verify it's a real image
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(content))
                img.verify()
            except Exception:
                errors.append(f"{f.filename}: Invalid or corrupted image")
                continue
            
            # 5. Save file
            filename = f"{uuid4().hex}{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            with open(filepath, "wb") as out:
                out.write(content)
            
            urls.append(f"{base_url}/static/uploads/{filename}")
            
        except HTTPException:
            raise
        except Exception as e:
            errors.append(f"{f.filename}: {str(e)}")
    
    return urls, errors

def delete_file(filename: str) -> bool:
    """Delete a file from upload directory."""
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception:
        return False

def get_file_size(filename: str) -> int:
    """Get file size in bytes."""
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        return os.path.getsize(filepath)
    except Exception:
        return 0
