"""Local chord/rotation known answers only; no candidate evaluation."""

import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_kinematics as method


def main():
    positions = np.array([[0., 0., 0.], [100., 0., 0.]])
    angle = .2
    state = np.zeros((2, 6)); state[:, 5] = [-500*angle, 500*angle]
    state[1, 0] = 100*(np.sin(angle/2)/(angle/2)-1)
    shaft = method.shaft_element(positions, np.eye(3), state.ravel())
    timber = method.timber_element(positions, np.eye(3), state.ravel())
    hand_chord_strain = np.sin(angle/2)/(angle/2)-1
    if (abs(shaft["midpoint_axial_strain_measure"]-hand_chord_strain) > 1e-14
            or abs(timber["chord_extension_over_reference_length"]-hand_chord_strain) > 1e-14
            or abs(shaft["material_bending_curvature_norm_rad_mm"]-angle/100) > 1e-14):
        raise ValueError("local circular-arc chord coupon failed")
    shear_state = np.zeros(12); shear_state[6:9] = [2., 3., -4.]
    shear = method.shaft_element(positions, np.eye(3), shear_state)
    rotation = method.corot.so3_exp([.5, -.7, .6])
    rigid_q = np.zeros((2, 6))
    rigid_q[:, :3] = positions @ (rotation-np.eye(3)).T + [7., -11., 13.]
    rigid_q[:, 3:] = 1000*method.corot.so3_log(rotation)
    rigid = {"timber": method.timber_element(positions, np.eye(3), rigid_q.ravel()),
             "shaft": method.shaft_element(positions, np.eye(3), rigid_q.ravel()),
             "fitting": method.fitting_element(positions, rigid_q.ravel())}
    pins = method.source_pins()
    for source in [Path(__file__).resolve(), method.frame.ROOT/"tests/test_thin_bolted_finite_kinematics.py"]:
        pins[str(source.relative_to(method.frame.ROOT))] = method.frame.sha(source)
    result = {
        "schema": "thin_bolted_finite_kinematics_method_coupons/v1", "source_sha256": pins,
        "command": "OPENBLAS_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/finite-kinematics-method-v4.py",
        "circular_arc_coupon": {"element_reference_length_mm": 100., "relative_director_turn_rad": angle,
            "hand_chord_extension_over_reference_length": float(hand_chord_strain),
            "observed_shaft_midpoint_axial_measure": shaft["midpoint_axial_strain_measure"],
            "observed_timber_chord_extension_over_reference_length": timber["chord_extension_over_reference_length"],
            "observed_shaft_bending_curvature_rad_mm": shaft["material_bending_curvature_norm_rad_mm"],
            "comparison_is_a_recovered_candidate_axial_strain": False},
        "midpoint_extension_shear_coupon": {"hand_axial_measure": .02, "hand_shear_measures": [.03, -.04],
            "observed_axial_measure": shear["midpoint_axial_strain_measure"], "observed_shear_measures": shear["midpoint_shear_measures"]},
        "large_common_rigid_motion": {name: {"neighbor_relative_rotation_rad": row["neighbor_relative_rotation_rad"],
            "chord_extension_mm": row["chord_extension_mm"]} for name, row in rigid.items()},
        "validation": {"tests": 9, "independent_read_only_review_pass": True,
            "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_finite_kinematics.py",
            "lint_command": ".venv/bin/ruff check scripts/thin_bolted_finite_kinematics.py tests/test_thin_bolted_finite_kinematics.py docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/finite-kinematics-method-v4.py"},
        "candidate_command_template": "OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.thin_bolted_finite_kinematics --field FIELD --admission RAW_BYTE_ADMISSION_RECEIPT --admission-sha256 RECEIPT_SHA --gate-sha256 FROZEN_GATE_SHA --out NEW_LOCAL_DIAGNOSTIC_JSON",
        "reused_method_documentation": {"corotational_beam": method.corot.SOURCES, "isotropic_shaft": method.isotropic.SOURCES},
        "limits": [
            "Only geometry/q and the unchanged source-bound timber reference triads are selected. No K, material energy, load/stress recovery, global assembly, CAD or solve is evaluated.",
            "Timber quantities reproduce the frozen local corotational rotations and chord change; averaged shear-angle mismatch is a marker, not condensed Timoshenko strain/stress.",
            "Shaft v and omega/L are exact measures of the recorded midpoint finite extension with condensed shear, not measured continuum stiffness or a large-curvature qualification.",
            "Fitting quantities describe one condensed two-port pose. They cannot resolve individual flat-leg, heel or hole curvature from the saved map.",
            "Circular-arc chord shortening is a geometric comparison, not a recovered second-order candidate strain or force correction.",
            "Per-element rankings suggest where a targeted refinement comparison would be informative. No arbitrary acceptance threshold, stability conclusion or gross-versus-cut stiffness bound is supplied.",
            "Candidate diagnostics require an immutable NEW finite-current admission with exact raw field bytes; canonical hashes or failed fields do not substitute for that admission.",
        ],
        "candidate_evaluated": False, "candidate_strength_or_release_established": False,
        "arbitrary_acceptance_thresholds": None, "release": method.frame.RELEASE,
    }
    output = method.frame.PACKET/"finite-kinematics-method-v4.json"
    if output.exists():
        raise FileExistsError("preserve finite kinematics method evidence")
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"path": str(output), "sha256": method.frame.sha(output), "producer_sha256": method.LOADED_PRODUCER_SHA256}))


if __name__ == "__main__":
    main()
