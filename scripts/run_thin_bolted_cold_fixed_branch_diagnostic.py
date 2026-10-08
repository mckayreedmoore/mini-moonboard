"""Observe one cold fixed support branch through the frozen lean writer.

The prescribed mask uses the original bilateral initialization, incremental
Newton engine and fresh original force laws. Even a consistent diagnostic
coefficient vector exports no recovered actions or accepted field.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import run_thin_bolted_linear_timber_frame as lean
from scripts import thin_bolted_linear_timber_admission as linear
from scripts import thin_bolted_support_state_search as branch
from scripts.thin_bolted_timber_face_contact import merge_pins

frame = lean.frame
OWN = str(Path(__file__).resolve().relative_to(frame.ROOT))
OWN_TEST = "tests/test_run_thin_bolted_cold_fixed_branch_diagnostic.py"
LOADED_DRIVER_SHA256 = frame.sha(Path(__file__))
METHOD = "cold-prescribed-centroid-mask-original-fixed-branch-diagnostic"
SCHEMA = "thin_bolted_cold_fixed_branch_diagnostic/v1"
METHOD_SCHEMA = "thin_bolted_cold_fixed_branch_method/v1"
METHOD_RECEIPT = frame.PACKET / "cold-fixed-branch-method-v4.json"
FROZEN_BRANCH_SHA256 = "c162d296306a263be4e6769c4249abf6491512e8f7d9af323ab2e9b10b1018e8"
FROZEN_LINEAR_GATE_SHA256 = "e6dcb38947bea00ca583cd9a9e8d37a0cf0720d1f3ca97f7013ba9f2def0c676"


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def method_sources():
    """Read frozen sources only; do not prepare geometry or operators."""
    reused_receipts = [(linear.METHOD_RECEIPT, linear.METHOD_RECEIPT_SHA256),
                       (lean.reused.CERTIFICATE, lean.reused.CERTIFICATE_SHA),
                       (lean.reused.previous.CERTIFICATE, lean.reused.previous.CERTIFICATE_SHA)]
    receipt_pins = {}
    for path, digest in reused_receipts:
        if frame.sha(path) != digest:
            raise ValueError("preserve the frozen reused method input: " + str(path))
        receipt_pins = merge_pins(receipt_pins, json.loads(path.read_bytes())["source_sha256"],
                                 {str(path.relative_to(frame.ROOT)): digest})
    pins = merge_pins(branch.source_pins(), linear.source_pins(), lean.faces.source_pins(),
                      lean.common.shafts.source_pins(), lean.PANEL_OPERATOR_PINS, receipt_pins, {
        OWN: LOADED_DRIVER_SHA256, OWN_TEST: frame.sha(frame.ROOT / OWN_TEST),
        linear.DRIVER: linear.DRIVER_SHA256,
        "scripts/thin_bolted_support_state_search.py": FROZEN_BRANCH_SHA256,
        "scripts/thin_bolted_linear_timber_admission.py": FROZEN_LINEAR_GATE_SHA256,
        "scripts/run_thin_bolted_common_shaft_frame.py": "d2f62c4cc7f98c48dcde5cd9f05b94cd3515eb9314497051a6322a64f2d2a7e8",
        "scripts/run_thin_bolted_common_shaft_incremental.py": lean.REUSED_DRIVER_SHA256,
        "scripts/run_thin_bolted_finite_frame.py": lean.SAVED_PANEL_HELPER_SHA256,
    })
    for name, digest in pins.items():
        if frame.sha(frame.ROOT / name) != digest:
            raise ValueError("cold diagnostic source changed: " + name)
    return pins


def write_method_input_receipt(path: Path, *, validation: dict):
    """Issue exclusive input bytes after the parent records passed coupons."""
    if path.resolve() != METHOD_RECEIPT.resolve():
        raise ValueError("the distinct cold diagnostic method receipt path is required")
    if (validation.get("checks_pass") is not True
            or not isinstance(validation.get("command"), list)
            or not validation["command"]
            or type(validation.get("passed_tests")) is not int
            or validation["passed_tests"] <= 0):
        raise ValueError("explicit passed method validation required")
    receipt = {"schema": METHOD_SCHEMA, "method": METHOD, "method_checks_pass": True,
               "source_sha256": method_sources(), "validation": copy.deepcopy(validation),
               "diagnostic_only": True, "current_actions_or_acceptance_exported": False,
               "physical_laws_changed": False, "released": False, "release": frame.RELEASE}
    with path.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def source_pins(receipt_path: Path, expected_sha256: str):
    if receipt_path.resolve() != METHOD_RECEIPT.resolve():
        raise ValueError("the distinct cold diagnostic method receipt path is required")
    if frame.sha(receipt_path) != expected_sha256:
        raise ValueError("cold diagnostic method receipt differs from frozen input")
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get("schema") != METHOD_SCHEMA or receipt.get("method") != METHOD
            or receipt.get("method_checks_pass") is not True
            or receipt.get("diagnostic_only") is not True
            or receipt.get("current_actions_or_acceptance_exported") is not False
            or receipt.get("physical_laws_changed") is not False
            or receipt.get("released") is not False or receipt.get("release") != frame.RELEASE):
        raise ValueError("checked, unreleased diagnostic-only method input required")
    expected = method_sources()
    if any(receipt.get("source_sha256", {}).get(name) != digest for name, digest in expected.items()):
        raise ValueError("method input must bind loaded cold diagnostic and all frozen reuse sources")
    pins = merge_pins(expected, receipt["source_sha256"], {
        str(receipt_path.resolve().relative_to(frame.ROOT)): expected_sha256})
    for name, digest in pins.items():
        if frame.sha(frame.ROOT / name) != digest:
            raise ValueError("cold diagnostic input changed: " + name)
    return pins, receipt


def parse_mask(mask_id, hosts):
    prefix = "centroid-mask-"
    if (not isinstance(mask_id, str) or not mask_id.startswith(prefix)
            or len(mask_id[len(prefix):]) != len(hosts)
            or set(mask_id[len(prefix):]) - {"0", "1"}):
        raise ValueError("explicit centroid-mask bits in sorted original host order required")
    return {host for host, bit in zip(hosts, mask_id[len(prefix):], strict=True) if bit == "1"}


def verify_prepared_census(mapping, groups, contacts, tangents):
    """Check original prepared port identities before the bounded branch call."""
    kinds = Counter(row["kind"] for row in contacts)
    faces = [row for row in contacts if row["kind"] == "timber_face_contact"]
    hosts = branch._hosts(contacts, tangents)
    if (len(mapping["members"]) != 20 or len(hosts) != 8 or len(tangents) != 16
            or kinds["floor_normal"] != 32 or kinds["shaft_end_capture"] != 140
            or kinds["timber_face_contact"] != 272
            or len({(row["first"], row["second"]) for row in faces}) != 6
            or sum(row["kind"] == "common_shaft_bearing" for row in groups) != 308
            or sum(row["kind"] == "panel_screw" for row in groups) != 66
            or any(row["kind"] in {"fitting_bolt", "retained_bolt"} for row in groups)
            or len({row["id"] for row in [*groups, *contacts, *tangents]}) != len(groups) + len(contacts) + len(tangents)):
        raise ValueError("reviewed 20-timber/6-face/308-bearing/140-capture/32-normal/16-XY/66-screw census required")
    return {"timber_members": 20, "paired_timber_interfaces": 6,
            "paired_timber_compression_cells": 272, "radial_bearing_quadrature_ports": 308,
            "own_axial_end_captures": 140, "floor_normal_ports": 32, "centroid_xy_ports": 16,
            "panel_screw_axes": 66, "floor_hosts": hosts, "dofs": mapping["ndof"]}


def motion_markers(mapping, contacts, q):
    """Read linear reference kinematics; supply no deformation acceptance limit."""
    q = np.asarray(q, dtype=float)
    if (q.shape != (mapping["ndof"],) or not np.isfinite(q).all()
            or mapping["rotation_scale"] != frame.ROTATION_SCALE):
        raise ValueError("finite complete original scaled coordinate vector required")
    members = []
    for row in mapping["members"]:
        index = np.asarray(row["node_dof_indices"])
        if (index.ndim != 2 or index.shape[1] != 6 or len(index) < 2
                or not np.issubdtype(index.dtype, np.integer)
                or np.any(index < 0) or np.any(index >= len(q))):
            raise ValueError("original complete timber node coordinate indices required")
        values = q[index]
        members.append({"member": row["member"],
            "maximum_node_translation_norm_mm": float(np.linalg.norm(values[:, :3], axis=1).max()),
            "maximum_node_rotation_norm_rad": float(np.linalg.norm(values[:, 3:] / mapping["rotation_scale"], axis=1).max())})
    faces, floor = [], []
    for row in contacts:
        if row["kind"] == "timber_face_contact":
            point, normal = np.asarray(row["point_xyz_mm"]), np.asarray(row["direction_xyz"])
            relative = (linear.point_displacement(mapping, row["first"], point, q)
                        - linear.point_displacement(mapping, row["second"], point, q))
            tangential = relative - normal * float(normal @ relative)
            faces.append({"contact_id": row["id"], "first": row["first"], "second": row["second"],
                "reference_point_xyz_mm": point.tolist(),
                "relative_normal_motion_mm": float(normal @ relative),
                "relative_tangential_motion_norm_mm": float(np.linalg.norm(tangential))})
        elif row["kind"] == "floor_normal":
            displacement = linear.point_displacement(mapping, row["first"], row["point_xyz_mm"], q)
            floor.append({"contact_id": row["id"], "host": row["first"],
                "reference_point_xyz_mm": row["point_xyz_mm"],
                "reference_port_motion_xyz_mm": displacement.tolist()})
    maximum_slip = max((r["relative_tangential_motion_norm_mm"] for r in faces), default=0.)
    return {"basis": "original-linear-reference-point-kinematics", "timber_node_markers": members,
            "coordinate_map_canonical_sha256": canonical_sha(mapping),
            "diagnostic_q_canonical_sha256": canonical_sha(q.tolist()),
            "paired_face_reference_motion_markers": faces, "floor_reference_motion_markers": floor,
            "coverage": "mapped timber nodes and original timber-face/floor reference ports only",
            "maximum_timber_node_translation_norm_mm": max((r["maximum_node_translation_norm_mm"] for r in members), default=0.),
            "maximum_timber_node_rotation_norm_rad": max((r["maximum_node_rotation_norm_rad"] for r in members), default=0.),
            "maximum_face_tangential_motion_norm_mm": maximum_slip,
            "reference_face_cell_size_mm": 25., "maximum_face_tangential_motion_over_cell_size": maximum_slip / 25.,
            "deformation_limit_adopted": False, "small_motion_applicability_established": False,
            "current_contact_overlap_established": False, "diagnostic_q_is_a_physical_motion_prediction": False}


def cold_branch_diagnostic(K, applied, groups, contacts, tangents, max_iterations=300, *,
                           mask_id, warm_q=None, mapping=None):
    """Call one genuine frozen cold branch and independently recompute its laws."""
    if warm_q is not None:
        raise ValueError("cold branch rejects all external or preceding warm coefficients")
    if type(max_iterations) is not int or not 0 < max_iterations <= 300:
        raise ValueError("one through 300 original Newton iterations required")
    hosts = branch._hosts(contacts, tangents)
    enabled = parse_mask(mask_id, hosts)
    result = branch._fixed_branch(K, applied, groups, contacts, tangents, enabled, max_iterations, None)
    diagnostic = {"schema": SCHEMA, "method": METHOD, "host_order": hosts, "mask_id": mask_id,
        "enabled_centroid_xy_hosts": sorted(enabled), "disabled_centroid_xy_hosts": sorted(set(hosts) - enabled),
        "initialization": "original-frozen-bilateral-and-gap-correction", "warm_initialization": None,
        "old_q_or_forces_used": False, "fixed_branch_solver_converged": bool(result["converged"]),
        "fixed_branch_converged": False, "self_consistent": False,
        "fresh_original_gradient_inf_n": None, "floor_normal_force_n_by_host": None,
        "floor_normal_port_diagnostics": None, "demanded_enabled_centroid_xy_hosts": None,
        "diagnostic_q_canonical_sha256": None, "floor_activation_threshold_n": branch.FLOOR_ACTIVATION_THRESHOLD_N,
        "generalized_residual_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
        "normal_force_error_bound_established": False, "uniqueness_or_nonexistence_proven": False,
        "physical_laws_changed": False, "current_actions_or_acceptance_exported": False,
        "motion_applicability_diagnostics": None, "fixed_branch_termination": result["termination"]}
    q = result.get("q") if result["converged"] else result.get("diagnostic_last_q")
    energy = result.get("potential_energy_nmm")
    if q is not None:
        q = np.asarray(q, dtype=float)
        if q.shape != (K.shape[0],) or not np.isfinite(q).all():
            raise ValueError("fresh branch diagnostic must have complete finite coefficients")
        gradient, energy, _, _, normal, displacement = branch._fresh_fields(
            K, applied, groups, contacts, tangents, enabled, q)
        residual = float(abs(gradient).max())
        if not np.isfinite(residual) or not np.isfinite(normal).all() or not np.isfinite(energy):
            raise ValueError("fresh original residual, normals and energy must be finite")
        normals, ports = dict.fromkeys(hosts, 0.), []
        for row, force, motion in zip(contacts, normal, displacement, strict=True):
            if row["kind"] == "floor_normal":
                normals[row["first"]] += float(force)
                ports.append({"contact_id": row["id"], "host": row["first"],
                              "compression_n": float(force), "positive_closing_coordinate_mm": float(motion)})
        demanded = [host for host in hosts if normals[host] > branch.FLOOR_ACTIVATION_THRESHOLD_N]
        fixed = bool(result["converged"] and residual < frame.GENERALIZED_RESIDUAL_TOLERANCE_N)
        diagnostic.update(fresh_original_gradient_inf_n=residual, fixed_branch_converged=fixed,
            floor_normal_force_n_by_host=normals, floor_normal_port_diagnostics=ports,
            demanded_enabled_centroid_xy_hosts=demanded, self_consistent=fixed and set(demanded) == enabled,
            diagnostic_q_canonical_sha256=canonical_sha(q.tolist()),
            motion_applicability_diagnostics=motion_markers(mapping, contacts, q) if mapping is not None else None)
    return {"converged": False, "termination": "cold fixed-branch diagnostic only",
        "gradient_inf_n": diagnostic["fresh_original_gradient_inf_n"], "potential_energy_nmm": energy,
        "diagnostic_last_q": q, "diagnostic_last_q_is_a_converged_or_accepted_force_field": False,
        "cold_fixed_branch_diagnostic_v1": diagnostic, "numerical_step_strategy": METHOD,
        "physical_residual_uses_unmodified_laws": True, "original_force_tolerance_or_physical_laws_changed": False,
        "generalized_residual_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
        "floor_pattern_iterations": 1,
        **{key: result[key] for key in ("iteration_history", "accepted_numerical_steps", "rejected_numerical_trials",
                                      "maximum_transient_scaled_step_regularization")}}


def bind_cold_metadata(report, pins, command, receipt_path, receipt_sha, mask_id, census):
    report["parameters"].update({"support_mask_schedule_cold_branch_driver_sha256": LOADED_DRIVER_SHA256,
        "support_mask_schedule_cold_branch_method_receipt_sha256": receipt_sha,
        "support_mask_schedule_cold_branch_mask_id": mask_id,
        "support_mask_schedule_cold_branch_initialization": "original-frozen-bilateral-and-gap-correction"})
    report["source_sha256"] = merge_pins(report["source_sha256"], pins)
    report["cold_fixed_branch_execution"] = {"command": command, "loaded_driver_sha256": LOADED_DRIVER_SHA256,
        "loaded_fixed_branch_method_sha256": FROZEN_BRANCH_SHA256,
        "method_receipt_path": str(receipt_path.resolve().relative_to(frame.ROOT)),
        "method_receipt_sha256": receipt_sha, "mask_id": mask_id, "warm_initialization": None,
        "one_case_and_one_fixed_branch_only": True, "automatic_retries": 0,
        "nested_lean_execution_is_a_reused_internal_call": True,
        "diagnostic_only": True, "current_actions_or_acceptance_exported": False,
        "old_q_or_forces_used": False, "physical_laws_changed": False, "prepared_census": census}
    report["limits"].append("One cold prescribed-mask diagnostic supplies no recovered current actions or acceptance. Residual and mask consistency do not establish motion applicability, uniqueness, capacities or absence of another solution.")
    return report


def main():
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--cold-mask", required=True)
    parser.add_argument("--cold-method-receipt", type=Path, required=True)
    parser.add_argument("--cold-method-sha256", required=True)
    custom, remainder = parser.parse_known_args(arguments)
    parse_mask(custom.cold_mask, sorted(lean.common.finished.FLOOR_HOSTS))
    scope = argparse.ArgumentParser(add_help=False)
    scope.add_argument("--out", type=Path)
    scope.add_argument("--out-dir", type=Path)
    scope.add_argument("--cases", nargs="+", default=["a12-rear"])
    scope.add_argument("--warm-start")
    scope.add_argument("--warm-start-sha256")
    scope.add_argument("--newton-limit", type=int, default=300)
    scope.add_argument("--wall-seconds", type=float, default=1800.)
    scope.add_argument("--accessory", default="retained-original-top-hold")
    scope.add_argument("--fitting-section", default="gross")
    for flag, default in {"beam-size": 150., "shaft-segment": 25., "wood-bedding": 1.,
        "intervals": 8., "contact-edge": 70., "floor-tangent-stiffness": 100000.,
        "wood-bearing-foundation": 1000. / 38.1, "steel-bearing-foundation": 10000. / 5.55625,
        "end-capture-stiffness": 1000., "shaft-E": 200000., "shaft-nu": .3,
        "shaft-diameter-scale": 1., "screw-stiffness": 1000.}.items():
        scope.add_argument("--" + flag, type=float, default=default)
    selected, _ = scope.parse_known_args(remainder)
    if (selected.cases != ["a12-rear"] or selected.warm_start or selected.warm_start_sha256
            or not 0 < selected.newton_limit <= 300 or not np.isfinite(selected.wall_seconds)
            or not 0 < selected.wall_seconds <= 1800.):
        parser.error("one cold A12-rear branch, at most 300 Newton iterations and 1800 seconds required")
    expected = {"beam_size": 150., "shaft_segment": 25., "wood_bedding": 1., "intervals": 8.,
        "contact_edge": 70., "floor_tangent_stiffness": 100000., "wood_bearing_foundation": 1000. / 38.1,
        "steel_bearing_foundation": 10000. / 5.55625, "end_capture_stiffness": 1000.,
        "shaft_E": 200000., "shaft_nu": .3, "shaft_diameter_scale": 1., "screw_stiffness": 1000.}
    if (selected.accessory != "retained-original-top-hold" or selected.fitting_section != "gross"
            or any(not np.isfinite(getattr(selected, key)) or abs(getattr(selected, key) - value) > 1e-8
                   for key, value in expected.items())):
        parser.error("preserve the reviewed current preparation and physical scenario")
    if (selected.out is None) == (selected.out_dir is None):
        parser.error("one fresh explicit output path or output directory required")
    output = selected.out or selected.out_dir / "compatible-frame-a12-rear-v4.json"
    if output.exists() or output.with_name(output.name + ".interrupted.json").exists():
        parser.error("preserve previous fields and interruptions; choose a fresh output")
    pins, _ = source_pins(custom.cold_method_receipt, custom.cold_method_sha256)
    command = [sys.executable, "-m", "scripts.run_thin_bolted_cold_fixed_branch_diagnostic", *arguments]
    original_metadata = lean.common.bind_common_metadata
    original_preparation = lean.faces.prepare_linear_timber_faces
    prepared, census = {}, {}
    calls = 0

    def prepare(*args, **kwargs):
        if prepared:
            raise ValueError("one unchanged timber-face preparation required")
        result = original_preparation(*args, **kwargs)
        prepared.update(result)
        return result

    def solve(K, applied, groups, contacts, tangents, max_iterations=300, *, warm_q=None):
        nonlocal calls
        calls += 1
        if calls != 1 or not prepared:
            raise ValueError("one prepared cold branch per invocation required")
        if prepared["coordinate_map"]["ndof"] != K.shape[0]:
            raise ValueError("original coordinate map must match the complete prepared operator")
        census.update(verify_prepared_census(prepared["coordinate_map"], groups, contacts, tangents))
        return cold_branch_diagnostic(K, applied, groups, contacts, tangents, max_iterations,
            mask_id=custom.cold_mask, warm_q=warm_q, mapping=prepared["coordinate_map"])

    def metadata(report, system, inner_pins, inner_command):
        report = original_metadata(report, system, inner_pins, inner_command)
        expected_counts = {"timber_members": 20, "finite_fittings": 36, "flexible_panels": 6,
                           "physical_bolt_axes": 70, "panel_screw_axes": 66}
        if (len(system.assembly.geo["bodies"]) != 132 or len(system.shafts) != 70
                or any(report.get("counts", {}).get(key) != value for key, value in expected_counts.items())
                or report.get("usable_conditional_actions") is not False or report.get("release") != frame.RELEASE
                or report["response"].get("converged") is not False or "q" in report["response"]
                or any(report.get(key) for key in ("attachment_actions", "retained_bolt_actions",
                    "contact_actions", "connector_actions", *lean.common.COMMON_TABLES))):
            raise ValueError("unaccepted 132-body/70-shaft diagnostic without recovered actions required")
        census.update(structural_bodies=132, physical_shaft_bodies=70, finite_fittings=36, flexible_panels=6)
        if source_pins(custom.cold_method_receipt, custom.cold_method_sha256)[0] != pins:
            raise ValueError("cold diagnostic inputs changed during the branch")
        return bind_cold_metadata(report, pins, command, custom.cold_method_receipt,
                                  custom.cold_method_sha256, custom.cold_mask, census)

    def interruption(path, _inner_command, inner_prepared, panel_preparation, last):
        if source_pins(custom.cold_method_receipt, custom.cold_method_sha256)[0] != pins:
            raise ValueError("cold diagnostic inputs changed before interruption export")
        sidecar = path.with_name(path.name + ".interrupted.json")
        report = {"schema": "thin_bolted_cold_fixed_branch_interrupted/v1", "command": command,
            "source_sha256": merge_pins(pins, inner_prepared.get("source_sha256", {}),
                                        panel_preparation.get("source_sha256", {})),
            "mask_id": custom.cold_mask, "warm_initialization": None, "phase": last.get("phase"),
            "response": lean.failed_wall_response(last), "diagnostic_only": True,
            "usable_conditional_actions": False, "accepted_field_exported": False,
            "release": frame.RELEASE}
        with sidecar.open("x") as stream:
            stream.write(lean.common.finished.writer.dump(report))
        return sidecar

    old_argv = sys.argv.copy()
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(lean.faces, "prepare_linear_timber_faces", prepare),
              patch.object(lean.incremental, "compatible_contact_solve", solve),
              patch.object(lean.common, "bind_common_metadata", metadata),
              patch.object(lean, "write_interruption", interruption)):
            lean.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
