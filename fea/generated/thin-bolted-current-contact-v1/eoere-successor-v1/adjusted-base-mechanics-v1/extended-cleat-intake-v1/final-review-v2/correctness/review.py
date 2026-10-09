"""Independent metadata/fake-only correctness review; no CAD imports or queries."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[8]
TARGET = OWN.parents[2]
FIX = TARGET / "review-fix-v2/export.py"
MANIFEST = TARGET.parent / "parent-authority-v1/extended-cleat-manifest.json"
MANIFEST_SHA = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejects(callback, text):
    try:
        callback()
    except ValueError as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("expected rejection: " + text)


def main():
    fixed = load(FIX, "independent_correctness_reservation")
    x = fixed.load_frozen()
    expected = {
        TARGET / "export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
        TARGET / "test_extended_intake.py": "786cdfb9e8560716ab603d26179ce3a0b5635965d3238e234f669811768fe63a",
        TARGET / "verification.json": "e5b8451c7b6d23822b8909378f2df98e6132e16384900ac20b5c3522b5193544",
        FIX: "93ed36c39b4237cd587498fbb9dd2b2b7e3d275afc2be89302dab178c25d5858",
        FIX.with_name("test_output_reservation.py"): "3ceae6b82c0022493115a9ab0ce0b5a6c54a628337cb30cdb3fe6b1b3018daae",
        FIX.with_name("verification.json"): "a046295fd38714893276dda6f495307821ab2c2545107298bb530d897e7e8ed3",
        MANIFEST: MANIFEST_SHA,
        MANIFEST.with_name("adjusted-base-manifest.json"): "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2",
    }
    assert all(sha(path) == digest for path, digest in expected.items())
    prepared = x.prepare(MANIFEST, MANIFEST_SHA)
    p, old, report, panels, pins = prepared
    current = json.loads((ROOT / x.GEOMETRY["path"]).read_bytes())
    parent = json.loads((ROOT / x.PARENT["path"]).read_bytes())
    assert current["axes"] == parent["axes"] and current["screw_axes"] == parent["screw_axes"]

    # Independently replay source-row ancestry using JSON only, then replace two cleats.
    sources = {r["id"]: copy.deepcopy(r["source"]) for r in old["finished_body_observations"]}
    ancestry, node = [], parent
    while True:
        ancestry.append(node)
        if "parent_geometry" not in node:
            break
        ref = node["parent_geometry"]
        assert sha(ROOT / ref["path"]) == ref["sha256"]
        node = json.loads((ROOT / ref["path"]).read_bytes())
    for node in reversed(ancestry):
        for group in ("finished_solids", "finished_panel_solids", "changed_finished_solids"):
            sources.update({r["id"]: copy.deepcopy(r) for r in node.get(group, []) if r["id"] in sources})
    sources.update({r["id"]: r for r in current["changed_finished_solids"]})
    actual = {r["id"]: r for r in report["finished_solids"] + panels}
    assert sources == actual and len(actual) == 28 and len(report["finished_solids"]) == 22
    assert all(pins[r["path"]] == r["sha256"] for r in actual.values())
    owners = {r["id"]: r for r in p["physical_owner_gravity_descriptors"]}
    assert len(owners) == 150
    assert all(owners[name]["source"] == row for name, row in actual.items())
    assert all(math.isclose(owners[name]["mass_kg"], row["volume_mm3"] * 500e-9) for name, row in actual.items())

    profiles = {r["name"]: r for r in p["gross_raw_timber_rows"]}
    parent_ref = p["parent_base_manifest"]
    before = x.a.preflight(ROOT / parent_ref["path"], parent_ref["sha256"])
    before_profiles = {r["name"]: r for r in before["gross_raw_timber_rows"]}
    assert {name for name in profiles if profiles[name] != before_profiles[name]} == x.CLEATS
    polygon = current["new_cleat_YZ_polygon_mm"]
    area = abs(sum(a[0]*b[1] - b[0]*a[1] for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2
    for name in x.CLEATS:
        row, source = profiles[name], actual[name]
        assert row["axis"] == [0., 0., 1.] and math.isclose(row["width_mm"], 38.1) and math.isclose(row["depth_mm"], 139.7)
        assert math.isclose(math.dist(row["start"], row["end"]), current["maximum_blank_length_mm"])
        assert math.isclose(area * 38.1, source["raw_polygon_volume_mm3"])
        assert math.isclose(source["raw_polygon_volume_mm3"] - source["volume_mm3"], source["preserved_void_volume_mm3"])
        assert source["center_of_mass_xyz_mm"] == owners[name]["center_xyz_mm"]
        assert not row["raw_profile_source"]["grain_inspected"]

    old_sources = {r["id"]: r["source"] for r in old["finished_body_observations"]}
    old_axes = {r["axis_id"]: r["source_axis"] for r in old["shafts"]}
    pairs = {(axis["id"], receiver) for axis in report["axes"] for receiver in axis["receivers"]}
    fresh = {(axis["id"], receiver) for axis in report["axes"] for receiver in axis["receivers"]
             if actual[receiver]["sha256"] != old_sources[receiver]["sha256"]
             or any(axis[key] != old_axes[axis["id"]][key] for key in ("point_xyz_mm", "direction_xyz", "bore_diameter_mm"))}
    assert len(pairs) == 120 and len(fresh) == 60
    assert fresh == {(r["axis_id"], r["receiver"]) for r in p["required_own_wall_queries"]}
    assert sum(receiver in x.CLEATS for _, receiver in fresh) == 8

    ex, m = x.a.generic()
    wall_rows = {(r["axis_id"], r["receiver"]): r for r in old["finished_receiver_wall_queries"]}
    lookup = {(receiver, tuple(axis["point_xyz_mm"])): axis["id"] for axis in report["axes"] for receiver in axis["receivers"]}

    class Vector:
        def __init__(self, *values):
            self.values = values

        def toTuple(self):
            return self.values

    bodies = {name: SimpleNamespace(name=name) for name in actual}
    observations = [{"id": name, "source": source} for name, source in actual.items()]
    def fake_wall(body, point, direction, radius):
        axis_id = lookup[(body.name, tuple(point.toTuple()))]
        row = wall_rows[(axis_id, body.name)]
        return {"full_wall_intervals_mm": copy.deepcopy(row["full_wall_intervals_mm"]), "fake_only": True}

    q = SimpleNamespace(cq=SimpleNamespace(Vector=Vector), bore=SimpleNamespace(finished_bore_wall_intervals=fake_wall),
                        frame=SimpleNamespace(connector_basis=lambda _: SimpleNamespace(tolist=lambda: [[1,0,0],[0,1,0],[0,0,1]])),
                        inventory=SimpleNamespace(hardware_volumes=lambda axis: {r["kind"]: r["volume_mm3"] for r in next(s for s in old["shafts"] if s["axis_id"] == axis["id"])["metal_roles"]}))
    query, names, proof = x.e.wall_cache(ex, old, report, observations, profiles, q, m)
    names.update({id(body): name for name, body in bodies.items()})
    with patch.object(q.bore, "finished_bore_wall_intervals", query):
        shafts, walls = ex.shafts(report, profiles, bodies, q, m)
    assert len(shafts) == 100 and len(walls) == 120 and sum(len(s["ends"]) for s in shafts) == 200
    assert len(proof["fresh"]) == len(proof["reused"]) == 60
    assert all(not end["delivered_bearing_seat_or_pressure_qualified"] for s in shafts for end in s["ends"])
    assert sum(s["kind"] == "steel" for axis in shafts for s in axis["surfaces"]) == 88

    # The complete broad-phase fixture forces all 231 timber and 132 panel/timber pairs.
    atlas_calls, contact_calls = [], []
    for body in bodies.values():
        body.BoundingBox = lambda: SimpleNamespace(xmin=0, xmax=1, ymin=0, ymax=1, zmin=0, zmax=1)
    atlas = SimpleNamespace(source_face_records=lambda name, body: atlas_calls.append(name) or [])
    geometry = SimpleNamespace(find_patches=lambda first, second, *args, **kwargs: contact_calls.append((first, second)) or [])
    contact_q = SimpleNamespace(atlas=atlas, geometry=geometry)
    _, _, census, _ = ex.contact_bank(bodies, sorted(profiles), old["panel_ids"], contact_q, p["parameters"])
    assert len(set(atlas_calls)) == 28 and len(contact_calls) == len(census) == 363

    flange_calls = []
    def fake_face(pose, flange, sign, scenario, query_methods, vectors):
        return SimpleNamespace(normal=[0., 0., 1.]), 100., [0., 0., 1.]
    flange_q = SimpleNamespace(atlas=SimpleNamespace(source_face_records=lambda name, mask: [{"signature": {"oriented_normal_xyz": [0., 0., -1.]}}]),
                               geometry=SimpleNamespace(find_patches=lambda first, second, *args, **kwargs: flange_calls.append((first, second)) or []))
    with patch.object(ex, "fitting_face", fake_face):
        domains, _, _ = ex.flange_bank(p["fitting_poses"], report, bodies, {name: [] for name in bodies}, flange_q, m, p["parameters"])
    assert len(domains) == len(flange_calls) == 88
    assert {(r["fitting"], r["model_port_id"], r["receiver"]) for r in domains} == {
        (port["angle_id"], port["model_port_id"], next(a["receiver"] for axis in report["axes"] for a in axis["attachments"]
         if a["angle_id"] == port["angle_id"] and ex.port_id(a["flange"], a["transverse"]) == port["model_port_id"])) for port in p["fitting_ports"]}

    floor_points = {r["host"]: r["normal_reference_points_xyz_mm"] for r in p["floor_descriptors"]}
    floor_calls = []
    floor_q = SimpleNamespace(floor=SimpleNamespace(level_face_points=lambda body, down: floor_calls.append(body.name) or floor_points[body.name]))
    floors = x.e.floor_observations(p, bodies, floor_q)
    assert len(floors) == len(floor_calls) == 8 and sum(len(r["observed_normal_reference_points_xyz_mm"]) for r in floors) == 32

    with tempfile.TemporaryDirectory(prefix="intake-correctness-fake-") as temporary:
        temp = Path(temporary)
        source_only = fixed.export_to_file(MANIFEST, MANIFEST_SHA, temp / "source-only.json")
        assert source_only["schema"] == "eoere_extended_cleat_cached_source_export_plan/v1"
        assert len(source_only["source_sha256"]) == 1077 and not source_only["release"]["structural"]
        assert source_only["geometry"] == x.GEOMETRY and source_only["candidate_K_q_forces_or_acceptance"] is None
        assert source_only["fresh_wall_rows_expected"] == p["required_own_wall_queries"]
        native_calls = []
        base_slot = {"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                     "approved_geometry_sha256": x.GEOMETRY["sha256"], "approved_manifest_sha256": MANIFEST_SHA,
                     "fixture_only_never_parent_issued": True}
        with patch.dict(os.environ, {"EOERE_PARENT_SERIALIZED_EXTRACTION": "1"}), patch.object(x, "prepare", return_value=prepared), patch.object(x.e, "export_native", side_effect=lambda *args: native_calls.append(args) or {"source_sha256": pins}):
            for key, value, message in (("status", "BUSY", "parent slot does not authorize"),
                                        ("cached_descriptor_extraction_authorized", False, "parent slot does not authorize"),
                                        ("approved_geometry_sha256", "wrong", "parent slot does not authorize"),
                                        ("approved_manifest_sha256", "wrong", "exact frozen intake manifest")):
                slot = {**base_slot, key: value}
                slot_path = temp / (key + ".json")
                slot_path.write_text(json.dumps(slot))
                rejects(lambda: x.export_native(MANIFEST, MANIFEST_SHA, slot_path, sha(slot_path)), message)
            rejects(lambda: x.export_native(MANIFEST, MANIFEST_SHA, slot_path, "wrong"), "exact parent serial-slot")
            assert not native_calls
        x.a.verify(source_only["source_sha256"])
    assert "cadquery" not in sys.modules and "OCP" not in sys.modules and "numpy" not in sys.modules
    assert all(sha(path) == digest for path, digest in expected.items())
    receipt = {
        "schema": "eoere_extended_cleat_final_correctness_review/v2", "status": "PASS_NO_SUBSTANTIAL_FINDINGS",
        "scope": "Frozen cached-solid metadata intake and corrected output reservation only",
        "findings": [], "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in expected.items()},
        "review_script_sha256": sha(OWN), "source_closure": {"verified_pins": 1077, "before_after_unchanged": True},
        "independent_checks": {"json_only_current_finished_source_composition": 28, "all_owner_descriptors": 150,
            "gross_profiles": 22, "changed_gross_profiles": 2, "cleat_maximum_blank_mm": current["maximum_blank_length_mm"],
            "declared_cleat_grain": "+Z, uninspected", "all_current_shaft_records": 100, "preserved_screws": 66,
            "source_derived_fresh_walls": 60, "fresh_cleat_walls": 8, "fake_wall_reuse": 60,
            "fake_complete_shaft_external_seats": 200, "fake_atlas_owners": 28,
            "fake_complete_broadphase_pair_queries": 363, "fake_own_flange_queries": 88,
            "fake_own_floor_observations": 8, "fake_floor_points": 32, "invalid_slot_controls": 5,
            "invalid_slot_native_callbacks": 0, "corrected_source_only_api": True},
        "session_pytest_results": {"test_extended_intake.py": "17 passed in 2.32s",
            "review-fix-v2/test_output_reservation.py": "6 passed in 1.66s", "current-source-export-v1/test_export.py": "8 passed in 0.27s"},
        "actual_BREP_metadata_extraction_CAD_K_q_loads_native_browser_or_physical_work": False,
        "parent_authorization_or_serial_slot_issued": False,
        "limits": ["All shaft/contact/floor geometry used here is synthetic; current genuine source queries remain unperformed.",
            "Parent owns same-manifest slot issuance and serialized extraction; this review grants no extraction authorization.",
            "Current panel bank, force bridge, field admission, complete joint resistance and release remain separate unresolved duties."]}
    with OWN.with_name("receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "verified_pins": 1077, "findings": 0, "fake_shaft_seats": 200}))


if __name__ == "__main__":
    main()
