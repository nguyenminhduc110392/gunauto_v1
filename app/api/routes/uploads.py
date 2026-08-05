from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.projects import UploadResponse
from app.services.storage import safe_filename

router = APIRouter(prefix="/uploads", tags=["uploads"])
settings = get_settings()


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(file: UploadFile = File(...)) -> UploadResponse:
    filename = f"{uuid.uuid4().hex}-{safe_filename(file.filename or 'upload.bin')}"
    target = settings.uploads_dir / filename
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return UploadResponse(
        uri=target.as_posix(),
        original_filename=file.filename or filename,
        size_bytes=size,
        content_type=file.content_type,
    )
