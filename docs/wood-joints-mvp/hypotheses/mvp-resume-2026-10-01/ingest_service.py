"""Join the completed service-joint worksheet and existing Hillman evidence.

Read saved evidence and validate its bindings. Do not rerun studies, edit the
worker's packet, or transfer its conditional result into joint acceptance.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = HERE.parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / "service-and-hillman-ingestion.json"
    if output.exists():
        raise ValueError("preserve the existing ingestion record")
    pins, counts = {}, {}

    def bind(label, records, folder):
        counts[label] = len(records)
        for name, digest in records.items():
            path = Path(name)
            if not path.is_absolute():
                path = folder / path
            path = path.resolve()
            if not path.is_file() or sha(path) != digest:
                raise ValueError(f"changed saved source: {path}")
            if path in pins and pins[path] != digest:
                raise ValueError(f"contradictory source binding: {path}")
            pins[path] = digest

    service = BASE / "upper-left-service-frame-clearance-2026-10-01"
    working = BASE / "upper-left-service-transfer-preflight-2026-10-01"
    motion = BASE / "upper-left-service-motion-sensitivity-2026-10-01"
    hillman = BASE / "current-panel-receiver-transfer-2026-10-01"
    receipt = read(service / "completion-receipt.json")
    final = read(service / "comparison-final.json")
    audit = read(service / "parent-validation.json")
    bind("latest_worker_outputs", receipt["output_sha256"], service)
    bind(
        "preserved_worker_initial_packet",
        receipt["preserved_original_working_packet_sha256"],
        working,
    )
    bind("worker_frame_inputs", final["source_sha256"], ROOT)
    bind(
        "worker_report_and_vectors",
        {
            "comparison-final.json": audit["report_sha256"],
            "response-vectors-final.npz": audit["vectors_sha256"],
        },
        service,
    )
    for lane in (working, motion):
        bind(lane.name, read(lane / "parent-validation.json")["artifact_sha256"], lane)
    bind("motion_source_inputs", read(motion / "comparison.json")["source_pins"], ROOT)
    bind(
        "previous_hillman_inputs",
        {r["path"]: r["sha256"] for r in read(hillman / "source-pins.json")["sources"]},
        ROOT,
    )
    previous = read(hillman / "receiver-transfer.json")
    bind(
        "hillman_source_manifest",
        {"source-pins.json": previous["source_pins_sha256"]},
        hillman,
    )
    if (
        final["state_count"] != 252
        or len(final["states"]) != 252
        or audit["states_checked"] != 252
    ):
        raise ValueError("incomplete service comparison")
    if any(s["status"] != "CONDITIONAL_FIXED_FLOOR_BRANCH" for s in final["states"]):
        raise ValueError("service worksheet contains a refused state")
    if final["complete_joint"] != "HOLD" or final["release"]:
        raise ValueError("unexpected service acceptance claim")
    axes = {a["axis_id"]: a for a in previous["inventory"]["axes"]}
    current = read(
        BASE / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
    )
    screws = {
        r["axis_id"]: r for r in current["connections"] if r["kind"] == "panel_screw"
    }
    if len(axes) != 66 or axes.keys() != screws.keys():
        raise ValueError("different Hillman inventories")
    for axis, a in axes.items():
        s = screws[axis]
        if (
            s["receiver_member_ids"] != [a["panel_member"], a["receiver_member"]]
            or s["source_point_xyz_mm"] != a["origin_global_xyz_mm"]
        ):
            raise ValueError(f"Hillman receiver or station changed: {axis}")
    rows_path = HERE / "corner-frame-attempt01/row-identities.json"
    rows = read(rows_path)
    role_counts = {
        role: sum(r["ownership"]["role"] == role for r in rows)
        for role in (
            "panel_screw_lateral_plane",
            "non_qualifying_parametric_screw_withdrawal",
        )
    }
    if role_counts != {
        "panel_screw_lateral_plane": 132,
        "non_qualifying_parametric_screw_withdrawal": 66,
    }:
        raise ValueError("corrected frame omitted a Hillman component")
    right_axes = [a for a in axes.values() if a["panel_member"] == "main_upper_right"]
    ledger = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
    for path in (
        service / "completion-receipt.json",
        hillman / "receiver-transfer.json",
        rows_path,
        ledger,
    ):
        pins[path] = sha(path)
    record = {
        "schema": "service_joint_and_hillman_parent_ingestion/v1",
        "producer_sha256": sha(Path(__file__)),
        "status": "INGESTED_SAVED_EVIDENCE_WITH_MATCHING_SOURCE_BINDINGS",
        "checked_reference_counts": counts,
        "unique_bound_paths": len(pins),
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): h
            for p, h in pins.items()
        },
        "left_service": {
            "block": "left_service_outer_upper_cleat",
            "geometry_decision": "retain reviewed geometry for development",
            "load_scale": final["load_scale"],
            "cases": sorted({s["case"] for s in final["states"]}),
            "state_count": 252,
            "frozen_lateral_law_summaries": [
                s for s in final["summary"] if s["scenario"] == "frozen source"
            ],
            "saved_vector_audit": audit,
            "remaining": [
                "complete joint resistance",
                "conditional Hillman sharing",
                "missing cases in this worker worksheet",
                "installation and removal",
            ],
        },
        "hillman": {
            "inventory_counts": previous["inventory"]["counts"],
            "action_counts": previous["actions"]["counts"],
            "claim_boundary": previous["claim_boundary"],
            "corrected_frame_component_counts": role_counts,
            "right_upper_panel_axes": [
                {
                    "axis_id": a["axis_id"],
                    "panel": a["panel_member"],
                    "receiver": a["receiver_member"],
                }
                for a in right_axes
            ],
            "required_treatment": "include panel stiffness, both lateral screw components, axial ties and panel contact in the coupled joint calculation; record conditional properties explicitly",
            "forbidden_double_count": "do not add an independent screw capacity to bolt resistance after the frame already distributes actions through those same screws",
        },
        "integration_decisions": [
            "Use the worker's coupled frame clearance method for the right-corner decision before adopting stronger hardware.",
            "Keep the left service cleat and its four axes; its coupled result supports this development choice within the recorded three-case assumptions.",
            "Parent's preserved six-case zero-withdrawal result already addresses the worker's proposed zero-credit screen: it stops on missing upper-panel normal restraint.",
            "Continue the simpler MVP with panel assumptions explicit, as directed by the revised goal; formal Hillman qualification remains unresolved.",
        ],
        "native_run": False,
        "software_tests_run": False,
        "worker_files_changed": False,
        "reviewed_geometry_changed": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    for path, digest in pins.items():
        if sha(path) != digest:
            raise ValueError(f"source changed during ingestion: {path}")
    output.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "status": record["status"],
                "unique_bound_paths": len(pins),
                "right_upper_panel_axes": len(right_axes),
                "output_sha256": sha(output),
            }
        )
    )


if __name__ == "__main__":
    main()
