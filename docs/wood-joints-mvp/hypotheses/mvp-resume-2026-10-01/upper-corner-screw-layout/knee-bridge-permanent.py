"""Parent-owned permanent comparison for the frozen six-bore knee proposal.

Import and --sourcepin-only perform no mechanics, CAD, native solve or coupon.
run(output) executes exactly two states using the preserved pure functions.
The parent must serialize API calls through the shared analysis slot.
"""

from __future__ import annotations

import argparse
import copy
import csv
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-permanent"
DEAD = HERE / "dead-load-check.py"
FRAME = HERE / "rawlocal/knee-bridge-gravity/attempt01"
SOURCE = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
MEMBERS = PACKET / "member-screen-attempt02/knee-bridge-gravity01"
STABILITY = PACKET / "member-stability-attempt01/four-screw-layout01/checks.json"
GEOMETRY = HERE / "rawlocal/knee-bridge-geometry/attempt01"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
ORACLE = HERE / "rawlocal/dead-load-check/parent-attempt06/comparison.json"
GEOMETRY_HELPER = HERE / "longitudinal-bore-geometry.py"
SPINES = ("knee_outer_left_spine", "knee_outer_right_spine")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
CD = 0.9
RUNTIME = {"python": "3.12.3", "numpy": "2.5.2", "scipy": "1.18.1", "osqp": "1.0.4"}
PINS = {
    DEAD: "ffdb2ee797000c055cd67c6e46ac80e549b4865a79346e728074625767bf213d",
    FRAME / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    FRAME / "operators.npz": "7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f",
    SOURCE / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    SOURCE / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    SOURCE.parent / "receipt.json": "6acb01eb1b07dc9f9175cb3a0e916fe74a9a32a7b90941cf3b18e84a24d9c599",
    MEMBERS / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    MEMBERS / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBERS / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    STABILITY: "aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574",
    GEOMETRY / "manifest.json": "254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147",
    GEOMETRY / "inputs.json": "25c3a49825d898815e4311c95ea0f16be1bcf415d9983d496feb0371d157d965",
    GEOMETRY / "receipt.json": "92ccabb307b6d9cbcd8f768b8275a7ecf4ef6ae6a55a7be2cd83742d76be9973",
    GEOMETRY_HELPER: "faab8b5e5ff13dc4252329ed2f8917d9e2054f05e823a4e5fdbeb11da46accc4",
    INTEGRATION: "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    ORACLE: "20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75",
}
FLAGS = dict.fromkeys((
    "proposal_adopted", "source_acceptance_transferred", "complete_member_acceptance",
    "complete_joint_acceptance", "full_frame_acceptance", "strict_frame_stability",
    "actual_changed_hole_elastic_stiffness_established", "local_bridge_compatibility_solved",
    "internal_bridge_permanent_allocation_qualified", "opening_resistance_qualified",
    "formal_torsion_qualification", "physical_release", "fabrication_release",
    "native_launch", "CAD_rebuilt", "geometry_changed", "hardware_changed",
    "material_laws_changed", "tests_run", "review_run", "rated_cases_replaced",
    "combined_duration_basis_adopted", "engineering_oracles_executed",
), False)


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


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source outside repository")
    require(path not in pins or pins[path] == digest, "conflicting source binding: " + str(path))
    pins[path] = digest


@contextmanager
def import_environment():
    """Restore import settings changed by the preserved helper imports."""
    old_path, old_bytecode = sys.path[:], sys.dont_write_bytecode
    sys.path[:0] = [str(PACKET), str(ROOT)]
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.path[:] = old_path
        sys.dont_write_bytecode = old_bytecode


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    result = importlib.util.module_from_spec(spec)
    with import_environment():
        spec.loader.exec_module(result)
    return result


