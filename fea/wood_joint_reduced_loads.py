"""Compile source-bound gravity carriers for the reduced six-case model.

This module supplies exact static gravity force/first-moment equivalents for
the frozen mass inventory and the existing nine accessory scenarios. It does
not set connection stiffness, member constraints, rotational inertia, or an
observed accessory installation. The carrier mapping is an explicit
kinematic assumption for the response model; it is not a mechanical acceptance
result.

Run ``python3 fea/wood_joint_reduced_loads.py --check`` for the focused input
and equilibrium check, or ``--json`` to emit the complete compiled mapping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_INPUTS_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "reduced-static-attempt01/model-inputs.json"
)
MASS_CENTROIDS_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-mass-centroids-attempt01/mass-centroids.json"
)
MASS_TOPOLOGY_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-mass-topology-map-attempt03/source-topology-map.json"
)
DEAD_LOAD_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-dead-load-scenarios-attempt01/dead-load-scenarios.json"
)

PINNED_SHA256 = {
    MODEL_INPUTS_PATH: "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    MASS_CENTROIDS_PATH: "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    MASS_TOPOLOGY_PATH: "308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4",
    DEAD_LOAD_PATH: "37df743291b49d0a2b68274cd18337051c75dc927d72e49a903162d10f982e83",
}

GRAVITY_M_S2 = 9.80665
TOL = 1.0e-7
SCHEMA = "wood_joint_reduced_gravity_loads/v1"


def _read_pinned(path: Path) -> tuple[dict[str, Any], str]:
    raw = (ROOT / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = PINNED_SHA256[path]
    if digest != expected:
        raise ValueError(f"Pinned source changed: {path}; expected {expected}, got {digest}")
    return json.loads(raw), digest


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def _sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def _scale(a: list[float], scale: float) -> list[float]:
    return [x * scale for x in a]


def _close(actual: list[float], expected: list[float], tol: float = TOL) -> None:
    if len(actual) != len(expected) or any(
        abs(a - b) > tol * max(1.0, abs(a), abs(b))
        for a, b in zip(actual, expected, strict=True)
    ):
        raise AssertionError(f"Wrench/vector mismatch: {actual} != {expected}")


def _gravity(mass_kg: float) -> list[float]:
    return [0.0, 0.0, -mass_kg * GRAVITY_M_S2]


def _point_moment(point_xyz_mm: list[float], force_xyz_n: list[float]) -> list[float]:
    return _cross(point_xyz_mm, force_xyz_n)


def _wrench_about_origin(entry: dict[str, Any]) -> tuple[list[float], list[float]]:
    force = entry["force_xyz_n"]
    moment = _add(_point_moment(entry["reference_point_xyz_mm"], force),
                  entry["couple_xyz_nmm_about_reference"])
    return force, moment


def _label_maps(accessory: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_source_name = {row["axis_id"]: row for row in accessory["hold_axes"]}
    by_label = {row["label"]: row for row in accessory["hold_axes"]}
    if len(by_label) != len(accessory["hold_axes"]):
        raise AssertionError("Hold-axis labels must uniquely identify the current face grid")
    return by_source_name, by_label


def _parse_wire_endpoints(body_id: str, labels: dict[str, dict[str, Any]]) -> tuple[str, str]:
    if not body_id.startswith("wire_"):
        raise ValueError(f"Not a wire body id: {body_id}")
    suffix = body_id.split("_", 1)[1]
    _, separator, endpoints = suffix.partition("_")
    if not separator:
        raise ValueError(f"Wire id lacks endpoints: {body_id}")
    # Axis labels are drawn from a known finite set; a longest-prefix match
    # resolves delimiters when both endpoint labels themselves contain digits.
    candidates = sorted(labels, key=len, reverse=True)
    for first in candidates:
        prefix = first + "_"
        if endpoints.startswith(prefix):
            second = endpoints[len(prefix):]
            if second in labels:
                return first, second
    raise ValueError(f"Wire endpoint labels are not in the current hold-axis map: {body_id}")


def _source_rows(model: dict[str, Any], centroids: dict[str, Any],
                 topology: dict[str, Any], connections: dict[str, dict[str, Any]],
                 hold_axes_by_source: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    centroid_rows = {row["name"]: row for row in centroids["rows"]}
    topology_rows = {row["inventory_name"]: row for row in topology["physical_mass_rows"]}
    member_ids = {row["member_id"] for row in model["members"]}
    if len(centroid_rows) != 778 or len(topology_rows) != 778:
        raise AssertionError("Expected the frozen 778-row mass inventory")

    model_input_rows: dict[str, dict[str, Any]] = {}
    for member_id, rows in model["assigned_gravity_by_member"].items():
        for row in rows:
            if row["source_name"] in model_input_rows:
                raise AssertionError(f"Duplicate reduced-model source row: {row['source_name']}")
            model_input_rows[row["source_name"]] = row
    for row in model["unassigned_hardware_gravity"]:
        if row["source_name"] in model_input_rows:
            raise AssertionError(f"Duplicate reduced-model source row: {row['source_name']}")
        model_input_rows[row["source_name"]] = row
    if set(model_input_rows) != set(centroid_rows):
        missing = sorted(set(centroid_rows) - set(model_input_rows))
        extra = sorted(set(model_input_rows) - set(centroid_rows))
        raise AssertionError(f"Reduced inputs do not cover the frozen inventory: missing={missing[:4]}, extra={extra[:4]}")

    output: list[dict[str, Any]] = []
    for source_name, source in centroid_rows.items():
        topology_row = topology_rows[source_name]
        model_row = model_input_rows[source_name]
        mass = source["mass_kg"]
        point = source["mass_center_global_xyz_mm"]
        force = _gravity(mass)
        entity = topology_row["source_mass_entity"]
        receivers = entity["current_graph_member_references"]
        if not receivers or len(receivers) != len(set(receivers)):
            raise AssertionError(f"Missing or duplicate physical receiver references: {source_name}")
        if any(receiver not in member_ids for receiver in receivers):
            raise AssertionError(f"Source references a member absent from the reduced model: {source_name}")

        _close([mass], [topology_row["mass_kg"]])
        _close(point, topology_row["mass_center_global_xyz_mm"])
        _close(force, topology_row["gravity_force_global_xyz_n"])
        _close(force, model_row["force_xyz_n"])
        _close(point, model_row["point_xyz_mm"])
        _close([mass], [model_row["mass_kg"]])
        _close(_point_moment(point, force), topology_row["gravity_moment_about_global_origin_nmm"])
        _close(_point_moment(point, force), source["gravity_moment_about_global_origin_nmm"])

        kind = entity["kind"]
        load_common: dict[str, Any] = {
            "source_name": source_name,
            "source_entity_id": entity["id"],
            "source_group": source["group"],
            "source_entity_kind": kind,
            "source_component_role": entity.get("component_role"),
            "source_axis_id": entity.get("axis_id"),
            "mass_kg": mass,
            "source_centroid_xyz_mm": point,
            "source_force_xyz_n": force,
            "source_moment_about_global_origin_xyz_nmm": _point_moment(point, force),
            "source_receiver_member_ids": receivers,
        }

        if kind == "current_physical_member_solid":
            if len(receivers) != 1 or receivers[0] != source_name:
                raise AssertionError(f"Physical member mass lacks its same-member receiver: {source_name}")
            receiver = receivers[0]
            carrier = {
                "carrier_id": f"member-gravity/{receiver}",
                "carrier_kind": "physical_member_body_or_beam_elements",
                "receiver_member_ids": [receiver],
                "receiver_axis_id": None,
                "reference_point_xyz_mm": point,
                "carrier_map_basis": "Direct current physical member solid, matched by its current graph member ID.",
                "kinematic_assumption": "Mass follows this physical member. Use body density or distributed beam gravity when internal self-weight bending is in scope; a centroid resultant alone omits that bending.",
                "mapping_uncertainty": "Source volume/density and member identity are frozen analytical inputs; member properties and delivered wood are not measured here.",
            }
        elif kind == "current_physical_tnut_component":
            if len(receivers) != 1:
                raise AssertionError(f"T-nut needs one panel receiver: {source_name}")
            axis = hold_axes_by_source.get(source_name)
            if axis is None or axis["panel_id"] != receivers[0]:
                raise AssertionError(f"T-nut does not match its current hold-axis/panel map: {source_name}")
            carrier = {
                "carrier_id": f"hold-axis/{source_name}",
                "carrier_kind": "hold_axis_reference",
                "receiver_member_ids": [receivers[0]],
                "receiver_axis_id": source_name,
                "reference_point_xyz_mm": axis["climbing_face_axis_point_global_xyz_mm"],
                "carrier_map_basis": "The protected current T-nut row maps by exact source name to its current face-axis point and same-panel graph receiver.",
                "kinematic_assumption": "T-nut mass follows the matching hold-axis point on its mapped panel; eccentric gravity couple preserves the source T-nut centroid.",
                "mapping_uncertainty": "CAD source centroid and panel identity are mapped; T-nut/panel attachment mechanics are not defined by this load map.",
            }
        else:
            axis_id = entity.get("axis_id")
            if not axis_id or axis_id not in connections:
                raise AssertionError(f"Hardware component has no matching current axis: {source_name}")
            connection = connections[axis_id]
            if set(receivers) != set(connection["receiver_member_ids"]):
                raise AssertionError(f"Source/connection receiver disagreement for {source_name}: {receivers}")
            connection_kind = connection["kind"]
            expected_kind = {
                "current_candidate_hardware_component": "candidate_bolt",
                "current_retained_frame_hardware_component": "retained_bolt",
                "current_panel_screw_axis_envelope_proxy": "panel_screw",
            }.get(kind)
            if connection_kind != expected_kind:
                raise AssertionError(f"Source axis family mismatch for {source_name}: {kind}/{connection_kind}")
            interval_rows = []
            if connection_kind == "candidate_bolt":
                interval_rows = connection["source_record"]["geometry"]["wood_receiver_intervals"]
                if {row["receiver_id"] for row in interval_rows} != set(receivers):
                    raise AssertionError(f"Candidate bolt intervals do not cover source receivers: {source_name}")
            carrier = {
                "carrier_id": f"connector-axis/{connection_kind}/{axis_id}",
                "carrier_kind": "connector_axis_reference",
                "receiver_member_ids": connection["receiver_member_ids"],
                "receiver_axis_id": axis_id,
                "reference_point_xyz_mm": connection["source_point_xyz_mm"],
                "connection_kind": connection_kind,
                "current_receiver_intervals": [
                    {
                        "receiver_member_id": row["receiver_id"],
                        "intervals_from_underhead_mm": row["intersection_solid_intervals_from_underhead_mm"],
                        "interval_source": "current_finished receiver-axis intersection in reduced model-inputs.json",
                    }
                    for row in interval_rows
                ],
                "receiver_interval_status": (
                    "source-bound-current-intervals"
                    if interval_rows else
                    "receiver IDs and axis reference are source-bound; current axial intervals are not present in the reduced input artifact"
                ),
                "carrier_map_basis": (
                    "Exact source axis_id plus its current receiver-member references; hardware roles are condensed at that physical connection reference."
                ),
                "kinematic_assumption": (
                    "The carrier follows the current physical connection-axis DOFs associated with all listed receivers. This load mapping does not prescribe bolt/contact stiffness, fastener engagement, or receiver force split."
                ),
                "mapping_uncertainty": (
                    "Source component role and centroid are mapped; detailed mass inertia and local hardware-to-wood transfer are omitted."
                ),
            }

        reference = carrier["reference_point_xyz_mm"]
        couple = _cross(_sub(point, reference), force)
        contribution = {
            "source_name": source_name,
            "source_entity_id": entity["id"],
            "source_component_role": entity.get("component_role"),
            "mass_share_kg": mass,
            "condensation_weight": 1.0,
            "carrier_id": carrier["carrier_id"],
            "carrier_kind": carrier["carrier_kind"],
            "receiver_member_ids": carrier["receiver_member_ids"],
            "receiver_axis_id": carrier["receiver_axis_id"],
            "reference_point_xyz_mm": reference,
            "force_xyz_n": force,
            "couple_xyz_nmm_about_reference": couple,
            "source_centroid_xyz_mm": point,
            "carrier_map_basis": carrier["carrier_map_basis"],
            "kinematic_assumption": carrier["kinematic_assumption"],
            "mapping_uncertainty": carrier["mapping_uncertainty"],
        }
        load_common["carrier"] = carrier
        load_common["contributions"] = [contribution]
        output.append(load_common)

    return output


def _aggregate(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for entry in entries:
        carrier_id = entry["carrier_id"]
        if carrier_id not in groups:
            groups[carrier_id] = {
                "carrier_id": carrier_id,
                "carrier_kind": entry["carrier_kind"],
                "receiver_member_ids": entry["receiver_member_ids"],
                "receiver_axis_id": entry["receiver_axis_id"],
                "reference_point_xyz_mm": entry["reference_point_xyz_mm"],
                "mass_kg": 0.0,
                "force_xyz_n": [0.0, 0.0, 0.0],
                "couple_xyz_nmm_about_reference": [0.0, 0.0, 0.0],
                "source_names": [],
                "mapping_uncertainty": entry["mapping_uncertainty"],
            }
        group = groups[carrier_id]
        if group["reference_point_xyz_mm"] != entry["reference_point_xyz_mm"]:
            raise AssertionError(f"Carrier has inconsistent reference points: {carrier_id}")
        if group["receiver_member_ids"] != entry["receiver_member_ids"]:
            raise AssertionError(f"Carrier has inconsistent receiver list: {carrier_id}")
        group["mass_kg"] += entry["mass_share_kg"]
        group["force_xyz_n"] = _add(group["force_xyz_n"], entry["force_xyz_n"])
        group["couple_xyz_nmm_about_reference"] = _add(
            group["couple_xyz_nmm_about_reference"], entry["couple_xyz_nmm_about_reference"]
        )
        group["source_names"].append(entry["source_name"])
    return [groups[key] for key in sorted(groups)]


def _electrical_contributions(accessory: dict[str, Any],
                              hold_axes_by_label: dict[str, dict[str, Any]],
                              electrical_mass_kg: float) -> list[dict[str, Any]]:
    body_rows = accessory["electrical_body_rows"]
    total_volume = sum(row["volume_mm3"] for row in body_rows)
    if len(body_rows) != 263 or total_volume <= 0.0:
        raise AssertionError("Expected 263 positive-volume electrical source bodies")
    output: list[dict[str, Any]] = []
    for body in body_rows:
        mass = electrical_mass_kg * body["volume_mm3"] / total_volume
        source_point = body["centroid_global_xyz_mm"]
        force = _gravity(mass)
        if body["kind"] == "light":
            label = body["body_id"].removeprefix("light_")
            axis = hold_axes_by_label.get(label)
            if axis is None:
                raise AssertionError(f"Light has no same-label hold-axis support: {body['body_id']}")
            endpoint_labels = [label]
            weights = [1.0]
            basis = "Current light name labels its current hold axis; source CAD light centroid is eccentrically condensed to that face-axis support."
        elif body["kind"] == "wire":
            endpoint_labels = list(_parse_wire_endpoints(body["body_id"], hold_axes_by_label))
            weights = [0.5, 0.5]
            basis = "Current wire ID names its two light/hold-axis endpoints; equal two-endpoint condensation represents a linear end-supported wire mass and residual couples preserve the source CAD centroid exactly."
        else:
            raise AssertionError(f"Unrecognized electrical body kind: {body['kind']}")

        row_contributions = []
        for label, weight in zip(endpoint_labels, weights, strict=True):
            axis = hold_axes_by_label[label]
            reference = axis["climbing_face_axis_point_global_xyz_mm"]
            receiver = axis["panel_id"]
            carrier_id = f"hold-axis/{axis['axis_id']}"
            force_share = _scale(force, weight)
            couple_share = _scale(_cross(_sub(source_point, reference), force), weight)
            contribution = {
                "source_name": body["body_id"],
                "source_entity_id": f"electrical_cad_body/{body['body_id']}",
                "source_component_role": body["kind"],
                "mass_share_kg": mass * weight,
                "condensation_weight": weight,
                "carrier_id": carrier_id,
                "carrier_kind": "hold_axis_reference",
                "receiver_member_ids": [receiver],
                "receiver_axis_id": axis["axis_id"],
                "reference_point_xyz_mm": reference,
                "force_xyz_n": force_share,
                "couple_xyz_nmm_about_reference": couple_share,
                "source_centroid_xyz_mm": source_point,
                "carrier_map_basis": basis,
                "kinematic_assumption": (
                    "Electrical mass is allocated to current electrical CAD bodies in proportion to modeled body volume, then follows the indicated current hold-axis point(s) into their mapped panel(s). This is an analytical mass allocation and attachment model, not observed wiring support."
                ),
                "mapping_uncertainty": (
                    "Per-body electrical mass is unknown; volume-proportional allocation preserves the supplied combined-volume centroid. Wire load split among its two named endpoints is an assumed 50/50 baseline; total force and first moment are exact after the residual couple."
                ),
                "wire_endpoint_split_sensitivity": (
                    {"baseline_weights": [0.5, 0.5], "admissible_alternative_weights": [[0.0, 1.0], [1.0, 0.0]],
                     "alternatives_preserve_global_wrench_with_recomputed_residual_couples": True}
                    if body["kind"] == "wire" else None
                ),
            }
            row_contributions.append(contribution)
            output.append(contribution)
        expected_force = force
        expected_moment = _point_moment(source_point, force)
        actual_force = [0.0, 0.0, 0.0]
        actual_moment = [0.0, 0.0, 0.0]
        for contribution in row_contributions:
            f, m = _wrench_about_origin(contribution)
            actual_force = _add(actual_force, f)
            actual_moment = _add(actual_moment, m)
        _close(actual_force, expected_force)
        _close(actual_moment, expected_moment)
    return output


def _hold_contributions(accessory: dict[str, Any],
                        hold_axes_by_source: dict[str, dict[str, Any]],
                        hold_mass_kg: float,
                        hold_distribution: str) -> list[dict[str, Any]]:
    if hold_distribution == "equal_axis_weighted_face_centroid":
        axes = accessory["hold_axes"]
        weights = [1.0 / len(axes)] * len(axes)
        basis = "Equal mass share over all 142 current hold axes at their climbing-face projection points."
    elif hold_distribution.startswith("single_face_axis_endpoint:"):
        source_name = hold_distribution.split(":", 1)[1]
        axis = hold_axes_by_source.get(source_name)
        if axis is None:
            raise AssertionError(f"Scenario endpoint is not a current hold axis: {source_name}")
        axes = [axis]
        weights = [1.0]
        basis = "Full hold-and-hold-bolt scenario mass at the named current face-axis endpoint."
    else:
        raise AssertionError(f"Unsupported frozen hold distribution: {hold_distribution}")

    output = []
    for axis, weight in zip(axes, weights, strict=True):
        mass = hold_mass_kg * weight
        point = axis["climbing_face_axis_point_global_xyz_mm"]
        force = _gravity(mass)
        output.append({
            "source_name": f"accessory-hold-mass/{axis['axis_id']}",
            "source_entity_id": f"accessory_hold_scenario/{axis['axis_id']}",
            "source_component_role": "holds_and_hold_bolts_unitemized",
            "mass_share_kg": mass,
            "condensation_weight": weight,
            "carrier_id": f"hold-axis/{axis['axis_id']}",
            "carrier_kind": "hold_axis_reference",
            "receiver_member_ids": [axis["panel_id"]],
            "receiver_axis_id": axis["axis_id"],
            "reference_point_xyz_mm": point,
            "force_xyz_n": force,
            "couple_xyz_nmm_about_reference": [0.0, 0.0, 0.0],
            "source_centroid_xyz_mm": point,
            "carrier_map_basis": basis,
            "kinematic_assumption": (
                "Unitemized hold plus hold-bolt scenario mass follows the current selected hold-axis projection(s) into the same panel named by the frozen axis map. The case is analytical, not an observed accessory installation."
            ),
            "mapping_uncertainty": (
                "The total 25 kg budget is unitemized; this scenario's split and selected equal-axis or endpoint distribution are explicit sensitivity assumptions. The 142 T-nuts and listed structural fasteners remain in the modeled 224.420776668 kg inventory and are not duplicated here."
            ),
        })
    return output


def _validate_scenario_entries(scenario: dict[str, Any],
                               entries: list[dict[str, Any]]) -> dict[str, Any]:
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    mass = 0.0
    for entry in entries:
        f, m = _wrench_about_origin(entry)
        force = _add(force, f)
        moment = _add(moment, m)
        mass += entry["mass_share_kg"]
    _close(force, scenario["accessory_gravity_force_global_xyz_n"])
    _close(moment, scenario["accessory_gravity_moment_about_global_origin_nmm"])
    _close([mass], [scenario["accessory_budget_kg"]])
    return {
        "scenario_id": scenario["scenario_id"],
        "mass_kg": mass,
        "force_xyz_n": force,
        "moment_about_global_origin_xyz_nmm": moment,
        "entry_count": len(entries),
        "source_resultant_match": True,
    }


def compile_loads() -> dict[str, Any]:
    model, model_sha = _read_pinned(MODEL_INPUTS_PATH)
    centroids, centroid_sha = _read_pinned(MASS_CENTROIDS_PATH)
    topology, topology_sha = _read_pinned(MASS_TOPOLOGY_PATH)
    dead_load, dead_load_sha = _read_pinned(DEAD_LOAD_PATH)
    if model["source_sha256"].get(str(MASS_CENTROIDS_PATH)) != centroid_sha:
        raise AssertionError("Reduced model-inputs.json is not bound to the pinned mass centroid artifact")
    if model["source_sha256"].get(str(MASS_TOPOLOGY_PATH)) != topology_sha:
        raise AssertionError("Reduced model-inputs.json is not bound to the pinned source topology artifact")
    if model["source_sha256"].get(str(DEAD_LOAD_PATH)) != dead_load_sha:
        raise AssertionError("Reduced model-inputs.json is not bound to the pinned dead-load scenario artifact")
    if centroids["revision_id"] != topology["revision_id"] or centroids["revision_id"] != model["revision_id"]:
        raise AssertionError("Source mass artifacts do not share the reduced model revision")

    accessory = dead_load["accessory_allowance"]
    hold_axes_by_source, hold_axes_by_label = _label_maps(accessory)
    if len(hold_axes_by_source) != 142:
        raise AssertionError("Expected 142 source-bound hold axes")
    connection_rows = model["connections"]
    connections = {row["axis_id"]: row for row in connection_rows}
    if len(connections) != 170:
        raise AssertionError("Expected 170 unique current candidate/frame/screw axes")

    source_records = _source_rows(model, centroids, topology, connections, hold_axes_by_source)
    base_contributions = [record["contributions"][0] for record in source_records]
    if len(source_records) != 778 or len(base_contributions) != 778:
        raise AssertionError("The compiled base mass representation must include all 778 source rows once")
    if len(model["unassigned_hardware_gravity"]) != 586:
        raise AssertionError("Expected all 586 previously unassigned hardware rows")
    hardware_mass = sum(row["mass_kg"] for row in model["unassigned_hardware_gravity"])
    _close([hardware_mass], [7.728314002341739], tol=1.0e-10)

    base_total_force = [0.0, 0.0, 0.0]
    base_total_moment = [0.0, 0.0, 0.0]
    base_total_mass = 0.0
    for entry in base_contributions:
        force, moment = _wrench_about_origin(entry)
        base_total_force = _add(base_total_force, force)
        base_total_moment = _add(base_total_moment, moment)
        base_total_mass += entry["mass_share_kg"]
    _close([base_total_mass], [topology["modeled_mass_kg"]])
    _close(base_total_force, topology["gravity_force_global_xyz_n"])
    _close(base_total_moment, topology["gravity_moment_about_global_origin_nmm"])
    if len({row["source_name"] for row in source_records}) != 778:
        raise AssertionError("Source rows must be unique in the compiler result")

    accessory_scenarios = []
    accessory_summaries = []
    for scenario in accessory["scenarios"]:
        hold_entries = _hold_contributions(
            accessory, hold_axes_by_source,
            scenario["hold_and_hold_bolt_mass_kg"], scenario["hold_distribution"]
        )
        electrical_entries = _electrical_contributions(
            accessory, hold_axes_by_label, scenario["electrical_mass_kg"]
        )
        entries = hold_entries + electrical_entries
        summary = _validate_scenario_entries(scenario, entries)
        # Validate each side of the stated split separately as well as the total.
        hold_force = [0.0, 0.0, 0.0]
        hold_moment = [0.0, 0.0, 0.0]
        for entry in hold_entries:
            f, m = _wrench_about_origin(entry)
            hold_force = _add(hold_force, f)
            hold_moment = _add(hold_moment, m)
        _close(hold_force, scenario["hold_gravity"]["gravity_force_global_xyz_n"])
        _close(hold_moment, scenario["hold_gravity"]["gravity_moment_about_global_origin_nmm"])

        electrical_force = [0.0, 0.0, 0.0]
        electrical_moment = [0.0, 0.0, 0.0]
        for entry in electrical_entries:
            f, m = _wrench_about_origin(entry)
            electrical_force = _add(electrical_force, f)
            electrical_moment = _add(electrical_moment, m)
        _close(electrical_force, scenario["electrical_gravity"]["gravity_force_global_xyz_n"])
        _close(electrical_moment, scenario["electrical_gravity"]["gravity_moment_about_global_origin_nmm"])

        accessory_scenarios.append({
            "scenario_id": scenario["scenario_id"],
            "status": scenario["status"],
            "accessory_budget_kg": scenario["accessory_budget_kg"],
            "hold_and_hold_bolt_mass_kg": scenario["hold_and_hold_bolt_mass_kg"],
            "electrical_mass_kg": scenario["electrical_mass_kg"],
            "hold_distribution": scenario["hold_distribution"],
            "hold_outward_cg_offset_mm": scenario["hold_outward_cg_offset_mm"],
            "mass_allocation_assumptions": {
                "holds_and_hold_bolts": "Equal mass per current face axis for mean cases; one named axis for endpoint cases, exactly as the frozen scenario defines.",
                "electrical": "Per-body mass is allocated in proportion to the 263 modeled electrical body volumes, preserving the source combined-volume centroid. Lights route by exact label to the corresponding hold axis; wires route to the two named endpoint axes with an explicit equal-share kinematic assumption.",
                "physical_installation_status": "Analytical placement scenario, not observed installation or measured item masses.",
            },
            "entries": entries,
            "carrier_wrenches": _aggregate(entries),
            "equilibrium": summary,
            "wire_load_split_sensitivity": {
                "baseline": "Equal force shares at the two named endpoint axes, with source-centroid residual couples.",
                "alternatives": "For each wire, [0,1] and [1,0] endpoint force shares with recomputed residual couples preserve the exact source global force and first moment; local response may differ.",
                "not_run_by_this_compiler": True,
            },
        })
        accessory_summaries.append(summary)

    # Preserve useful source-count accounting at the exact carrier level.
    kind_counts: dict[str, int] = defaultdict(int)
    for record in source_records:
        kind_counts[record["source_entity_kind"]] += 1
    return {
        "schema": SCHEMA,
        "candidate": model["candidate"],
        "revision_id": model["revision_id"],
        "status": "SOURCE_BOUND_STATIC_GRAVITY_MAPPING_WITH_EXPLICIT_CARRIER_ASSUMPTIONS",
        "mechanical_acceptance": False,
        "native_solve_run": False,
        "source_sha256": {
            str(MODEL_INPUTS_PATH): model_sha,
            str(MASS_CENTROIDS_PATH): centroid_sha,
            str(MASS_TOPOLOGY_PATH): topology_sha,
            str(DEAD_LOAD_PATH): dead_load_sha,
        },
        "units": {"mass": "kg", "length": "mm", "force": "N", "moment": "N mm", "gravity": "m/s^2"},
        "gravity_m_s2": GRAVITY_M_S2,
        "base_mass_accounting": {
            "source_row_count": len(source_records),
            "source_entity_kind_counts": dict(sorted(kind_counts.items())),
            "previously_unassigned_hardware_row_count": len(model["unassigned_hardware_gravity"]),
            "previously_unassigned_hardware_mass_kg": hardware_mass,
            "total_modeled_mass_kg": base_total_mass,
            "gravity_force_global_xyz_n": base_total_force,
            "gravity_moment_about_global_origin_xyz_nmm": base_total_moment,
            "source_resultant_match": True,
            "base_carrier_count": len(_aggregate(base_contributions)),
            "use_policy": "Use carrier_wrenches as the assembled dead-load table; source_rows are its exact audit decomposition, not additional loads.",
        },
        "base_carrier_wrenches": _aggregate(base_contributions),
        "source_rows": source_records,
        "accessory_scenario_count": len(accessory_scenarios),
        "accessory_summaries": accessory_summaries,
        "accessory_scenarios": accessory_scenarios,
        "limits": [
            "The 778 source masses are modeled CAD volume/density estimates and screw-axis proxies, not measured part masses.",
            "The 586 omitted hardware rows are explicitly condensed to their source connection axes; each source role's force and centroid first moment are exact, but detailed component inertia and local engagement are not represented.",
            "Candidate bolt receiver intervals are copied from the current reduced model inputs. Retained frame-bolt and panel-screw receiver identities are source-bound, but their current axial intervals are absent from those inputs and are not fabricated here.",
            "The member, T-nut, connector, electrical light, and wire carriers require the parent model's stated kinematic mapping. This compiler does not implement their constraints or stiffness.",
            "The nine accessory cases are analytical placement scenarios. Volume-proportional per-body electrical mass and equal wire endpoint condensation are explicit assumptions; wiring attachment and actual mass distribution are unobserved.",
            "Global gravity force and first moments are exact. Local load sharing, member self-weight bending under centroid-only use, connector behavior, reactions, response, capacities, and acceptance are not established by this load map.",
        ],
    }


def focused_check() -> dict[str, Any]:
    data = compile_loads()
    base = data["base_mass_accounting"]
    if base["source_row_count"] != 778 or base["previously_unassigned_hardware_row_count"] != 586:
        raise AssertionError("Source row coverage check failed")
    if len(data["accessory_scenarios"]) != 9:
        raise AssertionError("The nine existing accessory scenarios were not retained")
    for scenario in data["accessory_summaries"]:
        if not scenario["source_resultant_match"]:
            raise AssertionError(f"Accessory equilibrium check failed: {scenario['scenario_id']}")
    return {
        "status": "PASS_SOURCE_COVERAGE_AND_STATIC_WRENCH_CONSERVATION",
        "base_source_rows": base["source_row_count"],
        "hardware_rows_mapped": base["previously_unassigned_hardware_row_count"],
        "hardware_mass_kg": base["previously_unassigned_hardware_mass_kg"],
        "base_carriers": base["base_carrier_count"],
        "accessory_scenarios": len(data["accessory_scenarios"]),
        "scenario_entry_counts": {row["scenario_id"]: row["entry_count"] for row in data["accessory_summaries"]},
        "total_mass_kg": base["total_modeled_mass_kg"],
        "gravity_force_global_xyz_n": base["gravity_force_global_xyz_n"],
        "gravity_moment_about_global_origin_xyz_nmm": base["gravity_moment_about_global_origin_xyz_nmm"],
        "native_solve_run": False,
        "mechanical_acceptance": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true", help="emit the complete carrier mapping as JSON")
    mode.add_argument("--check", action="store_true", help="run focused source-coverage and wrench checks")
    args = parser.parse_args()
    result = compile_loads() if args.json else focused_check()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
