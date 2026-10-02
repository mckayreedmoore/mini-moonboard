"""Extract relocated-frame screw demands against retained generic references.

Example, from repository root:
  uv run python .../head_check.py --source .../frame-250-attempt02 \
      --source .../frame-140-attempt01 --output .../rawlocal/head-check/attempt01

This consumer reads saved responses and each packet's explicit operator
directory. It neither solves a frame nor replays panel-only redistribution.
Head/withdrawal references are unadjusted hypotheses, never Hillman ratings.
No lateral resistance or combined-action capacity is transferred to new axes.
"""

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "panel-attachment"))

import attachment_screen as references
import frame_state_contract

AXIAL = "non_qualifying_parametric_screw_withdrawal"
LATERAL = "panel_screw_lateral_plane"
REFERENCE = HERE.parent / "panel-attachment/results/attempt08-all-two-receiver/comparison.json"
REFERENCE_SHA = "7146069ad3ecf913cbb354f3a37d1e6af6768fc3b577f574feb5a10bd483eb2f"
MOVED = {
    f"round_panel_upper_{side}_{column}_4"
    for side in ("left", "right") for column in ("center", "rim")
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def label(path):
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def reference_scenarios(pins):
    require(sha(REFERENCE) == REFERENCE_SHA, "retained reference worksheet changed")
    pins[label(REFERENCE)] = REFERENCE_SHA
    saved = read(REFERENCE)
    result = {}
    for kind, key, fields, value_key, function in (
        ("head", "generic_head_reference_sensitivities",
         ("plywood_G_hypothesis", "circular_head_diameter_mm_hypothesis",
          "net_plywood_thickness_mm_hypothesis"),
         "unadjusted_generic_head_reference_n", references.head_reference),
        ("withdrawal", "withdrawal_sensitivities",
         ("timber_G_hypothesis", "effective_thread_penetration_mm_hypothesis"),
         "unadjusted_generic_withdrawal_n", references.withdrawal_reference),
    ):
        scenarios = []
        for row in saved[key]:
            value = float(function(*(row[field] for field in fields)))
            require(math.isclose(value, row[value_key], rel_tol=1e-12),
                    "helper and retained generic reference disagree")
            scenarios.append({**{field: row[field] for field in fields},
                              "reference_n": value})
        require(len(scenarios) == 12, "retained reference census changed")
        result[kind] = scenarios
    for path in (Path(references.__file__), Path(frame_state_contract.__file__)):
        pins[label(path)] = sha(path)
    return result


def consume(source, pins):
    source = source.resolve()
    if source.is_file():
        require(source.name == "comparison.json", "--source must be a packet or comparison.json")
        source = source.parent
    comparison_path = source / "comparison.json"
    comparison = read(comparison_path)
    scope = frame_state_contract.force_state_scope(comparison)
    require(comparison.get("frame_operator_directory"), "explicit frame operator directory required")
    frame = Path(comparison["frame_operator_directory"])
    frame = frame.resolve() if frame.is_absolute() else (ROOT / frame).resolve()
    require(frame.is_relative_to(ROOT), "operator directory must be inside this repository")
    pins[label(comparison_path)] = sha(comparison_path)

    def bind(path, expected):
        digest = sha(path)
        require(digest == expected, "changed direct input: " + label(path))
        pins[label(path)] = digest

    bind(source / "response.npz", comparison["response_sha256"])
    for name in ("model.json", "row-identities.json", "operators.npz", "operator-assessment.json"):
        path = frame / name
        bind(path, comparison["source_sha256"][label(path)])
    assessment = read(frame / "operator-assessment.json")
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
            "frame operator assessment is not usable")
    for name in ("model.json", "row-identities.json", "operators.npz"):
        require(pins[label(frame / name)] == assessment["output_sha256"][name],
                "operator assessment/output mismatch")

    model, rows = read(frame / "model.json"), read(frame / "row-identities.json")
    require([row["row"] for row in rows] == list(range(len(rows))), "noncontiguous raw row ordering")
    moves = {row["axis_id"]: row for row in model["owner_authorized_screw_movements"]}
    require(set(moves) == MOVED, "expected four owner-authorized upper movements")
    axial = [row for row in rows if row["ownership"]["role"] == AXIAL]
    lateral = [row for row in rows if row["ownership"]["role"] == LATERAL]
    require(len(axial) == 66 and len(lateral) == 132, "66-screw scalar census changed")
    groups = defaultdict(list)
    for row in lateral:
        groups[row["row_id"].split("/")[0]].append(row)
    require(set(groups) == {row["row_id"].split("/")[0] for row in axial},
            "axial/lateral identities differ")
    retained = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    positions = {row["row"]: i for i, row in enumerate(retained)}
    laws = comparison["panel_screw_stiffness_n_per_mm"]
    require(laws["product_laws_measured"] is False, "unexpected product-law claim")
    stiffness = {}
    for selected, kind in ((axial, "withdrawal"), (lateral, "lateral_components")):
        values = np.asarray(laws[kind], dtype=float)
        require(values.shape == (len(selected),) and np.isfinite(values).all()
                and (values > 0).all(), "invalid declared screw stiffness")
        require(np.array_equal(laws["source_" + kind],
                               [row["law"]["stiffness_N_per_mm"] for row in selected]),
                "source law/row ordering mismatch")
        stiffness.update({row["row"]: float(k) for row, k in zip(selected, values, strict=True)})

    records, panel_counts, maximum_law_error = [], Counter(), 0.0
    with np.load(frame / "operators.npz", allow_pickle=False) as operators, \
            np.load(source / "response.npz", allow_pickle=False) as response:
        D = operators["D"]
        require(D.shape == (len(rows), 6 * len(model["body_names"])), "rigid map dimensions differ")
        for state in comparison["states"]:
            case, gap = state["case_id"], state["gap_scale"]
            tag = case + ("_gap" if gap else "_zero")
            force, q = response[tag + "_raw_force_n"], response[tag + "_lumped_q_mm"]
            require(force.shape == (len(rows),) and q.ndim == 1 and len(q) >= len(retained)
                    and np.isfinite(force).all() and np.isfinite(q).all(), "invalid saved force/motion")
            for tie in axial:
                axis = tie["row_id"].split("/")[0]
                group = [*groups[axis], tie]
                require(len(group) == 3, "missing lateral screw component")
                hosts = {tie["ownership"][key] for key in ("first_body", "second_body")}
                panels = [body for body in hosts if body.startswith(("main_", "kicker_"))]
                require(len(panels) == 1 and len(hosts) == 2, "ambiguous panel receiver")
                panel = panels[0]
                receiver = (hosts - {panel}).pop()
                require(all({row["ownership"][key] for key in ("first_body", "second_body")} == hosts
                            and np.linalg.norm(np.array(row["ownership"]["point_mm"])
                                               - tie["ownership"]["point_mm"]) < 1e-6
                            for row in group), "screw components have different hosts/datums")
                relocated = axis in moves
                require(all(bool(row.get("station_reprojected_after_owner_authorization")) == relocated
                            for row in group), "relocation row flags differ")
                if relocated:
                    require(receiver == moves[axis]["after"]["receiver_member"]
                            and panel == moves[axis]["after"]["panel_member"],
                            "moved receiver differs from the new operator model")
                ids = [row["row"] for row in group]
                block = 6 * model["body_names"].index(panel)
                basis = D[ids, block:block + 3]
                require(np.max(np.abs(basis @ basis.T - np.eye(3))) < 1e-10,
                        "screw component basis is not orthonormal")
                relative = q[[positions[row] for row in ids]]
                expected = [stiffness[row] * (max(0.0, opening) if row == tie["row"] else opening)
                            for row, opening in zip(ids, relative, strict=True)]
                error = float(np.max(np.abs(force[ids] - expected)))
                maximum_law_error = max(maximum_law_error, error)
                require(error < 1e-4 and force[tie["row"]] >= -1e-4,
                        "saved force/opening is inconsistent with the declared screw law")
                tension = max(0.0, float(force[tie["row"]]))
                signed = -basis.T @ force[ids]
                point = tie["ownership"]["point_mm"]
                records.append({
                    "source": label(source), "case_id": case, "gap_scale": gap,
                    "source_state_status": state["status"], "axis_id": axis,
                    "panel": panel, "receiver": receiver, "axis_relocated": relocated,
                    "previous_receiver": (moves[axis]["before"]["receiver_member"] if relocated else receiver),
                    "point_x_mm": point[0], "point_y_mm": point[1], "point_z_mm": point[2],
                    "axial_raw_signed_n": float(force[tie["row"]]),
                    "head_pullthrough_demand_n": tension, "withdrawal_demand_n": tension,
                    "lateral_1_signed_n": float(force[ids[0]]),
                    "lateral_2_signed_n": float(force[ids[1]]),
                    "lateral_resultant_n": float(np.linalg.norm(force[ids[:2]])),
                    "relative_axial_signed_mm": float(relative[2]),
                    "relative_opening_mm": max(0.0, float(relative[2])),
                    "relative_lateral_1_signed_mm": float(relative[0]),
                    "relative_lateral_2_signed_mm": float(relative[1]),
                    "withdrawal_stiffness_hypothesis_n_per_mm": stiffness[tie["row"]],
                    "force_on_panel_x_n": float(signed[0]),
                    "force_on_panel_y_n": float(signed[1]),
                    "force_on_panel_z_n": float(signed[2]),
                })
                panel_counts[panel] += 1
    require(len(records) == 792 and len({(r["case_id"], r["gap_scale"], r["axis_id"])
                                        for r in records}) == 792, "incomplete screw-state census")
    require(panel_counts == Counter({**{f"main_{level}_{side}": 144
                                       for level in ("upper", "lower") for side in ("left", "right")},
                                     "kicker_left": 108, "kicker_right": 108}),
            "12-per-main/9-per-kicker census changed")
    return records, {
        "source": label(source), "frame_operator_directory": label(frame),
        "comparison_sha256": pins[label(comparison_path)],
        "response_sha256": comparison["response_sha256"], "force_state_scope": scope,
        "load_metadata": {key: comparison[key] for key in (
            "climber_load_scale", "source_climber_weight_lb", "comparison_climber_weight_lb",
            "horizontal_force_scaled_with_climber", "dead_load_factor") if key in comparison},
        "source_operator_model_load_metadata": {key: value for key, value in model.items()
                                                 if "load" in key or "climber" in key},
        "owner_authorized_screw_movements": list(moves.values()),
        "saved_frame_states": 12, "screw_states": 792,
        "maximum_screw_force_law_error_n": maximum_law_error,
    }


def summary(records, scenarios):
    peak = max(records, key=lambda row: row["head_pullthrough_demand_n"])
    result = {
        "screw_states": len(records), "same_state_peak_head_withdrawal": peak,
        "same_state_peak_lateral": max(records, key=lambda row: row["lateral_resultant_n"]),
        "same_state_peak_opening": max(records, key=lambda row: row["relative_opening_mm"]),
        "generic_reference_comparisons": {},
    }
    for kind, refs in scenarios.items():
        result["generic_reference_comparisons"][kind] = [
            {**ref, "maximum_demand_reference_ratio": peak["head_pullthrough_demand_n"] / ref["reference_n"],
             "states_exceeding_declared_reference": sum(row["head_pullthrough_demand_n"] > ref["reference_n"]
                                                        for row in records),
             "qualified_connection_capacity": False}
            for ref in refs
        ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", type=Path, required=True,
                        help="completed frame packet; repeat for multiple load scenarios")
    parser.add_argument("--output", type=Path, required=True,
                        help="new directory under upper-corner-screw-layout/rawlocal/head-check")
    args = parser.parse_args()
    output = args.output.resolve()
    allowed = (HERE / "rawlocal/head-check").resolve()
    require(output.is_relative_to(allowed) and output != allowed,
            "choose a fresh attempt directory under rawlocal/head-check")
    require(not output.exists(), "preserve the existing output directory")
    pins, sources, all_records, seen = {}, [], [], set()
    scenarios = reference_scenarios(pins)
    for source in args.source:
        records, metadata = consume(source, pins)
        require(metadata["source"] not in seen, "duplicate source packet")
        seen.add(metadata["source"])
        scopes = {"all_saved_states": records,
                  "zero_gap": [row for row in records if row["gap_scale"] == 0],
                  "nominal_gap": [row for row in records if row["gap_scale"] == 1]}
        metadata["demand_summaries"] = {name: summary(rows, scenarios) for name, rows in scopes.items()}
        metadata["panel_nominal_gap_summaries"] = {
            panel: summary([row for row in scopes["nominal_gap"] if row["panel"] == panel], scenarios)
            for panel in sorted({row["panel"] for row in records})
        }
        sources.append(metadata)
        all_records.extend(records)
    producer = sha(Path(__file__))
    report = {
        "schema": "relocated_panel_screw_head_withdrawal_reference/v1",
        "producer_sha256": producer, "source_sha256": pins,
        "source_packets": sources, "total_screw_states": len(all_records),
        "claim_boundary": {
            "hillman_resistance_established": False, "qualified_connection_capacity": False,
            "lateral_or_combined_reference_transferred": False, "complete_joint_acceptance": False,
            "formal_criterion_pass_adopted": False, "physical_release": False,
            "frame_or_native_solve_run": False, "geometry_changed_by_consumer": False,
        },
        "limits": [
            "Generic head and side-grain withdrawal assumptions are reused from attempt08; no Hillman rating or end-use adjustment is adopted.",
            "Head and withdrawal both receive the same saved axial tension; lateral demand is reported at that same state, without assigning lateral or combined capacity.",
            "The four moved axes use current operator ownership, including the two inner corners now entering the top rail. Previous grain-direction lateral references are not reused.",
            "Motion is the saved representative relative opening, not a unique pose, a bounded-seating motion envelope, or an installed measurement.",
            "No old force allocation, LP redistribution or frame solve was replayed. A lighter-user comparison does not qualify the 250 lb dynamic requirement.",
        ],
    }
    output.mkdir(parents=True)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / "comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    with (output / "screw-states.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(all_records[0]))
        writer.writeheader()
        writer.writerows(all_records)
    receipt = {
        "schema": "relocated_panel_head_check_receipt/v1", "producer_sha256": producer,
        "source_sha256": pins, "source_packets": len(sources), "screw_states": len(all_records),
        "output_sha256": {name: sha(output / name) for name in
                          ("comparison.json", "screw-states.csv", "producer.py.snapshot")},
        "complete_joint_acceptance": False, "physical_release": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": label(output), "screw_states": len(all_records),
                      "receipt_sha256": sha(output / "receipt.json")}, indent=2))


if __name__ == "__main__":
    main()
