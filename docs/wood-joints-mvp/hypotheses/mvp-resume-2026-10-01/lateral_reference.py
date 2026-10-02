"""Basic single-bolt lateral references for the six-case static scenario.

Reuse the existing six-mode helper and both existing Fyb hypotheses. Keep
multi-receiver and end-grain method boundaries explicit; accept no joint.
"""

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from fea.dowel_yield import single_shear

BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
INPUTS = BASE / "reduced-static-attempt01/model-inputs.json"
HELPER = ROOT / "fea/dowel_yield.py"
PINS = {
    INPUTS: "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    HELPER: "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}
N_PER_LBF = 4.4482216152605


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def angle(force, grain):
    magnitude = math.sqrt(sum(v * v for v in force))
    if magnitude < 1e-10:
        return 90.0  # Conservative directional reference for a zero load.
    cosine = abs(sum(a * b for a, b in zip(force, grain, strict=True))) / magnitude
    return math.degrees(math.acos(min(1.0, cosine)))


def bearing(theta):
    radians = math.radians(theta)
    return 5600 * 4450 / (5600 * math.sin(radians) ** 2 + 4450 * math.cos(radians) ** 2)


def reference(lengths, angles, fyb):
    d = 0.25
    moment = fyb * d**3 / 6
    factor = 1 + 0.25 * max(angles) / 90
    return single_shear(
        main_length_in=lengths[0] / 25.4,
        side_length_in=lengths[1] / 25.4,
        main_bearing_lb_in=bearing(angles[0]) * d,
        side_bearing_lb_in=bearing(angles[1]) * d,
        main_yield_moment_lb_in=moment,
        side_yield_moment_lb_in=moment,
        gap_in=0,
        reduction_terms={
            key: value * factor
            for key, value in {
                "Im": 4,
                "Is": 4,
                "II": 3.6,
                "IIIm": 3.2,
                "IIIs": 3.2,
                "IV": 3.2,
            }.items()
        },
    )


