#!/usr/bin/env python3
"""Join saved lower-cleat forces to existing unadopted single-shear references."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SAVED = HERE / "results/attempt01"
OLD = HERE.parent / "remaining-single-shear-reference-2026-10-01/produce.py"
OLD_REPORT = Path(
    "/tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json"
)
FIXED = {
    OLD: "5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf",
    OLD_REPORT: "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e",
    SAVED
    / "comparison.json": "b1a34ac787541ee2c77ad58150ece4143b3330932e4174fcb14c4d8ecb5a0391",
    SAVED
    / "vectors.npz": "37584db3326977a87b691d4ccd3b9661c6ee770395ed99de393f16db275b7ecc",
}


def digest(path):
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def produce():
    for p, h in FIXED.items():
        if digest(p) != h:
            raise ValueError(f"source changed: {p}")
    spec = importlib.util.spec_from_file_location("saved_single_shear", OLD)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    method_pins = method.pin_sources()
    _, nds, bearing = method.basis_sources()
    old = json.loads(OLD_REPORT.read_text())
    report = json.loads((SAVED / "comparison.json").read_text())
    for p, h in report["source_sha256"].items():
        if digest(ROOT / p) != h:
            raise ValueError(f"working input changed: {p}")
    comp = (
        ROOT
        / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04"
    )
    identities = json.loads((comp / "row-identities.json").read_text())
    names = json.loads((comp / "assessment.json").read_text())[
        "body_names_in_rigid_column_order"
    ]
    with np.load(comp / "operators.npz", allow_pickle=False) as data:
        D = data["D"]
    with np.load(SAVED / "vectors.npz", allow_pickle=False) as data:
        forces = data["f"]
    rows = []
    for index, state in enumerate(report["states"]):
        for i in range(4):
            positions = report["target_lateral_rows"][2 * i : 2 * i + 2]
            axis_id = identities[positions[0]]["row_id"].rsplit("/", 1)[0]
            axis = old["axis_geometry_and_grain"][axis_id]
            by_receiver = {}
            for receiver in axis["receivers"]:
                body = receiver["receiver_id"]
                start = 6 * names.index(body)
                by_receiver[body] = (
                    -D[positions, start : start + 3].T @ forces[index, positions]
                ).tolist()
            if np.linalg.norm(np.sum(list(by_receiver.values()), axis=0)) > 1e-6:
                raise ValueError("axis action/reaction mismatch")
            exclusion, assignments, ratios, angles = method.state_reference_fields(
                nds, bearing, axis, by_receiver
            )
            if exclusion not in (
                None,
                "EXCLUDED_ZERO_LATERAL_RESULTANT_DIRECTION_UNDEFINED",
            ):
                raise ValueError(
                    f"unexpected applicability/null-reference branch: {exclusion}"
                )
            rows.append(
                {
                    "state_index": index,
                    "case": state["case"],
                    "increment": state["increment"],
                    "scenario": state["scenario"],
                    "clearance_mm": state["clearance_mm"],
                    "axis_id": axis_id,
                    "force_on_receiver_global_n": by_receiver,
                    "lateral_grain_angles_deg": angles,
                    "assignments": assignments,
                    "maximum_unadjusted_ratio": max(ratios.values())
                    if ratios is not None
                    else None,
                    "reference_exclusion": exclusion,
                    "joint_accepted": False,
                }
            )
    return {
        "schema": "lower_service_unadjusted_lateral_comparison/v1",
        "status": "REFERENCE_ARITHMETIC_ONLY",
        "complete_joint": "HOLD",
        "release": False,
        "source_sha256": {str(p): h for p, h in FIXED.items()},
        "method_pins": method_pins,
        "producer_sha256": digest(Path(__file__)),
        "reference_basis": old["reference_basis"],
        "count": len(rows),
        "null_reference_count": sum(
            r["maximum_unadjusted_ratio"] is None for r in rows
        ),
        "maximum_unadjusted_ratio": max(
            r["maximum_unadjusted_ratio"]
            for r in rows
            if r["maximum_unadjusted_ratio"] is not None
        ),
        "rows": rows,
        "limit": "Unadopted Fyb=45ksi/DF-L SG0.50/full nominal shank/zero face-gap reference. Adjustments, group/splitting, axial interaction and contact applicability are not qualified.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("refusing to overwrite evidence")
    result = produce()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "count": result["count"],
                "maximum_unadjusted_ratio": result["maximum_unadjusted_ratio"],
                "sha256": digest(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
