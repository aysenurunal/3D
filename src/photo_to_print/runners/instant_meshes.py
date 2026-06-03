from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..command import format_command, run_command


@dataclass(frozen=True)
class InstantMeshesOptions:
    input_mesh: Path
    output_mesh: Path
    binary: Path | None = None
    target_faces: int = 10000
    rosy: int = 4
    posy: int = 4
    crease: float = 30.0
    dry_run: bool = False


@dataclass(frozen=True)
class RunnerResult:
    message: str


def run_instant_meshes(options: InstantMeshesOptions) -> RunnerResult:
    input_mesh = options.input_mesh.resolve()
    output_mesh = options.output_mesh.resolve()

    if not input_mesh.exists() and not options.dry_run:
        raise FileNotFoundError(f"Input mesh does not exist: {input_mesh}")

    binary = _resolve_binary(options.binary, dry_run=options.dry_run)
    output_mesh.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(binary),
        "--output",
        str(output_mesh),
        "--faces",
        str(options.target_faces),
        "--rosy",
        str(options.rosy),
        "--posy",
        str(options.posy),
        "--crease",
        str(options.crease),
        str(input_mesh),
    ]

    if options.dry_run:
        return RunnerResult(f"Dry run Instant Meshes command: {format_command(command)}")

    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(
            "Instant Meshes command failed.\n"
            f"Command: {format_command(result.command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    if not output_mesh.exists():
        raise RuntimeError(f"Instant Meshes finished but did not create {output_mesh}")

    return RunnerResult(f"Remeshed asset: {output_mesh}")


def _resolve_binary(binary: Path | None, dry_run: bool = False) -> Path:
    if binary is None:
        env_value = os.environ.get("PHOTO_TO_PRINT_INSTANT_MESHES_BIN")
        if env_value:
            binary = Path(env_value)

    if binary:
        if dry_run:
            return binary
        binary = binary.resolve()
        if binary.exists():
            return binary
        raise FileNotFoundError(f"Instant Meshes binary does not exist: {binary}")

    for candidate in ("InstantMeshes", "instant-meshes", "Instant Meshes"):
        found = shutil.which(candidate)
        if found:
            return Path(found)

    if dry_run:
        return Path("InstantMeshes")

    raise FileNotFoundError("Instant Meshes binary was not found. Pass --instant-meshes-bin /path/to/InstantMeshes.")