def main():
    for path, expected in PINS.items():
        if sha(path) != expected:
            raise ValueError("changed source: " + str(path))
    summary_path = HERE / "simple-bolt-demand-summary.json"
    summary = json.loads(summary_path.read_text())
    demands_path = HERE / "simple-bolt-demands.csv"
    if sha(demands_path) != summary["csv_sha256"]:
        raise ValueError("changed bolt demands")
    inputs = json.loads(INPUTS.read_text())
    grains = {
        r["member_id"]: r["reduced_geometry_descriptor"]["axis"]
        for r in inputs["members"]
        if r["member_kind"] != "panel"
    }
    bolts = {
        r["axis_id"]: r for r in inputs["connections"] if r["kind"] == "candidate_bolt"
    }
    with demands_path.open(newline="") as stream:
        demands = [
            r
            for r in csv.DictReader(stream)
            if r["role"] == "candidate_bolt_lateral_plane"
        ]
    records = []
    for demand in demands:
        axis = demand["axis_id"]
        bolt = bolts[axis]
        geometry = bolt["source_record"]["geometry"]
        if not math.isclose(geometry["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8):
            raise ValueError("expected a quarter-inch modeled shaft")
        members = [demand["first_body"], demand["second_body"]]
        intervals = {r["receiver_id"]: r for r in geometry["wood_receiver_intervals"]}
        vector = [float(demand["lateral_" + a + "_n"]) for a in "xyz"]
        record = {
            "case_id": demand["case_id"],
            "axis_id": axis,
            "plane_id": demand["plane_id"],
            "lateral_n": float(demand["lateral_resultant_n"]),
            "outer_tie_n": float(demand["outer_tie_n"]),
            "reference_45ksi_n": None,
            "ratio_45ksi": None,
            "mode_45ksi": None,
            "reference_106ksi_n": None,
            "ratio_106ksi": None,
            "mode_106ksi": None,
        }
        if len(bolt["receiver_member_ids"]) != 2:
            record["status"] = "MULTI_RECEIVER_NOT_SINGLE_SHEAR"
        elif any(
            abs(sum(a * b for a, b in zip(bolt["axis_xyz"], grains[m], strict=True)))
            > 1e-8
            for m in members
        ):
            record["status"] = "END_GRAIN_METHOD_SEPARATE"
        else:
            lengths = []
            for member in members:
                spans = intervals[member][
                    "current_shaft_intersection_solid_intervals_from_underhead_mm"
                ]
                if len(spans) != 1:
                    raise ValueError("non-contiguous wood bearing interval")
                lengths.append(spans[0][1] - spans[0][0])
            angles = [angle(vector, grains[m]) for m in members]
            record["status"] = "CONDITIONAL_UNADJUSTED_INDIVIDUAL_BOLT_REFERENCE"
            for fyb, name in [(45000, "45ksi"), (106000, "106ksi")]:
                result = reference(lengths, angles, fyb)
                reverse = reference(lengths[::-1], angles[::-1], fyb)
                value = result["reference_lateral_lbf"] * N_PER_LBF
                if not math.isclose(
                    result["reference_lateral_lbf"],
                    reverse["reference_lateral_lbf"],
                    rel_tol=1e-10,
                ):
                    raise ValueError("receiver role swap changed governing reference")
                record["reference_" + name + "_n"] = value
                record["ratio_" + name] = record["lateral_n"] / value
                record["mode_" + name] = result["governing_mode"]
        records.append(record)
    output = HERE / "simple-lateral-references.csv"
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    eligible = [r for r in records if r["ratio_45ksi"] is not None]
    excluded = [r for r in records if r["ratio_45ksi"] is None]
    peaks = []
    for axis in sorted({r["axis_id"] for r in eligible}):
        states = [r for r in eligible if r["axis_id"] == axis]
        peaks.append(max(states, key=lambda r: r["ratio_45ksi"]))
    peaks.sort(key=lambda r: r["ratio_45ksi"], reverse=True)
    result = {
        "schema": "simple_static_lateral_references/v1",
        "source_sha256": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
        "source_demands_sha256": sha(demands_path),
        "producer_sha256": sha(Path(__file__)),
        "output_csv_sha256": sha(output),
        "candidate_axes": 92,
        "eligible_axes": len(peaks),
        "eligible_states": len(eligible),
        "explicit_separate_method_states": len(excluded),
        "peaks": peaks[:12],
        "above_one_45ksi": [r for r in peaks if r["ratio_45ksi"] > 1],
        "above_one_106ksi": [
            max(
                (r for r in eligible if r["axis_id"] == axis),
                key=lambda r: r["ratio_106ksi"],
            )
            for axis in sorted({r["axis_id"] for r in eligible})
            if any(r["axis_id"] == axis and r["ratio_106ksi"] > 1 for r in eligible)
        ],
        "mechanical_acceptance": False,
        "assumptions": [
            "quarter-inch full smooth-body bearing diameter and zero interface gap",
            "conditional DF-L SG 0.50, rounded Fe parallel 5600/perpendicular 4450 psi",
            "CD=1; reference before group, geometry and other end-use adjustments",
            "45 ksi is an unadopted quarter-inch Fyb hypothesis; 106 ksi is a Grade 5 Commentary estimate, not a guaranteed product minimum",
        ],
        "limits": [
            "Individual bolt lateral yield only; complete group, splitting, axial/bending, washer and member checks remain.",
            "Raw receiving intervals are the analysis geometry; actual shank and finished bearing lengths are not observed.",
            "Twelve end-grain axes and four continuous three-receiver axes retain separate methods.",
            "The twelve retained frame bolt arrangements are outside this candidate quarter-inch reference.",
        ],
    }
    (HERE / "simple-lateral-reference-summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(
        f"{len(peaks)} eligible axes / {len(eligible)} simultaneous states; {len(excluded)} explicit separate-method states."
    )
    for r in peaks[:8]:
        print(
            r["axis_id"],
            r["case_id"],
            "45ksi ratio",
            round(r["ratio_45ksi"], 3),
            "106ksi ratio",
            round(r["ratio_106ksi"], 3),
        )


if __name__ == "__main__":
    main()
