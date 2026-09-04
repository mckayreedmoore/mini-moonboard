import csv
import json
from pathlib import Path
from xml.etree import ElementTree

import cadquery as cq

from mini_moonboard.export import (
    export_panel_grid,
    export_panel_grid_drawing,
    export_reference,
    export_reference_panel_cut_list,
    export_v1_bom,
    export_v1_cad_render,
    export_v1_concept,
    export_v1_concept_side_drawing,
    export_v1_connection_schedule,
    export_v1_cut_list,
    export_v1_drill_schedule,
    export_v1_front_drawing,
    export_v1_isometric_drawing,
    export_v1_rear_drawing,
    export_v1_viewer_mesh,
)
from mini_moonboard.model import (
    V1_PANEL_SIZE_MM,
    build_v1_concept,
    v1_leg_geometry,
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


def test_exports_v1_concept_with_board_and_two_legs(tmp_path: Path) -> None:
    path = export_v1_concept(tmp_path)

    assert cq.importers.importStep(str(path)).solids().size() == 56


def test_exports_selectable_viewer_meshes_for_every_physical_part(tmp_path: Path) -> None:
    index_path = export_v1_viewer_mesh(tmp_path)
    parts = json.loads(index_path.read_text())["parts"]

    assert len(parts) == len(build_v1_concept().children)
    assert len({part["name"] for part in parts}) == len(parts)
    for part in parts:
        mesh_path = tmp_path / part["path"]
        assert mesh_path.is_file()
        assert mesh_path.stat().st_size > 84
        assert len(part["dimensions_mm"]) == 3
        assert all(dimension > 0 for dimension in part["dimensions_mm"])

    viewer_html = (Path(__file__).parents[1] / "site" / "index.html").read_text()
    assert "fetch('parts.json')" in viewer_html
    assert "loader.load(part.path" in viewer_html


def test_exports_v1_side_render(tmp_path: Path) -> None:
    path = export_v1_concept_side_drawing(tmp_path)
    root = ElementTree.parse(path).getroot()

    assert root.attrib["data-units"] == "mm"
    assert "PROVISIONAL GEOMETRY" in path.read_text()
    assert "row 8 bend datum" in path.read_text()


def test_exports_v1_plan_and_fabrication_schedules(tmp_path: Path) -> None:
    for path in (
        export_v1_front_drawing(tmp_path),
        export_v1_rear_drawing(tmp_path),
        export_v1_isometric_drawing(tmp_path),
    ):
        root = ElementTree.parse(path).getroot()
        assert root.attrib["data-units"] == "mm"
        assert "PROVISIONAL" in path.read_text()

    cut_rows = list(csv.DictReader(export_v1_cut_list(tmp_path).open(newline="")))
    drill_rows = list(csv.DictReader(export_v1_drill_schedule(tmp_path).open(newline="")))
    assert len(cut_rows) == 10
    assert len(drill_rows) == 274
    assert {row["diameter_mm"] for row in drill_rows if row["feature"] != "LED"} == {"11.112"}
    connection_rows = list(csv.DictReader(export_v1_connection_schedule(tmp_path).open(newline="")))
    bom_rows = list(csv.DictReader(export_v1_bom(tmp_path).open(newline="")))
    assert len(connection_rows) == 8
    assert len(bom_rows) == 10
    assert {row["axis"] for row in connection_rows} == {"X"}
    assert {row["clearance_hole_mm"] for row in connection_rows} == {"10.000"}
    lower_leg = next(row for row in cut_rows if row["part"] == "leg-lower lamination")
    assert lower_leg["length_mm"] == f"{v1_leg_geometry()['lower_length']:.1f}"
    rear_tie = next(row for row in cut_rows if row["part"] == "rear-tie-half lamination")
    assert rear_tie["length_mm"] == f"{V1_PANEL_SIZE_MM + 180 / 2:.1f}"
    gusset = next(row for row in cut_rows if row["part"].startswith("kicker-main side-gusset"))
    assert gusset["quantity"] == "4"
    assert all("X is bolt-stack midpoint" in row["datum"] for row in connection_rows)
    assert export_v1_rear_drawing(tmp_path).read_text().count('class="rail"') == 5
    assert export_v1_isometric_drawing(tmp_path).read_text().count('class="rail"') == 5


def test_exports_are_reproducible(tmp_path: Path) -> None:
    first = export_reference(tmp_path / "first")
    second = export_reference(tmp_path / "second")

    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    assert export_panel_grid(tmp_path / "first").read_bytes() == export_panel_grid(tmp_path / "second").read_bytes()
    assert export_panel_grid_drawing(tmp_path / "first").read_bytes() == export_panel_grid_drawing(
        tmp_path / "second"
    ).read_bytes()
    assert export_reference_panel_cut_list(tmp_path / "first").read_bytes() == export_reference_panel_cut_list(
        tmp_path / "second"
    ).read_bytes()
    assert export_v1_concept(tmp_path / "first").read_bytes() == export_v1_concept(tmp_path / "second").read_bytes()


def test_committed_exports_are_fresh(tmp_path: Path) -> None:
    generated_dir = tmp_path / "exports"
    export_reference(generated_dir)
    export_v1_concept(generated_dir)
    export_v1_cad_render(generated_dir)
    export_v1_concept_side_drawing(generated_dir)
    export_v1_front_drawing(generated_dir)
    export_v1_rear_drawing(generated_dir)
    export_v1_isometric_drawing(generated_dir)
    export_v1_cut_list(generated_dir)
    export_v1_drill_schedule(generated_dir)
    export_v1_connection_schedule(generated_dir)
    export_v1_bom(generated_dir)
    export_panel_grid(generated_dir)
    export_panel_grid_drawing(generated_dir)
    export_reference_panel_cut_list(generated_dir)
    committed_dir = Path(__file__).parents[1] / "exports"
    assert {path.name: path.read_bytes() for path in generated_dir.iterdir()} == {
        path.name: path.read_bytes() for path in committed_dir.iterdir()
    }


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


def test_exports_reference_panel_cut_list(tmp_path: Path) -> None:
    path = export_reference_panel_cut_list(tmp_path, kicker_height_mm=300)
    rows = list(csv.DictReader(path.open(newline="")))

    assert rows == [
        {
            "scope": "reference climbing surface only — excludes frame and hardware",
            "part": "main climbing panel",
            "quantity": "4",
            "length_mm": "1220.0",
            "width_mm": "1220.0",
            "thickness_mm": "18.0",
            "length_in": "48.0315",
            "width_in": "48.0315",
            "thickness_in": "0.7087",
            "material": "birch plywood; verify grade and actual thickness",
        },
        {
            "scope": "reference climbing surface only — excludes frame and hardware",
            "part": "kicker panel",
            "quantity": "2",
            "length_mm": "1220.0",
            "width_mm": "300.0",
            "thickness_mm": "18.0",
            "length_in": "48.0315",
            "width_in": "11.8110",
            "thickness_in": "0.7087",
            "material": "birch plywood; verify grade and actual thickness",
        },
    ]
