from dataclasses import dataclass
from pathlib import Path

from mini_moonboard.sketchup import export_scene_obj


@dataclass
class Face:
    vertex_positions: list[tuple[float, float, float]]


@dataclass
class Mesh:
    faces: list[Face]


@dataclass
class Node:
    name: str
    transform: list[float]
    mesh: Mesh | None
    children: list["Node"]


IDENTITY = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]


def test_sketchup_scene_export_applies_nested_transforms_and_converts_to_mm(tmp_path: Path) -> None:
    child_transform = [*IDENTITY]
    child_transform[9] = 2.0
    root = Node(
        "Scene",
        IDENTITY,
        None,
        [Node("two by six", child_transform, Mesh([Face([(0, 0, 0), (1, 0, 0), (0, 1, 0)])]), [])],
    )

    output = export_scene_obj(root, tmp_path / "reference.obj")
    text = output.read_text()

    assert "g Scene_two-by-six" in text
    assert "v 50.800000 0.000000 0.000000" in text
    assert "v 76.200000 0.000000 0.000000" in text
    assert "f 1 2 3" in text
