#!/usr/bin/env python3
"""Prepare proposed joint-local front-face N datums from frozen saved geometry.

The installed inventory is reused byte-for-byte from the ordinary-N packet.
Only source-bound arithmetic and saved finite-face predicates are evaluated.
No station datum, dimensioned exception or criterion acceptance is adopted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = HERE / "rawlocal" / "station-n-envelope"
H = "docs/wood-joints-mvp/hypotheses"
R = f"{H}/mvp-resume-2026-10-01"
U = f"{R}/upper-corner-screw-layout"
A = f"{R}/assembly-package"
F = f"{H}/current-finished-feature-register-2026-10-01"
M = f"{H}/retained-frame-bolt-finished-edges-2026-10-01"
INPUTS = {
    "ordinary": (f"{A}/rawlocal/ordinary-n-envelope/attempt01/envelope.json", "278407d84e0061ab845ff73fb31dfc5551300a3afb9aa20327a5cca9e6b86ffc"),
    "ordinary_receipt": (f"{A}/rawlocal/ordinary-n-envelope/attempt01/receipt.json", "8cec13103d82b262cdbd9446aefb2227ecc0270ebb241999366bc1be8f690fc2"),
    "ordinary_producer": (f"{A}/ordinary-n-envelope.py", "2986919f215d9aaeb857e5d3b9a79b85e148e47cba418c7a14979eb594f0430a"),
    "manifest": (f"{U}/rawlocal/knee-bridge-working-package/attempt02/manifest.json", "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0"),
    "model": (f"{U}/operators-attempt02/model-inputs.json", "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc"),
    "working_axes": (f"{A}/rawlocal/working-order/attempt03/working-order-axes.csv", "b5eb648c0e684f110efd6ec39700e1ba954bbea6642cff88dac6b8022b5cde5f"),
    "surfaces": (f"{F}/surfaces.json", "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb"),
    "axis_features": (f"{F}/axis-features.json", "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19"),
    "method": (f"{M}/method.py", "3aabafb6c1ce25545ae00050dc213ba82a749a9c6ef5a8c0d4819f47c2532aa4"),
    "method_pins": (f"{M}/source-pins.json", "2d7050f533e315fb28a635b93546e1e5d2036011eddfb77e966dcd73c947f9c9"),
    "top": (f"{R}/top-corner-correction/proposal.json", "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2"),
    "knee": (f"{U}/rawlocal/knee-bridge-geometry/attempt01/manifest.json", "254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147"),
    "criteria": ("docs/wood-joints-mvp/criteria.json", "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784"),
    "plan": ("docs/wood-joints-mvp/plan.md", "2aa0806ae16d2f6b933c67c04edb5308b05fbec2dc6b4fa196634eda49f7e197"),
    "decisions": ("docs/wood-joints-mvp/decision-log.md", "0b4b9ffc85ac2c3421b79af20a0b91616c88e39e4a66a092ccfe2032725cd0d0"),
}
N = (0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0)))
T = (0.0, math.cos(math.radians(50.0)), math.sin(math.radians(50.0)))
LIMIT = 139.7
TOL = 1e-5
FALSE_CLAIMS = {
    "convention_adopted": False,
    "station_datum_adopted": False, "dimensioned_exception_adopted": False,
    "criterion_acceptance": False, "criterion_closed": False,
    "candidate_adopted": False, "physical_release": False, "fabrication_release": False,
    "delivered_hardware_verified": False, "contact_proved": False,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authenticate(expected: dict[str, str]) -> dict[str, str]:
    actual = {}
    for relative, digest in expected.items():
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"Missing pinned source: {relative}")
        actual[relative] = sha(path)
        if actual[relative] != digest:
            raise ValueError(f"Changed pinned source: {relative}: {actual[relative]} != {digest}")
    return actual


def read(name: str) -> dict:
    return json.loads((ROOT / INPUTS[name][0]).read_text(encoding="utf-8"))


def reference(name: str, pointer: str = "") -> dict:
    path, digest = INPUTS[name]
    return {"path": path, "sha256": digest, "record_pointer": pointer}


def vec(values) -> tuple[float, float, float]:
    values = tuple(float(value) for value in values)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError(f"Invalid XYZ vector: {values!r}")
    return values


def dot(a, b) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def advance(origin, axis, distance) -> tuple[float, float, float]:
    return vec(p + distance * d for p, d in zip(origin, axis, strict=True))


def mean(points) -> tuple[float, float, float]:
    if not points:
        raise ValueError("A station group has no bearing anchors")
    return vec(math.fsum(point[i] for point in points) / len(points) for i in range(3))


def module():
    """Load the pinned inert stdlib module; call only finite saved-face predicates."""
    name = "station_n_saved_face_predicates"
    spec = importlib.util.spec_from_file_location(name, ROOT / INPUTS["method"][0])
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load pinned finite-face predicates")
    helper = importlib.util.module_from_spec(spec)
    sys.modules[name] = helper
    previous_bytecode_policy = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(helper)
    finally:
        sys.dont_write_bytecode = previous_bytecode_policy
    return helper


def build(output: str | Path) -> dict:
    output = Path(output).resolve()
    if output.parent != OUT.resolve() or output.exists():
        raise ValueError("Output must be a fresh immediate child of rawlocal/station-n-envelope")
    expected = {path: digest for path, digest in INPUTS.values()}
    authenticate(expected)
    producer = Path(__file__).resolve()
    producer_bytes = producer.read_bytes()
    producer_sha = hashlib.sha256(producer_bytes).hexdigest()
    ordinary, receipt, manifest = (read(name) for name in ("ordinary", "ordinary_receipt", "manifest"))
    model, atlas, axis_features = (read(name) for name in ("model", "surfaces", "axis_features"))
    top, knee, criteria = (read(name) for name in ("top", "knee", "criteria"))
    if receipt["output_sha256"]["envelope.json"] != INPUTS["ordinary"][1]:
        raise ValueError("Ordinary inventory receipt does not bind its frozen result")
    if receipt["producer"]["sha256"] != INPUTS["ordinary_producer"][1]:
        raise ValueError("Ordinary inventory producer receipt differs")
    if any(abs(a - b) > 1e-12 for a, b in zip(N, ordinary["definition"]["canonical_n_global_xyz"], strict=True)):
        raise ValueError("Canonical N differs from the frozen installed inventory")
    if ordinary["counts"]["bolt_axes"] != 108 or ordinary["counts"]["stack_components"] != 540:
        raise ValueError("Expected 108 complete installed stacks")
    with (ROOT / INPUTS["working_axes"][0]).open(newline="", encoding="utf-8-sig") as handle:
        working = {row["axis_id"]: row for row in csv.DictReader(handle)}
    members = {row["member_id"]: row for row in model["members"]}
    surfaces = {row["member_id"]: row for row in atlas["records"]}
    effective = {row["body"]: row for row in manifest["geometry"]["effective_members"]}
    blocks = {body for body, row in members.items() if "current_candidate_timber" in row["composition_roles"]}
    existing = {row["axis_id"]: row for row in manifest["existing_bolt_axes"]}
    internal = {row["axis_id"]: row for row in manifest["proposed_internal_bolt_axes"]}
    axes = {row["axis_id"]: row for row in ordinary["axes"]}
    components = {row["component_id"]: row for row in ordinary["components"]}
    shafts = {row["axis_id"]: row for row in ordinary["components"] if row["role"] == "shaft"}
    if len(blocks) != 24 or len(effective) != 50 or len(working) != 104 or set(working) != set(existing):
        raise ValueError("Frozen member/working-axis census differs")
    # Bind both the effective geometry and any old signatures actually reused.
    for row in effective.values():
        binding = row["effective_proposal_step"]
        expected[binding["path"]] = binding["sha256"]
    for row in surfaces.values():
        binding = row["step_binding"]
        expected[binding["path"]] = binding["file_sha256"]
    before = authenticate(expected)
    helper = module()
    plane_cache, plane_errors, member_cache = {}, {}, {}

    def host_planes(host):
        if host in plane_cache:
            return plane_cache[host]
        if host not in surfaces:
            plane_errors[host] = ["No saved finished timber-face record for named host"]
            plane_cache[host] = []
            return []
        source = surfaces[host]
        current = effective[host]["effective_proposal_step"]
        binding = source["step_binding"]
        reuse = []
        if binding["file_sha256"] != current["sha256"]:
            if host not in {"base_side_left", "base_side_right"} or top["proposal_step_sha256"].get(current["path"]) != current["sha256"]:
                plane_errors[host] = ["Saved finished signature does not match effective host STEP, and no frozen exterior reuse applies"]
                plane_cache[host] = []
                return []
            proposal = next(row for row in top["proposals"]
                            if row["block"] == ("top_outer_left_cleat" if host.endswith("left") else "top_outer_right_cleat"))
            side_axes = [row for row in proposal["axes"] if "/side_" in row["axis_id"]]
            for row in side_axes:
                facts = row["host_geometry_comparators"]
                radius = float(row["proposed_CAD_bore_envelope_mm"]) / 2.0
                if min(facts["grain_end_distances_mm"] + facts["transverse_edge_distances_mm"]) <= radius:
                    raise ValueError(f"Frozen changed side bore reaches the outer YZ perimeter: {row['axis_id']}")
                reuse.append({"axis_id": row["axis_id"], "radius_mm": radius,
                              "old_axis_point_xyz_mm": row["old_axis_point_mm"],
                              "new_axis_point_xyz_mm": row["proposed_axis_point_mm"],
                              "grain_end_distances_mm": facts["grain_end_distances_mm"],
                              "transverse_edge_distances_mm": facts["transverse_edge_distances_mm"]})
        compiled, cylinders, errors = [], [], []
        for feature in source["features"]:
            try:
                if feature["surface_kind"] == "PLANE":
                    compiled.append(helper._compile_plane(feature))
                elif feature["surface_kind"] == "CYLINDER":
                    cylinders.append(helper._compile_cylinder(feature))
                else:
                    errors.append({"feature_id": feature["feature_id"],
                                   "reason": f"Unsupported saved surface kind {feature['surface_kind']}"})
            except ValueError as error:
                errors.append({"feature_id": feature["feature_id"], "reason": str(error)})
        plane_cache[host] = [plane for plane in compiled if plane.outer_is_polygon]
        plane_errors[host] = errors
        member_cache[host] = (helper._Member(host, tuple(compiled), tuple(cylinders),
                                            frozenset(feature["feature_id"] for feature in source["features"]))
                              if not errors and compiled else None)
        exterior_reuse[host] = {
            "saved_binding": binding, "effective_binding": current,
            "changed_exterior_reuse": bool(reuse), "two_X_bore_perimeter_evidence": reuse,
            "reuse_limit": "For changed side hosts, replaced X bores remain clear of the external YZ perimeter; N-facing exterior plane/polygon and other archived trim are reused. Changed X-face bore trims are not queried along canonical N.",
        }
        return plane_cache[host]

    memberships = {}
    for group in axis_features["source_axis_groups"].values():
        for row in group["axes"]:
            for membership in row["receiver_memberships"]:
                memberships[(row["axis_id"], membership["receiver_member_id"])] = membership
    exterior_reuse = {}

    def own_fill(host, plane, point, axis_ids):
        """Fill only a matched bore whose finite centerline contains this anchor."""
        filled, facts = set(), []
        by_id = {feature["feature_id"]: feature for feature in surfaces[host]["features"]}
        for axis_id in axis_ids:
            for feature_id in memberships.get((axis_id, host), {}).get("matched_feature_ids", []):
                feature = by_id.get(feature_id)
                if feature is None or feature["surface_kind"] != "CYLINDER":
                    continue
                try:
                    cylinder = helper._compile_cylinder(feature)
                except ValueError:
                    continue
                delta = tuple(a - b for a, b in zip(point, cylinder.origin, strict=True))
                station = dot(delta, cylinder.axis)
                radial = tuple(delta[i] - station * cylinder.axis[i] for i in range(3))
                if math.sqrt(dot(radial, radial)) > TOL or not cylinder.low - TOL <= station <= cylinder.high + TOL:
                    continue
                for wire, center, circle_axis, radius in plane.circle_loops:
                    matches, _ = helper._circle_matches_endpoint(center, circle_axis, radius, cylinder)
                    if wire > 1 and matches:
                        filled.add(wire)
                        facts.append({"axis_id": axis_id, "own_feature_id": feature_id,
                                      "plane_feature_id": plane.feature_id, "filled_inner_wire": wire,
                                      "contact_proof": False})
        return frozenset(filled), facts

    def ray_context(host, point, axis_ids):
        host_planes(host)
        member = member_cache.get(host)
        if member is None:
            return None, "No complete supported finite saved surface record for this host"
        wires, fill_facts = set(), []
        for plane in member.planes:
            filled, facts = own_fill(host, plane, point, axis_ids)
            wires.update((plane.feature_id, wire) for wire in filled)
            fill_facts.extend(facts)
        own_ids = {fact["own_feature_id"] for fact in fill_facts}
        if len(own_ids) > 1:
            return None, "Anchor lies on multiple matched own bores; no single fill is inferred"
        own_id = next(iter(own_ids), "__station_reference_no_own_bore__")
        suppressed_caps = []
        if own_ids:
            cylinder = next(cylinder for cylinder in member.cylinders if cylinder.feature_id == own_id)
            for plane in member.planes:
                if plane.outer_is_polygon:
                    continue
                for _, center, circle_axis, radius in plane.circle_loops:
                    matches, _ = helper._circle_matches_endpoint(center, circle_axis, radius, cylinder)
                    if matches:
                        suppressed_caps.append(plane.feature_id)
            # Filling this one finite own bore for a datum reference also removes
            # its blind cap. Other cylindrical walls, holes and caps remain.
            member = helper._Member(member.member_id,
                                     tuple(plane for plane in member.planes if plane.feature_id not in suppressed_caps),
                                     member.cylinders, member.feature_ids)
        return {"member": member, "own_id": own_id, "own_wires": frozenset(wires),
                "filled_own_bore_reference_only": fill_facts,
                "suppressed_own_blind_caps_reference_only": suppressed_caps}, None

    def oriented_trace(host, point, direction, context):
        # Changed side-host X bores are not present in the old signature. A ray
        # touching their old or new occupancy cannot inherit that full trace.
        if abs(abs(dot(direction, N)) - 1.0) < 1e-8:
            for change in exterior_reuse.get(host, {}).get("two_X_bore_perimeter_evidence", []):
                for label, center, radius in (("old", change["old_axis_point_xyz_mm"], 3.75),
                                               ("new", change["new_axis_point_xyz_mm"], change["radius_mm"])):
                    delta = tuple(a - b for a, b in zip(point, center, strict=True))
                    if abs(dot(delta, T)) <= radius + TOL:
                        return {"events": [], "origin_inside_reference_material": None,
                                "reason": f"Canonical-N ray can intersect {label} replaced X bore {change['axis_id']}; old full surface trace is not transferred"}
        raw, ambiguities = helper._raw_hits(context["member"], point, direction,
                                            context["own_id"], context["own_wires"], fill_own_hole=True)
        events = helper._group_hits(raw)
        inside = bool(events and events[0]["entry_or_exit"] == "exit")
        _, sequence_reason = helper._trace_state(events, initially_inside=inside)
        reason = ambiguities[0] if ambiguities else sequence_reason
        return {"direction_xyz": list(direction), "events": events,
                "origin_inside_reference_material": inside if reason is None else None,
                "reason": reason}

    def front_datum(group_id, host, anchor, axis_ids, anchor_sources):
        result = {"datum_id": group_id, "host": host, "anchor_xyz_mm": list(anchor),
                  "anchor_sources": anchor_sources, "origin_xyz_mm": None,
                  "canonical_n_global_xyz": list(N), "ray_direction_xyz": [-v for v in N],
                  "status": "unsupported", "supporting_plane_fallback_used": False,
                  "source": reference("surfaces"), "method": reference("method"),
                  "finite_face_errors": [], **FALSE_CLAIMS}
        context, reason = ray_context(host, anchor, axis_ids)
        result["finite_face_errors"] = plane_errors.get(host, [])
        if reason:
            result["reason"] = reason
            return result
        front = oriented_trace(host, anchor, tuple(-value for value in N), context)
        back = oriented_trace(host, anchor, N, context)
        result["finite_oriented_traces"] = {"front": front, "back": back}
        result["filled_own_bore_reference_only"] = context["filled_own_bore_reference_only"]
        result["suppressed_own_blind_caps_reference_only"] = context["suppressed_own_blind_caps_reference_only"]
        if front["reason"] or back["reason"]:
            result["reason"] = front["reason"] or back["reason"]
            return result
        if not front["origin_inside_reference_material"] or not back["origin_inside_reference_material"]:
            result["reason"] = "Finite oriented crossings in both +/-N do not place the fixed anchor inside the receiver reference material; origin is not moved"
            return result
        exterior = next((event for event in front["events"] if event["entry_or_exit"] == "exit"
                         and event["exterior_classification"] == "polygon_outerwire_plane"), None)
        if exterior is None:
            result["reason"] = "No finite front exterior polygon exit along -N with non-own holes retained"
            return result
        result.update({"status": "proposed_finite_front_face_datum",
                       "origin_xyz_mm": exterior["point_global_xyz_mm"],
                       "front_ray_distance_mm": exterior["distance_mm"], "front_face_hits": [exterior],
                       "reason": "First finite front exterior exit along -N from the fixed mean bearing anchor, with consistent oriented reference-material crossings in both +/-N"})
        return result

    def bearing_anchor(axis_id, host):
        row = working[axis_id]
        intervals = json.loads(row["working_profile_member_bearing_intervals"])
        match = [entry for entry in intervals if entry["receiver_id"] == host]
        if len(match) != 1:
            raise ValueError(f"Expected one current working bearing interval: {axis_id}/{host}")
        low, high = match[0]["underhead_interval_mm"]
        shaft = shafts[axis_id]["geometry"]
        point = advance(shaft["start_xyz_mm"], shaft["direction_xyz"], (low + high) / 2.0)
        return point, {"axis_id": axis_id, "host": host,
                       "bearing_interval_from_installed_underhead_mm": [low, high],
                       "bearing_midpoint_xyz_mm": list(point),
                       "working_profile": reference("working_axes"),
                       "shaft_component": f"{axis_id}/shaft", "inventory": reference("ordinary")}

    def screw_anchor(host, axis_id, geometry):
        origin, direction = vec(geometry["start_xyz_mm"]), vec(geometry["direction_xyz"])
        nominal = float(geometry["length_mm"])
        host_planes(host)
        member = member_cache.get(host)
        source = {"axis_id": axis_id, "purchased_nominal_length_mm": nominal,
                  "inventory": reference("ordinary"), "axis_feature_source": reference("axis_features"),
                  "anchor_interval_is_contact_proof": False}
        if member is None:
            return None, source, "No complete finite receiver signature for the screw anchor"
        feature_ids = set(memberships.get((axis_id, host), {}).get("matched_feature_ids", []))
        intervals = []
        for cylinder in member.cylinders:
            if cylinder.feature_id not in feature_ids or abs(abs(dot(direction, cylinder.axis)) - 1.0) > 1e-8:
                continue
            delta = tuple(a - b for a, b in zip(origin, cylinder.origin, strict=True))
            station = dot(delta, cylinder.axis)
            radial = tuple(delta[i] - station * cylinder.axis[i] for i in range(3))
            if math.sqrt(dot(radial, radial)) > TOL:
                continue
            ends = [dot(tuple(p[i] - origin[i] for i in range(3)), direction)
                    for p in (advance(cylinder.origin, cylinder.axis, cylinder.low),
                              advance(cylinder.origin, cylinder.axis, cylinder.high))]
            low, high = max(0.0, min(ends)), min(nominal, max(ends))
            if high - low > TOL:
                intervals.append({"feature_id": cylinder.feature_id,
                                  "finite_interval_from_current_screw_origin_mm": [low, high]})
        intervals.sort(key=lambda row: (row["finite_interval_from_current_screw_origin_mm"][0], row["feature_id"]))
        if intervals:
            low, high = intervals[0]["finite_interval_from_current_screw_origin_mm"]
            selected = [intervals[0]]
            for row in intervals[1:]:
                a, b = row["finite_interval_from_current_screw_origin_mm"]
                if a > high + TOL:
                    break
                high = max(high, b)
                selected.append(row)
            source.update({"basis": "First contiguous matched finite receiver-bore interval, verified coaxial with the current saved screw axis and clipped to nominal occupancy; own-bore external-reference anchor only",
                           "matched_finite_intervals": selected,
                           "anchor_interval_from_screw_origin_mm": [low, high]})
            return advance(origin, direction, (low + high) / 2.0), source, None
        # Current moved screws can lack an old bore match. Trace their actual
        # finite saved receiver surfaces; do not substitute a convex box/prism.
        context, reason = ray_context(host, origin, [axis_id])
        if reason:
            return None, source, reason
        forward = oriented_trace(host, origin, direction, context)
        reverse = oriented_trace(host, origin, tuple(-value for value in direction), context)
        source["finite_receiver_axis_traces"] = {"forward": forward, "reverse": reverse}
        if forward["reason"] or reverse["reason"]:
            return None, source, forward["reason"] or reverse["reason"]
        if forward["origin_inside_reference_material"] != reverse["origin_inside_reference_material"]:
            return None, source, "Opposite finite screw-axis crossing traces disagree on source-origin membership"
        start = 0.0 if forward["origin_inside_reference_material"] else None
        for event in forward["events"]:
            if event["entry_or_exit"] == "entry":
                start = event["distance_mm"]
            elif event["entry_or_exit"] == "exit" and start is not None:
                low, high = max(0.0, start), min(nominal, event["distance_mm"])
                if high - low > TOL:
                    source.update({"basis": "First finite oriented receiver-material interval along the current screw axis, clipped to nominal occupancy; no convex-shell replacement",
                                   "anchor_interval_from_screw_origin_mm": [low, high]})
                    return advance(origin, direction, (low + high) / 2.0), source, None
                start = None
        return None, source, "No finite oriented receiver interval overlaps the purchased nominal screw occupancy"

    groups, block_axes = {}, defaultdict(set)
    station_ids = {row["axis_id"]: row.get("source_record", {}).get("station_id")
                   for row in model["connections"]}
    for axis_id, row in existing.items():
        receivers = set(row["receivers"])
        for block in receivers & blocks:
            block_axes[block].add(axis_id)
            for host in receivers - blocks:
                key = f"connector/{block}/host/{host}"
                group = groups.setdefault(key, {"group_id": key, "kind": "connector_host",
                                               "connector": block, "host": host,
                                               "interface_axis_ids": [], "recorded_station_ids": []})
                group["interface_axis_ids"].append(axis_id)
                if station_ids.get(axis_id):
                    group["recorded_station_ids"].append(station_ids[axis_id])
    for axis_id, row in internal.items():
        if len(row["receivers"]) != 1 or row["receivers"][0] not in blocks:
            raise ValueError(f"New same-body knee receiver differs: {axis_id}")
        block_axes[row["receivers"][0]].add(axis_id)
    retained_pairs = defaultdict(list)
    for axis_id, row in existing.items():
        if not set(row["receivers"]) & blocks:
            retained_pairs[tuple(sorted(row["receivers"]))].append(axis_id)
    if len(retained_pairs) != 6 or sum(map(len, retained_pairs.values())) != 12 or any(len(ids) != 2 for ids in retained_pairs.values()):
        raise ValueError("Retained axes do not reconcile to six two-bolt receiver pairs")
    for pair, axis_ids in sorted(retained_pairs.items()):
        for host in pair:
            key = f"retained/{'::'.join(pair)}/host/{host}"
            groups[key] = {"group_id": key, "kind": "retained_pair_host", "connector": None,
                           "host": host, "receiver_pair": list(pair),
                           "interface_axis_ids": sorted(axis_ids), "associated_axis_ids": sorted(axis_ids),
                           "recorded_station_ids": [], "retained_exemption": False}

    body_projections = {}
    top_by_body = {row["block"]: row for row in top["proposals"]}
    for body in sorted(blocks):
        current = effective[body]["effective_proposal_step"]
        points, status, source = [], "supported_outer_geometry_projection", reference("surfaces")
        if body in top_by_body:
            proposal = top_by_body[body]
            if top["proposal_step_sha256"].get(current["path"]) != current["sha256"]:
                raise ValueError(f"Corrected top STEP is not proposal-bound: {body}")
            descriptor = members[body]["reduced_geometry_descriptor"]
            center = advance(mean([vec(descriptor["start"]), vec(descriptor["end"])]), T,
                             float(proposal["center_translation_T_mm"]))
            width, depth = proposal["proposed_section_X_T_mm"]
            length = proposal["grain_length_mm"]
            for x, t, n in product((-width / 2, width / 2), (-depth / 2, depth / 2), (-length / 2, length / 2)):
                points.append(advance(advance(advance(center, (1.0, 0.0, 0.0), x), T, t), N, n))
            source = reference("top", f"/proposals/{top['proposals'].index(proposal)}")
            basis = "Corrected 88.9 x139.7 x119.7 mm oriented outer box, translated -25.4 mm along T; bores do not remove outer corners. Old top atlas/world boxes are not used."
        elif body in knee["bodies"]:
            saved = knee["bodies"][body]
            if saved["source_bounds_max_change_mm"] != 0.0 or saved["exports"].get(f"{body}.proposal.step", {}).get("sha256") != current["sha256"]:
                raise ValueError(f"Effective knee exterior is not unchanged-bound: {body}")
            box = saved["proposal"]["analytic"]["bounds_xyz_mm"]
            points = [vec(point) for point in product(*box)]
            source = reference("knee", f"/bodies/{body}")
            basis = "Recorded analytic/observed exterior stock bounds unchanged by two added v bores; corners and their N extrema remain."
        elif body in surfaces and surfaces[body]["step_binding"]["file_sha256"] == current["sha256"]:
            unsupported = []
            for feature in surfaces[body]["features"]:
                if feature["surface_kind"] != "PLANE":
                    continue
                wire = next((wire for wire in feature["trim"]["wires"] if wire["wire_index_one_based"] == 1), None)
                if wire and all(edge["curve_kind"] == "LINE" for edge in wire["edges"]):
                    for edge in wire["edges"]:
                        points.extend(vec(point) for point in edge["parameter_endpoint_global_xyz_mm"])
                elif wire and not (len(wire["edges"]) == 1 and wire["edges"][0]["curve_kind"] == "CIRCLE"):
                    unsupported.append(feature["feature_id"])
            basis = "Saved finite outer-polygon LINE endpoints on unchanged finished STEP; bore circles/blind caps do not define the outer stock extent."
            if unsupported:
                status, points = "unsupported_outer_geometry_projection", []
                basis += f" Unsupported exterior wire features: {unsupported}."
        else:
            status = "unsupported_outer_geometry_projection"
            basis = "No exact saved outer geometry matching this effective body"
        values = [dot(N, point) for point in points]
        body_projections[body] = {"body": body, "status": status,
                                  "global_n_extrema_mm": [min(values), max(values)] if values else None,
                                  "saved_point_count": len(points), "basis": basis,
                                  "source": source, "effective_step": current,
                                  "CAD_loaded": False, "collision_proof": False}

    datums, comparisons, group_rows, unsupported = [], [], [], []

    def comparison(group, object_id, role, extrema, basis, controlling_ids=None):
        origin = group["datum"]["origin_xyz_mm"]
        available = origin is not None and extrema is not None
        shift = dot(N, origin) if available else None
        low, high = ((extrema[0] - shift, extrema[1] - shift) if available else (None, None))
        row = {"group_id": group["group_id"], "group_kind": group["kind"],
               "host": group["host"], "connector": group.get("connector"),
               "object_id": object_id, "role": role, "datum_status": group["datum"]["status"],
               "n_min_mm": low, "n_max_mm": high, "reference_upper_n_mm": LIMIT,
               "dimensioned_conditional_excess_mm": max(0.0, high - LIMIT) if available else None,
               "geometry_basis": basis, "controlling_component_ids": controlling_ids or [],
               "station_datum_adopted": False, "dimensioned_exception_adopted": False,
               "criterion_acceptance": False, "physical_release": False}
        comparisons.append(row)
        return row

    for key, group in sorted(groups.items()):
        interface_ids = sorted(set(group["interface_axis_ids"]))
        anchors = [bearing_anchor(axis_id, group["host"]) for axis_id in interface_ids]
        anchor = mean([point for point, _ in anchors])
        group["interface_axis_ids"] = interface_ids
        group["recorded_station_ids"] = sorted(set(group["recorded_station_ids"]))
        group["datum"] = front_datum(key, group["host"], anchor, interface_ids, [source for _, source in anchors])
        datums.append(group["datum"])
        if group["kind"] == "connector_host":
            group["associated_axis_ids"] = sorted(block_axes[group["connector"]])
            projection = body_projections[group["connector"]]
            comparison(group, group["connector"], "whole_connector_body",
                       projection["global_n_extrema_mm"], projection["basis"])
        for axis_id in group["associated_axis_ids"]:
            for component_id in axes[axis_id]["component_ids"]:
                saved = components[component_id]
                comparison(group, component_id, saved["role"], saved["global_n_extrema_mm"],
                           saved["geometry_limit"])
            comparison(group, axis_id, "complete_installed_stack", axes[axis_id]["global_n_extrema_mm"],
                       "Frozen five-component installed planning union", axes[axis_id]["controlling_max_component_ids"])
        hardware_extrema = [axes[axis_id]["global_n_extrema_mm"] for axis_id in group["associated_axis_ids"]]
        extents = list(hardware_extrema)
        body_supported = True
        if group["kind"] == "connector_host":
            body_extrema = body_projections[group["connector"]]["global_n_extrema_mm"]
            if body_extrema is None:
                body_supported = False
            else:
                extents.append(body_extrema)
        union = [min(value[0] for value in extents), max(value[1] for value in extents)] if body_supported else None
        controlling_min, controlling_max = [], []
        if union is not None:
            for axis_id in group["associated_axis_ids"]:
                if abs(axes[axis_id]["global_n_extrema_mm"][0] - union[0]) < 1e-9:
                    controlling_min.extend(axes[axis_id]["controlling_min_component_ids"])
                if abs(axes[axis_id]["global_n_extrema_mm"][1] - union[1]) < 1e-9:
                    controlling_max.extend(axes[axis_id]["controlling_max_component_ids"])
            if group["kind"] == "connector_host":
                if abs(body_extrema[0] - union[0]) < 1e-9:
                    controlling_min.append(f"{group['connector']}/outer_geometry")
                if abs(body_extrema[1] - union[1]) < 1e-9:
                    controlling_max.append(f"{group['connector']}/outer_geometry")
        group["controlling_min_component_ids"] = sorted(set(controlling_min))
        group["controlling_max_component_ids"] = sorted(set(controlling_max))
        group["complete_permanent_comparison"] = comparison(group, key, "complete_permanent_station",
                                                             union, "Whole connector and all associated installed stacks; retained pair includes both complete stacks",
                                                             group["controlling_max_component_ids"])
        group["new_internal_knee_axes_inherited"] = sorted(set(group["associated_axis_ids"]) & set(internal))
        group_rows.append(group)
        if group["datum"]["origin_xyz_mm"] is None:
            unsupported.append({"group_id": key, "host": group["host"], "reason": group["datum"]["reason"]})

    screw_rows = []
    screw_connections = {row["axis_id"]: row for row in model["connections"] if row["kind"] == "panel_screw"}
    for screw in ordinary["screws"]:
        axis_id = screw["axis_id"]
        connection = screw_connections[axis_id]
        host = connection["source_record"]["receiver_member"]
        geometry = screw["geometry"]
        key = f"screw/{axis_id}/receiver/{host}"
        anchor, anchor_source, reason = screw_anchor(host, axis_id, geometry)
        if reason:
            datum = {"datum_id": key, "host": host, "anchor_xyz_mm": None,
                     "anchor_sources": [anchor_source], "status": "unsupported",
                     "origin_xyz_mm": None, "reason": reason,
                     "supporting_plane_fallback_used": False, **FALSE_CLAIMS}
        else:
            datum = front_datum(key, host, anchor, [axis_id], [anchor_source])
        datums.append(datum)
        group = {"group_id": key, "kind": "screw_receiver_diagnostic", "host": host,
                 "connector": None, "datum": datum}
        row = comparison(group, screw["component_id"], "purchased_screw_occupancy",
                         screw["global_n_extrema_mm"], screw["geometry_limit"], [screw["component_id"]])
        screw_rows.append({"axis_id": axis_id, "receiver": host, "datum": datum, "comparison": row,
                           "panel_member": connection["source_record"]["panel_member"],
                           "panel_source_datum_diagnostic_retained_in": reference("ordinary"),
                           "complete_product_head_profile_available": False})
        if datum["origin_xyz_mm"] is None:
            unsupported.append({"group_id": key, "host": host, "reason": datum["reason"]})

    for body, projection in body_projections.items():
        if projection["global_n_extrema_mm"] is None:
            unsupported.append({"body": body, "reason": projection["basis"]})
    for axis_id in internal:
        inherited = [group for group in group_rows if axis_id in group["associated_axis_ids"]]
        if {group["host"] for group in inherited} != ({"base_post_outer_left", "base_side_left"}
                                                      if "left" in axis_id else {"base_post_outer_right", "base_side_right"}):
            raise ValueError(f"Internal knee axis does not inherit both existing host stations: {axis_id}")
    if len(screw_rows) != 66 or len(body_projections) != 24:
        raise ValueError("Expected all66 screws and all24 connector projections")
    complete = [row for row in comparisons if row["role"] in {"complete_permanent_station", "purchased_screw_occupancy"}]
    exceptions = [row for row in complete if row["dimensioned_conditional_excess_mm"] is not None
                  and row["dimensioned_conditional_excess_mm"] > 0.0]
    available = [row for row in complete if row["n_max_mm"] is not None]
    maximum = max((row["n_max_mm"] for row in available), default=None)
    counts = {**ordinary["counts"], "comparison_rows": len(comparisons),
              "connector_host_groups": sum(group["kind"] == "connector_host" for group in group_rows),
              "retained_receiver_pair_groups": len(retained_pairs),
              "retained_host_datums": sum(group["kind"] == "retained_pair_host" for group in group_rows),
              "screw_receiver_diagnostics": len(screw_rows), "proposed_datums": len(datums),
              "supported_finite_front_datums": sum(datum["origin_xyz_mm"] is not None for datum in datums),
              "unsupported_front_datums": sum(datum["origin_xyz_mm"] is None for datum in datums)}
    category_summary = {}
    for category, kind in (("candidate", "connector_host"), ("retained", "retained_pair_host"),
                           ("screw", "screw_receiver_diagnostic")):
        rows = [row for row in comparisons if row["group_kind"] == kind]
        whole = [row for row in complete if row["group_kind"] == kind]
        category_summary[category] = {
            "datum_count": len(whole),
            "finite_front_datums": sum(row["datum_status"] == "proposed_finite_front_face_datum" for row in whole),
            "null_front_datums": sum(row["datum_status"] != "proposed_finite_front_face_datum" for row in whole),
            "comparison_rows": len(rows),
            "numeric_comparison_rows": sum(row["n_max_mm"] is not None for row in rows),
            "null_comparison_rows": sum(row["n_max_mm"] is None for row in rows),
            "all_dimensioned_excess_rows": sum(row["dimensioned_conditional_excess_mm"] is not None
                                               and row["dimensioned_conditional_excess_mm"] > 0.0 for row in rows),
            "complete_station_or_screw_excess_rows": sum(row["dimensioned_conditional_excess_mm"] is not None
                                                          and row["dimensioned_conditional_excess_mm"] > 0.0 for row in whole),
        }
    criterion = next(row for row in criteria["additional_candidate_obligations"] if row["id"] == "ordinary_n_envelope")
    result = {
        "schema": "proposed_station_front_n_envelope/v1", "status": "proposed_local_datums_not_adopted",
        "definition": {"canonical_n_global_xyz": list(N), "reference_upper_n_mm": LIMIT,
                       "criterion": criterion, "criterion_source": reference("criteria"),
                       "scope_trace": [reference("plan"), reference("decisions")],
                       "convention": "One connector/nonblock-host group datum: arithmetic mean of current receiver-bearing interval midpoints, traced along -N to the first finite front exterior polygon exit. Both +/-N finite oriented material crossing sequences must locate the anchor inside the receiver reference material; no convex/all-plane halfspace substitute. A retained pair has one mean datum for each of its two hosts. Four new knee bolts inherit both existing spine host datums. Every complete connector and all associated installed stacks are reported at every linked host datum. No origin is moved to reduce an excess.",
                       "own_bore_policy": "Only a matched finite bore containing the anchor may have its own circular endpoint inner wire filled for the external datum reference. Other holes remain. This is not contact, bearing or delivered-part proof.",
                       "screw_policy": "All66 purchased nominal screw cylinders receive separate timber-receiver local front-face diagnostics. Anchors use matched finite receiver-bore intervals verified against the current screw axis, or finite oriented receiver-axis material intervals when unmatched; no convex clipping. Earlier panel source-frame diagnostics remain preserved in the ordinary packet. Complete purchased screw-head/profile remains unavailable.",
                       "temporary_operations": "Separate assembly/removal scope, not adopted installed N exceptions",
                       "frontward_bound_adopted": False},
        "counts": counts, "category_summary": category_summary,
        "groups": group_rows, "datum_candidates": datums,
        "body_projections": list(body_projections.values()), "screws": screw_rows,
        "comparisons": comparisons, "dimensioned_conditional_exception_candidates": exceptions,
        "unsupported_pairs_or_bodies": unsupported, "exterior_signature_reuse": exterior_reuse,
        "inherited_inventory_uncertainties": ordinary["unsupported_facts"],
        "global_installed_inventory_reference": reference("ordinary"),
        "controlling_complete_n_max_mm": maximum,
        "controlling_complete_rows": [row for row in available if abs(row["n_max_mm"] - maximum) < 1e-9],
        "no_retained_station_exemption_applied": True,
        "source_sha256": before, "producer_sha256": producer_sha,
        "tests_run": False, "native_or_CAD_or_frame_run": False, **FALSE_CLAIMS,
    }
    after = authenticate(expected)
    if after != before or sha(producer) != producer_sha:
        raise ValueError("Pinned source or producer bytes changed during calculation")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n", encoding="utf-8")
    (output / "producer.py.snapshot").write_bytes(producer_bytes)
    (output / "envelope.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    with (output / "comparisons.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows({**row, "controlling_component_ids": json.dumps(row["controlling_component_ids"])} for row in comparisons)
    final = authenticate(expected)
    if final != before or sha(producer) != producer_sha:
        raise ValueError("Pinned source or producer bytes changed while writing output")
    receipt = {
        "schema": "proposed_station_front_n_envelope_receipt/v1",
        "output": output.relative_to(ROOT).as_posix(), "counts": counts,
        "category_summary": category_summary,
        "producer": {"path": producer.relative_to(ROOT).as_posix(), "sha256": producer_sha},
        "source_sha256_before": before, "source_sha256_after": final,
        "source_pins_unchanged": before == final,
        "output_sha256": {name: sha(output / name) for name in
                          ("envelope.json", "comparisons.csv", "producer.py.snapshot", ".gitignore")},
        "unsupported_pairs_or_bodies": unsupported,
        "dimensioned_conditional_exception_candidate_count": len(exceptions),
        "tests_run": False, "native_or_CAD_or_frame_run": False, **FALSE_CLAIMS,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = build(args.output)
    print(json.dumps({"output": receipt["output"], "counts": receipt["counts"],
                      "output_sha256": receipt["output_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
