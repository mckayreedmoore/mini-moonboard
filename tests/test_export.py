import csv
import json
import math
from pathlib import Path
from xml.etree import ElementTree

import cadquery as cq
import pytest

from mini_moonboard.export import (
    export_panel_grid,
    export_panel_grid_drawing,
    export_reference,
    export_reference_panel_cut_list,
    export_v1_assembly_layout,
    export_v1_bom,
    export_v1_cad_render,
    export_v1_concept,
    export_v1_concept_side_drawing,
    export_v1_connection_schedule,
    export_v1_cut_list,
    export_v1_drill_schedule,
    export_v1_front_drawing,
    export_v1_isometric_drawing,
    export_v1_leg_cut_schedule,
    export_v1_panel_drill_schedule,
    export_v1_rear_drawing,
    export_v1_secondary_joinery_schedule,
    export_v1_stability_screen,
    export_v1_viewer_mesh,
)
from mini_moonboard.model import (
    V1_KICKER_MAIN_GUSSET_BLANK_HEIGHT_MM,
    V1_KNEE_BOLT_LENGTH_MM,
    V1_LEG_RAIL_BOLT_LENGTH_MM,
    V1_PANEL_SIZE_MM,
    _v1_kicker_holes,
    _v1_main_panel_holes,
    build_v1_concept,
    v1_face_rail_centres,
    v1_leg_geometry,
    v1_lower_leg_cut_profile,
)


def test_exports_interoperable_reference_files(tmp_path: Path) -> None:
    step_path, front_path, side_path = export_reference(tmp_path)

    imported = cq.importers.importStep(str(step_path))
    assert imported.solids().size() == 6

    for svg_path in (front_path, side_path):
        root = ElementTree.parse(svg_path).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["data-units"] == "mm"

    assert "2440.0 mm / 96 1/16 in" in front_path.read_text()
    assert "40 degrees from vertical" in side_path.read_text()


def test_exports_v1_concept_with_board_and_two_legs(tmp_path: Path) -> None:
    path = export_v1_concept(tmp_path)

    assert cq.importers.importStep(str(path)).solids().size() == 66