def source_pins():
    """Authenticate the recorded source closure without importing mechanics."""
    authenticate(PINS)
    dead = module(DEAD, "knee_permanent_preserved_dead")
    # This authenticates old evidence, not old demands for the new comparison.
    # It also verifies the recorded bottom-helper reporting-only substitution.
    pins = {**dead.source_pins(), **PINS}
    bottom = PACKET / "bottom_corner_checks.py"
    snapshot = PACKET / "bottom-corner-component-attempt06/producer.py.snapshot"
    for report_path, directory in (
        (FRAME / "operator-assessment.json", FRAME),
        (SOURCE / "comparison.json", None),
        (SOURCE.parent / "receipt.json", SOURCE.parent),
        (MEMBERS / "member-results.json", MEMBERS),
        (GEOMETRY / "receipt.json", GEOMETRY),
        (GEOMETRY / "inputs.json", None),
        (INTEGRATION, None),
    ):
        report = read(report_path)
        for relative, digest in report["source_sha256"].items():
            path = ROOT / relative
            if path == bottom and digest == pins[snapshot]:
                continue  # Its exact old bytes and unchanged saved_actions are already bound.
            bind(pins, path, digest)
        if directory is not None:
            for relative, digest in report["output_sha256"].items():
                path = (directory / relative).resolve()
                require(path.is_relative_to(directory), "output binding leaves source packet")
                bind(pins, path, digest)
    bind(pins, Path(__file__), sha(Path(__file__)))
    authenticate(pins)
    return pins


def contract(pins):
    assessment, source, member, integration, geometry = [read(path) for path in (
        FRAME / "operator-assessment.json", SOURCE / "comparison.json",
        MEMBERS / "member-results.json", INTEGRATION, GEOMETRY / "inputs.json")]
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["operator_ready"] and assessment["gravity_delta_in_proposal_operators"]
            and assessment["H_D_B_connector_rows_and_k_unchanged"], "fresh gravity operators not ready")
    require(source["frame_operator_directory"] == member["frame_operator_directory"]
            == str(FRAME.relative_to(ROOT))
            and member["clearance_input_directory"] == str(SOURCE.relative_to(ROOT)),
            "fresh member/frame/operator binding differs")
    require(source["source_sha256"][str((FRAME / "operator-assessment.json").relative_to(ROOT))]
            == PINS[FRAME / "operator-assessment.json"]
            and source["response_sha256"] == PINS[SOURCE / "response.npz"], "fresh response binding differs")
    require({(s["case_id"], s["gap_scale"]) for s in source["states"]}
            == {(case, gap) for case in CASES for gap in (0.0, 1.0)}
            and len(source["states"]) == 12 and tuple(assessment["case_ids"]) == CASES,
            "fresh six-case seed census differs")
    mass, factor = assessment["modeled_mass_kg"], assessment["dead_load_factor"]
    require(mass == source["modeled_mass_kg"] == 225.19791414318078
            and factor == source["dead_load_factor"] == member["same_state_dead_load_factor"]
            == 1.1110134616260479 and abs(factor - (mass + 25.0) / mass) < 1e-14,
            "new gravity/equipment allowance differs")
    census = integration["census"]
    require(census["current"] == {"bolts": 104, "nuts": 104, "washers": 208, "Hillman_screws": 66}
            and census["proposal"] == {"bolts": 108, "nuts": 108, "washers": 216, "Hillman_screws": 66}
            and census["new_internal_bolt_axes"] == 4, "global/proposal inventory differs")
    require(set(geometry["bodies"]) == set(SPINES), "six-bore geometry body census differs")
    for body, record in geometry["bodies"].items():
        old, new = record["original_geometry"], record["proposal_geometry"]
        require(len(old["bores"]) == 4 and new["bores"] == old["bores"] + record["new_axes"]
                and [(b["station_mm"], b["radius_mm"], b["removed_interval_axis"])
                     for b in record["new_axes"]] == [(100.0, 3.75, 1), (250.0, 3.75, 1)],
                "four original plus two proposed bores required: " + body)
    oracle = read(ORACLE)
    require(oracle["engineering_oracles_executed"] and oracle["engineering_oracles"]["floor"]
            == "PASS_COMPRESSION_NO_SLIP_AND_TENSION_REFUSAL_ORACLE", "recorded floor/disk evidence missing")
    return {
        "schema": "knee-bridge-permanent-comparison/v1", "status": "PREPARED_NOT_EXECUTED",
        "api": "run(output: Path) -> dict; source_pins() -> authenticated pins",
        "frame_operator_directory": str(FRAME.relative_to(ROOT)),
        "source_comparison_sha256": PINS[SOURCE / "comparison.json"],
        "source_response_sha256": PINS[SOURCE / "response.npz"],
        "source_gravity_assessment_sha256": PINS[FRAME / "operator-assessment.json"],
        "modeled_mass_kg": mass, "equipment_mass_kg": 25.0, "dead_load_factor": factor,
        "load_case": "permanent-only", "gap_scales": [0.0, 1.0],
        "selected_unfactored_gravity_column": 0, "equipment_multiplier_applied_once": True,
        "additional_dead_load_multiplier": 1.0,
        "live_gravity_scale": 0.0, "live_horizontal_scale": 0.0, "live_moment_scale": 0.0,
        "wood_strength_CD": CD, "duration_adjusted_strengths": ["Fb", "Ft_parallel", "Fc_parallel", "Fv"],
        "elastic_or_hardware_duration_factor": 1.0,
        "census": {"raw_rows": 1888, "clearance_planes": 88, "floor_footprints": 8,
                   "rigid_coordinates": 300, "unchanged_timber_bodies": 42,
                   "modified_six_bore_spines": 2, "global_bolts": 104,
                   "Hillman_screws": 66, "proposal_bolts": 108, "internal_static_bolts": 4},
        "declared_adapter_overrides": ["private dead.FRAME", "private dead.SOURCE",
                                       "private dead.MEMBERS", "private dead.STABILITY",
                                       "private dead.read for in-memory geometry only"],
        "known_answer_evidence": {"path": str(ORACLE.relative_to(ROOT)), "sha256": PINS[ORACLE],
                                  "recorded_results": oracle["engineering_oracles"],
                                  "rerun": False, "scope": "Same pinned floor and circular-gap methods only; no proposal acceptance."},
        "runtime_pins": RUNTIME, "frame_solve": False,
        "opening_section_basis": "Signed cut demands and six-bore exclusion coverage; opening resistance is missing.",
        "source_sha256": {str(p.relative_to(ROOT)): digest for p, digest in sorted(pins.items())},
        **FLAGS,
    }


