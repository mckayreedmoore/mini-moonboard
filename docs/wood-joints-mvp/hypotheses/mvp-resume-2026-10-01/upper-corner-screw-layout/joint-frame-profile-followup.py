"""Bounded source-mask retries and source-only enrichment of the working profile.

prepare/aggregate never solve the global frame. retry performs exactly one
existing fixed-mask call per frozen target and is reserved for the parent.
The original profile sweep, v3 producer and all five traces stay unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/joint-frame-profile-followup"
SOURCE = HERE / "rawlocal/joint-frame-member-replacement/profile-frame01"
SOURCE_RECEIPT_SHA256 = "3688daecf06c6966c534d198a27830b11ccbfb021b83455cfa8e89c724948b0a"
SOURCE_COMPARISON_SHA256 = "b3a80d09f0dfb142a89b385a283cbbce89543d921b6c5656528aa9cdf7d2c774"
MECHANICS_SHA256 = "0f4c5b62c1b2fecda31ff83c4d7d641d03f51f164beda37f797a461ca90d909b"
TARGETS = ("a12-left_gap", "k12-rear_zero", "a1-rear_gap")
SUFFIXES = ("_force_n", "_relative_motion_mm", "_rigid_scaled_mm", "_shaft_pose_mm", "_bearing")


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def mechanics():
    path = HERE / "joint-frame-member-replacement.py"
    require(sha(path) == MECHANICS_SHA256, "frozen v3 mechanics source differs")
    spec = importlib.util.spec_from_file_location("profile_followup_v3", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def floor_failure_summary(exception):
    """The unchanged action exporter extracts this wrapper from the snapshot."""
    import importlib.util
    from pathlib import Path

    root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "current-candidate.json").is_file())
    path = root / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-compatibility-completion.py"
    spec = importlib.util.spec_from_file_location("profile_followup_saved_floor_summary", path)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    return method.floor_failure_summary(exception)


def bind_packet(directory, pins, m):
    """Reuse the existing absolute-source-aware binding without changing it."""
    directory = Path(directory).resolve()
    profile = m.module(HERE / "washer-working-profile-completion.py", "profile_followup_binding")
    profile.bind(pins, directory / "receipt.json", sha(directory / "receipt.json"))
    receipt = profile.packet(pins, directory, "receipt.json")
    profile.authenticate(pins)
    return receipt


def source_bindings():
    """Source-only closure for the parent request; no H/native matrix is read."""
    m, pins = mechanics(), {}
    require(sha(SOURCE / "receipt.json") == SOURCE_RECEIPT_SHA256
            and sha(SOURCE / "comparison.json") == SOURCE_COMPARISON_SHA256, "actual profile source differs")
    bind_packet(SOURCE, pins, m)
    core = m.compatibility()
    core.bind_packet(m.FRAME, pins, preserved_producer=True)
    adapter = m.module(core.DIAGNOSTICS, "profile_followup_reference_inputs")
    _, _, references, _ = adapter.frozen_inputs()
    for record in references.values():
        path = (ROOT / record["path"]).resolve()
        require(path not in pins or pins[path] == record["sha256"], "diagnostic reference pin conflict")
        pins[path] = record["sha256"]
    pins.update({Path(__file__).resolve(): sha(__file__), HERE / "joint-frame-member-replacement.py": MECHANICS_SHA256})
    m.authenticate(pins)
    return {m.source_key(path): digest for path, digest in pins.items()}


def new_output(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate followup output child required")
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def receipt(output, status, pins, m, **extra):
    m.authenticate(pins)
    write(output / "receipt.json", {"schema": "joint_frame_profile_followup_receipt/v1", "status": status,
        "source_sha256": {m.source_key(path): digest for path, digest in pins.items()},
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        "physical_release": False, **extra})


def mask_audit(m):
    """Read the exact stopped source branches and original accepted masks."""
    core = m.compatibility()
    old = read(m.FRAME / "comparison.json")
    source = read(SOURCE / "comparison.json")
    records = []
    with np.load(m.FRAME / "response.npz", allow_pickle=False) as saved:
        for tag in TARGETS:
            old_index, accepted = next((i, s) for i, s in enumerate(old["states"])
                if s["case_id"] + ("_zero" if s["gap_scale"] == 0 else "_gap") == tag)
            require(accepted["audit"]["all_passed"], "original source mask was not accepted")
            case, gap = accepted["case_id"], accepted["gap_scale"]
            disposition = next(s for s in source["case_dispositions"] if (s["case_id"], s["gap_scale"]) == (case, gap))
            require(not disposition["accepted_force_field_exists"], "retry target is already accepted")
            bearing = saved[tag + "_bearing"].copy()
            trace = read(SOURCE / (tag + "-stop.json"))["exception"]
            require(trace.startswith(core.FLOOR_FAILURE_PREFIX), "target lacks complete original procedure trace")
            history = json.loads(trace[len(core.FLOOR_FAILURE_PREFIX):])
            require(len(history) == 256 and len({tuple(e["bearing_footprints"]) for e in history}) == 256,
                    "source finite search inventory differs")
            matching = [e for e in history if e["bearing_footprints"] == np.flatnonzero(bearing).tolist()]
            require(len(matching) == 1, "source accepted mask is absent/duplicated in new trace")
            records.append({"state_tag": tag, "case_id": case, "gap_scale": gap, "bearing": bearing.tolist(),
                "original_accepted_state": {"path": m.source_key(m.FRAME / "comparison.json"),
                    "sha256": sha(m.FRAME / "comparison.json"), "pointer": "/states/" + str(old_index)},
                "new_profile_source_mask_trial": matching[0],
                "original_trace": {"path": m.source_key(SOURCE / (tag + "-stop.json")),
                    "sha256": sha(SOURCE / (tag + "-stop.json")), "pointer": "exception"},
                "question": "Can unchanged physical/panel tolerances be satisfied by one stricter solve at the original accepted floor mask?",
                "floor_nonexistence_claim": False, "physical_release": False})
    return records


def prepare(output, request, expected_sha256):
    m = mechanics()
    request = Path(request).resolve()
    require(sha(request) == expected_sha256, "request SHA differs")
    document = read(request)
    require(document.get("schema") == "joint_frame_profile_followup_request/v1"
            and document.get("source_frame_directory") == m.source_key(SOURCE)
            and document.get("source_frame_receipt_sha256") == SOURCE_RECEIPT_SHA256
            and document.get("target_state_tags") == list(TARGETS)
            and document.get("maximum_coupled_calls") == 3
            and document.get("solver_settings") == m.compatibility().REFINEMENT_SETTINGS, "frozen retry request differs")
    expected = source_bindings()
    require(all(document.get("source_sha256", {}).get(path) == digest for path, digest in expected.items()),
            "request omits/changes a required source binding")
    profile = m.module(HERE / "washer-working-profile-completion.py", "profile_followup_request_paths")
    pins = {}
    for path, digest in document["source_sha256"].items():
        profile.bind(pins, profile.artifact(ROOT, path, absolute=True), digest)
    m.authenticate(pins)
    output = new_output(output)
    (output / "request.json").write_bytes(request.read_bytes())
    write(output / "source-mask-audit.json", {"schema": "joint_frame_profile_source_mask_audit/v1",
        "status": "PREPARED_THREE_BOUNDED_SOURCE_MASK_RETRIES", "records": mask_audit(m),
        "source_accepted_states": 9, "source_trace_states": 5,
        "maximum_coupled_calls": 3, "new_coupled_calls": 0, "physical_release": False})
    receipt(output, "PREPARED_THREE_BOUNDED_SOURCE_MASK_RETRIES", pins, m, request_sha256=expected_sha256)
    return output


def profile_frame(m):
    frame = m.apply_joint_update(m.load_frame(), read(SOURCE / "joint-update.json"))
    frame["L"] = np.zeros((12, 12))
    return frame


def recover_shaft_pose(frame, force, rigid):
    joint = frame["joint"]
    pose = joint["Rbolt"] @ rigid[300:320] - joint["Cbolt"] @ frame["Bbolt"].T @ force
    require(np.max(abs(joint["Kbolt"] @ pose + frame["Bbolt"].T @ force)) <= .1,
            "new continuous shaft nodal balance failed")
    return pose


def retry(output, preparation):
    """Parent-only: three fixed-mask calls, without mask search or law changes."""
    m, pins = mechanics(), {}
    prepared = bind_packet(preparation, pins, m)
    require(prepared["status"] == "PREPARED_THREE_BOUNDED_SOURCE_MASK_RETRIES", "frozen preparation required")
    required = read(Path(preparation) / "source-mask-audit.json")["records"]
    require([r["state_tag"] for r in required] == list(TARGETS), "prepared target inventory differs")
    frame, core = profile_frame(m), m.compatibility()
    output = new_output(output)
    write(output / "inputs.json", {"source_frame": m.source_key(SOURCE), "source_frame_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "preparation": m.source_key(preparation), "solver_settings": core.REFINEMENT_SETTINGS,
        "maximum_coupled_calls": 3, "washer_joint_update": frame["joint_update"], "physical_release": False})
    vectors, states, dispositions = {}, [], []
    for record in required:
        tag, case, gap = record["state_tag"], record["case_id"], record["gap_scale"]
        c, bearing = m.load_coefficients(case, frame["dead_load_factor"]), np.asarray(record["bearing"], dtype=bool)
        audit, solver = None, None
        print(tag + ": one bounded stricter source-mask call", flush=True)
        try:
            f, q, a, solver, audit = core.fixed_floor_branch(frame["H"], frame["D"], frame["e"] @ c,
                frame["W"] @ c, frame["joint"], bearing, gap, core.REFINEMENT_SETTINGS)
            require(audit["all_passed"], "stricter source-mask physical/panel audit failed: " + json.dumps(audit))
            pose = recover_shaft_pose(frame, f, a)
        except ValueError as error:
            trial = getattr(error, "trial", None)
            if trial is not None:
                np.savez_compressed(output / (tag + "-unaccepted-trial.npz"),
                    trial_force_n=trial["force"], trial_motion_mm=trial["motion"], trial_rigid_scaled_mm=trial["rigid"])
            write(output / (tag + "-stop.json"), {"case_id": case, "gap_scale": gap, "exception": str(error),
                "solver": trial.get("solver") if trial else solver, "audit": trial.get("audit") if trial else audit,
                "accepted_force_field_exists": False, "physical_frame_failure_claim": False, "physical_release": False})
            dispositions.append({"case_id": case, "gap_scale": gap, "status": "STOP_NUMERICAL_QUALIFICATION_OPEN",
                "accepted_force_field_exists": False, "physical_frame_failure_claim": False, "physical_release": False,
                "stop_evidence": {"packet": m.source_key(output), "receipt_sha256": None,
                    "trace_path": m.source_key(output / (tag + "-stop.json")),
                    "trace_sha256": sha(output / (tag + "-stop.json")), "pointer": "exception"}})
            continue
        energy = m.assembled_potential(f, q, a, frame["H"], frame["e"], frame["W"], frame["L"], c,
            frame["joint"], gap, frame["energy_constant_scope"], frame["unchanged_constant_token"])
        vectors.update({tag + suffix: value for suffix, value in zip(SUFFIXES, (f, q, a, pose, bearing), strict=True)})
        states.append({"case_id": case, "gap_scale": gap, "audit": audit, "energy": energy, "solver": solver,
            "source_mask": record["original_accepted_state"], "floor_branch_history": [{"step": 0,
                "bearing_footprints": np.flatnonzero(bearing).tolist(), "solver": solver,
                "original_physical_law_audit": audit}], "physical_acceptance": False})
        dispositions.append({"case_id": case, "gap_scale": gap, "status": "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM",
            "accepted_force_field_exists": True, "response_tag": tag, "physical_release": False})
        print(tag + ": original physical/panel gates passed", flush=True)
    np.savez_compressed(output / "response.npz", **vectors)
    status = "COMPLETE_THREE_AUDITED_PROFILE_SOURCE_MASK_RETRIES" if len(states) == 3 else "PARTIAL_PROFILE_SOURCE_MASK_RETRIES_NUMERICAL_QUALIFICATION_OPEN"
    write(output / "comparison.json", {"schema": "joint_frame_profile_source_mask_retry/v1", "status": status,
        "states": states, "case_dispositions": dispositions, "new_coupled_calls": 3,
        "original_exhaustive_traces_preserved": True, "physical_release": False})
    receipt(output, status, pins, m, completed_states=len(states))
    return output


def diagnostic_context(m, pins):
    core = m.compatibility()
    adapter = m.module(core.DIAGNOSTICS, "profile_followup_same_field_diagnostics")
    contract, _, reference_receipts, references = adapter.frozen_inputs()
    for record in reference_receipts.values():
        pins[(ROOT / record["path"]).resolve()] = record["sha256"]
    shaft = m.module(HERE / "knee-compatible.py", "profile_followup_continuous_beam_models")
    models = {axis: shaft.assemble(contract["geometry"][axis],
        shaft.pure_helper(contract["geometry"][axis]["modeled_wood_grip_mm"])) for axis in core.AXES}
    labels = read(m.PREPARATION / "port-labels.json")["new_ports"]
    return core, adapter, contract, models, references, labels


def aggregate(output, retry_packet):
    """Source-only: preserve new fields, add exact metadata and diagnostics."""
    m, pins = mechanics(), {}
    require(sha(SOURCE / "receipt.json") == SOURCE_RECEIPT_SHA256, "actual profile source receipt differs")
    bind_packet(SOURCE, pins, m)
    retry_packet = Path(retry_packet).resolve()
    retried = bind_packet(retry_packet, pins, m)
    require(retried["status"] == "COMPLETE_THREE_AUDITED_PROFILE_SOURCE_MASK_RETRIES",
            "previously accepted states remain numerically open; do not close them as floor-search limitations")
    original, replacement = read(SOURCE / "comparison.json"), read(retry_packet / "comparison.json")
    states, dispositions, vectors = {}, {}, {}
    for packet, comparison in ((SOURCE, original), (retry_packet, replacement)):
        with np.load(packet / "response.npz", allow_pickle=False) as saved:
            for index, state in enumerate(comparison["states"]):
                key = (state["case_id"], state["gap_scale"])
                tag = key[0] + ("_zero" if key[1] == 0 else "_gap")
                require(state["audit"]["all_passed"] and key not in states, "duplicate or unaccepted retained field")
                states[key] = copy.deepcopy(state)
                states[key]["source_state_record"] = {"path": m.source_key(packet / "comparison.json"),
                    "sha256": sha(packet / "comparison.json"), "pointer": "/states/" + str(index)}
                for suffix in SUFFIXES:
                    vectors[tag + suffix] = saved[tag + suffix].copy()
            for disposition in comparison["case_dispositions"]:
                key = (disposition["case_id"], disposition["gap_scale"])
                item = copy.deepcopy(disposition)
                if not item["accepted_force_field_exists"]:
                    item["stop_evidence"]["receipt_sha256"] = sha(packet / "receipt.json")
                dispositions[key] = item
    require(len(dispositions) == 14 and len(states) == sum(d["accepted_force_field_exists"] for d in dispositions.values()),
            "complete exact fourteen-disposition inventory required")
    frame = profile_frame(m)
    core, adapter, contract, models, references, labels = diagnostic_context(m, pins)
    for key, state in states.items():
        case, gap = key
        tag = case + ("_zero" if gap == 0 else "_gap")
        f, q, a, pose, bearing = [vectors[tag + suffix] for suffix in SUFFIXES]
        c = m.load_coefficients(case, frame["dead_load_factor"])
        audit = core.force_law_audit(f, q, a, frame["H"], frame["D"], frame["e"] @ c, frame["W"] @ c,
            frame["joint"]["k"], frame["joint"]["unilateral"], frame["joint"]["floor_normals"],
            frame["joint"]["floor_tangents"], bearing, frame["joint"]["clearance_pairs"],
            gap * frame["joint"]["clearance_gaps"], frame["joint"]["panel_screw_ports"])
        require(audit["all_passed"], "retained new field fails unchanged applied-profile laws")
        require(np.max(abs(pose - recover_shaft_pose(frame, f, a))) <= 1e-8, "retained new shaft pose differs")
        state["compatible_shaft_diagnostics"] = core.shaft_diagnostics(case, f, q, pose,
            len(frame["joint"]["old_kept_lumped_rows"]), labels, contract, models, adapter, references)
        state["load_scope"] = "gravity_plus_proportional_accessory_only" if case == "dead-only" else "source_live_plus_gravity_and_accessory"
        state["same_saved_field_postprocessing_audit"] = audit
    output = new_output(output)
    inputs = read(SOURCE / "inputs.json")
    inputs.update(permanent_only_load_columns={"gravity": 0, "live": None},
        actual_profile_source={"path": m.source_key(SOURCE / "receipt.json"), "sha256": SOURCE_RECEIPT_SHA256},
        bounded_retry_source={"path": m.source_key(retry_packet / "receipt.json"), "sha256": sha(retry_packet / "receipt.json")},
        global_frame_solves_in_aggregate=0)
    write(output / "inputs.json", inputs)
    (output / "joint-update.json").write_bytes((SOURCE / "joint-update.json").read_bytes())
    (output / "joint-law-update.npz").write_bytes((SOURCE / "joint-law-update.npz").read_bytes())
    require(sha(output / "joint-update.json") == inputs["joint_update_sha256"], "applied profile contract bytes changed")
    np.savez_compressed(output / "response.npz", **vectors)
    status = core.PARTIAL_STATUS if len(states) < 14 else "COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES"
    report = copy.deepcopy(original)
    report.update(status=status, states=list(states.values()), case_dispositions=list(dispositions.values()),
        diagnostic_references=references,
        complete_requested_state_inventory=True,
        complete_six_case_zero_and_nominal_scope={key for key in states if key[0] in m.CASES} == {(case, gap) for case in m.CASES for gap in (0., 1.)},
        complete_permanent_zero_and_nominal_scope={key for key in states if key[0] == "dead-only"} == {("dead-only", gap) for gap in (0., 1.)},
        aggregate_global_frame_solves=0, original_nine_accepted_fields_preserved=True,
        original_five_exhaustive_traces_preserved=True, numerical_goal_complete=False, physical_release=False)
    write(output / "comparison.json", report)
    pins[Path(__file__).resolve()] = sha(__file__)
    m.authenticate(pins)
    write(output / "receipt.json", {"schema": "joint_frame_compatibility_completion_receipt/v1", "status": status,
        "source_sha256": {m.source_key(path): digest for path, digest in pins.items()},
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        "completed_states": len(states), "physical_release": False})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "retry", "aggregate"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--retry-packet", type=Path)
    args = parser.parse_args()
    if args.stage == "prepare":
        require(args.request is not None and args.expected_sha256, "frozen request and digest required")
        prepare(args.output, args.request, args.expected_sha256)
    elif args.stage == "retry":
        require(args.preparation is not None, "frozen retry preparation required")
        retry(args.output, args.preparation)
    else:
        require(args.retry_packet is not None, "completed bounded retry packet required")
        aggregate(args.output, args.retry_packet)


if __name__ == "__main__":
    main()
