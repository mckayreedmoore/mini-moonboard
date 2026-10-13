"""Portable numerical identities and adapter wiring; no candidate assembly."""

import copy
import math
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.linalg import block_diag
from scipy.spatial.transform import Rotation

from scripts import eoere_finite_fitting_precision as precision
from scripts.thin_bolted_corotational_methods import ROTATION_SCALE, rigid_port, skew
from scripts.thin_bolted_frame_mechanics import beam_stiffness


def test_loaded_producer_drift_rejects_before_current_intake(monkeypatch):
    original = precision.current.sha
    monkeypatch.setattr(precision.current, "sha", lambda p: "changed" if p == precision.OWN else original(p))
    monkeypatch.setattr(precision.intake_source, "intake", lambda: pytest.fail("intake reached after producer drift"))
    with pytest.raises(ValueError, match="loaded finite fitting producer changed"):
        precision.current_fitting_checks()


def test_standalone_execution_sources_include_eagerly_imported_intake_and_guard_loaded_bytes(monkeypatch):
    pins = precision.execution_pins()
    assert pins[precision.INTAKE["path"]] == precision.INTAKE["sha256"]
    assert pins[precision.PUBLICATION_MANIFEST["path"]] == precision.PUBLICATION_MANIFEST["sha256"]
    assert pins[precision.OUTPUT_BRIDGE["path"]] == precision.OUTPUT_BRIDGE["sha256"]
    monkeypatch.setattr(precision.intake_source, "LOADED_SHA", "foreign-loaded-source")
    with pytest.raises(ValueError, match="intake execution source"):
        precision.execution_pins()


@pytest.mark.parametrize("failure", [None, "manifest", "selection", "loaded_bridge"])
def test_publication_dependencies_bind_actual_manifest_selection_and_loaded_writer(monkeypatch, failure):
    bridge = precision.current.load("bridge")
    if failure == "manifest":
        monkeypatch.setattr(precision, "PUBLICATION_MANIFEST", {"path": "foreign", "sha256": "foreign"})
    elif failure == "selection":
        monkeypatch.setattr(precision.current, "manifest", lambda: {"references": {"bridge": {"path": "foreign", "sha256": "foreign"}}})
    elif failure == "loaded_bridge":
        monkeypatch.setattr(bridge, "LOADED_SHA", "foreign")
    if failure is None:
        assert precision.publication_sources() == [precision.PUBLICATION_MANIFEST, precision.OUTPUT_BRIDGE]
    else:
        with pytest.raises(ValueError, match="publication"):
            precision.publication_sources()


def stopped_root(fun, seed, *, options):
    """Simulate xtol convergence while the independently checked force is high."""
    return SimpleNamespace(x=np.array(seed), fun=fun(seed), nfev=1, success=True, message="relative iterate converged")


def test_residual_refinement_recovers_known_coupled_root_without_changing_force_gate():
    b = np.arange(36., dtype=float).reshape(6, 6)/100.
    matrix = b.T @ b+np.diag(np.arange(1., 7.))
    target = np.array([.3, -.1, .7, -2., 3., 1.])
    seed = target+np.array([1., -2., 3., -4., 5., -6.])*1e-6
    solved, trace = precision.residual_refined_root(stopped_root, lambda h: matrix @ (h-target), seed,
        options={"xtol": 1e-10, "maxfev": 100}, tolerance_n=1e-8, step_mm=1e-3)
    assert trace["initial_heel_residual_inf_n"] > 1e-6
    assert len(trace["corrections"]) == 1
    assert solved.x == pytest.approx(target, abs=1e-14)
    assert max(abs(solved.fun)) < 1e-12
    assert solved.nfev == trace["total_callback_count"] == 14
    assert trace["refinement_callback_count"] == 13
    assert trace["initial_scipy_reported_success"] is True
    assert not np.shares_memory(solved.x, seed)


def test_already_admissible_root_is_not_changed_or_refined():
    seed = np.arange(6.)
    solved, trace = precision.residual_refined_root(stopped_root, lambda h: h-seed, seed,
        options={"xtol": 1e-10, "maxfev": 100}, tolerance_n=1e-8, step_mm=1e-3)
    assert np.array_equal(solved.x, seed)
    assert trace["corrections"] == [] and solved.nfev == 1


@pytest.mark.parametrize("limit", [8, 13])
def test_insufficient_callback_budget_keeps_failed_residual_instead_of_accepting_it(limit):
    solved, trace = precision.residual_refined_root(stopped_root, lambda h: h-1., np.zeros(6),
        options={"xtol": 1e-10, "maxfev": limit}, tolerance_n=1e-8, step_mm=1e-3)
    assert max(abs(solved.fun)) == 1. and trace["corrections"] == []
    assert solved.nfev == 1 and trace["hard_callback_limit"] == limit


def test_callback_budget_is_hard_even_if_underlying_solver_ignores_maxfev():
    def runaway(fun, seed, *, options):
        for _ in range(101):
            fun(seed)
        pytest.fail("underlying root exceeded hard callback budget")
    with pytest.raises(ValueError, match="callback budget exhausted"):
        precision.residual_refined_root(runaway, lambda h: h-1., np.zeros(6),
            options={"xtol": 1e-10, "maxfev": 100}, tolerance_n=1e-8, step_mm=1e-3)


def test_refinement_rejects_worse_step_and_retains_original_pose():
    seed = np.full(6, -2.)
    solved, trace = precision.residual_refined_root(stopped_root, lambda h: np.exp(h)-1., seed,
        options={"xtol": 1e-10, "maxfev": 100}, tolerance_n=1e-8, step_mm=1e-3)
    assert np.array_equal(solved.x, seed) and max(abs(solved.fun)) > .8
    assert trace["corrections"] == [] and solved.nfev == 14


