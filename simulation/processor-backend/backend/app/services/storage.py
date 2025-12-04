import os
from uuid import uuid4
from typing import List
from fastapi import UploadFile

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_files_local(files: List[UploadFile], base_url: str) -> List[str]:
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
