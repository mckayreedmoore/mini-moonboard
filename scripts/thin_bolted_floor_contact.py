"""Corner-local elastic sticking for the reviewed finished floor footprints.

This is a new support scenario, not unchanged centroid physics. Each actual
corner's XY penalty is present only when its own normal force exceeds 1e-7 N.
The frozen incremental solver is reused with virtual identifiers solely for
its outer support bookkeeping; operators and physical body identities stay
unchanged. A fixed support pattern has a conservative potential. Opening/
reclosing, history, a global energy minimum and uniqueness are not qualified.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import scipy
from scipy.sparse import csr_matrix, vstack

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as incremental

LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
TEST_PATH = frame.ROOT / "tests/test_thin_bolted_floor_contact.py"
LOADED_TEST_SHA256 = frame.sha(TEST_PATH)
INCREMENTAL_SHA = "3a3c794bb38352f1cc34d4c736a0812c14a53021d484549dc61d0a634cf83489"
CONTACT_PATH = frame.PACKET / "frame-contact-geometry-v4.json"
CONTACT_SHA = "e6c7ac4548b943bef4580b7c58efd67c11e29ed3335ae4036998a70c346986fc"
NORMAL_ACTIVATION_THRESHOLD_N = 1e-7
SUPPORT_BASIS = "finished-corner-local-rough-elastic-stick-v1"
METHOD_SOURCES = {
    "rough_sticking": {
        "url": "https://docs.software.vt.edu/abaqusv2025/English/SIMACAEITNRefMap/simaitn-c-friction.htm",
        "locator": "Preventing Slipping regardless of Contact Pressure; Shear Stress Versus Elastic Slip While Sticking",
        "scope": "Primary contact-method analogy only, not an Abaqus execution or material capacity. Rough sticking acts while normal constraints are active; finite penalty permits elastic slip. The source warns that opening rough contact can cause convergence difficulty. Its customary no-separation option is NOT adopted.",
    },
    "linear_solve": {
        "implementation": "frozen scripts.thin_bolted_incremental_step and thin_bolted_numerical_step; existing scipy.sparse.linalg.spsolve",
        "scope": "Existing source-pinned numerical step and tolerance reused; no new sparse-solver feature.",
    },
}


def source_pins():
    pins = {**incremental.source_pins(),
            "scripts/thin_bolted_floor_contact.py": LOADED_PRODUCER_SHA256,
            str(TEST_PATH.relative_to(frame.ROOT)): LOADED_TEST_SHA256,
            str(CONTACT_PATH.relative_to(frame.ROOT)): CONTACT_SHA}
    if pins["scripts/thin_bolted_incremental_step.py"] != INCREMENTAL_SHA:
        raise ValueError("frozen incremental solver differs")
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("corner support method or finished-footprint source differs")
    return pins


def corner_rows(assembly, contacts, foot_tangent_stiffness=100000.):
    """Two physical-host XY rows per existing normal, kfoot/four corners.

    The all-four-bearing translation stiffness equals the old centroid value;
    yaw restraint and rocking transfer change explicitly. No new floor point,
    body, degree of freedom, member, bolt or axis is introduced.
    """
    if not np.isfinite(foot_tangent_stiffness) or foot_tangent_stiffness <= 0.:
        raise ValueError("positive finite per-foot tangent stiffness required")
    normals = [row for row in contacts if row["kind"] == "floor_normal"]
    counts = Counter(row["first"] for row in normals)
    if not normals or any(count != 4 for count in counts.values()):
        raise ValueError("four actual normal corners per footprint required")
    if len({row["id"] for row in normals}) != len(normals):
        raise ValueError("unique floor normal identifiers required")
    result = []
    for row in normals:
        point = np.asarray(row["point_xyz_mm"], dtype=float)
        if (point.shape != (3,) or not np.isfinite(point).all() or row.get("second") != "floor"
                or not np.array_equal(row["direction_xyz"], [0., 0., 1.])):
            raise ValueError("finite actual corner and global-Z floor normal required")
        for component in (0, 1):
            direction = np.eye(3)[component]
            result.append({"id": row["id"] + f"/no-slip-{component}", "kind": "floor_tangent",
                           "first": row["first"], "physical_first": row["first"], "second": "floor",
                           "floor_support_id": row["id"], "normal_contact_id": row["id"],
                           "point_xyz_mm": point.tolist(), "direction_xyz": direction.tolist(),
                           "B": assembly.scalar_port(row["first"], point, direction),
                           "stiffness": foot_tangent_stiffness / counts[row["first"]],
                           "foot_tangent_stiffness_n_mm": foot_tangent_stiffness})
    return result


def _support_rows(contacts, tangents):
    normals = {row["id"]: row for row in contacts if row["kind"] == "floor_normal"}
    if len(normals) != sum(row["kind"] == "floor_normal" for row in contacts):
        raise ValueError("unique floor normal identifiers required")
    pairs = Counter()
    for tangent in tangents:
        support = tangent["floor_support_id"]
        normal = normals.get(support)
        if (normal is None or tangent["normal_contact_id"] != support
                or tangent["first"] != normal["first"] or tangent["physical_first"] != normal["first"]
                or not np.array_equal(tangent["point_xyz_mm"], normal["point_xyz_mm"])):
            raise ValueError("corner sticking must share its actual normal host and point")
        direction = tuple(tangent["direction_xyz"])
        if direction not in ((1., 0., 0.), (0., 1., 0.)):
            raise ValueError("floor tangent must be one global XY component")
        if not np.isfinite(tangent["stiffness"]) or tangent["stiffness"] <= 0.:
            raise ValueError("positive finite own-corner tangent stiffness required")
        pairs[support, direction] += 1
    if set(pairs) != {(key, direction) for key in normals
                      for direction in ((1., 0., 0.), (0., 1., 0.))} or any(n != 1 for n in pairs.values()):
        raise ValueError("exactly two distinct XY rows per floor corner required")
    return normals


def compatible_contact_solve(K, applied, groups, contacts, tangents, max_iterations=500, *, warm_q=None):
    """Reuse fixed-pattern solve; change only corner-local support bookkeeping."""
    source_pins()
    normals = _support_rows(contacts, tangents)
    virtual_contacts = [{**row, "first": row["id"]} if row["kind"] == "floor_normal" else row
                        for row in contacts]
    virtual_tangents = [{**row, "first": row["floor_support_id"]} for row in tangents]
    original_fields = incremental.ORIGINAL_FIELDS
    patterns, latest_linear, last_normals = [], None, {}

    def fields(linear, *args, **kwargs):
        nonlocal latest_linear, last_normals
        result = original_fields(linear, *args, **kwargs)
        if kwargs.get("tangent"):
            if linear is not latest_linear:
                disabled = {key for key, value in last_normals.items()
                            if value <= NORMAL_ACTIVATION_THRESHOLD_N}
                expected = K.copy()
                for row in tangents:
                    if row["floor_support_id"] not in disabled:
                        expected += row["stiffness"] * (row["B"].T @ row["B"])
                difference = (linear - expected).tocoo()
                if difference.nnz and abs(difference.data).max() > 1e-8:
                    raise ValueError("observed floor pattern differs from corner-local operators")
                patterns.append({"pattern_index": len(patterns),
                                 "enabled_corner_xy_support_ids": sorted(set(normals) - disabled)})
                latest_linear = linear
            last_normals = {row["id"]: float(force) for row, force in zip(contacts, result[4], strict=True)
                            if row["kind"] == "floor_normal"}
            patterns[-1].update(last_gradient_inf_n=float(abs(result[0]).max()),
                                last_floor_normal_force_n_by_corner=last_normals.copy())
        return result

    with patch.object(incremental, "ORIGINAL_FIELDS", fields):
        response = incremental.compatible_contact_solve(K, applied, groups, virtual_contacts, virtual_tangents,
                                                       max_iterations=max_iterations, warm_q=warm_q)
    response.update(floor_pattern_diagnostics=patterns, floor_contact_basis=SUPPORT_BASIS,
                    floor_normal_activation_threshold_n=NORMAL_ACTIVATION_THRESHOLD_N,
                    virtual_support_ids_are_physical_bodies=False,
                    floor_support_distribution_changed_from_centroid=True,
                    original_force_tolerance_or_physical_laws_changed=True,
                    physical_law_reference="new corner support scenario and preserved internal/normal laws",
                    original_connector_normal_laws_and_force_tolerance_changed=False,
                    conservative_potential_scope="one fixed corner-bearing pattern only",
                    active_pattern_uniqueness_or_global_energy_minimum_established=False,
                    near_activation_threshold_diagnostic_corner_ids=sorted(
                        key for key, value in last_normals.items()
                        if value <= frame.GENERALIZED_RESIDUAL_TOLERANCE_N),
                    near_threshold_diagnostic_is_a_normal_reaction_error_bound=False)
    # The reused solver's generic name described centroid hosts. Publish the
    # actual per-corner pattern separately and keep physical host names physical.
    if response["converged"]:
        disabled = response["nonbearing_no_slip_removed"]
        response["disabled_floor_support_ids"] = disabled
        response["nonbearing_no_slip_removed"] = sorted(
            host for host in {row["first"] for row in normals.values()}
            if all(key in disabled for key, row in normals.items() if row["first"] == host))
        _validate_final_pattern(response, contacts, tangents)
    source_pins()
    return response


def _validate_final_pattern(response, contacts, tangents):
    normals = _support_rows(contacts, tangents)
    disabled = set(response["disabled_floor_support_ids"])
    if not disabled <= set(normals):
        raise ValueError("disabled support is not an actual normal corner")
    forces = {row["id"]: float(value) for row, value in
              zip(contacts, response["normal_contact_force_n"], strict=True) if row["kind"] == "floor_normal"}
    if any(not np.isfinite(value) or value < 0. for value in forces.values()):
        raise ValueError("finite nonnegative own-corner normal required")
    if disabled != {key for key, value in forces.items() if value <= NORMAL_ACTIVATION_THRESHOLD_N}:
        raise ValueError("same-state own-corner normal and sticking activation differ")
    for key, normal in normals.items():
        physical = normal["stiffness"] * max(float((normal["B"] @ response["q"])[0]), 0.)
        if abs(physical - forces[key]) > 1e-7:
            raise ValueError("recovered corner normal differs from its unchanged compression law")
    return forces


def compatible_actions(recover, case, response, groups, contacts, tangents):
    """Wrap the frozen physical-body writer; retain all 64 XY rows, including 0."""
    if not response["converged"]:
        raise ValueError("failed corner pattern supplies no recovered actions")
    normals = _validate_final_pattern(response, contacts, tangents)
    disabled = set(response["disabled_floor_support_ids"])
    active = [row for row in tangents if row["floor_support_id"] not in disabled]
    result = recover(case, {**response, "nonbearing_no_slip_removed": []}, groups, contacts, active)
    by_id = {row["id"]: row for row in result["floor_actions"]}
    for tangent in tangents:
        support = tangent["floor_support_id"]
        enabled = support not in disabled
        if tangent["id"] not in by_id:
            row = {"id": tangent["id"], "kind": "floor_tangent", "first": tangent["physical_first"],
                   "second": "floor", "case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
                   "point_xyz_mm": tangent["point_xyz_mm"], "force_on_first_xyz_n": [0., 0., 0.],
                   "tangent_displacement_mm": float((tangent["B"] @ response["q"])[0]),
                   "penalty_stiffness_n_mm": tangent["stiffness"]}
            result["floor_actions"].append(row)
            by_id[tangent["id"]] = row
        by_id[tangent["id"]].update(floor_support_id=support, normal_contact_id=support,
                                    interaction_enabled=enabled, own_corner_normal_n=normals[support])
        if not enabled and np.any(by_id[tangent["id"]]["force_on_first_xyz_n"]):
            raise ValueError("inactive own-corner tangent force must be exactly zero")
    for support, normal in normals.items():
        by_id[support].update(floor_support_id=support, interaction_enabled=normal > NORMAL_ACTIVATION_THRESHOLD_N)
        contact = next(row for row in contacts if row["id"] == support)
        own_tangents = [row for row in tangents if row["floor_support_id"] == support]
        displacement = np.zeros(3)
        for tangent in own_tangents:
            displacement += np.asarray(tangent["direction_xyz"]) * float((tangent["B"] @ response["q"])[0])
        displacement[2] = -float((contact["B"] @ response["q"])[0])
        reference = np.array(contact["point_xyz_mm"])
        for row in [by_id[support], *[by_id[tangent["id"]] for tangent in own_tangents]]:
            row.update(reference_point_xyz_mm=reference.tolist(), current_point_xyz_mm=(reference + displacement).tolist(),
                       action_wrench_uses_reference_point_first_order=True,
                       current_point_is_first_order_kinematic_diagnostic=True,
                       moment_on_first_at_point_xyz_nmm=[0., 0., 0.])
    summary = result["floor_support_summary"]
    summary.pop("maximum_centroid_xy_penalty_motion_mm", None)
    summary.pop("maximum_centroid_tangent_component_n", None)
    summary.pop("centroid_xy_penalty_is_exact_distributed_no_slip", None)
    summary.update(floor_contact_basis=SUPPORT_BASIS,
                   maximum_active_corner_xy_penalty_motion_mm=max(
                       (abs(row["tangent_displacement_mm"]) for row in by_id.values()
                        if row["kind"] == "floor_tangent" and row["interaction_enabled"]), default=0.),
                   maximum_corner_tangent_component_n=max(
                       (float(np.linalg.norm(row["force_on_first_xyz_n"])) for row in by_id.values()
                        if row["kind"] == "floor_tangent"), default=0.),
                   finite_penalty_is_exact_no_slip=False, floor_no_slip_assumed=True, floor_no_slip_verified=False,
                   friction_or_anchor_capacity_established=False)
    return result


def rigid_block_fixture(corners, *, normal_stiffness=100., foot_tangent_stiffness=100.):
    """Small first-order rigid block only; q rotations retain 1000 mm scaling."""
    class Block:
        @staticmethod
        def scalar_port(host, point, direction):
            if host != "coupon-block":
                raise ValueError("coupon has one actual body")
            return csr_matrix(np.asarray(direction) @ np.c_[np.eye(3), -frame.cross_matrix(np.asarray(point)) / frame.ROTATION_SCALE])
    assembly = Block()
    contacts = [{"id": f"coupon-block/floor-{i}", "kind": "floor_normal", "first": "coupon-block",
                 "second": "floor", "point_xyz_mm": list(point), "direction_xyz": [0., 0., 1.],
                 "B": -assembly.scalar_port("coupon-block", point, [0., 0., 1.]), "stiffness": normal_stiffness}
                for i, point in enumerate(corners)]
    return contacts, corner_rows(assembly, contacts, foot_tangent_stiffness)


def rigid_block_recovery(assembly, case, response, groups, contacts, tangents):
    """Exercise frozen writer, which requires a nonempty screw summary.

    This zero-force self row supplies that summary only. It adds no port law,
    constraint, physical body or stiffness to the contact coupon.
    """
    summary = {"axis_id": "coupon-zero-screw-summary", "kind": "panel_screw",
               "first": "coupon-block", "second": "coupon-block", "point_xyz_mm": [0., 0., 0.],
               "basis": np.eye(3)}
    return frame.elastic_actions(assembly, case,
                                 {**response, "connector_local_force_n": [*response["connector_local_force_n"], np.zeros(3)]},
                                 [*groups, summary], contacts, tangents)


def method_coupons():
    """Known-answer contact/sticking controls; no candidate/global/native solve."""
    square = [[x, y, 0.] for x in (-50., 50.) for y in (-50., 50.)]
    contacts, tangents = rigid_block_fixture(square)
    zero = csr_matrix((6, 6))
    coupons = []
    for name, applied, expected in (
        ("fully_compressed_translation", [10., 20., -100., 0., 0., 0.], [.1, .2, -.25, 0., 0., 0.]),
        ("fully_compressed_yaw", [0., 0., -100., 0., 0., 2.], [0., 0., -.25, 0., 0., 4.]),
        ("free_block_edge_rocking_zero_normal_release", [5., 0., -100., 0., 5., 0.], [.1, 0., -.25, 0., 5., 0.]),
    ):
        response = compatible_contact_solve(zero, np.array(applied), [], contacts, tangents)
        if not response["converged"]:
            raise AssertionError(name + ": " + response["termination"])
        error = float(abs(response["q"] - expected).max())
        if error > 2e-7:
            raise AssertionError(name + ": known answer differs")
        coupons.append({"name": name, "maximum_coefficient_error_mm": error,
                        "gradient_inf_n": response["gradient_inf_n"],
                        "normal_force_n": response["normal_contact_force_n"].tolist(),
                        "disabled_floor_support_ids": response["disabled_floor_support_ids"]})
    mounted = csr_matrix(np.diag([2., 3., 4., 5., 6., 7.]))
    for name, vertical in (("zero_normal_releases_all_shear", 0.), ("open_foot_releases_all_shear", 8.)):
        applied = np.array([10., 12., vertical, 0., 0., 0.])
        response = compatible_contact_solve(mounted, applied, [], contacts, tangents)
        expected = np.array([5., 4., vertical / 4., 0., 0., 0.])
        if not response["converged"] or abs(response["q"] - expected).max() > 2e-7:
            raise AssertionError(name + ": mounted known answer differs")
        if len(response["disabled_floor_support_ids"]) != 4 or max(response["normal_contact_force_n"]) > 1e-12:
            raise AssertionError(name + ": unsupported floor reaction")
        coupons.append({"name": name, "gradient_inf_n": response["gradient_inf_n"],
                        "normal_force_n": response["normal_contact_force_n"].tolist(),
                        "coupon_external_springs_are_not_candidate_restraints": True})
    # Virtual identifiers cannot change an operator or its work dual. Compare
    # directly against the original physical-host fields and exact row energy.
    state = np.array([.1, -.2, -.4, .3, -.2, .5])
    applied = np.zeros(6)
    linear = sum((row["stiffness"] * (row["B"].T @ row["B"]) for row in tangents), zero.copy())
    C = vstack([row["B"] for row in contacts], format="csr")
    ck = np.array([row["stiffness"] for row in contacts])
    physical = incremental.ORIGINAL_FIELDS(linear, applied, [], C, ck, state, tangent=True)
    virtual_contacts = [{**row, "first": row["id"]} for row in contacts]
    virtual_C = vstack([row["B"] for row in virtual_contacts], format="csr")
    virtual = incremental.ORIGINAL_FIELDS(linear, applied, [], virtual_C, ck, state, tangent=True)
    errors = [float(abs(physical[0] - virtual[0]).max()), abs(physical[1] - virtual[1]),
              float(abs((physical[2] - virtual[2]).toarray()).max())]
    if max(errors) != 0.:
        raise AssertionError("virtual bookkeeping changed physical fields")
    coupons.append({"name": "physical_host_virtual_bookkeeping_energy_gradient_hessian_identity",
                    "gradient_energy_hessian_error": errors})
    # Exercise the exact frozen recovery path, not a replacement action writer.
    load = {"id": "coupon-edge-load", "body": "coupon-block", "point_xyz_mm": [50., 0., 0.],
            "force_xyz_n": [5., 0., -100.]}
    applied_wrench = frame.wrench(load["force_xyz_n"], load["point_xyz_mm"], np.zeros(3))
    rhs = applied_wrench * np.r_[np.ones(3), np.full(3, 1. / frame.ROTATION_SCALE)]
    response = compatible_contact_solve(zero, rhs, [], contacts, tangents)
    assembly = SimpleNamespace(geo={"bodies": [{"id": "coupon-block"}], "members": []}, members={})
    case = {"case_id": "coupon-edge", "accessory_placement": "coupon", "loads": [load],
            "applied_force_xyz_n": applied_wrench[:3].tolist(),
            "applied_moment_about_global_origin_xyz_nmm": applied_wrench[3:].tolist()}

    def recover(*args):
        return rigid_block_recovery(assembly, *args)

    actions = compatible_actions(recover, case, response, [], contacts, tangents)
    rows = actions["floor_actions"]
    inactive = [row for row in rows if row["kind"] == "floor_tangent" and not row["interaction_enabled"]]
    if (len(rows) != 12 or len(inactive) != 4
            or any(row["first"] != "coupon-block" for row in rows)
            or any(np.any(row["force_on_first_xyz_n"]) for row in inactive)
            or not actions["equilibrium_verification"]["all_body_and_global_checks_pass"]):
        raise AssertionError("physical-body recovery or zero-normal shear release differs")
    coupons.append({"name": "frozen_physical_body_recovery_inactive_rows_exact_zero",
                    "normal_rows": 4, "tangent_rows": 8, "disabled_zero_tangent_rows": len(inactive),
                    "maximum_body_force_norm_n": actions["equilibrium_verification"]["maximum_body_force_norm_n"],
                    "maximum_body_moment_norm_nmm": actions["equilibrium_verification"]["maximum_body_moment_about_reference_norm_nmm"],
                    "virtual_ids_exported_as_bodies": False})
    point, force = np.array([31., -23., 17.]), np.array([3., -7., 11.])
    port = np.c_[np.eye(3), -frame.cross_matrix(point) / frame.ROTATION_SCALE]
    generalized = port.T @ force
    exact = frame.wrench(force, point, np.zeros(3)) * np.r_[np.ones(3), np.full(3, 1. / frame.ROTATION_SCALE)]
    if abs(generalized - exact).max() > 1e-14:
        raise AssertionError("off-origin physical point force/torque dual differs")
    coupons.append({"name": "off_origin_point_force_wrench_and_virtual_work_dual",
                    "maximum_generalized_force_error_n": float(abs(generalized - exact).max())})
    return coupons


def main():
    output = frame.PACKET / "floor-corner-stick-method-coupons-v4.json"
    if output.exists():
        raise FileExistsError("preserve issued corner contact certificate")
    report = {"schema": "thin_bolted_floor_corner_method/v1", "candidate": "compact-floor-flush-thin-bolted-development",
              "source_sha256": source_pins(), "method": SUPPORT_BASIS, "method_sources": METHOD_SOURCES,
              "environment": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
              "command": [sys.executable, "-m", "scripts.thin_bolted_floor_contact"],
              "coupons": method_coupons(), "generalized_force_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
              "normal_activation_threshold_n": NORMAL_ACTIVATION_THRESHOLD_N,
              "floor_no_slip_assumed": True, "floor_no_slip_verified": False,
              "native_or_candidate_global_solves_performed": False,
              "limits": ["Four corner normal springs approximate bearing; actual distributed contact/stiffness remain unqualified.",
                         "Equal quarter-foot tangent stiffness preserves all-bearing translation only; yaw/rocking change.",
                         "Finite penalty permits elastic motion; no coefficient of friction or floor capacity is supplied.",
                         "Exactly zero or threshold-level normal disables all own-corner shear; this is the declared perfect-stick boundary convention.",
                         "The near-threshold comparison is a diagnostic, not an individual reaction error bound.",
                         "Only each fixed pattern has a conservative potential; history, global minimum, uniqueness, opening/reclosing and finite-motion applicability are unresolved.",
                         "Any repeated support pattern or unconverged physical residual supplies no accepted field."],
              "release": frame.RELEASE.copy()}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output.relative_to(frame.ROOT)), "sha256": frame.sha(output),
                      "coupons": len(report["coupons"]), "source_sha256": report["source_sha256"]}))


if __name__ == "__main__":
    main()
