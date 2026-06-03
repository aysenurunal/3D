from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .command import format_command, render_command_template, run_command
from .preprocess import SUPPORTED_IMAGE_EXTENSIONS


@dataclass(frozen=True)
class MultiViewOptions:
    input_dir: Path
    output_asset: Path
    command_template: str | None
    min_images: int = 2
    max_images: int = 8
    dry_run: bool = False


@dataclass(frozen=True)
class MultiViewResult:
    message: str


def run_multiview_adapter(options: MultiViewOptions) -> MultiViewResult:
    input_dir = options.input_dir.resolve()
    output_asset = options.output_asset.resolve()

    if not input_dir.exists() and not options.dry_run:
        raise FileNotFoundError(f"Input image directory does not exist: {input_dir}")
    if not options.command_template:
        raise ValueError(
            "Missing multi-view command template. It must support {input_dir}, {images}, and {output}."
        )

    images = _collect_images(input_dir)
    if not options.dry_run:
        if len(images) < options.min_images:
            raise ValueError(f"Expected at least {options.min_images} images, found {len(images)}.")
        if len(images) > options.max_images:
            raise ValueError(f"Expected at most {options.max_images} images, found {len(images)}.")

    output_asset.parent.mkdir(parents=True, exist_ok=True)
    image_list = " ".join(str(path) for path in images)
    if options.dry_run and not image_list:
        image_list = "IMAGE_1 IMAGE_2"
    command = render_command_template(
        options.command_template,
        input_dir=input_dir,
        images=image_list,
        output=output_asset,
    )

    if options.dry_run:
        return MultiViewResult(f"Dry run multi-view command: {format_command(command)}")

    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(
            "Multi-view generation command failed.\n"
            f"Command: {format_command(result.command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    if not output_asset.exists():
        raise RuntimeError(f"Multi-view command finished but did not create {output_asset}")

    return MultiViewResult(f"Generated multi-view asset: {output_asset}")


def _collect_images(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        path.resolve()
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )
