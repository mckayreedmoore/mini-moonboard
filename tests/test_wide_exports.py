"""Lightweight publication checks; no STEP import or CAD construction."""
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import pytest

KEY = "wide-principal-development"
DIRECTORY = Path("exports")/KEY
REFERENCE = Path("docs/panel-insert-reference.json")


def test_export_rejects_changed_inherited_reference_before_geometry(tmp_path, monkeypatch):
    from mini_moonboard import wide_exports as exporter

    reference = REFERENCE.read_text()
    monkeypatch.chdir(tmp_path)
    REFERENCE.parent.mkdir()
    REFERENCE.write_text(reference)
    baseline = Path("exports/panel-insert-development/manifest.json")
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps({"sources": {str(REFERENCE): "0"*64}}))
    Path("mini_moonboard").mkdir()
    for name in ("wide_frame.py", "wide_exports.py"):
        Path("mini_moonboard", name).write_text("fixture source")
    monkeypatch.setattr(exporter.model, "connections", lambda: pytest.fail("Reached geometry after invalid inherited reference"))
    with pytest.raises(RuntimeError, match="Historical dependency changed"):
        exporter.export()
    assert not Path("exports", KEY).exists()


def table(suffix):
    with (DIRECTORY/f"{KEY}_{suffix}.csv").open() as stream:
        return list(csv.DictReader(stream))


@pytest.fixture(scope="module")
def publication():
    return (json.loads((DIRECTORY/"manifest.json").read_text()),
            json.loads((Path("site/hybrid")/KEY/"parts.json").read_text()),
            json.loads(REFERENCE.read_text()))


def test_inventory_source_closure_and_artifact_hashes(publication):
    manifest, viewer, _ = publication
    baseline_path = Path("exports/panel-insert-development/manifest.json")
    baseline = json.loads(baseline_path.read_text())
    assert set(manifest["sources"]) == set(baseline["sources"]) | {
        str(baseline_path), str(REFERENCE), "mini_moonboard/wide_frame.py", "mini_moonboard/wide_exports.py"}
    assert all(manifest["sources"][p] == sha for p, sha in baseline["sources"].items())
    assert viewer["design"] == manifest["design"]
    assert viewer["design"]["key"] == KEY
    assert "NOT build-ready" in viewer["design"]["status"]
    assert "unqualified" in viewer["design"]["status"]
    old = json.loads(Path("site/hybrid/panel-insert-development/parts.json").read_text())
    names = {p["name"] for p in viewer["parts"]}
    inserts = {p["name"] for p in viewer["parts"] if p["fabrication"]["kind"] == "insert"}
    assert len(viewer["parts"]) == len(names) == 291
    assert len(inserts) == 56
    assert inserts == {p["name"] for p in old["parts"] if p["fabrication"]["kind"] == "insert"}
    assert sum(n.startswith("clip_") for n in names) == 18
    assert sum(n.startswith("fastener_clip_") for n in names) == 108
    assert {f"base_post_center_{side}_{end}" for side in ("left", "right") for end in ("front", "rear")} <= names
    assert inserts == {"insert_"+r["connection"] for r in table("panel_drilling")}
    assert {p["path"] for p in viewer["parts"]} == {f"hybrid/{KEY}/models/{n}.stl" for n in names}
    assert set(manifest["viewer_artifacts"]) == {p["path"] for p in viewer["parts"]} | {f"hybrid/{KEY}/parts.json"}
    assert set(manifest["artifacts"]) == {KEY+s for s in
        (".step", "_front.png", "_parts.csv", "_connections.csv", "_panel_drilling.csv")}
    for root, category in ((Path("."), "sources"), (DIRECTORY, "artifacts"), (Path("site"), "viewer_artifacts")):
        for name, sha in manifest[category].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, name