def test_three_correction_limit_does_not_turn_incomplete_root_into_pass():
    solved, trace = precision.residual_refined_root(stopped_root, lambda h: h*h-1., np.full(6, 10.),
        options={"xtol": 1e-10, "maxfev": 100}, tolerance_n=1e-8, step_mm=1e-3)
    assert len(trace["corrections"]) == 3 and solved.nfev == 40
    assert trace["final_heel_residual_inf_n"] > 1.
    assert max(abs(solved.fun)) > 1.


def test_refinement_samples_original_central_difference_step_without_rescaling():
    samples = []
    def residual(state):
        samples.append(state.copy())
        return state-1.
    solved, _ = precision.residual_refined_root(stopped_root, residual, np.zeros(6),
        options={"xtol": 1e-10, "maxfev": 100}, tolerance_n=1e-8, step_mm=1e-3)
    expected = [sign*1e-3*np.eye(6)[i] for i in range(6) for sign in [-1., 1.]]
    assert len(samples) == solved.nfev == 14
    assert sorted(tuple(q) for q in samples[1:13]) == sorted(tuple(q) for q in expected)


def finite_work_fixture():
    body, origin = "own-fitting", np.array([101., -203., 307.])
    reference = np.array([[11., 0., 0.], [-11., 0., 0.], [0., 0., 13.], [0., 0., -13.]])+origin
    theta, translation = np.array([.13, -.21, .17]), np.array([3., -2., 5.])
    rotation = Rotation.from_rotvec(theta).as_matrix()
    heel_point = origin+translation
    points = heel_point+(reference-origin) @ rotation.T
    port_rotations = np.array([theta, [-.27, .08, .19], [.07, .31, -.12], [.22, -.16, -.29]])
    q = np.zeros((4, 6)); q[:, :3], q[:, 3:] = points-reference, port_rotations*1000.
    load_reference, force = origin+[.1, .2, .3], np.array([0., 0., -2.])
    load_point = heel_point+rotation @ (load_reference-origin)
    load = {"id": "own-gravity", "body": body, "point_xyz_mm": load_reference.tolist(), "force_xyz_n": force.tolist()}
    forces = np.array([[3., 1., .2], [-1., -2., .4], [-2., 1., .6], [0., 0., .8]])
    assert np.array_equal(forces.sum(axis=0), -force)
    force_moment = sum((np.cross(point-heel_point, own_force) for point, own_force in zip(points, forces, strict=True)), np.zeros(3))
    assert np.linalg.norm(force_moment) > 10.
    couple = -(np.cross(load_point-heel_point, force)+force_moment)/4.
    manifest = [{"id": f"own-port-{i}", "point_reference_xyz_mm": p.tolist()} for i, p in enumerate(reference)]
    ports = [{"body": body, "port_id": m["id"], "point_xyz_mm": point.tolist(),
              "external_force_required_at_port_xyz_n": own_force.tolist(),
              "external_couple_required_at_port_xyz_nmm": couple.tolist()}
             for m, point, own_force in zip(manifest, points, forces, strict=True)]
    gradient = np.zeros((4, 6)); gradient[:, :3] = forces
    # Independent SciPy matrix differences give each port's spatial angular
    # velocity, rather than using the production left-Jacobian implementation.
    for i, own_theta in enumerate(port_rotations):
        own_rotation = Rotation.from_rotvec(own_theta).as_matrix()
        for j in range(3):
            delta = np.eye(3)[j]*1e-6
            derivative = (Rotation.from_rotvec(own_theta+delta).as_matrix()
                          -Rotation.from_rotvec(own_theta-delta).as_matrix())/(2e-6)
            spin = derivative @ own_rotation.T
            velocity = np.array([spin[2, 1]-spin[1, 2], spin[0, 2]-spin[2, 0], spin[1, 0]-spin[0, 1]])/2.
            gradient[i, j+3] = couple @ velocity/1000.
    adapter = SimpleNamespace(body=body, model=SimpleNamespace(origin=origin, port_manifest=manifest))
    result = {"internal_heel_q_mm_1000rad": np.r_[translation, theta*1000.].tolist(),
        "port_actions": ports, "gradient_n": gradient.ravel(),
        "current_load_actions": [{**copy.deepcopy(load), "point_xyz_mm": load_point.tolist()}],
        "external_body_resultant_about_current_heel_n_nmm": [0.]*6,
        "heel_residual_inf_n": 1e-10, "heel_hessian_min_symmetric_eigenvalue_n_mm": 39.,
        "hessian_n_per_mm": np.eye(24), "local_function_evaluations": 14,
        "local_solver_reported_success": True, "elastic_energy_nmm": 1.,
        "unsymmetrized_full_hessian_asymmetry_inf_n_mm": 1e-8, "strip_root_actions": [],
        "residual_refinement": {"corrections": []}}
    return adapter, q.ravel(), result, [load]


def test_spatial_work_and_gravity_transport_at_nonzero_finite_pose():
    adapter, q, result, loads = finite_work_fixture()
    checked = precision.fitting_work_check(adapter, q, result, loads)
    assert max(abs(v) for v in checked["external_spatial_work_error_n_nmm"]) < 1e-8
    assert max(abs(v) for v in checked["independent_body_wrench_residual_n_nmm"]) < 1e-12


