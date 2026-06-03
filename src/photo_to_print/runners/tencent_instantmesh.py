from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from ..command import format_command, run_command


@dataclass(frozen=True)
class TencentInstantMeshOptions:
    input_image: Path
    output_mesh: Path
    instantmesh_root: Path
    config: str = "configs/instant-mesh-large.yaml"
    output_dir: Path = Path("outputs/instantmesh")
    python_bin: str = "python"
    no_rembg: bool = False
    export_texmap: bool = False
    save_video: bool = False
    dry_run: bool = False


@dataclass(frozen=True)
class RunnerResult:
    message: str


def run_tencent_instantmesh(options: TencentInstantMeshOptions) -> RunnerResult:
    input_image = options.input_image.resolve()
    output_mesh = options.output_mesh.resolve()
    instantmesh_root = options.instantmesh_root.resolve()
    output_dir = options.output_dir.resolve()
    config_path = _resolve_config(instantmesh_root, options.config)

    if not options.dry_run:
        if not input_image.exists():
            raise FileNotFoundError(f"Input image does not exist: {input_image}")
        _validate_instantmesh_root(instantmesh_root, config_path)

    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        options.python_bin,
        str(instantmesh_root / "run.py"),
        str(config_path),
        str(input_image),
        "--output_path",
        str(output_dir),
    ]
    if options.no_rembg:
        command.append("--no_rembg")
    if options.export_texmap:
        command.append("--export_texmap")
    if options.save_video:
        command.append("--save_video")

    expected_mesh = _expected_mesh_path(output_dir, config_path, input_image)

    if options.dry_run:
        return RunnerResult(
            "Dry run TencentARC InstantMesh command: "
            f"{format_command(command)}\nExpected mesh: {expected_mesh}\nFinal mesh: {output_mesh}"
        )

    result = run_command(command, cwd=instantmesh_root)
    if result.returncode != 0:
        raise RuntimeError(
            "TencentARC InstantMesh command failed.\n"
            f"Command: {format_command(result.command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    if not expected_mesh.exists():
        raise RuntimeError(f"InstantMesh finished but did not create the expected mesh: {expected_mesh}")

    shutil.copy2(expected_mesh, output_mesh)
    return RunnerResult(f"Generated InstantMesh OBJ: {output_mesh}")


def _resolve_config(instantmesh_root: Path, config: str) -> Path:
    config_path = Path(config)
    if not config_path.is_absolute():
        config_path = instantmesh_root / config_path
    return config_path


def _validate_instantmesh_root(instantmesh_root: Path, config_path: Path) -> None:
    if not instantmesh_root.exists():
        raise FileNotFoundError(f"InstantMesh root does not exist: {instantmesh_root}")
    if not (instantmesh_root / "run.py").exists():
        raise FileNotFoundError(f"InstantMesh run.py was not found under: {instantmesh_root}")
    if not config_path.exists():
        raise FileNotFoundError(f"InstantMesh config does not exist: {config_path}")


def _expected_mesh_path(output_dir: Path, config_path: Path, input_image: Path) -> Path:
    config_name = config_path.stem
    input_name = input_image.stem
    return output_dir / config_name / "meshes" / f"{input_name}.obj"
