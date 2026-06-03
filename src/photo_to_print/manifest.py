from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PhotoRecord:
    source_path: str
    processed_path: str
    size_bytes: int
    sha256: str
    is_primary: bool = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, records: list[PhotoRecord], primary: PhotoRecord) -> None:
    payload: dict[str, Any] = {
        "primary_photo": primary.processed_path,
        "photos": [asdict(record) for record in records],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