def test_dual_units_and_separate_pilot_body_reservations(publication):
    _, viewer, reference = publication
    parts = {p["name"]: p for p in viewer["parts"]}
    rows = table("parts")
    assert len(rows) == len(parts)
    assert {r["part"] for r in rows} == parts.keys()
    for row in rows:
        for axis, dimension in enumerate(parts[row["part"]]["fabrication"]["dimensions_mm"], 1):
            assert float(row[f"dimension_{axis}_mm"]) == pytest.approx(dimension)
            assert float(row[f"dimension_{axis}_in"])*25.4 == pytest.approx(dimension, abs=.001)
    connections = table("connections")
    assert len(connections) == len({r["connection"] for r in connections}) == 188
    for row in connections:
        for field in ("length", "diameter", "grip"):
            assert float(row[field+"_in"])*25.4 == pytest.approx(float(row[field+"_mm"]), abs=.001)
    drilling = table("panel_drilling")
    assert len(drilling) == len({r["connection"] for r in drilling}) == 56
    indexed = {r["connection"]: r for r in connections}
    insert, screw, assumed = (reference[k] for k in ("insert", "screw", "project_geometry_assumptions"))
    for row in drilling:
        c = indexed[row["connection"]]
        assert c["kind"] == "screw"
        assert parts["fastener_"+row["connection"]]["fabrication"]["kind"] == "screw"
        assert float(c["length_mm"]) == pytest.approx(screw["nominal_overall_length"])
        assert float(c["diameter_mm"]) == pytest.approx(screw["nominal_thread_diameter"])
        assert parts["insert_"+row["connection"]]["fabrication"]["dimensions_mm"] == pytest.approx([
            insert["nominal_length"], insert["nominal_outer_diameter"], insert["nominal_outer_diameter"]])
        expected = {"panel_clearance": assumed["panel_clearance_bore_diameter"],
            "receiver_pilot": insert["pilot_diameter_inch_recommendation"],
            "receiver_pilot_depth": assumed["pilot_tip_clearance_depth"],
            "insert_nominal_od": insert["nominal_outer_diameter"],
            "insert_max_od_reservation": insert["nominal_outer_diameter"]+insert["drawing_general_tolerance_plus_minus"]}
        for name, value in expected.items():
            assert float(row[name+"_mm"]) == pytest.approx(value, abs=.001)
            assert float(row[name+"_in"])*25.4 == pytest.approx(value, abs=.001)
        assert float(row["receiver_pilot_mm"]) < float(row["insert_nominal_od_mm"])
        assert row["effective_engagement_mm"] == "unknown"
        assert "not pilot diameter" in row["status"]
        for axis in "xyz":
            assert float(row["receiver_"+axis+"_mm"])-float(row["face_"+axis+"_mm"]) == pytest.approx(
                assumed["face_and_kicker_thickness"]*float(row["axis_"+axis]), abs=.002)


def test_all_stl_bounds_and_analytical_insert_screw_volumes(publication):
    _, viewer, reference = publication
    insert, screw = reference["insert"], reference["screw"]
    attachment_names = {"fastener_"+r["connection"] for r in table("panel_drilling")}
    all_lower, all_upper = [math.inf]*3, [-math.inf]*3
    for part in viewer["parts"]:
        data = (Path("site")/part["path"]).read_bytes()
        count = struct.unpack_from("<I", data, 80)[0]
        assert count and len(data) == 84+count*50
        triangles = list(struct.iter_unpack("<12fH", data[84:]))
        lower = [min(min(t[3+a:12:3]) for t in triangles) for a in range(3)]
        upper = [max(max(t[3+a:12:3]) for t in triangles) for a in range(3)]
        assert all(math.isfinite(v) for t in triangles for v in t[:12])
        assert [hi-lo for hi, lo in zip(upper, lower, strict=True)] == pytest.approx(part["viewer_aabb_mm"], abs=.501)
        origin = [(lo+hi)/2 for lo, hi in zip(lower, upper, strict=True)]
        volumes = []
        for t in triangles:
            a, b, c = [tuple(t[3+3*i+j]-origin[j] for j in range(3)) for i in range(3)]
            cross = (b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0])
            volumes.append(sum(a[i]*cross[i] for i in range(3))/6)
        volume = math.fsum(volumes)
        assert volume > 0, part["name"]
        if part["fabrication"]["kind"] == "insert":
            expected = math.pi/4*(insert["nominal_outer_diameter"]**2-screw["nominal_thread_diameter"]**2)*insert["nominal_length"]
            assert volume == pytest.approx(expected, rel=.02), part["name"]
        elif part["name"] in attachment_names:
            r, head = screw["nominal_thread_diameter"]/2, screw["head_diameter_max"]/2
            depth = (head-r)/math.tan(math.radians(screw["head_angle_min_deg"]/2))
            expected = math.pi*r*r*(screw["nominal_overall_length"]-depth)+math.pi*depth/3*(head*head+head*r+r*r)
            assert volume == pytest.approx(expected, rel=.02), part["name"]
        all_lower = [min(a, b) for a, b in zip(all_lower, lower, strict=True)]
        all_upper = [max(a, b) for a, b in zip(all_upper, upper, strict=True)]
    assert all_lower == pytest.approx(viewer["bounds_mm"][0], abs=.501)
    assert all_upper == pytest.approx(viewer["bounds_mm"][1], abs=.501)
