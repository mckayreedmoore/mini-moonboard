"""Prepare current same-state demands for a two-loose-washer comparison.

Importing this module is inert. ``load_current_cases`` authenticates and reads
the already saved current dispositions; ``load_engine`` imports the pinned
Mindlin helpers; ``make_stack_model`` and ``solve_case`` are called by the
parent-owned serialized run only. Each plate keeps the current profile's own
thickness and constitutive law. The doubled operator is the sum of two
identical plates on an admissible common-field branch, with an explicit
compression-only interface pressure witness; it is not a bonded 2t plate.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-working-profile-completion"
PROFILE_DIR = RAW / "preparation01"
FULL_DIR = RAW / "plate-current-full01"
DISPOSITION_DIR = RAW / "plate-current-dispositions01"

STACKED = HERE / "stacked-washers.py"
EDGE = HERE / "upper-right-washer-edge.py"
FLEXURE = HERE / "upper-right-washer-flexure.py"
PROFILE_API = HERE / "washer-working-profile-completion.py"

PINS = {
    STACKED: "974331e6c98f07b7957adf86ebf3fd7c546e8926133ce0f6c43d5ee02a34eb97",
    EDGE: "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61",
    FLEXURE: "782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac",
    PROFILE_API: "6dd34bc0bd0d92da590cfedff8cdbfc6305843161e2cd95102b397e8eb9525f4",
    PROFILE_DIR / "receipt.json": "8f64eabfd382d51b2cf5cf0aa67c2149bc13cb7ea825ebe076572c80418a89c1",
    PROFILE_DIR / "profile-contract.json": "793848a80900c4fc8f13472f148680b96cf588b58ab5c455ae5aea7a408e9f93",
    FULL_DIR / "receipt.json": "5d7d97048f8d9f9726b5633a7ab5be4e660582da377c4a104b81e59c37c84c56",
    FULL_DIR / "end-states.jsonl": "bb24f618896033c73d963dcccdbd74505f151f27cf012ae335c89afded4478e2",
    DISPOSITION_DIR / "receipt.json": "86b9d36cc74904ce466a3efd21dfc54ab9a3c36dea235cc7f60928d6b4fa22df",
    DISPOSITION_DIR / "summary.json": "eeb2f6a34ecf94b8042280d2235267be0c44876f4c29882ef345855b98c95c1f",
}

EXPECTED_EXCEEDANCES = 18
EXPECTED_SELECTED_END_STATES = 144
EXPECTED_PHYSICAL_ENDS = 12
EXPECTED_AXES = 7
EXPECTED_PROFILE_ENDS = {"retained_15023": 4, "retained_15025": 6, "top_rail_wide": 2}
EXPECTED_HYPOTHESES = {
    "E_mpa": 200000.0,
    "nu": 0.3,
    "Fy_mpa": 250.0,
    "Kwood_mpa_per_mm": 20.0,
    "Khead_mpa_per_mm": 10000.0,
    "preload_n": 0.0,
    "first_order": True,
    "concentric_nominal_seats": True,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _check_pins() -> None:
    for path, digest in PINS.items():
        require(path.is_file() and sha(path) == digest, f"pinned source differs: {path}")


def _check_packet_receipts(contract: dict[str, Any], summary: dict[str, Any]) -> dict[str, str]:
    preparation = _json(PROFILE_DIR / "receipt.json")
    full = _json(FULL_DIR / "receipt.json")
    dispositions = _json(DISPOSITION_DIR / "receipt.json")
    require(preparation["schema"] == "washer_working_profile_preparation_receipt/v1"
            and preparation["output_sha256"].get("profile-contract.json") == PINS[PROFILE_DIR / "profile-contract.json"],
            "working profile contract is outside its preparation receipt")
    require(full["schema"] == "current_force_washer_plate_receipt/v1"
            and full["output_sha256"].get("end-states.jsonl") == PINS[FULL_DIR / "end-states.jsonl"],
            "current plate fields are outside their receipt")
    require(dispositions["schema"] == "current_force_washer_plate_receipt/v1"
            and dispositions["output_sha256"].get("summary.json") == PINS[DISPOSITION_DIR / "summary.json"],
            "current dispositions are outside their receipt")
    require(contract["schema"] == "washer_working_profile_contract/v1"
            and contract["status"] == "FROZEN_NUMERICAL_PROFILE_CONTRACT",
            "working profile contract schema/status differs")
    require(summary["schema"] == "current_force_washer_plate_dispositions/v1"
            and summary["status"] == "COMPLETE_CURRENT_WASHER_END_NUMERICAL_DISPOSITIONS"
            and summary["force_branch"] == "washer_updated_compatible_frame",
            "current disposition packet is not the pinned accepted force branch")
    require(summary["counts"]["finite_metal_fields"] == 2400
            and summary["counts"]["sampled_Fy250_exceedances"] == EXPECTED_EXCEEDANCES
            and summary["counts"]["unavailable_required_state_ends"] == 416,
            "current washer field census differs")
    hypotheses = contract["hypotheses"]
    require(hypotheses == EXPECTED_HYPOTHESES and hypotheses["Fy_mpa"] == 250.0,
            "washer contact/material hypotheses differ")
    return {
        "profile_preparation_receipt_sha256": PINS[PROFILE_DIR / "receipt.json"],
        "current_plate_receipt_sha256": PINS[FULL_DIR / "receipt.json"],
        "current_dispositions_receipt_sha256": PINS[DISPOSITION_DIR / "receipt.json"],
    }


def _plate_sources_by_index(path: Path, indices: set[int]) -> dict[int, dict[str, Any]]:
    """Read only the selected, receipt-indexed records from the large JSONL."""
    found: dict[int, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index in indices:
                found[index] = json.loads(line)
                if len(found) == len(indices):
                    break
    require(found.keys() == indices, "one or more referenced current plate records are missing")
    return found


def _profile_for_source(source: dict[str, Any], contract: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    binding = source["geometry"]["profile_binding"]
    profile_id = binding["profile_id"]
    require(profile_id in contract["profiles"], "source washer profile is absent from the working contract")
    profile = contract["profiles"][profile_id]
    actual = binding["plate_profile"]
    for name in ("inner_radius_mm", "outer_radius_mm", "head_radius_mm", "thickness_mm"):
        require(math.isclose(float(actual[name]), float(profile[name]), rel_tol=0.0, abs_tol=1e-12),
                f"current modeled {name} differs from its working profile")
    require(binding["part"] == profile["part"], "current modeled washer part label differs")
    require(source["geometry"]["kind"] == "FULL_CONCENTRIC_ANNULUS"
            and source["geometry"]["nominal_concentric_geometry_only"] is True
            and source["geometry"]["loaded_shift_or_tilt_qualified"] is False,
            "selected exceedance is outside the full concentric annulus method")
    return profile_id, {name: float(actual[name]) for name in
                        ("inner_radius_mm", "outer_radius_mm", "head_radius_mm", "thickness_mm")}


def load_current_cases(include_all_selected_end_states: bool = False) -> dict[str, Any]:
    """Authenticate saved same-state inputs for the 12 selected physical ends.

    By default, return the 18 same-state fields that seeded this correction.
    With ``include_all_selected_end_states=True``, return all 144 finite saved
    state fields on those same 12 physical ends. This is a read-only source
    preflight: it does not import NumPy/SciPy or build a plate model. Every
    returned input retains its own current T/M and source record pointers;
    repeated states on one physical end remain separate cases.
    """
    _check_pins()
    contract = _json(PROFILE_DIR / "profile-contract.json")
    summary = _json(DISPOSITION_DIR / "summary.json")
    receipt_pins = _check_packet_receipts(contract, summary)
    indexed_dispositions = list(enumerate(summary["end_dispositions"]))
    exceedances = [(index, row) for index, row in indexed_dispositions
                   if row.get("metal_reference_index") is not None and row["metal_reference_index"] > 1.0]
    require(len(exceedances) == EXPECTED_EXCEEDANCES, "same-state hypothetical-yield exceedance census differs")
    selected_end_keys = {(row["join_key"][2], row["join_key"][3]) for _index, row in exceedances}
    selected_rows = ([(index, row) for index, row in indexed_dispositions
                      if (row["join_key"][2], row["join_key"][3]) in selected_end_keys]
                     if include_all_selected_end_states else exceedances)
    if include_all_selected_end_states:
        require(len(selected_end_keys) == EXPECTED_PHYSICAL_ENDS
                and len(selected_rows) == EXPECTED_SELECTED_END_STATES,
                "all-state expansion for the selected physical ends differs from 144 records")
        identities = [(row["join_key"][1], row["join_key"][2], row["join_key"][3])
                      for _index, row in selected_rows]
        require(len(set(identities)) == EXPECTED_SELECTED_END_STATES,
                "all-state expansion merged or duplicated a same-state physical-end record")
    indexes: set[int] = set()
    for _index, row in selected_rows:
        reference = row["source_plate_record"]
        require(reference["path"] == str((FULL_DIR / "end-states.jsonl").relative_to(ROOT))
                and reference["sha256"] == PINS[FULL_DIR / "end-states.jsonl"],
                "current disposition points outside the pinned plate fields")
        pointer = reference["pointer"]
        require(pointer.startswith("/") and pointer.count("/") == 1, "current plate record pointer is malformed")
        indexes.add(int(pointer[1:]))
    plate_records = _plate_sources_by_index(FULL_DIR / "end-states.jsonl", indexes)

    cases: list[dict[str, Any]] = []
    unique_ends: dict[tuple[str, str], dict[str, Any]] = {}
    for disposition_index, disposition in selected_rows:
        reference = disposition["source_plate_record"]
        index = int(reference["pointer"][1:])
        result = plate_records[index]
        source = result["source"]
        join_key = disposition["join_key"]
        require(result["status"] == "FINITE_CURRENT_FORCE_ELASTIC_PLATE_REFERENCE"
                and result["stress_proxy_over_Fy250"] is not None,
                "a selected current end is not a finite plate result")
        require([source["join_key"][0], source["state_tag"], source["axis_id"], source["end_role"],
                 source["receiver_member"]] == join_key,
                "current source identity differs from its disposition join")
        require(math.isclose(float(result["stress_proxy_over_Fy250"]),
                             float(disposition["metal_reference_index"]), rel_tol=1e-12, abs_tol=1e-12),
                "current disposition index differs from its own saved plate field")

        profile_id, profile = _profile_for_source(source, contract)
        tension = float(source["T_n"])
        moment = float(source["M_magnitude_nmm"])
        moment_vector = source["source_signed_own_M_xyz_nmm"]
        require(math.isfinite(tension) and tension > 0 and math.isfinite(moment) and moment >= 0
                and len(moment_vector) == 3 and all(math.isfinite(float(x)) for x in moment_vector),
                "current own-end demand contains an invalid T/M")
        first = source["plate_pressure_first_moment_targets_nmm"]
        require(len(first) == 2 and math.isclose(float(first[0]), moment, rel_tol=1e-8, abs_tol=0.02)
                and abs(float(first[1])) <= 0.02,
                "the saved own-end moment does not match the plate chart demand")
        require(source["source_force_compatibility"] is False,
                "current isolated end field unexpectedly claims global force compatibility")
        require(source["head_compression_certificate"]["status"] == "ELIGIBLE_POSITIVE_T_FINE_REFERENCE",
                "selected current demand is outside the compression-only head branch")

        baseline_stress = float(result["sampled_stress_proxy_mpa"])
        baseline_index = float(result["stress_proxy_over_Fy250"])
        end_key = (source["axis_id"], source["end_role"])
        prior = unique_ends.get(end_key)
        if prior is not None:
            require(prior["profile_id"] == profile_id and prior["profile"] == profile,
                    "one physical end changes current washer profile between saved states")
        else:
            unique_ends[end_key] = {"profile_id": profile_id, "profile": profile}

        input_pointer = {"path": str((FULL_DIR / "end-states.jsonl").relative_to(ROOT)),
                         "record_index": index, "sha256": PINS[FULL_DIR / "end-states.jsonl"]}
        compact_source = {
            "T_n": tension,
            "M_magnitude_nmm": moment,
            "state_tag": source["state_tag"],
            "case_id": source["case_id"],
            "gap_scale": source["gap_scale"],
            "axis_id": source["axis_id"],
            "end_role": source["end_role"],
            "receiver_member": source["receiver_member"],
            "force_branch": source["join_key"][0],
            "source_force_compatibility": False,
            "source_signed_own_M_xyz_nmm": [float(x) for x in moment_vector],
            "plate_pressure_first_moment_targets_nmm": [float(x) for x in first],
            "chart_x_xyz": [float(x) for x in source["chart_x_xyz"]],
            "chart_y_xyz": [float(x) for x in source["chart_y_xyz"]],
            "normal_into_receiver_xyz": [float(x) for x in source["normal_into_receiver_xyz"]],
            "geometry": {
                "kind": source["geometry"]["kind"],
                "supported_area_mm2": float(source["geometry"]["supported_area_mm2"]),
                "nominal_concentric_geometry_only": True,
                "loaded_shift_or_tilt_qualified": False,
                "profile_binding": {
                    "profile_id": profile_id,
                    "part": source["geometry"]["profile_binding"]["part"],
                    "plate_profile": profile,
                    "hypotheses": deepcopy(source["geometry"]["profile_binding"]["hypotheses"]),
                },
            },
            "source_state_record": deepcopy(source.get("source_state_record")),
            "source_end_record": deepcopy(source.get("source_endrecord")),
            "source_axis_state_record": deepcopy(source.get("source_join", {}).get("source_axis_state_record")),
        }
        stack_added = profile["thickness_mm"]
        cases.append({
            "case_id": source["case_id"],
            "state_tag": source["state_tag"],
            "gap_scale": source["gap_scale"],
            "axis_id": source["axis_id"],
            "end_role": source["end_role"],
            "receiver_member": source["receiver_member"],
            "join_key": join_key,
            "profile_id": profile_id,
            "profile": profile,
            "T_n": tension,
            "M_magnitude_nmm": moment,
            "source_signed_own_M_xyz_nmm": compact_source["source_signed_own_M_xyz_nmm"],
            "plate_pressure_first_moment_targets_nmm": compact_source["plate_pressure_first_moment_targets_nmm"],
            "source_force_compatibility": False,
            "single_washer_reference": {"sampled_stress_proxy_mpa": baseline_stress,
                                        "over_hypothetical_Fy250": baseline_index,
                                        "current_field_same_state": True},
            "source_input": input_pointer,
            "source_disposition_pointer": {"record_index": disposition_index,
                                           "summary_path": str((DISPOSITION_DIR / "summary.json").relative_to(ROOT)),
                                           "summary_sha256": PINS[DISPOSITION_DIR / "summary.json"]},
            "solver_source": compact_source,
            "fit_grip_applicability": {
                "current_washers_per_physical_end": 1,
                "analyzed_washers_per_physical_end": 2,
                "additional_washers_at_end": 1,
                "conditional_exterior_stack_increase_mm": stack_added,
                "wood_grip_change_mm": 0.0,
                "bolt_length_and_thread_engagement_rechecked": False,
                "purchased_or_cad_inventory_changed": False,
            },
        })

    expected_case_count = EXPECTED_SELECTED_END_STATES if include_all_selected_end_states else EXPECTED_EXCEEDANCES
    require(len(cases) == expected_case_count
            and len({(c["state_tag"], c["axis_id"], c["end_role"]) for c in cases}) == expected_case_count,
            "selected cases were merged across states")
    require(len(unique_ends) == EXPECTED_PHYSICAL_ENDS, "physical washer end count differs")
    require(len({axis for axis, _end in unique_ends}) == EXPECTED_AXES, "affected bolt axis count differs")
    end_counts: dict[str, int] = {}
    for value in unique_ends.values():
        end_counts[value["profile_id"]] = end_counts.get(value["profile_id"], 0) + 1
    require(end_counts == EXPECTED_PROFILE_ENDS, "selected physical ends no longer match the three current profiles")
    return {
        "schema": "current_two_washer_stack_inputs/v1",
        "status": "PREPARED_CURRENT_SAME_STATE_CASES_NO_MECHANICS_RUN",
        "case_count": len(cases),
        "include_all_selected_end_states": include_all_selected_end_states,
        "exceedance_seed_case_count": EXPECTED_EXCEEDANCES,
        "case_scope": ("all_accepted_states_for_selected_physical_ends"
                       if include_all_selected_end_states else "hypothetical_Fy250_exceedance_seed_fields"),
        "physical_end_count": len(unique_ends),
        "axis_count": EXPECTED_AXES,
        "current_one_washer_physical_quantity": contract["counts"]["physical_washers"],
        "conditional_added_washer_quantity": len(unique_ends),
        "illustrative_whole_candidate_washer_quantity_if_scope_is_adopted":
            contract["counts"]["physical_washers"] + len(unique_ends),
        "cases": cases,
        "unique_physical_ends": [
            {"axis_id": axis, "end_role": end_role,
             "profile_id": unique_ends[(axis, end_role)]["profile_id"],
             "profile": unique_ends[(axis, end_role)]["profile"]}
            for axis, end_role in sorted(unique_ends)
        ],
        "fit_grip_impacts_by_axis": _fit_grip_impacts(unique_ends),
        "hypotheses": deepcopy(contract["hypotheses"]),
        "source_pins": {**{str(path.relative_to(ROOT)): digest for path, digest in PINS.items()}, **receipt_pins},
        "applicability": {
            "current_demand_is_same_state_own_end_T_and_M": True,
            "mixed_state_force_or_moment_maxima_used": False,
            "scalar_own_end_curvature_is_globally_compatible": False,
            "nominal_support_masks_qualify_loaded_shift_or_tilt": False,
            "Fy250_is_a_hypothesis_not_a_published_washer_property": True,
            "actual_washer_yield_mpa": None,
            "actual_washer_capacity_n": None,
            "preload_or_friction_included": False,
            "complete_joint_acceptance": False,
            "physical_release": False,
        },
    }


def _fit_grip_impacts(unique_ends: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    by_axis: dict[str, dict[str, float]] = {}
    for (axis_id, end_role), row in unique_ends.items():
        value = by_axis.setdefault(axis_id, {"head_stack_increase_mm": 0.0, "nut_stack_increase_mm": 0.0})
        slot = "head_stack_increase_mm" if end_role == "head" else "nut_stack_increase_mm"
        value[slot] += row["profile"]["thickness_mm"]
    return [
        {"axis_id": axis_id, **values,
         "combined_exterior_stack_increase_mm": values["head_stack_increase_mm"] + values["nut_stack_increase_mm"],
         "wood_grip_change_mm": 0.0,
         "bolt_length_and_thread_engagement_rechecked": False}
        for axis_id, values in sorted(by_axis.items())
    ]


def known_answer_coupon(profile: dict[str, Any], hypotheses: dict[str, Any] | None = None,
                        tension_n: float = 100.0) -> dict[str, Any]:
    """Exact full-face two-plate compression/contact coupon, without model build."""
    assumptions = EXPECTED_HYPOTHESES if hypotheses is None else hypotheses
    inner, outer = float(profile["inner_radius_mm"]), float(profile["outer_radius_mm"])
    thickness = float(profile["thickness_mm"])
    kwood = float(assumptions["Kwood_mpa_per_mm"])
    khead = float(assumptions["Khead_mpa_per_mm"])
    require(0.0 < inner < outer and thickness > 0 and tension_n > 0 and kwood > 0 and khead > 0,
            "invalid known-answer coupon input")
    area = math.pi * (outer * outer - inner * inner)
    pressure = tension_n / area
    wood_deflection = pressure / kwood
    head_closure = pressure / khead
    interface_pressure = (pressure + pressure) / 2.0
    require(math.isclose(pressure * area, tension_n, rel_tol=0.0, abs_tol=1e-10)
            and math.isclose(interface_pressure * area, tension_n, rel_tol=0.0, abs_tol=1e-10)
            and interface_pressure >= 0.0,
            "uniform-load force or compression-only interface coupon differs")
    return {
        "status": "PASS_ANALYTIC_TWO_SEPARATE_PLATE_CONTACT_COUPON",
        "T_n": tension_n,
        "M_nmm": 0.0,
        "full_face_annulus_area_mm2": area,
        "uniform_wood_pressure_mpa": pressure,
        "uniform_head_pressure_mpa": pressure,
        "uniform_interplate_pressure_mpa": interface_pressure,
        "wood_spring_closure_mm": wood_deflection,
        "head_spring_closure_mm": head_closure,
        "interplate_normal_gap_mm": 0.0,
        "interplate_pressure_gap_product_mpa_mm": 0.0,
        "all_three_normal_pressures_nonnegative": True,
        "wood_force_residual_n": pressure * area - tension_n,
        "head_force_residual_n": pressure * area - tension_n,
        "interplate_force_residual_n": interface_pressure * area - tension_n,
        "each_plate_bending_and_shear_energy_nmm": 0.0,
        "each_plate_face_stress_proxy_mpa": 0.0,
        "plate_count": 2,
        "individual_plate_thicknesses_mm": [thickness, thickness],
        "assembled_transverse_plate_stiffness_multiplier": 2,
        "bonded_2t_plate_stiffness_multiplier_used": False,
        "contact_model": "compression-only wood and head springs plus hard compression-only interplate normal contact; zero friction and no adhesion",
        "coupon_limit": "Uniform full-face supports exercise signs and contact equilibrium; production pressing footprints and nonuniform moment response require the pinned fine Mindlin calculation.",
    }


def coupon_suite(inputs: dict[str, Any]) -> dict[str, Any]:
    hypotheses = inputs["hypotheses"]
    profiles = {case["profile_id"]: case["profile"] for case in inputs["cases"]}
    coupons = {profile_id: known_answer_coupon(profile, hypotheses)
               for profile_id, profile in sorted(profiles.items())}
    require(all(row["status"] == "PASS_ANALYTIC_TWO_SEPARATE_PLATE_CONTACT_COUPON"
                for row in coupons.values()), "one or more analytic stack coupons failed")
    return {"schema": "current_two_washer_coupon_suite/v1", "coupons": coupons,
            "profile_count": len(coupons), "solver_or_native_build_invoked": False}


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import pinned helper: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def load_engine() -> dict[str, Any]:
    """Load only the pinned Python plate helpers; no model is assembled here."""
    _check_pins()
    edge = _load_module(EDGE, "washer_stack_pinned_edge")
    stacked = _load_module(STACKED, "washer_stack_pinned_stacked")
    flexure = _load_module(FLEXURE, "washer_stack_pinned_flexure")
    edge.require(edge.sha(EDGE) == PINS[EDGE], "Mindlin edge helper differs")
    require(stacked.EDGE_SHA256 == PINS[EDGE] and sha(EDGE) == PINS[EDGE],
            "older stacked-washer adapter no longer points to the pinned Mindlin helper")
    require((flexure.ESTEEL, flexure.NU, flexure.FY_HYPOTHESIS, flexure.KWOOD, flexure.KHEAD)
            == (200000.0, 0.3, 250.0, 20.0, 10000.0),
            "pinned current plate material/contact hypotheses differ")
    require(edge.np.__version__ == "2.5.2" and edge.scipy.__version__ == "1.18.1",
            "recorded NumPy/SciPy versions differ")
    return {"edge": edge, "stacked": stacked, "flexure": flexure,
            "versions": {"numpy": edge.np.__version__, "scipy": edge.scipy.__version__}}


def _profile_family(profile: dict[str, Any]) -> dict[str, float]:
    result = {key: float(profile[key]) for key in
              ("inner_radius_mm", "outer_radius_mm", "head_radius_mm", "thickness_mm")}
    require(0.0 < result["inner_radius_mm"] < result["head_radius_mm"] < result["outer_radius_mm"]
            and result["thickness_mm"] > 0.0,
            "washer profile radii or thickness are invalid")
    return result


def _separate_plate_coupon(engine: dict[str, Any], model: dict[str, Any],
                           single_stiffness: Any, coupon_debug: dict[str, Any]) -> dict[str, Any]:
    edge = engine["edge"]
    pose = edge.np.asarray(coupon_debug["scaled_variables_mm"])
    state = {"scaled_variables_mm": pose, "T_n": 100.0, "M_magnitude_nmm": 0.0}
    area, mapping = model["area"], model["wood_map"]
    full_contacts = edge.contacts(model, full_head=True)
    drive = edge.drive_vector(model, state["T_n"], state["M_magnitude_nmm"])
    _energy, _gradient, _tangent, pressures, _contact_energies = edge.evaluate(
        model, pose, drive, full_contacts)
    wood = pressures[0]
    head = pressures[1]
    interface = (wood + head) / 2.0
    top_residual = single_stiffness @ pose + mapping.T @ (area * (interface - head))
    bottom_residual = single_stiffness @ pose + mapping.T @ (area * (wood - interface))
    force = float(area @ interface)
    profile = model["family"]
    exact_area = math.pi * (profile["outer_radius_mm"]**2 - profile["inner_radius_mm"]**2)
    require(float(interface.min()) >= 0.0
            and math.isclose(float(area.sum()), exact_area, rel_tol=0.0, abs_tol=1e-9)
            and abs(force - 100.0) <= edge.FORCE_TOLERANCE
            and max(float(abs(top_residual[:-3]).max()), float(abs(bottom_residual[:-3]).max()))
            <= edge.GRADIENT_TOLERANCE,
            "two separate plate full-face compression/contact coupon failed")
    return {"status": "PASS_DISCRETE_TWO_SEPARATE_PLATE_CONTACT_COUPON",
            "full_face_coupon_only": True,
            "normal_gap_mm": 0.0,
            "interplate_pressure_minimum_mpa": float(interface.min()),
            "interplate_pressure_maximum_mpa": float(interface.max()),
            "interplate_force_n": force,
            "interplate_first_moments_nmm": [float((area * model[key]) @ interface) for key in ("x", "y")],
            "top_plate_scaled_gradient_maximum_n": float(abs(top_residual[:-3]).max()),
            "bottom_plate_scaled_gradient_maximum_n": float(abs(bottom_residual[:-3]).max()),
            "individual_plate_thicknesses_mm": [profile["thickness_mm"], profile["thickness_mm"]],
            "bonded_2t_plate_stiffness_multiplier_used": False}


def make_stack_model(engine: dict[str, Any], profile: dict[str, Any],
                     resolution: str = "fine") -> dict[str, Any]:
    """Build one profile's two-plate reduced model and both coupon checks.

    Call serially from the parent run. The two single-plate Mindlin operators
    are summed; original thickness remains in stress recovery and in each
    separate plate equilibrium equation.
    """
    edge, flexure = engine["edge"], engine["flexure"]
    family = _profile_family(profile)
    assumptions = EXPECTED_HYPOTHESES
    require((flexure.ESTEEL, flexure.NU, flexure.FY_HYPOTHESIS, flexure.KWOOD, flexure.KHEAD)
            == (assumptions["E_mpa"], assumptions["nu"], assumptions["Fy_mpa"],
                assumptions["Kwood_mpa_per_mm"], assumptions["Khead_mpa_per_mm"]),
            "working contract and Mindlin helpers have different plate hypotheses")
    prior_families = flexure.FAMILIES
    try:
        flexure.FAMILIES = {**prior_families, "rail": family}
        model = edge.make_model(flexure, resolution)
    finally:
        flexure.FAMILIES = prior_families

    single_stiffness = model["stiffness"].copy()
    for key in ("bending_stiffness", "shear_stiffness", "stiffness"):
        model[key] = 2.0 * model[key]
    debug: dict[str, Any] = {}
    rigid = edge.rigid_modes(model, debug)
    coupon = edge.coupon(model, rigid, debug)
    separate_coupon = _separate_plate_coupon(engine, model, single_stiffness, debug)
    return {"model": model, "single_plate_stiffness": single_stiffness,
            "profile": family, "resolution": resolution,
            "rigid_modes": rigid, "assembled_plate_coupon": coupon,
            "separate_plate_contact_coupon": separate_coupon}


def _centered_seed(source: dict[str, Any]) -> dict[str, Any]:
    """Match the current single-plate runner's non-evidentiary centered seed."""
    family = source["geometry"]["profile_binding"]["plate_profile"]
    tension = float(source["T_n"])
    wood_area = float(source["geometry"]["supported_area_mm2"])
    head_area = math.pi * (float(family["head_radius_mm"])**2 - float(family["inner_radius_mm"])**2)
    require(tension >= 0.0 and wood_area > 0.0 and head_area > 0.0,
            "current centered seed has a nonpositive support area")
    wood = {"closure_mm": tension/(20.0*wood_area), "tilt_rad": 0.0,
            "active_area_mm2": wood_area, "pressure_peak_mpa": tension/wood_area}
    head = {"closure_mm": tension/(10000.0*head_area), "tilt_rad": 0.0,
            "active_area_mm2": head_area, "pressure_peak_mpa": tension/head_area}
    return {"wood_contact": wood, "head_contact": head,
            "total_closure_mm": wood["closure_mm"] + head["closure_mm"],
            "relative_tilt_rad": 0.0, "centered_starting_pose_only": True,
            "source_rigid_pressure_not_transferred": True}


