"""Parent-only frame response from authenticated knee-bridge gravity operators.

Importing this module performs no source reads, helper imports or calculations.
The preserved response supplies numerical guesses only, never acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
OUTPUT_BASE = HERE / "rawlocal/knee-bridge-frame"
ORIGINAL = PACKET / "corner-frame-attempt01"
SOURCE = HERE / "operators-attempt02"
MANIFEST = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
MANIFEST_SHA256 = "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c"
FILES = ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json")
HELPER_PINS = {
    "both_corner_frame": "27a8a8d2f5d34f1230c86f34385e68a8a895f675683f0dc39199e82c93096bc0",
    "simple_frame": "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    "right_corner_clearance": "93c7727c1c24fb5b7ed725fc4656651fe6e760a36a378d635a97e202b872fb88",
    "circular_clearance": "0314817effad8d8279e80576ed2cd77012566d0c8252f74e279dc83e366df98b",
    "bounded_clearance": "35c0ceb7609c7ff77118ddf0a8e9f0da681ae41ad3396e4a95a71792724a9c7b",
    "top_corner_actions": "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    "lateral_reference": "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
}
SOURCE_PINS = {
    ORIGINAL / "frame-response.npz": "b3aa4bab7594b048466333eda63a472490649a9378d7dea88c26d10ad45216f8",
    ORIGINAL / "frame-results.json": "34eb66332a655244a4018e1b77344985e4c145fc946cb2028405a437003d0c41",
    SOURCE / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    SOURCE / "B.npz": "d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a",
    SOURCE / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    SOURCE / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    SOURCE / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    ROOT / "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    MANIFEST: MANIFEST_SHA256,
}
LIMITS = {
    "proposal_adopted": False,
    "numerical_seed_acceptance_transferred": False,
    "actual_changed_hole_elastic_stiffness_established": False,
    "local_bridge_compatibility_solved": False,
    "stability_acceptance": False,
    "hardware_capacity_qualified": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def array_sha(array):
    """Use the gravity producer's dtype/shape/C-order array fingerprint."""
    digest = hashlib.sha256(f"{array.dtype.str}:{array.shape}".encode())
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, record):
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = path.resolve()
    require(path.is_relative_to(ROOT), "source lies outside repository: " + str(path))
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
            "invalid source SHA-256: " + str(path))
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed: " + str(path))


