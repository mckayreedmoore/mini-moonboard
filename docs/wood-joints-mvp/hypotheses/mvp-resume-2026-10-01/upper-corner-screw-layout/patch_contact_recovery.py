"""Recover the two refined A1 responses using the frozen displacement method.

Adapt only the source packet locations and the forty-four contact centroid
identities/sample count. Elastic equations and the original-q gate stay fixed.
"""

from __future__ import annotations

import argparse
import fcntl
import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import corner_frame as method
import top_corner_actions as accounting

ROOT = accounting.ROOT
require, sha, read = accounting.require, accounting.sha, accounting.read
RECOVERY = HERE / "contact-gap-recovery.py"
RECOVERY_SHA = "37d8b7a1f6789fe993f0036ba7e390c5f1a55262b5736c9bfc4e484dc04ea93b"


def run(operator_root, frame_root, output):
    require(not output.exists(), "Preserve previous gap recoveries")
    require(sha(RECOVERY) == RECOVERY_SHA, "Frozen recovery helper changed")
    geometry_path = operator_root / "geometry.json"
    geometry = read(geometry_path)
    receipt = read(operator_root / "result.json")
    require(sha(geometry_path) == receipt["geometry_sha256"], "Refinement geometry changed")
    cells = geometry["cells"]
    require(len(cells) == 44 and geometry["new_x_divisions"] == 22
            and geometry["transverse_divisions"] == 2, "Unexpected refined contact grid")
    pins = {Path(__file__): sha(Path(__file__)), geometry_path: sha(geometry_path),
            operator_root / "result.json": sha(operator_root / "result.json")}
    recovery = method.module(RECOVERY, "refined_saved_gap_recovery")
    recovery.FRAMES = {}
    for count in (12, 20):
        frame = frame_root / f"frame-{count}-attempt01"
        comparison = read(frame / "comparison.json")
        operators = operator_root / f"operators-{count}"
        require(comparison["frame_operator_directory"] == str(operators.relative_to(ROOT))
                and comparison["screws_per_main_panel"] == count, "Frame belongs to another operator")
        require(len(comparison["states"]) == 1
                and comparison["states"][0]["case_id"] == "a1-rear"
                and comparison["states"][0]["gap_scale"] == 1.0, "Expected one returned A1 nominal state")
        require(sha(frame / "response.npz") == comparison["response_sha256"], "Frame response changed")
        assessment_sha = sha(operators / "operator-assessment.json")
        require(assessment_sha == receipt["operators"][str(count)]["assessment_sha256"],
                "Refined operator assessment changed")
        recovery.FRAMES[count] = (str(frame.relative_to(HERE)), sha(frame / "comparison.json"),
                                 comparison["response_sha256"], assessment_sha)
    points_text = inspect.getsource(recovery.points_for_patch)
    point_sites = {
        'len(bands[0]) == len(bands[1]) == 11, "Expected eleven stations in each transverse band"':
            'len(bands[0]) == len(bands[1]) == 22, "Expected twenty-two stations in each transverse band"',
        "for i in range(10):": "for i in range(21):",
        '== 22, "Original cell excluded"': '== 44, "Original refined cell excluded"',
    }
    require(all(points_text.count(site) == 1 for site in point_sites), "Frozen point sampler changed")
    for old, new in point_sites.items():
        points_text = points_text.replace(old, new)
    build_text = inspect.getsource(recovery.build)
    old_cells = 'cells = [r for r in physical["contact_cell_ownership"] if r.get("source_patch_index") == 59]'
    require(build_text.count(old_cells) == 1, "Frozen contact selection changed")
    build_text = build_text.replace(old_cells, "cells = refined_cells")
    namespace = recovery.__dict__.copy()
    namespace["refined_cells"] = cells
    adapted = points_text + "\n" + build_text
    exec(compile(adapted, "<refined-contact-saved-gap-recovery>", "exec"), namespace)  # noqa: S102 -- frozen source and exact checked substitutions
    namespace["build"](output)
    for path, digest in pins.items():
        require(sha(path) == digest, "Input changed during refined recovery")
    result = read(output / "result.json")
    result["source_sha256"].update({str(path.relative_to(ROOT)): digest for path, digest in pins.items()})
    result.update(schema="refined_patch59_saved_contact_gap_recovery/v1",
                  original_contact_centroids_per_state=44,
                  displacement_method_and_q_gate_changed=False,
                  frame_solve_executed=False, native_launch=False, physical_release=False)
    (output / "patch-recovery-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / "adapted-recovery.py.snapshot").write_text(adapted)
    result["adapted_recovery_sha256"] = sha(output / "adapted-recovery.py.snapshot")
    (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("refined_result_sha256", sha(output / "result.json"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-root", type=Path, required=True)
    parser.add_argument("--frame-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "Shared mechanics slot occupied")
        run(args.operator_root.resolve(), args.frame_root.resolve(), args.output.resolve())