def solve_case(engine: dict[str, Any], stack_model: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Solve one saved same-state own-end T/M with the explicit stack witness.

    The caller owns execution order, run output paths, receipts and any retry
    decision. A failure remains a numerical stop; it does not prove physical
    incompatibility.
    """
    edge = engine["edge"]
    require(case["profile"] == stack_model["profile"], "case/profile model mismatch")
    source = deepcopy(case["solver_source"])
    require(math.isfinite(source["T_n"]) and source["T_n"] > 0
            and math.isfinite(source["M_magnitude_nmm"]) and source["M_magnitude_nmm"] >= 0,
            "case demand is invalid")
    source["saved_rigid_contact"] = _centered_seed(source)
    source["centered_seed_is_initialization_only"] = True
    source["source_rigid_contact_transferred"] = False
    edge.STATE_ID = "/".join((case["state_tag"], case["axis_id"], case["end_role"]))
    debug: dict[str, Any] = {}
    state, fields = edge.solve_state(stack_model["model"], source, debug)
    interface, interface_pressure, wood_pressure, head_pressure = engine["stacked"].interface_witness(
        edge, stack_model["model"], stack_model["single_plate_stiffness"], state)
    for row in fields:
        row["current_case_id"] = case["case_id"]
        row["current_state_tag"] = case["state_tag"]
        row["current_axis_id"] = case["axis_id"]
        row["current_end_role"] = case["end_role"]
        row["interface_pressure_mpa"] = (row["head_pressure_mpa"] + row["wood_pressure_mpa"]) / 2.0

    doubled_stress = float(state["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"])
    baseline = float(case["single_washer_reference"]["sampled_stress_proxy_mpa"])
    fy = EXPECTED_HYPOTHESES["Fy_mpa"]
    result = {
        "schema": "current_two_washer_stack_case/v1",
        "status": "FINITE_TWO_SEPARATE_WASHER_CONTACT_HYPOTHESIS",
        "case": {key: case[key] for key in ("case_id", "state_tag", "gap_scale", "axis_id", "end_role",
                                              "receiver_member", "join_key", "source_input", "source_disposition_pointer")},
        "profile": {"profile_id": case["profile_id"], "part": case["solver_source"]["geometry"]["profile_binding"]["part"],
                    **stack_model["profile"]},
        "demand": {"T_n": source["T_n"], "own_end_M_magnitude_nmm": source["M_magnitude_nmm"],
                   "own_end_M_signed_xyz_nmm": case["source_signed_own_M_xyz_nmm"],
                   "plate_pressure_first_moment_targets_nmm": case["plate_pressure_first_moment_targets_nmm"],
                   "source_force_compatibility": False},
        "individual_plate_count": 2,
        "individual_plate_thickness_mm": stack_model["profile"]["thickness_mm"],
        "assembled_bending_and_shear_stiffness_multiplier": 2,
        "individual_stress_constitutive_thickness_preserved": True,
        "interface_witness": interface,
        "sampled_field_counts": {"total": len(fields),
                                  "quadrature": sum(row["sample_set"] == "quadrature" for row in fields),
                                  "edge_band_and_interiors": sum(row["sample_set"] == "edges_band_and_interiors" for row in fields)},
        "stress_comparison": {
            "current_single_washer_same_state_mpa": baseline,
            "two_washers_peak_individual_proxy_mpa": doubled_stress,
            "reduction_fraction_vs_current_same_state": 1.0 - doubled_stress / baseline,
            "hypothetical_Fy250_mpa": fy,
            "over_hypothetical_Fy250": doubled_stress / fy,
            "Fy250_is_published_product_property": False,
            "actual_washer_yield_mpa": None,
            "actual_washer_capacity_n": None,
        },
        "fit_grip_applicability": deepcopy(case["fit_grip_applicability"]),
        "source_pins": {str(path.relative_to(ROOT)): digest for path, digest in PINS.items()},
        "limits": [
            "The same-state own-end T/M is the current isolated scalar recovery; global shaft curvature compatibility is not established.",
            "The common-field reduction is admissible only while both individual plate residuals pass and the recovered interplate pressure is nonnegative.",
            "Each washer retains its own catalog-model thickness; tangential sliding is free and no 2t bonded plate is used.",
            "Kwood, Khead, E, nu and Fy250 are hypotheses; actual washer metallurgy and strength are unestablished.",
            "Nominal concentric support does not qualify loaded shift/tilt, actual bearing faces, preload, friction or complete joint resistance.",
            "The extra washer increases the relevant exterior stack by its profile thickness; bolt length and thread engagement were not rechecked here.",
            "No CAD axes, frame forces, hardware order, candidate authority or physical release are changed by this local calculation.",
        ],
        "actual_washer_yield_mpa": None,
        "actual_washer_capacity_n": None,
        "complete_joint_acceptance": False,
        "physical_release": False,
        "native_CAD_or_frame_solve_run": False,
    }
    return {"result": result, "state": state, "fields": fields,
            "interface_pressure_mpa": interface_pressure,
            "wood_pressure_mpa": wood_pressure, "head_pressure_mpa": head_pressure,
            "last_debug_state": debug}