@pytest.mark.parametrize("failure", ["rotational_units", "wrong_port_rotation", "missing_couple", "wrong_port", "duplicate_gravity", "wrong_gravity_pose", "wrong_gravity_force"])
def test_spatial_work_guards_reject_changed_duals_or_duplicate_and_moved_loads(failure):
    adapter, q, result, loads = finite_work_fixture()
    if failure == "rotational_units":
        result["gradient_n"].reshape(4, 6)[:, 3:] *= 1000.
    elif failure == "wrong_port_rotation":
        q.reshape(4, 6)[1:, 3:] = q.reshape(4, 6)[0, 3:]
    elif failure == "missing_couple":
        result["port_actions"][0]["external_couple_required_at_port_xyz_nmm"] = [0., 0., 0.]
    elif failure == "wrong_port":
        result["port_actions"][0]["point_xyz_mm"][0] += .1
    elif failure == "duplicate_gravity":
        result["current_load_actions"] *= 2
    elif failure == "wrong_gravity_pose":
        result["current_load_actions"][0]["point_xyz_mm"][0] += .1
    else:
        result["current_load_actions"][0]["force_xyz_n"][2] -= 1.
    with pytest.raises(ValueError):
        precision.fitting_work_check(adapter, q, result, loads)


@pytest.mark.parametrize("failure", [None, "solver_rejects", "heel_gate", "negative_heel", "nan_tangent"])
def test_current_probe_routes_own_noncontiguous_coordinates_seed_and_gravity(failure):
    adapter, q24, result, loads = finite_work_fixture()
    indices = np.arange(24)*3+11
    old_q = np.arange(100., dtype=float)
    old_q[indices] = q24
    descriptor = {"body": adapter.body, "dof_indices": indices.tolist(), "elastic_block_little_endian_float64_sha256": "own-matrix"}
    action = {"body": adapter.body, "loaded_heel_q_mm_rad": [3., -2., 5., .13, -.21, .17]}
    before = copy.deepcopy((old_q.tolist(), action, loads))
    def condensed(received_q, *, heel_seed, loads, tangent, recover_actions, heel_tolerance_n, max_local_evaluations):
        assert np.array_equal(received_q, q24)
        assert heel_seed == pytest.approx([3., -2., 5., 130., -210., 170.])
        assert len(loads) == 1 and loads[0]["id"] == "own-gravity"
        assert tangent and recover_actions and heel_tolerance_n == 1e-8 and max_local_evaluations == 100
        if failure == "solver_rejects":
            raise ValueError("finite internal heel failed local stationarity; no fallback")
        if failure == "heel_gate": result["heel_residual_inf_n"] = 2e-8
        if failure == "negative_heel": result["heel_hessian_min_symmetric_eigenvalue_n_mm"] = -1.
        if failure == "nan_tangent": result["hessian_n_per_mm"][0, 0] = np.nan
        return result
    adapter.condensed_response = condensed
    record = precision.probe_current_fitting(adapter, descriptor, old_q, action, loads)
    assert record["finite_local_fitting_probe_pass"] is (failure is None)
    assert record["candidate_equilibrium_admitted"] is False
    if failure is not None:
        assert record["accepted_local_actions"] is None and "error" in record
    else:
        assert record["diagnostic_port_q_mm_1000rad"] == q24.tolist()
        assert record["source_dof_indices"] == indices.tolist()
        assert len(record["port_actions"]) == 4
        assert record["port_actions"] == result["port_actions"]
    assert (old_q.tolist(), action, loads) == before


@pytest.mark.parametrize("fail", [False, True])
def test_refined_adapter_restores_original_root_callback_on_success_and_rejection(monkeypatch, tmp_path, fail):
    current = precision.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    for name in ["precision.py", "uv.lock", "method.py"]:
        (tmp_path/name).write_bytes(name.encode())
    monkeypatch.setattr(precision, "OWN", tmp_path/"precision.py")
    monkeypatch.setattr(precision, "LOADED_SHA", current.sha(precision.OWN))
    monkeypatch.setattr(precision, "execution_pins", dict)
    objective = SimpleNamespace(root=stopped_root)

    class Element:
        model = SimpleNamespace(origin=np.zeros(3))

    class Base:
        def __init__(self, element, *, step_mm):
            assert step_mm == 1e-3
            self.model, self.strips, self.step = element.model, [], step_mm
        def _relative_fingerprint(self):
            return ()
        def condensed_response(self, q, *, heel_seed, heel_tolerance_n=1e-8, max_local_evaluations=100):
            solved = objective.root(lambda h: h-1., heel_seed,
                                    options={"xtol": 1e-10, "maxfev": max_local_evaluations})
            if fail:
                raise ValueError("original final branch rejected")
            assert max(abs(solved.fun)) <= heel_tolerance_n
            return {"local_function_evaluations": solved.nfev}

    objective.ObjectiveFourPort = Base
    method = SimpleNamespace(GuardedFourPortAssemblyElement=Element, objective=objective,
        source_pins=lambda: {"method.py": current.sha(tmp_path/"method.py")})
    original_refinement = precision.residual_refined_root
    def checked_refinement(*args, step_mm, **kwargs):
        assert step_mm == 1e-3
        return original_refinement(*args, step_mm=step_mm, **kwargs)
    monkeypatch.setattr(precision, "residual_refined_root", checked_refinement)
    adapter = precision.stable_adapter(method, Element(), refine_heel=True)
    if fail:
        with pytest.raises(ValueError, match="original final branch rejected"):
            adapter.condensed_response(np.zeros(24), heel_seed=np.zeros(6))
    else:
        result = adapter.condensed_response(np.zeros(24), heel_seed=np.zeros(6))
        assert result["local_function_evaluations"] == 14
        assert len(result["residual_refinement"]["corrections"]) == 1
    assert objective.root is stopped_root


