"""Individual references for the lower-left service bolts from a saved source scope."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import frame_state_contract as frame_contract
import numpy as np
import remaining_joint_screen as screen
import right_corner_clearance as method
import top_corner_actions as accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
DEFAULT_CLEARANCE = HERE / "all-outer-corner-frame-attempt01"
INPUTS = (
    HERE.parent
    / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
)
BLOCK = "left_service_outer_lower_cleat"
sha, read, require = accounting.sha, accounting.read, accounting.require


def run(output, clearance=DEFAULT_CLEARANCE, *, frame_dir=FRAME,
        metadata_seed_dir=None):
    output = output.resolve()
    require(output.is_relative_to(HERE)
            and output.relative_to(HERE).parts
            and output.relative_to(HERE).parts[0].startswith("service-joint-current-attempt"),
            "output must be inside an owned service-joint-current-attempt directory")
    require(not output.exists(), "preserve existing service calculation")
    binding = screen.bind_frame_sources(frame_dir, clearance, metadata_seed_dir)
    FRAME, clearance = binding["frame_dir"], binding["clearance_dir"]
    comparison, force_scope = binding["comparison"], binding["force_scope"]
    inputs = read(INPUTS)
    rows, model = binding["rows"], binding["model"]
    require(inputs["revision_id"] == model["source_revision"], "mixed geometry revision")
    require(inputs["candidate"] == model["candidate"], "mixed candidate")
    pins = dict(binding["pins"])
    pins.update(
        {
            INPUTS: sha(INPUTS),
            Path(method.__file__): sha(Path(method.__file__)),
            Path(method.lateral.__file__): sha(Path(method.lateral.__file__)),
            Path(frame_contract.__file__): sha(Path(frame_contract.__file__)),
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
    nominal_sources = [s for s in comparison["states"] if s["gap_scale"] == 1.0]
    with (
        np.load(FRAME / "operators.npz", allow_pickle=False) as operators,
        np.load(clearance / "response.npz", allow_pickle=False) as response,
    ):
        D = operators["D"]
        for source in nominal_sources:
            require(
                source["status"]
                in (frame_contract.STRICT_STATUS, frame_contract.BOUNDED_STATUS),
                "failed frame state",
            )
            raw = response[source["case_id"] + "_gap_raw_force_n"]
            require(raw.shape == (1888,) and np.isfinite(raw).all(), "invalid saved force")
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
    require(
        len(states) == len(nominal_sources) * len(planes),
        "selected-source service state count changed",
    )
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    report = {
        "schema": "current_lower_service_individual_reference/v1",
        "frame_directory": str(FRAME.relative_to(ROOT)),
        "metadata_seed_directory": str(binding["metadata_seed_dir"].relative_to(ROOT)),
        "metadata_seed_scope": "Case order and inherited seed provenance only; no old force vectors or acceptance transferred.",
        "force_source": str((clearance / "response.npz").relative_to(ROOT)),
        "force_key": "case_id + '_gap_raw_force_n'",
        "gap_scale": 1.0,
        "case_ids": [s["case_id"] for s in nominal_sources],
        "axis_count": len(planes),
        "state_count": len(states),
        "states": states,
        "force_state_scope": force_scope,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "producer_sha256": sha(Path(__file__)),
        "limits": [
            "Same-state signed forces and ties use selected source schema "
            + force_scope["source_schema"]
            + ": "
            + force_scope["force_scope"],
            force_scope["motion_scope"],
            "References reuse the existing six-mode smooth-quarter-inch DF-L SG0.50 single-shear arithmetic; Fyb45/92/106ksi are explicit conditional scenarios.",
            "These unadjusted individual lateral references do not establish group/splitting, simultaneous steel interaction, washer transfer, actual hardware or complete joint acceptance.",
        ],
        "reviewed_geometry_changed": bool(model.get("owner_authorized_screw_movements")),
        "native_solve_run": False,
        "frame_solve_run": False,
        "CAD_rebuilt": False,
        "tests_run": False,
        "review_run": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    output.mkdir()
    (output / ".gitignore").write_text("*\n")
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
    parser.add_argument("--frame", type=Path, default=FRAME,
                        help="Physical operator directory; defaults to the historical corrected frame.")
    parser.add_argument("--metadata-seed", type=Path,
                        help="Case metadata directory; defaults to --frame. No seed force arrays are consumed.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clearance", type=Path, default=DEFAULT_CLEARANCE)
    args = parser.parse_args()
    run(args.output, args.clearance, frame_dir=args.frame,
        metadata_seed_dir=args.metadata_seed)
