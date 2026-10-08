"""Pure execution/recovery guard seams; no source candidate or toy solve."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("run_first_order.py")
SPEC = importlib.util.spec_from_file_location("eoere_first_order_runner_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)
TOY_SPEC = importlib.util.spec_from_file_location("eoere_first_order_runner_toy", PATH.with_name("test_first_order_factory.py"))
toy_module = importlib.util.module_from_spec(TOY_SPEC)
TOY_SPEC.loader.exec_module(toy_module)


def prepared():
    data, panels, integrated = toy_module.toy()
    return method.factory.prepare_synthetic(data, panels, integrated)


def test_recovery_keeps_all_disabled_floor_rows_and_loaded_root_gravity():
    p = prepared()
    q = np.zeros(p.assembly.ndof)
    diagnostic = {"converged": True, "q": q, "connector_local_force_n": [np.zeros(3) for _ in p.groups],
                  "normal_contact_force_n": np.zeros(len(p.contacts)), "nonbearing_no_slip_removed": ["wood-a"]}
    # Synthetic same-call recovery fixture only: body gravity is deliberately
    # unbalanced, so this result cannot pass execution/admission.
    recovered = method.recover(p, diagnostic)
    floors = recovered["floor_actions"]
    assert len(floors) == 6
    tangents = [row for row in floors if row["kind"] == "floor_tangent"]
    assert len(tangents) == 2
    assert all(row["interaction_enabled"] is False and row["energy_nmm"] == 0.
               and row["force_on_first_xyz_n"] == [0., 0., 0.] for row in tangents)
    fit = recovered["four_port_fitting_actions"][0]
    assert len(fit["strip_root_actions"]) == 4
    assert np.max(abs(np.asarray(fit["loaded_root_wrench_minus_source_body_wrench_n_nmm"]))) < 1e-8
    assert recovered["equilibrium_verification"]["all_body_and_global_checks_pass"] is False


def test_failed_response_and_synthetic_context_cannot_produce_production_actions_or_solve(monkeypatch):
    p = prepared()
    with pytest.raises(ValueError, match="failed branches"):
        method.recover(p, {"converged": False, "q": np.zeros(p.assembly.ndof)})
    monkeypatch.setattr(method.search, "compatible_contact_solve", lambda *a, **k: pytest.fail("synthetic production solve"))
    with pytest.raises(ValueError, match="synthetic assembly"):
        method.execute(p, pins={}, command=["not-a-case"])


def test_operator_fingerprint_detects_matrix_and_load_mutations():
    p = prepared()
    initial = method.operator_fingerprint(p)
    p.applied[0] += 1.
    assert method.operator_fingerprint(p) != initial
    p.applied[0] -= 1.
    assert method.operator_fingerprint(p) == initial
    p.assembly.K.data[0] += 1.
    assert method.operator_fingerprint(p) != initial


@pytest.mark.parametrize("fresh_gradient", ["vector", "scalar", "nan"])
def test_success_dispatch_uses_full_gradient_not_energy_and_rejects_nonvector_or_nonfinite(monkeypatch, fresh_gradient):
    p = prepared()
    # Five genuine toy owners, no padding or solve. The declared stub response
    # tests execution dispatch only; it is not a coupled-equilibrium coupon.
    p.synthetic_only = False
    p.source_review = {"synthetic_dispatch_only": True}
    q = np.zeros(p.assembly.ndof)
    response = {"converged": True, "q": q,
                "support_state_search_v1": {"accepted_enabled_centroid_xy_hosts": ["wood-a"]}}
    gradient = np.linspace(-2e-6, 3e-6, p.assembly.ndof)
    supplied = gradient if fresh_gradient == "vector" else (np.array(0.) if fresh_gradient == "scalar" else gradient.copy())
    if fresh_gradient == "nan":
        supplied[0] = np.nan
    monkeypatch.setattr(method.search, "compatible_contact_solve", lambda *a, **k: response)
    monkeypatch.setattr(method.search, "_fresh_fields", lambda *a: (supplied, 19.25, None, [], [], []))
    calls = []

    def recovery(*args):
        calls.append("stub closure only")
        return {"equilibrium_verification": {"all_body_and_global_checks_pass": True}}

    monkeypatch.setattr(method, "recover", recovery)
    if fresh_gradient != "vector":
        with pytest.raises(ValueError, match="finite full-coordinate vector"):
            method.execute(p, pins={}, command=["synthetic-dispatch-fixture"])
        assert not calls
    else:
        result = method.execute(p, pins={}, command=["synthetic-dispatch-fixture"])
        assert result["response"]["gradient_n"] == gradient.tolist()
        assert result["response"]["gradient_inf_n"] == 3e-6
        assert result["response"]["gradient_canonical_sha256"] == method.factory.canonical(gradient.tolist())
        assert result["disposition"] == "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION"
        assert len(calls) == 1 and not any(result["release"].values())


def test_exclusive_output_preserves_existing_bytes_and_no_implicit_run(tmp_path, monkeypatch):
    out = tmp_path/"field.json"
    method.write_exclusive(out, {"diagnostic_only": True})
    old = out.read_bytes()
    with pytest.raises(FileExistsError):
        method.write_exclusive(out, {"different": True})
    assert out.read_bytes() == old
    monkeypatch.setattr(method.sys, "argv", [str(PATH), "--input-review", "absent-review.json", "--input-review-sha256", "0"*64,
                                           "--inputs", "absent.json", "--inputs-sha256", "0"*64,
                                           "--out", str(out)])
    with pytest.raises(ValueError, match="explicit parent"):
        method.main()


@pytest.mark.parametrize("output_race", [False, True])
def test_wall_before_preparation_exports_honest_source_pinned_sidecar(tmp_path, monkeypatch, output_race):
    out = tmp_path/"fresh.json"
    monkeypatch.setattr(method.sys, "argv", [str(PATH), "--run", "--input-review", "absent-review.json", "--input-review-sha256", "0"*64,
                                           "--inputs", "absent.json", "--inputs-sha256", "0"*64,
                                           "--out", str(out), "--wall-seconds", "1"])

    def expired(*args):
        if output_race:
            out.write_text("preserved existing output\n")
        raise method.CaseWallTimeLimit("synthetic outside-response expiry")

    monkeypatch.setattr(method.factory, "read_inputs", expired)
    monkeypatch.setattr(method.signal, "setitimer", lambda *args: None)
    assert method.main() == 1
    payload = method.json.loads(out.with_suffix(".json.interrupted.json").read_bytes())
    assert payload["accepted_q"] is None and payload["accepted_actions"] is None
    assert payload["last_observation"] == {"phase": "before-source-read", "gradient_available": False}
    assert payload["source_sha256"][str(method.OWN.relative_to(method.frame.ROOT))] == method.LOADED_SHA
    assert bool(payload["preserved_output_sha256"]) == output_race
    if output_race:
        assert out.read_text() == "preserved existing output\n"


def test_guard_failure_before_preparation_never_exports_fake_gradient_or_forces(tmp_path, monkeypatch):
    out = tmp_path/"guarded.json"
    monkeypatch.setattr(method.sys, "argv", [str(PATH), "--run", "--input-review", "absent-review.json", "--input-review-sha256", "0"*64,
                                           "--inputs", "absent.json", "--inputs-sha256", "0"*64,
                                           "--out", str(out)])
    monkeypatch.setattr(method.factory, "read_inputs", lambda *args: (_ for _ in ()).throw(ValueError("missing source join")))
    monkeypatch.setattr(method.signal, "setitimer", lambda *args: None)
    assert method.main() == 1
    payload = method.json.loads(out.with_suffix(".json.failed.json").read_bytes())
    assert not out.exists() and payload["accepted_q"] is None and payload["accepted_actions"] is None
    assert payload["error"] == "missing source join" and payload["last_observation"]["gradient_available"] is False


def test_saved_panels_join_only_source_equivalent_geometry_and_all_loader_pins(tmp_path, monkeypatch):
    from scripts import run_thin_bolted_finite_frame as saved

    evidence, cache, loader = (tmp_path/name for name in ("evidence.json", "cache.json", "loader.py"))
    evidence.write_text('{"unchanged_source_measure":true}')
    loader.write_text("source-only-loader-fixture\n")
    parts = []
    for i in range(6):
        path = tmp_path/f"panel-{i}.brep"
        path.write_text(f"inert source bytes {i}\n")
        parts.append({"id": f"panel-{i}", "kind": "panel", "path": path.name, "sha256": method.frame.sha(path)})
    cache.write_text(method.json.dumps({"parts": parts}))
    monkeypatch.setattr(method.frame, "ROOT", tmp_path)
    monkeypatch.setattr(method.frame, "EVIDENCE", evidence)
    monkeypatch.setattr(method.frame, "EVIDENCE_SHA", method.frame.sha(evidence))
    monkeypatch.setattr(method.frame, "GEOMETRY_CACHE", cache)
    monkeypatch.setattr(method.frame, "GEOMETRY_CACHE_SHA", method.frame.sha(cache))
    monkeypatch.setattr(method, "SAVED_PANEL_PATH", loader.name)
    monkeypatch.setattr(method, "SAVED_PANEL_SHA", method.frame.sha(loader))
    monkeypatch.setattr(saved, "FIXED_HELPERS", {"pure-mass-helper.py": "a"*64})
    monkeypatch.setattr(method.factory, "source_pins", lambda extra: dict(extra))
    calls = []

    def reuse():
        calls.append("one pure source rehydration")
        return {row["id"]: {} for row in parts}, {"saved-operator.npz": "b"*64}, {"source_contact_count": 530}

    monkeypatch.setattr(saved, "reuse_panel_operators", reuse)
    pins = {row["path"]: row["sha256"] for row in parts}
    pins.update({evidence.name: method.frame.EVIDENCE_SHA, cache.name: method.frame.GEOMETRY_CACHE_SHA})
    data = {"source_sha256": pins, "panel_ids": [row["id"] for row in parts]}
    panels, integrated, joined, proof = method.load_panel_dependencies(data)
    assert len(calls) == 1 and set(panels) == set(data["panel_ids"])
    assert integrated == {"unchanged_source_measure": True}
    assert joined["pure-mass-helper.py"] == "a"*64 and joined[loader.name] == method.SAVED_PANEL_SHA
    assert proof["old_contact_rows_or_owners_used"] is False
    (tmp_path/parts[0]["path"]).write_text("different geometry\n")
    with pytest.raises(ValueError, match="byte-identical"):
        method.load_panel_dependencies(data)
