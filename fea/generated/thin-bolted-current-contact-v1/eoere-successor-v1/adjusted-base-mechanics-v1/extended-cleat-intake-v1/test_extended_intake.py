"""Current JSON metadata and fake-solid checks; no genuine CAD or mechanics."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("extended_cleat_export_under_test", OWN.with_name("export.py"))
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
MANIFEST = OWN.parent.parent / "parent-authority-v1/extended-cleat-manifest.json"
MANIFEST_SHA = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"


@pytest.fixture(scope="module")
def prepared():
    return x.prepare(MANIFEST, MANIFEST_SHA)


def test_actual_current_metadata_closes_and_only_two_gross_blanks_change(prepared):
    p, old, report, panels, pins = prepared
    ref = p["parent_base_manifest"]
    parent = x.a.preflight(x.ROOT / ref["path"], ref["sha256"])
    assert p["geometry"] == x.GEOMETRY and p["parent_base_geometry"] == x.PARENT
    current = json.loads((x.ROOT / x.GEOMETRY["path"]).read_bytes())
    assert current["source_sha256"].items() <= pins.items()
    assert (len(report["finished_solids"]), len(panels), len(p["physical_owner_gravity_descriptors"])) == (22, 6, 150)
    assert (len(p["shaft_descriptors"]), len(p["fitting_ports"]), len(p["hillman_rows"])) == (100, 88, 66)
    assert len(p["auxiliary_metal_gravity_descriptors"]) == 274
    assert sum(len(r["holes"]) for r in p["all_factory_holes"]) == 176
    assert len(p["required_own_wall_queries"]) == 60
    assert sum(r["receiver"] in x.CLEATS for r in p["required_own_wall_queries"]) == 8
    assert p["hillman_rows"] == parent["hillman_rows"]
    assert p["current_panel_machining_descriptors"] == parent["current_panel_machining_descriptors"]
    assert p["floor_descriptors"] == parent["floor_descriptors"]
    before = x.a.indexed(parent["gross_raw_timber_rows"], "name")
    profiles = x.a.indexed(p["gross_raw_timber_rows"], "name")
    assert {name for name, row in profiles.items() if row != before[name]} == x.CLEATS
    for name in x.CLEATS:
        row = profiles[name]
        assert row["axis"] == [0., 0., 1.]
        assert row["end"][2] == pytest.approx(500.8860828293809)
        assert row["end"][2]-row["start"][2] == pytest.approx(361.1860828293809)
        assert row["width_mm"] == pytest.approx(38.1) and row["depth_mm"] == 139.7
        assert not row["raw_profile_source"]["grain_inspected"]
        assert not row["finished_cut_stiffness_or_resistance_qualified"]
        source = next(r["source"] for r in p["physical_owner_gravity_descriptors"] if r["id"] == name)
        assert source["sha256"] in pins.values()
        assert source["raw_polygon_volume_mm3"] < 38.1*139.7*361.1860828293809
    assert p["panel_refresh"]["fresh_aperture_K_mass_and_screw_port_panels"] == ["kicker_right", "main_lower_right", "main_upper_right"]
    assert not p["candidate_CAD_K_factorization_q_force_or_native_run_performed"]
    assert not p["historical_q_forces_or_passes_transferred"]
    assert not any(p["release"].values())
    assert "cadquery" not in sys.modules
    assert len(old["shafts"]) == 100


@pytest.mark.parametrize("field, mutate, match", [
    ("axes", lambda rows: rows[0]["point_xyz_mm"].__setitem__(0, 999.), "all100 shaft"),
    ("screw_axes", lambda rows: rows[0].__setitem__("receiver", "other"), "all66 screw"),
    ("changed_finished_solids", lambda rows: rows.append(copy.deepcopy(rows[0])), "only two finished"),
])
def test_extension_record_drift_rejected(field, mutate, match):
    current = json.loads((x.ROOT / x.GEOMETRY["path"]).read_bytes())
    parent = json.loads((x.ROOT / x.PARENT["path"]).read_bytes())
    mutate(current[field])
    with pytest.raises(ValueError, match=match):
        x.close_extension(current, parent)


def test_changed_gross_grain_not_silently_inherited(prepared):
    ref = prepared[0]["parent_base_manifest"]
    p = x.a.preflight(x.ROOT / ref["path"], ref["sha256"])
    current = json.loads((x.ROOT / x.GEOMETRY["path"]).read_bytes())
    row = next(r for r in p["gross_raw_timber_rows"] if r["name"] == "eoere_cleat_left")
    row["raw_profile_source"]["basis_grain_u_v_xyz"][0] = [1., 0., 0.]
    ex, m = x.a.generic()
    with pytest.raises(ValueError, match="declared cleat grain"):
        x.extend_descriptors(p, current, ex, m)


@pytest.mark.parametrize("mutate", [
    lambda m: m.__setitem__("optional_2026_extra", True),
    lambda m: m.__setitem__("parent_model_review_approved", False),
    lambda m: m["geometry"].__setitem__("sha256", "foreign"),
])
def test_bad_manifest_stops_before_parent_metadata_intake(tmp_path, monkeypatch, mutate):
    manifest = json.loads(MANIFEST.read_bytes())
    mutate(manifest)
    path = tmp_path / "bad-manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(x.a, "preflight", lambda *_: pytest.fail("parent metadata intake reached"))
    with pytest.raises(ValueError, match="approved exact extended-cleat OFF"):
        x.prepare(path, x.a.sha(path))


def test_cached_descriptor_authority_cannot_enable_solve(tmp_path):
    manifest = json.loads(MANIFEST.read_bytes())
    manifest["readiness"]["candidate_assembly_or_solve"] = True
    path = tmp_path / "wrong-authority.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="cached-descriptor-only parent authority"):
        x.checked_manifest(path, x.a.sha(path))


def test_historical_review_computational_overlap_must_match(monkeypatch):
    read_ref = x.a.read_ref
    def contradicted(ref, pins):
        result = read_ref(ref, pins)
        if ref["path"].endswith("actual-output-review.json"):
            result["source_sha256"][x.a.INTERVAL_METHOD] = "synthetic-conflicting-computational-pin"
        return result
    monkeypatch.setattr(x.a, "read_ref", contradicted)
    with pytest.raises(ValueError, match="historical review computational overlap differs"):
        x.prepare(MANIFEST, MANIFEST_SHA)


def test_wrong_manifest_raw_sha_stops_before_json_read(tmp_path):
    path = tmp_path / "not-json"
    path.write_text("not JSON")
    with pytest.raises(ValueError, match="exact frozen parent manifest SHA"):
        x.checked_manifest(path, "wrong")


def test_native_mode_requires_parent_marker_before_source_intake(monkeypatch):
    monkeypatch.delenv("EOERE_PARENT_SERIALIZED_EXTRACTION", raising=False)
    monkeypatch.setattr(x, "prepare", lambda *_: pytest.fail("source intake reached"))
    with pytest.raises(ValueError, match="parent serialized extraction marker"):
        x.export_native(None, None, None, None)


def test_same_geometry_foreign_manifest_slot_stops_before_native_export(tmp_path, monkeypatch, prepared):
    monkeypatch.setenv("EOERE_PARENT_SERIALIZED_EXTRACTION", "1")
    monkeypatch.setattr(x, "prepare", lambda *_: prepared)
    monkeypatch.setattr(x.e, "export_native", lambda *_: pytest.fail("native exporter reached"))
    path = tmp_path / "slot.json"
    path.write_text(json.dumps({"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                               "approved_geometry_sha256": x.GEOMETRY["sha256"],
                               "approved_manifest_sha256": "foreign"}))
    with pytest.raises(ValueError, match="exact frozen intake manifest SHA"):
        x.export_native(MANIFEST, MANIFEST_SHA, path, x.a.sha(path))


def test_fake_descriptor_export_wrapper_preserves_current_sources_and_contract(tmp_path, monkeypatch, prepared):
    monkeypatch.setenv("EOERE_PARENT_SERIALIZED_EXTRACTION", "1")
    monkeypatch.setattr(x, "prepare", lambda *_: prepared)
    p = prepared[0]
    def fake_export(*args):
        actual = x.e.prepare(*args[:2])[0]
        assert actual is p
        return {"geometry": actual["geometry"], "source_sha256": actual["source_sha256"]}
    monkeypatch.setattr(x.e, "export_native", fake_export)
    path = tmp_path / "synthetic-slot.json"
    path.write_text(json.dumps({"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                               "approved_geometry_sha256": x.GEOMETRY["sha256"],
                               "approved_manifest_sha256": MANIFEST_SHA}))
    result = x.export_native(MANIFEST, MANIFEST_SHA, path, x.a.sha(path))
    assert result["schema"] == "eoere_extended_cleat_cached_source_export/v1"
    assert result["manifest"]["sha256"] == MANIFEST_SHA
    for key in ("parameters", "material_scenario", "support", "case_provider", "panel_refresh"):
        assert result[key] == p[key]
    assert result["geometry"] == x.GEOMETRY


def test_reused_genuine_importer_with_existing_tiny_fake_solid_fixture(tmp_path):
    source = x.EXPORT.with_name("test_export.py")
    spec = importlib.util.spec_from_file_location("frozen_fake_solid_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ex, report, panels, pins, q, calls = module.fake_importer(tmp_path)
    before = copy.deepcopy(report)
    bodies, observations, proof = x.e.import_current(ex, report, panels, pins, q)
    assert len(bodies) == len(observations) == len(calls) == len(set(calls)) == 28
    assert observations[0]["volume_mm3"] == 24. and observations[0]["center_xyz_mm"] == [1., 2., 3.]
    assert report == before and proof["original_import_function_restored"]
    assert not proof["derived_bounds_claimed_as_independent_prior_metadata"]
    assert "cadquery" not in sys.modules


def test_existing_output_stops_before_any_source_intake(tmp_path, monkeypatch):
    path = tmp_path / "preserved.json"
    path.write_text("preserved")
    monkeypatch.setattr(sys, "argv", ["export.py", "--manifest", "missing", "--manifest-sha256", "none", "--out", str(path), "--extract"])
    monkeypatch.setattr(x, "export_native", lambda *_: pytest.fail("native intake reached"))
    with pytest.raises(ValueError, match="preserve prior descriptor output"):
        x.main()
    assert path.read_text() == "preserved"


def test_source_plan_uses_current_prepare_without_native_methods(monkeypatch, prepared):
    monkeypatch.setattr(x, "prepare", lambda *_: prepared)
    monkeypatch.setattr(x.a, "generic", lambda: pytest.fail("native or generic methods unexpectedly loaded"))
    result = x.source_plan(MANIFEST, MANIFEST_SHA)
    assert result["schema"] == "eoere_extended_cleat_cached_source_export_plan/v1"
    assert result["native_queries_deferred"] and result["optional_2026_extra"] is False
    assert result["serial_slot_API"]["approved_manifest_sha256"] == MANIFEST_SHA
    assert result["candidate_K_q_forces_or_acceptance"] is None
