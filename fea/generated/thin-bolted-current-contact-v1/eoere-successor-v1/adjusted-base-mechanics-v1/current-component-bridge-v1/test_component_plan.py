"""Metadata/source checks only; no current field or geometry engine execution."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

OWN = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("current_component_plan_test_subject", OWN / "component_plan.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


@pytest.fixture
def sources():
    return {key: json.loads(m.checked_bytes(source)) for key, source in m.ARTIFACTS.items() if key != "gate"}


def metadata(s):
    return m.verify_current_metadata(s["descriptors"], s["geometry"], s["parent_geometry"],
                                     s["descriptor_review"], s["preserved_metadata"])


def seats(s):
    return m.nominal_seat_carry(s["descriptors"], s["geometry"], s["seat_audit"], s["seat_details"], s["extension_review"])


def test_actual_pinned_source_plan_without_heavy_imports():
    code = """
import builtins, importlib.util, json, pathlib, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'cadquery', 'OCP', 'numpy', 'scipy', 'mini_moonboard'}:
        raise AssertionError('source-only plan attempted numerical/CAD import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
p = pathlib.Path(sys.argv[1])
s = importlib.util.spec_from_file_location('isolated_current_component_plan', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
plan = m.component_plan()
assert not hasattr(m, 'consume')
assert plan['status'] == 'SOURCE_PLAN_ONLY_CONSUMER_DEFERRED'
assert plan['complete_joint_resistance'] is None
assert plan['census']['flange_backing_cells'] == 352
assert len([r for r in plan['finished_sources'] if r['changed_since_preserved']]) == 15
assert plan['nominal_seat_geometry']['nominal_wood_seats'] == 112
assert plan['nominal_seat_geometry']['old_actions_or_strength_transferred'] is False
assert plan['future_admission']['gate']['sha256'] == '4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643'
assert not any(plan['release'].values())
print(json.dumps({'pins': len(plan['source_sha256']), 'method_files': len(plan['methods'])}))
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, str(OWN / "component_plan.py")],
                            cwd=m.ROOT, text=True, capture_output=True, check=True)
    assert json.loads(result.stdout) == {"pins": 1099, "method_files": 16}


@pytest.mark.parametrize("mutation, match", [
    (lambda s: s["descriptors"].update(geometry=m.ARTIFACTS["parent_geometry"]), "exact current geometry"),
    (lambda s: s["descriptors"].update(manifest=m.ARTIFACTS["parent_manifest"]), "exact current geometry"),
    (lambda s: s["descriptors"]["shafts"][0]["source_axis"].update(grip_mm=40), "own shaft source"),
    (lambda s: s["descriptors"]["shafts"][0]["ends"][0].update(support_s_mm=0), "geometric end offsets"),
    (lambda s: s["descriptors"]["hillman_rows"][0]["source_screw_descriptor"].update(receiver="wrong"), "66 current ordered"),
    (lambda s: s["descriptors"]["finished_body_observations"][0]["source"].update(sha256="0" * 64), "15 changed finished"),
    (lambda s: s["descriptors"]["physical_owner_gravity_rows"].pop(), "owner/wall/port/contact census"),
    (lambda s: s["descriptors"]["current_panel_machining_descriptors"]["features"].pop(), "hole/end/machining census"),
    (lambda s: s["descriptors"]["flange_shared_face_patches"][0]["cells"].pop(), "16 backing cells"),
])
def test_current_metadata_rejects_stale_or_incomplete_inputs(sources, mutation, match):
    mutation(sources)
    with pytest.raises(ValueError, match=match):
        metadata(sources)


@pytest.mark.parametrize("mutation, match", [
    (lambda s: s["extension_review"]["body_checks"][0].update(lost_old_volume_mm3=1), "old cleat volume"),
    (lambda s: s["seat_details"]["washer_seat_rows"][0].update(full_modeled_support=False), "supported seat identity"),
    (lambda s: s["seat_details"]["washer_seat_rows"][0].update(bounding_OD_mm=20), "annulus must bound"),
    (lambda s: s["seat_details"]["washer_seat_rows"][0].update(current_host_support_point_xyz_mm=[0, 0, 0]), "seat source/point join"),
    (lambda s: s["seat_details"]["washer_seat_rows"][0]["solid_source"].update(sha256="0" * 64), "seat host source"),
    (lambda s: s["seat_details"]["washer_seat_rows"].pop(), "112 wood seat IDs"),
    (lambda s: s["extension_review"]["bore_and_land_checks"][0].update(axis_id="wrong"), "eight cleat bore/land"),
])
def test_nominal_seat_carry_rejects_broken_geometry_proofs(sources, mutation, match):
    mutation(sources)
    with pytest.raises(ValueError, match=match):
        seats(sources)


def test_tiny_duplicate_and_source_byte_controls(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="unique"):
        m.indexed([{"id": "same"}, {"id": "same"}], "id")
    path = tmp_path / "source.json"
    path.write_text('{"tiny": 1}\n')
    source = m.ref("source.json", hashlib.sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr(m, "ROOT", tmp_path)
    assert json.loads(m.checked_bytes(source)) == {"tiny": 1}
    path.write_text('{"tiny": 2}\n')
    with pytest.raises(ValueError, match="exact source bytes"):
        m.checked_bytes(source)
    with pytest.raises(ValueError, match="repository source"):
        m.checked_bytes(m.ref("../outside.json", "0" * 64))


def test_historical_force_values_are_not_component_inputs(sources):
    original = seats(sources)
    changed = copy.deepcopy(sources)
    changed["seat_details"]["old_brace_axis_actions"] = "deliberately unusable old force payload"
    changed["seat_details"]["unsupported_stack_own_case_ports"] = None
    changed["seat_audit"]["reused_single_bolt_yield_components"] = None
    assert seats(changed) == original
