"""Replay native constrained-export energy and equation-map evidence."""
from pathlib import Path
import importlib.util
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.wood_joint_reduced_native import digest, verify, write_json


def assess():
    verify(HERE, check_live=True)
    execution = json.loads((HERE / "execution.json").read_text())
    assert execution["native_solve_executed"] is True
    assert execution["returncode"] == 0
    assert execution["container_confirmed_terminal"] is True
    for name, expected in execution["outputs_sha256"].items():
        assert digest(HERE / name) == expected, name
    parser = HERE.parent / "current-constrained-elastic-operator-export-preflight-attempt01/constrained_matrix_export_oracle.py"
    spec = importlib.util.spec_from_file_location("constrained_matrix_export_oracle", parser)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.check_export(HERE / "model.sti", HERE / "model.dof")
    assert result["status"] == "PASS_CONSTRAINED_MATRIX_EXPORT_ORACLE"
    labels = module.read_dof(HERE / "model.dof")
    stiffness, _ = module.read_sti(HERE / "model.sti", len(labels))
    eig = np.linalg.eigvalsh(stiffness)
    tolerance = float(np.max(np.abs(eig))) * 1.e-8
    # SPC at the origin excludes Tx. Internal interpolation/spring preserve
    # Ty, Tz and all three rotations; no extra zero mode is expected.
    modes = []
    for axis in (1, 2):
        modes.append(np.array([float(direction == axis+1) for _, direction in labels]))
    for axis in np.eye(3):
        modes.append(np.array([np.cross(axis, module.COORDS[node])[direction-1]
                               for node, direction in labels]))
    scale = np.linalg.norm(stiffness, ord=np.inf)
    residual = max(np.linalg.norm(stiffness @ mode, ord=np.inf)
                   / (scale * np.linalg.norm(mode, ord=np.inf)) for mode in modes)
    assert np.count_nonzero(np.abs(eig) <= tolerance) == 5
    assert np.count_nonzero(eig < -tolerance) == 0
    assert residual <= 1.e-8
    result.update({
        "remaining_rigid_modes": 5,
        "negative_stiffness_modes_below_tolerance": 0,
        "rigid_spectral_tolerance_N_per_mm": tolerance,
        "max_remaining_rigid_mode_residual_relative": float(residual),
        "native_execution_provenance_checked": True,
        "execution_provenance_note": "Parent checks exact live/frozen sources, recorded native output hashes, zero exit and terminal container.",
        "input_freeze_sha256": digest(HERE / "freeze.json"),
        "execution_sha256": digest(HERE / "execution.json"),
        "independent_review_sha256": digest(HERE / "independent-review.json"),
        "assessment_producer_sha256": digest(Path(__file__)),
        "native_run_id": execution["run_id"],
        "limits": ["Synthetic SPC/MPC/linear-spring and rotated-material affine-energy coupon only; external offset/load-work probes are algebraic, not native load or capture observations. No current-frame gravity/contact state or joint acceptance."],
    })
    return result


if __name__ == "__main__":
    result = assess()
    if "--verify" in sys.argv:
        assert result == json.loads((HERE / "assessment.json").read_text())
        print("PASS_REPLAY_NATIVE_CONSTRAINED_EXPORT_ASSESSMENT")
    else:
        write_json(HERE / "assessment.json", result)
        print(result["status"])
