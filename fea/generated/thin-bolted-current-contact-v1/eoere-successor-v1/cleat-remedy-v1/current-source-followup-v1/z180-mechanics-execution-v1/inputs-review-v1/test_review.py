"""Inert source-review controls. No saved Z180 input is constructed or reviewed."""
from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_independent_input_review_inert_fixture", OWN.with_name("review.py"))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def cross(a, b):
    return [a[(i + 1) % 3] * b[(i + 2) % 3] - a[(i + 2) % 3] * b[(i + 1) % 3] for i in range(3)]


def synthetic():
    """Arithmetic/census witnesses only; no real candidate geometry or sources."""
    panels = ["main_upper_left", "main_upper_right", "main_lower_left", "main_lower_right", "kicker_left", "kicker_right"]
    roster = [("timber-" + str(i), "timber") for i in range(22)] + [("fitting-" + str(i), "fitting") for i in range(22)]
    roster += [(name, "panel") for name in panels] + [("shaft-" + str(i), "shaft") for i in range(100)]
    owners = [{"id": name, "kind": kind, "mass_kg": 1. if i < 149 else 191.908938620187 - 149.,
               "center_xyz_mm": [float(i), 0., 0.]} for i, (name, kind) in enumerate(roster)]
    shafts = [{"axis_id": "axis-" + str(i), "body": owner["id"], "ends": [{}, {}],
               "metal_roles": [{"id": "role-" + str(i) + "-" + str(j), "mass_kg": owner["mass_kg"] / 5.,
                                 "center_of_mass_xyz_mm": owner["center_xyz_mm"], "basis": "synthetic"} for j in range(5)]}
              for i, owner in enumerate(owners[50:])]
    aux = [{"id": "aux-" + str(i), "owner": owners[0]["id"], "mass_kg": 2.207001080119 / 274.,
            "center_xyz_mm": [0., 0., 0.]} for i in range(274)]
    features = [{"identity": "hold_tnut_main_" + name, "panel": panels[0], "start_xyz_mm": [0., 0., 0.],
                 "direction_xyz": [0., 0., 1.]} for name in ("A12", "K12", "A1")]
    features += [{"identity": "inert-aperture-" + str(i)} for i in range(337)]
    screws = [{"source_screw_descriptor": {"axis_id": "screw-" + str(i)}} for i in range(66)]
    holes = [{"angle_id": "angle-" + str(i), "holes": [{"installed_bolt_axis_id": "bolt" if j < 4 else None} for j in range(8)]}
             for i in range(22)]
    contacts = [{"id": kind + "-" + str(i), "kind": kind, "first": owners[0]["id"], "second": owners[1]["id"],
                 "stiffness": 1., "reference_area_mm2": 1.}
                for kind, count in (("timber_face_contact", 332), ("panel_contact", 922), ("flange_contact", 352)) for i in range(count)]
    common = [{"id": "common-" + str(i), "cells": [None] * (14 if i < 6 else 13)} for i in range(96)]
    flanges = [{"id": "flange-" + str(i), "cells": [None] * 4} for i in range(88)]
    observations = [{"id": name, "source": {"id": name, "path": "inert/" + name, "sha256": "a" * 64, "volume_mm3": 1.}}
                    for name in panels] + [{"id": "wood-observation-" + str(i)} for i in range(22)]
    raw = {"schema": r.INPUT_SCHEMA, "status": "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW", "optional_2026_extra": False,
        "historical_q": None, "old_field": None, "readiness": {"source_joins_independently_reviewed": False, "complete_reference_contact_inventory": False},
        "source_pins_before_after_unchanged": True, "release": dict(r.RELEASE), "parameters": {}, "scenario": {},
        "physical_owner_gravity_rows": owners, "base_bodies": owners[:50], "shafts": shafts,
        "finished_body_observations": observations, "finished_receiver_wall_queries": [{}] * 120, "fitting_port_bindings": [{}] * 88,
        "hillman_rows": screws, "panel_ids": sorted(panels), "all_factory_holes": holes,
        "current_panel_machining_descriptors": {"features": features}, "direct_contacts": contacts,
        "timber_and_panel_shared_face_patches": common, "flange_shared_face_patches": flanges, "shared_pair_query_census": [{}] * 72,
        "floor_footprints": {"floor-" + str(i): [[0., 0., 0.]] * 4 for i in range(8)}}
    raw["factory_holes"] = [{**hole, "angle_id": angle["angle_id"], "used": hole["installed_bolt_axis_id"] is not None}
                            for angle in holes for hole in angle["holes"]]
    for key, _source in r.JOINS:
        raw.setdefault(key, [])
    exported = {source: copy.deepcopy(raw[key]) for key, source in r.JOINS}
    exported.update(parameters={}, material_scenario={}, auxiliary_metal_gravity_descriptors=aux,
                    floor_observations=[{"host": key, "observed_normal_reference_points_xyz_mm": value} for key, value in raw["floor_footprints"].items()],
                    support={"enabled_centroid_xy_hosts": ["lumber_leg_left", "lumber_leg_right"], "no_slip_assumed_not_verified": True})
    permanent = [{"id": "self-weight/" + row["id"], "body": row["id"], "point_xyz_mm": row["center_xyz_mm"],
                  "force_xyz_n": [0., 0., -row["mass_kg"] * 9.80665]} for row in owners[:50]]
    permanent += [{"id": "physical-bolt-metal/" + role["id"], "body": shaft["body"], "point_xyz_mm": role["center_of_mass_xyz_mm"],
                   "force_xyz_n": [0., 0., -role["mass_kg"] * 9.80665]} for shaft in shafts for role in shaft["metal_roles"]]
    permanent += [{"id": "bolt-weight/" + row["id"], "body": row["owner"], "point_xyz_mm": row["center_xyz_mm"],
                   "force_xyz_n": [0., 0., -row["mass_kg"] * 9.80665]} for row in aux]
    permanent += [{"id": "accessory/" + name, "body": name, "point_xyz_mm": [1019.2, 0., 18.25625],
                   "force_xyz_n": [0., 0., -12.5 * 9.80665]} for name in panels[:2]]
    raw["cases"] = []
    for case_id, label, horizontal in (("a12-rear", "A12", [0., 300.]), ("a12-forward", "A12", [0., -300.]),
        ("a12-left", "A12", [-300., 0.]), ("k12-right", "K12", [300., 0.]), ("k12-rear", "K12", [0., 300.]),
        ("a1-rear", "A1", [0., 300.]), ("gravity-only", None, None)):
        loads, hold = copy.deepcopy(permanent), None
        if label:
            force = [*horizontal, -500. * .45359237 * 9.80665]
            loads.append({"id": "climber/" + label, "body": panels[0], "point_xyz_mm": [0., 0., -100.], "force_xyz_n": force})
            hold = {"label": label, "panel": panels[0], "front_xyz_mm": [0., 0., 0.], "load_point_xyz_mm": [0., 0., -100.],
                    "panel_midplane_xyz_mm": [0., 0., 9.128125], "force_xyz_n": force,
                    "moment_about_panel_midplane_xyz_nmm": cross([0., 0., -109.128125], force)}
        raw["cases"].append({"case_id": case_id, "primary_load_basis": True, "accessory_placement": "retained-original-top-hold",
            "loads": loads, "hold": hold, "applied_force_xyz_n": [math.fsum(row["force_xyz_n"][j] for row in loads) for j in range(3)],
            "applied_moment_about_global_origin_xyz_nmm": [math.fsum(cross(row["point_xyz_mm"], row["force_xyz_n"])[j] for row in loads) for j in range(3)]})
    raw["case"] = raw["cases"][0]
    raw["gravity"] = {"known_modeled_mass_kg": 191.908938620187 + 2.207001080119,
                      "additional_accessory_kg": 25., "primary_accessory_point_xyz_mm": [1019.2, 0., 18.25625]}
    return raw, exported


