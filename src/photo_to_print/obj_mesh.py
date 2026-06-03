from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MeshData:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]


@dataclass(frozen=True)
class MeshReport:
    vertices: int
    faces: int
    boundary_edges: int
    non_manifold_edges: int
    bounds_min: tuple[float, float, float] | None
    bounds_max: tuple[float, float, float] | None


def read_obj(path: Path) -> MeshData:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("v "):
                parts = line.split()
                if len(parts) < 4:
                    continue
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                indices = [_parse_obj_index(part, len(vertices)) for part in line.split()[1:]]
                indices = [index for index in indices if index is not None]
                if len(indices) < 3:
                    continue
                for i in range(1, len(indices) - 1):
                    faces.append((indices[0], indices[i], indices[i + 1]))

    if not vertices:
        raise ValueError(f"OBJ has no vertices: {path}")
    if not faces:
        raise ValueError(f"OBJ has no faces: {path}")

    return MeshData(vertices=vertices, faces=faces)


def write_ascii_stl(mesh: MeshData, path: Path, name: str = "photo_to_print") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"solid {name}\n")
        for face in mesh.faces:
            normal = _face_normal(mesh.vertices, face)
            handle.write(f"  facet normal {normal[0]:.8g} {normal[1]:.8g} {normal[2]:.8g}\n")
            handle.write("    outer loop\n")
            for vertex_index in face:
                vertex = mesh.vertices[vertex_index]
                handle.write(f"      vertex {vertex[0]:.8g} {vertex[1]:.8g} {vertex[2]:.8g}\n")
            handle.write("    endloop\n")
            handle.write("  endfacet\n")
        handle.write(f"endsolid {name}\n")


def build_report(mesh: MeshData) -> MeshReport:
    edge_counts: dict[tuple[int, int], int] = {}
    for face in mesh.faces:
        for edge in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            normalized = tuple(sorted(edge))
            edge_counts[normalized] = edge_counts.get(normalized, 0) + 1

    bounds_min = tuple(min(vertex[index] for vertex in mesh.vertices) for index in range(3))
    bounds_max = tuple(max(vertex[index] for vertex in mesh.vertices) for index in range(3))
    return MeshReport(
        vertices=len(mesh.vertices),
        faces=len(mesh.faces),
        boundary_edges=sum(1 for count in edge_counts.values() if count == 1),
        non_manifold_edges=sum(1 for count in edge_counts.values() if count > 2),
        bounds_min=bounds_min,
        bounds_max=bounds_max,
    )


def _parse_obj_index(value: str, vertex_count: int) -> int | None:
    raw_index = value.split("/")[0]
    if not raw_index:
        return None
    index = int(raw_index)
    if index > 0:
        return index - 1
    return vertex_count + index


def _face_normal(vertices: list[tuple[float, float, float]], face: tuple[int, int, int]) -> tuple[float, float, float]:
    a = vertices[face[0]]
    b = vertices[face[1]]
    c = vertices[face[2]]
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    normal = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    length = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)
    if length == 0:
        return (0.0, 0.0, 0.0)
    return (normal[0] / length, normal[1] / length, normal[2] / length)
