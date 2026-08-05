from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from app.core.config import get_settings

settings = get_settings()
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = _SAFE_NAME.sub("_", name).strip("._")
    return cleaned or f"upload-{uuid.uuid4().hex}"


def project_directory(project_id: uuid.UUID) -> Path:
    path = settings.projects_dir / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text_artifact(project_id: uuid.UUID, filename: str, content: str) -> str:
    path = project_directory(project_id) / safe_filename(filename)
    path.write_text(content, encoding="utf-8")
    return path.as_posix()


def write_json_artifact(project_id: uuid.UUID, filename: str, payload: Any) -> str:
    return write_text_artifact(project_id, filename, json.dumps(payload, ensure_ascii=False, indent=2))