def test_extracted_load_arithmetic_and_complete_census_on_synthetic_witness():
    raw, exported = synthetic()
    result = r.check_rows(raw, exported, exported, r.independent_load_method())
    assert len(result["cases"]) == 7 and [case["load_count"] for case in result["cases"]] == [827] * 6 + [826]
    assert len(result["roles"]) == 500 and len(result["aux"]) == 274
    assert abs(result["total_mass"] - 219.115939700306) < 1e-10


@pytest.mark.parametrize("mutation", [
    lambda raw: raw["cases"][0]["loads"][0]["force_xyz_n"].__setitem__(2, 0.),
    lambda raw: raw["cases"][0]["loads"][0].update(body="foreign"),
    lambda raw: raw["cases"][0]["loads"][0]["point_xyz_mm"].__setitem__(0, 1.),
    lambda raw: raw["cases"][0]["loads"].pop(),
    lambda raw: raw["cases"][0]["applied_moment_about_global_origin_xyz_nmm"].__setitem__(0, 1.),
    lambda raw: raw["gravity"].update(additional_accessory_kg=0.),
])
def test_independent_load_mutations_reject(mutation):
    raw, exported = synthetic()
    mutation(raw)
    with pytest.raises(AssertionError):
        r.independent_load_method()(raw, exported, {row["id"]: row for row in raw["physical_owner_gravity_rows"]}, raw["base_bodies"])


