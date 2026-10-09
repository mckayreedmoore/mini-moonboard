"""Compact inert controls for the saved metadata audit; no candidate execution."""
import copy
import datetime
import importlib.util
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("z180_saved_output_metadata_review", Path(__file__).with_name("review.py"))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def vector_fixture(gradient=1e-5):
    response = {"q": [0., 2., 3.], "gradient_n": [gradient, 0., 0.], "gradient_inf_n": gradient,
                "generalized_residual_tolerance_n": 1e-5, "converged": True}
    for name, key in (("q", "q"), ("gradient", "gradient_n")):
        response[name + "_canonical_sha256"] = r.canonical(response[key])
    admission = {k: response[k] for k in ("q_canonical_sha256", "gradient_canonical_sha256")}
    admission["declared_law_checks"] = {"gradient_inf_n": gradient,
        "full_signed_gradient_canonical_sha256": response["gradient_canonical_sha256"]}
    return response, admission


def test_exact_gradient_limit_inclusive():
    assert r.vector_checks(*vector_fixture(), 3) == 1e-5


def test_gradient_above_original_limit_rejects():
    with pytest.raises(ValueError, match="full-gradient"):
        r.vector_checks(*vector_fixture(1.0000000001e-5), 3)


@pytest.mark.parametrize("mutation", ["q", "sign", "length", "nan"])
def test_vector_binding_mutations_reject(mutation):
    response, admission = vector_fixture()
    if mutation == "q":
        response["q"][1] += 1.
    elif mutation == "sign":
        response["gradient_n"][0] *= -1.
    elif mutation == "length":
        response["gradient_n"].pop()
    else:
        response["q"][0] = float("nan")
    with pytest.raises(ValueError):
        r.vector_checks(response, admission, 3)


def test_distinct_source_inventories_and_conflicts():
    method = {"source-"+str(i): "0"*64 for i in range(1171)}
    manifest = {**method, str(r.METHOD): r.METHOD_SHA}
    pointer = {"arrays": r.ref("own.npz", "1"*64), "manifest": r.ref("own.json", "2"*64)}
    field = {**manifest, "own.npz": "1"*64, "own.json": "2"*64}
    r.source_inventories(method, manifest, field, pointer)
    wrong = dict(field)
    wrong["source-0"] = "3"*64
    with pytest.raises(ValueError, match="field source closure"):
        r.source_inventories(method, manifest, wrong, pointer)
    with pytest.raises(ValueError, match="distinct"):
        r.source_inventories(method, field, field, pointer)
    with pytest.raises(ValueError, match="conflict"):
        r.merge(method, {"source-0": "4"*64})


def test_exact_admit_command_and_changed_path_reject():
    directory = r.CASES / "a12-forward/attempt01"
    command = [str(r.ROOT / ".venv/bin/python3"), "-B", str(r.GATE), "--mode", "admit",
               "--field", str(directory / "field.json"), "--out", str(directory / "admission.json")]
    r.command_checks(command, "a12-forward", directory, "admit")
    command[-1] = str(directory / "foreign.json")
    with pytest.raises(ValueError, match="exact source/method/slot"):
        r.command_checks(command, "a12-forward", directory, "admit")


def test_phase_serialization_and_overlap_reject():
    producer = {"started_at_utc": "2026-10-09T10:00:00+00:00", "finished_at_utc": "2026-10-09T10:01:00+00:00", "elapsed_seconds": 60.}
    audit = {"started_at_utc": "2026-10-09T10:01:00+00:00", "finished_at_utc": "2026-10-09T10:02:00+00:00", "elapsed_seconds": 60.}
    end = r.chronology(producer, audit, None)
    assert end == datetime.datetime.fromisoformat(audit["finished_at_utc"])
    with pytest.raises(ValueError, match="serialized"):
        r.chronology(producer, audit, end)
    audit["started_at_utc"] = "2026-10-09T10:00:59+00:00"
    with pytest.raises(ValueError, match="serialized"):
        r.chronology(producer, audit, None)


