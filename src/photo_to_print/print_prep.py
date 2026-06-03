from __future__ import annotations

import json
import shutil
from importlib.util import find_spec
from dataclasses import asdict, dataclass
from pathlib import Path

from .command import format_command, render_command_template, run_command
from .obj_mesh import build_report, read_obj, write_ascii_stl


@dataclass(frozen=True)
class PrintPrepResult:
    message: str
    report_path: Path | None = None


def prepare_for_print(
    input_mesh: Path,
    output_mesh: Path,
    report_path: Path | None = None,
    repair_command_template: str | None = None,
    backend: str = "auto",
    scale: float | None = None,
    target_max_dimension_mm: float | None = None,
    require_watertight: bool = False,
    min_wall_thickness_mm: float | None = None,
    dry_run: bool = False,
) -> PrintPrepResult:
    input_mesh = input_mesh.resolve()
    output_mesh = output_mesh.resolve()
    report_path = report_path.resolve() if report_path else output_mesh.with_suffix(".report.json")

    if not input_mesh.exists() and not dry_run:
        raise FileNotFoundError(f"Input mesh does not exist: {input_mesh}")

    if repair_command_template:
        output_mesh.parent.mkdir(parents=True, exist_ok=True)
        command = render_command_template(
            repair_command_template,
            input=input_mesh,
            output=output_mesh,
            report=report_path,
        )
        if dry_run:
            return PrintPrepResult(f"Dry run repair command: {format_command(command)}", report_path=None)

        result = run_command(command)
        if result.returncode != 0:
            raise RuntimeError(
                "Repair command failed.\n"
                f"Command: {format_command(result.command)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        if not output_mesh.exists():
            raise RuntimeError(f"Repair command finished but did not create {output_mesh}")
        return PrintPrepResult(f"Prepared printable mesh with external repair command: {output_mesh}", report_path)

    if scale is not None and target_max_dimension_mm is not None:
        raise ValueError("Use either --scale or --target-max-dimension-mm, not both.")

    if backend not in {"auto", "builtin", "trimesh"}:
        raise ValueError(f"Unsupported print-prep backend: {backend}")

    has_trimesh = find_spec("trimesh") is not None
    if backend == "trimesh" and not has_trimesh:
        raise RuntimeError("The trimesh backend is not installed. Install with: pip install -e '.[mesh]'")

    if backend == "trimesh" or (backend == "auto" and has_trimesh):
        return _prepare_with_trimesh(
            input_mesh=input_mesh,
            output_mesh=output_mesh,
            report_path=report_path,
            scale=scale,
            target_max_dimension_mm=target_max_dimension_mm,
            require_watertight=require_watertight,
            min_wall_thickness_mm=min_wall_thickness_mm,
        )

    if target_max_dimension_mm is not None:
        raise RuntimeError("Target dimension scaling requires the trimesh backend. Install with: pip install -e '.[mesh]'")

    if input_mesh.suffix.lower() != ".obj":
        if input_mesh.suffix.lower() == output_mesh.suffix.lower():
            output_mesh.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_mesh, output_mesh)
            return PrintPrepResult(f"Copied printable mesh candidate: {output_mesh}", report_path=None)
        raise ValueError(
            "Built-in print prep currently supports OBJ input for mesh reporting and STL export. "
            "Use --repair-command-template for GLB/PLY/3MF conversion or repair."
        )

    mesh = read_obj(input_mesh)
    report = build_report(mesh)
    if scale is not None:
        mesh = _scale_builtin_mesh(mesh, scale)
        report = build_report(mesh)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    payload["backend"] = "builtin"
    payload["scale"] = scale
    payload["min_wall_thickness_mm"] = min_wall_thickness_mm
    payload["wall_thickness_check"] = "not_available_in_builtin_backend"
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if output_mesh.suffix.lower() == ".stl":
        write_ascii_stl(mesh, output_mesh, name=output_mesh.stem)
        message = f"Converted OBJ to printable STL candidate: {output_mesh}"
    elif output_mesh.suffix.lower() == ".obj":
        output_mesh.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_mesh, output_mesh)
        message = f"Copied printable OBJ candidate: {output_mesh}"
    else:
        raise ValueError("Built-in print prep supports .stl or .obj output. Use --repair-command-template otherwise.")

    return PrintPrepResult(message=message, report_path=report_path)


def _prepare_with_trimesh(
    input_mesh: Path,
    output_mesh: Path,
    report_path: Path,
    scale: float | None,
    target_max_dimension_mm: float | None,
    require_watertight: bool,
    min_wall_thickness_mm: float | None,
) -> PrintPrepResult:
    import trimesh

    loaded = trimesh.load(str(input_mesh), force="scene")
    if isinstance(loaded, trimesh.Scene):
        geometries = tuple(loaded.geometry.values())
        if not geometries:
            raise ValueError(f"No geometry found in {input_mesh}")
        mesh = trimesh.util.concatenate(geometries)
    else:
        mesh = loaded

    if mesh.is_empty:
        raise ValueError(f"Mesh is empty: {input_mesh}")

    mesh.process(validate=True)
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fill_holes(mesh)
    mesh.remove_unreferenced_vertices()

    applied_scale = scale
    if target_max_dimension_mm is not None:
        max_dimension = float(max(mesh.extents))
        if max_dimension <= 0:
            raise ValueError("Cannot scale a mesh with zero bounding-box extent.")
        applied_scale = target_max_dimension_mm / max_dimension
    if applied_scale is not None:
        mesh.apply_scale(applied_scale)

    report = _trimesh_report(mesh, applied_scale, min_wall_thickness_mm)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if require_watertight and not report["is_watertight"]:
        raise RuntimeError(f"Mesh is not watertight. Report written to {report_path}")

    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(output_mesh))
    return PrintPrepResult(f"Prepared printable mesh with trimesh backend: {output_mesh}", report_path)


def _trimesh_report(mesh, applied_scale: float | None, min_wall_thickness_mm: float | None) -> dict[str, object]:
    extents = [float(value) for value in mesh.extents.tolist()]
    bounds = [[float(value) for value in row] for row in mesh.bounds.tolist()]
    report: dict[str, object] = {
        "backend": "trimesh",
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "is_watertight": bool(mesh.is_watertight),
        "is_winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "body_count": int(mesh.body_count) if hasattr(mesh, "body_count") else None,
        "bounds": bounds,
        "extents": extents,
        "surface_area": float(mesh.area),
        "volume": float(mesh.volume) if mesh.is_watertight else None,
        "applied_scale": applied_scale,
        "min_wall_thickness_mm": min_wall_thickness_mm,
        "wall_thickness_check": "external_slicer_or_dedicated_thickness_tool_recommended",
    }
    if min_wall_thickness_mm is not None:
        report["wall_thickness_warning"] = (
            "Automatic wall-thickness validation is not implemented in this local backend. "
            "Use the slicer or an external repair command for this threshold."
        )
    return report


def _scale_builtin_mesh(mesh, scale: float):
    from .obj_mesh import MeshData

    return MeshData(
        vertices=[(x * scale, y * scale, z * scale) for x, y, z in mesh.vertices],
        faces=mesh.faces,
    )