def owned_output(output):
    output = Path(output).resolve()
    require(output.parent == RAW and not output.exists() and RAW.resolve() == RAW,
            "fresh immediate child of rawlocal/knee-bridge-permanent required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def proposal_records(method):
    """Refresh both spine exclusions from six-bore sources; preserve other 42 records."""
    packet = read(MEMBERS / "geometry.json")
    records = copy.deepcopy(packet["members"])
    proposal = read(GEOMETRY / "inputs.json")["bodies"]
    manifest = read(GEOMETRY / "manifest.json")["bodies"]
    helper = module(GEOMETRY_HELPER, "knee_permanent_geometry")
    require(len(records) == 44 and set(SPINES).issubset(records), "44-timber census differs")
    for body in SPINES:
        record, source = records[body], proposal[body]
        old, new = source["original_geometry"], source["proposal_geometry"]
        helper.validate_geometry(new)  # Pure validation, never analytical_coupon or CAD.
        geometry = record["geometry"]
        require(geometry["start"] == new["start_xyz_mm"]
                and [geometry[k] for k in ("axis", "section_u", "section_v")] == new["grain_frame_rows_xyz"]
                and [geometry["width_mm"], geometry["depth_mm"]] == new["width_depth_mm"],
                "proposal grain/stock placement differs: " + body)
        require({b["id"] for b in record["bore_or_passage_intervals"]}
                == {b["axis_id"] for b in old["bores"]}, "old member openings differ: " + body)
        for bore in old["bores"]:
            prior = next(b for b in record["bore_or_passage_intervals"] if b["id"] == bore["axis_id"])
            require([prior["lo"], prior["hi"]] == bore["saved_grain_interval_mm"], "old bore interval differs")
        intervals = [{"id": b["axis_id"], "lo": b["station_mm"] - b["radius_mm"],
                      "hi": b["station_mm"] + b["radius_mm"], "radius_mm": b["radius_mm"],
                      "source": "frozen_six_bore_proposal_geometry"} for b in new["bores"]]
        # Preserve old stations; add center, tangent, and 0.001 mm flank samples.
        stations = set(record["stations_mm"])
        for bore in source["new_axes"]:
            station, radius = bore["station_mm"], bore["radius_mm"]
            stations.update((station, station - radius, station + radius,
                             station - radius - .001, station - radius + .001,
                             station + radius - .001, station + radius + .001))
        record["stations_mm"] = sorted(stations)
        record["bore_or_passage_intervals"] = intervals
        record["rectangle_at_station"] = [method.member.rectangle_at(
            s, geometry, record["profile_planes"], intervals) for s in record["stations_mm"]]
        name = body + ".proposal.step"
        record["current_finished_step"] = str((GEOMETRY / name).relative_to(ROOT))
        record["current_finished_step_sha256"] = manifest[body]["exports"][name]["sha256"]
        record["permanent_proposal_geometry"] = new
        # The original diagnostic descriptor remains provenance, never a six-bore capacity.
        record["geometry_descriptor_scope"] = "Original stock/basis descriptor; finished opening scope is permanent_proposal_geometry."
        record["opening_resistance_qualified"] = False
    packet["members"] = records
    return packet


@contextmanager
def replay_adapter(dead, packet):
    """Override only a private module instance and restore every parameter."""
    overrides = {"FRAME": FRAME, "SOURCE": SOURCE, "MEMBERS": MEMBERS, "STABILITY": STABILITY,
                 "read": lambda path: packet if Path(path) == MEMBERS / "geometry.json" else read(path)}
    previous = {name: getattr(dead, name) for name in overrides}
    try:
        for name, value in overrides.items():
            setattr(dead, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(dead, name, value)


def section_coverage(packet, arrays, tags):
    """Export every signed cut, including null opening/profile references."""
    coverage = []
    for body, record in packet["members"].items():
        for tag in tags:
            values = arrays[tag + "__" + body + "__internal_negative_grain_u_v"]
            for i, value in enumerate(values):
                rectangle = record["rectangle_at_station"][i // 2]
                applicable = rectangle["status"].startswith("BORE_FREE_")
                coverage.append({"state": tag, "member": body, "station_mm": record["stations_mm"][i // 2],
                                 "trace": "before" if i % 2 == 0 else "after", "section": rectangle,
                                 "signed_cut_grain_u_v_n_nmm": value.tolist(),
                                 "normal_shear_torsion_reference_applicable": applicable,
                                 "opening_resistance_ratio": None,
                                 "missing_basis": None if applicable else "Finished opening/profile resistance, local traction and ligament transfer; no intact-rectangle ratio.",
                                 "modified_six_bore_spine": body in SPINES})
    return coverage


def opening_register(packet, coverage):
    """Name every opening and its demand coverage without inventing resistance."""
    result = []
    for body, record in packet["members"].items():
        for opening in record["bore_or_passage_intervals"]:
            witnesses = [r for r in coverage if r["member"] == body
                         and opening["id"] in r["section"].get("feature_ids", [])]
            result.append({"member": body, "opening": opening,
                           "modified_six_bore_spine": body in SPINES,
                           "signed_demand_witness_count": len(witnesses),
                           "states_with_saved_demands": sorted({r["state"] for r in witnesses}),
                           "demand_witnesses": [{k: r[k] for k in (
                               "state", "station_mm", "trace", "signed_cut_grain_u_v_n_nmm")}
                                                for r in witnesses],
                           "opening_resistance_ratio": None,
                           "status": "DEMAND_SAMPLES_ONLY_MISSING_OPENING_RESISTANCE_BASIS" if witnesses
                                     else "MISSING_DEMAND_SAMPLES_AND_OPENING_RESISTANCE_BASIS"})
    require(all(sum(r["member"] == body for r in result) == 6 for body in SPINES),
            "six openings per modified spine must remain explicit")
    return result


def exceptions(traces):
    """Retain domain nulls, strength exceedances and separate sensitivities."""
    result = []
    for trace in traces:
        reasons = []
        for scope in ("end_only", "timber_braced"):
            if not trace[scope + "_domain_ok"]:
                reasons.append(scope + "_normal_domain_exception")
            ratio = trace[scope + "_normal_ratio_cd0_9"]
            if ratio is None or ratio > 1:
                reasons.append(scope + "_normal_strength_exception")
        if trace["timber_braced_normal_exceeds"]:
            reasons.append("timber_braced_normal_or_3_9_4_exception")
        for metric, label in (("shear_face_ratio_cd0_9", "face_shear_strength_exception"),
                              ("shear_component_bound_cd0_9", "component_bound_sensitivity"),
                              ("coefficient5_sensitivity_cd0_9", "coefficient5_sensitivity"),
                              ("RT_swap_sensitivity_cd0_9", "RT_swap_sensitivity")):
            if trace[metric] is not None and trace[metric] > 1:
                reasons.append(label)
        if reasons:
            result.append({"reasons": reasons, "signed_witness": trace})
    return result


def run(output):
    """Parent-only two-state numerical execution; no all-pass requirement."""
    pins = source_pins()
    report = contract(pins)
    output = owned_output(output)
    write(output / "inputs.json", report)
    states, responses, raw_states = [], {}, {}
    try:
        versions = {"python": platform.python_version(), **{
            name: importlib.metadata.version(name) for name in ("numpy", "scipy", "osqp")}}
        require(versions == RUNTIME, "runtime differs from fresh frame pins: " + str(versions))
        report["runtime_versions"] = versions
        with import_environment():
            import numpy as np

            dead = module(DEAD, "knee_permanent_execution_dead")
            frame, solver, disk, bounds, method = dead.load_helpers()
            method.frame_contract.force_state_scope(read(SOURCE / "comparison.json"))
            for imported in (frame, solver, disk, bounds, method, method.member, method.bottom, method.accounting):
                path = Path(imported.__file__).resolve()
                require(path in pins and sha(path) == pins[path], "unexpected imported mechanics helper: " + str(path))
            with np.load(FRAME / "operators.npz", allow_pickle=False) as saved:
                operators = {name: saved[name].copy() for name in ("H", "D", "e", "W", "F")}
            require(operators["H"].shape == (1888, 1888) and operators["D"].shape == (1888, 300)
                    and operators["e"].shape == (1888, 12) and operators["W"].shape == (300, 12),
                    "physical operator census differs")
            report["gravity_column_checks"] = {}
            for name, tolerance in (("e", solver.GAP_TOL), ("W", 1e-12), ("F", 1e-9)):
                values = operators[name][:, ::2]
                require(np.isfinite(operators[name]).all(), "nonfinite load operator: " + name)
                differences = np.max(abs(values - values[:, :1]), axis=0)
                require(float(differences.max()) <= tolerance, "gravity columns exceed inherited guard: " + name)
                report["gravity_column_checks"][name] = {"maximum_absolute_difference_by_case": differences.tolist(),
                                                        "absolute_tolerance": tolerance, "relative_tolerance": 0.0,
                                                        "selected_column": 0, "values_modified": False}
            rows, source = read(FRAME / "row-identities.json"), read(SOURCE / "comparison.json")
            roles = Counter(r["ownership"]["role"] for r in rows)
            require(len(rows) == 1888 and roles["physical_bolt_outer_seat_tension"] == 104
                    and roles["non_qualifying_parametric_screw_withdrawal"] == 66, "global hardware row census differs")
            H, D, e, W, k, uni, normals, tangents, transform, footprints = frame.lump_floor(
                *[operators[name] for name in ("H", "D", "e", "W")], rows)
            require(len(normals) == 8 and footprints == source["floor_footprints"], "floor footprint scope differs")
            retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
            by_id = {}
            for i, row in enumerate(retained):
                by_id.setdefault(row["row_id"], []).append(i)
            pairs = [by_id[p["plane_id"]] for p in source["clearance_planes"]]
            require(len(pairs) == 88 and all(len(pair) == 2 and pair[1] == pair[0] + 1 for pair in pairs)
                    and all(retained[i]["ownership"]["role"] == "candidate_bolt_lateral_plane" for pair in pairs for i in pair),
                    "88 adjacent signed clearance pairs required")
            targets = np.array([i for pair in pairs for i in pair])
            gaps = np.array([p["relative_radial_gap_mm"] for p in source["clearance_planes"]])
            factor = report["dead_load_factor"]
            matrices = ((H + H.T) / 2, D, factor * e[:, 0], factor * W[:, 0], k, uni, normals, tangents)
            with np.load(SOURCE / "response.npz", allow_pickle=False) as saved:
                for gap_scale, suffix in ((0.0, "zero"), (1.0, "gap")):
                    tag = "permanent-only_" + suffix
                    seed = transform @ saved["a12-rear_" + suffix + "_raw_force_n"]
                    report["frame_solve"] = True
                    try:
                        f, q, a, audit, certificate = dead.solve_state(
                            solver, disk, bounds, matrices, targets, gaps, seed, gap_scale)
                    except ValueError as error:
                        trace, terminal = error.__traceback__, {}
                        while trace is not None:
                            if trace.tb_frame.f_code is solver.solve.__code__:
                                terminal = trace.tb_frame.f_locals
                            trace = trace.tb_next
                        responses.update({tag + "_unaccepted_" + name: terminal[name]
                                          for name in ("f", "q", "a") if name in terminal})
                        states.append({"case_id": "permanent-only", "state": tag, "gap_scale": gap_scale,
                                       "status": "STOP_UNACCEPTED_STATE", "exception_type": type(error).__name__,
                                       "terminal_exception": str(error), "audit": terminal.get("audit"), **FLAGS})
                        continue  # Still attempt exactly the other declared state.
                    raw = transform.T @ f
                    raw_states[tag] = raw
                    responses.update({tag + "_raw_force_n": raw, tag + "_lumped_q_mm": q, tag + "_rigid_coordinates": a})
                    states.append({"case_id": "permanent-only", "state": tag, "gap_scale": gap_scale,
                                   "status": "PASS_CONDITIONAL_WITH_BOUNDED_SEATING" if certificate else "PASS_CONDITIONAL_COUPLED_LAWS",
                                   "audit": audit, "fixed_force_clearance_certificate": certificate, **FLAGS})
            np.savez_compressed(output / "response.npz", **responses)
            report["states"] = states
            require(len(raw_states) == 2, "one or both declared frame states stopped; no member acceptance transferred")
            packet = proposal_records(method)
            # The intact-prism stability dimensions/old receiver restraints are
            # reused conditionally, never assigned to the six opening regions.
            write(output / "geometry.json", packet)
            with replay_adapter(dead, packet):
                traces, summaries, balances, arrays = dead.replay_members(method, operators, raw_states, pins)
            for body, record in packet["members"].items():
                arrays[body + "__cut_stations_mm"] = np.array(record["stations_mm"])
            coverage = section_coverage(packet, arrays, raw_states)
            openings = opening_register(packet, coverage)
            failures = exceptions(traces)
            for summary in summaries:
                summary["scope"] = "modified_six_bore_spine_intact_samples_only" if summary["member"] in SPINES else "unchanged_body_intact_samples_only"
            require(len(balances) == 88 and {s["member"] for s in summaries} == set(packet["members"]),
                    "44-body/two-state recovery incomplete")
            np.savez_compressed(output / "member-actions.npz", **arrays)
            with (output / "same-cut-states.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(traces[0]))
                writer.writeheader()
                writer.writerows(traces)
            write(output / "body-balances.json", balances)
            write(output / "section-coverage.json", coverage)
            write(output / "opening-register.json", openings)
            write(output / "exceptions.json", failures)
            authenticate(pins)
            report.update(status="COMPLETED_BOUNDED_NUMERICAL_COMPARISON_WITH_EXPLICIT_GAPS",
                          members=summaries, applicable_cut_trace_count=len(traces),
                          member_balance_count=len(balances), signed_cut_count=len(coverage),
                          non_applicable_signed_cut_count=sum(not r["normal_shear_torsion_reference_applicable"] for r in coverage),
                          exception_witness_count=len(failures),
                          named_opening_count=len(openings),
                          modified_spine_opening_count=12,
                          missing_basis=["All finite opening/profile resistances, concentrations and ligament transfer",
                                         "Four internal bridge bolts: permanent-state allocation and local compatibility",
                                         "Actual six-bore elastic stiffness and complete member/joint/hardware qualification",
                                         "Strict frame stability and whole-model register are separate parent work"],
                          source_sha256={str(p.relative_to(ROOT)): digest for p, digest in sorted(pins.items())})
            report["output_sha256"] = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
            write(output / "comparison.json", report)
            return report
    except Exception as error:
        # Preserve accepted/failed state arrays already written; never rerun a state.
        write(output / "stop.json", {**report, "status": "STOP_PERMANENT_COMPARISON",
                                    "states": states, "exception_type": type(error).__name__,
                                    "terminal_exception": str(error),
                                    "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}})
        raise


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
