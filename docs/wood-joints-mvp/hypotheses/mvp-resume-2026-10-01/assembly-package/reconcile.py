#!/usr/bin/env python3
"""Reconcile source-pinned assembly bodies, hardware, and stock scenarios."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
RAW = HERE / "rawlocal"
MVP = ROOT / "docs/wood-joints-mvp"
RESUME = MVP / "hypotheses/mvp-resume-2026-10-01"
STOCK = MVP / "hypotheses/current-stock-envelope-reconciliation-2026-10-01"
DENSITY_KG_M3 = 600.0
CORNER_DELTA_DENSITY_KG_M3 = 500.0


class Blocked(Exception):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


class Pins:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.errors: list[str] = []

    def add(self, rel: str, role: str, expected: str | None = None) -> None:
        path = (ROOT / rel).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError:
            self.errors.append(f"source path escapes repository: {rel}")
            return
        if not path.is_file():
            self.errors.append(f"missing source: {rel} ({role})")
            return
        actual = digest(path)
        row = self.rows.setdefault(rel, {"path": rel, "sha256": actual, "roles": []})
        if row["sha256"] != actual:
            self.errors.append(f"source changed while read: {rel}")
        if expected and actual != expected:
            self.errors.append(f"SHA-256 mismatch: {rel} expected {expected}, got {actual}")
        if role not in row["roles"]:
            row["roles"].append(role)

    def add_map(self, mapping: dict[str, str], role: str) -> None:
        for rel, expected in sorted(mapping.items()):
            self.add(rel, role, expected)

    def add_list(self, values: list[dict[str, Any]], role: str) -> None:
        for value in values:
            self.add(value["path"], role, value["sha256"])

    def output(self) -> list[dict[str, Any]]:
        rows = [self.rows[key] for key in sorted(self.rows)]
        for row in rows:
            row["roles"].sort()
        return rows


def read_json(rel: str) -> Any:
    path = ROOT / rel
    if not path.is_file():
        raise Blocked(f"missing required source: {rel}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Blocked(f"cannot read required source {rel}: {exc}") from exc


def csv_bytes(rows: list[dict[str, Any]], columns: list[str]) -> bytes:
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def build() -> dict[str, bytes]:
    model_rel = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01/model.json"
    model_dir = str(Path(model_rel).parent)
    operator_rel = f"{model_dir}/operator-assessment.json"
    proposal_rel = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/proposal.json"
    hardware_rel = "docs/wood-joints-mvp/current-hardware-coverage.json"
    top_hardware_dir = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-hardware"
    top_hardware_inputs_rel = f"{top_hardware_dir}/hardware-inputs.json"
    top_hardware_readme_rel = f"{top_hardware_dir}/README.md"
    top_hardware_fit_rel = f"{top_hardware_dir}/assembly-fit.md"
    inventory_rel = "docs/wood-joints-mvp/source-inventory.json"
    weight_rel = "docs/wood-joints-mvp/board-weight-2026-09-24.json"
    envelope_rel = f"{STOCK.relative_to(ROOT)}/envelopes.json"
    source_pins_rel = f"{STOCK.relative_to(ROOT)}/source-pins.json"
    cuts_rel = f"{STOCK.relative_to(ROOT)}/cut-scenarios.json"

    model = read_json(model_rel)
    operator = read_json(operator_rel)
    proposal = read_json(proposal_rel)
    hardware = read_json(hardware_rel)
    top_hardware = read_json(top_hardware_inputs_rel)
    inventory = read_json(inventory_rel)
    weights = read_json(weight_rel)
    envelopes = read_json(envelope_rel)
    envelope_pins = read_json(source_pins_rel)
    cuts = read_json(cuts_rel)

    pins = Pins()
    pins.add(model_rel, "current corner-frame model", operator.get("output_sha256", {}).get("model.json"))
    pins.add(operator_rel, "corner-frame operator assessment")
    pins.add(f"{model_dir}/inputs.json", "corner-frame frozen inputs")
    pins.add_map(operator.get("source_sha256", {}), "corner-frame source pin")
    for name, expected in operator.get("output_sha256", {}).items():
        pins.add(f"{model_dir}/{name}", "corner-frame generated output", expected)
    pins.add(
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner_frame.py",
        "corner-frame mass-delta method",
    )
    pins.add(
        f"{model_dir}/corner_frame.py.snapshot",
        "corner-frame frozen producer snapshot",
        operator.get("producer_sha256"),
    )
    pins.add(proposal_rel, "top-corner proposal")
    pins.add_map(proposal.get("source_sha256", {}), "top-corner source pin")
    pins.add_map(proposal.get("producer_dependency_sha256", {}), "top-corner producer dependency")
    pins.add_map(proposal.get("proposal_step_sha256", {}), "top-corner finished solid")
    pins.add(
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/lateral-states.csv",
        "top-corner lateral state",
        proposal.get("lateral_csv_sha256"),
    )
    pins.add(
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/side-view.svg",
        "top-corner side view",
        proposal.get("side_preview_sha256"),
    )

    pins.add(hardware_rel, "current hardware coverage")
    coverage_sources = {row["path"]: row["sha256"] for row in hardware.get("source_document_pins", [])}
    axis_source = hardware.get("axis_source", {})
    if axis_source.get("path"):
        coverage_sources[axis_source["path"]] = axis_source["sha256"]
    pins.add_map(coverage_sources, "hardware coverage source pin")
    pins.add(top_hardware_inputs_rel, "current conditional top-corner catalog options")
    pins.add_list(top_hardware.get("source_inputs", []), "top-corner hardware source pin")
    pins.add(top_hardware_readme_rel, "reviewed top-corner catalog options")
    pins.add(top_hardware_fit_rel, "reviewed top-corner assembly-fit scope")
    pins.add(inventory_rel, "current source inventory")
    pins.add_map(inventory.get("source_hashes_sha256", {}), "source inventory source pin")
    pins.add_map(inventory.get("source_runtime_module_hashes_sha256", {}), "source inventory runtime module")
    pins.add(weight_rel, "recorded finished-volume and density inventory")

    pins.add(envelope_rel, "reviewed stock-envelope result")
    pins.add(source_pins_rel, "stock-envelope source-pin list", envelopes.get("source_pins_sha256"))
    pins.add_list(list(envelope_pins.get("pins", {}).values()), "stock-envelope source pin")
    pins.add(cuts_rel, "reviewed stock-cut scenarios")
    pins.add_list(cuts.get("source_pins", []), "stock-cut scenario source pin")
    for rel in (
        f"{STOCK.relative_to(ROOT)}/README.md",
        f"{STOCK.relative_to(ROOT)}/envelopes.md",
        f"{STOCK.relative_to(ROOT)}/cut-scenarios.md",
        f"{STOCK.relative_to(ROOT)}/review.md",
        f"{STOCK.relative_to(ROOT)}/envelopes.py",
        f"{STOCK.relative_to(ROOT)}/cut_scenarios.py",
        f"{STOCK.relative_to(ROOT)}/nesting.py",
        "docs/wood-joints-mvp/current-hardware-schedule.md",
        "docs/current-panel-screw-purchase.md",
    ):
        pins.add(rel, "reviewed packet or reconciliation method")

    errors = pins.errors
    check(model.get("schema") == "simple_corrected_frame_model/v1", "corner-frame schema changed", errors)
    check(proposal.get("schema") == "top_corner_correction_proposal/v1", "top-corner schema changed", errors)
    check(model.get("candidate") == inventory.get("candidate") == proposal.get("source_candidate"), "candidate identity mismatch", errors)
    check(model.get("source_revision") == proposal.get("source_revision") == weights.get("revision_id"), "source revision mismatch", errors)
    check(envelopes.get("geometry_revision_id") == model.get("source_revision"), "stock-envelope revision mismatch", errors)
    check(model.get("physical_release") is False and proposal.get("physical_release") is False, "source unexpectedly claims physical release", errors)
    check(proposal.get("status") == "ISOLATED_FIXED_DEMAND_PROPOSAL_NOT_SELECTED", "top proposal status changed", errors)
    check(top_hardware.get("schema") == "top_corner_catalog_hardware_inputs/v1", "top-corner hardware input schema changed", errors)
    check(top_hardware.get("status") == "CATALOG_OPTIONS_CONDITIONAL_INPUTS_NOT_ADOPTED", "top-corner catalog options no longer conditional", errors)
    check(top_hardware.get("reviewed_source_revision") == model.get("source_revision"), "top-corner hardware revision differs from current model", errors)

    names = model.get("body_names", [])
    timbers = inventory.get("transport_decomposition", {}).get("timber", [])
    panels = inventory.get("transport_decomposition", {}).get("panels", [])
    records = envelopes.get("records", [])
    envelope_by_id = {row["member_id"]: row for row in records}
    blocks = [row["member_id"] for row in records if row.get("member_kind") == "candidate_block"]
    schedule = cuts.get("piece_schedule", [])
    stock_by_id = {row["member_id"]: row for row in schedule}
    weight_rows = [row for row in weights.get("rows", []) if row.get("group") in ("frame timber", "corner blocks", "plywood panels")]
    weight_by_id = {row["name"]: row for row in weight_rows}
    part_by_id = {row["part_id"]: row for row in inventory.get("parts", [])}
    check(len(names) == 50 and len(set(names)) == 50, "model body names must be 50 unique IDs", errors)
    check(len(timbers) == 20 and len(blocks) == 24 and len(panels) == 6, "expected 20 timber, 24 block, 6 panel bodies", errors)
    check(set(names) == set(timbers) | set(blocks) | set(panels), "50 body identities do not reconcile", errors)
    check(len(records) == len(envelope_by_id) == 44, "stock-envelope names must be 44 unique IDs", errors)
    check(len(schedule) == len(stock_by_id) == 44 and set(stock_by_id) == set(timbers) | set(blocks), "stock schedule must cover 44 unique blanks", errors)
    check(len(weight_rows) == len(weight_by_id) == 50 and set(weight_by_id) == set(names), "finished-volume inventory must cover 50 unique bodies", errors)
    check(set(panels).issubset(part_by_id), "panel dimensions absent from source inventory", errors)
    check(all(float(row.get("density_kg_m3", -1)) == DENSITY_KG_M3 for row in weight_rows), "recorded 600 kg/m³ density basis changed", errors)
    for row in records:
        recorded = weight_by_id.get(row["member_id"], {}).get("volume_mm3")
        current = row.get("current_finished_volume_mm3")
        check(recorded is not None and current is not None and abs(float(recorded) - float(current)) < 0.1,
              f"stock-envelope and finished-volume inventories disagree for {row['member_id']}", errors)

    top_names = {"top_outer_left_cleat", "top_outer_right_cleat"}
    top_proposals = {row["block"]: row for row in proposal.get("proposals", [])}
    model_proposals = {row["block"]: row for row in model.get("proposed_corner_axes", [])}
    check(set(top_proposals) == set(model_proposals) == top_names, "current proposal/model must identify exactly two top cleats", errors)
    for name in top_names:
        proposal_row = top_proposals.get(name, {})
        model_row = model_proposals.get(name, {})
        check(proposal_row.get("proposed_section_X_T_mm") == [88.9, 139.7] == model_row.get("proposed_section_X_T_mm"), f"4x6 section missing for {name}", errors)
        check(abs(float(proposal_row.get("grain_length_mm", 0)) - 119.7) < 1e-6, f"proposal grain length changed for {name}", errors)
        check(abs(float(proposal_row.get("finished_proposal_volume_mm3", 0)) - float(model_row.get("finished_proposal_volume_mm3", 0))) < 1e-6, f"proposal/model volume mismatch for {name}", errors)
    mass_changes = {row["body"]: row for row in model.get("wood_mass_changes", [])}
    check(len(mass_changes) == len(model.get("wood_mass_changes", [])), "duplicate changed body in model mass changes", errors)
    check(set(mass_changes) == {"base_side_left", "base_side_right", *top_names}, "corner model must report two top cleats and two side hosts", errors)
    for name in top_names:
        prior = float(weight_by_id[name]["volume_mm3"])
        corrected = float(model_proposals[name]["finished_proposal_volume_mm3"])
        model_delta = float(mass_changes[name]["wood_mass_change_kg"])
        check(abs((corrected - prior) * CORNER_DELTA_DENSITY_KG_M3 * 1e-9 - model_delta) < 1e-9,
              f"top-cleat volume does not reproduce recorded 500 kg/m³ mass delta for {name}", errors)

    candidate_families = hardware.get("candidate_family_coverage", [])
    candidate_by_family = {row["family_id"]: row for row in candidate_families}
    side_family = candidate_by_family.get("candidate_side_16", {})
    side_model_length = float(side_family.get("modeled", {}).get("underhead_to_tip_mm", 0))
    check(side_model_length > 0, "current modeled side-bolt length is missing", errors)

    catalog_parts = top_hardware.get("catalog_parts", {})
    side_bolt_option = catalog_parts.get("side_bolt_grade8", {})
    rail_bolt_options = [
        catalog_parts.get("rail_bolt_grade5_lawson", {}),
        catalog_parts.get("rail_bolt_grade5_motion", {}),
    ]
    check(side_bolt_option.get("item") == "28650" and side_bolt_option.get("quantity_required") == 4,
          "conditional Bolt Depot 28650 side lead changed", errors)
    check(side_bolt_option.get("catalog_size_and_standard_compatible") is True
          and side_bolt_option.get("complete_installed_fit_accepted") is False,
          "side catalog lead must remain conditional on complete fit", errors)
    check({row.get("item") for row in rail_bolt_options} == {"FA21103", "MI 11706127"},
          "conditional Lawson/Motion rail leads changed", errors)
    check(all(row.get("quantity_required") == 4 and row.get("catalog_size_and_standard_compatible") is True
              and row.get("complete_installed_fit_accepted") is False for row in rail_bolt_options),
          "rail catalog leads must remain conditional on complete fit", errors)
    check(top_hardware.get("scope", {}).get("side_bolts") == 4
          and top_hardware.get("scope", {}).get("rail_bolts") == 4
          and top_hardware.get("scope", {}).get("wood_grip_mm_each") == 177.8,
          "top-corner catalog packet quantity/grip changed", errors)

    def catalog_length_summary(part: dict[str, Any]) -> dict[str, Any]:
        length = part.get("length_under_head", {}).get("mm", {})
        source_ids = part.get("source_ids", [])
        return {
            "supplier": part.get("supplier", ""),
            "item": part.get("item", ""),
            "description": part.get("description", ""),
            "catalog_diameter_mm": part.get("diameter", {}).get("mm", {}).get("nominal"),
            "catalog_nominal_underhead_length_mm": length.get("nominal"),
            "catalog_minimum_underhead_length_mm": length.get("minimum"),
            "catalog_maximum_underhead_length_mm": length.get("maximum"),
            "catalog_length_guarantee_note": (
                "exact product-page range" if length.get("minimum") is not None and length.get("maximum") is not None
                else "nominal listing only; delivered minimum not listed"
            ),
            "thread_partial": part.get("thread", {}).get("partial"),
            "material_standard": part.get("material_standard", part.get("dimension_standard_catalog", "")),
            "source_ids": source_ids,
            "source_urls": [top_hardware.get("sources", {}).get(source_id, {}).get("url", "") for source_id in source_ids],
            "complete_installed_fit_accepted": part.get("complete_installed_fit_accepted", False),
            "product_selected": False,
        }

    side_catalog_summary = catalog_length_summary(side_bolt_option)
    rail_catalog_summaries = [catalog_length_summary(row) for row in rail_bolt_options]
    side_catalog_ref = (
        "Bolt Depot 28650 (conditional 5/16-18 × 8-in Grade 8 lead); catalog underhead "
        f"nominal {side_catalog_summary['catalog_nominal_underhead_length_mm']} mm, exact range "
        f"{side_catalog_summary['catalog_minimum_underhead_length_mm']}–{side_catalog_summary['catalog_maximum_underhead_length_mm']} mm; fit not accepted"
    )
    rail_catalog_ref = (
        "Lawson FA21103 or Motion MI 11706127 (conditional 1/4-20 × 8-in Grade 5 leads); "
        "catalog nominal underhead length 203.2 mm; delivered minimum not listed; fit not accepted"
    )
    side_model_vs_catalog = (
        f"modeled underhead-to-tip {side_model_length:g} mm; Bolt Depot catalog nominal "
        f"{side_catalog_summary['catalog_nominal_underhead_length_mm']} mm, range "
        f"{side_catalog_summary['catalog_minimum_underhead_length_mm']}–{side_catalog_summary['catalog_maximum_underhead_length_mm']} mm; "
        "catalog range does not guarantee body/thread profile or complete fit"
    )
    rail_model_vs_catalog = (
        f"modeled underhead-to-tip {side_model_length:g} mm; Lawson/Motion catalog nominal 203.2 mm, "
        "no exact delivered minimum; B18.2.1 length sensitivity remains conditional"
    )

    # The eight changed top axes are resolved against current candidate IDs.
    retained_families = hardware.get("retained_family_coverage", [])
    candidate_axes: dict[str, dict[str, Any]] = {}
    retained_axes: dict[str, dict[str, Any]] = {}
    for family in candidate_families:
        modeled = family["modeled"]
        check(len(family["axis_ids"]) == family["count"], f"hardware family count mismatch: {family['family_id']}", errors)
        for axis_id in family["axis_ids"]:
            if axis_id in candidate_axes:
                errors.append(f"duplicate candidate bolt axis: {axis_id}")
            candidate_axes[axis_id] = {
                "axis_id": axis_id,
                "system": "candidate",
                "source_family_id": family["family_id"],
                "family_id": family["family_id"],
                "family": family["family"],
                "diameter_mm": float(modeled["shaft_envelope_diameter_mm"]),
                "model_length_mm": float(modeled["underhead_to_tip_mm"]),
                "grip_mm": float(modeled["wood_grip_mm"]),
                "old_grip_mm": float(modeled["wood_grip_mm"]),
                "catalog_reference": family.get("catalog_or_length_screen", ""),
                "catalog_status": "coverage lead only; no SKU selected",
            }
    for family in retained_families:
        modeled = family["modeled"]
        check(len(family["axis_ids"]) == family["count"], f"retained family count mismatch: {family['family_id']}", errors)
        for axis_id in family["axis_ids"]:
            if axis_id in candidate_axes or axis_id in retained_axes:
                errors.append(f"duplicate structural bolt axis: {axis_id}")
            retained_axes[axis_id] = {
                "axis_id": axis_id,
                "system": "retained",
                "source_family_id": family["family_id"],
                "family_id": family["family_id"],
                "family": family["family"],
                "diameter_mm": float(modeled["D_mm"]),
                "model_length_mm": float(modeled["L_mm"]),
                "grip_mm": float(modeled["grip_mm"]),
                "old_grip_mm": float(modeled["grip_mm"]),
                "catalog_reference": "; ".join(family.get("catalog_references", [])),
                "catalog_status": "retained source arrangement",
            }
    check(len(candidate_axes) == 92 and len(retained_axes) == 12, "current hardware must be 92 candidate + 12 retained axes", errors)

    top_axis_data = {}
    for name in sorted(top_names):
        for axis in top_proposals[name].get("axes", []):
            if axis["axis_id"] in top_axis_data:
                errors.append(f"duplicate axis in top proposal: {axis['axis_id']}")
            top_axis_data[axis["axis_id"]] = axis
    check(len(top_axis_data) == 8 and set(top_axis_data).issubset(candidate_axes), "top proposal must change eight current candidate axes", errors)
    for axis_id, proposal_axis in top_axis_data.items():
        axis = candidate_axes[axis_id]
        if axis_id.rsplit("/", 1)[-1].startswith("rail_"):
            check(float(proposal_axis["old_wood_grip_mm"]) == 127.0 and float(proposal_axis["wood_grip_mm"]) == 177.8, f"top rail grip mismatch: {axis_id}", errors)
            axis.update(family_id="candidate_top_rail_quarter_8in_4", family="top outer 1/4-in 177.8-mm grip", diameter_mm=6.35, model_length_mm=side_model_length, grip_mm=177.8, old_grip_mm=127.0, catalog_reference=rail_catalog_ref, catalog_status="conditional Lawson/Motion catalog leads; unselected; delivered minimum and complete fit unresolved")
        elif axis_id.rsplit("/", 1)[-1].startswith("side_"):
            check(float(proposal_axis["nominal_bolt_diameter_mm"]) == 7.9375 and float(proposal_axis["wood_grip_mm"]) == 177.8, f"top side axis mismatch: {axis_id}", errors)
            axis.update(family_id="candidate_top_side_5_16_4", family="top outer 5/16-in 177.8-mm grip", diameter_mm=7.9375, model_length_mm=side_model_length, grip_mm=177.8, old_grip_mm=177.8, catalog_reference=side_catalog_ref, catalog_status="conditional Bolt Depot 28650 catalog lead; unselected; delivered thread profile and complete fit unresolved")
        else:
            errors.append(f"unexpected top proposal axis role: {axis_id}")
    check(sum(row["diameter_mm"] == 6.35 for row in candidate_axes.values()) == 88, "candidate 1/4-in axis sum must be 88", errors)
    check(sum(row["diameter_mm"] == 7.9375 for row in candidate_axes.values()) == 4, "candidate 5/16-in axis sum must be 4", errors)

    screws = inventory.get("fixed_panel_kicker_screws", [])
    screw_ids = [row["axis_id"] for row in screws]
    check(len(screws) == len(set(screw_ids)) == 66, "Hillman screw inventory must contain 66 unique axes", errors)
    structural_ids = set(candidate_axes) | set(retained_axes)
    check(not structural_ids.intersection(screw_ids), "Hillman axes overlap structural bolt axes", errors)
    quantities = hardware.get("quantity_reconciliation", {})
    check(quantities.get("candidate", {}).get("axes") == 92, "coverage candidate count changed", errors)
    check(quantities.get("retained", {}).get("axes") == 12, "coverage retained count changed", errors)
    check(quantities.get("structural_total", {}).get("separate_washers") == 208, "coverage washer total changed", errors)
    check(quantities.get("removed_SDS25112", {}).get("axes") == 144, "removed SDS axis record changed", errors)
    if errors:
        raise Blocked("source hashes or input invariants failed:\n- " + "\n- ".join(errors))

    # Exact current volumes use the 44-piece packet, panel inventory, and the
    # two proposal/model updates. Every reported body mass then uses 600 kg/m³.
    body_rows = []
    correction_step = proposal.get("proposal_step_sha256", {})
    corrected_path_by_name = {Path(path).stem: path for path in correction_step}
    for name in names:
        weight = weight_by_id[name]
        previous_volume = float(weight["volume_mm3"])
        volume = previous_volume
        kind = weight["group"]
        source_path = weight_rel
        source_hash = pins.rows[weight_rel]["sha256"]
        shape_hash = ""
        local = {}
        envelope = envelope_by_id.get(name)
        stock = stock_by_id.get(name)

        if envelope:
            shape_hash = envelope["current_finished_step_sha256"]
            spans = envelope["original_stock_containment"]["finished_oriented_spans_g_q_r_mm"]
            local = {"axes": ["grain", "section_q", "section_r"], "dimensions_mm": spans}
            if name in top_names:
                top = model_proposals[name]
                volume = float(top["finished_proposal_volume_mm3"])
                changed_step_path = corrected_path_by_name[name]
                shape_hash = correction_step[changed_step_path]
                local = {"axes": ["grain", "X", "T"], "dimensions_mm": [float(top["grain_length_mm"]), 88.9, 139.7]}
                source_path = model_rel
                source_hash = pins.rows[model_rel]["sha256"]
            elif name in ("base_side_left", "base_side_right"):
                delta_kg = float(mass_changes[name]["wood_mass_change_kg"])
                volume += delta_kg / (CORNER_DELTA_DENSITY_KG_M3 * 1e-9)
                changed_step_path = corrected_path_by_name[name]
                shape_hash = correction_step[changed_step_path]
                source_path = model_rel
                source_hash = pins.rows[model_rel]["sha256"]
            else:
                volume = float(envelope["current_finished_volume_mm3"])
                source_path = envelope_rel
                source_hash = pins.rows[envelope_rel]["sha256"]
            section = [88.9, 139.7] if name in top_names else list(stock["original_stock_section_mm"])
            length = float(model_proposals[name]["grain_length_mm"]) if name in top_names else float(stock["stock_blank_length_mm"])
            stock_class = "4x6" if name in top_names else stock["stock_class"]
            stock_box = [section[0], section[1], length]
            stock_status = "top correction proposal; old 4x4 containment not reused" if name in top_names else envelope["original_stock_containment"]["status"]
            prepared_section = None if name in top_names else stock.get("prepared_section_mm")
            material_part = "timber or block"
        else:
            part = part_by_id[name]
            extents = part["actual_shape_extents_local_mm"]
            local = {
                "axes": ["X", "T", "N"],
                "dimensions_mm": [extents["X"][1] - extents["X"][0], extents["T"][1] - extents["T"][0], extents["N"][1] - extents["N"][0]],
            }
            stock_box = list(part["source_blank_dimensions_mm"])
            stock_class = "plywood panel blank"
            stock_status = "source-inventory geometry; no new containment claim"
            prepared_section = None
            material_part = "panel"
            shape_hash = part["source_shape_sha256"]
        check(volume > 0, f"non-positive finished volume: {name}", errors)
        body_rows.append(
            {
                "body_id": name,
                "kind": kind,
                "local_dimensions": local,
                "proposed_stock_box_mm": stock_box,
                "prepared_stock_section_mm": prepared_section,
                "stock_class": stock_class,
                "stock_status": stock_status,
                "finished_volume_mm3": volume,
                "previous_inventory_volume_mm3": previous_volume,
                "volume_delta_mm3": volume - previous_volume,
                "density_kg_m3": DENSITY_KG_M3,
                "mass_kg": volume * DENSITY_KG_M3 * 1e-9,
                "volume_source_path": source_path,
                "volume_source_sha256": source_hash,
                "shape_source_sha256": shape_hash,
                "shape_source_scope": (
                    "source-inventory uncut source shape/extents for local dimensions only; finished volume is from board-weight inventory, so this shape hash is not a finished-volume solid hash"
                    if material_part == "panel"
                    else "source geometry binding for member dimensions; finished volume follows the separately pinned source path/hash"
                ),
                "material_basis": f"recorded {DENSITY_KG_M3:g} kg/m^3 planning density; actual material density unmeasured",
                "source_scope": material_part,
            }
        )

    if errors:
        raise Blocked("body reconciliation failed:\n- " + "\n- ".join(errors))

    # Reclassify exactly two top cleats and rerun all 15 recorded cases with the
    # existing helper, preserving kerf, stock options, and trim assumptions.
    sys.path.insert(0, str(STOCK))
    try:
        from nesting import Blank, nest_blanks
    except ImportError as exc:
        raise Blocked(f"reviewed stock nesting helper unavailable: {exc}") from exc
    finally:
        sys.path.remove(str(STOCK))
    blanks = []
    old_counts: dict[str, int] = {}
    new_counts: dict[str, int] = {}
    old_lengths: dict[str, float] = {}
    new_lengths: dict[str, float] = {}
    for row in schedule:
        name = row["member_id"]
        old_class = row["stock_class"]
        new_class = "4x6" if name in top_names else old_class
        old_length = float(row["stock_blank_length_mm"])
        new_length = float(model_proposals[name]["grain_length_mm"]) if name in top_names else old_length
        old_counts[old_class] = old_counts.get(old_class, 0) + 1
        new_counts[new_class] = new_counts.get(new_class, 0) + 1
        old_lengths[old_class] = old_lengths.get(old_class, 0.0) + old_length
        new_lengths[new_class] = new_lengths.get(new_class, 0.0) + new_length
        rip = row.get("prepared_section_mm") if name not in top_names else None
        blanks.append(Blank(name, new_length, new_class, tuple(rip) if rip else None))
    check(len(blanks) == 44 and new_counts == {"2x6": 18, "4x4": 16, "4x6": 10}, "revised stock blanks/classes failed", errors)
    scenarios = []
    for scenario in cuts["scenarios"]:
        result = nest_blanks(
            blanks,
            scenario["nominal_stock_length_options_mm_by_original_section"],
            crosscut_kerf_mm=scenario["crosscut_separation_kerf_mm_per_blank"],
            end_trim_start_mm=scenario["end_trim_start_mm_including_trim_cut_loss"],
            end_trim_end_mm=scenario["end_trim_end_mm_including_trim_cut_loss"],
        )
        section_counts = {item.section: item.board_count for item in result.section_totals}
        scenarios.append(
            {
                "scenario_id": scenario["scenario_id"],
                "stock_length_options_ft": scenario["nominal_stock_length_options_ft"],
                "trim_each_end_mm": scenario["end_trim_start_mm_including_trim_cut_loss"],
                "kerf_per_blank_mm": scenario["crosscut_separation_kerf_mm_per_blank"],
                "sticks_by_class": {key: section_counts.get(key, 0) for key in ("2x6", "4x4", "4x6")},
                "sticks_total": result.totals.board_count,
                "requested_blanks": result.totals.requested_blank_count,
                "placed_blanks": result.totals.placed_blank_count,
                "unplaced_blanks": result.totals.infeasible_blank_count,
                "unplaced_body_ids": list(result.infeasible_item_ids),
                "all_44_placed": result.complete,
                "heuristic": result.heuristic,
                "purchase_quantity_or_optimum_established": False,
            }
        )
    if errors:
        raise Blocked("replacement-aware stock arithmetic failed:\n- " + "\n- ".join(errors))

    # Aggregate hardware rows without selecting or pricing a product.
    all_axes = list(candidate_axes.values()) + list(retained_axes.values())
    families: dict[str, dict[str, Any]] = {}
    for family in candidate_families:
        fam = family["family_id"]
        families[fam] = {
            "system": "candidate",
            "source_family_id": fam,
            "family": family["family"],
            "diameter_mm": float(family["modeled"]["shaft_envelope_diameter_mm"]),
            "model_length_mm": float(family["modeled"]["underhead_to_tip_mm"]),
            "grip_mm": float(family["modeled"]["wood_grip_mm"]),
            "catalog_reference": family.get("catalog_or_length_screen", ""),
        }
    for family in retained_families:
        fam = family["family_id"]
        families[fam] = {
            "system": "retained",
            "source_family_id": fam,
            "family": family["family"],
            "diameter_mm": float(family["modeled"]["D_mm"]),
            "model_length_mm": float(family["modeled"]["L_mm"]),
            "grip_mm": float(family["modeled"]["grip_mm"]),
            "catalog_reference": "; ".join(family.get("catalog_references", [])),
        }
    families["candidate_top_rail_quarter_8in_4"] = {
        "system": "candidate", "source_family_id": "candidate_ordinary_48",
        "family": "top outer 1/4-in 177.8-mm grip", "diameter_mm": 6.35,
        "model_length_mm": side_model_length, "grip_mm": 177.8,
        "catalog_reference": rail_catalog_ref,
    }
    families["candidate_top_side_5_16_4"] = {
        "system": "candidate", "source_family_id": "candidate_side_16",
        "family": "top outer 5/16-in 177.8-mm grip", "diameter_mm": 7.9375,
        "model_length_mm": side_model_length, "grip_mm": 177.8,
        "catalog_reference": side_catalog_ref,
    }
    family_counts: dict[str, int] = {}
    for axis in all_axes:
        family_counts[axis["family_id"]] = family_counts.get(axis["family_id"], 0) + 1
    family_rows = []
    for fam, count in sorted(family_counts.items()):
        entry = families[fam]
        family_rows.append(
            {
                **entry,
                "reconciled_family_id": fam,
                "axis_count": count,
                "bolts": count,
                "nuts": count,
                "separate_washers": count * 2,
                "screws": 0,
                "model_vs_catalog_length": (
                    side_model_vs_catalog if fam == "candidate_top_side_5_16_4"
                    else rail_model_vs_catalog if fam == "candidate_top_rail_quarter_8in_4"
                    else f"modeled underhead-to-tip {entry['model_length_mm']} mm; catalog reference kept separate"
                ),
                "product_selected": False,
                "capacity_assigned": False,
            }
        )
    family_rows.append(
        {
            "system": "separate_panel_kicker_policy",
            "source_family_id": "fixed_panel_kicker_screws",
            "family": "Hillman 42605 #10 x 2-1/2-in",
            "reconciled_family_id": "separate_hillman_42605_66",
            "axis_count": 66,
            "bolts": 0,
            "nuts": 0,
            "separate_washers": 0,
            "screws": 66,
            "diameter_mm": None,
            "model_length_mm": 50.8,
            "grip_mm": None,
            "model_vs_catalog_length": "50.8-mm occupied CAD length != 63.5-mm purchased length",
            "catalog_reference": "purchased Hillman 42605 policy; price/receipt absent",
            "product_selected": True,
            "capacity_assigned": False,
        }
    )

    axis_rows = []
    for axis in all_axes:
        axis_rows.append(
            {
                "fastener_type": "structural through-bolt",
                **axis,
                "bolts": 1,
                "nuts": 1,
                "separate_washers": 2,
                "screws": 0,
            }
        )
    for screw in screws:
        axis_rows.append(
            {
                "fastener_type": "panel/kicker screw",
                "axis_id": screw["axis_id"],
                "system": "separate_panel_kicker_policy",
                "source_family_id": "fixed_panel_kicker_screws",
                "family_id": "separate_hillman_42605_66",
                "family": "Hillman 42605 #10 x 2-1/2-in",
                "diameter_mm": None,
                "model_length_mm": float(screw["source_occupied_length_mm"]),
                "grip_mm": None,
                "old_grip_mm": None,
                "catalog_reference": "purchased length 63.5 mm; separate from occupied CAD length",
                "catalog_status": "purchased policy; no capacity or weight inferred",
                "bolts": 0,
                "nuts": 0,
                "separate_washers": 0,
                "screws": 1,
            }
        )
    axis_ids = [row["axis_id"] for row in axis_rows]
    check(len(axis_ids) == len(set(axis_ids)) == 170, "expected 104 unique structural axes + 66 unique Hillman axes", errors)
    check(len(all_axes) == 104 and sum(row["bolts"] for row in axis_rows) == 104, "structural bolt total is not 104", errors)
    check(sum(row["nuts"] for row in axis_rows) == 104 and sum(row["separate_washers"] for row in axis_rows) == 208, "structural nuts/washers do not sum to 104/208", errors)
    if errors:
        raise Blocked("hardware reconciliation failed:\n- " + "\n- ".join(errors))

    shared_8in = [row["axis_id"] for row in candidate_axes.values() if row["family_id"] in ("candidate_side_16", "candidate_top_rail_quarter_8in_4", "candidate_knee_inner_header_4")]
    check(len(shared_8in) == 20, "conditional shared 8-in Lawson lead must cover 20 axes", errors)
    if errors:
        raise Blocked("shared 8-in family count failed")

    body_mass = sum(row["mass_kg"] for row in body_rows)
    base_body_mass = sum(float(row["mass_kg"]) for row in weight_rows)
    body_mass_delta = body_mass - base_body_mass
    model_delta = sum(float(row["wood_mass_change_kg"]) for row in mass_changes.values())
    model_mass_rebuild = float(weights["modeled_mass_kg"]) + model_delta
    check(abs(model_mass_rebuild - float(model["modeled_mass_kg"])) < 1e-9, "corner model total does not equal baseline plus recorded 500 kg/m³ deltas", errors)
    if errors:
        raise Blocked("mass basis reconciliation failed")

    stock_classes = []
    for stock_class in ("2x6", "4x4", "4x6"):
        stock_classes.append(
            {
                "stock_class": stock_class,
                "old_piece_count": sum(1 for row in schedule if row["stock_class"] == stock_class),
                "new_piece_count": new_counts.get(stock_class, 0),
                "piece_count_delta": new_counts.get(stock_class, 0) - sum(1 for row in schedule if row["stock_class"] == stock_class),
                "old_blank_length_total_mm": old_lengths.get(stock_class, 0.0),
                "new_blank_length_total_mm": new_lengths.get(stock_class, 0.0),
                "blank_length_delta_mm": new_lengths.get(stock_class, 0.0) - old_lengths.get(stock_class, 0.0),
                "changed_bodies": ";".join(sorted(top_names)) if stock_class in ("4x4", "4x6") else "",
            }
        )
    scenarios_csv = [
        {
            "scenario_id": row["scenario_id"],
            "stock_length_options_ft": ",".join(str(value) for value in row["stock_length_options_ft"]),
            "trim_each_end_mm": row["trim_each_end_mm"],
            "sticks_2x6": row["sticks_by_class"]["2x6"],
            "sticks_4x4": row["sticks_by_class"]["4x4"],
            "sticks_4x6": row["sticks_by_class"]["4x6"],
            "sticks_total": row["sticks_total"],
            "placed_blanks": row["placed_blanks"],
            "requested_blanks": row["requested_blanks"],
            "unplaced_blanks": row["unplaced_blanks"],
            "unplaced_body_ids": ";".join(row["unplaced_body_ids"]),
            "all_44_placed": row["all_44_placed"],
            "heuristic": row["heuristic"],
        }
        for row in scenarios
    ]
    body_csv = []
    for row in body_rows:
        body_csv.append(
            {
                "body_id": row["body_id"],
                "kind": row["kind"],
                "finished_dim_axes": ";".join(row["local_dimensions"]["axes"]),
                "finished_dimensions_mm": ";".join(str(value) for value in row["local_dimensions"]["dimensions_mm"]),
                "stock_class": row["stock_class"],
                "stock_box_dimensions_mm": ";".join(str(value) for value in row["proposed_stock_box_mm"]),
                "prepared_stock_section_mm": ";".join(str(value) for value in row["prepared_stock_section_mm"]) if row["prepared_stock_section_mm"] else "",
                "finished_volume_mm3": row["finished_volume_mm3"],
                "density_kg_m3": row["density_kg_m3"],
                "mass_kg": row["mass_kg"],
                "previous_inventory_volume_mm3": row["previous_inventory_volume_mm3"],
                "volume_delta_mm3": row["volume_delta_mm3"],
                "stock_status": row["stock_status"],
                "volume_source_path": row["volume_source_path"],
                "volume_source_sha256": row["volume_source_sha256"],
                "shape_source_sha256": row["shape_source_sha256"],
                "shape_source_scope": row["shape_source_scope"],
            }
        )
    family_csv = [
        {
            "system": row.get("system", ""),
            "source_family_id": row.get("source_family_id", ""),
            "reconciled_family_id": row.get("reconciled_family_id", ""),
            "family": row.get("family", ""),
            "axes": row.get("axis_count", ""),
            "bolts": row.get("bolts", ""),
            "nuts": row.get("nuts", ""),
            "separate_washers": row.get("separate_washers", ""),
            "screws": row.get("screws", ""),
            "diameter_mm": row.get("diameter_mm", ""),
            "model_length_mm": row.get("model_length_mm", ""),
            "grip_mm": row.get("grip_mm", ""),
            "model_vs_catalog_length": row.get("model_vs_catalog_length", ""),
            "catalog_reference": row.get("catalog_reference", ""),
            "product_selected": row.get("product_selected", False),
            "capacity_assigned": row.get("capacity_assigned", False),
        }
        for row in family_rows
    ]

    pin_output = pins.output()
    body_change_rows = []
    for name in sorted(top_names):
        model_proposal = model_proposals[name]
        body_change_rows.append(
            {
                "body_id": name,
                "old_stock_class": "4x4",
                "new_stock_class": "4x6",
                "new_stock_box_mm": [88.9, 139.7, float(model_proposal["grain_length_mm"])],
                "finished_volume_mm3": float(model_proposal["finished_proposal_volume_mm3"]),
                "mass_at_600kg_m3": float(model_proposal["finished_proposal_volume_mm3"]) * DENSITY_KG_M3 * 1e-9,
                "corner_model_mass_delta_at_500kg_m3": float(mass_changes[name]["wood_mass_change_kg"]),
            }
        )
    assembly = {
        "schema": "wood-joints-assembly-package-reconciliation/v1",
        "status": "conditional inventory reconciliation; top proposal remains unselected",
        "candidate": model["candidate"],
        "source_revision": model["source_revision"],
        "body_counts": {"frame_timber": 20, "connector_blocks": 24, "panels": 6, "total": 50, "stock_blanks": 44},
        "body_mass": {
            "density_kg_m3": DENSITY_KG_M3,
            "density_basis": "recorded current board-weight inventory; planning assumption, not measured density",
            "finished_volume_total_mm3": sum(row["finished_volume_mm3"] for row in body_rows),
            "transport_body_mass_total_kg": body_mass,
            "previous_50_body_inventory_mass_kg": base_body_mass,
            "volume_adjustment_mass_at_600kg_m3": body_mass_delta,
            "corner_model_wood_mass_delta_at_500kg_m3": model_delta,
            "600kg_m3_adjustment_minus_500kg_m3_model_delta_kg": body_mass_delta - model_delta,
            "corner_frame_model_total_mass_kg": model["modeled_mass_kg"],
            "previous_full_model_total_mass_kg": weights["modeled_mass_kg"],
            "model_total_minus_transport_body_subtotal_kg": float(model["modeled_mass_kg"]) - body_mass,
            "scope_note": "Transport subtotal covers only 50 timber/block/panel bodies; frame model total includes other modeled hardware. Do not add or compare as equal scopes.",
            "side_volume_method": "old envelope finished volume + pinned corner-model mass delta / (500 kg/m³ × 1e-9 m³/mm³); then body mass uses 600 kg/m³ uniformly",
        },
        "top_corner_reconciliation": {
            "changed_bodies": body_change_rows,
            "old_4x4_volume_and_stock_envelope_reused": False,
            "top_local_dimensions_mm": [88.9, 139.7, 119.7],
        },
        "stock_reconciliation": {
            "old_counts": {key: sum(row["stock_class"] == key for row in schedule) for key in ("2x6", "4x4", "4x6")},
            "new_counts": new_counts,
            "classes": stock_classes,
            "scenarios": scenarios,
            "method": "pinned nesting helper; 3.2-mm kerf and recorded 0/10/20-mm trim cases",
            "purchase_optimum_or_price_established": False,
            "note": "Two top cleats move from 4x4 to 4x6. Recomputed 8/10/12/16-ft and mixed options; 8-ft cases require one extra 4x6 stick under this heuristic.",
        },
        "hardware": {
            "candidate_axes_bolts_nuts": 92,
            "retained_axes_bolts_nuts": 12,
            "structural_axes_bolts_nuts_washers": [104, 104, 208],
            "candidate_diameter_counts": {"6.35 mm (1/4 in)": 88, "7.9375 mm (5/16 in)": 4},
            "retained_diameter_counts": {"9.525 mm (3/8 in)": 8, "12.7 mm (1/2 in)": 4},
            "hillman_axes_screws_separate": 66,
            "removed_SDS25112_axes_not_included": 144,
            "historical_104_candidate_count_not_used": True,
            "top_axis_edits": [
                {"axis_ids": sorted(axis_id for axis_id, row in top_axis_data.items() if axis_id.endswith(("rail_1", "rail_2"))), "count": 4, "diameter_mm": 6.35, "old_grip_mm": 127.0, "new_grip_mm": 177.8, "model_length_mm": side_model_length, "model_vs_catalog_length": rail_model_vs_catalog, "catalog_reference": rail_catalog_ref},
                {"axis_ids": sorted(axis_id for axis_id in top_axis_data if axis_id.endswith(("side_1", "side_2"))), "count": 4, "diameter_mm": 7.9375, "grip_mm": 177.8, "model_length_mm": side_model_length, "model_vs_catalog_length": side_model_vs_catalog, "catalog_reference": side_catalog_ref},
            ],
            "conditional_top_catalog_options": {
                "source_path": top_hardware_inputs_rel,
                "source_sha256": digest(ROOT / top_hardware_inputs_rel),
                "observed_on": top_hardware.get("observed_on"),
                "status": top_hardware.get("status"),
                "product_selected": False,
                "side_5_16": side_catalog_summary,
                "rail_1_4": rail_catalog_summaries,
                "note": "Catalog length fields are distinct from modeled 203.2-mm underhead-to-tip lengths; exact delivered threads and complete installed fit remain unresolved.",
            },
            "conditional_shared_Lawson_8in_axes": sorted(shared_8in),
            "conditional_shared_Lawson_8in_count": len(shared_8in),
            "hillman_length_mm": {"purchased": 63.5, "occupied_model_envelope": 50.8},
            "product_or_capacity_selected": False,
            "families": family_rows,
        },
        "bodies": body_rows,
        "source_pins": pin_output,
    }
    return {
        "reconciled-assembly.json": json_bytes(assembly),
        "bodies.csv": csv_bytes(body_csv, ["body_id", "kind", "finished_dim_axes", "finished_dimensions_mm", "stock_class", "stock_box_dimensions_mm", "prepared_stock_section_mm", "finished_volume_mm3", "density_kg_m3", "mass_kg", "previous_inventory_volume_mm3", "volume_delta_mm3", "stock_status", "volume_source_path", "volume_source_sha256", "shape_source_sha256", "shape_source_scope"]),
        "hardware-families.csv": csv_bytes(family_csv, ["system", "source_family_id", "reconciled_family_id", "family", "axes", "bolts", "nuts", "separate_washers", "screws", "diameter_mm", "model_length_mm", "grip_mm", "model_vs_catalog_length", "catalog_reference", "product_selected", "capacity_assigned"]),
        "hardware-axes.csv": csv_bytes(axis_rows, ["fastener_type", "axis_id", "system", "source_family_id", "family_id", "family", "diameter_mm", "model_length_mm", "grip_mm", "old_grip_mm", "catalog_reference", "catalog_status", "bolts", "nuts", "separate_washers", "screws"]),
        "stock-classes.csv": csv_bytes(stock_classes, ["stock_class", "old_piece_count", "new_piece_count", "piece_count_delta", "old_blank_length_total_mm", "new_blank_length_total_mm", "blank_length_delta_mm", "changed_bodies"]),
        "stock-scenarios.json": json_bytes({"schema": "wood-joints-replacement-aware-stock-nesting/v1", "scenarios": scenarios, "source_pins": pin_output, "purchase_optimum_or_price_established": False}),
        "stock-scenarios.csv": csv_bytes(scenarios_csv, ["scenario_id", "stock_length_options_ft", "trim_each_end_mm", "sticks_2x6", "sticks_4x4", "sticks_4x6", "sticks_total", "placed_blanks", "requested_blanks", "unplaced_blanks", "unplaced_body_ids", "all_44_placed", "heuristic"]),
    }


def write_blocker(message: str) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "blockers.json").write_bytes(json_bytes({"status": "blocked; no reconciliation result produced", "reason": message}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write ignored JSON/CSV outputs (default)")
    mode.add_argument("--verify", action="store_true", help="compare outputs to regenerated bytes")
    args = parser.parse_args()
    try:
        outputs = build()
    except (Blocked, OSError, KeyError, TypeError, ValueError) as exc:
        # Report unavailable or malformed inputs; unexpected implementation
        # errors, including nesting invariant failures, retain their traceback.
        message = str(exc)
        print(message, file=sys.stderr)
        write_blocker(message)
        return 2
    if args.verify:
        failed = []
        for name, content in outputs.items():
            path = RAW / name
            if not path.is_file() or path.read_bytes() != content:
                failed.append(name)
        if failed:
            print("missing or mismatched output(s): " + ", ".join(failed), file=sys.stderr)
            return 1
        for name, content in outputs.items():
            print(f"verified {RAW.relative_to(ROOT) / name} sha256={hashlib.sha256(content).hexdigest()}")
        return 0
    RAW.mkdir(parents=True, exist_ok=True)
    stale_blocker = RAW / "blockers.json"
    if stale_blocker.exists():
        stale_blocker.unlink()
    for name, content in outputs.items():
        path = RAW / name
        path.write_bytes(content)
        print(f"wrote {path.relative_to(ROOT)} sha256={hashlib.sha256(content).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
