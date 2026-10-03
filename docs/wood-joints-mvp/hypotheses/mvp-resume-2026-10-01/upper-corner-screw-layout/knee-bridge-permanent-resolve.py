"""Prepare or execute one convex-seeded resolution of the frozen gap cycle.

Only the parent calls run(output). Import and --sourcepin-only use stdlib
source authentication only. The accepted original zero state is retained;
one nominal seed and one unchanged final solve are permitted. No retry exists.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-permanent-resolve"
PERMANENT = HERE / "knee-bridge-permanent.py"
OLD = HERE / "rawlocal/knee-bridge-permanent/attempt01"
CONIC = HERE / "conic_frame.py"
ORACLE = HERE / "rawlocal/load-lever/frame-attempt01/conic-seeding.json"
SCHEMA_STOP = RAW / "attempt01"
PINS = {
    PERMANENT: "3eddb384ac05820203bed59369ee270661b643bdc07e69159baec904eb5979a7",
    PERMANENT.with_suffix(".md"): "79fca9fdb96c2e88860aa7ef33ce89d3adc1ebebbdd2be4d97c6cac3e7203a10",
    OLD / "stop.json": "c3e568102c6cc921e09e526955f55860c01aa7be3e8f9b08b7ba8724f4918b7e",
    OLD / "response.npz": "df426ebdf6a8e6fe6ba9e7dbd36cbcf06aea3296a587bd96707c73b0e08bcaa1",
    OLD / "inputs.json": "0fd81c9f7c6ddcc4cabfaebb4da61a2bc10c3ba74d741a47c361dc5f2ab8da2f",
    OLD / "producer.py.snapshot": "3eddb384ac05820203bed59369ee270661b643bdc07e69159baec904eb5979a7",
    CONIC: "445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025",
    ORACLE: "4f04814e435742108b4cb6aa80562ea2fb7faca1bb27d94f082b2e0a94576ea7",
    HERE / "panel-orientation-comparison.md": "145e94349a0c8cb632d2388da7232bd33edf91d98b7618aca8b8ad1ef3c4a02f",
    SCHEMA_STOP / "stop.json": "2354ff0e77566a9e5744e5edc8065ed3e2cea2a82238beeaccc12afdfef666e7",
    SCHEMA_STOP / "resolution-method.json": "ab5187eeea1020ce7c9435726a04fb51485345d6b745c3895257b3e540088549",
    SCHEMA_STOP / "response.npz": "605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033",
    SCHEMA_STOP / "producer.py.snapshot": "0faa17c6acf94f59eb7bb5cd3505e5f31f23e8917c76e0daa9dbd6e7de07292c",
}
LIMITS = {
    "convex_seed_calls": 1, "convex_seed_max_iterations": 150,
    "convex_seed_time_limit_seconds": 30.0,
    "original_nominal_solver_calls": 1, "original_normal_branch_limit": 30,
    "original_zero_solver_calls": 0, "cycle_guard_retained": True,
    "disk_projection_method_unchanged": True, "floor_mask_searches": 0,
    "coupons_or_tests_executed": 0,
}


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


def preserved():
    require(sha(PERMANENT) == PINS[PERMANENT], "frozen permanent producer changed")
    spec = importlib.util.spec_from_file_location("private_permanent_for_resolution", PERMANENT)
    require(spec is not None and spec.loader is not None, "private producer import unavailable")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)  # The preserved producer has no mechanics imports here.
    return result


def source_pins():
    """Bind original STOP, unchanged mechanics and recorded cone known answers."""
    base = preserved()
    base.authenticate(PINS)
    pins = base.source_pins()
    for path, digest in PINS.items():
        base.bind(pins, path, digest)
    for name, digest in read(SCHEMA_STOP / "stop.json")["output_sha256"].items():
        require(Path(name).name == name, "schema STOP output must be an immediate file")
        base.bind(pins, SCHEMA_STOP / name, digest)
    base.bind(pins, Path(__file__), sha(Path(__file__)))
    base.authenticate(pins)
    return pins


def contract(pins):
    base = preserved()
    report = base.contract(pins)
    old, oracle = read(OLD / "stop.json"), read(ORACLE)
    require(old["status"] == "STOP_PERMANENT_COMPARISON"
            and len(old["states"]) == 2
            and old["states"][0]["state"] == "permanent-only_zero"
            and old["states"][0]["status"] == "PASS_CONDITIONAL_COUPLED_LAWS"
            and old["states"][0]["audit"]["force_bearing_rigid_rank"] == 300
            and old["states"][1]["state"] == "permanent-only_gap"
            and old["states"][1]["terminal_exception"] == "normal active-set cycle",
            "expected frozen zero-pass/nominal-cycle pair missing")
    require(old["source_gravity_assessment_sha256"] == report["source_gravity_assessment_sha256"]
            and old["source_comparison_sha256"] == report["source_comparison_sha256"]
            and old["source_response_sha256"] == report["source_response_sha256"]
            and old["modeled_mass_kg"] == report["modeled_mass_kg"]
            and old["dead_load_factor"] == report["dead_load_factor"]
            and old["census"] == report["census"] and old["wood_strength_CD"] == .9,
            "resolution must retain the same proposal and permanent loads")
    for name, digest in old["output_sha256"].items():
        require(sha(OLD / name) == digest, "changed original STOP output: " + name)
    require(oracle["producer_sha256"] == PINS[CONIC] and oracle["clarabel_version"] == "0.11.1"
            and oracle["preserved_solver_sha256"] == pins[base.PACKET / "right_corner_clearance.py"]
            and oracle["oracle"]["conic"]["status"] == "Solved"
            and oracle["oracle"]["circular_force_n"] == [3.0, 4.0],
            "recorded exact-helper cone direction/dual-sign evidence differs")
    report.update(
        schema="knee-bridge-permanent-gap-resolution/v1", status="PREPARED_NOT_EXECUTED",
        method="One preserved convex_seed from saved failed f, then preserved solve_state",
        original_stop_sha256=PINS[OLD / "stop.json"],
        original_response_sha256=PINS[OLD / "response.npz"],
        zero_state_reused_for_identical_frozen_inputs=True,
        original_nominal_cycle_replayed=False, numerical_initializer_is_acceptance=False,
        method_limits=LIMITS, runtime_pins={**base.RUNTIME, "clarabel": "0.11.1"},
        cone_known_answer_evidence={"path": str(ORACLE.relative_to(ROOT)), "sha256": PINS[ORACLE],
                                    "recorded_oracle": oracle["oracle"], "rerun": False},
        changed_library_behavior=False, tiny_coupon_required=False,
        parent_serialization_required=True,
        private_geometry_schema_adapter={
            "scope": "Only legacy global-axis metadata in the six-bore proposal validation call",
            "global_axis_fields_transformed_to_existing_grain_frame": True,
            "saved_axis_parameter_interval_renamed_without_change": True,
            "saved_grain_interval_checked_against_station_plus_minus_radius": True,
            "original_validator_and_tolerances_retained": True,
            "unknown_fields_or_physical_trims_still_rejected": True,
            "source_records_or_shared_helpers_modified": False,
            "prior_schema_stop_sha256": PINS[SCHEMA_STOP / "stop.json"],
            "prior_seed_calls": read(SCHEMA_STOP / "resolution-method.json")["seed_calls"],
            "prior_nominal_calls": read(SCHEMA_STOP / "resolution-method.json")["nominal_calls"],
        },
    )
    return report


def owned_output(output):
    output = Path(output).resolve()
    require(output.parent == RAW and RAW.resolve() == RAW and not output.exists(),
            "fresh immediate child of rawlocal/knee-bridge-permanent-resolve required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    # Preserve both original states before any environment/seed/solve failure.
    (output / "original-stop.json").write_bytes((OLD / "stop.json").read_bytes())
    (output / "original-response.npz").write_bytes((OLD / "response.npz").read_bytes())
    return output


def geometry_schema_proxy(helper, context):
    """Translate source-axis metadata; leave shape validation to the frozen helper."""
    legacy = {"axis_origin_global_xyz_mm", "axis_unit_global_xyz",
              "saved_axis_parameter_interval_mm", "saved_grain_interval_mm"}
    local = {"source_center_grain_u_v_mm", "axis_unit_grain_u_v", "axis_parameter_interval_mm"}

    def validate_geometry(geometry):
        # The original proposal object is also exported as provenance. Do not
        # replace it, drop unknown fields or change any cut/shape descriptor.
        translated = copy.deepcopy(geometry)
        mapped = []
        for hole in translated.get("bores", []):
            if not isinstance(hole, dict) or not legacy.intersection(hole):
                continue  # The original validator handles malformed/local holes.
            require(legacy.issubset(hole) and not local.intersection(hole),
                    "incomplete or conflicting legacy cylinder metadata")
            origin = helper._vector(hole.pop("axis_origin_global_xyz_mm"), 3, "global source center")
            direction = helper._vector(hole.pop("axis_unit_global_xyz"), 3, "global cylinder direction")
            start = helper._vector(geometry["start_xyz_mm"], 3, "source stock start")
            basis = [helper._vector(row, 3, "source grain frame")
                     for row in geometry["grain_frame_rows_xyz"]]
            require(len(basis) == 3, "source grain frame requires three rows")
            hole["source_center_grain_u_v_mm"] = [
                sum(row[j] * (origin[j] - start[j]) for j in range(3)) for row in basis]
            hole["axis_unit_grain_u_v"] = [
                sum(row[j] * direction[j] for j in range(3)) for row in basis]
            # Retain the physical shaft endpoints, including their sign and
            # source-axis parameterization. The helper checks full stock span.
            hole["axis_parameter_interval_mm"] = hole.pop("saved_axis_parameter_interval_mm")
            interval = helper._vector(hole.pop("saved_grain_interval_mm"), 2, "saved grain interval")
            station = helper._number(hole.get("station_mm"), "bore station")
            radius = helper._number(hole.get("radius_mm"), "bore radius")
            require(all(abs(a - b) <= helper.GEOMETRY_TOL_MM
                        for a, b in zip(interval, [station - radius, station + radius])),
                    "saved grain interval differs from the declared cylinder")
            mapped.append({"axis_id": hole.get("axis_id"),
                           "source_center_grain_u_v_mm": hole["source_center_grain_u_v_mm"],
                           "axis_unit_grain_u_v": hole["axis_unit_grain_u_v"],
                           "axis_parameter_interval_mm": hole["axis_parameter_interval_mm"],
                           "saved_grain_interval_mm": interval})
        result = helper.validate_geometry(translated)
        context.setdefault("geometry_schema_validations", []).append({
            "body": geometry.get("block"), "translated_legacy_bores": mapped,
            "all_cylinders_validated": len(result[1]),
            "original_validator_sha256": sha(Path(helper.__file__)),
            "source_geometry_copied_before_translation": True,
        })
        return result

    return SimpleNamespace(__file__=helper.__file__, validate_geometry=validate_geometry)


def install_private_adapter(base, output, context):
    """Configure a disposable producer/dead module, never shared mechanics globals."""
    original_module = base.module

    def adapted_module(path, name):
        dead = original_module(path, name)
        if Path(path) == base.GEOMETRY_HELPER:
            return geometry_schema_proxy(dead, context)
        if Path(path) != base.DEAD:
            return dead
        load_helpers, solve_state, replay_members = dead.load_helpers, dead.solve_state, dead.replay_members

        def configured_helpers():
            frame, solver, disk, bounds, method = load_helpers()
            version = importlib.metadata.version("clarabel")
            require(version == "0.11.1", "Clarabel runtime differs from recorded method evidence")
            conic = original_module(CONIC, "private_preserved_convex_initializer")
            context["conic"], context["runtime_clarabel"] = conic, version

            def capture_floor(*args):
                result = frame.lump_floor(*args)
                context["transform"] = result[8]
                return result

            # Only the private return value is adapted; frame.lump_floor stays intact.
            proxy = SimpleNamespace(__file__=frame.__file__, lump_floor=capture_floor)
            return proxy, solver, disk, bounds, method

        def seeded_state(helper, disk, bounds, matrices, targets, gaps, seed, gap_scale):
            import numpy as np

            with np.load(OLD / "response.npz", allow_pickle=False) as saved:
                if gap_scale == 0.0:
                    context["phase"] = "reuse_original_zero"
                    transform = context["transform"]
                    raw = saved["permanent-only_zero_raw_force_n"].copy()
                    # Disjoint rows: T T' is diagonal. Recover the original lumped
                    # force, not T @ raw alone (which scales weighted floor forces).
                    norms = np.einsum("ij,ij->i", transform, transform)
                    require(np.all(norms > 0), "floor map cannot recover zero force")
                    f = (transform @ raw) / norms
                    require(np.max(abs(transform.T @ f - raw)) < helper.FORCE_TOL,
                            "reused zero force leaves the frozen floor map")
                    original = read(OLD / "stop.json")["states"][0]
                    return (f, saved["permanent-only_zero_lumped_q_mm"].copy(),
                            saved["permanent-only_zero_rigid_coordinates"].copy(),
                            copy.deepcopy(original["audit"]), None)
                require(gap_scale == 1.0 and context["seed_calls"] == 0,
                        "only one nominal initializer is permitted")
                H, D, e, W, k, uni, normals, tangents = matrices
                f, q, a = [saved["permanent-only_gap_unaccepted_" + key].copy() for key in ("f", "q", "a")]
            require(f.shape == q.shape == k.shape and a.shape == W.shape
                    and all(np.isfinite(v).all() for v in (f, q, a)), "invalid saved cycle vectors")
            identity_error = float(np.max(abs(q - (D @ a + e - H @ f))))
            require(identity_error < helper.GAP_TOL, "saved cycle iterate belongs to a different load/operator map")
            context["phase"] = "one_convex_seed"
            context["seed_calls"] += 1
            guessed, info = context["conic"].convex_seed(
                H, D, e, W, k, uni, normals, tangents, targets, gaps, f)
            context["seed_report"] = {**info, "saved_iterate_compatibility_error_mm": identity_error,
                                      "saved_floor_force_n": f[normals].tolist(),
                                      "saved_floor_motion_mm": q[normals].tolist()}
            require(guessed.shape == f.shape and np.isfinite(guessed).all(), "nonfinite convex force initializer")
            context["initial_normal_branch_changed"] = bool(
                not np.array_equal(uni & (f > 1e-6), uni & (guessed > 1e-6)))
            context["original_failed_starting_branch_changed"] = bool(
                not np.array_equal(uni & (seed > 1e-6), uni & (guessed > 1e-6)))
            np.savez_compressed(output / "convex-seed.npz", force_n=guessed)
            require(context["original_failed_starting_branch_changed"],
                    "convex initializer selects the original failed starting branch; deterministic rerun prohibited")
            context["phase"] = "one_original_nominal_solve"
            context["nominal_calls"] += 1
            try:
                return solve_state(helper, disk, bounds, matrices, targets, gaps, guessed, 1.0)
            except ValueError as error:
                trace, terminal = error.__traceback__, {}
                while trace is not None:
                    if trace.tb_frame.f_code is helper.solve.__code__:
                        terminal = trace.tb_frame.f_locals
                    trace = trace.tb_next
                context["final_solver_history"] = copy.deepcopy(terminal.get("history", []))
                context["final_solver_exception"] = str(error)
                context["final_solver_iteration"] = int(terminal["iteration"]) if "iteration" in terminal else None
                context["final_solver_active_rows"] = terminal["active"].tolist() if "active" in terminal else None
                raise

        def exact_zero_replay(method, operators, raw_states, pins):
            import numpy as np

            with np.load(OLD / "response.npz", allow_pickle=False) as saved:
                raw_states["permanent-only_zero"] = saved["permanent-only_zero_raw_force_n"].copy()
            return replay_members(method, operators, raw_states, pins)

        dead.load_helpers, dead.solve_state, dead.replay_members = configured_helpers, seeded_state, exact_zero_replay
        return dead

    base.module = adapted_module


def finalize(output, context, error):
    """Keep zero arrays byte-identical and expose both state records on every STOP."""
    target = output / ("comparison.json" if (output / "comparison.json").exists() else "stop.json")
    report = read(target)
    if (output / "response.npz").exists():
        with preserved().import_environment():
            import numpy as np

            with np.load(output / "response.npz", allow_pickle=False) as data:
                arrays = {name: data[name].copy() for name in data.files}
            with np.load(OLD / "response.npz", allow_pickle=False) as data:
                for name in data.files:
                    if name.startswith("permanent-only_zero_"):
                        arrays[name] = data[name].copy()
            np.savez_compressed(output / "response.npz", **arrays)
    original_zero = copy.deepcopy(read(OLD / "stop.json")["states"][0])
    original_zero.update(reused_without_solve=True, original_stop_sha256=PINS[OLD / "stop.json"])
    states = [original_zero, *[s for s in report.get("states", []) if s["gap_scale"] == 1.0]]
    if len(states) == 1:
        states.append({"case_id": "permanent-only", "state": "permanent-only_gap", "gap_scale": 1.0,
                       "status": "STOP_RESOLUTION_BEFORE_RETURNED_NOMINAL_STATE",
                       "phase": context["phase"], "terminal_exception": str(error),
                       "audit": None, "complete_member_acceptance": False})
    seed_record = {key: value for key, value in context.items() if key not in ("conic", "transform")}
    seed_record.update(schema="one_bounded_convex_seed/v1", numerical_seed_is_acceptance=False,
                       known_answer_evidence_sha256=PINS[ORACLE], method_limits=LIMITS)
    write(output / "resolution-method.json", seed_record)
    report.update(states=states, resolution_method_sha256=sha(output / "resolution-method.json"),
                  accepted_zero_preserved_without_resolve=True, original_stop_sha256=PINS[OLD / "stop.json"],
                  resolver_producer_sha256=sha(Path(__file__)),
                  runtime_clarabel=context.get("runtime_clarabel"),
                  post_execution_source_authentication=context.get("post_execution_source_authentication", False))
    if context.get("source_authentication_exception"):
        report.update(status="STOP_RESOLUTION_SOURCE_AUTHENTICATION",
                      source_authentication_exception=context["source_authentication_exception"])
    report["output_sha256"] = {p.name: sha(p) for p in sorted(output.iterdir())
                               if p.is_file() and p.name not in ("comparison.json", "stop.json")}
    write(target, report)
    return report


def run(output):
    """Parent API: preserve zero, seed/solve nominal once, then reuse member replay."""
    pins = source_pins()
    report = contract(pins)
    output = owned_output(output)
    write(output / "inputs.json", report)
    base = preserved()
    old_parameters = {key: getattr(base, key) for key in ("module", "source_pins", "contract", "owned_output")}
    context = {"phase": "environment", "seed_calls": 0, "nominal_calls": 0}
    failure = None
    try:
        base.source_pins = lambda: pins
        base.contract = lambda bound: copy.deepcopy(report)
        base.owned_output = lambda path: output
        install_private_adapter(base, output, context)
        base.run(output)
    except Exception as error:
        failure = error
        raise
    finally:
        for key, value in old_parameters.items():
            setattr(base, key, value)
        # Original producer always writes a final record after owned_output.
        if (output / "stop.json").exists() or (output / "comparison.json").exists():
            authentication_error = None
            try:
                base.authenticate(pins)
                context["post_execution_source_authentication"] = True
            except ValueError as error:
                authentication_error = error
                context["post_execution_source_authentication"] = False
                context["source_authentication_exception"] = str(error)
            completed = finalize(output, context, failure)
            if authentication_error is not None:
                raise authentication_error
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--sourcepin-only", action="store_true")
    modes.add_argument("--run", action="store_true", help="parent-owned serialized execution")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sourcepin_only:
        pins = source_pins()
        output = owned_output(args.output)
        write(output / "api-freeze.json", contract(pins))
        print("PASS_SOURCEPINS_ONLY", sha(Path(__file__)), "pins", len(pins))
        return
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "shared mechanics slot occupied")
        run(args.output)


if __name__ == "__main__":
    main()
