from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .paths import ProjectPaths, ensure_project_dirs
from .pipeline import run_pipeline
from .preprocess import preprocess_photos
from .convert import convert_mesh
from .doctor import doctor_report_to_json, format_doctor_report, run_doctor
from .multiview import MultiViewOptions, run_multiview_adapter
from .print_prep import prepare_for_print
from .runners.instant_meshes import InstantMeshesOptions, run_instant_meshes
from .runners.trellis2 import Trellis2Options, run_trellis2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="photo-to-print",
        description="Run a photo-to-3D-print asset pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create the expected data and output directories.")
    init_parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root directory.")

    doctor_parser = subparsers.add_parser("doctor", help="Check local external tool readiness.")
    doctor_parser.add_argument("--trellis-root", type=Path, help="Path to a TRELLIS.2 checkout.")
    doctor_parser.add_argument("--instant-meshes-bin", type=Path, help="Path to the Instant Meshes binary.")
    doctor_parser.add_argument("--converter-bin", help="Converter executable to check, for example blender or assimp.")
    doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    preprocess_parser = subparsers.add_parser("preprocess", help="Import and normalize input photos.")
    preprocess_parser.add_argument("--input-dir", type=Path, default=Path("data/input_photos"))
    preprocess_parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    preprocess_parser.add_argument(
        "--primary-strategy",
        choices=("largest-file", "first"),
        default="largest-file",
        help="How to choose the primary image for the MVP single-image generation step.",
    )
    preprocess_parser.add_argument("--primary-name", help="Optional exact source filename to use as primary.")

    generate_parser = subparsers.add_parser("generate", help="Run the TRELLIS.2 generation adapter.")
    generate_parser.add_argument("--input", type=Path, required=True, help="Primary input image.")
    generate_parser.add_argument("--output", type=Path, required=True, help="Raw generated asset path.")
    generate_parser.add_argument(
        "--command-template",
        help="Command template used to run TRELLIS.2. Supports {input} and {output}.",
    )
    generate_parser.add_argument("--model", default="microsoft/TRELLIS.2-4B")
    generate_parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")

    multiview_parser = subparsers.add_parser("generate-multiview", help="Run a pluggable multi-view generation adapter.")
    multiview_parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    multiview_parser.add_argument("--output", type=Path, required=True, help="Generated asset path.")
    multiview_parser.add_argument(
        "--command-template",
        required=True,
        help="External multi-view command. Supports {input_dir}, {images}, and {output}.",
    )
    multiview_parser.add_argument("--min-images", type=int, default=2)
    multiview_parser.add_argument("--max-images", type=int, default=8)
    multiview_parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")

    convert_parser = subparsers.add_parser("convert", help="Convert mesh formats between generation and remeshing.")
    convert_parser.add_argument("--input", type=Path, required=True, help="Input mesh path.")
    convert_parser.add_argument("--output", type=Path, required=True, help="Converted output mesh path.")
    convert_parser.add_argument(
        "--command-template",
        help="External conversion command. Supports {input} and {output}.",
    )
    convert_parser.add_argument("--preset", choices=("blender", "assimp"), help="Use a known converter command preset.")
    convert_parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")

    remesh_parser = subparsers.add_parser("remesh", help="Run the Instant Meshes remesh adapter.")
    remesh_parser.add_argument("--input", type=Path, required=True, help="Input OBJ/PLY mesh.")
    remesh_parser.add_argument("--output", type=Path, required=True, help="Remeshed output OBJ/PLY path.")
    remesh_parser.add_argument("--instant-meshes-bin", type=Path, help="Path to the Instant Meshes binary.")
    remesh_parser.add_argument("--faces", type=int, default=10000, help="Target face count.")
    remesh_parser.add_argument("--rosy", type=int, default=4, choices=(2, 4, 6))
    remesh_parser.add_argument("--posy", type=int, default=4, choices=(3, 4))
    remesh_parser.add_argument("--crease", type=float, default=30.0, help="Crease angle in degrees.")
    remesh_parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")

    print_parser = subparsers.add_parser("print-prep", help="Prepare a mesh for 3D printing.")
    print_parser.add_argument("--input", type=Path, required=True, help="Input mesh path.")
    print_parser.add_argument("--output", type=Path, required=True, help="Printable output path.")
    print_parser.add_argument("--report", type=Path, help="Optional JSON mesh report path.")
    print_parser.add_argument("--backend", choices=("auto", "builtin", "trimesh"), default="auto")
    print_parser.add_argument("--scale", type=float, help="Uniform scale factor to apply before export.")
    print_parser.add_argument("--target-max-dimension-mm", type=float, help="Scale the largest bounding-box axis to this size.")
    print_parser.add_argument("--require-watertight", action="store_true", help="Fail if the repaired mesh is not watertight.")
    print_parser.add_argument("--min-wall-thickness-mm", type=float, help="Record the intended wall-thickness threshold.")
    print_parser.add_argument(
        "--repair-command-template",
        help="Optional external repair/conversion command. Supports {input}, {output}, and {report}.",
    )
    print_parser.add_argument("--dry-run", action="store_true", help="Print external repair command without running it.")

    run_parser = subparsers.add_parser("run", help="Run the MVP pipeline end to end.")
    run_parser.add_argument("--name", required=True, help="Asset run name, for example 'mug-test-01'.")
    run_parser.add_argument("--input-dir", type=Path, default=Path("data/input_photos"))
    run_parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    run_parser.add_argument("--raw-output", type=Path, help="Raw asset path. Defaults to outputs/raw/<name>.glb.")
    run_parser.add_argument("--mesh-for-remesh", type=Path, help="OBJ/PLY mesh passed into Instant Meshes.")
    run_parser.add_argument("--remeshed-output", type=Path, help="Remeshed path. Defaults to outputs/remeshed/<name>.obj.")
    run_parser.add_argument("--printable-output", type=Path, help="Printable path. Defaults to outputs/printable/<name>.stl.")
    run_parser.add_argument("--trellis-command-template", help="TRELLIS.2 command template.")
    run_parser.add_argument("--generation-mode", choices=("single", "multiview"), default="single")
    run_parser.add_argument("--multiview-command-template", help="External multi-view generation command template.")
    run_parser.add_argument("--mesh-convert-command-template", help="Command template for GLB-to-OBJ/PLY conversion.")
    run_parser.add_argument("--mesh-convert-preset", choices=("blender", "assimp"), help="Known converter preset.")
    run_parser.add_argument("--instant-meshes-bin", type=Path, help="Path to the Instant Meshes binary.")
    run_parser.add_argument("--faces", type=int, default=10000, help="Target remesh face count.")
    run_parser.add_argument("--dry-run", action="store_true", help="Print external commands without running them.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            paths = ProjectPaths.from_root(args.root)
            ensure_project_dirs(paths)
            print(f"Initialized project directories under {paths.root}")
            return

        if args.command == "doctor":
            report = run_doctor(
                trellis_root=args.trellis_root,
                instant_meshes_bin=args.instant_meshes_bin,
                converter_bin=args.converter_bin,
            )
            if args.json:
                print(doctor_report_to_json(report), end="")
            else:
                print(format_doctor_report(report))
            if report.has_failures:
                raise SystemExit(2)
            return

        if args.command == "preprocess":
            result = preprocess_photos(
                input_dir=args.input_dir,
                output_dir=args.output_dir,
                primary_strategy=args.primary_strategy,
                primary_name=args.primary_name,
            )
            print(f"Imported {len(result.photos)} photo(s).")
            print(f"Primary image: {result.primary_photo.processed_path}")
            print(f"Manifest: {result.manifest_path}")
            return

        if args.command == "generate":
            result = run_trellis2(
                Trellis2Options(
                    input_image=args.input,
                    output_asset=args.output,
                    command_template=args.command_template,
                    model=args.model,
                    dry_run=args.dry_run,
                )
            )
            print(result.message)
            return

        if args.command == "generate-multiview":
            result = run_multiview_adapter(
                MultiViewOptions(
                    input_dir=args.input_dir,
                    output_asset=args.output,
                    command_template=args.command_template,
                    min_images=args.min_images,
                    max_images=args.max_images,
                    dry_run=args.dry_run,
                )
            )
            print(result.message)
            return

        if args.command == "convert":
            result = convert_mesh(
                input_mesh=args.input,
                output_mesh=args.output,
                command_template=args.command_template,
                preset=args.preset,
                dry_run=args.dry_run,
            )
            print(result.message)
            return

        if args.command == "remesh":
            result = run_instant_meshes(
                InstantMeshesOptions(
                    input_mesh=args.input,
                    output_mesh=args.output,
                    binary=args.instant_meshes_bin,
                    target_faces=args.faces,
                    rosy=args.rosy,
                    posy=args.posy,
                    crease=args.crease,
                    dry_run=args.dry_run,
                )
            )
            print(result.message)
            return

        if args.command == "print-prep":
            result = prepare_for_print(
                input_mesh=args.input,
                output_mesh=args.output,
                report_path=args.report,
                repair_command_template=args.repair_command_template,
                backend=args.backend,
                scale=args.scale,
                target_max_dimension_mm=args.target_max_dimension_mm,
                require_watertight=args.require_watertight,
                min_wall_thickness_mm=args.min_wall_thickness_mm,
                dry_run=args.dry_run,
            )
            print(result.message)
            if result.report_path:
                print(f"Report: {result.report_path}")
            return

        if args.command == "run":
            result = run_pipeline(
                name=args.name,
                input_dir=args.input_dir,
                processed_dir=args.processed_dir,
                raw_output=args.raw_output,
                mesh_for_remesh=args.mesh_for_remesh,
                remeshed_output=args.remeshed_output,
                printable_output=args.printable_output,
                generation_mode=args.generation_mode,
                trellis_command_template=args.trellis_command_template,
                multiview_command_template=args.multiview_command_template,
                mesh_convert_command_template=args.mesh_convert_command_template,
                mesh_convert_preset=args.mesh_convert_preset,
                instant_meshes_bin=args.instant_meshes_bin,
                target_faces=args.faces,
                dry_run=args.dry_run,
            )
            for message in result.messages:
                print(message)
            return

        parser.error(f"Unknown command: {args.command}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