@pytest.mark.parametrize("failure", [None, "matrix", "port", "foreign_owner", "old_chart"])
def test_prepare_current_fitting_requires_exact_saved_matrix_ports_owner_and_full_chart(monkeypatch, failure):
    descriptor = {"body": "own", "ports": [{"id": "own-port"}], "all_factory_holes": list(range(8)),
        "own_fitting_scenario": {"scenario": "own-source"}, "dof_indices": list(range(11, 35)),
        "centroidal_correction": {"span": 65.0875},
        "elastic_block_little_endian_float64_sha256": precision.matrix_sha(np.eye(24))}
    pose = {"id": "own", "origin_xyz_mm": [101., -203., 307.],
        "u_xyz": [1., 0., 0.], "v_xyz": [0., 0., 1.], "w_xyz": [0., -1., 0.]}
    fresh = copy.deepcopy(descriptor)
    if failure == "matrix": descriptor["elastic_block_little_endian_float64_sha256"] = "changed"
    if failure == "port": fresh["ports"][0]["id"] = "wrong-port"
    if failure == "foreign_owner": pose["id"] = "foreign"
    calls = []

    class Element:
        def __init__(self, model, body, indices, ndof):
            assert model == "genuine-model" and body == "own" and ndof == 9450
            assert np.array_equal(indices, np.arange(11, 35))
        def descriptor(self): return fresh
        def elastic_block(self): return None, np.eye(24)

    def model_from_reference_pose(origin, u, v, w):
        assert [origin, u, v, w] == [pose["origin_xyz_mm"], pose["u_xyz"], pose["v_xyz"], pose["w_xyz"]]
        calls.append("model")
        return "genuine-model", None

    method = SimpleNamespace(model_from_reference_pose=model_from_reference_pose, GuardedFourPortAssemblyElement=Element)
    monkeypatch.setattr(precision, "stable_adapter", lambda m, e, *, refine_heel: (m, e, refine_heel))
    if failure is None:
        result = precision.prepare_current_fitting(method, pose, descriptor, full_ndof=9450)
        assert result[0] is method and type(result[1]) is Element and result[2] is True
        assert calls == ["model"]
    else:
        with pytest.raises(ValueError):
            precision.prepare_current_fitting(method, pose, descriptor, full_ndof=9372 if failure == "old_chart" else 9450)


