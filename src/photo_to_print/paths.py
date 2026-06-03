from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    input_photos: Path
    processed: Path
    instantmesh_outputs: Path
    raw_outputs: Path
    printable_outputs: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        root = root.resolve()
        return cls(
            root=root,
            input_photos=root / "data" / "input_photos",
            processed=root / "data" / "processed",
            instantmesh_outputs=root / "outputs" / "instantmesh",
            raw_outputs=root / "outputs" / "raw",
            printable_outputs=root / "outputs" / "printable",
        )


def ensure_project_dirs(paths: ProjectPaths) -> None:
    for directory in (
        paths.input_photos,
        paths.processed,
        paths.instantmesh_outputs,
        paths.raw_outputs,
        paths.printable_outputs,
    ):
        directory.mkdir(parents=True, exist_ok=True)
        keep_file = directory / ".gitkeep"
        keep_file.touch(exist_ok=True)