@pytest.mark.parametrize("key, error", [("shafts", "unique 100"), ("physical_owner_gravity_rows", "unique own owners"),
    ("direct_contacts", "unique 1606"), ("floor_footprints", "32 own normal")])
def test_independent_census_mutations_reject(key, error):
    raw, exported = synthetic()
    if key == "floor_footprints":
        raw[key].pop(next(iter(raw[key])))
        exported["floor_observations"].pop(0)
    else:
        raw[key][0] = copy.deepcopy(raw[key][1])
        source_key = dict(r.JOINS)[key]
        exported[source_key] = copy.deepcopy(raw[key])
    with pytest.raises(ValueError, match=error):
        r.check_rows(raw, exported, exported, r.independent_load_method())


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_exclusive_output_refused_before_dependent_imports(tmp_path, kind):
    out = tmp_path / "preserved.json"
    out.write_text("preserved") if kind == "file" else out.symlink_to(tmp_path / "absent")
    with patch.object(r, "load_gate", side_effect=AssertionError("existing output reached imports")), pytest.raises(FileExistsError):
        r.main(["--mode", "review", "--run", "--out", str(out)])
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()


def test_default_preflight_is_not_saved_input_readiness(tmp_path):
    out = tmp_path / "preflight.json"
    with patch.object(r, "load_gate", side_effect=AssertionError("preflight reached imports")), \
            patch.object(r, "read", side_effect=AssertionError("preflight read saved data")):
        assert r.main(["--out", str(out)]) == 0
    result = json.loads(out.read_bytes())
    assert result["reviewed_input"] is None and result["review_readiness"] is False
    assert result["complete_reference_contact_inventory"] is False and result["actual_saved_input_review_performed"] is False
    assert not any(result["release"].values())


def test_review_without_run_preserves_failed_attempt_before_dependency_load(tmp_path):
    out = tmp_path / "failed.json"
    with patch.object(r, "load_gate", side_effect=AssertionError("unapproved review reached imports")), \
            pytest.raises(ValueError, match="explicit --run"):
        r.main(["--mode", "review", "--out", str(out)])
    failed = json.loads(out.read_bytes())
    assert failed["status"] == "FAILED" and failed["complete_reference_contact_inventory"] is False
    assert failed["reviewed_input"] is None and not any(failed["release"].values())


def test_exact_descriptor_review_contract():
    ref = {"path": "synthetic-descriptor", "sha256": "a" * 64}
    review = {"schema": "eoere_z180_geometry_descriptors_independent_review/v1", "success": "independent_z180_descriptor_source_checks_pass",
              "descriptor": ref, "release": dict(r.DESCRIPTOR_RELEASE), "source_sha256": {ref["path"]: ref["sha256"]}}
    assert r.check_descriptor_receipt(review, ref) == review["source_sha256"]
    review["release"] = dict(r.RELEASE)
    with pytest.raises(ValueError, match="geometry release contract"):
        r.check_descriptor_receipt(review, ref)
    review["release"] = dict(r.DESCRIPTOR_RELEASE)
    review["descriptor"] = {**ref, "sha256": "b" * 64}
    with pytest.raises(ValueError, match="exact descriptor review"):
        r.check_descriptor_receipt(review, ref)


@pytest.mark.parametrize("field, value", [("exit_code", 1), ("output_sha256", "b" * 64), ("wrapper_sha256", "b" * 64),
    ("elapsed_seconds", float("nan")), ("source_drift", ["changed"]), ("source_pins_verified_before_after", 0)])
def test_process_semantic_failures_precede_command_and_log_use(field, value):
    process = {"exit_code": 0, "output_sha256": "a" * 64, "wrapper_sha256": r.GATE_SHA, "elapsed_seconds": 1.,
               "source_pins_verified_before_after": 1, "source_drift": []}
    process[field] = value
    with pytest.raises(ValueError, match="successful exact source-only raw-input process"):
        r.check_process(process, {"path": "inert/inputs.json", "sha256": "a" * 64}, {}, None, None)


