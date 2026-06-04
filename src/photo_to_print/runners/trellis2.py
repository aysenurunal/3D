from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..command import format_command, render_command_template, run_command


DEFAULT_TRELLIS2_COMMAND_TEMPLATE = (
    "python scripts/trellis2_image_to_3d.py --input {input} --output {output} --model {model}"
)


@dataclass(frozen=True)
class Trellis2Options:
    input_image: Path
    output_asset: Path
    command_template: str | None
    model: str = "microsoft/TRELLIS.2-4B"
    dry_run: bool = False


@dataclass(frozen=True)
class RunnerResult:
    message: str


def run_trellis2(options: Trellis2Options) -> RunnerResult:
    input_image = options.input_image.resolve()
    output_asset = options.output_asset.resolve()
    command_template = options.command_template or DEFAULT_TRELLIS2_COMMAND_TEMPLATE

    if not input_image.exists() and not options.dry_run:
        raise FileNotFoundError(f"Input image does not exist: {input_image}")

    output_asset.parent.mkdir(parents=True, exist_ok=True)
    command = render_command_template(
        command_template,
        input=input_image,
        output=output_asset,
        model=options.model,
    )

    if options.dry_run:
        return RunnerResult(f"Dry run TRELLIS.2 command: {format_command(command)}")

    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(
            "TRELLIS.2 command failed.\n"
            f"Command: {format_command(result.command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    if not output_asset.exists():
        raise RuntimeError(f"TRELLIS.2 command finished but did not create {output_asset}")

    return RunnerResult(f"Generated raw asset: {output_asset}")
