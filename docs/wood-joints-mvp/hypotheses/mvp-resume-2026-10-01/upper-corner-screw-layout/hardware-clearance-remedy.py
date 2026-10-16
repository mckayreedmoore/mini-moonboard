"""Bounded response study of four specified top-side shafts in 9 mm bores.

The reviewed geometry and earlier evidence stay immutable. This proposal
changes only the four radial clearance laws. Its gross-member compliance,
washer profiles, panel axes and loads stay at the authenticated source basis.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE / "rawlocal/current-method-corrections/horizontal04"
SOURCE_RECEIPT_SHA = "1b279461a6d3898927a5202a02609d1b56add8a98ed9ce81355484e2cd319825"
AXES = tuple(f"top_outer/clip_single_top_{side}_{cleat}/side_{number}"
             for side, cleat in (("left", 1), ("right", 2)) for number in (1, 2))
SHAFT_MM = 7.9375
BORE_MM = 9.0


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def load_methods():
    import importlib.util

    path = HERE / "current-method-corrections.py"
    spec = importlib.util.spec_from_file_location("hardware_clearance_shared", path)
    shared = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared)
    return shared


def load_frame(shared):
    """Use the existing authenticated profile and panel-orientation adapter."""
    follow = shared.module(HERE / "joint-frame-profile-followup.py", "clearance_profile")
    pins = {Path(key) if Path(key).is_absolute() else ROOT / key: digest
            for key, digest in follow.source_bindings().items()}
    mechanics = follow.mechanics()
    frame = follow.profile_frame(mechanics)
    panel = shared.module(HERE / "panel-method-correction.py", "clearance_panel_orientation")
    frame["H"], frame["e"], orientation = panel.apply_cached_strong_x_delta(
        frame["H"], frame["e"], frame["joint"]["old_kept_lumped_rows"])
    for path, digest in {**frame["source_sha256"], **panel.PINS}.items():
        require(path not in pins or pins[path] == digest, "conflicting source binding")
        pins[path] = digest
    for path in (Path(__file__), HERE / "current-method-corrections.py",
                 HERE / "panel-method-correction.py"):
        pins[path] = shared.sha(path)
    require(shared.sha(SOURCE / "receipt.json") == SOURCE_RECEIPT_SHA,
            "horizontal source receipt changed")
    receipt = json.loads((SOURCE / "receipt.json").read_text())
    pins[SOURCE / "receipt.json"] = SOURCE_RECEIPT_SHA
    for name, digest in receipt["output_sha256"].items():
        path = (SOURCE / name).resolve()
        require(path.is_relative_to(SOURCE.resolve()), "source output escapes packet")
        require(shared.sha(path) == digest, "horizontal source output changed: " + name)
        pins[path] = digest
    mechanics.authenticate(pins)
    return follow, mechanics, frame, pins, orientation


def revise_clearance(shared, frame):
    core_path = HERE / "operators-attempt02/row-identities.json"
    rows = json.loads(core_path.read_text())
    mapping = json.loads((HERE / "rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json").read_text())
    selected = {}
    for item in mapping["kept_map"]:
        owners = {rows[old]["row_id"].rsplit("/", 1)[0] for old in item["raw_rows"]
                  if rows[old]["ownership"]["role"] == "candidate_bolt_lateral_plane"}
        if owners.intersection(AXES):
            require(len(owners) == 1 and len(item["raw_rows"]) == 1,
                    "top-side scalar row was lumped with another physical port")
            selected[item["kept_position"]] = next(iter(owners))
    require(len(selected) == 8 and set(selected.values()) == set(AXES),
            "four top-side lateral-pair identities differ")
    joint = frame["joint"]
    original = joint["clearance_gaps"].copy()
    new_gap = (BORE_MM - SHAFT_MM) / 2
    require(25.4 / 32 <= BORE_MM - SHAFT_MM <= 25.4 / 16,
            "proposed bore falls outside NDS12.1.3.2 nominal oversize interval")
    changed = []
    for index, pair in enumerate(joint["clearance_pairs"]):
        pair = list(map(int, pair))
        if any(row in selected for row in pair):
            require(all(row in selected for row in pair)
                    and len({selected[row] for row in pair}) == 1,
                    "top-side circle has mixed owners")
            require(abs(original[index] - 1.0625) < 1e-12, "source top-side gap differs")
            # These laws already use the specified 5/16-inch diameter. Do not
            # apply the earlier 1/4-to-5/16 stiffness multiplier a second time.
            require(np.max(abs(joint["k"][pair] - 3858.4325155228)) < 1e-7,
                    "top-side catalog-diameter spring basis differs")
            joint["clearance_gaps"][index] = new_gap
            changed.append({"axis_id": selected[pair[0]], "pair_index": index,
                            "lateral_rows": pair, "original_radial_gap_mm": float(original[index]),
                            "proposed_radial_gap_mm": new_gap,
                            "unchanged_lateral_stiffness_N_per_mm": joint["k"][pair].tolist()})
    require(len(changed) == 4, "proposed circle count differs")
    untouched = [i for i in range(len(original)) if i not in {r["pair_index"] for r in changed}]
    require(np.array_equal(original[untouched], joint["clearance_gaps"][untouched]),
            "unrelated bore clearance changed")
    return {"schema": "top_side_bore_clearance_remedy_proposal/v1",
            "axes": changed, "host_bores": 8, "reviewed_bore_mm": 7.5,
            "proposed_finished_bore_mm": BORE_MM, "specified_shaft_mm": SHAFT_MM,
            "minimum_radial_ligament_change_mm": -(BORE_MM - 7.5) / 2,
            "NDS_nominal_bore_interval_mm": [SHAFT_MM + 25.4 / 32, SHAFT_MM + 25.4 / 16],
            "lateral_and_axial_catalog_stiffness_already_present": True,
            "geometry_revision_reported_before_test": True,
            "reviewed_geometry_files_changed": False,
            "limits": ["Gap-law response only: no new bore-void/member compliance assembly.",
                       "Same single-washer force profile; doubled-stack force feedback is separate.",
                       "Delivered hole and shaft tolerances, edge/group checks and shank windows remain separate."],
            "primary_source": "https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf",
            "physical_release": False}


def audit_saved(core, frame, coefficient, gap, values):
    f, q, a, _pose, bearing = values
    joint = frame["joint"]
    return core.force_law_audit(f, q, a, frame["H"], frame["D"], frame["e"] @ coefficient,
        frame["W"] @ coefficient, joint["k"], joint["unilateral"], joint["floor_normals"],
        joint["floor_tangents"], bearing, joint["clearance_pairs"], gap * joint["clearance_gaps"],
        joint["panel_screw_ports"])


def apply_axis_operators(shared, mechanics, frame, source, pins):
    """Read a separately authenticated changed-point compliance packet."""
    from scipy import sparse

    source = Path(source).resolve()
    receipt = json.loads((source / "receipt.json").read_text())
    for name, digest in receipt["output_sha256"].items():
        path = (source / name).resolve()
        require(path.is_relative_to(source) and shared.sha(path) == digest,
                "axis-operator output changed: " + name)
        pins[path] = digest
    pins[source / "receipt.json"] = shared.sha(source / "receipt.json")
    preserved_code = {
        digest: (source / name).resolve()
        for name, digest in receipt["output_sha256"].items()
        if name.endswith(".py.snapshot")
    }
    for key, digest in receipt["source_sha256"].items():
        if key.endswith(".py.snapshot"):
            path = Path(key) if Path(key).is_absolute() else ROOT / key
            require(shared.sha(path) == digest, "preserved source-code snapshot changed")
            preserved_code[digest] = path
    for key, digest in receipt["source_sha256"].items():
        path = Path(key) if Path(key).is_absolute() else ROOT / key
        if path.suffix == ".py" and shared.sha(path) != digest and digest not in preserved_code:
            # Earlier runners save exact producer bytes. A matching complete
            # SHA identifies the historical code even when the operator
            # receipt originally named the live development helper.
            for archived in (HERE / "rawlocal/current-method-corrections").rglob("*.py.snapshot"):
                if shared.sha(archived) == digest:
                    preserved_code[digest] = archived.resolve()
                    break
        if path.suffix == ".py" and shared.sha(path) != digest and digest in preserved_code:
            # Verify the exact receipt-bound producer bytes for historical
            # packets after later code maintenance; data bindings stay exact.
            path = preserved_code[digest]
        require(path not in pins or pins[path] == digest, "axis source binding conflict")
        pins[path] = digest
    mechanics.authenticate(pins)
    with np.load(source / "operator-delta.npz", allow_pickle=False) as data:
        nrows = data["dH"].shape[0]
        previous = frame["H"].shape[0]
        require(nrows >= previous, "axis operator unexpectedly removes ports")
        if nrows > previous:
            count = nrows - previous
            require(count == 96 and context_count(source) == 98,
                    "only the authorized 32-screw port extension is supported")
            frame["H"] = np.pad(frame["H"], ((0, count), (0, count)))
            frame["D"] = np.pad(frame["D"], ((0, count), (0, 0)))
            frame["e"] = np.pad(frame["e"], ((0, count), (0, 0)))
            frame["Bbolt"] = np.pad(frame["Bbolt"], ((0, count), (0, 0)))
            laws = json.loads((source / "added-screw-laws.json").read_text())
            require(len(laws["k"]) == len(laws["unilateral"]) == count,
                    "added screw law census differs")
            joint = frame["joint"]
            joint["k"] = np.concatenate((joint["k"], laws["k"]))
            joint["unilateral"] = np.concatenate((joint["unilateral"], laws["unilateral"]))
            joint["panel_screw_ports"] = np.concatenate((joint["panel_screw_ports"],
                np.arange(previous, nrows)))
        if "dW" in data:
            require(data["dW"].shape == frame["W"].shape, "changed dead-load wrench shape differs")
            frame["W"] += data["dW"]
        for target, delta in (("H", "dH"), ("D", "dD"), ("e", "de")):
            require(data[delta].shape == frame[target].shape, "axis operator dimension differs")
            frame[target] += data[delta]
        recovery = {"D": data["D_raw"].copy(), "F": data["F_native"].copy()}
    recovery.update(B=sparse.load_npz(source / "B.npz").tocsr(),
                    rows=json.loads((source / "row-identities.json").read_text()),
                    axes=json.loads((source / "axes.json").read_text()),
                    mapping=json.loads((source / "source-row-map.json").read_text()))
    context = json.loads((source / "panel-reference-context.json").read_text())
    return recovery, context, {"path": mechanics.source_key(source),
                               "receipt_sha256": shared.sha(source / "receipt.json")}


def context_count(source):
    return json.loads((source / "panel-reference-context.json").read_text())["screw_axis_count"]


def apply_case_loads(shared, mechanics, frame, source, pins):
    """Apply a separately authenticated load comparison before geometry deltas."""
    from scipy import sparse

    source = Path(source).resolve()
    receipt = json.loads((source / "receipt.json").read_text())
    require(receipt.get("schema") == "climber_weight_load_delta_receipt/v1",
            "unsupported case-load packet")
    for key, digest in receipt["source_sha256"].items():
        path = Path(key) if Path(key).is_absolute() else ROOT / key
        if path.suffix == ".py" and shared.sha(path) != digest:
            snapshots = [p for p in (HERE / "rawlocal/current-method-corrections").rglob("*.py.snapshot")
                         if shared.sha(p) == digest]
            require(snapshots, "case-load producer bytes unavailable: " + key)
            path = snapshots[0]
        require(shared.sha(path) == digest, "case-load source changed: " + key)
        pins[path] = digest
    for name, digest in receipt["output_sha256"].items():
        path = (source / name).resolve()
        require(path.is_relative_to(source) and shared.sha(path) == digest,
                "case-load output changed: " + name)
        pins[path] = digest
    pins[source / "receipt.json"] = shared.sha(source / "receipt.json")
    comparison = json.loads((source / "load-comparison.json").read_text())
    require(comparison["horizontal_live_scale"] == 1
            and comparison["gravity_and_accessory_unchanged"]
            and comparison["geometry_operator_basis"] == "original_66_horizontal_profile_before_any_axis_operator_delta",
            "case-load comparison policy differs")
    with np.load(source / "load-delta.npz", allow_pickle=False) as data:
        require(data["de"].shape == frame["e"].shape and data["dW"].shape == frame["W"].shape,
                "case-load operator basis differs")
        require(np.max(abs(data["de"][:, ::2])) == 0 and np.max(abs(data["dW"][:, ::2])) == 0,
                "comparison changed gravity columns")
        frame["e"] += data["de"]
        frame["W"] += data["dW"]
        F = data["F_native"].copy()
    api = shared.module(HERE / "panel-compatible-response.py", "weight_panel_load_recovery")
    static = api.static_sources()
    with np.load(api.ORIGINAL / "operators.npz", allow_pickle=False) as data:
        D = data["D"].copy()
    recovery = {"D": D, "F": F, "B": sparse.load_npz(api.ORIGINAL / "B.npz").tocsr(),
        "axes": static.axes, "rows": static.rows,
        "mapping": json.loads((HERE / "rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json").read_text())}
    context = {"schema": "panel_remedy_reference_context/v1", "screw_axis_count": 66,
        "geometry": static.geometry, "head_pull_through_esg": 0.50,
        "panel_grade_owner_report": "Group 1, sanded A-C", "load_comparison": comparison,
        "physical_release": False}
    return recovery, context, {"path": mechanics.source_key(source),
        "receipt_sha256": shared.sha(source / "receipt.json"), "comparison": comparison}


def run(output, retry_source=None, axis_operators=None, case_loads=None):
    shared = load_methods()
    follow, mechanics, frame, pins, orientation = load_frame(shared)
    proposal = revise_clearance(shared, frame)
    recovery, context = None, None
    load_binding = None
    if case_loads is not None:
        recovery, context, load_binding = apply_case_loads(shared, mechanics, frame, case_loads, pins)
        proposal["case_load_comparison_packet"] = load_binding
    comparison_F = recovery["F"] if recovery is not None else None
    if axis_operators is not None:
        recovery, context, binding = apply_axis_operators(shared, mechanics, frame, axis_operators, pins)
        proposal["changed_axis_operator_packet"] = binding
        if comparison_F is not None:
            require(np.array_equal(recovery["F"][:, 1::2], comparison_F[:, 1::2]),
                    "geometry packet was not built with comparison live loads")
            context["load_comparison"] = load_binding["comparison"]
    core = mechanics.compatibility()
    settings = dict(core.REFINEMENT_SETTINGS)
    reuse, prior_vectors = {}, {}
    if retry_source is not None:
        retry_source = Path(retry_source).resolve()
        prior_receipt = json.loads((retry_source / "receipt.json").read_text())
        for name, digest in prior_receipt["output_sha256"].items():
            path = (retry_source / name).resolve()
            require(path.is_relative_to(retry_source), "retry path escapes packet")
            require(shared.sha(path) == digest, "retry source changed")
            pins[path] = digest
        pins[retry_source / "receipt.json"] = shared.sha(retry_source / "receipt.json")
        require(json.loads((retry_source / "proposal.json").read_text()) == proposal,
                "retry proposal differs")
        prior = json.loads((retry_source / "comparison.json").read_text())
        reuse = {r["state_tag"]: r for r in prior["states"] if r["audit"]["all_passed"]}
        with np.load(retry_source / "response.npz", allow_pickle=False) as data:
            prior_vectors = {key: data[key].copy() for key in data.files}
        settings = {**core.SOLVER_SETTINGS, "tol_feas": 1e-9}
    output = shared.output_directory(output)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    shared.write(output / "proposal.json", proposal)
    if context is not None:
        shared.write(output / "panel-reference-context.json", context)
    # New nominal gap checked against the exact circular spring answer before
    # any frame call; the existing native/conic formulation remains unchanged.
    f, q, _a, coupon_info = core.conic_branch(np.zeros((2, 2)), np.eye(2), np.zeros(2),
        np.array([3., 4.]), np.full(2, 1000.), np.zeros(2, dtype=bool), np.array([], dtype=int),
        np.array([[0, 1]]), np.array([(BORE_MM - SHAFT_MM) / 2]), settings)
    exact = np.array([3., 4.]) * (0.001 + (BORE_MM - SHAFT_MM) / 10)
    require(np.max(abs(f - [3., 4.])) < 1e-8 and np.max(abs(q - exact)) < 1e-8,
            "new-clearance analytic circle coupon failed")
    shared.write(output / "known-answer.json", {"force_N": f.tolist(), "motion_mm": q.tolist(),
        "exact_motion_mm": exact.tolist(), "solver": coupon_info, "passed": True,
        "primary_solver_docs": list(core.PRIMARY_DOCS)})
    shared.write(output / "inputs.json", {"source_sha256": {mechanics.source_key(p): h for p, h in pins.items()},
        "solver_settings": settings, "panel_orientation_adapter": orientation,
        "retry_source": str(retry_source) if retry_source else None,
        "unchanged_physics_tolerances": True,
        "maximum_new_fixed_floor_calls": (12 if axis_operators or case_loads else 7) if not reuse else 12 - len(reuse),
        "case_load_comparison": load_binding,
        "native_matrix_reassembly": False, "candidate_selected": False, "physical_release": False})
    baseline = json.loads((SOURCE / "comparison.json").read_text())
    states, dispositions, vectors = [], [], {}
    suffixes = ("_force", "_motion", "_rigid", "_shaft_pose", "_bearing")
    started = time.monotonic()
    with np.load(SOURCE / "response.npz", allow_pickle=False) as original:
        for source in baseline["states"]:
            tag, case, gap = [source[k] for k in ("state_tag", "case_id", "gap_scale")]
            coefficient = mechanics.load_coefficients(case, frame["dead_load_factor"])
            identical_zero = gap == 0 and axis_operators is None and (case_loads is None or case == "dead-only")
            if identical_zero or tag in reuse:
                data = prior_vectors if tag in reuse else original
                values = [data[tag + suffix].copy() for suffix in suffixes]
                audit = audit_saved(core, frame, coefficient, gap, values)
                require(audit["all_passed"], "reused field failed fresh original gates: " + tag)
                details = reuse.get(tag, source)["solver"]
                method = ("REUSED_ZERO_GAP_IDENTICAL_EQUATIONS"
                    if gap == 0 and axis_operators is None else "REUSED_AUDITED_PROPOSAL_FIELD")
            else:
                print(tag + ": specified top-side shafts / 9 mm bore clearance", flush=True)
                bearing = original[tag + "_bearing"].copy()
                trial = None
                try:
                    f, q, a, details, audit = core.fixed_floor_branch(frame["H"], frame["D"],
                        frame["e"] @ coefficient, frame["W"] @ coefficient, frame["joint"], bearing, gap, settings)
                    trial = {"solver": details, "audit": audit}
                    require(audit["all_passed"], "original physical gates failed")
                    pose = follow.recover_shaft_pose(frame, f, a)
                except ValueError as error:
                    trial = getattr(error, "trial", trial)
                    shared.write(output / (tag + "-stop.json"), {"error": str(error),
                        "trial_solver": trial.get("solver") if trial else None,
                        "trial_audit": trial.get("audit") if trial else None,
                        "accepted_force_field_exists": False, "physical_failure_claimed": False})
                    dispositions.append({"state_tag": tag, "case_id": case, "gap_scale": gap,
                        "accepted_force_field_exists": False, "status": "STOP_FIXED_SOURCE_MASK_OR_NUMERICAL_AUDIT"})
                    continue
                values, method = [f, q, a, pose, bearing], "NEW_PROPOSAL_FIXED_SOURCE_FLOOR_MASK"
            states.append({"state_tag": tag, "case_id": case, "gap_scale": gap, "audit": audit,
                           "solver": details, "field_method": method, "physical_release": False})
            vectors.update({tag + suffix: value for suffix, value in zip(suffixes, values, strict=True)})
            dispositions.append({"state_tag": tag, "case_id": case, "gap_scale": gap,
                "accepted_force_field_exists": True, "status": "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM"})
            shared.write(output / "progress.json", {"state_tag": tag, "accepted_states": len(states),
                "elapsed_seconds": time.monotonic() - started})
            print(tag + ": original physical gates passed; " + method, flush=True)
    shared.write(output / "comparison.json", {"schema": "top_side_clearance_remedy_response/v1",
        "states": states, "case_dispositions": dispositions, "requested_states": 12,
        "accepted_states": len(states), "baseline_unavailable_states": baseline["baseline_unavailable_states"],
        "physical_geometry_changed": axis_operators is not None, "gap_law_proposal_changed": True,
        "case_load_comparison": load_binding,
        "complete_joint_acceptance": False, "physical_release": False})
    np.savez_compressed(output / "response.npz", **vectors)
    recovered = shared.extract_panels(output, frame, states, vectors, recovery=recovery)
    shared.write(output / "summary.json", {"accepted_states": len(states), "elapsed_seconds": time.monotonic() - started,
        "stopped_requested_states": 12 - len(states), "baseline_unavailable_states": 2, **recovered,
        "complete_joint_acceptance": False, "physical_release": False})
    mechanics.authenticate(pins)
    shared.write(output / "receipt.json", {"schema": "hardware_clearance_remedy_receipt/v1",
        "source_sha256": {mechanics.source_key(p): h for p, h in pins.items()},
        "output_sha256": {p.name: shared.sha(p) for p in output.iterdir()
                          if p.is_file() and p.name != ".gitignore"},
        "status": "COMPLETED_BOUNDED_TOP_SIDE_CLEARANCE_PROPOSAL_RESPONSE", "physical_release": False})
    print(json.dumps({"output": str(output.relative_to(ROOT)), "accepted_states": len(states),
                      "head_peak_N": recovered["peak_head_tension_n"]["tension_n"]}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retry-source", type=Path)
    parser.add_argument("--axis-operators", type=Path)
    parser.add_argument("--case-loads", type=Path)
    args = parser.parse_args()
    sys.path[:0] = [str(ROOT), str(HERE.parent)]
    run(args.output, args.retry_source, args.axis_operators, args.case_loads)
