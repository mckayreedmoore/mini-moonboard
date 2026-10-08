"""Genuine saved floor rows and converged zero-state forwarding coupons."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix, vstack

SPEC = importlib.util.spec_from_file_location("observer_isolation_runner_coupon", Path(__file__).with_name("runner.py"))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


@pytest.fixture
def floor_rows():
    R.gate.linear.verify_pins(R.PROBE_PINS)
    path = R.ROOT / "fea/generated/thin-bolted-direct-contact-a12-v1/operator-inputs.json"
    manifest = json.loads(path.read_bytes())
    with np.load(path.with_name("operators.npz"), allow_pickle=False) as arrays:
        tangents = [{**row, "B": R.gate.read_csr(arrays, row["B"])} for row in manifest["tangents"]]
        # Read sparse normal rows only; the saved material K/applied are unused.
        C = R.gate.read_csr(arrays, manifest["C"])
    floor = [{**row, "B": C[i]} for i, row in enumerate(manifest["contacts"]) if row["kind"] == "floor_normal"]
    columns = sorted({int(c) for row in tangents + floor for c in row["B"].indices})
    lookup = {column: i for i, column in enumerate(columns)}
    for row in tangents + floor:
        B = row["B"]
        row["B"] = csr_matrix((B.data.copy(), np.asarray([lookup[int(c)] for c in B.indices]),
                                B.indptr.copy()), shape=(1, len(columns)))
    return tangents, floor, columns


def raw(row):
    B = row["B"]
    return R.base.csr_digest(B)


def linear_floor(tangents, hosts):
    n = tangents[0]["B"].shape[1]
    result = csr_matrix((n, n))
    for row in tangents:
        if row["first"] in hosts:
            result += row["stiffness"] * (row["B"].T @ row["B"])
    return result


def test_exact_mutation_is_eight_permuted_rows_with_identical_coefficients(floor_rows):
    rows, _, _ = floor_rows
    before = [raw(row) for row in rows]
    coefficients = [row["B"].toarray() for row in rows]
    assert all(len(row["B"].indices) == len(set(row["B"].indices)) for row in rows)
    original = R.KNOWN_ENABLED_FLOOR_HOSTS
    zero = csr_matrix((rows[0]["B"].shape[1],) * 2)
    signature_before = R.base.immutable_operator_signature(zero, np.zeros(zero.shape[0]), [], [], rows)
    hosts = sorted({row["first"] for row in rows})
    assert original(linear_floor(rows, hosts), zero, rows) == hosts
    assert sum(old != raw(row) for old, row in zip(before, rows, strict=True)) == 8
    for row, prior in zip(rows, coefficients, strict=True):
        np.testing.assert_array_equal(row["B"].toarray(), prior)
    assert R.base.immutable_operator_signature(zero, np.zeros(zero.shape[0]), [], [], rows) != signature_before


@pytest.mark.parametrize("count", [0, 4, 8])
def test_copy_isolation_preserves_raw_ports_masks_and_no_shared_buffers(floor_rows, count, monkeypatch):
    rows, _, _ = floor_rows
    old = [raw(row) for row in rows]
    original = R.KNOWN_ENABLED_FLOOR_HOSTS

    def observe(linear, material, copied):
        assert copied is not rows
        for live, clone in zip(rows, copied, strict=True):
            for key in ("data", "indices", "indptr"):
                assert not np.shares_memory(getattr(live["B"], key), getattr(clone["B"], key))
            assert {k: v for k, v in live.items() if k != "B"} == {k: v for k, v in clone.items() if k != "B"}
        return original(linear, material, copied)

    monkeypatch.setattr(R, "KNOWN_ENABLED_FLOOR_HOSTS", observe)
    hosts = sorted({r["first"] for r in rows})[:count]
    zero = csr_matrix((rows[0]["B"].shape[1],) * 2)
    assert R.enabled_floor_hosts_readonly(linear_floor(rows, hosts), zero, rows) == hosts
    assert [raw(row) for row in rows] == old


def test_live_coefficient_change_is_still_detected(floor_rows):
    rows, _, _ = floor_rows
    n = rows[0]["B"].shape[1]
    before = R.base.immutable_operator_signature(csr_matrix((n, n)), np.zeros(n), [], [], rows)
    rows[0]["B"].data[0] += .25
    after = R.base.immutable_operator_signature(csr_matrix((n, n)), np.zeros(n), [], [], rows)
    assert before != after


def test_converged_response_genuine_recovery_and_final_capture_chain(floor_rows, tmp_path, monkeypatch):
    tangents, contacts, _ = floor_rows
    n = tangents[0]["B"].shape[1]
    zero = csr_matrix((n, n))
    applied, q = np.zeros(n), np.zeros(n)
    # A prescribed all-zero point-law coupon, with10 receiving bodies and no
    # material K, stiffness assembly, global solve or132-body admission claim.
    groups = [{"id": "fixture-screw", "axis_id": "fixture-screw", "kind": "panel_screw",
        "first": "fixture-panel", "second": "fixture-neighbor", "point_xyz_mm": [0., 0., 0.],
        "basis": np.eye(3), "B": csr_matrix((3, n)), "ka": 1000., "kl": 1000.,
        "clearance": 0., "tension_only": True}]
    hosts = sorted({row["first"] for row in tangents})
    assembly = SimpleNamespace(members={}, geo={"members": [],
        "bodies": [{"id": host} for host in [*hosts, "fixture-panel", "fixture-neighbor"]]})
    case = {"case_id": "fixture-zero", "accessory_placement": "fixture-only", "loads": [],
            "applied_force_xyz_n": [0., 0., 0.], "applied_moment_about_global_origin_xyz_nmm": [0., 0., 0.]}
    signature = R.base.immutable_operator_signature(zero, applied, groups, contacts, tangents)
    callback_count = []
    original = R.KNOWN_ENABLED_FLOOR_HOSTS

    def tracked(linear, material, copied):
        callback_count.append(True)
        return original(linear, material, copied)

    monkeypatch.setattr(R, "KNOWN_ENABLED_FLOOR_HOSTS", tracked)
    monkeypatch.setattr(R.base, "relative", lambda path: str(Path(path).resolve()))
    actual_command = [sys.executable, str(Path(R.__file__).resolve()), "fixture-only-no-execution"]
    observed = {}

    def prescribed_response(K, rhs, actual_groups, actual_contacts, actual_tangents, *, max_iterations, warm_q):
        assert warm_q is None and max_iterations == 300
        C = vstack([row["B"] for row in actual_contacts], format="csr")
        ck = np.asarray([row["stiffness"] for row in actual_contacts])
        fields = R.base.incremental.ORIGINAL_FIELDS(K, rhs, actual_groups, C, ck, q, tangent=True)
        np.testing.assert_array_equal(fields[0], np.zeros(n))
        return {"converged": True, "q": q.copy(), "gradient_inf_n": 0.,
            "potential_energy_nmm": 0., "connector_local_force_n": fields[3],
            "normal_contact_force_n": fields[4], "nonbearing_no_slip_removed": hosts}

    def original_main():
        observed["response"] = R.base.lean.reused.previous.numerical.compatible_contact_solve(
            zero, applied, groups, contacts, tangents, max_iterations=300)

    # No evaluation or candidate preparation: invoke the frozen nested observer
    # seam through its actual cold orchestration and the prescribed zero law.
    monkeypatch.setattr(R.base.incremental, "compatible_contact_solve", prescribed_response)
    monkeypatch.setattr(R.base.lean.reused.previous, "main", original_main)
    monkeypatch.setattr(sys, "argv", ["fixture", "--cases", "a12-rear", "--out", str(tmp_path / "unused")])

    def coupon_metadata(report, prepared, **kwargs):
        assert report["equilibrium_verification"]["all_bodies"] == 10
        assert report["counts"]["structural_bodies"] == 10
        report["complete_timber_a12_execution"] = {"command": kwargs["command"],
            "loaded_driver_sha256": R.FROZEN_DRIVER_SHA256,
            "loaded_admission_sha256": R.FROZEN_GATE_SHA256}
        return report

    monkeypatch.setattr(R, "KNOWN_METADATA", coupon_metadata)
    original_observer = R.base.lean.reused.enabled_floor_hosts
    with R.forwarding_scope(actual_command):
        manifest, arrays, record = R.base.capture_operators(zero, applied, groups, contacts, tangents,
            directory=tmp_path, pins={}, command=["internal-call"], receipt={"path": "fixture", "sha256": "fixture"})
        assert manifest["command"] == actual_command
        R.base.lean.reused.main()
        response = observed["response"]
        assert response["converged"]
        assert len(callback_count) == 1
        recovered = R.base.frame.elastic_actions(assembly, case, response, groups, contacts, tangents)
        assert recovered["equilibrium_verification"]["all_bodies"] == 10
        assert recovered["equilibrium_verification"]["all_body_and_global_checks_pass"]
        report = {**recovered, "parameters": {}, "limits": [], "counts": {"dofs": n, "structural_bodies": 10},
            "response": {"q": q.tolist(), "converged": True, "gradient_inf_n": 0.,
                         "nonbearing_no_slip_removed": hosts}, "source_sha256": {},
            "case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
            "state_id": "fixture-prior", "geometry_cache_sha256": "fixture-only",
            "fixture_is_not_a_current_or132_body_admission": True}
        report = R.base.add_complete_metadata(report, {}, command=["internal-call"], pins={},
            method_record={}, operator_record=record, operator_manifest=manifest, wall_seconds=600.)
        context = {"inputs": (zero, applied, groups, contacts, tangents), "last_linear": zero,
            "directory": tmp_path, "pins": {}, "operator_manifest": manifest,
            "operator_arrays": arrays, "operator_record": record}
        R.base.final_gradient_capture(report, context)
        assert len(callback_count) == 2  # nested source observer AND final source observer
        assert R.base.immutable_operator_signature(zero, applied, groups, contacts, tangents) == signature
        assert report["parameters"]["complete_timber_a12_driver_sha256"] == R.LOADED_SHA256
        assert report["complete_timber_a12_execution"]["command"] == actual_command
        assert report["complete_timber_a12_execution"]["loaded_admission_sha256"] == R.gate.LOADED_PRODUCER_SHA256
        assert report["response"]["original_gradient_replay_v1"]["same_state_support_mask_consistent"]
        report = R.base.common.finished.bind_finished_state(report, [], {}, "fixture-only")
        identity = {k: report[k] for k in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
        assert report["state_id"] == "thin-v4-" + R.base.canonical_sha(identity)[:24]
        assert report["counts"]["structural_bodies"] == 10
    assert R.base.lean.reused.enabled_floor_hosts is original_observer


def test_exception_restores_all_forwarding_targets_and_genuine_source_paths():
    targets = [(R.base.lean.reused, "enabled_floor_hosts"), (R.base, "capture_operators"),
        (R.base, "add_complete_metadata"), (R.base, "write_json"), (R.base, "admission"),
        (R.base.common, "bind_common_metadata")]
    before = [getattr(module, key) for module, key in targets]
    with pytest.raises(RuntimeError, match="coupon"), R.forwarding_scope(["fixture"]):
        raise RuntimeError("coupon")
    assert all(getattr(module, key) is old for (module, key), old in zip(targets, before, strict=True))
    assert Path(R.base.__file__).resolve() == R.ROOT / R.FROZEN_DRIVER
    assert R.base.LOADED_SHA256 == R.FROZEN_DRIVER_SHA256
    assert R.base.OWN == R.FROZEN_DRIVER


def test_wrapper_receipt_freeze_read_and_original_source_guards(tmp_path, monkeypatch):
    # Pure receipt forwarding; parent remains the only real method freezer.
    monkeypatch.setattr(R, "method_sources", lambda: {R.FROZEN_DRIVER: R.FROZEN_DRIVER_SHA256})
    reviewed = {"focused_fixtures_pass": True, "independent_readiness_review_pass": True,
        "runner_sha256": R.LOADED_SHA256, "admission_sha256": R.gate.LOADED_PRODUCER_SHA256}
    receipt = R.freeze_method_inputs(tmp_path / "coupon-receipt.json", reviewed_checks=reviewed)
    assert receipt["driver"] == {"path": R.OWN, "sha256": R.LOADED_SHA256}
    assert receipt["observer_isolation"] == R.gate.observer_isolation_contract()
    assert not receipt["execution_authorization_supplied_by_receipt"]
    assert R.read_method_inputs(tmp_path / "coupon-receipt.json", R.frame.sha(tmp_path / "coupon-receipt.json")) == receipt
    assert R.base.LOADED_SHA256 == R.FROZEN_DRIVER_SHA256
    assert R.base.admission is R.ORIGINAL_BASE_GATE


def test_interruption_command_forwarding_is_truthful(tmp_path, monkeypatch):
    monkeypatch.setattr(R.base, "relative", lambda path: str(Path(path).resolve()))
    command = [sys.executable, str(Path(R.__file__).resolve()), "fixture"]
    with R.forwarding_scope(command):
        record = R.base.write_json(tmp_path / "coupon-interruption.json", {
            "schema": "thin_bolted_complete_timber_a12_interrupted/v1", "command": ["internal-call"]})
    report = json.loads(Path(record["path"]).read_bytes())
    assert report["command"] == command
    assert report["observer_isolation"] == R.gate.observer_isolation_contract()


def test_mismatched_frozen_options_are_rejected_before_case_launch(tmp_path, monkeypatch):
    options = SimpleNamespace(method_input=tmp_path / "fixture-receipt.json", method_input_sha256="fixture",
        out=tmp_path / "fixture-field.json", cases=["a12-rear"], wood_bedding=1.,
        intervals=8, contact_edge=70., newton_limit=300, wall_seconds=600.)
    actual = {key: getattr(options, key) for key in ("cases", "wood_bedding", "intervals", "contact_edge",
                                                    "newton_limit", "wall_seconds")}
    monkeypatch.setattr(R, "parse_options", lambda _: options)
    monkeypatch.setattr(R, "read_method_inputs", lambda *_: {"fixed_options": {**actual, "wood_bedding": 2.}})
    launched = []
    monkeypatch.setattr(R, "run_case", lambda *_: launched.append(True))
    with pytest.raises(ValueError, match="actual invocation differs from parent-frozen options"):
        R.main()
    assert not launched and not list(tmp_path.iterdir())
