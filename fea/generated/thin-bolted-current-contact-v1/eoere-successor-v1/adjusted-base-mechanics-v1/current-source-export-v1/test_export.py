"""Cheap fake-solid fixtures exercising the unchanged real importer and guards."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("deferred_source_export_under_test", OWN.with_name("export.py"))
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def fake_importer(tmp_path):
    ex, _ = e.a.generic()
    calls, bodies, rows, pins = [], {}, [], {}

    class Shape:
        @staticmethod
        def importBrep(path):
            calls.append(path)
            return bodies[path]

        def Volume(self):
            return 24.

        def Center(self):
            return SimpleNamespace(toTuple=lambda: (1., 2., 3.))

        def BoundingBox(self):
            return SimpleNamespace(xmin=0., xmax=2., ymin=0., ymax=4., zmin=0., zmax=6.)

    for i in range(28):
        path = tmp_path / f"fake-{i}.brep"
        path.write_text("synthetic-not-a-BREP")
        row = {"id": f"body-{i}", "path": str(path), "sha256": e.a.sha(path), "volume_mm3": 24.}
        if i % 2:
            row["bounds_xyz_mm"] = [[0., 2.], [0., 4.], [0., 6.]]
        rows.append(row)
        pins[str(path)] = row["sha256"]
        bodies[str(path)] = Shape()
    q = SimpleNamespace(cq=SimpleNamespace(Shape=Shape),
                        distance=SimpleNamespace(brep_sha=lambda body: "synthetic-container"),
                        bridge=SimpleNamespace(strict_solid=lambda body, ref: (body, {"synthetic": True})),
                        atlas=SimpleNamespace(_bounds=lambda body, label: [0., 2., 0., 4., 0., 6.]))
    return ex, {"finished_solids": rows[:22]}, rows[22:], pins, q, calls


def test_missing_bounds_are_observations_genuine_importer_one_load_each_and_no_source_mutation(tmp_path):
    ex, report, panels, pins, q, calls = fake_importer(tmp_path)
    prior = copy.deepcopy(report)
    original = q.cq.Shape.importBrep
    bodies, observed, proof = e.import_current(ex, report, panels, pins, q)
    assert len(bodies) == len(observed) == len(calls) == len(set(calls)) == 28
    assert len(proof["missing_bounds_measured_owner_ids"]) == 14
    assert not proof["derived_bounds_claimed_as_independent_prior_metadata"]
    assert q.cq.Shape.importBrep == original
    assert report == prior
    assert all("bounds_xyz_mm" not in r["source"] for r in observed if not r["bounds_were_supplied_prior_metadata"])
    assert all(r["center_xyz_mm"] == [1., 2., 3.] for r in observed)


def test_original_volume_failure_preserved_and_import_patch_restored(tmp_path):
    ex, report, panels, pins, q, _ = fake_importer(tmp_path)
    panels[-1]["volume_mm3"] = 999.
    original = q.cq.Shape.importBrep
    with pytest.raises(ValueError, match="cached volume join differs"):
        e.import_current(ex, report, panels, pins, q)
    assert q.cq.Shape.importBrep == original


def test_contradictory_supplied_COM_rejected(tmp_path):
    ex, report, panels, pins, q, _ = fake_importer(tmp_path)
    report["finished_solids"][0]["center_of_mass_xyz_mm"] = [999., 0., 0.]
    with pytest.raises(ValueError, match="own source COM differs"):
        e.import_current(ex, report, panels, pins, q)


def test_wall_reuse_requires_identical_source_and_axis_and_calls_actual_fallback():
    ex, m = e.a.generic()
    old = json.loads((e.ROOT / e.a.OLD_INPUT).read_bytes())
    report = {"axes": [copy.deepcopy(r["source_axis"]) for r in old["shafts"]]}
    observations = copy.deepcopy(old["finished_body_observations"])
    profiles = {r["name"]: r for r in old["timber_rows"]}
    calls = []
    q = SimpleNamespace(bore=SimpleNamespace(finished_bore_wall_intervals=lambda *args: calls.append(args) or {"fresh": True}))
    query, names, proof = e.wall_cache(ex, old, report, observations, profiles, q, m)
    axis = report["axes"][0]
    body = object()
    names[id(body)] = axis["receivers"][0]
    vector = lambda values: SimpleNamespace(toTuple=lambda: tuple(values))
    result = query(body, vector(axis["point_xyz_mm"]), vector(m.unit(axis["direction_xyz"])), axis["bore_diameter_mm"]/2)
    assert result["full_wall_intervals_mm"]
    assert len(proof["reused"]) == 1 and not calls
    changed = [axis["point_xyz_mm"][0]+0.001, *axis["point_xyz_mm"][1:]]
    assert query(body, vector(changed), vector(m.unit(axis["direction_xyz"])), axis["bore_diameter_mm"]/2) == {"fresh": True}
    assert len(proof["fresh"]) == len(calls) == 1
    next(row for row in observations if row["id"] == axis["receivers"][0])["source"]["sha256"] = "synthetic-changed-source"
    query, names, proof = e.wall_cache(ex, old, report, observations, profiles, q, m)
    names[id(body)] = axis["receivers"][0]
    assert query(body, vector(axis["point_xyz_mm"]), vector(m.unit(axis["direction_xyz"])), axis["bore_diameter_mm"]/2) == {"fresh": True}
    assert not proof["reused"]


def test_floor_translation_confirmed_from_own_points_and_incompatible_face_rejected():
    p = {"floor_descriptors": [{"host": "moved-post", "normal_reference_points_xyz_mm": [[x, y, 0.] for x in (11.75, 49.85) for y in (-175.7, -36.)]}]}
    points = p["floor_descriptors"][0]["normal_reference_points_xyz_mm"]
    q = SimpleNamespace(floor=SimpleNamespace(level_face_points=lambda body, down: points))
    assert e.floor_observations(p, {"moved-post": object()}, q)[0]["own_floor_face_confirmed_from_current_cached_solid"]
    q.floor.level_face_points = lambda body, down: [[0., 0., 0.]]*4
    with pytest.raises(ValueError, match="floor face differs"):
        e.floor_observations(p, {"moved-post": object()}, q)


def test_native_mode_refused_before_any_current_source_read_without_parent_marker(monkeypatch):
    monkeypatch.delenv("EOERE_PARENT_SERIALIZED_EXTRACTION", raising=False)
    monkeypatch.setattr(e, "prepare", lambda *args: pytest.fail("source intake reached without parent marker"))
    with pytest.raises(ValueError, match="parent serialized extraction marker"):
        e.export_native(None, None, None, None)


@pytest.mark.parametrize("record", [
    {"status": "BUSY", "cached_descriptor_extraction_authorized": True, "approved_geometry_sha256": "current"},
    {"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True, "approved_geometry_sha256": "other"},
])
def test_busy_or_foreign_geometry_slot_rejected(tmp_path, monkeypatch, record):
    monkeypatch.setenv("EOERE_PARENT_SERIALIZED_EXTRACTION", "1")
    path = tmp_path / "slot.json"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="slot does not authorize"):
        e.slot(path, e.a.sha(path), "current")
