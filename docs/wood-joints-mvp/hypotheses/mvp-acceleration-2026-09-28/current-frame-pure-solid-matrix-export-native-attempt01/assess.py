"""Parent authentication and replay of the physical-solid sparse export."""
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
    authorization = json.loads((HERE / "authorization.json").read_text())
    review_path = ROOT / authorization["independent_review"]
    assert digest(review_path) == authorization["independent_review_sha256"]
    review = json.loads(review_path.read_text())
    assert review["input_freeze_sha256"] == digest(HERE / "freeze.json")
    assert review["ready_for_scoped_native_run"] is True
    method = HERE.parent / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
    spec = importlib.util.spec_from_file_location("pure_solid_sparse_assessor", method)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.verify_source_pins()
    source = HERE.parent / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
    result = module.assess_frame_export(HERE / "model.sti", HERE / "model.dof", source)
    result.update({
        "native_execution_provenance_checked": True,
        "input_freeze_sha256": digest(HERE / "freeze.json"),
        "execution_sha256": digest(HERE / "execution.json"),
        "independent_review_sha256": digest(review_path),
        "assessment_producer_sha256": digest(Path(__file__)),
        "native_run_id": execution["run_id"],
        "auxiliary_mass_output_used_for_gravity": False,
        "frame_response_computed": False,
        "mechanical_acceptance": False,
    })
    return result


if __name__ == "__main__":
    result = assess()
    if "--verify" in sys.argv:
        assert result == json.loads((HERE / "assessment.json").read_text())
        print("PASS_REPLAY_AUTHENTICATED_PURE_SOLID_EXPORT")
    else:
        write_json(HERE / "assessment.json", result)
        print(json.dumps({"status": result["status"],
                          "equations": result["dof_map"]["equation_count"],
                          "triangle_pairs": result["stiffness"]["triangle_pair_count"],
                          "rigid_residual": result["body_rigid_mode_screen"]["overall_max_relative_residual"]}))
