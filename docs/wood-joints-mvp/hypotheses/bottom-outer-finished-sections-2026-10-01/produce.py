#!/usr/bin/env python3
"""Join bottom finished bore sections to complete source point-action cut demands."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = HERE.parent
FEATURES = PACKETS / "current-finished-feature-register-2026-10-01/axis-features.json"
FREEZE = PACKETS / "upper-frame-joint-review-2026-09-30/freeze.json"
CONTACT = (
    PACKETS
    / "mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
)
HOST_METHOD = PACKETS / "upper-outer-load-path-2026-10-01/host_actions.py"
SECTION_METHOD = (
    PACKETS / "upper-outer-finished-sections-2026-10-01/section_geometry.py"
)
PINS = {
    "axis_features": (
        FEATURES,
        "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    ),
    "three_case_freeze": (
        FREEZE,
        "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73",
    ),
    "source_contact_geometry": (
        CONTACT,
        "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    ),
    "point_action_method": (
        HOST_METHOD,
        "39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b",
    ),
    "finished_section_method": (
        SECTION_METHOD,
        "8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3",
    ),
}
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PREFIX = "bottom_outer/clip_horizontal_bottom_left_1/"
AXES = {f"{PREFIX}{role}_{i}" for role in ("rail", "side") for i in (1, 2)}
CLEAT, RAIL, SIDE = "bottom_outer_left_cleat", "base_rail_bottom_left", "base_side_left"
MEMBERS = {CLEAT, RAIL, SIDE}
RECEIVERS = {"rail": {CLEAT, RAIL}, "side": {CLEAT, SIDE}}
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
GATES = (
    "mpc_interval_checks_passed",
    "retained_bilateral_checks_passed",
    "springa_law_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources():
    for name, (path, digest) in PINS.items():
        require(sha(path) == digest, f"source pin changed: {name}")


def module(path, digest, name):
    require(sha(path) == digest, f"pinned method changed: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "source method unavailable")
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def frames_from_model(host, model, bindings):
    result = {}
    for member in sorted(MEMBERS):
        record = model["body_geometry"][member]["geometry_record"]
        descriptor = record["source_descriptor"]
        binding = bindings[member]
        g, u, v = [
            host.vec(record[key], f"{member} {key}")
            for key in ("axis", "section_u", "section_v")
        ]
        require(
            all(abs(host.norm(a) - 1) <= 1e-8 for a in (g, u, v))
            and all(abs(host.dot(a, b)) <= 1e-8 for a, b in ((g, u), (g, v), (u, v))),
            "source model frame is not orthonormal",
        )
        require(
            host.dot(host.cross(g, u), v) >= 1 - 1e-8,
            "source model frame handedness differs",
        )
        start, end = [
            host.vec(record[key], f"{member} {key}") for key in ("start", "end")
        ]
        length = host.dot(host.sub(end, start), g)
        require(
            length > 0 and abs(length - host.norm(host.sub(end, start))) <= 1e-6,
            "source model grain extent differs",
        )
        require(
            descriptor["step_path"] == binding["path"]
            and descriptor["step_sha256"] == binding["file_sha256"],
            "model/finished STEP identity differs",
        )
        result[member] = {
            "host": member,
            "grain_axis_global_xyz": g,
            "section_u_global_xyz": u,
            "section_v_global_xyz": v,
            "member_start_xyz_mm": start,
            "member_end_xyz_mm": end,
            "member_grain_length_mm": length,
            "step_path": binding["path"],
            "step_sha256": binding["file_sha256"],
            "transverse_assignment_status": descriptor["transverse_status"],
        }
    return result


def plan_planes(host, axes, frames):
    require(set(axes) == AXES, "four bottom axes missing or foreign")
    result = []
    for axis_id, axis in sorted(axes.items()):
        role = axis_id.removeprefix(PREFIX).split("_")[0]
        memberships = axis["receiver_memberships"]
        require(
            len(memberships) == 2
            and {r["receiver_member_id"] for r in memberships} == RECEIVERS[role],
            "bottom receiver scope differs",
        )
        fields = axis["source_axis_fields"]
        require(
            abs(host.finite(fields["occupied_diameter_mm"], "occupied diameter") - 6.35)
            < 1e-6,
            "occupied bolt diameter differs",
        )
        datum = host.vec(fields["datum_global_xyz_mm"], "source axis datum")
        direction = host.vec(fields["direction_global_xyz"], "source axis direction")
        require(
            abs(host.norm(direction) - 1) <= 1e-8, "source axis direction is not unit"
        )
        for receiver in memberships:
            member = receiver["receiver_member_id"]
            frame = frames[member]
            require(
                receiver["match_status"] == "matched_bore_patch"
                and len(receiver["matched_feature_ids"]) == 1,
                "bottom finished bore ambiguous",
            )
            matches = [
                p
                for p in receiver["cylinder_surface_candidates"]
                if p["feature_id"] == receiver["matched_feature_ids"][0]
            ]
            require(len(matches) == 1, "matched bore patch missing or duplicated")
            patch = matches[0]
            lo, hi = [
                host.finite(v, "finite bore interval")
                for v in patch["patch_interval_projected_from_axis_datum_mm"]
            ]
            require(
                patch["association_status"] == "eligible_bore_patch"
                and hi > lo
                and abs(host.finite(patch["cylinder_radius_mm"], "bore radius") - 3.75)
                < 1e-6,
                "wrong finished bore scenario",
            )
            midpoint = host.add(datum, host.scale(direction, (lo + hi) / 2))
            s = host.station(frame, midpoint)
            require(
                0 < s < frame["member_grain_length_mm"],
                "bore plane outside source member",
            )
            existing = next(
                (
                    p
                    for p in result
                    if p["member_id"] == member and abs(p["cut_station_mm"] - s) <= 1e-6
                ),
                None,
            )
            identity = {
                "axis_id": axis_id,
                "bore_feature_id": patch["feature_id"],
                "receiver_bore_midpoint_xyz_mm": midpoint,
                "source_grain_station_mm": s,
                "bore_radius_mm": patch["cylinder_radius_mm"],
            }
            if existing is not None:
                existing["axis_memberships"].append(identity)
            else:
                result.append(
                    {
                        "plane_id": f"{member}/bore-plane-{axis_id.split('/')[-1]}",
                        "member_id": member,
                        "cut_station_mm": s,
                        "plane_origin_xyz_mm": host.add(
                            frame["member_start_xyz_mm"],
                            host.scale(frame["grain_axis_global_xyz"], s),
                        ),
                        "plane_normal_xyz": frame["grain_axis_global_xyz"],
                        "axis_memberships": [identity],
                        "plane_source": "through source finite-bore midpoint, normal to unchanged model grain",
                    }
                )
    require(
        len(result) == 6 and sum(len(p["axis_memberships"]) for p in result) == 8,
        "six-plane/eight-membership coverage differs",
    )
    return sorted(result, key=lambda p: (p["member_id"], p["cut_station_mm"]))


def section_at_plane(method, shape, plane, frame):
    result = method.section_properties(
        shape,
        plane["plane_origin_xyz_mm"],
        frame["grain_axis_global_xyz"],
        frame["section_u_global_xyz"],
        frame["section_v_global_xyz"],
    )
    require(
        result["component_count"] >= 1 and result["area_mm2"] > 0,
        "finished section has no positive material",
    )
    return {
        **result,
        "common_strain_or_component_load_sharing_established": False,
        "actual_integrated_traction_established": False,
        "section_resistance_accepted": False,
    }


def crossing_contacts(actions, station, band):
    result = []
    for action in actions:
        if action["contact_patch"] is None:
            continue
        low, high = action["finite_footprint_station_bounds_mm"]
        if low + band < station < high - band:
            result.append(action["source_name"])
    return sorted(result)


def produce():
    verify_sources()
    host = module(
        HOST_METHOD, PINS["point_action_method"][1], "bottom_section_host_actions"
    )
    section = module(
        SECTION_METHOD,
        PINS["finished_section_method"][1],
        "bottom_finished_section_geometry",
    )
    features, freeze, contacts = [
        json.loads(path.read_text()) for path in (FEATURES, FREEZE, CONTACT)
    ]
    require(
        features["candidate"] == CANDIDATE
        and features["geometry_revision_id"] == REVISION,
        "finished feature identity differs",
    )
    all_axes = features["source_axis_groups"]["candidate_bolt_axes"]["axes"]
    require(
        len(all_axes) == 92 and len({a["axis_id"] for a in all_axes}) == 92,
        "candidate bolt coverage differs",
    )
    axes = {a["axis_id"]: a for a in all_axes if a["axis_id"] in AXES}
    require(set(axes) == AXES, "four bottom axes missing")
    bindings = {}
    for axis in axes.values():
        for r in axis["receiver_memberships"]:
            member, binding = (
                r["receiver_member_id"],
                r["current_finished_step_binding"],
            )
            require(
                member not in bindings or bindings[member] == binding,
                "member STEP binding inconsistent",
            )
            require(
                sha(ROOT / binding["path"]) == binding["file_sha256"],
                "finished STEP changed",
            )
            bindings[member] = binding
    require(
        set(bindings) == MEMBERS
        and set(freeze["cases"]) == {"a1-rear", "a12-rear", "k12-rear"},
        "member/case scope differs",
    )
    source_cases = {}
    for case, files in freeze["cases"].items():
        for pin in files.values():
            require(
                sha(ROOT / pin["path"]) == pin["sha256"], "frozen case source changed"
            )
        model, response, audit = [
            json.loads((ROOT / files[k]["path"]).read_text())
            for k in ("model", "response", "all_body_audit")
        ]
        require(
            model["candidate"] == response["candidate"] == CANDIDATE
            and model["geometry_revision_id"]
            == response["geometry_revision_id"]
            == REVISION
            and model["case_id"] == response["case_id"] == case,
            "frozen case identity differs",
        )
        require(
            tuple(i["load_factor"] for i in response["increments"]) == FACTORS
            and tuple(i["load_factor"] for i in audit["increments"]) == FACTORS,
            "seven-state source coverage differs",
        )
        source_cases[case] = (model, response, audit)
    frames = frames_from_model(host, source_cases["a1-rear"][0], bindings)
    require(
        all(
            frames_from_model(host, m, bindings) == frames
            for m, _, _ in source_cases.values()
        ),
        "case member frames differ",
    )
    planes = plan_planes(host, axes, frames)
    import cadquery as cq

    shapes = {
        member: cq.importers.importStep(str(ROOT / b["path"])).val()
        for member, b in bindings.items()
    }
    for member, shape in shapes.items():
        require(
            shape.isValid()
            and len(shape.Solids()) == 1
            and len(shape.Faces()) == bindings[member]["face_count"],
            "source finished solid invalid or changed",
        )
    for plane in planes:
        member = plane["member_id"]
        plane["finished_section"] = section_at_plane(
            section, shapes[member], plane, frames[member]
        )
    states, body_states = [], []
    baseline_geometry = {}
    for case, (model, response, audit) in source_cases.items():
        for index, (increment, audited) in enumerate(
            zip(response["increments"], audit["increments"], strict=True)
        ):
            require(
                all(increment.get(gate) is True for gate in GATES)
                and audited["passed"] is True,
                "source response gate failed",
            )
            identity = {
                "case_id": case,
                "increment_index": index,
                "load_factor": increment["load_factor"],
            }
            for member, frame in frames.items():
                actions, _, _ = host.host_actions_for_state(
                    model, increment, member, frame, contacts
                )
                point_geometry = [
                    {
                        k: a[k]
                        for k in (
                            "action_id",
                            "source_name",
                            "source_row_ids",
                            "source_kind",
                            "role",
                            "body",
                            "other_body",
                            "point_xyz_mm",
                            "grain_station_mm",
                            "finite_footprint_station_bounds_mm",
                        )
                    }
                    for a in actions
                ]
                require(
                    member not in baseline_geometry
                    or baseline_geometry[member] == point_geometry,
                    "source action geometry changed across states",
                )
                baseline_geometry[member] = point_geometry
                balance = host.host_balance(model, increment, audited, member, actions)
                body_states.append(
                    {
                        **identity,
                        "member_id": member,
                        "source_action_count": len(actions),
                        "whole_body_source_balance": {
                            k: v for k, v in balance.items() if k != "_external_wrench"
                        },
                    }
                )
                for plane in [p for p in planes if p["member_id"] == member]:
                    for trace in (
                        "approached_from_negative_station",
                        "approached_from_positive_station",
                    ):
                        cut = host.cut_trace(
                            actions,
                            plane["cut_station_mm"],
                            frame,
                            trace,
                            balance["_external_wrench"],
                        )
                        centroid = plane["finished_section"]["centroid_global_xyz_mm"]
                        positive_centroid = host.transport_wrench(
                            cut["internal_cut_wrench_on_positive_side_material"],
                            cut["cut_plane_origin_xyz_mm"],
                            centroid,
                        )
                        negative_centroid = host.transport_wrench(
                            cut["internal_cut_wrench_on_negative_side_material"],
                            cut["cut_plane_origin_xyz_mm"],
                            centroid,
                        )
                        states.append(
                            {
                                **identity,
                                "plane_id": plane["plane_id"],
                                "member_id": member,
                                "source_point_action_cut": cut,
                                "positive_internal_wrench_at_finished_area_centroid": positive_centroid,
                                "negative_internal_wrench_at_finished_area_centroid": negative_centroid,
                                "positive_local_wrench_at_finished_area_centroid": host.local_wrench(
                                    positive_centroid, frame
                                ),
                                "negative_local_wrench_at_finished_area_centroid": host.local_wrench(
                                    negative_centroid, frame
                                ),
                                "finite_contact_patch_bounds_crossing_plane": crossing_contacts(
                                    actions,
                                    plane["cut_station_mm"],
                                    host.STATION_BAND_MM,
                                ),
                                "finite_patch_or_ligament_force_distribution_established": False,
                                "section_resistance_accepted": False,
                            }
                        )
    require(
        len(states) == 252 and len(body_states) == 63, "cut/body state coverage differs"
    )
    return {
        "schema": "bottom_outer_finished_sections/v1",
        "status": "PASS_FROZEN_GEOMETRY_AND_POINT_ACTION_DEMAND_JOIN_ONLY",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "producer_sha256": sha(HERE / "produce.py"),
        "source_pins": {
            k: {"path": str(p.relative_to(ROOT)), "sha256": h}
            for k, (p, h) in PINS.items()
        },
        "case_sources": freeze["cases"],
        "member_frames": frames,
        "member_action_geometry": baseline_geometry,
        "planes": planes,
        "whole_body_states": body_states,
        "cut_states": states,
        "counts": {
            "axes": 4,
            "members": 3,
            "receiver_memberships": 8,
            "unique_planes": 6,
            "whole_body_states": 63,
            "two_trace_cut_states": 252,
        },
        "claim_limits": {
            "current_cases": 3,
            "actual_traction": False,
            "common_strain": False,
            "per_ligament_force_sharing": False,
            "adopted_resistance": False,
            "criterion_pass": False,
            "joint_accepted": False,
            "native_solve": False,
            "geometry_changed": False,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(produce(), indent=2, allow_nan=False))
