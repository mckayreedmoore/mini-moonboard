"""Admit a fresh support-search field using frozen JSON-only mechanics checks.

The actual runner, finite mask search and method receipt receive explicit
parent-frozen pins. Historical linear-timber admission is not invoked or
relabelled. No CAD, stiffness assembly, response solve or capacity is evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_linear_timber_admission as linear

common_export = linear.common_export
common, support, original = linear.common, linear.support, linear.proof_method.original
ROOT, PACKET = linear.ROOT, linear.PACKET
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = support.digest(Path(__file__))
SCHEMA = "thin_bolted_independent_support_search_admission/v1"
SUCCESS = "independent_support_search_face_source_map_law_and_equilibrium_checks_pass"
DRIVER = "scripts/run_thin_bolted_support_search_frame.py"
SEARCH = "scripts/thin_bolted_support_state_search.py"
METHOD = "nonrepeating-whole-foot-centroid-mask-search"
METHOD_RECEIPT = PACKET / "support-state-search-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_state_search_method/v1"
SEARCH_SCHEMA = "thin_bolted_support_state_search/v1"
LINEAR_GATE = "scripts/thin_bolted_linear_timber_admission.py"
LINEAR_GATE_SHA256 = "e6dcb38947bea00ca583cd9a9e8d37a0cf0720d1f3ca97f7013ba9f2def0c676"
SEARCH_TEST = "tests/test_thin_bolted_support_state_search.py"
IDENTITIES = linear.IDENTITIES
RELEASE_KEYS = {
    "candidate_accepted", "complete_joint_acceptance", "capacity_established",
    "fabrication_released", "structural_released", "climbing_released",
}
require, canonical_sha, merge_pins = linear.require, linear.canonical_sha, linear.merge_pins


def verify_pins(pins):
    for path, expected in pins.items():
        require(isinstance(path, str) and isinstance(expected, str)
                and len(expected) == 64 and support.digest(ROOT / path) == expected,
                "support-search admission source changed: " + str(path))


def require_unreleased(release):
    require(isinstance(release, dict) and set(release) == RELEASE_KEYS
            and all(value is False for value in release.values()),
            "all six explicit release flags must remain false")


def source_pins(*, driver_sha256, search_sha256, method_receipt_path, method_receipt_sha256):
    """Bind freshly loaded gate and producer sources before inspecting a field."""
    receipt_path = Path(method_receipt_path).resolve()
    require(receipt_path == METHOD_RECEIPT.resolve(), "the fresh support-search method receipt path is required")
    payload = receipt_path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == method_receipt_sha256,
            "support-search method receipt differs from its expected immutable bytes")
    receipt = json.loads(payload)
    require(receipt.get("schema") == METHOD_SCHEMA and receipt.get("method_checks_pass") is True
            and receipt.get("released") is False, "checked, unreleased support-search method receipt required")
    require_unreleased(receipt.get("release"))
    producer_pins = {DRIVER: driver_sha256, SEARCH: search_sha256, linear.DRIVER: linear.DRIVER_SHA256}
    require(all(receipt.get("source_sha256", {}).get(path) == sha for path, sha in producer_pins.items())
            and SEARCH_TEST in receipt.get("source_sha256", {}),
            "method receipt must bind the fresh runner, search, method tests and frozen reused driver")
    pins = merge_pins(linear.source_pins(), receipt["source_sha256"], producer_pins, {
        OWN: LOADED_PRODUCER_SHA256, LINEAR_GATE: LINEAR_GATE_SHA256,
        linear.METHOD: linear.METHOD_SHA256,
        str(receipt_path.relative_to(ROOT)): method_receipt_sha256,
    })
    verify_pins(pins)
    return pins


def verify_execution(field, *, driver_sha256, search_sha256, method_receipt_path, method_receipt_sha256):
    """Authenticate the actual command separately from reused internal calls."""
    execution = field.get("support_state_search_execution", {})
    command = execution.get("command")
    require(isinstance(command, list) and len(command) >= 3 and all(isinstance(v, str) and v for v in command)
            and command[1:3] == ["-m", "scripts.run_thin_bolted_support_search_frame"],
            "the actual fresh support-search execution module is required")
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
    parser.add_argument("--support-mask-budget", type=int, default=64)
    parser.add_argument("--support-method-receipt", type=Path)
    parser.add_argument("--support-method-sha256")
    parser.add_argument("--cases", nargs="+", default=["a12-rear"])
    parser.add_argument("--accessory", default="retained-original-top-hold")
    parser.add_argument("--warm-start")
    parser.add_argument("--warm-start-sha256")
    parser.add_argument("--wood-bedding", type=float, default=1.)
    parser.add_argument("--wall-seconds", type=float, default=1800.)
    parser.add_argument("--newton-limit", type=int, default=300)
    parser.add_argument("--intervals", type=int, default=8)
    parser.add_argument("--contact-edge", type=float, default=70.)
    parser.add_argument("--beam-size", type=float, default=150.)
    parser.add_argument("--shaft-segment", type=float, default=25.)
    parser.add_argument("--shaft-E", type=float, default=200000.)
    parser.add_argument("--shaft-nu", type=float, default=.3)
    parser.add_argument("--shaft-diameter-scale", type=float, default=1.)
    parser.add_argument("--wood-bearing-foundation", type=float, default=1000. / 38.1)
    parser.add_argument("--steel-bearing-foundation", type=float, default=10000. / 5.55625)
    parser.add_argument("--end-capture-stiffness", type=float, default=1000.)
    parser.add_argument("--floor-tangent-stiffness", type=float, default=100000.)
    parser.add_argument("--screw-stiffness", type=float, default=1000.)
    parser.add_argument("--bolt-stiffness", type=float, default=1000.)
    parser.add_argument("--clearance", type=float, default=1.5875)
    parser.add_argument("--fitting-section", default="gross")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path)
    try:
        args, remainder = parser.parse_known_args(command[3:])
    except (argparse.ArgumentError, SystemExit) as exc:
        raise ValueError("invalid fresh support-search command arguments") from exc
    receipt_path = Path(method_receipt_path).resolve()
    relative = str(receipt_path.relative_to(ROOT))
    require(args.support_method_receipt is not None
            and (ROOT / args.support_method_receipt).resolve() == receipt_path
            and args.support_method_sha256 == method_receipt_sha256,
            "actual command must bind the expected support-search receipt path and SHA")
    budget = execution.get("mask_budget")
    require(type(budget) is int and 1 <= budget <= 256 and args.support_mask_budget == budget,
            "actual command and finite support-search mask budget differ")
    require(not remainder and args.cases == ["a12-rear"] and field["case_id"] == "a12-rear"
            and args.accessory == field["accessory_placement"] == "retained-original-top-hold"
            and args.warm_start is None and args.warm_start_sha256 is None
            and 0. < args.wall_seconds <= 1800. and 1 <= args.newton_limit <= 300
            and args.bolt_stiffness == 1000. and args.clearance == 1.5875
            and (args.out is None) != (args.out_dir is None),
            "actual command must retain one A12-rear case, original initialization and bounded reviewed scope")
    require(execution.get("loaded_driver_sha256") == driver_sha256
            and execution.get("loaded_method_sha256") == search_sha256
            and execution.get("method_receipt_path") == relative
            and execution.get("method_receipt_sha256") == method_receipt_sha256
            and execution.get("warm_initialization") is None
            and execution.get("one_case_per_invocation") is True
            and execution.get("frozen_floor_law_reused") is True
            and execution.get("old_forces_or_acceptance_transferred") is False
            and execution.get("new_solver_framework") is False
            and execution.get("nested_lean_execution_is_a_reused_internal_call") is True,
            "fresh loaded producers and unchanged-law execution provenance required")
    params = field["parameters"]
    expected = {"support_state_search_driver_sha256": driver_sha256,
                "support_state_search_method_sha256": search_sha256,
                "support_state_search_method_receipt_sha256": method_receipt_sha256,
                "support_state_search_mask_budget": budget,
                "linear_timber_frame_driver_sha256": linear.DRIVER_SHA256,
                "linear_timber_face_contact_producer_sha256": linear.METHOD_SHA256,
                "linear_timber_face_contact_bedding_n_mm3": 1., "beam_size_mm": 150.,
                "shaft_max_segment_mm": 25., "panel_intervals": 8, "foundation_port_cell_mm": 70.,
                "floor_corner_contact_n_mm": 25000., "floor_no_slip_xy_penalty_n_mm": 100000.,
                "shaft_steel_E_mpa": 200000., "shaft_steel_nu": .3, "shaft_diameter_scale": 1.,
                "end_capture_stiffness_n_mm": 1000., "Hillman_axial_lateral_stiffness_n_mm": 1000.,
                "fitting_section": "gross", "lean_case_wall_time_limit_seconds": args.wall_seconds,
                "numerical_newton_iteration_limit_per_floor_pattern": args.newton_limit}
    require(all(params.get(key) == value for key, value in expected.items()),
            "reviewed support-search parameters or frozen linear-face producers differ")
    command_parameters = {
        "linear_timber_face_contact_bedding_n_mm3": args.wood_bedding, "beam_size_mm": args.beam_size,
        "shaft_max_segment_mm": args.shaft_segment, "panel_intervals": args.intervals,
        "foundation_port_cell_mm": args.contact_edge, "floor_no_slip_xy_penalty_n_mm": args.floor_tangent_stiffness,
        "shaft_steel_E_mpa": args.shaft_E, "shaft_steel_nu": args.shaft_nu,
        "shaft_diameter_scale": args.shaft_diameter_scale, "end_capture_stiffness_n_mm": args.end_capture_stiffness,
        "Hillman_axial_lateral_stiffness_n_mm": args.screw_stiffness, "fitting_section": args.fitting_section,
        "wood_radial_foundation_n_mm2": args.wood_bearing_foundation,
        "plate_radial_foundation_n_mm2": args.steel_bearing_foundation,
    }
    require(all(params.get(key) == value for key, value in command_parameters.items()),
            "actual support-search command differs from serialized physical parameters")
    require(abs(support.finite_scalar(params["wood_radial_foundation_n_mm2"]) - 1000. / 38.1) <= 1e-8
            and abs(support.finite_scalar(params["plate_radial_foundation_n_mm2"]) - 10000. / 5.55625) <= 1e-8,
            "reviewed radial foundation scenario required")
    return execution


def host_mask(value, hosts, message):
    require(isinstance(value, list) and all(isinstance(host, str) for host in value) and len(value) == len(set(value))
            and value == sorted(value) and set(value) <= set(hosts), message)
    return set(value)


def normal_resultants(value, hosts):
    require(isinstance(value, dict) and set(value) == set(hosts), "all eight whole-foot normal resultants required")
    result = {host: support.finite_scalar(value[host]) for host in hosts}
    require(all(v >= 0. for v in result.values()), "whole-foot normal resultants must be nonnegative")
    return result


def verify_support_search(field):
    """Replay finite-mask bookkeeping against the final exported32 normals."""
    response = field["response"]
    tolerance = support.finite_scalar(response["generalized_residual_tolerance_n"])
    residual = support.finite_scalar(response["gradient_inf_n"])
    require(response.get("converged") is True and field.get("usable_conditional_actions") is True
            and response.get("physical_residual_uses_unmodified_laws") is True
            and response.get("wall_time_limit_reached", False) is False
            and tolerance == 1e-5 and 0. <= residual <= tolerance and "q" in response
            and "diagnostic_last_q" not in response,
            "accepted fresh original-law coefficients and residual at most1e-5 required")
    search = response.get("support_state_search_v1", {})
    hosts = sorted(support.FLOOR_HOSTS)
    require(search.get("schema") == SEARCH_SCHEMA and search.get("method") == METHOD
            and search.get("host_order") == hosts and search.get("total_possible_masks") == 256
            and search.get("floor_activation_threshold_n") == 1e-7
            and search.get("old_field_initialization_used") is False
            and search.get("physical_laws_changed") is False and search.get("no_fixed_point_proven") is False
            and search.get("near_threshold_diagnostic_is_a_normal_force_error_bound") is False
            and search.get("body_global_and_export_admission_required") is True,
            "fresh finite support-search method and unchanged whole-foot law required")
    budget = search.get("mask_budget")
    rows = search.get("tested_masks")
    require(type(budget) is int and budget == field["parameters"]["support_state_search_mask_budget"]
            and 1 <= budget <= 256 and isinstance(rows, list) and 1 <= len(rows) <= budget,
            "bounded nonempty support-search history required")
    seen = set()
    for index, row in enumerate(rows):
        enabled = host_mask(row["enabled_centroid_xy_hosts"], hosts, "unique ordered enabled support hosts required")
        disabled = host_mask(row["disabled_centroid_xy_hosts"], hosts, "unique ordered disabled support hosts required")
        mask = tuple(host in enabled for host in hosts)
        require(row["pattern_index"] == index and disabled == set(hosts) - enabled and mask not in seen,
                "support-search masks must be complete and never repeat")
        require(row.get("mask_id") == "centroid-mask-" + "".join("1" if host in enabled else "0" for host in hosts)
                and (index != 0 or enabled == set(hosts))
                and row.get("initialization_from_previous_fresh_branch_only") is (
                    index != 0 and rows[index - 1].get("fresh_original_gradient_inf_n") is not None),
                "support search must start with all hosts and use fresh preceding-branch initialization")
        seen.add(mask)
        if row.get("fixed_branch_converged") is True:
            normal = normal_resultants(row["floor_normal_force_n_by_host"], hosts)
            demanded = {host for host, force in normal.items() if force > 1e-7}
            recorded = host_mask(row["demanded_enabled_centroid_xy_hosts"], hosts, "complete demanded mask required")
            value = support.finite_scalar(row["fresh_original_gradient_inf_n"])
            require(0. <= value <= tolerance and recorded == demanded
                    and row.get("self_consistent") is (enabled == demanded),
                    "converged support branch must use its own fresh residual and whole-foot mask")
            require(row.get("disabled_xy_force_exactly_zero") is True
                    and row.get("disabled_xy_force_n_by_host") == {host: [0., 0.] for host in sorted(disabled)},
                    "disabled centroid support must have zero reactions")
        else:
            require(row.get("fixed_branch_converged") is False and row.get("self_consistent") is False,
                    "an unresolved branch cannot be a self-consistent support state")
    index = search.get("accepted_pattern_index")
    require(type(index) is int and index == len(rows) - 1, "accepted support pattern must be the final fresh branch")
    row = rows[index]
    enabled = host_mask(search.get("accepted_enabled_centroid_xy_hosts"), hosts, "accepted enabled mask required")
    disabled = host_mask(search.get("accepted_disabled_centroid_xy_hosts"), hosts, "accepted disabled mask required")
    require(row.get("fixed_branch_converged") is True and row.get("self_consistent") is True
            and enabled == set(row["enabled_centroid_xy_hosts"]) and disabled == set(hosts) - enabled
            and host_mask(response["nonbearing_no_slip_removed"], hosts, "complete final disabled mask required") == disabled
            and sum(item.get("self_consistent") is True for item in rows) == 1
            and support.finite_scalar(row["fresh_original_gradient_inf_n"]) == residual,
            "accepted support mask and residual must come from the final fresh branch")
    final_normals = dict.fromkeys(hosts, 0.)
    normals = [row for row in field["floor_actions"] if row["kind"] == "floor_normal"]
    require(len(normals) == 32 and {row["id"] for row in normals} == {
        host + f"/floor-{corner}" for host in hosts for corner in range(4)},
            "all32 unique final normal ports including zero required")
    for normal in normals:
        require(normal["first"] in final_normals, "foreign final floor-normal host")
        force = support.finite_scalar(normal["compression_n"])
        require(force >= 0., "final floor compression must be nonnegative")
        final_normals[normal["first"]] += force
    accepted_normals = normal_resultants(row["floor_normal_force_n_by_host"], hosts)
    original.close(list(final_normals.values()), list(accepted_normals.values()), 1e-8,
                   "accepted branch normal resultants differ from final exported ports")
    require(enabled == {host for host, force in final_normals.items() if force > 1e-7},
            "accepted centroid mask must match its own final whole-foot normal bearing")
    q = original.array(response["q"], (field["counts"]["dofs"],))
    mask_id = "centroid-mask-" + "".join("1" if host in enabled else "0" for host in hosts)
    require(search.get("final_q_canonical_sha256") == canonical_sha(q.tolist())
            and search.get("final_mask_id") == mask_id
            and search.get("all_masks_visited") is (len(rows) == 256)
            and search.get("complete_enumeration") is (len(rows) == 256 and all(
                item["fixed_branch_converged"] for item in rows)),
            "accepted final q, mask identity and enumeration status must agree")
    return {"accepted_pattern_index": index, "tested_mask_count": len(rows), "final_mask_id": mask_id,
            "final_q_canonical_sha256": canonical_sha(q.tolist()), "bearing_hosts": sorted(enabled),
            "gradient_inf_n": residual, "generalized_residual_tolerance_n": tolerance,
            "floor_activation_threshold_n": 1e-7, "final_whole_foot_normal_force_n_by_host": final_normals,
            "independent_numerical_gradient_reassembly": False}


def verify_floor_q_laws(field, mapping, q):
    """Replay first-order floor ports directly from the admitted timber map."""
    for row in field["floor_actions"]:
        displacement = linear.point_displacement(mapping, row["first"], row["point_xyz_mm"], q)
        if row["kind"] == "floor_normal":
            compression = 25000. * max(-float(displacement[2]), 0.)
            require(abs(support.finite_scalar(row["compression_n"]) - compression) <= 1e-6,
                    "final floor normal differs from the original linear q compression law")
            original.close(row["force_on_first_xyz_n"], [0., 0., compression], 1e-6,
                           "final floor normal force differs from final q")
        else:
            require(row["kind"] == "floor_tangent" and row["id"] in {
                row["first"] + "/no-slip-0", row["first"] + "/no-slip-1"}, "foreign floor q path")
            component = int(row["id"][-1])
            require(abs(support.finite_scalar(row["tangent_displacement_mm"]) - displacement[component]) <= 1e-8
                    and row["penalty_stiffness_n_mm"] == 100000.,
                    "final centroid displacement or stiffness differs from original q")
            original.close(row["force_on_first_xyz_n"], -100000. * displacement[component] * np.eye(3)[component],
                           1e-6, "final centroid reaction differs from original q")
    return {"original_linear_q_normal_and_centroid_laws_replayed": True,
            "actual_floor_or_physical_stiffness_verified": False}


def audit_support_search_state(path_or_bytes, *, driver_sha256, search_sha256,
                               method_receipt_path, method_receipt_sha256):
    """Issue an immutable-byte receipt only after fresh and unchanged checks."""
    require(isinstance(path_or_bytes, (bytes, str, Path)), "immutable field bytes or one source path required")
    args = {"driver_sha256": driver_sha256, "search_sha256": search_sha256,
            "method_receipt_path": method_receipt_path, "method_receipt_sha256": method_receipt_sha256}
    pins = source_pins(**args)
    path = None if isinstance(path_or_bytes, bytes) else Path(path_or_bytes)
    payload = path.read_bytes() if path is not None else path_or_bytes
    field = json.loads(payload)
    before = canonical_sha(field)
    require(field.get("schema") == "thin_bolted_common_shaft_frame/v1", "fresh common-shaft field schema required")
    require_unreleased(field.get("release"))
    identity = {key: field[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field["state_id"] == "thin-v4-" + canonical_sha(identity)[:24], "fresh support-search state identity differs")
    execution = verify_execution(field, **args)
    search = verify_support_search(field)
    _, cache, _, layout, _, _, base_pins = common.read_sources()
    proof_payload = linear.proof_method.PROOF.read_bytes()
    require(hashlib.sha256(proof_payload).hexdigest() == linear.proof_method.PROOF_SHA256,
            "finished paired-face geometry proof changed")
    proof = json.loads(proof_payload)
    pins = merge_pins(pins, base_pins, proof["source_sha256"], {
        str(linear.proof_method.PROOF.relative_to(ROOT)): linear.proof_method.PROOF_SHA256,
    }, field["source_sha256"])
    verify_pins(pins)
    required = merge_pins(base_pins, proof["source_sha256"], {
        DRIVER: driver_sha256, SEARCH: search_sha256, linear.DRIVER: linear.DRIVER_SHA256,
        linear.METHOD: linear.METHOD_SHA256,
        str(Path(method_receipt_path).resolve().relative_to(ROOT)): method_receipt_sha256,
        str(linear.proof_method.PROOF.relative_to(ROOT)): linear.proof_method.PROOF_SHA256,
        str(linear.panel_sources.OPERATORS.relative_to(ROOT)): linear.panel_sources.OPERATORS_SHA,
        str(linear.panel_sources.coupled.DATUMS.relative_to(ROOT)): linear.panel_sources.coupled.DATUMS_SHA,
    })
    require(all(field["source_sha256"].get(name) == sha for name, sha in required.items()),
            "fresh field omits authenticated producers, face, floor or panel sources")
    inventory = linear.proof_method.verify_patch_inventory(proof, cache, layout)
    mapping, q = linear.verify_timber_map(field, cache, linear.spans.read_member_span_geometry())
    floor = verify_floor_q_laws(field, mapping, q)
    faces = linear.verify_face_actions(field, proof, mapping, q)
    census = linear.verify_action_census(field, linear.panel_contact_sources())
    require(not field.get("attachment_actions") and not field.get("retained_bolt_actions"), "old bolt proxies cannot survive")
    unchanged = common_export.audit_common_shaft_state(field)
    require(unchanged[common_export.ACCEPTANCE_KEY] is True, "unchanged common132-body/support/load audit failed")
    pins = merge_pins(pins, unchanged["source_sha256"])
    verify_pins(pins)
    require(source_pins(**args).items() <= pins.items(), "fresh source pins changed during admission")
    require(canonical_sha(field) == before, "parsed field changed during fresh admission")
    raw_sha = hashlib.sha256(payload).hexdigest()
    if path is not None:
        require(support.digest(path) == raw_sha, "raw field changed during fresh admission")
    return {"schema": SCHEMA, SUCCESS: True, **{key: field[key] for key in IDENTITIES},
            "field_sha256": raw_sha, "field_canonical_sha256": before, "source_sha256": pins,
            "actual_support_search_execution": execution, "support_search_checks": search,
            "floor_q_law_checks": floor, "linear_timber_map_checks_pass": True,
            "linear_timber_face_checks": faces, "timber_contact_geometry": inventory,
            "complete_action_census": census, "independent_common_shaft_audit": unchanged,
            "native_CAD_K_or_response_execution": False,
            "small_motion_applicability_physical_bounds_complete_capacity_or_release_established": False,
            "release": {key: False for key in field["release"]}}