@pytest.mark.parametrize("failed_probe", [None, (4, 9)])
@pytest.mark.parametrize("source_drift", [None, "before", "after"])
def test_current_six_case_orchestration_preserves_all132_own_fields_and_gravity_routes(monkeypatch, tmp_path, failed_probe, source_drift):
    current = precision.current
    names = ["producer.py", "response.py", "intake.py", "preflight.json", "method.py", "execution.py", "field.bin", "operators.bin", "uv.lock"]
    for name in names:
        (tmp_path/name).write_text(name)
    hashes = {name: current.sha(tmp_path/name) for name in names}
    monkeypatch.setattr(current, "ROOT", tmp_path)
    monkeypatch.setattr(current, "OWN", tmp_path/"response.py")
    monkeypatch.setattr(current, "LOADED_SHA", hashes["response.py"])
    monkeypatch.setattr(precision, "own_ref", lambda: {"path": "producer.py", "sha256": hashes["producer.py"]})
    monkeypatch.setattr(precision, "INTAKE", {"path": "intake.py", "sha256": hashes["intake.py"]})
    monkeypatch.setattr(precision.intake_source, "OWN", tmp_path/"intake.py")
    monkeypatch.setattr(precision.intake_source, "LOADED_SHA", hashes["intake.py"])
    monkeypatch.setattr(precision, "PREFLIGHT", {"path": "preflight.json", "sha256": hashes["preflight.json"]})
    monkeypatch.setattr(precision, "execution_pins", lambda: {name: hashes[name] for name in ["execution.py", "response.py"]})
    cases, bundles, parent_cases, calls = [], {}, [], []
    bodies = [f"own-fitting-{i:02d}" for i in reversed(range(22))]
    for i, case_id in enumerate(precision.component.SEQUENCE):
        ref = {"path": f"synthetic-manifest-{i}", "sha256": f"synthetic-sha-{i}"}
        loads = [{"id": f"gravity-{i}-{body}", "body": body} for body in bodies]
        bundles[ref["path"]] = {"coordinate_map": {"four_port_fittings": {body: {"body": body} for body in bodies}},
                                 "case": {"loads": loads}}
        q = [i+.13, i+.37]
        field = {"operator_bundle": {"manifest": ref}, "response": {"q": q},
            "source_inputs": {"fitting_poses": [{"id": body} for body in bodies]},
            "four_port_fitting_actions": [{"body": body, "own_case": i} for body in bodies]}
        binding = {"case_id": case_id, "state_id": f"state-{i}", "field": {"path": f"field-{i}", "sha256": f"field-sha-{i}"}}
        cases.append((binding, field, {}))
        parent_cases.append({**binding, "operator_manifest": ref, "coordinate_ownership": {"prospective_full_ndof": 9450}})
    parent = {"schema": "eoere_current_finite_ownership_and_shaft_gauge/v1", "source_sha256": {"operators.bin": hashes["operators.bin"]},
        "case_sequence": precision.component.SEQUENCE, "geometry_revision": "eoere-raised-kicker-screws-v1",
        "hardware_revision": "eoere-selected-purchase-hardware-v1", "extra_grid": False,
        "all_sources_unchanged": True, "cases": parent_cases}
    monkeypatch.setattr(precision.intake_source, "intake", lambda: (cases, {"field.bin": hashes["field.bin"]}))
    monkeypatch.setattr(precision.component, "load", lambda *_: SimpleNamespace(source_pins=lambda: {"method.py": hashes["method.py"]}))
    monkeypatch.setattr(precision.current, "read", lambda ref: parent if ref == precision.PREFLIGHT else bundles[ref["path"]])
    original_verify, checks = current.verify, []
    def verify(pins):
        checks.append(dict(pins))
        return original_verify(pins)
    monkeypatch.setattr(current, "verify", verify)
    monkeypatch.setattr(precision.current, "manifest", lambda: {"release": {"candidate_accepted": False},
        "references": {"bridge": precision.OUTPUT_BRIDGE}})

    def prepare(method, pose, descriptor, *, full_ndof):
        assert pose["id"] == descriptor["body"] and full_ndof == 9450
        return SimpleNamespace(body=pose["id"])

    def probe(adapter, descriptor, old_q, linear_action, loads):
        i = len(calls)//22
        body = bodies[len(calls) % 22]
        assert adapter.body == descriptor["body"] == linear_action["body"] == body
        assert old_q is cases[i][1]["response"]["q"] and linear_action["own_case"] == i
        assert len(loads) == 1 and loads[0]["body"] == body and loads[0]["id"] == f"gravity-{i}-{body}"
        passed = (i, len(calls) % 22) != failed_probe
        calls.append((i, body))
        if source_drift == "after" and len(calls) == 132:
            (tmp_path/"field.bin").write_text("changed during final probe")
        return {"body": body, "finite_local_fitting_probe_pass": passed,
                **({} if passed else {"accepted_local_actions": None, "error": "own local rejection retained"})}

    monkeypatch.setattr(precision, "prepare_current_fitting", prepare)
    monkeypatch.setattr(precision, "probe_current_fitting", probe)
    if source_drift is not None:
        if source_drift == "before": (tmp_path/"operators.bin").write_text("changed before calculation")
        with pytest.raises(ValueError, match="source drift"):
            precision.current_fitting_checks()
        assert len(calls) == (0 if source_drift == "before" else 132)
        assert checks == [hashes]*(1 if source_drift == "before" else 2)
        return
    result = precision.current_fitting_checks()
    assert checks == [hashes, hashes] and result["source_sha256"] == hashes
    assert len(calls) == len(set(calls)) == 132
    assert len(result["cases"]) == 6
    for i, (published, (binding, field, _)) in enumerate(zip(result["cases"], cases, strict=True)):
        assert {k: published[k] for k in ["case_id", "state_id", "field"]} == binding
        assert published["operator_manifest"] == field["operator_bundle"]["manifest"]
        assert len(published["fittings"]) == 22
        for j, row in enumerate(published["fittings"]):
            passed = (i, j) != failed_probe
            assert row == {"body": bodies[j], "finite_local_fitting_probe_pass": passed,
                           **({} if passed else {"accepted_local_actions": None, "error": "own local rejection retained"})}
    assert result["all132_local_fitting_probes_pass"] is (failed_probe is None)
    if failed_probe is not None:
        i, j = failed_probe
        assert result["cases"][i]["fittings"][j] == {
            "body": bodies[j], "finite_local_fitting_probe_pass": False,
            "accepted_local_actions": None, "error": "own local rejection retained"}
    assert result["full_frame_potential_equilibrium_native_solve_or_remedy_performed"] is False


@pytest.mark.parametrize("angle", [0., 1e-14, 1e-9, -.31, 1.2])
def test_rodrigues_increment_keeps_tiny_transverse_and_second_order_terms(angle):
    arm = np.array([11., -7., 3.])
    result = precision.rotation_increment([0., 0., angle], arm)
    cosine_minus_one = -2*math.sin(angle/2)**2
    expected = [cosine_minus_one*11+math.sin(angle)*7,
                math.sin(angle)*11-cosine_minus_one*7, 0.]
    np.testing.assert_allclose(result, expected, rtol=3e-15, atol=1e-28)
    theta = np.array([.3, -.7, .2])*angle
    if abs(angle) > 1e-6:
        np.testing.assert_allclose(precision.rotation_increment(theta, arm),
                                   Rotation.from_rotvec(theta).apply(arm)-arm, rtol=2e-14, atol=1e-14)


def strip(*, oblique=False):
    basis = Rotation.from_rotvec([.21, -.34, .12]).as_matrix() if oblique else np.eye(3)
    origin, length = np.array([101., -203., 307.]), 70.
    local = beam_stiffness(length, 30., 10., 15., 8., 200000., 77000.)
    transform = block_diag(*([basis]*4))
    matrix = transform @ local @ transform.T
    positions = np.array([origin, origin+basis[:, 0]*length])
    return precision.StableRelative(positions, matrix), basis


def test_tiny_axial_deformation_has_exact_known_energy_and_force():
    model, _ = strip()
    q = np.zeros(12)
    q[6] = 1e-12  # Far below the precision of adding this to a 70-mm chord.
    response = model.response(q)
    stiffness = 200000.*30./70.
    assert response["energy_nmm"] == pytest.approx(.5*stiffness*1e-24, rel=1e-14, abs=0.)
    np.testing.assert_allclose(response["gradient_n"][[0, 6]], [-stiffness*1e-12, stiffness*1e-12], rtol=1e-14, atol=0.)
    deformation, _ = model.deformation(q)
    assert deformation[6] == 1e-12


