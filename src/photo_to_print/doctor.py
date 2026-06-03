from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def has_failures(self) -> bool:
        return any(check.status == "fail" for check in self.checks)


def run_doctor(
    trellis_root: Path | None = None,
    instantmesh_root: Path | None = None,
    converter_bin: str | None = None,
) -> DoctorReport:
    checks = [
        _check_platform(),
        _check_python(),
        _check_nvidia_smi(),
        _check_conda(),
        _check_trellis_root(trellis_root),
        _check_tencent_instantmesh_root(instantmesh_root),
        _check_python_import("PIL", "Pillow"),
        _check_python_import("trellis2", "TRELLIS.2 Python package"),
        _check_python_import("o_voxel", "o-voxel package"),
        _check_converter(converter_bin),
    ]
    return DoctorReport(checks=checks)


def format_doctor_report(report: DoctorReport) -> str:
    lines = []
    for check in report.checks:
        lines.append(f"[{check.status.upper()}] {check.name}: {check.message}")
    return "\n".join(lines)


def doctor_report_to_json(report: DoctorReport) -> str:
    return json.dumps({"checks": [asdict(check) for check in report.checks]}, indent=2) + "\n"


def _check_platform() -> DoctorCheck:
    system = platform.system()
    machine = platform.machine()
    if system == "Linux":
        return DoctorCheck("platform", "pass", f"{system} {machine}")
    return DoctorCheck(
        "platform",
        "warn",
        f"{system} {machine}. Real InstantMesh/TRELLIS.2 generation should run on Linux with CUDA.",
    )


def _check_python() -> DoctorCheck:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        return DoctorCheck("python", "pass", version)
    return DoctorCheck("python", "fail", f"{version}. Python 3.10+ is required for this local pipeline.")


def _check_nvidia_smi() -> DoctorCheck:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return DoctorCheck("nvidia-smi", "fail", "Not found. TencentARC InstantMesh and TRELLIS.2 need an NVIDIA CUDA GPU.")

    result = subprocess.run([nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        return DoctorCheck("nvidia-smi", "fail", result.stderr.strip() or "nvidia-smi failed.")
    return DoctorCheck("nvidia-smi", "pass", result.stdout.strip() or nvidia_smi)


def _check_conda() -> DoctorCheck:
    conda = shutil.which("conda")
    if conda:
        return DoctorCheck("conda", "pass", conda)
    return DoctorCheck("conda", "warn", "Not found. TRELLIS.2 setup commonly uses conda.")


def _check_trellis_root(trellis_root: Path | None) -> DoctorCheck:
    if not trellis_root:
        return DoctorCheck("trellis-root", "warn", "Not provided. Pass --trellis-root /path/to/TRELLIS.2.")

    trellis_root = trellis_root.resolve()
    if not trellis_root.exists():
        return DoctorCheck("trellis-root", "fail", f"Directory does not exist: {trellis_root}")
    if not (trellis_root / "setup.sh").exists():
        return DoctorCheck("trellis-root", "warn", f"setup.sh was not found under {trellis_root}")
    return DoctorCheck("trellis-root", "pass", str(trellis_root))


def _check_tencent_instantmesh_root(instantmesh_root: Path | None) -> DoctorCheck:
    if not instantmesh_root:
        return DoctorCheck("tencent-instantmesh-root", "warn", "Not provided. Pass --instantmesh-root /path/to/InstantMesh.")

    instantmesh_root = instantmesh_root.resolve()
    if not instantmesh_root.exists():
        return DoctorCheck("tencent-instantmesh-root", "fail", f"Directory does not exist: {instantmesh_root}")
    if not (instantmesh_root / "run.py").exists():
        return DoctorCheck("tencent-instantmesh-root", "fail", f"run.py was not found under {instantmesh_root}")
    if not (instantmesh_root / "configs" / "instant-mesh-large.yaml").exists():
        return DoctorCheck(
            "tencent-instantmesh-root",
            "warn",
            f"configs/instant-mesh-large.yaml was not found under {instantmesh_root}",
        )
    return DoctorCheck("tencent-instantmesh-root", "pass", str(instantmesh_root))


def _check_python_import(module_name: str, label: str) -> DoctorCheck:
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}; print('ok')"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        return DoctorCheck(label, "pass", "Import succeeded.")
    return DoctorCheck(label, "warn", "Import failed in the current Python environment.")


def _check_converter(converter_bin: str | None) -> DoctorCheck:
    candidates = [converter_bin] if converter_bin else ["blender", "assimp"]
    for candidate in candidates:
        if not candidate:
            continue
        found = shutil.which(candidate)
        if found:
            return DoctorCheck("mesh-converter", "pass", found)
    if converter_bin:
        return DoctorCheck("mesh-converter", "fail", f"Converter not found on PATH: {converter_bin}")
    return DoctorCheck("mesh-converter", "warn", "Neither blender nor assimp was found on PATH.")
