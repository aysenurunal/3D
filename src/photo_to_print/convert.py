from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .command import format_command, render_command_template, run_command


@dataclass(frozen=True)
class ConvertResult:
    message: str


def convert_mesh(
    input_mesh: Path,
    output_mesh: Path,
    command_template: str | None = None,
    preset: str | None = None,
    dry_run: bool = False,
) -> ConvertResult:
    input_mesh = input_mesh.resolve()
    output_mesh = output_mesh.resolve()

    if not input_mesh.exists() and not dry_run:
        raise FileNotFoundError(f"Input mesh does not exist: {input_mesh}")

    command_template = command_template or _preset_template(preset) or _auto_template(input_mesh, output_mesh)

    if command_template:
        output_mesh.parent.mkdir(parents=True, exist_ok=True)
        command = render_command_template(command_template, input=input_mesh, output=output_mesh)
        if dry_run:
            return ConvertResult(f"Dry run mesh conversion command: {format_command(command)}")

        result = run_command(command)
        if result.returncode != 0:
            raise RuntimeError(
                "Mesh conversion command failed.\n"
                f"Command: {format_command(result.command)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        if not output_mesh.exists():
            raise RuntimeError(f"Mesh conversion command finished but did not create {output_mesh}")
        return ConvertResult(f"Converted mesh: {output_mesh}")

    if input_mesh.suffix.lower() == output_mesh.suffix.lower():
        if dry_run:
            return ConvertResult(f"Dry run mesh copy: {input_mesh} -> {output_mesh}")
        output_mesh.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_mesh, output_mesh)
        return ConvertResult(f"Copied mesh: {output_mesh}")

    raise ValueError(
        "No built-in converter is available for this format pair. "
        "Pass --command-template or use --preset blender/assimp."
    )


def _preset_template(preset: str | None) -> str | None:
    if not preset:
        return None
    if preset == "blender":
        return "blender --background --python scripts/blender_convert_mesh.py -- --input {input} --output {output}"
    if preset == "assimp":
        return "assimp export {input} {output}"
    raise ValueError(f"Unknown converter preset: {preset}")


def _auto_template(input_mesh: Path, output_mesh: Path) -> str | None:
    if input_mesh.suffix.lower() == output_mesh.suffix.lower():
        return None
    if shutil.which("blender"):
        return _preset_template("blender")
    if shutil.which("assimp"):
        return _preset_template("assimp")
    return None
