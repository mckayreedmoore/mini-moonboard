"""Review current 96-bolt placement checks from one explicit v8 readiness receipt.

This read-only reducer consumes already admitted fields and their independent
replays. It does not prepare inputs, recompute the response, rebuild CAD, or
transfer a result from an earlier frame revision.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts import eoere_bolt_geometry_rules as rules
from scripts import eoere_bolt_outer_geometry as outer
from scripts import eoere_bolt_pair_census as census
from scripts import eoere_v6_bolt_geometry_review as occurrence_source
from scripts import eoere_v6_bolt_geometry_review_v2 as pair_upgrade
from scripts import eoere_v8_analysis as analysis
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
SOURCE_EVIDENCE = occurrence_source.SOURCE
OUT = analysis.BASE / "bolt-geometry-review-v1"
READINESS = analysis.BASE / "adapter-readiness.json"
PUBLIC_ROOT = ROOT / "docs/bolted-frame-development"
LOAD_CONTRACT = {
    "input_weight": 250,
    "input_unit": "lb",
    "downward_multiplier": 2.0,
    "horizontal_force_n": 300.0,
    "duration_factor_CD": 1.0,
    "accessory_mass_kg": 25.0,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _pin_path(path: str | Path, pins: dict[str, str], expected: str | None = None) -> dict[str, Any]:
    binding = ref(path)
    if expected is not None:
        require(binding["sha256"] == expected, f"source hash changed: {binding['path']}")
    prior = pins.get(binding["path"])
    require(prior is None or prior == binding["sha256"], f"conflicting source pin: {binding['path']}")
    pins[binding["path"]] = binding["sha256"]
    return binding


def _read_ref(binding: dict[str, Any], pins: dict[str, str], label: str) -> Any:
    require(
        isinstance(binding, dict)
        and isinstance(binding.get("path"), str)
        and isinstance(binding.get("sha256"), str),
        f"{label} requires a path and SHA-256 binding",
    )
    return read(binding["path"], pins, binding["sha256"])


def _verify_pin_map(values: Any, pins: dict[str, str], label: str) -> None:
    require(isinstance(values, dict), f"{label} source_sha256 map required")
    for path, digest in values.items():
        require(isinstance(path, str) and isinstance(digest, str), f"malformed {label} source pin")
        _pin_path(path, pins, digest)


def _checked_readiness(
    readiness_path: Path,
    readiness_sha256: str,
    initial_pins: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    expected_path = READINESS.resolve()
    supplied_path = readiness_path.resolve()
    require(supplied_path == expected_path, "the v8 adapter-readiness.json is the required intake")
    require(
        len(readiness_sha256) == 64
        and all(character in "0123456789abcdef" for character in readiness_sha256),
        "explicit lowercase SHA-256 readiness binding required",
    )

    pins: dict[str, str] = {} if initial_pins is None else dict(initial_pins)
    _pin_path(OWN, pins)
    _pin_path(analysis.OWN, pins)
    readiness = read(supplied_path, pins, readiness_sha256)
    require(
        readiness.get("schema") == "eoere_v8_existing_response_method_readiness/v1"
        and readiness.get("analysis_revision") == analysis.REVISION,
        "current v8 adapter readiness required",
    )
    require(readiness.get("producer") == ref(analysis.OWN), "current v8 readiness producer changed")
    require(
        readiness.get("load_contract")
        == {
            "weight_lb": 250,
            "downward_multiplier": 2,
            "horizontal_force_N": 300,
            "accessory_mass_kg": 25,
            "duration_factor_CD": 1,
        },
        "current 250 lb, 2.0 downward, 300 N, CD=1 load contract required",
    )
    for flag in (
        "new_force_response_computed",
        "historical_force_pass_transferred",
        "complete_joint_or_frame_qualified",
    ):
        require(readiness.get(flag) is False, f"v8 readiness must keep {flag} false")

    context = analysis.context(
        readiness["receipt"]["sha256"],
        readiness["physical_geometry"]["sha256"],
        Path(readiness["receipt"]["path"]),
    )
    for key in ("receipt", "physical_geometry", "physical_clearance", "parent_v7_geometry"):
        require(readiness.get(key) == context[key], f"v8 readiness {key} binding changed")
    _verify_pin_map(context["source_sha256"], pins, "v8 context")
    _verify_pin_map(readiness.get("source_sha256"), pins, "adapter readiness")

    refs = {
        "analysis_geometry": analysis.BASE / "geometry/geometry.json",
        "material": analysis.BASE / "material.json",
        "inputs": analysis.BASE / "four-hosts/preparation/inputs.json",
        "method_readiness": analysis.BASE / "readiness.json",
    }
    loaded: dict[str, Any] = {}
    for name, expected in refs.items():
        binding = readiness.get(name)
        require(binding == ref(expected), f"readiness {name} must bind the current v8 packet")
        loaded[name] = _read_ref(binding, pins, name)

    method_ready = loaded["method_readiness"]
    require(
        method_ready.get("analysis_geometry") == readiness["analysis_geometry"]
        and method_ready.get("material") == readiness["material"]
        and method_ready.get("inputs") == readiness["inputs"]
        and method_ready.get("bodies") == 148
        and method_ready.get("shafts") == 96
        and method_ready.get("wood_walls") == 112
        and method_ready.get("fitting_ports") == 96
        and method_ready.get("screws") == 66
        and method_ready.get("cases") == 6
        and method_ready.get("new_force_response_computed") is False
        and method_ready.get("complete_joint_or_frame_qualified") is False,
        "v8 method readiness inventory or conditional boundary changed",
    )
    physical = _read_ref(readiness["physical_geometry"], pins, "physical geometry")
    geometry = loaded["analysis_geometry"]
    require(
        physical.get("revision") == analysis.PHYSICAL_REVISION
        and len(physical.get("axes", [])) == 96
        and len(physical.get("fitting_poses", [])) == 24
        and len(physical.get("profiles", {})) == 30
        and len(physical.get("screw_axes", [])) == 66,
        "current v8 physical 96-axis geometry required",
    )
    require(
        geometry.get("revision") == analysis.REVISION
        and geometry.get("parent_owner_geometry") == readiness["physical_geometry"]
        and geometry.get("perfect_bond_analysis") is True
        and geometry.get("physical_plywood_leaves") == 4
        and geometry.get("analytical_laminated_bodies") == 2
        and geometry.get("actual_bond_qualified") is False
        and len(geometry.get("axes", [])) == 96
        and len(geometry.get("screw_axes", [])) == 66,
        "current v8 bonded analysis geometry required",
    )
    material = loaded["material"]
    require(
        material.get("current_envelope_width_mm") == 139.7
        and material.get("physical_qualification") is False,
        "current 139.7 mm perfect-bond plywood material scenario required",
    )
    inputs = loaded["inputs"]
    require(
        inputs.get("geometry") == readiness["analysis_geometry"]
        and inputs.get("plywood_material") == readiness["material"]
        and inputs.get("scenario", {}).get("perfect_bond_analysis", {}).get("analysis_geometry")
        == readiness["analysis_geometry"]
        and inputs.get("scenario", {}).get("perfect_bond_analysis", {}).get("physical_parent")
        == readiness["physical_geometry"]
        and len(inputs.get("timber_rows", [])) == 22
        and len(inputs.get("shafts", [])) == 96
        and len(inputs.get("finished_receiver_wall_queries", [])) == 112
        and len(inputs.get("fitting_port_bindings", [])) == 96
        and len(inputs.get("hillman_rows", [])) == 66
        and len(inputs.get("cases", [])) == len(CASES)
        and {case.get("case_id") for case in inputs.get("cases", [])} == set(CASES),
        "v8 inputs must bind 22 members, 96 shafts, 112 wood walls, 96 ports, 66 screws and six cases",
    )
    expected_material_source = loaded["material"].get("source_sha256")
    require(isinstance(expected_material_source, dict), "current material source pins required")
    for key in (ref(analysis.OWN)["path"], ref(analysis.WORK / "owner_laminated_floor.py")["path"]):
        require(key in expected_material_source, f"current material source pin missing: {key}")
    return readiness, {**loaded, "physical_geometry": physical}, pins


def _admitted_fields(
    readiness: dict[str, Any], pins: dict[str, str]
) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]]]:
    geometry_ref = readiness["analysis_geometry"]
    rows = []
    geometry_fingerprint: dict[str, Any] | None = None
    for case_id in CASES:
        folder = analysis.BASE / "four-hosts" / case_id
        field_ref = _pin_path(folder / "field.json", pins)
        replay_ref = _pin_path(folder / "independent-replay.json", pins)
        plywood_ref = _pin_path(folder / "independent-replay-plywood.json", pins)
        field = _read_ref(field_ref, pins, f"{case_id} field")
        replay = _read_ref(replay_ref, pins, f"{case_id} independent replay")
        plywood = _read_ref(plywood_ref, pins, f"{case_id} plywood replay")
        require(field.get("case_id") == replay.get("case_id") == case_id, f"{case_id} replay labels disagree")
        require(replay.get("field") == plywood.get("field") == field_ref, f"{case_id} replay does not bind its own field")
        replay_producer = replay.get("producer")
        plywood_source = plywood.get("source")
        plywood_material = plywood.get("material")
        captured_launcher = plywood.get("captured_launcher")
        require(
            isinstance(replay_producer, dict)
            and isinstance(plywood_source, dict)
            and isinstance(plywood_material, dict)
            and isinstance(captured_launcher, dict),
            f"{case_id} replay source bindings required",
        )
        _pin_path(replay_producer["path"], pins, replay_producer["sha256"])
        _pin_path(plywood_source["path"], pins, plywood_source["sha256"])
        _pin_path(captured_launcher["path"], pins, captured_launcher["sha256"])
        require(plywood_material == readiness["material"], f"{case_id} plywood replay material changed")
        require(
            field.get("trial_parent_geometry") == geometry_ref
            and field.get("source_inputs", {}).get("geometry") == geometry_ref
            and field.get("source_inputs", {}).get("plywood_material") == readiness["material"]
            and field.get("counts", {}).get("physical_bodies") == 148
            and field.get("counts", {}).get("shaft") == 96
            and field.get("counts", {}).get("fitting") == 24
            and len(field.get("source_inputs", {}).get("shafts", [])) == 96
            and len(field["source_inputs"].get("timber_rows", [])) == 22
            and len(field.get("common_shaft_wood_bearing_actions", [])) == 112
            and len(field.get("source_inputs", {}).get("fitting_port_bindings", [])) == 96
            and len(field.get("panel_screw_actions", [])) == 66,
            f"{case_id} field inventory or geometry binding changed",
        )
        require(
            replay.get("false_screw_and_floor_forces_rejected") is True
            and replay.get("same_state_declared_fixed_floor_replayed") is True
            and replay.get("all_credited_hosts_in_bearing") is True
            and replay.get("equilibrium", {}).get("physical_body_count") == 148
            and replay.get("equilibrium", {}).get("gradient_inf_n", float("inf")) < 1e-5
            and len(plywood.get("raw_operator_checks", [])) == 2,
            f"{case_id} independent admission/replay did not satisfy the frozen gates",
        )
        release = field.get("release")
        release_keys = {
            "candidate_accepted",
            "capacity_established",
            "climbing_released",
            "complete_joint_acceptance",
            "fabrication_released",
            "structural_released",
        }
        require(
            isinstance(release, dict)
            and release_keys <= set(release)
            and all(value is False for value in release.values()),
            f"{case_id} candidate release flags must remain false",
        )
        parameters = field["source_inputs"]["scenario"]["climber_load_parameters"]
        perfect_bond = field["source_inputs"]["scenario"].get("perfect_bond_analysis", {})
        require(
            parameters.get("input_weight") == 250
            and parameters.get("input_unit") == "lb"
            and parameters.get("downward_multiplier") == 2.0
            and parameters.get("horizontal_force_n") == 300.0
            and perfect_bond.get("analysis_geometry") == geometry_ref
            and perfect_bond.get("physical_parent") == readiness["physical_geometry"]
            and perfect_bond.get("actual_bond_qualified") is False,
            f"{case_id} field load contract changed",
        )
        shafts = field["source_inputs"]["shafts"]
        shaft_by_id = {shaft["axis_id"]: shaft for shaft in shafts}
        require(len(shaft_by_id) == 96, f"{case_id} shaft IDs must be unique")
        actions = field["common_shaft_wood_bearing_actions"]
        action_by_key = {(action["axis_id"], action["host"]): action for action in actions}
        require(len(action_by_key) == 112, f"{case_id} wood-wall actions must be unique")
        for shaft in shafts:
            for surface in shaft["surfaces"]:
                if surface.get("kind") == "wood":
                    require(
                        (shaft["axis_id"], surface["host"]) in action_by_key,
                        f"{case_id} missing host wrench for {shaft['axis_id']}/{surface['host']}",
                    )
        current_fingerprint = {
            "shafts": field["source_inputs"]["shafts"],
            "timber_rows": field["source_inputs"]["timber_rows"],
        }
        if geometry_fingerprint is None:
            geometry_fingerprint = current_fingerprint
        else:
            require(current_fingerprint == geometry_fingerprint, "six v8 fields do not share one geometry/material intake")
        rows.append((case_id, field_ref, field, replay, plywood))
    return geometry_fingerprint or {}, rows


def _profiles_and_faces(
    geometry: dict[str, Any], first_field: dict[str, Any], pins: dict[str, str]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    profiles = {}
    faces = {}
    members = first_field["source_inputs"]["timber_rows"]
    for member in members:
        name = member["name"]
        require(name not in profiles and name in geometry.get("profiles", {}), f"missing unique v8 profile for {name}")
        profile = outer.outer_profile(member["raw_profile_source"])
        body_ref = geometry["profiles"][name]["finished"]
        _pin_path(body_ref["path"], pins, body_ref["sha256"])
        shape = occurrence_source.cq.Shape.importBrep(str(ROOT / body_ref["path"]))
        profiles[name] = profile
        faces[name] = outer.confirm_faces(shape, profile)
    require(len(profiles) == 22, "all 22 current timber/laminated-host profiles required")
    return profiles, faces


def _case_components(
    case_id: str,
    field_ref: dict[str, Any],
    field: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    faces: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    shafts = {shaft["axis_id"]: shaft for shaft in field["source_inputs"]["shafts"]}
    actions = {
        (action["axis_id"], action["host"]): action
        for action in field["common_shaft_wood_bearing_actions"]
    }
    rows = []
    receiver_groups: dict[tuple[tuple[str, str], ...], list[str]] = {}
    for axis_id, shaft in shafts.items():
        key = tuple(sorted((surface["kind"], surface["host"]) for surface in shaft["surfaces"]))
        receiver_groups.setdefault(key, []).append(axis_id)
        for surface in shaft["surfaces"]:
            if surface["kind"] != "wood":
                continue
            host = surface["host"]
            require(host in profiles, f"{case_id} has no outer-profile source for wood host {host}")
            action = actions.get((axis_id, host))
            require(action is not None, f"{case_id} has no own host action for {axis_id}/{host}")
            rows.append(occurrence_source.occurrence(profiles[host], shaft, surface, action, None))
    require(len(rows) == 112 and len({(row["axis_id"], row["host"]) for row in rows}) == 112,
            f"{case_id} must have 112 unique current wood occurrences")
    keyed = {(row["axis_id"], row["host"]): row for row in rows}

    original_pairs = []
    for receivers, identities in sorted(receiver_groups.items()):
        require(len(identities) in (1, 2), f"{case_id} has an unclassified receiver group larger than two axes")
        if len(identities) == 1:
            continue
        first_id, second_id = sorted(identities)
        first_shaft, second_shaft = shafts[first_id], shafts[second_id]
        for kind, host in receivers:
            if kind != "wood":
                continue
            frame = occurrence_source.np.asarray(profiles[host]["basis_grain_u_v_xyz"])
            own_rows = [keyed[(axis_id, host)] for axis_id in (first_id, second_id)]
            edge_dimension = own_rows[0]["placement"]["edge_transverse_dimension"]
            delta = frame @ (
                occurrence_source.np.asarray(second_shaft["point"])
                - occurrence_source.np.asarray(first_shaft["point"])
            )
            gv = [float(delta[0]), float(delta[edge_dimension])]
            load = occurrence_source.group_load(own_rows)
            row_classification = None
            if (
                load["direction"] == "parallel" and abs(gv[1]) < 1e-6
            ) or (
                load["direction"] == "perpendicular" and abs(gv[0]) < 1e-6
            ):
                row_classification = "same_row"
            wood_lengths = [
                surface["interval_mm"][1] - surface["interval_mm"][0]
                for surface in first_shaft["surfaces"]
                if surface["kind"] == "wood"
            ]
            rule = rules.pair_rule(
                gv,
                max(first_shaft["diameter_mm"], second_shaft["diameter_mm"]),
                min(wood_lengths),
                load,
                row_classification=row_classification,
            )
            original_pairs.append(
                {
                    "host": host,
                    "axes": [first_id, second_id],
                    "rule": rule,
                    "load_classification": load,
                    "row_classification": row_classification,
                    "complete_Cdelta": None,
                    "complete_joint_qualified": False,
                }
            )

    axis_rows = []
    for axis_id in sorted(shafts):
        own_rows = [row for row in rows if row["axis_id"] == axis_id]
        pair_rows = [pair for pair in original_pairs if axis_id in pair["axes"]]
        statuses = [row["edge_rule"]["status"] for row in own_rows]
        statuses.extend(end["rule"]["status"] for row in own_rows for end in row["end_rules"])
        statuses.extend(pair["rule"]["status"] for pair in pair_rows)
        if any(not faces[row["host"]]["all_profile_planes_present_on_cached_finished_faces"] for row in own_rows):
            statuses.append("unresolved")
        axis_rows.append(
            {
                "axis_id": axis_id,
                "component_status": rules.rollup_status(statuses),
                "complete_Cdelta": None,
                "complete_joint_qualified": False,
            }
        )
    return {
        "case_id": case_id,
        "field": field_ref,
        "wood_occurrences": rows,
        "receiver_pairs": original_pairs,
        "axes": axis_rows,
        "axis_status_counts": dict(Counter(row["component_status"] for row in axis_rows)),
        "load_class_counts": dict(Counter(row["load_classification"]["direction"] for row in rows)),
    }


def upgrade_case(case: dict[str, Any], shafts: dict[str, Any]) -> dict[str, Any]:
    """Add all-host pair census using the audited v2 wrapper, then harden flags."""
    result = pair_upgrade.upgrade_case(case, shafts)
    for pair in result["receiver_pairs"]:
        pair["complete_joint_qualified"] = False
    for pair in result["same_host_pairs"]:
        require(pair["complete_Cdelta"] is None and pair["complete_joint_qualified"] is False,
                "same-host census cannot qualify a complete joint")
    for axis in result["axes"]:
        axis["complete_Cdelta"] = None
        axis["complete_joint_qualified"] = False
    return result


def _component_exceedances(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for case in cases:
        for row in case["wood_occurrences"]:
            failed_ends = [end for end in row["end_rules"] if end["rule"]["status"] == "fail"]
            if row["edge_rule"]["status"] == "fail" or failed_ends:
                result.append(
                    {
                        "case_id": case["case_id"],
                        "axis_id": row["axis_id"],
                        "host": row["host"],
                        "edge_rule": row["edge_rule"] if row["edge_rule"]["status"] == "fail" else None,
                        "failed_end_rules": failed_ends,
                    }
                )
    return result


def _added_pair_geometry(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    added_by_case = [
        {
            (pair["host"], tuple(pair["axes"])): pair
            for pair in case["same_host_pairs"]
            if not pair["existing_connection_group_pair"]
        }
        for case in cases
    ]
    if not added_by_case:
        return []
    shared_keys = set(added_by_case[0])
    shared_geometry = True
    for current in added_by_case[1:]:
        if set(current) != shared_keys:
            shared_geometry = False
            break
        for key in shared_keys:
            first, other = added_by_case[0][key], current[key]
            if (
                first["parallel_bore_axes"] != other["parallel_bore_axes"]
                or first["actual_spacing_mm"] != other["actual_spacing_mm"]
            ):
                shared_geometry = False
                break
    if not shared_geometry:
        return [
            {"case_id": case["case_id"], **copy.deepcopy(pair)}
            for case in cases
            for pair in case["same_host_pairs"]
            if not pair["existing_connection_group_pair"]
        ]
    result = []
    case_ids = [case["case_id"] for case in cases]
    for key in sorted(shared_keys):
        pair = added_by_case[0][key]
        result.append(
            {
                "host": pair["host"],
                "axes": list(pair["axes"]),
                "case_ids": case_ids,
                "parallel_bore_axes": pair["parallel_bore_axes"],
                "actual_spacing_mm": pair["actual_spacing_mm"],
                "status": pair["status"],
                "rule_status": pair["rule_status"],
                "complete_Cdelta": None,
                "complete_joint_qualified": False,
                "reason": pair["reasons"],
            }
        )
    return result


def public_summary(result: dict[str, Any], full_path: Path) -> dict[str, Any]:
    summary = {
        key: copy.deepcopy(value)
        for key, value in result.items()
        if key not in {"source_sha256", "profile_face_confirmations", "cases"}
    }
    summary["full_review"] = ref(full_path)
    summary["producer"] = ref(OWN)
    summary["occurrence_producer"] = ref(occurrence_source.OWN)
    summary["rules_producer"] = ref(Path(rules.__file__))
    summary["outer_geometry_producer"] = ref(Path(outer.__file__))
    summary["pair_census_producer"] = ref(Path(census.__file__))
    summary["pair_upgrade_producer"] = ref(Path(pair_upgrade.__file__))
    summary["case_summaries"] = [
        {
            key: case[key]
            for key in (
                "case_id",
                "field",
                "axis_status_counts",
                "load_class_counts",
                "pair_census_counts",
            )
        }
        for case in result["cases"]
    ]
    summary["additional_same_host_pairs"] = _added_pair_geometry(result["cases"])
    summary["component_exceedances"] = _component_exceedances(result["cases"])
    summary["component_pair_exceedances"] = [
        {"case_id": case["case_id"], **copy.deepcopy(pair)}
        for case in result["cases"]
        for pair in case["receiver_pairs"]
        if pair["rule"]["status"] == "fail"
    ]
    return summary


def review(
    readiness_path: Path,
    readiness_sha256: str,
    out: Path,
    public_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Consume one hash-bound v8 readiness record and six admitted fields."""
    out = out.resolve()
    require(not out.exists() and out.is_relative_to(ROOT / "fea/generated"),
            "raw v8 review requires a fresh ignored fea/generated directory")
    if public_path is not None:
        public_path = public_path.resolve()
        require(not public_path.exists() and public_path.is_relative_to(PUBLIC_ROOT),
                "optional public output must be a fresh path under bolted-frame-development")

    readiness, loaded, pins = _checked_readiness(readiness_path, readiness_sha256)
    geometry = loaded["analysis_geometry"]
    field_fingerprint, admitted = _admitted_fields(readiness, pins)
    profiles, faces = _profiles_and_faces(geometry, admitted[0][2], pins)

    cases = []
    for case_id, field_ref, field, _, _ in admitted:
        base_case = _case_components(case_id, field_ref, field, profiles, faces)
        shafts = {shaft["axis_id"]: shaft for shaft in field["source_inputs"]["shafts"]}
        cases.append(upgrade_case(base_case, shafts))
    require(len(cases) == 6, "all six v8 admitted fields are required")

    source_pins = dict(pins)
    # Pin the current local method and evidence sources used to produce each
    # wood occurrence; no previous frame metrics are imported into this report.
    for source_path in (
        OWN,
        analysis.OWN,
        Path(census.__file__),
        Path(pair_upgrade.__file__),
        Path(occurrence_source.__file__),
        Path(rules.__file__),
        Path(outer.__file__),
        occurrence_source.SOURCE,
        ROOT / "scripts/eoere_mixed_stack_yield.py",
        ROOT / "scripts/thin_bolted_timber_resistance.py",
    ):
        _pin_path(source_path, source_pins)
    source_evidence = read(SOURCE_EVIDENCE, source_pins)
    require(
        sha(source_evidence["source"]["path"]) == source_evidence["source"]["sha256"],
        "pinned NDS source bytes changed",
    )
    _pin_path(source_evidence["source"]["path"], source_pins, source_evidence["source"]["sha256"])
    for path, digest in source_pins.items():
        require(sha(path) == digest, "source changed during current review: " + path)

    result = {
        "schema": "eoere_current_bolt_geometry_review/v1",
        "geometry_revision": analysis.PHYSICAL_REVISION,
        "analysis_revision": analysis.REVISION,
        "status": "CURRENT_COMPONENT_REVIEW_COMPLETE_JOINT_UNRESOLVED",
        "all_six_fields_share_geometry_and_material_intake": field_fingerprint is not None,
        "physical_geometry_receipt": readiness["receipt"],
        "physical_geometry": readiness["receipt"],
        "physical_geometry_raw": readiness["physical_geometry"],
        "analysis_geometry": readiness["analysis_geometry"],
        "base_input_manifest": {
            "physical_geometry_receipt": readiness["receipt"],
            "load_contract": copy.deepcopy(LOAD_CONTRACT),
            "legacy_screen_adjusted_indices": {},
        },
        "load_contract": copy.deepcopy(LOAD_CONTRACT),
        "inventory": {
            "shafts": 96,
            "wood_occurrences_per_case": 112,
            "timber_rows": 22,
            "fitting_ports": 96,
            "analytical_plywood_bodies": 2,
            "physical_plywood_leaves": 4,
            "cases": 6,
            "panels": 6,
            "screws": 66,
        },
        "source_evidence": ref(SOURCE_EVIDENCE),
        "NDS_source": source_evidence["source"],
        "source_bindings": {
            "readiness": ref(readiness_path),
            "analysis_geometry": readiness["analysis_geometry"],
            "material": readiness["material"],
            "inputs": readiness["inputs"],
            "method_readiness": readiness["method_readiness"],
            "fields_and_replays": {
                case_id: {
                    "field": field_ref,
                    "independent_replay": ref(analysis.BASE / "four-hosts" / case_id / "independent-replay.json"),
                    "independent_replay_plywood": ref(analysis.BASE / "four-hosts" / case_id / "independent-replay-plywood.json"),
                }
                for case_id, field_ref, _, _, _ in admitted
            },
        },
        "source_sha256": source_pins,
        "profile_face_confirmations": faces,
        "cases": cases,
        "formal_geometry_Cdelta": None,
        "complete_joint_qualified": False,
        "complete_joint_acceptance": False,
        "candidate_accepted": False,
        "capacity_established": False,
        "structural_acceptance": False,
        "structural_released": False,
        "physical_demand_bounds_established": False,
        "fabrication_released": False,
        "climbing_released": False,
        "frame_CAD_or_mechanics_recomputed": False,
        "historical_pass_transferred": False,
        "new_force_response_computed_by_this_review": False,
        "analysis_scenarios": {
            "nominal_metal_role_gravity": readiness["metal_role_gravity"],
            "perfect_bond_analysis": True,
            "full_width_plywood_envelope_mm": 139.7,
            "declared_fixed_floor_hosts": [
                "lumber_leg_left",
                "lumber_leg_right",
                "base_post_center_left",
                "base_post_center_right",
            ],
            "floor_capacity_or_no_slip_physical_qualification": False,
        },
        "qualification_limits": [
            "The admitted six fields are evaluated with their own v8 forces and geometry; no earlier frame metric or response is carried into this report.",
            "Principal-direction end, edge and row results are component screens. Oblique, reversing, sloped-end and unclassified row cases do not receive invented factors or complete-joint credit.",
            "All unordered axes sharing each wood host are listed. A new same-host pair has unresolved connection-row applicability until an applicable method is established.",
            "The cached outer-profile plane check does not prove intervening-bore ligament, splitting resistance, curved-face containment or a complete joint.",
            "The current 139.7 mm plywood beam envelope and perfect bond are analysis assumptions; they do not establish physical bond, panel action or force bounds.",
            "The four-host fixed-floor scenario and nominal metal-role gravity approximation remain conditional modeling inputs; no physical support or delivered-hardware qualification follows.",
            "This review computes placement components from admitted fields only. Complete Cdelta, complete-joint strength, structural acceptance, fabrication release and climbing release remain unestablished.",
        ],
    }
    full_path = out / "full-review.json"
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    (out / "pair-census-snapshot.py").write_bytes(Path(census.__file__).read_bytes())
    (out / "occurrence-producer-snapshot.py").write_bytes(Path(occurrence_source.__file__).read_bytes())
    _write_new(full_path, result)
    summary = public_summary(result, full_path)
    if public_path is not None:
        _write_new(public_path, summary)
    return result, summary


def _write_new(path: Path, value: Any) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--readiness-sha256", required=True)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--public", type=Path, help="optional fresh public summary path; no index is changed")
    args = parser.parse_args()
    result, summary = review(args.readiness, args.readiness_sha256, args.out, args.public)
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "case_pair_counts": [case["pair_census_counts"] for case in result["cases"]],
                "full_review": summary["full_review"],
                "complete_Cdelta": None,
                "complete_joint_qualified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
