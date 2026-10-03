"""Replay the exported coupon oracle with separately authenticated execution."""
from pathlib import Path
import importlib.util
import json
import sys

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
    parser = HERE.parent / "current-native-elastic-operator-export-preflight-attempt01/matrix_export_oracle.py"
    spec = importlib.util.spec_from_file_location("matrix_export_oracle", parser)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.check(HERE / "model")
    assert result["status"] == "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE"
    result.update({
        "native_execution_provenance_checked": True,
        "execution_provenance_note": "Parent verifies exact input/source freeze and every recorded native output hash, zero exit and terminal container.",
        "input_freeze_sha256": digest(HERE / "freeze.json"),
        "execution_sha256": digest(HERE / "execution.json"),
        "independent_review_sha256": digest(HERE / "independent-review.json"),
        "assessment_producer_sha256": digest(Path(__file__)),
        "native_run_id": execution["run_id"],
        "limits": ["Free isotropic C3D20 coupon only; no constrained mapping, rotated wood, gravity, floor state, frame response or joint acceptance."],
    })
    return result


if __name__ == "__main__":
    result = assess()
    if "--verify" in sys.argv:
        assert result == json.loads((HERE / "assessment.json").read_text())
        print("PASS_REPLAY_NATIVE_FREE_C3D20_EXPORT_ASSESSMENT")
    else:
        write_json(HERE / "assessment.json", result)
        print(result["status"])
