from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .convert import convert_mesh
from .multiview import MultiViewOptions, run_multiview_adapter
from .preprocess import preprocess_photos
from .print_prep import prepare_for_print
from .runners.instant_meshes import InstantMeshesOptions, run_instant_meshes
from .runners.trellis2 import Trellis2Options, run_trellis2


@dataclass(frozen=True)
class PipelineResult:
    messages: list[str]


def run_pipeline(
    name: str,
    input_dir: Path,
    processed_dir: Path,
    raw_output: Path | None,
    mesh_for_remesh: Path | None,
    remeshed_output: Path | None,
    printable_output: Path | None,
    generation_mode: str,
    trellis_command_template: str | None,
    multiview_command_template: str | None,
    mesh_convert_command_template: str | None,
    mesh_convert_preset: str | None,
    instant_meshes_bin: Path | None,
    target_faces: int,
    dry_run: bool = False,
) -> PipelineResult:
    raw_output = raw_output or Path("outputs/raw") / f"{name}.glb"
    mesh_for_remesh = mesh_for_remesh or _default_remesh_input(raw_output, name)
    remeshed_output = remeshed_output or Path("outputs/remeshed") / f"{name}.obj"
    printable_output = printable_output or Path("outputs/printable") / f"{name}.stl"

    if (
        raw_output.resolve() != mesh_for_remesh.resolve()
        and raw_output.suffix.lower() != mesh_for_remesh.suffix.lower()
        and not mesh_convert_command_template
        and not mesh_convert_preset
    ):
        raise ValueError(
            "The full pipeline needs a mesh conversion command before remeshing. "
            "Pass --mesh-convert-command-template, use --mesh-convert-preset, or set --raw-output to an OBJ/PLY path."
        )

    messages: list[str] = []
    preprocess_result = preprocess_photos(input_dir=input_dir, output_dir=processed_dir)
    messages.append(f"Imported {len(preprocess_result.photos)} photo(s).")
    messages.append(f"Primary image: {preprocess_result.primary_photo.processed_path}")

    if generation_mode == "single":
        generation = run_trellis2(
            Trellis2Options(
                input_image=Path(preprocess_result.primary_photo.processed_path),
                output_asset=raw_output,
                command_template=trellis_command_template,
                dry_run=dry_run,
            )
        )
    elif generation_mode == "multiview":
        generation = run_multiview_adapter(
            MultiViewOptions(
                input_dir=processed_dir,
                output_asset=raw_output,
                command_template=multiview_command_template,
                min_images=2,
                max_images=8,
                dry_run=dry_run,
            )
        )
    else:
        raise ValueError(f"Unsupported generation mode: {generation_mode}")
    messages.append(generation.message)

    if raw_output.resolve() != mesh_for_remesh.resolve():
        conversion = convert_mesh(
            input_mesh=raw_output,
            output_mesh=mesh_for_remesh,
            command_template=mesh_convert_command_template,
            preset=mesh_convert_preset,
            dry_run=dry_run,
        )
        messages.append(conversion.message)

    remesh = run_instant_meshes(
        InstantMeshesOptions(
            input_mesh=mesh_for_remesh,
            output_mesh=remeshed_output,
            binary=instant_meshes_bin,
            target_faces=target_faces,
            dry_run=dry_run,
        )
    )
    messages.append(remesh.message)

    print_prep = prepare_for_print(
        input_mesh=remeshed_output,
        output_mesh=printable_output,
        dry_run=dry_run,
    )
    messages.append(print_prep.message)
    if print_prep.report_path:
        messages.append(f"Report: {print_prep.report_path}")

    return PipelineResult(messages=messages)


def _default_remesh_input(raw_output: Path, name: str) -> Path:
    if raw_output.suffix.lower() in {".obj", ".ply"}:
        return raw_output
    return Path("outputs/raw") / f"{name}.obj"
