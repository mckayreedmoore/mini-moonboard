#!/usr/bin/env python3
"""Export timber blank identities from frozen assembly and stock records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01"
ASSEMBLY = f"{BASE}/assembly-package"
STOCK = (
    "docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01"
)
DEFAULT_OUTPUT = HERE / "rawlocal/blank-cut-list/attempt01"
SOURCE_SHA256 = {
    f"{ASSEMBLY}/rawlocal/reconciled-assembly.json": "2bb4e95fbd2a7ec158d24bc12860e0961000fdb9f9af7ffd8504ef966b2aee87",
    f"{ASSEMBLY}/rawlocal/bodies.csv": "9e54e5da262074e98e84e2c846e37d81e905791d7f619b3253142f4dd37f14bc",
    f"{ASSEMBLY}/rawlocal/stock-classes.csv": "c792f7c8d8e58a498d1ebed246b88aa0df3d916b6977a1b317d494637554a3f7",
    f"{ASSEMBLY}/rawlocal/stock-scenarios.json": "f10b683f0e23cf303ea9163468fa929f9a5850f649a54cf28752b1ebacf26cf8",
    f"{STOCK}/cut-scenarios.json": "9a450e0b6bca73cf62b95f5759bfcacffd9d682b3c465df3fbc27327723d6978",
    f"{STOCK}/envelopes.json": "0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01",
    f"{BASE}/top-corner-correction/proposal.json": "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
}
TOP_CLEATS = {"top_outer_left_cleat", "top_outer_right_cleat"}
TOP_OVERRIDES = TOP_CLEATS | {"base_side_left", "base_side_right"}
SECTION_RIPS = {
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
}
GRAIN_REFERENCES = {
    "GX": [1.0, 0.0, 0.0],
    "GY": [0.0, 1.0, 0.0],
    "GZ": [0.0, 0.0, 1.0],
    "GS": [0.0, 0.6427876096865427, 0.7660444431189752],
    "GL": [0.0, -0.23915183196324322, 0.9709821838059773],
    "GN+": [0.0, -0.766044443118978, 0.6427876096865394],
    "GN-": [0.0, 0.766044443118978, -0.6427876096865394],
}
UNAVAILABLE_OPERATIONS = (
    "bevel_or_miter_angles_deg",
    "profile_cut_locations_mm",
    "rip_face_and_setup",
    "pilot_and_bore_instructions",
    "service_machining_instructions",
    "machining_tolerance_mm",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()


def index(
    rows: list[dict[str, Any]], key: str, count: int
) -> dict[str, dict[str, Any]]:
    result = {row[key]: row for row in rows}
    require(len(rows) == len(result) == count, f"expected {count} unique {key} records")
    return result


def csv_rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode())))


def numbers(value: str) -> list[float] | None:
    return [float(part) for part in value.split(";")] if value else None


def grain_reference(vector: list[float]) -> str:
    for name, reference in GRAIN_REFERENCES.items():
        if len(vector) == 3 and all(
            abs(a - b) < 1e-8 for a, b in zip(vector, reference, strict=True)
        ):
            return name
    raise ValueError(f"unmapped conditional grain vector: {vector}")


def source_bytes() -> tuple[dict[str, bytes], dict[str, str]]:
    data = {}
    pins = dict(SOURCE_SHA256)
    for relative, expected in pins.items():
        data[relative] = (ROOT / relative).read_bytes()
        require(digest(data[relative]) == expected, f"source hash mismatch: {relative}")
    proposal = json.loads(data[f"{BASE}/top-corner-correction/proposal.json"])
    overrides = proposal["proposal_step_sha256"]
    require(
        {Path(path).stem for path in overrides} == TOP_OVERRIDES,
        "four top STEP overrides changed",
    )
    for relative, expected in overrides.items():
        require(
            relative == f"{BASE}/top-corner-correction/{Path(relative).stem}.step",
            f"unexpected override path: {relative}",
        )
        require(
            digest((ROOT / relative).read_bytes()) == expected,
            f"override hash mismatch: {relative}",
        )
        pins[relative] = expected
    return data, pins


def csv_bytes(rows: list[dict[str, Any]], columns: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def dimensions(values: list[float] | None) -> str:
    return ";".join(str(value) for value in values) if values is not None else ""


def display(values: list[float]) -> str:
    return " × ".join(f"{value:.3f}" for value in values)


def build() -> tuple[dict[str, bytes], dict[str, str], dict[str, Any]]:
    data, pins = source_bytes()
    assembly = json.loads(data[f"{ASSEMBLY}/rawlocal/reconciled-assembly.json"])
    envelopes = json.loads(data[f"{STOCK}/envelopes.json"])
    cuts = json.loads(data[f"{STOCK}/cut-scenarios.json"])
    scenario_source = json.loads(data[f"{ASSEMBLY}/rawlocal/stock-scenarios.json"])
    proposal = json.loads(data[f"{BASE}/top-corner-correction/proposal.json"])
    bodies = index(assembly["bodies"], "body_id", 50)
    envelope_by_id = index(envelopes["records"], "member_id", 44)
    cut_by_id = index(cuts["piece_schedule"], "member_id", 44)
    body_csv = index(csv_rows(data[f"{ASSEMBLY}/rawlocal/bodies.csv"]), "body_id", 50)
    class_csv = index(
        csv_rows(data[f"{ASSEMBLY}/rawlocal/stock-classes.csv"]), "stock_class", 3
    )
    overrides = {
        Path(path).stem: (path, sha)
        for path, sha in proposal["proposal_step_sha256"].items()
    }
    top_proposals = index(proposal["proposals"], "block", 2)
    require(set(top_proposals) == TOP_CLEATS, "two top cleat identities changed")
    require(set(bodies) == set(body_csv), "body JSON/CSV identities differ")
    require(
        set(envelope_by_id) == set(cut_by_id), "stock-envelope/cut identities differ"
    )
    require(
        assembly["body_counts"]
        == {
            "connector_blocks": 24,
            "frame_timber": 20,
            "panels": 6,
            "stock_blanks": 44,
            "total": 50,
        },
        "assembly body counts changed",
    )
    require(
        assembly["candidate"]
        == envelopes["candidate"]
        == cuts["candidate"]
        == "compact-floor-flush-wood-joints-development",
        "candidate identity mismatch",
    )
    require(
        assembly["source_revision"]
        == envelopes["geometry_revision_id"]
        == cuts["geometry_revision_id"]
        == proposal["source_revision"],
        "source revision mismatch",
    )

    timber = []
    plywood = []
    for member_id, body in bodies.items():
        saved = body_csv[member_id]
        require(
            saved["kind"] == body["kind"]
            and saved["stock_class"] == body["stock_class"],
            f"body CSV class/kind differs: {member_id}",
        )
        require(
            numbers(saved["stock_box_dimensions_mm"]) == body["proposed_stock_box_mm"]
            and numbers(saved["finished_dimensions_mm"])
            == body["local_dimensions"]["dimensions_mm"]
            and numbers(saved["prepared_stock_section_mm"])
            == body["prepared_stock_section_mm"]
            and saved["finished_dim_axes"].split(";")
            == body["local_dimensions"]["axes"],
            f"body CSV dimensions differ: {member_id}",
        )
        if body["source_scope"] == "panel":
            require(
                member_id not in envelope_by_id,
                f"panel also counted as timber: {member_id}",
            )
            plywood.append(
                {
                    "body_id": member_id,
                    "body_kind": "whole kicker"
                    if member_id.startswith("kicker_")
                    else "main panel",
                    "source_blank_dimensions_mm": body["proposed_stock_box_mm"],
                    "source_blank_dimension_scope": "source-inventory dimensions in recorded source order",
                    "recorded_local_envelope": body["local_dimensions"],
                    "envelope_scope": body["shape_source_scope"],
                    "factory_strength_axis_assignment": None,
                    "operation_facts": dict.fromkeys(UNAVAILABLE_OPERATIONS),
                    "actual": None,
                    "disposition": None,
                }
            )
            continue
        envelope = envelope_by_id[member_id]
        cut = cut_by_id[member_id]
        box = body["proposed_stock_box_mm"]
        grain = envelope["conditional_grain_axis_global_xyz"]
        prepared = body["prepared_stock_section_mm"]
        reduced = prepared is not None and any(
            abs(a - b) > 1e-6 for a, b in zip(prepared, box[:2], strict=True)
        )
        envelope_prepared = envelope["prepared_section_mm"]
        envelope_reduced = envelope_prepared is not None and any(
            abs(a - b) > 1e-6
            for a, b in zip(
                envelope_prepared, envelope["original_stock_section_mm"], strict=True
            )
        )
        require(
            cut["stock_blank_length_mm"] == envelope["stock_blank_length_mm"]
            and cut["stock_class"] == envelope["stock_class"]
            and cut["prepared_section_mm"]
            == (envelope_prepared if envelope_reduced else None),
            f"historical stock records differ: {member_id}",
        )
        if member_id in TOP_CLEATS:
            top = top_proposals[member_id]
            require(
                body["stock_class"] == "4x6"
                and box[:2] == top["proposed_section_X_T_mm"]
                and box[2] == top["grain_length_mm"]
                and prepared is None,
                f"top cleat replacement differs: {member_id}",
            )
        else:
            require(
                body["stock_class"] == cut["stock_class"]
                and box[:2] == cut["original_stock_section_mm"]
                and box[2] == cut["stock_blank_length_mm"]
                and prepared == cut["prepared_section_mm"],
                f"current stock row differs: {member_id}",
            )
        shape_path, shape_hash = overrides.get(
            member_id,
            (
                envelope["current_finished_step_path"],
                envelope["current_finished_step_sha256"],
            ),
        )
        require(
            shape_hash == body["shape_source_sha256"],
            f"shape binding differs: {member_id}",
        )
        timber.append(
            {
                "member_id": member_id,
                "member_kind": "frame timber"
                if body["kind"] == "frame timber"
                else "connector block",
                "quantity": 1,
                "source_stock_class": body["stock_class"],
                "source_section_mm": box[:2],
                "stock_blank_length_mm": box[2],
                "prepared_section_mm": prepared,
                "requires_source_section_rip": reduced,
                "recorded_finished_envelope": body["local_dimensions"],
                "grain_reference": grain_reference(grain),
                "grain_identity": {
                    "member_id": member_id,
                    "material_axis": "grain",
                    "conditional_axis_global_xyz": grain,
                    "source_path": f"{STOCK}/envelopes.json",
                    "source_record": f"records[member_id={member_id}].conditional_grain_axis_global_xyz",
                    "basis_scope": "saved conditional material axis; four top replacements retain grain identity",
                },
                "geometry_binding": {"path": shape_path, "sha256": shape_hash},
                "top_geometry_override": member_id in TOP_OVERRIDES,
                "previous_stock_class": cut["stock_class"],
                "previous_stock_blank_length_mm": cut["stock_blank_length_mm"],
                "previous_prepared_section_mm": cut["prepared_section_mm"],
                "historical_envelope_prepared_section_mm": envelope_prepared,
                "delivered_grade_observed": cut["delivered_grade_observed"],
                "post_rip_grade_assigned": cut["post_rip_grade_assigned"],
                "operation_facts": dict.fromkeys(UNAVAILABLE_OPERATIONS),
                "actual": None,
                "disposition": None,
            }
        )

    require(
        len(timber) == 44 and len(plywood) == 6,
        "44 timber / six plywood census differs",
    )
    require(
        Counter(row["member_kind"] for row in timber)
        == {"frame timber": 20, "connector block": 24},
        "timber duty census differs",
    )
    counts = Counter(row["source_stock_class"] for row in timber)
    require(
        counts == {"2x6": 18, "4x6": 10, "4x4": 16}, "source stock class census differs"
    )
    require(
        {row["member_id"] for row in timber if row["requires_source_section_rip"]}
        == SECTION_RIPS,
        "four source-section rip identities differ",
    )
    require(
        {row["body_id"] for row in plywood if row["body_kind"] == "whole kicker"}
        == {"kicker_left", "kicker_right"},
        "whole kicker identities differ",
    )
    for section, count in counts.items():
        total = sum(
            row["stock_blank_length_mm"]
            for row in timber
            if row["source_stock_class"] == section
        )
        require(
            int(class_csv[section]["new_piece_count"]) == count
            and math.isclose(
                total,
                float(class_csv[section]["new_blank_length_total_mm"]),
                rel_tol=0.0,
                abs_tol=1e-8,
            ),
            f"stock-class aggregate differs: {section}",
        )
    scenarios = scenario_source["scenarios"]
    index(scenarios, "scenario_id", 15)
    require(
        scenarios == assembly["stock_reconciliation"]["scenarios"],
        "saved nesting outputs differ",
    )
    require(
        all(row["requested_blanks"] == 44 for row in scenarios),
        "saved nesting census differs",
    )
    hardware = assembly["hardware"]
    require(
        hardware["hillman_axes_screws_separate"] == 66
        and hardware["candidate_axes_bolts_nuts"] == 92
        and hardware["retained_axes_bolts_nuts"] == 12
        and hardware["structural_axes_bolts_nuts_washers"] == [104, 104, 208],
        "preserved hardware census differs",
    )
    packet = {
        "schema": "wood-joints-conditional-blank-cut-list/v1",
        "status": "COMPLETE_FROZEN_RECORD_EXPORT",
        "candidate": assembly["candidate"],
        "source_revision": assembly["source_revision"],
        "counts": {
            "timber_blanks": 44,
            "frame_timbers": 20,
            "connector_blocks": 24,
            "plywood_bodies": 6,
            "source_section_rips": 4,
            "stock_classes": dict(counts),
            "saved_nesting_scenarios": 15,
        },
        "timber_blanks": timber,
        "plywood_bodies_separate": plywood,
        "preserved_hardware_policy": {
            "structural_bolts": 104,
            "nuts": 104,
            "washers": 208,
            "Hillman_42605_panel_kicker_screws": 66,
        },
        "source_pins": [{"path": path, "sha256": pins[path]} for path in sorted(pins)],
        "scope": {
            "stock_nesting_rerun": False,
            "geometry_rebuilt": False,
            "operation_instructions_supplied": False,
            "physical_release": False,
            "other_geometry_bindings": "inherited from frozen records; four top STEP bytes rehashed only",
            "unavailable_operation_facts": "null means not supplied by this blank-length packet",
        },
    }
    timber_csv = [
        {
            "member_id": row["member_id"],
            "member_kind": row["member_kind"],
            "quantity": 1,
            "source_stock_class": row["source_stock_class"],
            "source_section_mm": dimensions(row["source_section_mm"]),
            "stock_blank_length_mm": row["stock_blank_length_mm"],
            "prepared_section_mm": dimensions(row["prepared_section_mm"]),
            "requires_source_section_rip": row["requires_source_section_rip"],
            "finished_envelope_axes": ";".join(
                row["recorded_finished_envelope"]["axes"]
            ),
            "finished_envelope_mm": dimensions(
                row["recorded_finished_envelope"]["dimensions_mm"]
            ),
            "grain_reference": row["grain_reference"],
            "conditional_grain_global_xyz": dimensions(
                row["grain_identity"]["conditional_axis_global_xyz"]
            ),
            "actual": "",
            "disposition": "",
        }
        for row in timber
    ]
    panel_csv = [
        {
            "body_id": row["body_id"],
            "body_kind": row["body_kind"],
            "source_blank_dimensions_mm": dimensions(row["source_blank_dimensions_mm"]),
            "recorded_local_envelope_axes": ";".join(
                row["recorded_local_envelope"]["axes"]
            ),
            "recorded_local_envelope_mm": dimensions(
                row["recorded_local_envelope"]["dimensions_mm"]
            ),
            "actual": "",
            "disposition": "",
        }
        for row in plywood
    ]
    outputs = {
        "blank-cut-list.json": json_bytes(packet),
        "timber-blanks.csv": csv_bytes(timber_csv, list(timber_csv[0])),
        "plywood-bodies.csv": csv_bytes(panel_csv, list(panel_csv[0])),
        "stock-scenario-index.json": json_bytes(
            {
                "schema": "wood-joints-saved-stock-scenario-index/v1",
                "source_path": f"{ASSEMBLY}/rawlocal/stock-scenarios.json",
                "source_sha256": pins[f"{ASSEMBLY}/rawlocal/stock-scenarios.json"],
                "scenarios_copied_verbatim": True,
                "stock_nesting_rerun": False,
                "scenarios": scenarios,
            }
        ),
    }
    return outputs, pins, packet


def worksheet(
    packet: dict[str, Any], hashes: dict[str, str], producer_hash: str
) -> bytes:
    lines = [
        "# Conditional timber blank cut list",
        "",
        "This completed export identifies **44 unique timber blanks: 20 frame members and 24",
        "connector blocks**. Six plywood bodies are listed separately. It joins the frozen",
        "[assembly reconciliation](README.md) to the existing stock records and four saved top",
        "geometry overrides; it does not regenerate geometry or nesting.",
        "",
        "Use it with the [shop guide](shop-guide.md) and [current-joint addendum](current-joint-addendum.md).",
        "This is a conditional stock-length list, not a complete machining schedule or physical",
        "work authorization. Panel attachment retains its reference HOLD. Actual and Disposition",
        "cells stay blank until observed.",
        "",
        "## Read the lengths and sections",
        "",
        "The source-stock class identifies the stock before any section reduction: **18 2×6,",
        "10 4×6 and 16 4×4 blanks**. Dimensions are millimetres. Source sections retain their",
        "recorded dimension order. Finished envelopes use **grain × q × r**, except the two",
        "top outer cleats use **grain × X × T**. Grain references below identify saved conditional",
        "material directions; they are not saw settings or observations of delivered grain.",
        "",
        "Blank length and finished grain span are separate columns. The longer principal, side",
        "and leg blanks must not be shortened to their finished-envelope lengths. Values below",
        "are rounded to 0.001 mm for reading, with full recorded precision in the JSON/CSV exports.",
        "That display precision assigns no machining tolerance, cleanup or receiving allowance.",
        "",
        "The two top outer cleats use 4×6 source stock, 88.9 × 139.7 mm section and 119.7 mm grain",
        "length. Their historical 4×4 stock records are not reused. The four reduced-section",
        "blocks remain in the 4×6 stock class: two center-principal cleats at 83.9 × 139.7 mm and",
        "two inner knee blocks at 88.9 × 133.35 mm. The existing nesting convention takes",
        "full-section blanks before those later rips and preserves the original stock class of",
        "remnants. Rip face/setup and post-rip grade are not supplied or observed.",
        "",
        "In the Prepared column, **—** means no separate section reduction; any unchanged prepared",
        "section recorded by the source remains in the machine export. Missing bevel/miter angles,",
        "profile cuts, rip setup, pilot/bore instructions, service machining and machining tolerances",
        "are explicitly **null** in each row's `operation_facts`. This packet does not infer them",
        "from a finished envelope or historical CAD bore.",
        "",
        "## Forty-four timber blanks",
        "",
        "| Member | Duty | Source stock / section, mm | Blank length, mm | Prepared section, mm | Finished envelope, mm | Grain | Actual | Disposition |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in packet["timber_blanks"]:
        prepared = (
            display(row["prepared_section_mm"])
            if row["requires_source_section_rip"]
            else "—"
        )
        duty = "Frame" if row["member_kind"] == "frame timber" else "Block"
        lines.append(
            f"| `{row['member_id']}` | {duty} | {row['source_stock_class']} / "
            f"{display(row['source_section_mm'])} | {row['stock_blank_length_mm']:.3f} | "
            f"{prepared} | {display(row['recorded_finished_envelope']['dimensions_mm'])} | "
            f"{row['grain_reference']} | | |"
        )
    lines.extend(
        [
            "",
            "### Grain reference directions",
            "",
            "These global XYZ reference vectors are rounded here; the exact per-member vectors",
            "and their source-record identity remain in the machine export. Opposite signed",
            "references preserve the source convention for the same unoriented grain line.",
            "",
            "| Reference | Conditional global grain vector (X, Y, Z) |",
            "| --- | --- |",
        ]
    )
    for name, vector in GRAIN_REFERENCES.items():
        lines.append(f"| {name} | ({', '.join(f'{value:.6f}' for value in vector)}) |")
    lines.extend(
        [
            "",
            "## Six plywood bodies, separate from timber",
            "",
            "Keep four main panels and two whole kickers. Source blank dimensions below retain",
            "their source order; the local X/T/N envelope is an independent saved geometry record.",
            "The kicker's rotated local extents are not its sheet-cut depth or a bevel instruction.",
            "Six bodies are not six purchased sheets. Sheet nesting and the purchased Roseburg AC",
            "fir strength-axis binding retain their scope in the [assembly package](README.md#stock-panel-quantities-and-cost-scope)",
            "and [panel-material note](../upper-corner-screw-layout/panel-material-fidelity.md).",
            "",
            "| Body | Identity | Source blank dimensions, mm | Recorded local X × T × N envelope, mm | Actual | Disposition |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in packet["plywood_bodies_separate"]:
        lines.append(
            f"| `{row['body_id']}` | {row['body_kind']} | "
            f"{display(row['source_blank_dimensions_mm'])} | "
            f"{display(row['recorded_local_envelope']['dimensions_mm'])} | | |"
        )
    lines.extend(
        [
            "",
            "The unchanged fastening policy remains 66 purchased Hillman 42605 panel/kicker",
            "screws, 104 frame bolt stacks/nuts and 208 exterior washers. Use the [shop guide](shop-guide.md#forward-assembly)",
            "for the purchased screw and owner-selected pilot/countersink policy. This list adds",
            "no screw stations, insert pilots, old-bore drilling instructions or fastening products.",
            "",
            "## Existing stock-scenario index",
            "",
            "All fifteen replacement-aware scenarios are copied from frozen `stock-scenarios.json`",
            "without running its nesting helper. Each reserves 3.2 mm separation kerf per blank and",
            "the recorded 0, 10 or 20 mm trim at each stick end. These are first-fit scenarios,",
            "with no new optimization, stock selection, price or purchasing quantity.",
            "",
            "| Existing scenario ID | 2×6 sticks | 4×6 sticks | 4×4 sticks | Blanks placed |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in packet["_scenarios"]:
        counts = row["sticks_by_class"]
        lines.append(
            f"| `{row['scenario_id']}` | {counts['2x6']} | {counts['4x6']} | "
            f"{counts['4x4']} | {row['placed_blanks']}/44 |"
        )
    lines.extend(
        [
            "",
            "The three 8-ft scenarios leave `base_header`, both center principals and both sides",
            "unplaced. Larger and mixed scenarios place all 44 under their saved conventions.",
            "The current index includes the top 4×6 replacements; the earlier stock packet's",
            "4×4-top-cleat placements remain history. Existing nesting files are unchanged.",
            "",
            "## Engineering source bindings and export",
            "",
            "[blank_cut_list.py](blank_cut_list.py) uses only the standard library. Seven frozen",
            "input packets and the four top replacement STEP byte hashes are checked before",
            "and after export. The other geometry hashes and exact grain axes are inherited",
            "from those frozen records; no geometry is imported or mechanically evaluated.",
            "",
            "| Consumed packet | SHA-256 |",
            "| --- | --- |",
        ]
    )
    for path, sha in SOURCE_SHA256.items():
        relative = (
            path.removeprefix(f"{ASSEMBLY}/")
            if path.startswith(f"{ASSEMBLY}/")
            else path
        )
        lines.append(f"| `{relative}` | `{sha}` |")
    lines.extend(
        [
            "",
            f"Producer SHA-256: `{producer_hash}`.",
            "",
            "Ignored output child: `rawlocal/blank-cut-list/attempt01/`.",
            "`blank-cut-list.json` retains all row fields and eleven source pins; the two CSVs",
            "retain blank Actual/Disposition cells. `stock-scenario-index.json` retains all fifteen",
            "saved scenario objects verbatim. The child also contains this worksheet, the producer",
            "snapshot and a receipt binding their exact bytes. Raw outputs are local provenance,",
            "not newly published geometry evidence.",
            "",
            "| Export | SHA-256 |",
            "| --- | --- |",
        ]
    )
    for name, sha in hashes.items():
        lines.append(f"| `{name}` | `{sha}` |")
    lines.extend(
        [
            "",
            "From the repository root:",
            "",
            "```sh",
            f".venv/bin/python -B {ASSEMBLY}/blank_cut_list.py --write",
            f".venv/bin/python -B {ASSEMBLY}/blank_cut_list.py --verify",
            "```",
            "",
            "Write refuses to replace different raw bytes; verify reads the same frozen records",
            "and compares the export byte-for-byte. It runs no CAD, native/frame calculation,",
            "stock optimization, supplier research, software tests or review loop. The list assigns",
            "no delivered wood grade, physical fit, inspected cuts, joint capacity or climber rating.",
            "",
        ]
    )
    return "\n".join(lines).encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        producer = Path(__file__).read_bytes()
        outputs, pins, packet = build()
        packet["_scenarios"] = json.loads(outputs["stock-scenario-index.json"])[
            "scenarios"
        ]
        doc = worksheet(
            packet,
            {name: digest(value) for name, value in outputs.items()},
            digest(producer),
        )
        outputs["worksheet.md"] = doc
        outputs["producer.py.snapshot"] = producer
        receipt = {
            "schema": "wood-joints-blank-cut-list-receipt/v1",
            "status": "COMPLETE_FROZEN_RECORD_EXPORT",
            "producer_sha256": digest(producer),
            "source_pins": [
                {"path": path, "sha256": pins[path]} for path in sorted(pins)
            ],
            "output_sha256": {name: digest(value) for name, value in outputs.items()},
            "maintained_markdown_sha256": digest(doc),
            "counts": packet["counts"],
            "source_bytes_unchanged": True,
        }
        outputs["receipt.json"] = json_bytes(receipt)
        for relative, expected in pins.items():
            require(
                digest((ROOT / relative).read_bytes()) == expected,
                f"source changed: {relative}",
            )
        targets = {DEFAULT_OUTPUT / name: value for name, value in outputs.items()}
        targets[HERE / "blank-cut-list.md"] = doc
        for path, value in targets.items():
            if args.verify:
                require(
                    path.is_file() and path.read_bytes() == value,
                    f"export missing/different: {path}",
                )
            elif path.is_file() and path != HERE / "blank-cut-list.md":
                require(
                    path.read_bytes() == value,
                    f"refusing to replace frozen output: {path}",
                )
        if args.write:
            DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
            for path, value in targets.items():
                if not path.is_file() or path.read_bytes() != value:
                    path.write_bytes(value)
        for relative, expected in pins.items():
            require(
                digest((ROOT / relative).read_bytes()) == expected,
                f"source changed after export: {relative}",
            )
        print(
            json.dumps(
                {
                    "status": "verified" if args.verify else "written",
                    "timber_blanks": 44,
                    "plywood_bodies": 6,
                    "saved_scenarios": 15,
                    "source_pins": len(pins),
                    "maintained_markdown_sha256": digest(doc),
                    "output_sha256": {
                        name: digest(value) for name, value in outputs.items()
                    },
                },
                sort_keys=True,
            )
        )
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
        print(f"blank-cut-list: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