def test_finite_pose_matches_original_and_keeps_analytic_work_and_tangent():
    model, _ = strip(oblique=True)
    q = np.array([.12, -.21, .07, 90., -40., 30., -.09, .13, .22, 93., -38., 29.])
    original = precision.finite.ObjectiveCondensedFitting(model.reference_positions, model.condensed_stiffness)
    stable_deformation, stable_j = model.deformation(q)
    old_deformation, old_j = original.deformation(q)
    np.testing.assert_allclose(stable_deformation, old_deformation, rtol=2e-12, atol=2e-14)
    np.testing.assert_array_equal(stable_j, old_j)
    response = model.response(q)
    direction = np.array([.2, -.1, .3, -.7, .4, .2, -.3, .1, -.2, .5, -.6, .8])
    h = 1e-4
    plus, minus = model.response(q+h*direction, tangent=False), model.response(q-h*direction, tangent=False)
    assert (plus["energy_nmm"]-minus["energy_nmm"])/(2*h) == pytest.approx(response["gradient_n"] @ direction, rel=2e-7)
    np.testing.assert_allclose((plus["gradient_n"]-minus["gradient_n"])/(2*h),
                               response["hessian_n_per_mm"] @ direction, rtol=3e-7, atol=2e-6)


def test_common_rigid_pose_is_unstrained_and_relative_branch_guard_remains():
    model, _ = strip(oblique=True)
    theta, translation = np.array([.27, -.31, .18]), np.array([3., -7., 11.])
    rotation = Rotation.from_rotvec(theta)
    q = np.zeros((2, 6))
    for i, point in enumerate(model.reference_positions):
        q[i, :3] = rotation.apply(point)-point+translation
        q[i, 3:] = theta*ROTATION_SCALE
    result = model.response(q.ravel(), tangent=False)
    assert result["energy_nmm"] < 1e-20
    assert np.max(abs(result["gradient_n"])) < 1e-8
    bad = np.zeros(12)
    bad[11] = math.pi/2*ROTATION_SCALE
    with pytest.raises(ValueError, match="90-degree fitting relative rotation"):
        model.deformation(bad)