def test_process_binds_own_build_command_and_sibling_log_hashes(tmp_path):
    input_ref = {"path": str((tmp_path / "inputs.json").relative_to(r.ROOT)), "sha256": "a" * 64}
    process_ref = {"path": str((tmp_path / "process.json").relative_to(r.ROOT)), "sha256": "b" * 64}
    manifest, bank = {"path": "inert/manifest", "sha256": "c" * 64}, {"path": "inert/bank", "sha256": "d" * 64}
    parsed = SimpleNamespace(mode="build-inputs", run=False, slot=None, case_id=None, out=tmp_path / "inputs.json",
        source_export=r.DESCRIPTOR, source_export_sha256=r.DESCRIPTOR_SHA,
        source_manifest=r.ROOT / manifest["path"], source_manifest_sha256=manifest["sha256"],
        panel_bank=r.ROOT / bank["path"], panel_bank_sha256=bank["sha256"])
    bridge = SimpleNamespace(parse_args=lambda _argv: parsed)
    adapter = SimpleNamespace(SOURCE_MANIFEST=manifest, manifest=lambda: {"unchanged_panel_method": bank})
    process = {"exit_code": 0, "output_sha256": "a" * 64, "wrapper_sha256": r.GATE_SHA, "elapsed_seconds": 1.,
        "source_pins_verified_before_after": 1, "source_drift": [], "command": ["python", str(r.GATE), "--mode", "build-inputs"],
        "stdout_sha256": "e" * 64, "stderr_sha256": "f" * 64}
    assert r.check_process(process, input_ref, process_ref, adapter, bridge) == {
        str((tmp_path / "stdout.log").relative_to(r.ROOT)): "e" * 64,
        str((tmp_path / "stderr.log").relative_to(r.ROOT)): "f" * 64}
    parsed.mode = "run"
    with pytest.raises(ValueError, match="command source/output references differ"):
        r.check_process(process, input_ref, process_ref, adapter, bridge)


def test_authentic_original_panel_geometry_proof_on_synthetic_metadata():
    raw, parent = synthetic()
    adapter = r.load_gate().original()  # Definitions only; every source reader below is inert.
    geometry = {"path": "inert/original-panel-geometry", "sha256": "a" * 64}
    raw["geometry"] = {"report": adapter.GEOMETRY}
    raw["panel_operator_source_inputs"] = {"geometry": geometry, "optional_2026_extra": False,
        "finished_panel_solids": [row["source"] for row in raw["finished_body_observations"][:6]],
        "panel_machining_canonical_sha256": r.canonical(raw["current_panel_machining_descriptors"]),
        "screw_axes_canonical_sha256": r.canonical([row["source_screw_descriptor"] for row in raw["hillman_rows"]]),
        "screw_axis_ids": [row["source_screw_descriptor"]["axis_id"] for row in raw["hillman_rows"]],
        "old_contact_domains_reused": False, "old_response_or_acceptance_used": False}
    parent_input = {"panel_operator_source_inputs": copy.deepcopy(raw["panel_operator_source_inputs"])}
    with patch.object(adapter, "manifest", return_value={"parent_geometry": geometry}), patch.object(adapter, "read_ref", return_value=parent):
        proof = r.check_panels(raw, parent, parent_input, adapter)
        assert proof["panel_source_geometry"] == geometry and proof["proposal_geometry"] == adapter.GEOMETRY
        raw["panel_operator_source_inputs"]["geometry"] = adapter.GEOMETRY
        with pytest.raises(ValueError, match="authentic original panel contract/geometry"):
            r.check_panels(raw, parent, parent_input, adapter)


def test_raw_and_all_six_selected_review_authentication_is_explicit():
    raw = {"synthetic": True}
    ids = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
    observed = []
    def authenticate(record, data, pins, **kwargs):
        observed.append(kwargs.get("selection", "raw"))
        return pins, {"source_case_selection": kwargs["selection"]} if kwargs else {"inputs_canonical_sha256": r.canonical(raw)}
    bridge = SimpleNamespace(authenticate_review=authenticate,
        driver=SimpleNamespace(CASE_IDS=ids, select_case=lambda _raw, key: ({"selected": key}, {"case_id": key})))
    r.authenticate_receipt(bridge, {}, raw, {})
    assert observed == ["raw", *[{"case_id": key} for key in ids]]


def test_failed_authentication_clears_provisional_receipt(tmp_path):
    out = tmp_path / "failed-authentication.json"
    with pytest.raises(ValueError, match="authenticator sentinel"), r.reserve(out) as output:
        output.write({"schema": r.REVIEW_SCHEMA, "success": r.SUCCESS, "complete_reference_contact_inventory": True})
        raise ValueError("authenticator sentinel")
    failed = json.loads(out.read_bytes())
    assert failed["status"] == "FAILED" and failed["complete_reference_contact_inventory"] is False and "success" not in failed
