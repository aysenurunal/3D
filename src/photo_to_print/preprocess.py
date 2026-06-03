from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .manifest import PhotoRecord, sha256_file, write_manifest

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class PreprocessResult:
    photos: list[PhotoRecord]
    primary_photo: PhotoRecord
    manifest_path: Path


def preprocess_photos(
    input_dir: Path,
    output_dir: Path,
    primary_strategy: str = "largest-file",
    primary_name: str | None = None,
) -> PreprocessResult:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input photo directory does not exist: {input_dir}")

    sources = sorted(
        path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )
    if not sources:
        allowed = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ValueError(f"No supported image files found in {input_dir}. Supported extensions: {allowed}")

    output_dir.mkdir(parents=True, exist_ok=True)
    selected_primary = _select_primary(sources, primary_strategy, primary_name)

    records: list[PhotoRecord] = []
    primary_record: PhotoRecord | None = None
    for index, source in enumerate(sources, start=1):
        normalized_name = f"{index:02d}_{_safe_stem(source.stem)}{source.suffix.lower()}"
        destination = output_dir / normalized_name
        shutil.copy2(source, destination)

        record = PhotoRecord(
            source_path=str(source),
            processed_path=str(destination),
            size_bytes=destination.stat().st_size,
            sha256=sha256_file(destination),
            is_primary=source == selected_primary,
        )
        records.append(record)
        if record.is_primary:
            primary_record = record

    if primary_record is None:
        raise RuntimeError("Failed to mark a primary photo.")

    manifest_path = output_dir / "manifest.json"
    write_manifest(manifest_path, records, primary_record)
    return PreprocessResult(photos=records, primary_photo=primary_record, manifest_path=manifest_path)


def _select_primary(sources: list[Path], strategy: str, primary_name: str | None) -> Path:
    if primary_name:
        for source in sources:
            if source.name == primary_name:
                return source
        raise ValueError(f"Primary photo {primary_name!r} was not found in the input set.")

    if strategy == "first":
        return sources[0]
    if strategy == "largest-file":
        return max(sources, key=lambda path: path.stat().st_size)
    raise ValueError(f"Unsupported primary strategy: {strategy}")


def _safe_stem(value: str) -> str:
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        elif char in {"-", "_"}:
            safe.append(char)
        else:
            safe.append("-")
    normalized = "".join(safe).strip("-")
    return normalized or "photo"