def test_exports_selectable_viewer_meshes_for_every_physical_part(tmp_path: Path) -> None:
    index_path = export_v1_viewer_mesh(tmp_path)
    parts = json.loads(index_path.read_text())["parts"]

    connection_parts = [part for part in parts if part["name"].startswith("analysis_")]
    assert len(parts) == len(build_v1_concept().children) + 76
    assert len(connection_parts) == 76
    assert {part["name"].split("_")[1] for part in connection_parts} == {"leg", "knee", "panel", "main"}
    assert parts[0]["fabrication"]["dimensions_imperial"]
    assert len({part["name"] for part in parts}) == len(parts)
    for part in parts:
        mesh_path = tmp_path / part["path"]
        assert mesh_path.is_file()
        assert mesh_path.stat().st_size > 84
        assert len(part["fabrication"]["dimensions_mm"]) == 3
        assert all(dimension > 0 for dimension in part["fabrication"]["dimensions_mm"])
        assert len(part["viewer_aabb_mm"]) == 3
        assert all(dimension > 0 for dimension in part["viewer_aabb_mm"])

    viewer_html = (Path(__file__).parents[1] / "site" / "index.html").read_text()
    assert "fetch('parts.json')" in viewer_html
    assert "loader.load(part.path" in viewer_html
    assert "part.fabrication.dimensions_mm" in viewer_html
    assert "part.fabrication.dimensions_imperial" in viewer_html
    assert "analysis_" in viewer_html
    assert 'id="overlay"' in viewer_html
    assert "ABCDEFGHIJK" in viewer_html
    assert "labelDecal" in viewer_html
    assert "new THREE.PlaneGeometry" in viewer_html
    assert "mainFacePoint(1019.2, 80 + index * 200)" in viewer_html


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
    leg_cut_rows = list(csv.DictReader(export_v1_leg_cut_schedule(tmp_path).open(newline="")))
    layout_rows = list(csv.DictReader(export_v1_assembly_layout(tmp_path).open(newline="")))
    drill_rows = list(csv.DictReader(export_v1_drill_schedule(tmp_path).open(newline="")))
    panel_drill_rows = list(csv.DictReader(export_v1_panel_drill_schedule(tmp_path).open(newline="")))
    assert len(cut_rows) == 14
    assert len(leg_cut_rows) == 2
    assert len(layout_rows) == len(build_v1_concept().children) + 2
    expected_layout_parts = {child.name for child in build_v1_concept().children} - {"leg_left", "leg_right"}
    expected_layout_parts |= {"leg_left_lower", "leg_left_upper", "leg_right_lower", "leg_right_upper"}
    assert {row["part"] for row in layout_rows} == expected_layout_parts
    assert float(next(row for row in layout_rows if row["part"] == "leg_left_lower")["center_z_mm"]) < float(
        next(row for row in layout_rows if row["part"] == "leg_left_upper")["center_z_mm"]
    )
    assert all(math.isclose(sum(float(row[f"dominant_axis_{axis}"]) ** 2 for axis in "xyz"), 1, abs_tol=1e-5) for row in layout_rows)
    assert leg_cut_rows[0]["finished_profile_mm"].startswith(f"({v1_lower_leg_cut_profile()[0][0]:.3f},0.000)")
    assert "matched, identically profiled pairs" in leg_cut_rows[0]["cut_instruction"]
    assert len(drill_rows) == 274
    assert len(panel_drill_rows) == 274
    assert {row["part"] for row in panel_drill_rows} == {
        "main_lower_left", "main_lower_right", "main_upper_left", "main_upper_right", "kicker_left", "kicker_right"
    }
    assert all(0 < float(row["x_from_left_mm"]) < V1_PANEL_SIZE_MM for row in panel_drill_rows)
    actual_panel_bores = {
        (
            row["part"],
            round(float(row["x_from_left_mm"]), 3),
            round(float(row["z_from_bottom_mm"]), 3),
            round(float(row["diameter_mm"]), 3),
        )
        for row in panel_drill_rows
    }
    expected_panel_bores = {
        (
            f"main_{row_label}_{side}",
            round(x + V1_PANEL_SIZE_MM / 2, 3),
            round(z, 3),
            round(diameter, 3),
        )
        for row, row_label in enumerate(("lower", "upper"))
        for column, side in enumerate(("left", "right"))
        for x, z, diameter in _v1_main_panel_holes(column, row)
    } | {
        (
            f"kicker_{side}",
            round(x + V1_PANEL_SIZE_MM / 2, 3),
            round(z, 3),
            round(diameter, 3),
        )
        for column, side in enumerate(("left", "right"))
        for x, z, diameter in _v1_kicker_holes(column)
    }
    assert actual_panel_bores == expected_panel_bores
    assert len({(row["feature"], row["label"]) for row in panel_drill_rows}) == len(panel_drill_rows)
    assert {row["diameter_mm"] for row in drill_rows if row["feature"] != "LED"} == {"11.112"}
    connection_rows = list(csv.DictReader(export_v1_connection_schedule(tmp_path).open(newline="")))
    secondary_rows = list(csv.DictReader(export_v1_secondary_joinery_schedule(tmp_path).open(newline="")))
    bom_rows = list(csv.DictReader(export_v1_bom(tmp_path).open(newline="")))
    assert len(connection_rows) == 76
    assert len(bom_rows) == 14
    assert bom_rows[0]["quantity"] == "9 sheets"
    panel_screws = next(row for row in bom_rows if row["item"] == "#10 x 3.5 in countersunk structural wood screws")
    assert panel_screws["quantity"] == "60"
    assert sum(int(row["total_screws"]) for row in secondary_rows if row["hardware"] == "#10 x 2.5 in structural wood screw") == 72
    assert sum(int(row["total_screws"]) for row in secondary_rows if row["hardware"] == "#10 x 2 in structural wood screw") == 24
    assert next(row for row in bom_rows if row["item"] == "#10 x 2.5 in structural wood screws")["quantity"] == "72 plus 10% spare"
    assert next(row for row in bom_rows if row["item"] == "#10 x 2 in structural wood screws")["quantity"] == "24 plus 10% spare"
    hold_bundle = next(row for row in bom_rows if row["item"] == "Mini MoonBoard 2025 Setup Hold Bundle")
    assert hold_bundle["quantity"] == "1, SKU 60-105-2025"
    structural_bolt = next(row for row in bom_rows if row["item"] == "3/8 in Grade-5 structural through-bolts")
    assert structural_bolt["quantity"] == f"8 x {V1_LEG_RAIL_BOLT_LENGTH_MM / 25.4:.0f} in; 8 x {V1_KNEE_BOLT_LENGTH_MM / 25.4:.0f} in"
    assert all("10 in nominal" in row["hardware_assumption"] for row in connection_rows[:8])
    assert {row["axis"] for row in connection_rows} == {"X", "board-normal toward support frame"}
    assert {row["clearance_hole_mm"] for row in connection_rows} == {"10.000", "3.200 pilot"}
    lower_leg = next(row for row in cut_rows if row["part"] == "leg-lower lamination")
    assert lower_leg["length_mm"] == f"{v1_leg_geometry()['lower_length']:.1f}"
    assert float(lower_leg["length_in"]) == pytest.approx(v1_leg_geometry()["lower_length"] / 25.4, abs=0.0001)
    assert {"length_in", "width_in", "thickness_in"} <= set(lower_leg)
    rail_tie = next(row for row in cut_rows if row["part"] == "rail-cross-tie-half lamination")
    assert rail_tie["length_mm"] == f"{V1_PANEL_SIZE_MM + 180 / 2:.1f}"
    gusset = next(row for row in cut_rows if row["part"].startswith("kicker-main side-gusset"))
    assert gusset["quantity"] == "4"
    assert gusset["width_mm"] == f"{V1_KICKER_MAIN_GUSSET_BLANK_HEIGHT_MM:.1f}"
    assert all(
        "X is bolt-stack midpoint" in row["datum"]
        if row["axis"] == "X"
        else "countersunk screw-head centers at climbing face" in row["datum"]
        if row["axis"] == "board-normal toward support frame"
        else False
        for row in connection_rows
    )
    rear_drawing = export_v1_rear_drawing(tmp_path).read_text()
    assert rear_drawing.count('class="rail"') == 5
    rear_scale = 600 / (2 * V1_PANEL_SIZE_MM)
    for rail in v1_face_rail_centres():
        assert f'x1="{150 + (rail + V1_PANEL_SIZE_MM) * rear_scale:.1f}"' in rear_drawing
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
    export_v1_stability_screen(generated_dir)
    export_v1_cad_render(generated_dir)
    export_v1_concept_side_drawing(generated_dir)
    export_v1_front_drawing(generated_dir)
    export_v1_rear_drawing(generated_dir)
    export_v1_isometric_drawing(generated_dir)
    export_v1_cut_list(generated_dir)
    export_v1_leg_cut_schedule(generated_dir)
    export_v1_assembly_layout(generated_dir)
    export_v1_drill_schedule(generated_dir)
    export_v1_panel_drill_schedule(generated_dir)
    export_v1_connection_schedule(generated_dir)
    export_v1_secondary_joinery_schedule(generated_dir)
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


