from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def render_command_template(template: str, **values: Path | str | int | float) -> list[str]:
    rendered_values = {key: str(value) for key, value in values.items()}
    rendered = template.format(**rendered_values)
    return shlex.split(rendered)


def run_command(command: list[str], cwd: Path | None = None) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)
