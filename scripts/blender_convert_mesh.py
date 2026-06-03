#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert mesh files with Blender.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args(_argv_after_blender_separator())
    input_path = args.input.resolve()
    output_path = args.output.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _clear_scene()
    _import_mesh(input_path)
    _export_mesh(output_path)


def _argv_after_blender_separator() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def _import_mesh(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
        return
    if suffix == ".obj":
        _call_first_available(
            ("wm.obj_import", {"filepath": str(path)}),
            ("import_scene.obj", {"filepath": str(path)}),
        )
        return
    if suffix == ".ply":
        _call_first_available(
            ("wm.ply_import", {"filepath": str(path)}),
            ("import_mesh.ply", {"filepath": str(path)}),
        )
        return
    if suffix == ".stl":
        _call_first_available(
            ("wm.stl_import", {"filepath": str(path)}),
            ("import_mesh.stl", {"filepath": str(path)}),
        )
        return
    raise ValueError(f"Unsupported input format: {suffix}")


def _export_mesh(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        export_format = "GLB" if suffix == ".glb" else "GLTF_SEPARATE"
        bpy.ops.export_scene.gltf(filepath=str(path), export_format=export_format)
        return
    if suffix == ".obj":
        _call_first_available(
            ("wm.obj_export", {"filepath": str(path), "export_materials": True}),
            ("export_scene.obj", {"filepath": str(path), "use_materials": True}),
        )
        return
    if suffix == ".ply":
        _call_first_available(
            ("wm.ply_export", {"filepath": str(path)}),
            ("export_mesh.ply", {"filepath": str(path)}),
        )
        return
    if suffix == ".stl":
        _call_first_available(
            ("wm.stl_export", {"filepath": str(path)}),
            ("export_mesh.stl", {"filepath": str(path)}),
        )
        return
    raise ValueError(f"Unsupported output format: {suffix}")


def _call_first_available(*calls: tuple[str, dict[str, object]]) -> None:
    errors = []
    for operator_path, kwargs in calls:
        operator = _resolve_operator(operator_path)
        if operator is None:
            errors.append(f"{operator_path} is not available")
            continue
        try:
            operator(**kwargs)
            return
        except TypeError as exc:
            errors.append(f"{operator_path}: {exc}")
    raise RuntimeError("; ".join(errors))


def _resolve_operator(operator_path: str):
    current = bpy.ops
    for part in operator_path.split("."):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


if __name__ == "__main__":
    main()