def test_v1_sheet_nesting_map_has_kerf_separation_between_zones() -> None:
    """Keep the human cut maps mechanically usable after stock-route edits."""
    source = (Path(__file__).parents[1] / "docs" / "v1-sheet-nesting.md").read_text().splitlines()

    def zones_after(heading: str) -> list[tuple[str, float, float, float, float]]:
        start = source.index(heading) + 4
        zones = []
        for line in source[start:]:
            if not line.startswith("|"):
                break
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells[0] == "Zone":
                continue
            x0, x1 = (float(value) for value in cells[1].split("–"))
            y0, y1 = (float(value) for value in cells[2].split("–"))
            zones.append((cells[0], x0, x1, y0, y1))
        return zones

    for zones in (zones_after("### Sheet 7"), zones_after("### Sheet 8"), zones_after("### Sheet 9")):
        assert zones
        for _name, x0, x1, y0, y1 in zones:
            assert 0 <= x0 < x1 <= 1219.2
            assert 0 <= y0 < y1 <= 2438.4
        for index, (_name, x0, x1, y0, y1) in enumerate(zones):
            for _other, other_x0, other_x1, other_y0, other_y1 in zones[index + 1 :]:
                # Every pair of layout zones has at least one 2.4 mm kerf gap.
                assert x1 + 1.2 <= other_x0 or other_x1 + 1.2 <= x0 or y1 + 1.2 <= other_y0 or other_y1 + 1.2 <= y0

    # Sheets 1–4 retain the factory X width for both the square main panel and
    # each rail's long dimension; only their Y ranges consume the crosscut
    # remainder. This prevents a future rotation from making the route invalid.
    main_end, kerf, raw_length = 1219.2, 2.4, 2438.4
    rail_y_starts = tuple(main_end + kerf + index * (180 + kerf) for index in range(5))
    assert rail_y_starts[0] == pytest.approx(1221.6)
    assert rail_y_starts[-1] + 180 == pytest.approx(2131.2)
    assert rail_y_starts[-1] + 180 <= raw_length


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