def run(output, operator_directory, expected_assessment_sha256):
    """Run the pinned existing method once; parent owns readiness and execution."""
    output = Path(output).resolve()
    operator_directory = Path(operator_directory).resolve()
    require(output.parent == OUTPUT_BASE.resolve() and not output.exists(),
            "output must be a fresh immediate child of rawlocal/knee-bridge-frame")
    require(operator_directory.is_relative_to(ROOT) and operator_directory.is_dir(),
            "operator directory must be an existing repository packet")
    assessment_path = operator_directory / "operator-assessment.json"
    pins = dict(SOURCE_PINS)
    pins.update({PACKET / (name + ".py"): digest for name, digest in HELPER_PINS.items()})
    bind(pins, assessment_path, expected_assessment_sha256)
    bind(pins, Path(__file__), sha(Path(__file__)))
    verify(pins)
    assessment = read(assessment_path)
    require(assessment.get("schema") == "knee-bridge-gravity-operators/v1"
            and assessment.get("status") == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment.get("operator_ready") is True
            and assessment.get("gravity_delta_in_proposal_operators") is True,
            "completed knee-bridge gravity operators required")
    for name, digest in assessment["source_sha256"].items():
        bind(pins, ROOT / name, digest)
    for name, digest in assessment["output_sha256"].items():
        path = (operator_directory / name).resolve()
        require(path.is_relative_to(operator_directory), "operator output escapes packet")
        bind(pins, path, digest)
    require(set(FILES).issubset(assessment["output_sha256"]), "operator contract files missing")
    verify(pins)

    manifest = read(MANIFEST)
    original = read(ORIGINAL / "frame-results.json")
    model = read(operator_directory / "model.json")
    inputs = read(operator_directory / "model-inputs.json")
    source_inputs = read(SOURCE / "model-inputs.json")
    case_ids = [case["case_id"] for case in original["cases"]]
    require(case_ids == manifest["case_ids"] == assessment["case_ids"] and len(case_ids) == 6,
            "original case identities differ from integration or gravity assessment")
    require([case["case_id"] for case in inputs["cases"]] == case_ids, "operator case order changed")
    require(all(case["source_applied_load"] == source["source_applied_load"]
                and case["loaded_panel"] == source["loaded_panel"]
                for case, source in zip(inputs["cases"], source_inputs["cases"], strict=True)),
            "250 lb × 2 / 300 N / 100 mm live cases changed")
    require(inputs["connections"] == source_inputs["connections"], "global connector inputs changed")
    counts = {kind: sum(c["kind"] == kind for c in inputs["connections"])
              for kind in ("candidate_bolt", "retained_bolt", "panel_screw")}
    require(counts == {"candidate_bolt": 92, "retained_bolt": 12, "panel_screw": 66},
            "global 104-bolt / 66-screw inventory changed")
    for name in ("B.npz", "row-identities.json"):
        require(sha(operator_directory / name) == SOURCE_PINS[SOURCE / name],
                "global connector matrix or rows changed")
    mass, deadfactor = assessment["modeled_mass_kg"], assessment["dead_load_factor"]
    require(math.isfinite(mass) and mass > 0 and math.isfinite(deadfactor), "invalid operator mass")
    require(model["modeled_mass_kg"] == inputs["modeled_mass_kg"] == mass
            and model["dead_load_factor"] == inputs["dead_load_factor"] == deadfactor,
            "operator/model/input mass metadata differ")
    require(abs(deadfactor - (1 + 25 / mass)) < 1e-12, "25 kg accessory factor differs")
    require(mass != original["modeled_mass_kg"], "changed-mass operator packet required")
    require(original["response_sha256"] == SOURCE_PINS[ORIGINAL / "frame-response.npz"],
            "original numerical response pin differs")
    internal = manifest["proposed_internal_bolt_axes"]
    require(len(internal) == 4 and all(axis["global_operator_row"] is None
            and axis["same_body_end_pair"] for axis in internal), "internal bridge/global rows conflated")
    require(manifest["census"]["total_unique_proposal_bolt_axes"] == 108
            and manifest["census"]["existing_receiver_bolt_axes"] == 104
            and manifest["proposal_adopted"] is False, "unadopted census differs")
    allocations = manifest["proposed_internal_allocations"]
    allocations_path = MANIFEST.parent / allocations["file"]
    bind(pins, allocations_path, allocations["sha256"])
    verify(pins)

    # Direct imports execute only inside the parent API call. No method globals change.
    previous_path, previous_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.path[:0] = [str(PACKET), str(ROOT)]
    sys.dont_write_bytecode = True
    try:
        import both_corner_frame
        import bounded_clearance
        import numpy as np
        import simple_frame

        modules = (both_corner_frame, bounded_clearance, simple_frame,
                   both_corner_frame.method, both_corner_frame.circular_clearance,
                   both_corner_frame.accounting, both_corner_frame.method.lateral)
        for module in modules:
            require(Path(module.__file__).resolve() == PACKET / (module.__name__ + ".py"),
                    "import resolved to a different source: " + module.__name__)
        live_fingerprints = {}
        with np.load(SOURCE / "operators.npz", allow_pickle=False) as source_operators, \
                np.load(operator_directory / "operators.npz", allow_pickle=False) as new_operators:
            for name in ("F", "e", "W"):
                key = name + "/live_columns"
                source_digest = array_sha(source_operators[name][:, 1::2])
                require(assessment["unchanged_array_sha256"][key] == source_digest,
                        "gravity live fingerprint differs from pinned source: " + name)
                require(array_sha(new_operators[name][:, 1::2]) == source_digest,
                        "new operator live columns changed: " + name)
                live_fingerprints[key] = source_digest
        verify(pins)
        output.mkdir(parents=True)
        (output / ".gitignore").write_text("*\n")
        seed = output / "NUMERICAL_SEED_ONLY"
        seed.mkdir()
        (seed / "frame-response.npz").write_bytes((ORIGINAL / "frame-response.npz").read_bytes())
        require(sha(seed / "frame-response.npz") == original["response_sha256"], "seed bytes differ")
        write(seed / "frame-results.json", {
            "status": "NUMERICAL_SEED_ONLY",
            "source_sha256": {str(path.relative_to(ROOT)): SOURCE_PINS[path]
                              for path in (ORIGINAL / "frame-results.json", ORIGINAL / "frame-response.npz")},
            "original_modeled_mass_kg": original["modeled_mass_kg"],
            "original_dead_load_factor": original["dead_load_factor"],
            "operator_directory": str(operator_directory.relative_to(ROOT)),
            "operator_assessment_sha256": expected_assessment_sha256,
            "modeled_mass_kg": mass,
            "dead_load_factor": deadfactor,
            "response_sha256": original["response_sha256"],
            "case_ids": case_ids,
            "cases": [{"case_id": case_id} for case_id in case_ids],
        })
        for name in ("frame-response.npz", "frame-results.json"):
            bind(pins, seed / name, sha(seed / name))
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        call = {
            "service_joints": True, "bottom_corners": True,
            "all_two_receiver_clearances": True, "bounded_freeplay": True,
            "frame_directory": operator_directory, "seed_directory": seed,
            "connection_inputs": operator_directory / "model-inputs.json", "climber_load_scale": 1.0,
        }
        write(output / "inputs.json", {
            "operator_assessment_sha256": expected_assessment_sha256,
            "call": {key: str(value.relative_to(ROOT)) if isinstance(value, Path) else value
                     for key, value in call.items()},
            "source_load_identity": manifest["source_load_identity"],
            "authenticated_live_array_sha256": live_fingerprints,
            "elastic_assumption": "FILLED-BORE gross-compliance MVP; fresh gravity F/e/W only",
            "global_receiver_bolt_axes": 104, "proposal_census": manifest["census"]["proposal"],
            "separate_internal_axis_ids": [axis["axis_id"] for axis in internal],
            "separate_static_allocations": {"file": str(allocations_path.relative_to(ROOT)),
                "sha256": allocations["sha256"], "reallocated_from_this_response": False},
            **LIMITS,
        })

        def receipt(status, error=None):
            verify(pins)
            record = {
                "schema": "knee_bridge_parent_frame_receipt/v1", "status": status,
                "terminal_exception": str(error) if error is not None else None,
                "producer_sha256": pins[Path(__file__).resolve()],
                "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in pins.items()},
                "output_sha256": {str(path.relative_to(output)): sha(path)
                                  for path in sorted(output.rglob("*")) if path.is_file()},
                "modeled_mass_kg": mass, "dead_load_factor": deadfactor,
                "authenticated_live_array_sha256": live_fingerprints,
                "global_receiver_bolt_axes": 104, "total_unique_proposal_bolt_axes": 108,
                "new_internal_bolts_are_global_connectors": False, **LIMITS,
            }
            write(output / "receipt.json", record)
            return record

        try:
            both_corner_frame.run(output / "response", **call)
        except Exception as error:
            receipt("STOP_UNACCEPTED_FRAME_RUN", error)
            raise
        return receipt("COMPLETED_EXISTING_FRAME_RUN_NO_JOINT_ACCEPTANCE")
    finally:
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--operator-directory", type=Path, required=True)
    parser.add_argument("--expected-assessment-sha256", required=True)
    arguments = parser.parse_args()
    run(arguments.output, arguments.operator_directory, arguments.expected_assessment_sha256)