def test_adapter_uses_each_own_external_port_and_preserves_parent_maps_and_guards(monkeypatch, tmp_path):
    current = precision.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    (tmp_path/"precision.py").write_bytes(b"precision producer")
    (tmp_path/"uv.lock").write_bytes(b"lock")
    dependency = tmp_path/"method.py"
    dependency.write_bytes(b"frozen method")
    helper = tmp_path/"execution.py"
    helper.write_bytes(b"execution helper")
    monkeypatch.setattr(precision, "OWN", tmp_path/"precision.py")
    monkeypatch.setattr(precision, "LOADED_SHA", current.sha(precision.OWN))
    pins = {"method.py": current.sha(dependency)}
    helper_pins = {"execution.py": current.sha(helper)}
    monkeypatch.setattr(precision, "execution_pins", lambda: helper_pins)
    rows = [{"port_index": i, "root": np.array([110.+i, -200., 310.]),
             "center": np.array([170.+i, -190., 320.]), "point": np.array([170.+i, -193., 320.])}
            for i in range(4)]
    originals = []
    for i, row in enumerate(rows):
        chord = row["center"]-row["root"]
        x = chord/np.linalg.norm(chord)
        y = np.cross([0., 0., 1.], x)
        y /= np.linalg.norm(y)
        basis = np.column_stack([x, y, np.cross(x, y)])
        transform = block_diag(*([basis]*4))
        matrix = transform @ beam_stiffness(np.linalg.norm(chord), 30.+i, 10.+i, 15.+i, 8.+i,
                                             200000., 77000.) @ transform.T
        originals.append(precision.finite.ObjectiveCondensedFitting(
            np.array([row["root"], row["center"]]), matrix, .001*(i+1)))
    checks = []

    class Element:
        model = SimpleNamespace(origin=np.array([101., -203., 307.]))

    class Base:
        def __init__(self, element, *, step_mm):
            self.model = element.model
            self.strips = list(zip(rows, originals, strict=True))
        def _relative_fingerprint(self):
            return tuple(id(r) for _, r in self.strips)
        def _check(self):
            checks.append(True)
            current.require(self._relative_snapshot == self._relative_fingerprint(), "changed relative operator")
        def _beam_state(self, full, row):
            i = row["port_index"]
            indices = np.arange(6+6*i, 12+6*i)
            root, jr = rigid_port(row["root"], self.model.origin, full[:6])
            tip, jt = rigid_port(row["center"], row["point"], full[indices])
            q = np.r_[root-row["root"], full[3:6], tip-row["center"], full[indices[3:]]]
            j = np.zeros((12, 30))
            j[:3, :6], j[3:6, 3:6] = jr, np.eye(3)
            j[6:9, indices], j[9:12, indices[3:]] = jt, np.eye(3)
            return q, j, root, tip

    method = SimpleNamespace(GuardedFourPortAssemblyElement=Element,
                             objective=SimpleNamespace(ObjectiveFourPort=Base), source_pins=lambda: pins)
    adapter = precision.stable_adapter(method, Element())
    assert all(type(r) is precision.StableRelative for _, r in adapter.strips)
    for (_, copied), original in zip(adapter.strips, originals, strict=True):
        np.testing.assert_array_equal(copied.reference_positions, original.reference_positions)
        np.testing.assert_array_equal(copied.condensed_stiffness, original.condensed_stiffness)
        assert copied.tangent_step_mm == original.tangent_step_mm
    full = np.arange(30.)*.013
    full[3:6] = [17., -23., 11.]
    before = full.copy()
    for row in rows:
        q, jacobian, root, tip = adapter._beam_state(full, row)
        i = row["port_index"]
        state = full[6+6*i:12+6*i]
        heel_rotation = Rotation.from_rotvec(full[3:6]/ROTATION_SCALE)
        port_rotation = Rotation.from_rotvec(state[3:]/ROTATION_SCALE)
        expected_root = full[:3]+heel_rotation.apply(row["root"]-adapter.model.origin)-(row["root"]-adapter.model.origin)
        expected_tip = state[:3]+port_rotation.apply(row["center"]-row["point"])-(row["center"]-row["point"])
        np.testing.assert_allclose(q[:3], expected_root, rtol=2e-13, atol=3e-15)
        np.testing.assert_allclose(q[6:9], expected_tip, rtol=2e-13, atol=3e-15)
        old_q, old_j, old_root, old_tip = Base._beam_state(adapter, full, row)
        np.testing.assert_array_equal(q[[3, 4, 5, 9, 10, 11]], old_q[[3, 4, 5, 9, 10, 11]])
        np.testing.assert_array_equal(jacobian, old_j)
        np.testing.assert_array_equal(root, old_root)
        np.testing.assert_array_equal(tip, old_tip)
    np.testing.assert_array_equal(full, before)

    # Independent linear rigid-arm assembly in physical rotation coordinates.
    reference = np.zeros((30, 30))
    for row, original in zip(rows, originals, strict=True):
        i = row["port_index"]
        mapping = np.zeros((12, 30))
        mapping[:3, :3] = np.eye(3)
        mapping[:3, 3:6] = -skew(row["root"]-adapter.model.origin)/ROTATION_SCALE
        mapping[3:6, 3:6] = np.eye(3)/ROTATION_SCALE
        mapping[6:9, 6+6*i:9+6*i] = np.eye(3)
        mapping[6:9, 9+6*i:12+6*i] = -skew(row["center"]-row["point"])/ROTATION_SCALE
        mapping[9:12, 9+6*i:12+6*i] = np.eye(3)/ROTATION_SCALE
        reference += mapping.T @ original.condensed_stiffness @ mapping

    def gradient(state):
        value = np.zeros(30)
        for row, relative in adapter.strips:
            q, mapping, _, _ = adapter._beam_state(state, row)
            value += mapping.T @ relative.residual(q)
        return value

    step = 1e-4
    actual = np.column_stack([(gradient(h)-gradient(-h))/(2*step) for h in np.eye(30)*step])
    def schur(matrix):
        return matrix[6:, 6:]-matrix[6:, :6] @ np.linalg.solve(matrix[:6, :6], matrix[:6, 6:])
    np.testing.assert_allclose(actual, reference, rtol=2e-9, atol=1e-6)
    np.testing.assert_allclose(schur(actual), schur(reference), rtol=2e-8, atol=1e-6)
    adapter._check()
    assert checks == [True]
    helper.write_bytes(b"helper drift")
    with pytest.raises(ValueError, match="source drift: execution.py"):
        adapter._check()
    helper.write_bytes(b"execution helper")
    dependency.write_bytes(b"drift")
    with pytest.raises(ValueError, match="source drift"):
        adapter._check()
    class Pretender(Element):
        pass
    with pytest.raises(ValueError, match="genuine centroidal"):
        precision.stable_adapter(method, Pretender())


@pytest.mark.parametrize("value", [[0., 0.], [0., np.nan, 0.]])
def test_increment_rejects_invalid_vectors(value):
    with pytest.raises(ValueError):
        precision.rotation_increment(value, [1., 2., 3.])


def test_execution_helpers_are_bound_to_loaded_source_and_canonical_dependency(monkeypatch, tmp_path):
    current = precision.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    current_file = tmp_path/"current.py"
    current_file.write_bytes(b"current helper")
    monkeypatch.setattr(current, "OWN", current_file)
    monkeypatch.setattr(current, "LOADED_SHA", current.sha(current_file))
    refs = []
    for name in ["component.py", "canonical.py", "intake.py", "manifest.json", "bridge.py"]:
        file = tmp_path/name
        file.write_bytes(name.encode())
        refs.append({"path": name, "sha256": current.sha(file)})
    monkeypatch.setattr(precision.component, "own_ref", lambda: refs[0])
    monkeypatch.setattr(precision.component, "canonical_dependency", lambda: refs[1])
    monkeypatch.setattr(precision, "INTAKE", refs[2])
    monkeypatch.setattr(precision.intake_source, "OWN", tmp_path/"intake.py")
    monkeypatch.setattr(precision.intake_source, "LOADED_SHA", refs[2]["sha256"])
    monkeypatch.setattr(precision, "publication_sources", lambda: refs[3:])
    pins = precision.execution_pins()
    assert pins == {"current.py": current.LOADED_SHA, **{r["path"]: r["sha256"] for r in refs}}
    current.verify(pins)
    (tmp_path/"canonical.py").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source drift: canonical.py"):
        current.verify(pins)
    current_file.write_bytes(b"changed")
    with pytest.raises(ValueError, match="loaded response adapter changed"):
        precision.execution_pins()


