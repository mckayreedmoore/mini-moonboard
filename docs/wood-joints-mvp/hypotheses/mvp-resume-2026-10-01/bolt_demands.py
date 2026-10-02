"""Export simultaneous bolt actions from the simple static frame scenario."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ROWS = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04/row-identities.json"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    results = json.loads((HERE / "simple-frame-results.json").read_text())
    response = HERE / "simple-frame-response.npz"
    if sha(response) != results["response_sha256"]:
        raise ValueError("changed static response")
    if sha(ROWS) != results["source_sha256"]["row-identities.json"]:
        raise ValueError("changed row identities")
    if not results["source_unchanged"] or len(results["cases"]) != 6:
        raise ValueError("incomplete static scenario")
    if any(
        c["status"] != "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS" for c in results["cases"]
    ):
        raise ValueError("a static scenario failed its checks")
    rows = json.loads(ROWS.read_text())
    planes = defaultdict(list)
    ties = {}
    for row in rows:
        role = row["ownership"]["role"]
        if role in ("candidate_bolt_lateral_plane", "retained_bolt_lateral_plane"):
            planes[row["row_id"]].append(row)
        elif role == "physical_bolt_outer_seat_tension":
            axis = row["row_id"].rsplit("/", 1)[0]
            if axis in ties:
                raise ValueError("duplicate axial tie: " + axis)
            ties[axis] = row
    if len(planes) != 108 or len(ties) != 104:
        raise ValueError(
            "expected 96 candidate and 12 retained lateral interfaces; 104 outer ties"
        )
    output = []
    with np.load(response, allow_pickle=False) as data:
        for case in results["cases"]:
            case_id = case["case_id"]
            force = data[case_id + "_force_n"]
            if force.shape != (1840,) or not np.isfinite(force).all():
                raise ValueError("invalid source-row force vector")
            for plane, components in sorted(planes.items()):
                axis = plane.rsplit("/", 1)[0]
                tie = ties[axis]
                own = components[0]["ownership"]
                if len(components) != 2:
                    raise ValueError("lateral plane must have two components")
                for row in components:
                    if any(
                        row["ownership"][key] != own[key]
                        for key in ["first_body", "second_body", "point_mm"]
                    ):
                        raise ValueError("mixed plane identities")
                directions = np.array(
                    [r["ownership"]["direction_global_xyz"] for r in components]
                )
                np.testing.assert_allclose(
                    directions @ directions.T, np.eye(2), atol=1e-8
                )
                lateral = force[[r["row"] for r in components]] @ directions
                record = {
                    "case_id": case_id,
                    "axis_id": axis,
                    "plane_id": plane,
                    "first_body": own["first_body"],
                    "second_body": own["second_body"],
                    "point_x_mm": own["point_mm"][0],
                    "point_y_mm": own["point_mm"][1],
                    "point_z_mm": own["point_mm"][2],
                    "lateral_x_n": lateral[0],
                    "lateral_y_n": lateral[1],
                    "lateral_z_n": lateral[2],
                    "lateral_resultant_n": float(np.linalg.norm(lateral)),
                    "outer_tie_n": float(force[tie["row"]]),
                    "outer_tie_first_body": tie["ownership"]["first_body"],
                    "outer_tie_second_body": tie["ownership"]["second_body"],
                    "role": own["role"],
                }
                output.append(record)
    csv_path = HERE / "simple-bolt-demands.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    maxima = []
    for case in results["cases"]:
        values = [r for r in output if r["case_id"] == case["case_id"]]
        lateral = max(values, key=lambda r: r["lateral_resultant_n"])
        tension = max(values, key=lambda r: r["outer_tie_n"])
        maxima.append(
            {
                "case_id": case["case_id"],
                "peak_lateral": lateral,
                "peak_outer_tie": tension,
            }
        )
    summary = {
        "schema": "simple_static_bolt_demands/v1",
        "candidate": results["candidate"],
        "revision_id": results["revision_id"],
        "source_results_sha256": sha(HERE / "simple-frame-results.json"),
        "source_response_sha256": sha(response),
        "source_rows_sha256": sha(ROWS),
        "producer_sha256": sha(Path(__file__)),
        "csv_sha256": sha(csv_path),
        "cases": 6,
        "physical_bolt_axes": 104,
        "candidate_axes": 92,
        "retained_axes": 12,
        "lateral_interfaces": 108,
        "simultaneous_interface_states": len(output),
        "maxima": maxima,
        "mechanical_acceptance": False,
        "limits": [
            "Separate same-state lateral planes and outer axial ties; maxima from different states are not combined.",
            "Outer tie spans its recorded receivers and is not a local shear-plane axial stress.",
            "No local bolt bending moment or wood/hardware resistance is inferred.",
            "The four extra candidate interfaces belong to continuous three-receiver bolts; do not add their lateral resultants as one bolt shear.",
            "These are approximate static scenario demands, not replacement authenticated native exports.",
        ],
    }
    (HERE / "simple-bolt-demand-summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    print(
        f"Exported {len(output)} simultaneous plane states for 104 physical bolts across six cases."
    )
    for r in maxima:
        print(
            r["case_id"],
            "peak lateral N",
            round(r["peak_lateral"]["lateral_resultant_n"], 1),
            "peak outer tie N",
            round(r["peak_outer_tie"]["outer_tie_n"], 1),
        )


if __name__ == "__main__":
    main()
