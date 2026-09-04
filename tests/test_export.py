from pathlib import Path
from xml.etree import ElementTree

import cadquery as cq

from mini_moonboard.export import export_reference


def test_exports_interoperable_reference_files(tmp_path: Path) -> None:
    step_path, front_path, side_path = export_reference(tmp_path)

    imported = cq.importers.importStep(str(step_path))
    assert imported.solids().size() == 6

    for svg_path in (front_path, side_path):
        root = ElementTree.parse(svg_path).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["data-units"] == "mm"

    assert "2440 mm / 96 1/16 in" in front_path.read_text()
    assert "40 degrees from vertical" in side_path.read_text()


def test_exports_are_reproducible(tmp_path: Path) -> None:
    first = export_reference(tmp_path / "first")
    second = export_reference(tmp_path / "second")

    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