@pytest.mark.parametrize("failure", [None, "heel_gate", "nonfinite_heel", "closure", "tangent", "pre_drift", "post_drift"])
def test_coupon_keeps_exact_synthetic_problem_solver_gates_and_source_checks(monkeypatch, tmp_path, failure):
    current = precision.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    refs = {}
    for name in ["precision.py", "method.py", "execution.py", "uv.lock"]:
        file = tmp_path/name
        file.write_bytes(name.encode())
        refs[name] = current.sha(file)
    monkeypatch.setattr(precision, "OWN", tmp_path/"precision.py")
    monkeypatch.setattr(precision, "LOADED_SHA", refs["precision.py"])
    monkeypatch.setattr(precision, "execution_pins", lambda: {"execution.py": refs["execution.py"]})
    rotation = Rotation.from_rotvec([.31, -.27, .19])
    origin = np.array([101., -203., 307.])
    reference = np.diag(np.arange(1., 25.))
    events = []

    def model_from_reference_pose(point, u, v, w):
        events.append("pose")
        np.testing.assert_array_equal(point, origin)
        np.testing.assert_allclose(u, rotation.apply([1., 0., 0.]), rtol=0., atol=1e-15)
        np.testing.assert_allclose(v, rotation.apply([0., 0., 1.]), rtol=0., atol=1e-15)
        np.testing.assert_allclose(w, rotation.apply([0., -1., 0.]), rtol=0., atol=1e-15)
        return SimpleNamespace(origin=point), None

    class Element:
        def __init__(self, model, body, indices, ndof):
            events.append("element")
            self.model, self.body_id = model, body
            assert body == "synthetic-precision-fitting"
            np.testing.assert_array_equal(indices, np.arange(3, 27))
            assert ndof == 31
        def elastic_block(self):
            events.append("reference")
            return None, reference

    method = SimpleNamespace(GuardedFourPortAssemblyElement=Element, model_from_reference_pose=model_from_reference_pose,
                             source_pins=lambda: {"method.py": refs["method.py"]})
    def load(ref, name):
        assert ref == precision.METHOD
        assert name == "eoere_precision_centroidal_source"
        return method
    monkeypatch.setattr(precision.component, "load", load)

    class Adapter:
        def condensed_response(self, q, *, heel_seed, loads, tangent, **kwargs):
            np.testing.assert_array_equal(q, np.zeros(24))
            np.testing.assert_array_equal(heel_seed, np.zeros(6))
            assert tangent is True
            if loads:
                events.append("loaded")
                assert kwargs == {"recover_actions": True, "heel_tolerance_n": 1e-8, "max_local_evaluations": 100}
                assert len(loads) == 1
                load = loads[0]
                assert load["id"] == "synthetic-gravity-once"
                assert load["body"] == "synthetic-precision-fitting"
                np.testing.assert_allclose(load["point_xyz_mm"], origin+rotation.apply([18., 3., 21.]), rtol=0., atol=1e-13)
                np.testing.assert_allclose(load["force_xyz_n"], rotation.apply([0., 0., -.5]), rtol=0., atol=1e-15)
                if failure == "post_drift": (tmp_path/"execution.py").write_bytes(b"changed")
                return {"heel_residual_inf_n": 2e-8 if failure == "heel_gate" else np.nan if failure == "nonfinite_heel" else 3e-10,
                        "external_body_resultant_about_current_heel_n_nmm": [2e-5 if failure == "closure" else 2e-12, 0., 0., 0., 0., 0.],
                        "local_function_evaluations": 12, "local_solver_reported_success": True,
                        "heel_hessian_min_symmetric_eigenvalue_n_mm": 39.}
            events.append("zero")
            assert loads == [] and kwargs == {}
            return {"hessian_n_per_mm": reference*(1.01 if failure == "tangent" else 1.)}

    def adapter(source_method, element):
        assert source_method is method and type(element) is Element
        events.append("adapter")
        return Adapter()
    monkeypatch.setattr(precision, "stable_adapter", adapter)
    verify = current.verify
    def checked(pins):
        events.append("verify")
        assert pins == refs
        verify(pins)
    monkeypatch.setattr(current, "verify", checked)
    if failure == "pre_drift": (tmp_path/"method.py").write_bytes(b"changed")
    if failure:
        match = {"heel_gate": "heel residual", "nonfinite_heel": "heel residual", "closure": "wrench closure",
                 "tangent": "reference tangent", "pre_drift": "source drift: method.py", "post_drift": "source drift: execution.py"}[failure]
        with pytest.raises(ValueError, match=match): precision.coupon()
        assert events.count("verify") == (2 if failure == "post_drift" else 1)
        if failure == "pre_drift": assert events == ["verify"]
        return
    result = precision.coupon()
    assert events == ["verify", "pose", "element", "adapter", "loaded", "zero", "reference", "verify"]
    assert result["heel_gate_n"] == 1e-8 and result["heel_residual_inf_n"] == 3e-10
    assert result["local_function_evaluations"] == 12 and result["local_solver_reported_success"] is True
    assert result["heel_hessian_min_symmetric_eigenvalue_n_mm"] == 39.
    assert result["external_body_wrench_closure_inf_n_nmm"] == 2e-12
    assert result["reference_schur_relative_error"] == 0.
    assert result["source_sha256"] == refs and result["all_sources_unchanged"] is True
    assert result["reference_origin_xyz_mm"] == origin.tolist()
    assert result["reference_basis_rotation_vector_rad"] == [.31, -.27, .19]
    assert result["candidate_field_assembly_or_native_solver_run"] is False
    assert result["physical_fitting_stiffness_resistance_or_candidate_acceptance"] is False
