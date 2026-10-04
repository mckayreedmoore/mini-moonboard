"""Qualify one backend and retry the single still-unaccepted profile state.

The existing circular/near-open oracle and fixed-floor kernel are reused.
Only direct_solve_method changes; all strict tolerances and acceptance gates
remain unchanged. Parent owns the one project call. join is source-only.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path

import clarabel
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "rawlocal/joint-frame-profile-followup"
FOLLOWUP_SHA256 = "393b6870a87fd0f16129c1048614bd2075b31514fbe5bdbad11de9581ad3d342"
RETRY = RAW / "retry01"
RETRY_RECEIPT_SHA256 = "49e7ddde970b3f6ebcb8f45c052a737ab71d6c72ae2feb359c727ca1704b6ee1"
TARGET = "a12-left_gap"
BACKEND = "qdldl"
COUPON_PASS = "PASS_QDLDL_STRICT_CIRCULAR_AND_NEAR_OPEN_KNOWN_ANSWERS"
PREPARED = "PREPARED_ONE_STRICT_QDLDL_PROFILE_SOURCE_MASK_RETRY"
PASS = "PASS_ONE_STRICT_QDLDL_PROFILE_SOURCE_MASK_RETRY"
COMPLETE = "COMPLETE_THREE_AUDITED_PROFILE_SOURCE_MASK_RETRIES"


def followup():
    path = HERE / "joint-frame-profile-followup.py"
    spec = importlib.util.spec_from_file_location("profile_backend_frozen_followup", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    result.require(result.sha(path) == FOLLOWUP_SHA256, "frozen followup producer differs")
    return result


def backend_settings(core):
    return {**core.REFINEMENT_SETTINGS, "direct_solve_method": BACKEND}


def new_output(output, fu):
    output = Path(output).resolve()
    fu.require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate followup output child required")
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def write_receipt(output, status, pins, m, fu, schema="joint_frame_profile_backend_retry_receipt/v1", **extra):
    pins[Path(__file__).resolve()] = fu.sha(__file__)
    m.authenticate(pins)
    fu.write(output / "receipt.json", {"schema": schema, "status": status,
        "source_sha256": {m.source_key(path): digest for path, digest in pins.items()},
        "output_sha256": {p.name: fu.sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        "physical_release": False, **extra})


def original_retry(fu, m, pins):
    fu.require(fu.sha(RETRY / "receipt.json") == RETRY_RECEIPT_SHA256, "actual strict retry source differs")
    bound = fu.bind_packet(RETRY, pins, m)
    fu.require(bound["status"] == "PARTIAL_PROFILE_SOURCE_MASK_RETRIES_NUMERICAL_QUALIFICATION_OPEN",
               "actual partial retry packet required")
    report = fu.read(RETRY / "comparison.json")
    tags = {state["case_id"] + ("_zero" if state["gap_scale"] == 0 else "_gap") for state in report["states"]}
    fu.require(tags == set(fu.TARGETS) - {TARGET}
               and all(state["audit"]["all_passed"] for state in report["states"]),
               "two original successful stricter fields required")
    stopped = fu.read(RETRY / (TARGET + "-stop.json"))
    fu.require(stopped["solver"]["status"] == "AlmostSolved" and stopped["audit"]["all_passed"]
               and not stopped["accepted_force_field_exists"], "specific unaccepted backend trial differs")
    return report


def source_bindings(coupon_packet=None):
    """Read-only parent request closure; no frame matrix or native factorization."""
    fu, pins = followup(), {}
    m = fu.mechanics()
    profile = m.module(HERE / "washer-working-profile-completion.py", "backend_retry_binding_paths")
    for path, digest in fu.source_bindings().items():
        profile.bind(pins, profile.artifact(fu.ROOT, path, absolute=True), digest)
    original_retry(fu, m, pins)
    if coupon_packet is not None:
        proof = fu.bind_packet(coupon_packet, pins, m)
        fu.require(proof["status"] == COUPON_PASS, "passed frozen qdldl coupon required")
    pins[Path(__file__).resolve()] = fu.sha(__file__)
    m.authenticate(pins)
    return {m.source_key(path): digest for path, digest in pins.items()}


def load_pins(sources, m, fu):
    profile = m.module(HERE / "washer-working-profile-completion.py", "backend_retry_request_paths")
    pins = {}
    for path, digest in sources.items():
        profile.bind(pins, profile.artifact(fu.ROOT, path, absolute=True), digest)
    m.authenticate(pins)
    return pins


def coupon(output):
    """Two existing tiny known answers, with no global/native source solve."""
    fu = followup()
    m = fu.mechanics()
    pins = load_pins(source_bindings(), m, fu)
    core = m.compatibility()
    fu.require(clarabel.__version__ == "0.11.1", "pinned Clarabel version differs")
    core.REFINEMENT_SETTINGS = backend_settings(core)
    report = core.refinement_known_answer()
    for key in ("circular_solver", "unilateral_solver"):
        fu.require(report[key]["status"] == "Solved" and report[key]["linear_solver"] == BACKEND
                   and report[key]["settings"] == core.REFINEMENT_SETTINGS,
                   "known-answer actual backend/status/settings differ")
    output = new_output(output, fu)
    fu.write(output / "known-answer.json", {"schema": "joint_frame_profile_backend_known_answer/v1",
        "status": COUPON_PASS, "clarabel_version": clarabel.__version__, "backend": BACKEND,
        "changed_setting_keys": ["direct_solve_method"], "maximum_project_calls": 0,
        "existing_method": "joint-frame-compatibility-completion.py:refinement_known_answer",
        "result": report, "physical_release": False})
    write_receipt(output, COUPON_PASS, pins, m, fu, new_coupled_project_calls=0, tiny_known_answer_calls=2)
    return output


def prepare(output, request, expected_sha256, coupon_packet):
    fu = followup()
    m = fu.mechanics()
    core = m.compatibility()
    request, coupon_packet = Path(request).resolve(), Path(coupon_packet).resolve()
    fu.require(fu.sha(request) == expected_sha256, "frozen backend request SHA differs")
    document = fu.read(request)
    fu.require(document.get("schema") == "joint_frame_profile_backend_retry_request/v1"
               and document.get("target_state_tags") == [TARGET]
               and document.get("maximum_coupled_calls") == 1
               and document.get("solver_settings") == backend_settings(core)
               and document.get("source_retry_receipt_sha256") == RETRY_RECEIPT_SHA256
               and document.get("coupon_directory") == m.source_key(coupon_packet)
               and document.get("coupon_receipt_sha256") == fu.sha(coupon_packet / "receipt.json"),
               "bounded strict backend request differs")
    fu.require(document.get("source_sha256") == source_bindings(coupon_packet), "backend request source closure differs")
    pins = load_pins(document["source_sha256"], m, fu)
    proof = fu.read(coupon_packet / "known-answer.json")
    fu.require(proof["status"] == COUPON_PASS and proof["clarabel_version"] == clarabel.__version__ == "0.11.1"
               and proof["result"]["solver_settings"] == backend_settings(core), "coupon/runtime/settings differ")
    output = new_output(output, fu)
    (output / "request.json").write_bytes(request.read_bytes())
    fu.write(output / "source-mask-audit.json", next(record for record in fu.mask_audit(m) if record["state_tag"] == TARGET))
    write_receipt(output, PREPARED, pins, m, fu, request_sha256=expected_sha256, new_coupled_project_calls=0)
    return output


def retry(output, preparation):
    """Parent-only: exactly one strict call at the same original accepted mask."""
    fu, pins = followup(), {}
    m = fu.mechanics()
    prepared = fu.bind_packet(preparation, pins, m)
    fu.require(prepared["status"] == PREPARED, "frozen backend preparation required")
    request = fu.read(Path(preparation) / "request.json")
    core, frame = m.compatibility(), fu.profile_frame(m)
    settings = backend_settings(core)
    fu.require(request["solver_settings"] == settings and clarabel.__version__ == "0.11.1", "strict backend settings/runtime differ")
    record = fu.read(Path(preparation) / "source-mask-audit.json")
    fu.require(record["state_tag"] == TARGET, "single target mask differs")
    case, gap = record["case_id"], record["gap_scale"]
    c, bearing = m.load_coefficients(case, frame["dead_load_factor"]), np.asarray(record["bearing"], dtype=bool)
    output = new_output(output, fu)
    fu.write(output / "inputs.json", {"preparation": m.source_key(preparation), "solver_settings": settings,
        "maximum_coupled_calls": 1, "target_state_tags": [TARGET], "washer_joint_update": frame["joint_update"],
        "source_retry_receipt_sha256": RETRY_RECEIPT_SHA256, "physical_release": False})
    print(TARGET + ": one strict qdldl source-mask call", flush=True)
    try:
        f, q, a, solver, audit = core.fixed_floor_branch(frame["H"], frame["D"], frame["e"] @ c,
            frame["W"] @ c, frame["joint"], bearing, gap, settings)
        if not audit["all_passed"] or solver["linear_solver"] != BACKEND or solver["settings"] != settings:
            raise core.UnacceptedTrial("STOP: strict qdldl physical/status/backend audit failed", f, q, a, solver, audit)
        pose = fu.recover_shaft_pose(frame, f, a)
    except ValueError as error:
        trial = getattr(error, "trial", None)
        if trial is not None:
            np.savez_compressed(output / (TARGET + "-unaccepted-trial.npz"), trial_force_n=trial["force"],
                trial_motion_mm=trial["motion"], trial_rigid_scaled_mm=trial["rigid"])
        fu.write(output / (TARGET + "-stop.json"), {"case_id": case, "gap_scale": gap, "exception": str(error),
            "solver": trial["solver"] if trial else None, "audit": trial["audit"] if trial else None,
            "accepted_force_field_exists": False, "physical_frame_failure_claim": False, "physical_release": False})
        write_receipt(output, "STOP_ONE_STRICT_QDLDL_PROFILE_SOURCE_MASK_RETRY", pins, m, fu,
            completed_states=0, new_coupled_project_calls=1)
        return output
    energy = m.assembled_potential(f, q, a, frame["H"], frame["e"], frame["W"], frame["L"], c,
        frame["joint"], gap, frame["energy_constant_scope"], frame["unchanged_constant_token"])
    np.savez_compressed(output / "response.npz", **{TARGET + suffix: value
        for suffix, value in zip(fu.SUFFIXES, (f, q, a, pose, bearing), strict=True)})
    state = {"case_id": case, "gap_scale": gap, "audit": audit, "energy": energy, "solver": solver,
        "source_mask": record["original_accepted_state"], "floor_branch_history": [{"step": 0,
            "bearing_footprints": np.flatnonzero(bearing).tolist(), "solver": solver,
            "original_physical_law_audit": audit}], "physical_acceptance": False}
    disposition = {"case_id": case, "gap_scale": gap, "status": "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM",
        "accepted_force_field_exists": True, "response_tag": TARGET, "physical_release": False}
    fu.write(output / "comparison.json", {"schema": "joint_frame_profile_source_mask_retry/v1", "status": PASS,
        "states": [state], "case_dispositions": [disposition], "new_coupled_calls": 1, "physical_release": False})
    write_receipt(output, PASS, pins, m, fu, completed_states=1, new_coupled_project_calls=1)
    print(TARGET + ": strict qdldl status and all original physical/panel gates passed", flush=True)
    return output


def join(output, backend_packet):
    """Retain the two actual prior successes and one actual qdldl success."""
    fu, pins = followup(), {}
    m = fu.mechanics()
    original = original_retry(fu, m, pins)
    backend = fu.bind_packet(backend_packet, pins, m)
    fu.require(backend["status"] == PASS, "accepted strict backend field required; numerical qualification remains open")
    states, dispositions, vectors = {}, {}, {}
    for packet, report in ((RETRY, original), (Path(backend_packet), fu.read(Path(backend_packet) / "comparison.json"))):
        with np.load(packet / "response.npz", allow_pickle=False) as saved:
            for index, state in enumerate(report["states"]):
                tag = state["case_id"] + ("_zero" if state["gap_scale"] == 0 else "_gap")
                fu.require(tag in fu.TARGETS and tag not in states and state["audit"]["all_passed"], "unexpected retained accepted field")
                states[tag] = copy.deepcopy(state)
                states[tag]["source_state_record"] = {"path": m.source_key(packet / "comparison.json"),
                    "sha256": fu.sha(packet / "comparison.json"), "pointer": "/states/" + str(index)}
                for suffix in fu.SUFFIXES:
                    vectors[tag + suffix] = saved[tag + suffix].copy()
            for disposition in report["case_dispositions"]:
                if disposition["accepted_force_field_exists"]:
                    dispositions[disposition["response_tag"]] = copy.deepcopy(disposition)
    fu.require(set(states) == set(dispositions) == set(fu.TARGETS), "complete three-state actual accepted inventory required")
    output = new_output(output, fu)
    np.savez_compressed(output / "response.npz", **vectors)
    fu.write(output / "comparison.json", {"schema": "joint_frame_profile_source_mask_retry/v1", "status": COMPLETE,
        "states": [states[tag] for tag in fu.TARGETS], "case_dispositions": [dispositions[tag] for tag in fu.TARGETS],
        "new_coupled_calls": 0, "source_coupled_calls": 4, "original_two_accepted_retry_fields_preserved": True,
        "original_unaccepted_faer_trial_preserved_as_source_only": True, "physical_release": False})
    write_receipt(output, COMPLETE, pins, m, fu, schema="joint_frame_profile_followup_receipt/v1",
        completed_states=3, new_coupled_project_calls=0)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("coupon", "prepare", "retry", "join"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--coupon-packet", type=Path)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--backend-packet", type=Path)
    args = parser.parse_args()
    fu = followup()
    if args.stage == "coupon":
        coupon(args.output)
    elif args.stage == "prepare":
        fu.require(args.request and args.expected_sha256 and args.coupon_packet, "frozen request/hash/coupon required")
        prepare(args.output, args.request, args.expected_sha256, args.coupon_packet)
    elif args.stage == "retry":
        fu.require(args.preparation, "frozen preparation required")
        retry(args.output, args.preparation)
    else:
        fu.require(args.backend_packet, "accepted strict backend packet required")
        join(args.output, args.backend_packet)


if __name__ == "__main__":
    main()
