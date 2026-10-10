#!/usr/bin/env python3
"""Bind proposed stock-cut arithmetic to current finished geometry evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from nesting import Blank, nest_blanks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
MANIFEST = (
    BASE
    + "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
PROPOSALS = (
    BASE + "current-timber-source-yield-attempt01/current-timber-source-yield.json"
)
ENVELOPES = str((HERE / "envelopes.json").relative_to(ROOT))
ENVELOPE_PRODUCER = str((HERE / "envelopes.py").relative_to(ROOT))
NESTING_PRODUCER = str((HERE / "nesting.py").relative_to(ROOT))
OUTPUT = HERE / "cut-scenarios.json"
SECTION_DIMENSIONS = {"4x4": [88.9, 88.9], "4x6": [88.9, 139.7], "2x6": [38.1, 139.7]}
NOMINAL_LENGTH_MM = {8: 2438.4, 10: 3048.0, 12: 3657.6, 16: 4876.8}
PINNED = {
    INVENTORY: "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    MANIFEST: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    PROPOSALS: "2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c",
    ENVELOPES: "0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01",
    ENVELOPE_PRODUCER: "a4aa9e6d8d22178bdae28cab4c829d1f45fb5633575dd7119fe57cf03b374b0d",
    NESTING_PRODUCER: "c601d895319934cc42641e843470a413d70ece804141ba8b7ef3dd55936550b6",
}


class ReconciliationError(ValueError):
    """The proposed cut basis is not bound to the reviewed source evidence."""


def require(condition, message):
    if not condition:
        raise ReconciliationError(message)


def finite(value):
    require(
        type(value) in (int, float) and math.isfinite(value),
        "nonfinite or invalid numeric value",
    )
    return float(value)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pinned(root, relative):
    require(relative in PINNED, f"consumer input is not frozen: {relative}")
    path = root / relative
    require(
        path.is_file() and sha(path) == PINNED[relative],
        f"missing or changed input: {relative}",
    )
    return json.loads(path.read_bytes())


def section(values):
    require(
        isinstance(values, (list, tuple)) and len(values) == 2,
        "invalid section dimensions",
    )
    result = sorted(finite(value) for value in values)
    require(result[0] > 0, "nonpositive section dimension")
    return result


def near(actual, expected, label):
    require(abs(finite(actual) - finite(expected)) <= 1e-6, label)


def same_section(actual, expected, label):
    for a, b in zip(section(actual), section(expected), strict=True):
        near(a, b, label)


def unique(rows, key):
    result = {}
    for row in rows:
        name = row[key]
        require(
            isinstance(name, str) and name and name not in result,
            f"invalid or duplicate {key}: {name}",
        )
        result[name] = row
    return result


def stock_class(dimensions):
    dims = section(dimensions)
    matches = [
        name
        for name, target in SECTION_DIMENSIONS.items()
        if all(abs(a - b) <= 1e-6 for a, b in zip(dims, target, strict=True))
    ]
    require(
        len(matches) == 1, "source section does not identify one declared stock class"
    )
    return matches[0]


def prepared_box_is_inside_original(observed):
    original = observed["original_stock_containment"]["proposed_stock_bounds_g_q_r_mm"]
    prepared = observed["prepared_section_containment"][
        "proposed_stock_bounds_g_q_r_mm"
    ]
    require(len(original) == len(prepared) == 3, "stock bounds do not have three axes")
    for outer, inner in zip(original, prepared, strict=True):
        require(len(outer) == len(inner) == 2, "stock bounds are not intervals")
        outer_low, outer_high = (finite(value) for value in outer)
        inner_low, inner_high = (finite(value) for value in inner)
        require(
            outer_low <= outer_high and inner_low <= inner_high,
            "stock bounds contain an inverted interval",
        )
        require(
            outer_low <= inner_low + 1e-6 and inner_high <= outer_high + 1e-6,
            "prepared box does not lie inside its original stock box",
        )


def expected_records(inventory, manifest, proposals):
    for label, document in (("manifest", manifest), ("block proposals", proposals)):
        require(
            document["candidate"] == CANDIDATE
            and document["geometry_revision_id"] == REVISION,
            f"wrong {label} candidate or revision",
        )
    frames = unique(
        [row for row in inventory["parts"] if row["kind"] == "timber"], "part_id"
    )
    blocks = unique(manifest["candidate_blocks"], "part_id")
    proposal_map = unique(proposals["candidate_block_records"], "part_id")
    members = unique(manifest["physical_members"], "member_id")
    require(len(frames) == 20 and len(blocks) == 24, "wrong 20-frame/24-block coverage")
    require(
        set(blocks) == set(proposal_map),
        "block proposals do not match current manifest IDs",
    )
    require(not set(frames).intersection(blocks), "frame/block identities overlap")
    require(
        (set(frames) | set(blocks)) <= set(members),
        "current manifest omits proposed stock member",
    )
    result = {}
    for name, source in frames.items():
        dimensions = source["source_blank_dimensions_mm"]
        require(len(dimensions) == 3, "source frame blank dimensions are incomplete")
        length = finite(dimensions[0])
        same_section(
            dimensions[1:],
            source["actual_source_section_mm"],
            "frame blank/section mismatch",
        )
        require(length > 0, "nonpositive source frame length")
        result[name] = {
            "member_id": name,
            "member_kind": "timber",
            "stock_class": stock_class(dimensions[1:]),
            "stock_blank_length_mm": length,
            "original_stock_section_mm": section(dimensions[1:]),
            "prepared_section_mm": None,
            "frame_status": "rebuilt"
            if "current_rebuilt_host" in members[name]["composition_roles"]
            else "source_only",
            "source_blank_basis": "source inventory length/section used as a proposed starting-stock scenario",
            "current_finished_step_binding": members[name][
                "current_finished_step_binding"
            ],
        }
    for name, proposal in proposal_map.items():
        cls = proposal["proposed_stock_class"]
        require(cls in SECTION_DIMENSIONS, "unsupported proposed block stock class")
        length = finite(proposal["proposed_blank_stock_length_mm"])
        require(length > 0, "nonpositive proposed block length")
        prepared = section(proposal["proposed_blank_cross_section_mm"])
        original = SECTION_DIMENSIONS[cls]
        require(
            all(a <= b + 1e-6 for a, b in zip(prepared, original, strict=True)),
            "block section exceeds starting stock",
        )
        rip = (
            prepared
            if any(abs(a - b) > 1e-6 for a, b in zip(prepared, original, strict=True))
            else None
        )
        result[name] = {
            "member_id": name,
            "member_kind": "candidate_block",
            "stock_class": cls,
            "stock_blank_length_mm": length,
            "original_stock_section_mm": original,
            "prepared_section_mm": rip,
            "frame_status": None,
            "source_blank_basis": "preserved stock-pattern proposal reconciled to current member identity",
            "current_finished_step_binding": members[name][
                "current_finished_step_binding"
            ],
        }
    require(
        sum(row["prepared_section_mm"] is not None for row in result.values()) == 4,
        "the four prepared 4x6 section-rip proposals are not preserved",
    )
    require(
        sum(row["frame_status"] == "source_only" for row in result.values()) == 4,
        "source-only versus rebuilt frame coverage changed",
    )
    return result


def reconcile(envelope_report, expected):
    require(
        envelope_report["candidate"] == CANDIDATE
        and envelope_report["geometry_revision_id"] == REVISION,
        "wrong envelope candidate or revision",
    )
    records = unique(envelope_report["records"], "member_id")
    require(
        set(records) == set(expected),
        "envelope report does not cover the exact current 44-piece set",
    )
    eligible, excluded, schedule = [], [], []
    for name in sorted(expected):
        source, observed = expected[name], records[name]
        expected_kind = (
            "frame_timber" if source["member_kind"] == "timber" else "candidate_block"
        )
        require(
            observed["member_kind"] == expected_kind, f"{name} member kind mismatch"
        )
        require(
            observed["stock_class"] == source["stock_class"],
            f"{name} stock class mismatch",
        )
        near(
            observed["stock_blank_length_mm"],
            source["stock_blank_length_mm"],
            f"{name} blank length mismatch",
        )
        same_section(
            observed["original_stock_section_mm"],
            source["original_stock_section_mm"],
            f"{name} original section mismatch",
        )
        prepared = observed.get("prepared_section_mm")
        if source["prepared_section_mm"] is not None:
            require(prepared is not None, f"{name} prepared section omitted")
            same_section(
                prepared,
                source["prepared_section_mm"],
                f"{name} prepared section mismatch",
            )
        elif prepared is not None:
            same_section(
                prepared,
                source["original_stock_section_mm"],
                f"{name} unexpected section rip",
            )
        binding = source["current_finished_step_binding"]
        require(
            observed["current_finished_step_path"] == binding["path"]
            and observed["current_finished_step_sha256"] == binding["file_sha256"],
            f"{name} current STEP binding mismatch",
        )
        if source["member_kind"] == "timber":
            require(
                observed["frame_status"] == source["frame_status"],
                f"{name} frame status mismatch",
            )
        status = observed["containment_status"]
        require(
            status in {"CONTAINED", "INCOMPATIBLE", "AMBIGUOUS"},
            f"{name} unknown containment status",
        )
        detail_statuses = [observed["original_stock_containment"]["status"]]
        if prepared is not None:
            detail = observed.get("prepared_section_containment")
            require(detail is not None, f"{name} prepared section containment omitted")
            detail_statuses.append(detail["status"])
        require(
            all(
                item in {"CONTAINED", "INCOMPATIBLE", "AMBIGUOUS"}
                for item in detail_statuses
            ),
            f"{name} unknown detail containment status",
        )
        combined = (
            "AMBIGUOUS"
            if "AMBIGUOUS" in detail_statuses
            else ("INCOMPATIBLE" if "INCOMPATIBLE" in detail_statuses else "CONTAINED")
        )
        require(status == combined, f"{name} overall and detailed containment disagree")
        if status == "CONTAINED" and source["prepared_section_mm"] is not None:
            prepared_box_is_inside_original(observed)
        row = {
            key: value
            for key, value in source.items()
            if key != "current_finished_step_binding"
        }
        row.update(
            current_finished_step_path=binding["path"],
            current_finished_step_sha256=binding["file_sha256"],
            containment_status=status,
            stock_geometry_is_proposed=True,
            delivered_grade_observed=False,
            post_rip_grade_assigned=False if source["prepared_section_mm"] else None,
        )
        schedule.append(row)
        if status == "CONTAINED":
            eligible.append(
                Blank(
                    name,
                    source["stock_blank_length_mm"],
                    source["stock_class"],
                    tuple(source["prepared_section_mm"])
                    if source["prepared_section_mm"]
                    else None,
                )
            )
        else:
            excluded.append({"member_id": name, "containment_status": status})
    return schedule, eligible, excluded


def scenarios(blanks, excluded):
    results = []
    for feet_options in ((8,), (10,), (12,), (16,), (8, 10, 12, 16)):
        for trim in (0.0, 10.0, 20.0):
            stock = {
                cls: [NOMINAL_LENGTH_MM[feet] for feet in feet_options]
                for cls in SECTION_DIMENSIONS
            }
            result = nest_blanks(
                blanks,
                stock,
                crosscut_kerf_mm=3.2,
                end_trim_start_mm=trim,
                end_trim_end_mm=trim,
            )
            results.append(
                {
                    "scenario_id": "stock-"
                    + "-".join(str(ft) for ft in feet_options)
                    + f"ft-trim-{trim:g}mm",
                    "nominal_stock_length_options_ft": list(feet_options),
                    "nominal_stock_length_options_mm_by_original_section": stock,
                    "crosscut_separation_kerf_mm_per_blank": 3.2,
                    "end_trim_start_mm_including_trim_cut_loss": trim,
                    "end_trim_end_mm_including_trim_cut_loss": trim,
                    "defect_and_receiving_loss_allowance_mm": 0.0,
                    "section_cleanup_allowance_mm": 0.0,
                    "excluded_by_stock_geometry": excluded,
                    "all_current_44_lengths_arithmetically_placed": not excluded
                    and len(blanks) == 44
                    and result.complete,
                    "packing": asdict(result),
                    "purchase_quantities_or_optimum_established": False,
                }
            )
    return results


def build_report(root=ROOT):
    for producer in (ENVELOPE_PRODUCER, NESTING_PRODUCER):
        require(
            producer in PINNED and sha(root / producer) == PINNED[producer],
            f"unfrozen or changed producer: {producer}",
        )
    inventory, manifest, proposals, envelopes = [
        read_pinned(root, path) for path in (INVENTORY, MANIFEST, PROPOSALS, ENVELOPES)
    ]
    expected = expected_records(inventory, manifest, proposals)
    schedule, blanks, excluded = reconcile(envelopes, expected)
    for row in schedule:
        path = root / row["current_finished_step_path"]
        require(
            path.is_file() and sha(path) == row["current_finished_step_sha256"],
            f"changed current STEP: {row['member_id']}",
        )
    cases = scenarios(blanks, excluded)
    return {
        "schema": "current-stock-envelope-cut-scenarios/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "status": "SOURCE_BOUND_PROPOSED_STOCK_CUT_ARITHMETIC"
        if not excluded
        else "PARTIAL_PROPOSED_STOCK_GEOMETRY_COVERAGE",
        "producer_sha256": sha(Path(__file__)),
        "source_pins": [
            {"path": path, "sha256": digest} for path, digest in sorted(PINNED.items())
        ],
        "piece_schedule": schedule,
        "geometry_exclusions": excluded,
        "scenarios": cases,
        "counts": {
            "frame_records": 20,
            "block_records": 24,
            "proposed_records": len(schedule),
            "geometry_eligible_records": len(blanks),
            "geometry_excluded_records": len(excluded),
            "ripped_4x6_block_records": 4,
            "scenarios": len(cases),
        },
        "method_limits": [
            "Stock transforms are explicit proposals, not identities of saved current raw_hosts.",
            "Frame lengths are source-blank proposals; current finished grain spans are not substituted.",
            "One separation kerf is reserved for every cut blank, including a trailing reserve.",
            "Both trim allowances include their declared trim-cut losses; zero is an optimistic sensitivity.",
            "Cut full-section blanks first, then prepare the four section rips; remnants retain original stock section.",
            "First-fit decreasing is a deterministic heuristic, not an optimal schedule or stock order.",
            "Zero defect, receiving and cleanup allowances do not establish actual usable yield.",
        ],
        "claim_boundary": {
            "current_finished_geometry_modified": False,
            "native_solve_executed": False,
            "lumber_product_or_price_selected": False,
            "actual_stock_or_grain_observed": False,
            "post_rip_grade_assigned": False,
            "machining_sequence_complete": False,
            "strength_or_complete_joint_accepted": False,
            "physical_work_released": False,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    payload = canonical(report)
    if args.write:
        require(not OUTPUT.exists(), "refusing to overwrite frozen cut-scenarios.json")
        with OUTPUT.open("xb") as stream:
            stream.write(payload)
    else:
        require(
            OUTPUT.is_file() and OUTPUT.read_bytes() == payload,
            "cut-scenarios.json differs from canonical pinned replay",
        )
    print(
        json.dumps(
            {
                "mode": "write" if args.write else "verify",
                "status": report["status"],
                "counts": report["counts"],
                "cut_scenarios_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