def floor_fixture():
    hosts = ["base-"+str(i) for i in range(6)] + sorted(r.LEGS)
    support = {"enabled_centroid_xy_hosts": sorted(r.LEGS), "no_slip_assumed_not_verified": True,
               "physical_floor_capacity_established": False, "no_vertical_tension_or_anchor": True}
    point = [0., 750., 1100.]
    raw = {"floor_footprints": {h: [point] * 4 for h in hosts}}
    rows = [{"first": h, "second": "floor", "id": h+"/normal-"+str(i), "kind": "floor_normal",
             "compression_n": 1., "force_on_first_xyz_n": [0., 0., 1.], "point_xyz_mm": point}
            for h in hosts for i in range(4)]
    rows += [{"first": h, "second": "floor", "id": h+"/xy-"+str(i), "kind": "floor_tangent",
              "interaction_enabled": h in r.LEGS, "force_on_first_xyz_n": [0., 0., 0.], "point_xyz_mm": point}
             for h in hosts for i in range(2)]
    normals = dict.fromkeys(hosts, 4.)
    field = {"analytical_support_scenario": support, "floor_actions": rows,
        "global_equilibrium_residual_force_n": [0., 0., 0.], "global_equilibrium_residual_moment_nmm": [0., 0., 0.],
        "response": {"fixed_floor_support_v1": {**support, "normal_force_n_by_host": normals, "both_credited_legs_in_bearing": True}}}
    admission = {"support_contract": support, "normal_force_n_by_host": normals,
                 "horizontal_force_xyz_n_by_host": {h: [0., 0., 0.] for h in hosts},
                 "declared_law_checks": {"global_residual_n_nmm": [0.] * 6},
                 "applied_load_checks": {"applied_wrench_about_reference_n_nmm": [0., 0., -32., 0., 0., 0.]}}
    return field, admission, raw, support


def test_floor_inventory_and_saved_closure():
    assert r.floor_checks(*floor_fixture()) == 4.


def test_global_origin_and_load_work_reference_are_distinct():
    args = floor_fixture()
    field, admission, _, _ = args
    epsilon = 1e-7
    field["floor_actions"][0]["compression_n"] += epsilon
    field["floor_actions"][0]["force_on_first_xyz_n"][2] += epsilon
    admission["normal_force_n_by_host"]["base-0"] += epsilon
    field["global_equilibrium_residual_force_n"] = [0., 0., epsilon]
    field["global_equilibrium_residual_moment_nmm"] = [750.*epsilon, 0., 0.]
    admission["declared_law_checks"]["global_residual_n_nmm"] = [0., 0., epsilon, 750.*epsilon, 0., 0.]
    assert r.floor_checks(*args) == 4.


@pytest.mark.parametrize("mutation", ["negative_normal", "uncredited_xy", "omitted_normal", "closure"])
def test_floor_mutations_reject(mutation):
    args = copy.deepcopy(floor_fixture())
    field, admission, _, _ = args
    if mutation == "negative_normal":
        field["floor_actions"][0]["compression_n"] = -1.
    elif mutation == "uncredited_xy":
        field["floor_actions"][32]["force_on_first_xyz_n"] = [1., 0., 0.]
    elif mutation == "omitted_normal":
        field["floor_actions"].pop(0)
    else:
        admission["applied_load_checks"]["applied_wrench_about_reference_n_nmm"][2] += 1.
    with pytest.raises(ValueError):
        r.floor_checks(*args)


def test_foreign_identity_and_authenticated_case_roster_exception():
    expected = {"state_id": "own", "case_id": "case", "accessory_placement": "own"}
    r.identities({"source_inputs": {"cases": [{"case_id": "other"}]}, "actions": [{"case_id": "case"}]}, expected)
    with pytest.raises(ValueError, match="foreign"):
        r.identities({"actions": [{"state_id": "other"}]}, expected)


def test_absolute_exception_scope_and_relative_aliases():
    for name, digest in r.ABSOLUTE.items():
        assert str(r.location(name, digest)) == name
        with pytest.raises(ValueError, match="unapproved"):
            r.location(name, "0"*64)
    with pytest.raises(ValueError, match="unapproved"):
        r.location(str(r.OWN), r.sha(r.OWN))
    with pytest.raises(ValueError, match="exact relative"):
        r.location("docs/../AGENTS.md")


@pytest.mark.parametrize("symlink", [False, True])
def test_exclusive_output_guard_precedes_audit(tmp_path, monkeypatch, symlink):
    output = tmp_path / "existing.json"
    if symlink:
        output.symlink_to(tmp_path / "missing.json")
    else:
        output.write_text("preserved")
    monkeypatch.setattr(sys, "argv", ["review.py", "--out", str(output)])
    monkeypatch.setattr(r.Audit, "verify", lambda _self: pytest.fail("audit called before output guard"))
    with pytest.raises(FileExistsError):
        r.main()
    assert output.is_symlink() if symlink else output.read_text() == "preserved"
