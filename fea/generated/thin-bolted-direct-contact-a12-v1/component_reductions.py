"""Small complete-atlas bridge to unchanged first-order component methods.

Only the new admission's cheap immutable-payload validator is called here.
No legacy consumer/admission, constant patch, operator replay or solve occurs.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

import numpy as np

from scripts import thin_bolted_joint_post_admission as pure

ROOT = pure.ROOT
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PURE_SHA = "e63aa17cb56b71feb4c700d6bc0ffb4b801f7716753d350ae475409dc2470e5a"
GATE = ROOT / "fea/generated/thin-bolted-direct-contact-a12-v1/admission.py"
SCHEMA = "thin_bolted_complete_atlas_post_admission_references/v1"
METHOD = "source-bound-linear-complete-atlas-wood-compression-v1"
IDENTITIES = pure.IDENTITIES


def _load_gate(expected):
    pure.unit.require(isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected) is not None
                      and pure.unit.sha(GATE) == expected, "mandatory reviewed complete-atlas gate SHA differs")
    spec = importlib.util.spec_from_file_location("complete_timber_component_admission", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pure.unit.require(module.LOADED_PRODUCER_SHA256 == expected and pure.unit.sha(GATE) == expected,
                      "complete-atlas gate changed while loaded")
    return module


def face_diagnostics(demand, full):
    """Reference N/A and own grain geometry; no automatic allowable pressure."""
    cells = [r for r in demand["contact_actions"] if r["kind"] == "timber_face_contact"]
    alias = demand["timber_face_contact_actions"]
    indexed = {r["id"]: r for r in cells}
    pure.unit.require(len(indexed) == len(cells) == len(alias) == 584
                      and indexed == {r["id"]: r for r in alias}, "all584 unique faces and exact unused alias required")
    grains = {r["member"]: np.asarray(r["grain_axis_xyz"], dtype=float) for r in full["finished_member_sections"]}
    groups = {}
    for row in cells:
        pure.unit.require(all(row.get(k) == demand[k] for k in IDENTITIES), "face mixes admitted identity")
        area, force = row["cell_area_mm2"], row["compression_n"]
        normal = np.asarray(row["direction_xyz"], dtype=float)
        pure.unit.require(math.isfinite(area) and area > 0. and math.isfinite(force) and force >= 0.
                          and normal.shape == (3,) and np.isfinite(normal).all()
                          and abs(np.linalg.norm(normal) - 1.) < 1e-8, "invalid reference cell force/area/normal")
        host_rows = []
        for host in (row["first"], row["second"]):
            grain = grains[host]
            pure.unit.require(grain.shape == (3,) and np.isfinite(grain).all()
                              and abs(np.linalg.norm(grain) - 1.) < 1e-8, "unit own timber grain required")
            dot = float(normal @ (grain / np.linalg.norm(grain)))
            cosine = float(np.clip(abs(dot), 0., 1.))
            classification = "perpendicular" if cosine < 1e-8 else "parallel" if 1. - cosine < 1e-8 else "oblique"
            host_rows.append({"member": host, "normal_dot_reference_grain": dot,
                "acute_normal_to_reference_grain_degrees": math.degrees(math.acos(cosine)),
                "reference_grain_classification": classification,
                "perpendicular_Fc_material_reference_applicability_geometry_only": classification == "perpendicular",
                "allowable_pressure_mpa": None, "adjusted_bearing_resistance_or_ratio": None})
        witness = {**{k: row[k] for k in (*IDENTITIES, "id", "first", "second", "point_xyz_mm")},
            "compression_n": force, "reference_cell_area_mm2": area,
            "direction_reference_xyz": normal.tolist(),
            "normal_force_over_reference_cell_area_mpa": force / area, "own_host_grain_geometry": host_rows,
            "force_is_a_discrete_reference_foundation_resultant": True,
            "continuous_current_pressure_or_complete_joint_capacity": None}
        groups.setdefault((row["first"], row["second"]), []).append(witness)
    pure.unit.require(len(groups) == 30, "all30 source timber pairs required")
    return [{"first": pair[0], "second": pair[1], "cells_including_zeros": len(rows),
        "loaded_cells": sum(r["compression_n"] > 0. for r in rows),
        "total_model_compression_n": sum(r["compression_n"] for r in rows),
        "reference_area_mm2": sum(r["reference_cell_area_mm2"] for r in rows),
        "governing_discrete_reference_area_pressure_witness": max(rows, key=lambda r: r["normal_force_over_reference_cell_area_mpa"]),
        "own_host_material_allowables_or_joint_capacity": None} for pair, rows in groups.items()]


def _governing(wood, metal, sheets):
    """Select exported coherent witnesses without inventing a missing rating."""
    values = {}
    for name in ("tension", "compression"):
        rows = [r[f"maximum_{name}_average_area_witness"] for r in wood["simultaneous_existing_member_cut_witnesses"]]
        values["timber_average_" + name + "_CD1"] = max(rows, key=lambda r: r[name + "_average_area_reference"]["CD1_same_state_component_ratio"])
    values["own_wood_capture_ideal_annulus_no_CD"] = max(wood["own_direct_wood_capture_annulus_references"],
        key=lambda r: r["own_model_capture_over_ideal_annulus_component_ratio"])
    shaft = [{"axis_id": r["axis_id"], **s} for r in metal["shaft_same_section_references"] for s in r["section_scenarios"]]
    values["shaft_same_cut_conditional_circle_Grade5_Fy"] = max(shaft,
        key=lambda r: r["sampled_governing_section"]["same_section_nominal_first_yield_index"])
    values["generic_screw_head_CD1"] = max(sheets["screw_actions_and_generic_references"], key=lambda r: r["generic_head_ratio_CD1"])
    for scenario in ("gross_rectangle", "two_ligament_equal_twist_proxy"):
        eligible = [r for r in metal["flange_torsion_diagnostics"] if r["sampled_scenario_witnesses"][scenario] is not None]
        values["flange_" + scenario + "_torsion_bound_Fy33ksi"] = max(eligible,
            key=lambda r, scenario=scenario: r["sampled_scenario_witnesses"][scenario]["simultaneous_nominal_first_yield_bound_index"], default=None)
    for key in ("mean_net_bending_ratio_CD1", "mean_net_rolling_shear_ratio_CD1", "mean_net_axial_ratio_CD1"):
        rows = [{"panel": r["panel"], **r["integrated_net_section_diagnostics"]["simultaneous_signed_cut_witnesses"][key]}
                for r in sheets["panel_diagnostics"]]
        values["panel_" + key] = max(rows, key=lambda r, key=key: r[key])
    values["discrete_wood_face_N_over_Aref_mpa"] = max(
        (r["governing_discrete_reference_area_pressure_witness"] for r in wood["thirty_face_grain_and_area_diagnostics"]),
        key=lambda r: r["normal_force_over_reference_cell_area_mpa"])
    return {key: {"coherent_witness": witness, "status": "CONDITIONAL_DIAGNOSTIC_ONLY",
                  "adopted_complete_resistance_or_joint_pass": None} for key, witness in values.items()}


def _reduce(demand, *, samples, caller_sections):
    references, timber, steel = pure.references, pure.timber, pure.steel
    packet, _, layout = references.read_unit()
    detail = packet["reproducible_detail_artifact"]
    pins = {detail["path"]: detail["sha256"], str(references.UNIT.relative_to(ROOT)): references.UNIT_SHA}
    for report in (packet, json.loads(steel.methods.METHODS.read_bytes()), json.loads(steel.methods.HEAD.read_bytes())):
        for relative, digest in report["source_sha256"].items():
            pure.unit.require(relative not in pins or pins[relative] == digest, "component reports contradict a source")
            pins[relative] = digest
    pure.verify_pins(pins)
    full = json.loads((ROOT / detail["path"]).read_bytes())["finished_geometry_queries"]
    timber.verify_alias_state_labels(demand)
    steel.verify_component_state_labels(demand)
    wood = timber.aggregate_wood_bearings(layout, {"finished_geometry_queries": full}, demand)
    spans = timber.read_member_span_geometry()
    span_receipt = timber.verify_member_span_geometry(demand, spans)
    cuts = timber.replay_existing_member_cuts(demand, full, spans)
    duration = references.read_duration_sources()
    properties = []
    for name, digest in pure.PROPERTY_PINS.items():
        path = pure.PACKET / name
        pins[str(path.relative_to(ROOT))] = digest
        pure.verify_pins({str(path.relative_to(ROOT)): digest})
        report = json.loads(path.read_bytes())
        pure.unit.require(report["state_id"] is None and report["candidate"] == pure.unit.CANDIDATE
                          and not any(report["release"].values()), "only unchanged geometry-only section properties reused")
        properties.extend(report["finished_sections"])
        for relative, expected in report["source_sha256"].items():
            pure.unit.require(relative not in pins or pins[relative] == expected, "section properties contradict a source")
            pins[relative] = expected
    receivers = {(r["axis_id"], r["member"]): r for r in full["receiver_boundary_geometry"]}
    wood_result = {"actual82wood_bearing_wrenches": wood,
        "actual164body_root_bearing_parameter_diagnostics": timber.bearing_parameter_diagnostics(wood, layout),
        "own_direct_wood_capture_annulus_references": timber.own_wood_washer_references(demand, packet),
        "simultaneous_existing_member_cut_witnesses": cuts,
        "current70conditional_thread_windows": [references.standard_thread_window(a, receivers) for a in layout["installed_axes"]],
        "thirty_face_grain_and_area_diagnostics": face_diagnostics(demand, full),
        "independent_member_span_geometry": span_receipt, "conditional_duration_source": duration,
        "five_existing_geometry_only_section_properties": properties,
        "actual_trimmed_normal_stress_extrema_and_complete_member_resistance": None,
        "general_unequal_shared_shaft_ASD_group_splitting_resistance": None}
    metal = steel.component_values(demand, caller_sections)
    metal["flange_torsion_diagnostics"] = pure.flange_torsion_reductions(demand, metal, layout)
    sheets = pure.panel_reductions(demand, layout, samples)
    pure.unit.require(len(wood) == 82 and len(cuts) == 20 and len(properties) == 5
                      and len(wood_result["own_direct_wood_capture_annulus_references"]) == 68,
                      "unchanged own component census required")
    for row in duration["authenticated_primary_sources"]:
        pins[row["path"]] = row["sha256"]
    pins[duration["source_metadata_path"]] = duration["source_metadata_sha256"]
    return {"timber": wood_result, "steel": metal, "panels": sheets,
            "governing_conditional_diagnostic_witnesses": _governing(wood_result, metal, sheets)}, pins


def consume(field_path, admission, *, expected_field_sha256, admission_sha256, samples=41, caller_sections=None):
    """Exact fresh bytes + NEW original-gradient receipt -> pure references."""
    path = Path(field_path).resolve()
    payload = path.read_bytes()
    pure.unit.require(isinstance(expected_field_sha256, str)
                      and re.fullmatch("[0-9a-f]{64}", expected_field_sha256) is not None
                      and hashlib.sha256(payload).hexdigest() == expected_field_sha256,
                      "mandatory released fresh raw byte hash differs")
    pure.unit.require(type(samples) is int and 3 <= samples <= 101, "panel samples from3 to101 required")
    before = pure.references.canonical_sha(admission), pure.references.canonical_sha(caller_sections)
    gate = _load_gate(admission_sha256)
    demand, verified_pins = gate.require_admitted_payload(payload, admission, admission_sha256=admission_sha256)
    demand_before = pure.references.canonical_sha(demand)
    pure.unit.require(demand.get("linear_timber_face_method") == METHOD
                      and demand_before == pure.references.canonical_sha(json.loads(payload)),
                      "NEW validator must return unchanged complete-atlas field")
    pins = {**pure.PINS, str(Path(pure.__file__).relative_to(ROOT)): PURE_SHA,
            str(GATE.relative_to(ROOT)): admission_sha256, str(OWN.relative_to(ROOT)): LOADED_SHA,
            str(path.relative_to(ROOT)): expected_field_sha256}
    for source in (verified_pins, demand["source_sha256"], admission["source_sha256"]):
        for relative, digest in source.items():
            pure.unit.require(relative not in pins or pins[relative] == digest, "contradictory fresh source pin")
            pins[relative] = digest
    pure.verify_pins(pins)
    values, extra_pins = _reduce(demand, samples=samples, caller_sections=caller_sections)
    for relative, digest in extra_pins.items():
        pure.unit.require(relative not in pins or pins[relative] == digest, "component source contradicts fresh admission")
        pins[relative] = digest
    pure.unit.require(path.read_bytes() == payload and pure.unit.sha(GATE) == admission_sha256
                      and pure.references.canonical_sha(demand) == demand_before
                      and (pure.references.canonical_sha(admission), pure.references.canonical_sha(caller_sections)) == before,
                      "field/gate/input changed during pure reductions")
    pure.verify_pins(pins)
    return {"schema": SCHEMA, **{key: demand[key] for key in IDENTITIES},
        "field_sha256": expected_field_sha256, "field_canonical_sha256": demand_before,
        "independent_complete_timber_admission": admission, "source_sha256": pins, **values,
        "method": {"same_immutable_admitted_bytes": True, "new_584_faces_collected_once_from_contact_actions": True,
                   "face_alias_appended_or_old272_admission_called": False,
                   "own_shaft_cuts_include_only_own_bearings_captures_body_loads": True,
                   "CAD_K_native_operator_replay_or_response_solve": False},
        "limits": ["N/Aref is a discrete foundation diagnostic; reference grain classification is not an allowable contact pressure or current footprint.",
            "Own capture actions/couples are point-model actions, not resolved annular-face prying moments or pressures.",
            "Fe/Fyb/root and Grade5 Fy scenarios are not adopted actual bolt or complete joint resistances; general unequal-shaft ASD remains null.",
            "Actual threads, Fu/Fyb, washer material/pressure, Hillman ratings, group/splitting/shear/stability and net-stiffness qualification remain unresolved."],
        "complete_joint_resistance": None, "complete_joint_acceptance": False, "release": dict(pure.unit.RELEASE)}
