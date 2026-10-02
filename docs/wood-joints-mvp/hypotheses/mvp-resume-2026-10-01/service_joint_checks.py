"""Current six-case individual references for the four lower-left service bolts."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import right_corner_clearance as method
import top_corner_actions as accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
RESPONSE = HERE / "all-outer-corner-frame-attempt01"
INPUTS = (
    HERE.parent
    / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
)
BLOCK = "left_service_outer_lower_cleat"
sha, read, require = accounting.sha, accounting.read, accounting.require


def run(output):
    require(not output.exists(), "preserve existing service calculation")
    comparison, inputs = read(RESPONSE / "comparison.json"), read(INPUTS)
    rows, model = read(FRAME / "row-identities.json"), read(FRAME / "model.json")
    pins = {ROOT / p: h for p, h in comparison["source_sha256"].items()}
    pins.update(
        {
            RESPONSE / "comparison.json": sha(RESPONSE / "comparison.json"),
            RESPONSE / "response.npz": comparison["response_sha256"],
            FRAME / "row-identities.json": sha(FRAME / "row-identities.json"),
            FRAME / "model.json": sha(FRAME / "model.json"),
            FRAME / "operators.npz": sha(FRAME / "operators.npz"),
            INPUTS: sha(INPUTS),
            Path(method.__file__): sha(Path(method.__file__)),
            Path(method.lateral.__file__): sha(Path(method.lateral.__file__)),
            Path(__file__): sha(Path(__file__)),
        }
    )
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    planes = defaultdict(list)
    for row in rows:
        if row["ownership"]["role"] == accounting.LATERAL and BLOCK in (
            row["ownership"]["first_body"],
            row["ownership"]["second_body"],
        ):
            planes[row["row_id"]].append(row)
    require(
        len(planes) == 4 and all(len(p) == 2 for p in planes.values()), "service census"
    )
    members = {
        m["member_id"]: m["reduced_geometry_descriptor"] for m in inputs["members"]
    }
    connections = {
        c["axis_id"]: c for c in inputs["connections"] if c["kind"] == "candidate_bolt"
    }
    block_start = 6 * model["body_names"].index(BLOCK)
    states = []
    with (
        np.load(FRAME / "operators.npz", allow_pickle=False) as operators,
        np.load(RESPONSE / "response.npz", allow_pickle=False) as response,
    ):
        D = operators["D"]
        for source in comparison["states"]:
            if source["gap_scale"] != 1:
                continue
            require(
                source["status"] == "PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                "failed frame state",
            )
            raw = response[source["case_id"] + "_gap_raw_force_n"]
            for plane_id, components in sorted(planes.items()):
                axis = plane_id.rsplit("/", 1)[0]
                connection = connections[axis]
                geometry = connection["source_record"]["geometry"]
                receivers = geometry["wood_receiver_intervals"]
                require(len(receivers) == 2, "shared bolt outside service route")
                positions = [r["row"] for r in components]
                force = -D[positions, block_start : block_start + 3].T @ raw[positions]
                shear = float(np.linalg.norm(force))
                zero_lateral = shear <= 1e-8
                lengths, angles = [], []
                for receiver in receivers:
                    intervals = receiver[
                        "current_shaft_intersection_solid_intervals_from_underhead_mm"
                    ]
                    require(len(intervals) == 1, "disconnected receiver")
                    lengths.append(intervals[0][1] - intervals[0][0])
                    grain = np.asarray(
                        members[receiver["receiver_id"]]["axis"], dtype=float
                    )
                    grain /= np.linalg.norm(grain)
                    axis_direction = np.asarray(connection["axis_xyz"], dtype=float)
                    require(
                        abs(grain @ axis_direction) < 1e-8,
                        "end-grain route is separate",
                    )
                    angles.append(
                        None
                        if zero_lateral
                        else float(
                            np.rad2deg(
                                np.arccos(np.clip(abs(grain @ force) / shear, 0, 1))
                            )
                        )
                    )
                tie = [r for r in rows if r["row_id"] == axis + "/outer-seat-axial-tie"]
                require(len(tie) == 1, "outer tie identity missing")
                record = {
                    "case_id": source["case_id"],
                    "axis_id": axis,
                    "force_on_cleat_n": force.tolist(),
                    "shear_n": shear,
                    "simultaneous_tension_n": float(raw[tie[0]["row"]]),
                    "receiver_ids": [r["receiver_id"] for r in receivers],
                    "bearing_lengths_mm": lengths,
                    "load_to_grain_angles_degrees": angles,
                    "lateral_reference_status": "ZERO_LATERAL_DIRECTION_UNDEFINED"
                    if zero_lateral
                    else "CONDITIONAL_INDIVIDUAL_REFERENCE",
                }
                for name, fyb in (
                    ("45ksi", 45000),
                    ("92ksi", 92000),
                    ("106ksi", 106000),
                ):
                    reference = (
                        None
                        if zero_lateral
                        else method.diameter_reference(lengths, angles, 6.35, fyb)
                    )
                    record["reference_" + name + "_n"] = reference
                    record["ratio_" + name] = (
                        None if zero_lateral else shear / reference
                    )
                states.append(record)
    require(len(states) == 24, "six-case service state count changed")
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    report = {
        "schema": "current_lower_service_individual_reference/v1",
        "states": states,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "producer_sha256": sha(Path(__file__)),
        "limits": [
            "Same-state signed forces and ties belong to the current six-joint nominal-gap frame, not the historical 84 service states.",
            "References reuse the existing six-mode smooth-quarter-inch DF-L SG0.50 single-shear arithmetic; Fyb45/92/106ksi are explicit conditional scenarios.",
            "These unadjusted individual lateral references do not establish group/splitting, simultaneous steel interaction, washer transfer, actual hardware or complete joint acceptance.",
        ],
        "reviewed_geometry_changed": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    output.mkdir()
    (output / "result.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            max(
                (s for s in states if s["ratio_92ksi"] is not None),
                key=lambda s: s["ratio_92ksi"],
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
