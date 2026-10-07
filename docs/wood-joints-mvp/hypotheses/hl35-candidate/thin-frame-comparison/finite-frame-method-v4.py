"""Small composition evidence over reused fixtures; no candidate solve or CAD."""

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_frame as method
from scripts import thin_bolted_frame_mechanics as frame


def main():
    test = frame.ROOT / "tests/test_thin_bolted_finite_frame.py"
    spec = importlib.util.spec_from_file_location("finite_frame_coupons", test)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    potential, _, mechanics_fixture = fixture.small_potential(True, True)
    q = np.random.default_rng(27).normal(scale=.1, size=potential.ndof)
    q[3:6] *= 80.
    full, compact = potential.response(q), potential.response(q, False, recover_actions=True)
    direction = np.random.default_rng(28).normal(size=potential.ndof)
    direction /= np.linalg.norm(direction)
    h = 1e-4
    plus, minus = potential.response(q + h*direction, False), potential.response(q - h*direction, False)
    force_errors, moment_errors, replay_errors = [], [], []
    for action in compact["finite_interaction_actions"]:
        first, second = np.array(action["point_on_first_xyz_mm"]), np.array(action["point_on_second_xyz_mm"])
        force = np.array(action["force_on_first_xyz_n"])
        force_errors.append(np.linalg.norm(force + action["force_on_second_xyz_n"]))
        moment_errors.append(np.linalg.norm(np.cross(first - second, force) + action["moment_on_first_at_current_point_xyz_nmm"]
                                             + np.array(action["moment_on_second_at_current_point_xyz_nmm"])))
        for side in ("first", "second"):
            pose = method.current_pose_from_map(potential.map, action[side], action[f"reference_{side}_point_xyz_mm"], q,
                flange=action.get(side + "_flange"), projected_ring=(side == "first" and action["first_port_kind"] == "projected_ring"))
            replay_errors.append(np.linalg.norm(pose["position_xyz_mm"] - action[f"point_on_{side}_xyz_mm"]))
    objective, _, _ = fixture.small_potential(True)
    rotation = Rotation.from_rotvec([.21, -.19, .17]).as_matrix()
    translation = np.array([3., -5., 7.])
    rigid_q = mechanics_fixture.superpose(objective.mechanics, np.zeros(objective.ndof), rotation, translation)
    panel_fixture = fixture.fixture_file("test_thin_bolted_finite_panel_adapter.py")
    panel = objective.panels["kicker_left"]
    rigid_q[panel.indices] = panel_fixture.rigid_q(panel, rotation, translation)
    rigid = objective.response(rigid_q, False)
    replacement = fixture.fixture_file("test_thin_bolted_isotropic_shaft.py").small_adapter()
    replaced = method.FiniteFramePotential(replacement.mechanics, {}, {}, [], [], shaft_replacement=replacement)
    shaft_q = np.random.default_rng(53).normal(scale=.07, size=replaced.ndof)
    shaft_q[3:6] *= 80.
    expected, actual = replacement.replacement_response(shaft_q, False), replaced.response(shaft_q, False)
    metrics = {
        "small_composed_dof_count": potential.ndof,
        "max_current_pair_force_residual_n": max(force_errors),
        "max_current_pair_spatial_moment_residual_nmm": max(moment_errors),
        "max_saved_map_current_point_replay_error_mm": max(replay_errors),
        "full_vs_gradient_only_gradient_difference_inf_n": float(abs(full["gradient_n"] - compact["gradient_n"]).max()),
        "directional_energy_gradient_difference_n": float(abs(direction @ full["gradient_n"] - (plus["energy_nmm"] - minus["energy_nmm"])/(2*h))),
        "directional_tangent_difference_inf_n_mm": float(abs(full["hessian_csr"] @ direction - (plus["gradient_n"] - minus["gradient_n"])/(2*h)).max()),
        "common_finite_rigid_motion_potential_nmm": rigid["energy_nmm"],
        "common_finite_rigid_motion_gradient_inf_n": float(abs(rigid["gradient_n"]).max()),
        "replacement_only_energy_difference_nmm": actual["energy_nmm"] - expected["energy_nmm"],
        "replacement_only_gradient_difference_inf_n": float(abs(actual["gradient_n"] - expected["gradient_n"]).max()),
        "two_explicit_correction_rows_per_small_panel": len(compact["panel_generalized_load_corrections"]),
    }
    if (max(force_errors) > 1e-9 or max(moment_errors) > 1e-8 or max(replay_errors) > 1e-9
            or metrics["directional_energy_gradient_difference_n"] > 1e-4
            or metrics["directional_tangent_difference_inf_n_mm"] > 1e-4
            or rigid["energy_nmm"] > 1e-14 or metrics["common_finite_rigid_motion_gradient_inf_n"] > 1e-6
            or metrics["replacement_only_energy_difference_nmm"] != 0.
            or metrics["replacement_only_gradient_difference_inf_n"] != 0.):
        raise ValueError("finite composition coupon gate failed")
    pins = method.source_pins()
    for source in [Path(__file__).resolve(), test,
                   frame.ROOT / "tests/test_thin_bolted_finite_mechanics.py",
                   frame.ROOT / "tests/test_thin_bolted_finite_panel_adapter.py",
                   frame.ROOT / "tests/test_thin_bolted_isotropic_shaft.py"]:
        pins[str(source.relative_to(frame.ROOT))] = frame.sha(source)
    result = {
        "schema": "thin_bolted_finite_frame_method_coupons/v1", "source_sha256": pins,
        "command": "OPENBLAS_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/finite-frame-method-v4.py",
        "coupon_metrics": metrics,
        "validation": {
            "tests": 10,
            "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_finite_frame.py",
            "lint_command": ".venv/bin/ruff check scripts/thin_bolted_finite_frame.py tests/test_thin_bolted_finite_frame.py docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/finite-frame-method-v4.py",
            "additional_known_answers": ["Affine two-Gauss timber gravity preserves zeroth/first source mass moments.",
                "Own corner compression reports its normal reaction and explicit fixed XY activation pattern.",
                "Open/disabled corner retains its physical body and a zero current-action row.",
                "Frozen isotropic replacement is called once and the legacy shaft response is forbidden.",
                "Recovery requires one complete state/case/accessory identity."],
        },
        "api": {"factory": "FiniteFramePotential.from_prepared", "response": "response(q,tangent=True,disabled_floor_hosts=(),recover_actions=False,*,disabled_floor_support_ids=())",
                "current_position_replay": "current_pose_from_map(mapping,body,reference_point,q,flange=None,reference_director=None,projected_ring=False)",
                "physical_action_table": "finite_interaction_actions", "physical_load_table": "finite_body_applied_loads",
                "generalized_load_table": "panel_generalized_load_corrections", "saved_geometry_map": "finite_kinematic_map"},
        "limits": [
            "This composition evidence contains no candidate equilibrium solve or resistance acceptance.",
            "All actions use their own current points and explicitly owned spatial director couples. Generalized panel corrections remain distinct from physical point forces or pressure.",
            "The same six finite panels, frozen timber/fittings and isotropic shafts each contribute their energy exactly once. Prepared candidate geometry, stiffness scenarios and force/moment gates remain parent-owned.",
            "The original convex fixed-K/B stable incremental formula is inapplicable to this finite potential. A finite solver must evaluate this unchanged finite energy/residual and validate all132 current-body wrenches independently.",
            "Corner XY sticking is conditional on its own normal contact. A fixed activation pattern is conservative; opening/reclosing, pattern uniqueness, actual floor friction and global stability are not qualified.",
            "Gross timber sections, proxy panel/angle/shaft elasticity and declared connection/contact stiffness scenarios do not constitute measured stiffness or conservative strength bounds.",
        ],
        "candidate_strength_or_release_established": False, "release": frame.RELEASE,
    }
    output = frame.PACKET / "finite-frame-method-v4.json"
    if output.exists():
        raise FileExistsError("preserve finite composition method evidence")
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(output), "sha256": frame.sha(output), "producer_sha256": method.LOADED_PRODUCER_SHA256}))


if __name__ == "__main__":
    main()
