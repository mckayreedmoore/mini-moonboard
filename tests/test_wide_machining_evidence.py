"""Actual-part replay and geometric witnesses for the local inspection package."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import wide_frame as frame
from mini_moonboard import wide_machining as machining

DIRECTORY = Path("docs/wide-machining")


@pytest.fixture(scope="module")
def evidence():
    return json.loads((DIRECTORY/"metadata.json").read_text())


def test_entire_saved_schedule_replays_from_current_cad(evidence):
    assert json.loads(json.dumps(machining.build())) == evidence
    assert len(evidence["datums"]) == 29 and evidence["connection_count"] == 188
    assert len(evidence["connections"]) == 276
    assert Counter(r["class"] for r in evidence["features"]) == {
        "through_hole": 274, "service_reservation": 80, "countersink_envelope": 56,
        "header_bearing_plane": 4, "floor_bearing_plane": 4, "housing": 2, "counterbore": 2}
    for name, rows in (("datums", list(evidence["datums"].values())),
                       ("connections", evidence["connections"]), ("features", evidence["features"])):
        reader = csv.DictReader((DIRECTORY/(name+".csv")).open())
        assert reader.fieldnames == list(dict.fromkeys(k for row in rows for k in row))
        saved = list(reader)
        assert len(saved) == len(rows)
        for actual, row in zip(saved, rows, strict=True):
            for key in actual:
                value = row.get(key)
                expected = json.dumps(value) if isinstance(value, (list, dict)) else "" if value is None else str(value)
                assert actual[key] == expected


def test_every_raw_axis_entry_exit_maps_to_actual_part_surface(evidence):
    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    for row in evidence["connections"]:
        datum = evidence["datums"][row["part"]]
        for field in ("raw_entry_local", "raw_exit_local"):
            for point, inches in zip(row[field+"_mm"], row[field+"_in"], strict=True):
                assert point == pytest.approx([v*25.4 for v in inches], abs=1e-8)
                world = machining.to_world(point, datum)
                assert raw[row["part"]].isInside(cq.Vector(*world), 1e-5), (row["connection"], row["part"])
                assert machining.to_local(world, datum) == pytest.approx(point, abs=1e-8)
        assert row["machining_depth_mm"] is None


def test_plane_points_and_normals_are_reversible_and_at_real_bearing_elevations(evidence):
    for row in evidence["features"]:
        if "bearing_plane" not in row["class"]:
            continue
        datum = evidence["datums"][row["part"]]
        world = machining.to_world(row["plane_point_local_mm"], datum)
        assert world == pytest.approx(row["plane_point_world_mm"], abs=1e-8)
        assert world[2] == pytest.approx(225. if row["class"] == "header_bearing_plane" else 0., abs=1e-8)
        normal = [sum(row["plane_normal_local"][i]*datum["axes_world"][i][j] for i in range(3)) for j in range(3)]
        assert normal == pytest.approx([0., 0., -1.], abs=1e-8)
        assert row["actual_face_area_mm2"] == pytest.approx(row["actual_face_area_in2"]*25.4**2)


def test_all_drawing_sources_and_artifacts_are_bound(evidence):
    directory = DIRECTORY/"drawings"
    manifest = json.loads((directory/"manifest.json").read_text())
    assert manifest["candidate"] == evidence["candidate"]
    assert set(manifest["artifact_sha256"]) == {n+".svg" for n in evidence["datums"]} | {"vertices.csv"}
    for path, digest in manifest["source_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    for name, digest in manifest["artifact_sha256"].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest
