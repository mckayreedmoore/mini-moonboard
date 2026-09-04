from pathlib import Path
from xml.etree import ElementTree

import cadquery as cq

from mini_moonboard.export import (
    export_panel_grid,
    export_panel_grid_drawing,
    export_reference,
)


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
    assert export_panel_grid(tmp_path / "first").read_bytes() == export_panel_grid(tmp_path / "second").read_bytes()
    assert export_panel_grid_drawing(tmp_path / "first").read_bytes() == export_panel_grid_drawing(
        tmp_path / "second"
    ).read_bytes()


def test_custom_kicker_export_is_not_labeled_official(tmp_path: Path) -> None:
    _, front_path, side_path = export_reference(tmp_path, kicker_height_mm=300)

    for path in (front_path, side_path):
        drawing = path.read_text()
        assert "CUSTOM KICKER INPUT - UNREVIEWED" in drawing
        assert "official front envelope" not in drawing
        assert "official side envelope" not in drawing

    assert "official 150 mm / 5 7/8 in active zone" in front_path.read_text()


def test_exports_metric_template_datum_drawing(tmp_path: Path) -> None:
    path = export_panel_grid_drawing(tmp_path)
    root = ElementTree.parse(path).getroot()

    assert root.attrib["data-units"] == "mm"
    assert "CENTER DATUMS ONLY - NOT A DRILL TEMPLATE" in path.read_text()
    assert "2437 mm / 95 15/16 in template width" in path.read_text()
    assert "A" in path.read_text()
    assert "12" in path.read_text()
    assert len(root.findall("{http://www.w3.org/2000/svg}circle")) == 274
