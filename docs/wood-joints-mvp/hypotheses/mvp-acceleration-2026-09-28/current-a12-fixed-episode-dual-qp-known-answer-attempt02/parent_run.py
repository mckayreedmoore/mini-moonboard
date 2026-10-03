"""Parent-only, one-shot prescribed A12 episode QP and independent audits."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import resource
import signal
import time

import numpy as np
import scipy
from scipy import sparse
import osqp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
PREP = BASE / "current-a12-fixed-episode-dual-qp-preparation-attempt01"
COMP = BASE / "current-frame-connector-compliance-attempt04"
SETTINGS = dict(verbose=False, eps_abs=1e-10, eps_rel=1e-10,
                eps_prim_inf=1e-10, eps_dual_inf=1e-10,
                max_iter=200000, time_limit=45.0, polishing=True,
                adaptive_rho=True, adaptive_rho_interval=50, rho=0.1, sigma=1e-6, scaling=10,
                check_termination=25, warm_starting=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def interval_check(value, center, radius):
    difference = np.abs(value - center)
    # Arithmetic guard only, with the same operation-level convention as the
    # source replay; no physical/model uncertainty is added to token radii.
    guard = 128 * np.finfo(float).eps * (np.abs(value) + np.abs(center) + 1)
    bound = radius + guard
    ratios = difference / bound
    return dict(pass_gate=bool(np.all(difference <= bound)),
                max_abs_difference=float(np.max(difference)),
                max_ratio=float(np.max(ratios)),
                failed_count=int(np.count_nonzero(difference > bound)),
                worst_full_position=int(np.argmax(ratios)))


def solve_and_audit(answer):
    z = answer
    S = z["S"]
    active = z["active_row_positions"]
    nonnegative = z["nonnegative_active_positions"]
    D_active = z["D_active"]
    assert S.shape == (1615, 1615) and D_active.shape == (1615, 300)
    assert len(nonnegative) == 1217
    assert np.all(np.isfinite(S)) and np.max(np.abs(S - S.T)) <= 1e-14
    np.linalg.cholesky(S)  # Independently check this QP Hessian before setup.
    sign_rows = sparse.csc_matrix((np.ones(len(nonnegative)),
                                  (np.arange(len(nonnegative)), nonnegative)),
                                 shape=(len(nonnegative), len(active)))
    A = sparse.vstack([sparse.csc_matrix(D_active.T), sign_rows], format="csc")
    model = osqp.OSQP()
    model.setup(P=sparse.triu(sparse.csc_matrix(S), format="csc"),
                q=z["linear_objective"], A=A,
                l=np.r_[z["W_total"], np.zeros(len(nonnegative))],
                u=np.r_[z["W_total"], np.full(len(nonnegative), np.inf)],
                **SETTINGS)
    result = model.solve(raise_error=False)
    info = result.info
    report = {"solver_status": info.status, "solver_status_value": int(info.status_val),
              "iterations": int(info.iter), "solver_seconds": float(info.run_time),
              "primal_residual": float(info.prim_res),
              "dual_residual": float(info.dual_res),
              "polish_status": int(info.status_polish)}
    if info.status != "solved" or info.status_val != 1:
        report["status"] = "STOP_SOLVER_STATUS_OR_BUDGET"
        return report
    assert np.all(np.isfinite(result.x)) and np.all(np.isfinite(result.y))
    f = np.zeros(1840)
    f[active] = result.x
    a = -result.y[:300]
    with np.load(COMP / "operators.npz", allow_pickle=False) as operators:
        H_raw = operators["H"]
        D = operators["D"]
    assert np.array_equal(D[active], D_active)
    H_sym = (H_raw + H_raw.T) * 0.5
    q_raw = D @ a + z["e_total_full"] - H_raw @ f
    q_sym = D @ a + z["e_total_full"] - H_sym @ f
    skew_shift = float(np.max(np.abs(q_sym - q_raw)))
    equilibrium = (D.T @ f - z["W_total"]).reshape(50, 6)
    force_residual = float(np.max(np.abs(equilibrium[:, :3])))
    moment_residual = float(1000 * np.max(np.abs(equilibrium[:, 3:])))
    families = z["active_row_family"]
    finite = families != "conditional_floor_tangent_constraint"
    unilateral = families == "unilateral_springa"
    q_active = q_raw[active]
    expected = z["k_active"][finite] * np.where(
        unilateral[finite], np.maximum(q_active[finite], 0), q_active[finite])
    law_residual = float(np.max(np.abs(f[active][finite] - expected)))
    normal_closed = z["closed_floor_normal_rows"]
    normal_open = z["open_floor_normal_rows"]
    tang_held = z["held_floor_tangent_rows"]
    tang_released = z["released_floor_tangent_rows"]
    floor = dict(min_closed_normal_q_mm=float(np.min(q_raw[normal_closed])),
                 min_closed_normal_force_N=float(np.min(f[normal_closed])),
                 max_open_normal_q_mm=float(np.max(q_raw[normal_open])),
                 max_abs_open_normal_force_N=float(np.max(np.abs(f[normal_open]))),
                 max_abs_held_tangent_q_mm=float(np.max(np.abs(q_raw[tang_held]))),
                 max_abs_released_tangent_force_N=float(np.max(np.abs(f[tang_released]))))
    # q_sym is independently recovered from the QP equality multiplier;
    # q_raw is the original source-operator prediction. Their difference is
    # audited, rather than manufacturing a zero raw-H compatibility residual.
    physical_gates = dict(
        raw_body_force=force_residual <= 0.1,
        raw_body_moment=moment_residual <= 2.0,
        raw_H_compatibility=skew_shift <= 2e-8,
        source_spring_laws=law_residual <= 0.1,
        unilateral_nonnegative=bool(np.min(f[active][unilateral]) >= -1e-8),
        source_unilateral_table_domain=bool(np.max(np.abs(q_active[unilateral])) <= 10.0
                                            and np.max(np.abs(q_raw[normal_open])) <= 10.0),
        closed_normals_strict=bool(np.min(q_raw[normal_closed]) > 2e-8
                                  and np.min(f[normal_closed]) > 1e-8),
        open_normals_strict=bool(np.max(q_raw[normal_open]) < -2e-8
                                and np.all(f[normal_open] == 0)),
        held_tangent_reference=bool(np.max(np.abs(q_raw[tang_held])) <= 2e-8),
        released_tangent_law=bool(np.all(f[tang_released] == 0)))
    source_checks = dict(
        forces=interval_check(f, z["f_native_full_N"], z["f_native_rounding_radius_full_N"]),
        projected_q=interval_check(q_raw, z["q_native_full_mm"], z["q_native_DAT_rounding_radius_full_mm"]),
        rigid_coordinates=interval_check(a, z["a_native_mm_and_scaled_rotation"],
                                        z["a_native_DAT_rounding_radius"]))
    all_source = all(row["pass_gate"] for row in source_checks.values())
    all_physical = all(physical_gates.values())
    report.update(status=("PASS_FIXED_EPISODE_KNOWN_ANSWER_ONLY" if all_source and all_physical
                          else "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE"),
                  physical_gates=physical_gates, original_DAT_comparisons=source_checks,
                  max_body_force_residual_N=force_residual,
                  max_body_moment_residual_Nmm=moment_residual,
                  max_source_law_residual_N=law_residual,
                  max_raw_vs_symmetric_H_shift_mm=skew_shift, floor=floor)
    np.savez_compressed(HERE / "diagnostic-candidate.npz", f_N=f, a=a,
                        q_raw_mm=q_raw, q_sym_mm=q_sym,
                        body_wrench_residual=equilibrium)
    report["diagnostic_candidate_sha256"] = sha(HERE / "diagnostic-candidate.npz")
    report["candidate_forces_adopted"] = False
    return report


def run():
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    versions = dict(numpy=np.__version__, scipy=scipy.__version__, osqp=osqp.__version__)
    assert versions == dict(numpy="2.2.6", scipy="1.15.3", osqp="1.0.4")
    assert not (HERE / "frozen-inputs.json").exists(), "one-shot run already frozen"
    numerical_fixture = json.loads((HERE / "numerical-settings-fixture.json").read_text())
    assert numerical_fixture["status"] == "PASS_TINY_SOURCE_ORACLES_WITH_ADAPTIVE_RHO"
    assert numerical_fixture["settings"] == SETTINGS
    assert numerical_fixture["parent_run_sha256"] == sha(HERE / "parent_run.py")
    assert numerical_fixture["settings_script_sha256"] == sha(HERE / "verify_settings.py")
    prep = json.loads((PREP / "assessment.json").read_text())
    assert prep["status"] == "PREPARED_A12_FIXED_EPISODE_KNOWN_ANSWER_NO_SOLVE"
    assert prep["known_answer_sha256"] == sha(PREP / "known-answer.npz")
    # Logical source-map names are retained with exact file paths in the freeze.
    import importlib.util
    spec = importlib.util.spec_from_file_location("a12_input_source_paths", PREP / "prepare.py")
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    paths = producer.replay_pin_paths()
    logical_paths = {f"response_replay_pin:{name}": path for name, path in paths.items()}
    logical_paths.update(response_replay_assessment=producer.REPLAY_ASSESSMENT,
                         response_replay_script=producer.REPLAY_SCRIPT,
                         selected_branch_screen=producer.SCREEN,
                         dual_qp_method=producer.DUAL_METHOD / "solve_fixture.py",
                         dual_qp_method_assessment=producer.DUAL_METHOD / "fixed-mask-dual-qp.json",
                         this_readme=PREP / "README.md", this_producer=PREP / "prepare.py")
    assert set(logical_paths) == set(prep["source_sha256"])
    assert all(sha(path) == prep["source_sha256"][name] for name, path in logical_paths.items())
    sources = {str(path.relative_to(ROOT)): sha(path) for path in logical_paths.values()}
    for path in [PREP / "assessment.json", PREP / "known-answer.npz", PREP / "output-pin.json",
                 HERE / "parent_run.py", HERE / "README.md",
                 HERE / "verify_settings.py", HERE / "numerical-settings-fixture.json",
                 BASE / "current-a12-fixed-episode-dual-qp-known-answer-attempt01/assessment.json"]:
        sources[str(path.relative_to(ROOT))] = sha(path)
    write(HERE / "frozen-inputs.json", dict(source_sha256=sources, versions=versions,
          settings=SETTINGS, CPU_cap_seconds=180, wall_cap_seconds=180,
          memory_cap_bytes=6 * 1024**3, native_launch=False,
          scope="single full-load A12 prescribed episode; no new state selection"))
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    signal.signal(signal.SIGALRM, lambda *args: (_ for _ in ()).throw(TimeoutError("180 s parent cap")))
    signal.alarm(180)
    start = time.monotonic()
    report = dict(status="RUNNING", native_launch=False, joint_accepted=False,
                  candidate_forces_adopted=False, frozen_inputs_sha256=sha(HERE / "frozen-inputs.json"))
    try:
        with np.load(PREP / "known-answer.npz", allow_pickle=False) as data:
            answer = {name: data[name] for name in data.files}
        report.update(solve_and_audit(answer))
    except Exception as error:
        report.update(status="STOP_PARENT_EXCEPTION_OR_BUDGET", exception=repr(error))
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - start
        report["source_freeze_unchanged"] = all(sha(ROOT / name) == pin for name, pin in sources.items())
        if not report["source_freeze_unchanged"]:
            report["status"] = "STOP_SOURCE_CHANGED_DURING_RUN"
        write(HERE / "assessment.json", report)
        write(HERE / "output-pin.json", dict(assessment_sha256=sha(HERE / "assessment.json")))
        print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert json.loads(lock.with_suffix(".json").read_text())["slot"]["state"] == "idle"
        run()
