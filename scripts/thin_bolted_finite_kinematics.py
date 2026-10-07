"""Local method diagnostics from admitted finite coordinates; no stiffness solve.

The frozen beam/fitting/shaft kinematic functions are called directly. A small
geometry facade supplies only their reference positions/triads, never a K or
material response. Timber section triads omitted from the finite map come from
the authenticated unchanged span JSON; no earlier displacement or force is selected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from scripts import thin_bolted_corotational_methods as corot
from scripts import thin_bolted_finite_frame as finite
from scripts import thin_bolted_finite_mechanics as mechanical
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_isotropic_shaft as isotropic
from scripts import thin_bolted_timber_common_shaft_checks as spans_method

LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
REUSED_SOURCES = {
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
    "scripts/thin_bolted_timber_resistance.py": "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    "scripts/thin_bolted_timber_demand_checks.py": "1be05e74563d2cc7a7ea5437aa4ff7217e62f8314f9fe011ff273d201f755e20",
    str(spans_method.SPAN_SOURCE.relative_to(frame.ROOT)): spans_method.SPAN_SOURCE_SHA,
}


def source_pins(additional=None):
    pins = {**finite.source_pins(), **REUSED_SOURCES,
            "scripts/thin_bolted_finite_kinematics.py": LOADED_PRODUCER_SHA256}
    for path, digest in (additional or {}).items():
        if path in pins and pins[path] != digest:
            raise ValueError("contradictory local kinematics source pin")
        pins[path] = digest
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("local kinematics source or reference geometry changed")
    return pins


@dataclass(frozen=True)
class KinematicGeometry:
    """Only attributes read by frozen deformation/measures functions."""

    reference_positions: np.ndarray
    reference_basis: np.ndarray | None = None

    def __post_init__(self):
        p = np.asarray(self.reference_positions, dtype=float)
        if p.shape != (2, 3) or not np.isfinite(p).all() or np.linalg.norm(p[1]-p[0]) <= 1e-8:
            raise ValueError("two distinct finite reference centers required")
        object.__setattr__(self, "reference_positions", p)
        if self.reference_basis is not None:
            basis = corot.check_rotation(self.reference_basis)
            if np.linalg.norm(basis[:, 0] - (p[1]-p[0])/self.length_mm) > 1e-8:
                raise ValueError("reference element triad and chord differ")
            object.__setattr__(self, "reference_basis", basis)

    @property
    def length_mm(self):
        return float(np.linalg.norm(self.reference_positions[1]-self.reference_positions[0]))


def world_state(q, indices, storage_basis):
    index = np.asarray(indices)
    if index.shape != (2, 6) or not np.issubdtype(index.dtype, np.integer) or np.min(index) < 0 or np.max(index) >= len(q):
        raise ValueError("two full mapped finite node states required")
    basis = corot.check_rotation(storage_basis)
    state = corot.vector(q[index.ravel()], 12).reshape(2, 6)
    state[:, :3] = state[:, :3] @ basis.T
    state[:, 3:] = state[:, 3:] @ basis.T
    return state.ravel()


def common_element_measures(geometry, state):
    state = corot.vector(state, 12).reshape(2, 6)
    p = geometry.reference_positions + state[:, :3]
    length = float(np.linalg.norm(p[1]-p[0]))
    if length <= 1e-8:
        raise ValueError("collapsed current chord has no applicable local beam chart")
    rotations = [corot.so3_exp(row[3:]/corot.ROTATION_SCALE) for row in state]
    relative = corot.so3_log(rotations[0].T @ rotations[1])
    result = {"reference_length_mm": geometry.length_mm, "current_length_mm": length,
        "current_centerline_endpoints_xyz_mm": p.tolist(),
        "chord_extension_mm": length-geometry.length_mm,
        "chord_extension_over_reference_length": length/geometry.length_mm-1.,
        "neighbor_relative_rotation_rad": float(np.linalg.norm(relative)),
        "neighbor_relative_rotation_vector_first_pose_reference_world_rad": relative.tolist(),
        "relative_rotation_over_reference_length_rad_mm": float(np.linalg.norm(relative)/geometry.length_mm),
        "adopted_deformation_acceptance_limit": None}
    if geometry.reference_basis is not None:
        directors = [r @ geometry.reference_basis[:, 0] for r in rotations]
        bending_turn = float(np.arctan2(np.linalg.norm(np.cross(*directors)), np.clip(directors[0] @ directors[1], -1., 1.)))
        result.update(axial_director_bending_turn_rad=bending_turn,
            constant_bending_arc_chord_shortening_comparison=(1.-np.sinc(bending_turn/(2*np.pi))),
            arc_comparison_is_recovered_physical_axial_strain=False)
    return result


def timber_element(positions, basis, state):
    geometry = KinematicGeometry(positions, basis)
    deformation, _unused_jacobian, metadata = corot.CorotationalBeam.deformation(geometry, state)
    rotations = metadata["local_rotations_rad"]
    mean = rotations.mean(axis=0)
    # In the local straight chord frame, transverse chord slopes are zero.
    # This averaged rotation mismatch is a kinematic marker, not the condensed
    # Timoshenko shear strain or a recovered shear stress/force.
    shear_marker = np.array([-mean[2], mean[1]])
    return {**common_element_measures(geometry, state),
        "method": "frozen small-local-deformation corotational Timoshenko timber",
        "local_rotations_in_moving_chord_frame_rad": rotations.tolist(),
        "maximum_local_rotation_rad": float(np.linalg.norm(rotations, axis=1).max()),
        "local_rotation_gradient_marker_rad_mm": ((rotations[1]-rotations[0])/geometry.length_mm).tolist(),
        "corotational_chord_extension_mm": float(deformation[6]),
        "average_local_rotation_shear_angle_marker_rad": shear_marker.tolist(),
        "shear_angle_marker_norm_rad": float(np.linalg.norm(shear_marker)),
        "shear_marker_is_condensed_Timoshenko_strain_or_stress": False,
        "projected_average_second_director_norm": float(metadata["projected_average_director_norm"]),
        "moving_frame_columns_xyz": metadata["frame_columns_world"].tolist(),
        "recorded_chart_guard_rad": float(np.pi/2-corot.BRANCH_MARGIN),
        "kinematic_method_applicability_or_mesh_convergence_established": False}


def shaft_element(positions, basis, state):
    geometry = KinematicGeometry(positions, basis)
    strain, _unused_jacobian, metadata = isotropic.IsotropicShaftBeam.measures(geometry, state)
    return {**common_element_measures(geometry, state),
        "method": "frozen midpoint isotropic director shaft finite extension",
        "midpoint_axial_strain_measure": float(strain[0]),
        "midpoint_shear_measures": strain[1:3].tolist(),
        "midpoint_shear_measure_norm": float(np.linalg.norm(strain[1:3])),
        "material_twist_bend1_bend2_curvature_rad_mm": strain[3:].tolist(),
        "material_bending_curvature_norm_rad_mm": float(np.linalg.norm(strain[4:])),
        "material_relative_rotation_vector_rad": metadata["material_relative_rotation_rad"].tolist(),
        "midpoint_material_triad_columns_xyz": metadata["midpoint_material_triad_world"].tolist(),
        "midpoint_chord_projection_per_reference_length": metadata["chord_projection_per_reference_length"].tolist(),
        "recorded_chart_guard_rad": float(np.pi/2-corot.BRANCH_MARGIN),
        "condensed_shear_measure_is_measured_continuum_shear_or_strength": False,
        "finite_extension_large_curvature_or_mesh_convergence_established": False}


def fitting_element(positions, state):
    geometry = KinematicGeometry(positions)
    deformation, _unused_jacobian = mechanical.ObjectiveCondensedFitting.deformation(geometry, state)
    reference_chord = geometry.reference_positions[1]-geometry.reference_positions[0]
    along = reference_chord/geometry.length_mm
    translation = deformation[6:9]
    transverse = translation-along*(along @ translation)
    return {**common_element_measures(geometry, state),
        "method": "frozen objective two-port condensed small-local-deformation fitting",
        "relative_port_translation_in_first_pose_reference_world_xyz_mm": translation.tolist(),
        "relative_flange_rotation_in_first_pose_rad": deformation[9:].tolist(),
        "maximum_local_rotation_rad": float(np.linalg.norm(deformation[9:])),
        "relative_port_translation_over_reference_chord_length": float(np.linalg.norm(translation)/geometry.length_mm),
        "transverse_port_translation_over_reference_chord_length": float(np.linalg.norm(transverse)/geometry.length_mm),
        "port_translation_marker_is_flat_leg_shear_strain": False,
        "individual_flat_leg_heel_curvature_recovered": False,
        "recorded_chart_guard_rad": float(np.pi/2-corot.BRANCH_MARGIN),
        "small_local_strip_heel_hole_applicability_established": False}


def evaluate_map(mapping, q, timber_basis_rows):
    """No energy, stiffness, capacity, CAD, assembly or equilibrium operation."""
    source_pins()
    q = corot.vector(q, mapping["ndof"])
    result = {"timber_elements": [], "shaft_elements": [], "fitting_condensed_elements": []}
    for body, row in mapping["mechanical_bodies"].items():
        centers = np.asarray(row["node_reference_centers_xyz_mm"], dtype=float)
        indices = np.asarray(row["node_dof_indices"])
        storage = np.asarray(row["storage_basis_columns_xyz"])
        if centers.ndim != 2 or centers.shape[1] != 3 or indices.shape != (len(centers), 6):
            raise ValueError("finite local method map shape differs")
        pairs = [(0, 1)] if row["kind"] == "fitting" else [(i, i+1) for i in range(len(centers)-1)]
        for i, j in pairs:
            state = world_state(q, indices[[i, j]], storage)
            positions = centers[[i, j]]
            if row["kind"] == "timber":
                basis = np.asarray(timber_basis_rows[body], dtype=float).T
                measured, table = timber_element(positions, basis, state), "timber_elements"
            elif row["kind"] == "shaft":
                measured, table = shaft_element(positions, storage, state), "shaft_elements"
            elif row["kind"] == "fitting":
                if len(centers) != 2 or row["flange_node_map"] != {"beam": 0, "post": 1}:
                    raise ValueError("one exact beam/post fitting pair required")
                measured, table = fitting_element(positions, state), "fitting_condensed_elements"
            else:
                raise ValueError("unknown finite mechanical method")
            result[table].append({"id": body+f"/element-{i}", "body": body, "node_pair": [i, j],
                                  "global_dof_indices": indices[[i, j]].tolist(), **measured})
    result["ranked_refinement_indicators"] = {}
    for table, keys in (("timber_elements", ("maximum_local_rotation_rad", "shear_angle_marker_norm_rad")),
                       ("shaft_elements", ("axial_director_bending_turn_rad", "midpoint_shear_measure_norm")),
                       ("fitting_condensed_elements", ("maximum_local_rotation_rad", "relative_port_translation_over_reference_chord_length"))):
        result["ranked_refinement_indicators"][table] = {
            key: [{"id": row["id"], "body": row["body"], "value": row[key]} for row in sorted(result[table], key=lambda row: row[key], reverse=True)[:5]]
            for key in keys}
    result.update(no_global_CAD_K_material_energy_or_equilibrium_solve=True,
        arbitrary_acceptance_thresholds=None, stability_or_strength_from_convergence=False,
        gross_vs_finished_cut_stiffness_bounded=False, release=dict(frame.RELEASE))
    source_pins()
    return result


def evaluate_admitted(field_path, admission_path, expected_admission_sha256, expected_gate_sha256):
    """Reuse exact byte-bound admission, then evaluate only local kinematics."""
    if frame.sha(admission_path) != expected_admission_sha256:
        raise ValueError("explicit immutable finite admission receipt differs")
    admission = json.loads(admission_path.read_text())
    gate = "scripts/thin_bolted_finite_state_audit.py"
    if (admission.get("schema") != "thin_bolted_independent_finite_admission/v1"
            or admission.get("independent_finite_current_support_load_and_equilibrium_checks_pass") is not True
            or admission.get("source_sha256", {}).get(gate) != expected_gate_sha256
            or frame.sha(frame.ROOT/gate) != expected_gate_sha256):
        raise ValueError("new frozen finite-current admission is required")
    payload = field_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != admission.get("field_sha256"):
        raise ValueError("finite field bytes differ from independent admission")
    field = json.loads(payload)
    for key in ("state_id", "case_id", "accessory_placement"):
        if field[key] != admission[key]:
            raise ValueError("finite diagnostic/admission identity differs")
    pins = source_pins(admission["source_sha256"])
    spans = spans_method.read_member_span_geometry()
    basis = {name: row["basis_grain_u_v_xyz"] for name, row in spans.items()}
    result = evaluate_map(field["finite_kinematic_map"], field["response"]["q"], basis)
    result.update(schema="thin_bolted_finite_local_kinematics/v1", field_sha256=hashlib.sha256(payload).hexdigest(),
        source_sha256=pins, admission_receipt_sha256=expected_admission_sha256,
        reference_timber_section_triads={"path": str(spans_method.SPAN_SOURCE.relative_to(frame.ROOT)),
            "sha256": spans_method.SPAN_SOURCE_SHA, "earlier_forces_or_displacements_selected": False},
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")})
    if field_path.read_bytes() != payload or frame.sha(admission_path) != expected_admission_sha256:
        raise ValueError("admitted source changed during local diagnostics")
    source_pins(pins)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued local finite diagnostics")
    result = evaluate_admitted(args.field, args.admission, args.admission_sha256, args.gate_sha256)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"path": str(args.out), "sha256": frame.sha(args.out), "state_id": result["state_id"]}))


if __name__ == "__main__":
    main()
