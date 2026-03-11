"""
Image storage routes — upload DJ profile images and serve them back.

These routes are PUBLIC (no API key required) because browser clients
upload their own logo without access to the server API key.

POST /images/upload   — accept a multipart image, save it, return its URL
GET  /images/{name}   — serve a stored image by filename
"""

import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from config import IMAGES_DIR, log

router = APIRouter(prefix="/images")

_ALLOWED_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/upload")
async def upload_image(file: UploadFile):
    """Accept an image file upload, persist it, and return its public path."""
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {content_type!r}. Must be a JPEG, PNG, GIF, WebP, or SVG.",
        )

    data = await file.read(_MAX_BYTES + 1)
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller.")

    ext = mimetypes.guess_extension(content_type) or ".bin"
    # Normalise common mis-mappings from Python's mime DB
    ext = {".jpe": ".jpg", ".jpeg": ".jpg"}.get(ext, ext)

    filename = f"{uuid.uuid4().hex}{ext}"
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    dest = IMAGES_DIR / filename
    dest.write_bytes(data)

    log.info("Image stored: %s (%d bytes)", filename, len(data))
    return {"url": f"/images/{filename}"}


@router.get("/{filename}")
async def get_image(filename: str):
    """Serve a stored image by filename."""
    # Prevent path traversal — only allow the bare filename portion
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    path = IMAGES_DIR / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found.")

    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(path, media_type=media_type or "application/octet-stream")
