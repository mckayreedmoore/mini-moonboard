"""Extract inspectable geometry from a SketchUp ``.skp`` reference model.

This adapter is intentionally one-way.  It does not treat a reference model as
design authority or attempt to convert it into V1's parametric structure.
Instead it writes an OBJ mesh whose named groups retain the SketchUp scene
hierarchy, in millimetres, for comparison in any conventional CAD viewer.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Protocol

INCH_TO_MM = 25.4


class _Face(Protocol):
    vertex_positions: Sequence[tuple[float, float, float]]


class _Mesh(Protocol):
    faces: Iterable[_Face]


class _SceneNode(Protocol):
    name: str
    transform: Sequence[float]
    mesh: _Mesh | None
    children: Iterable[_SceneNode]


def _apply_transform(
    transform: Sequence[float], point: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Apply SketchUp's 13-value row-major affine transform to a point."""
    if len(transform) != 13:
        raise ValueError(f"expected 13 SketchUp transform values, got {len(transform)}")
    x, y, z = point
    return (
        transform[0] * x + transform[3] * y + transform[6] * z + transform[9],
        transform[1] * x + transform[4] * y + transform[7] * z + transform[10],
        transform[2] * x + transform[5] * y + transform[8] * z + transform[11],
    )


def _compose_transform(parent: Sequence[float], child: Sequence[float]) -> list[float]:
    """Return parent × child for SketchUp's affine transform representation."""
    origin = _apply_transform(parent, _apply_transform(child, (0.0, 0.0, 0.0)))
    x_axis = _apply_transform(parent, _apply_transform(child, (1.0, 0.0, 0.0)))
    y_axis = _apply_transform(parent, _apply_transform(child, (0.0, 1.0, 0.0)))
    z_axis = _apply_transform(parent, _apply_transform(child, (0.0, 0.0, 1.0)))
    return [
        x_axis[0] - origin[0], x_axis[1] - origin[1], x_axis[2] - origin[2],
        y_axis[0] - origin[0], y_axis[1] - origin[1], y_axis[2] - origin[2],
        z_axis[0] - origin[0], z_axis[1] - origin[1], z_axis[2] - origin[2],
        *origin,
        1.0,
    ]


def _obj_name(path: tuple[str, ...]) -> str:
    return "_".join("".join(char if char.isalnum() else "-" for char in piece) for piece in path)


def export_scene_obj(scene: _SceneNode, output_path: Path) -> Path:
    """Write all triangle-fan faces in *scene* to OBJ, in millimetres."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    identity = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    vertex_index = 1
    lines = ["# Extracted from SketchUp; units: millimetres", "# Reference geometry only"]

    def visit(node: _SceneNode, parent_transform: Sequence[float], path: tuple[str, ...]) -> None:
        nonlocal vertex_index
        transform = _compose_transform(parent_transform, node.transform)
        node_path = (*path, node.name or "unnamed")
        if node.mesh is not None:
            lines.append(f"g {_obj_name(node_path)}")
            for face in node.mesh.faces:
                points = list(face.vertex_positions)
                if len(points) < 3:
                    continue
                indices: list[int] = []
                for point in points:
                    x, y, z = _apply_transform(transform, point)
                    lines.append(f"v {x * INCH_TO_MM:.6f} {y * INCH_TO_MM:.6f} {z * INCH_TO_MM:.6f}")
                    indices.append(vertex_index)
                    vertex_index += 1
                for index in range(1, len(indices) - 1):
                    lines.append(f"f {indices[0]} {indices[index]} {indices[index + 1]}")
        for child in node.children:
            visit(child, transform, node_path)

    visit(scene, identity, ())
    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_skp_obj(input_path: Path, output_path: Path) -> Path:
    """Load a SketchUp model and export an inspectable millimetre OBJ mesh."""
    try:
        import skppy
    except ImportError as error:  # pragma: no cover - dependency is mandatory in production
        raise RuntimeError("Install project dependencies including skppy to import .skp files") from error
    return export_scene_obj(skppy.load(input_path).to_scene(), output_path)
