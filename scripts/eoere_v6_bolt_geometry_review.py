"""Correct the current bolt checker's geometry and rule-applicability claims.

Read the six issued fields without solving or changing the frame. Reuse the
whole-bearing-interval outer-profile method. Principal-direction components,
conservative markers and unresolved oblique complete joints stay distinct.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import eoere_bolt_geometry_rules as rules
from scripts import eoere_bolt_outer_geometry as outer
from scripts import eoere_v6_analysis as analysis
from scripts import eoere_v6_checks as basis
from scripts.eoere_mixed_stack_yield import affine_surface
from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha
from scripts.thin_bolted_timber_resistance import end_geometry_factor

OWN = Path(__file__).resolve()
SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/retained-frame-bolt-finished-edges-2026-10-01/source-evidence.json"
ORIGINAL = ROOT / "docs/bolted-frame-development/owner-frame-v6/engineering-review.json"
PUBLIC = ROOT / "docs/bolted-frame-development/owner-frame-v6/bolt-geometry-review.json"
OUT = analysis.BASE / "bolt-geometry-review-v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def lateral_endpoints(shaft, surface, action):
    """Reconstruct raw affine lateral pressures, preserving force and couple."""
    require(action["axis_id"] == shaft["axis_id"] and action["host"] == surface["host"]
            and action["surface_interval_mm"] == surface["interval_mm"], "own action/surface binding required")
    axis = np.asarray(shaft["basis"][0], dtype=float)
    lo, hi = surface["interval_mm"]
    length = hi - lo
    force = np.asarray(action["force_on_host_xyz_n"], dtype=float)
    moment = np.asarray(action["moment_on_host_at_point_xyz_nmm"], dtype=float)
    point = np.asarray(action["point_xyz_mm"], dtype=float)
    center = np.asarray(shaft["point"]) + axis * ((lo + hi) / 2)
    require(length > 0 and np.isfinite(force).all() and np.isfinite(moment).all()
            and np.linalg.norm(point - center) < 1e-6, "finite own midpoint wrench required")
    # End-capture axial force is recorded separately; it does not define the
    # direction of the lateral placement-table load.
    axial = float(force @ axis)
    lateral = force - axis * axial
    first = -np.cross(axis, moment)
    q0, q1 = lateral / length - 6 * first / length**2, lateral / length + 6 * first / length**2
    audit = affine_surface({"interval_from_axis_point_mm": [lo, hi],
                            "affine_endpoint_line_density_vectors_n_mm": [q0, q1],
                            "lateral_force_on_host_xyz_n": lateral,
                            "moment_on_host_about_interval_center_xyz_nmm": moment,
                            "host": surface["host"], "kind": "wood", "surface_index": action["surface_index"]}, axis)
    return q0, q1, {"lateral_force_xyz_N": lateral.tolist(), "axial_force_N": axial,
                     "own_free_couple_xyz_Nmm": moment.tolist(),
                     "force_reconstruction_error_N": audit["force_replay_error_n"],
                     "moment_reconstruction_error_Nmm": audit["moment_replay_error_nmm"]}


def occurrence(profile, shaft, surface, action, maximum_row_spacing):
    placement = outer.placement(profile, shaft, surface, end_geometry_factor)
    frame = np.asarray(profile["basis_grain_u_v_xyz"])
    edge_dimension = placement["edge_transverse_dimension"]
    q0, q1, wrench = lateral_endpoints(shaft, surface, action)
    local = [frame @ q for q in (q0, q1)]
    load = rules.classify_affine_load(*[[float(q[0]), float(q[edge_dimension])] for q in local])
    edges = [min(row["minimum_axis_to_outer_edge_mm"] for row in placement["outer_edge_distances"]
                 if row["edge_sign"] == sign) for sign in (-1, 1)]
    wood_lengths = [s["interval_mm"][1] - s["interval_mm"][0] for s in shaft["surfaces"] if s["kind"] == "wood"]
    effective = min(wood_lengths)
    edge = rules.edge_rule(edges, shaft["diameter_mm"], effective, load, maximum_row_spacing)
    ends = []
    for end in placement["grain_end_distances"]:
        category = None
        if not load["reversal"]:
            if load["direction"] == "parallel":
                category = "softwood_parallel_tension" if end["end_sign"] == load["grain_sign"] else "parallel_compression"
            elif load["direction"] == "perpendicular":
                category = "perpendicular"
        square = abs(abs(end["outward_normal_luv"][0]) - 1.) < 1e-7
        result = rules.end_rule(end["minimum_axis_to_end_along_grain_mm"], shaft["diameter_mm"], category, square_end=square)
        ends.append({**end, "rule": result})
    return {"axis_id": shaft["axis_id"], "host": surface["host"],
            "placement": placement, "load_classification": load,
            "raw_affine_endpoint_pressures_on_host_N_per_mm": [q0.tolist(), q1.tolist()],
            "wrench": wrench, "edge_rule": edge, "end_rules": ends,
            "component_status": rules.rollup_status([edge["status"], *[r["rule"]["status"] for r in ends]]),
            "complete_Cdelta": None, "complete_joint_qualified": False}


def group_load(rows):
    loads = [r["load_classification"] for r in rows]
    direction = {r["direction"] for r in loads}
    if len(direction) != 1 or any(r["reversal"] for r in loads):
        return {"direction": "oblique", "reversal": any(r["reversal"] for r in loads),
                "grain_sign": None, "crossgrain_sign": None}
    if next(iter(direction)) not in ("parallel", "perpendicular"):
        return loads[0]
    key = "grain_sign" if loads[0]["direction"] == "parallel" else "crossgrain_sign"
    if len({r[key] for r in loads}) != 1:
        return {"direction": "unresolved", "reversal": True, "grain_sign": None, "crossgrain_sign": None}
    return loads[0]


def compare(out):
    require(not out.exists(), "fresh geometry-review output required")
    require(out.resolve().is_relative_to(ROOT / "fea/generated"), "raw review must stay in ignored generated storage")
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    (out / "rules-snapshot.py").write_bytes(Path(rules.__file__).read_bytes())
    geometry, fields, pins = basis.load()
    original = read(ORIGINAL, pins)
    source = read(SOURCE, pins)
    require(sha(source["source"]["path"]) == source["source"]["sha256"], "pinned NDS source changed")
    active = [OWN, Path(rules.__file__), Path(outer.__file__), ROOT / "scripts/eoere_mixed_stack_yield.py",
              ROOT / "scripts/thin_bolted_timber_resistance.py", SOURCE]
    pins.update({ref(p)["path"]: sha(p) for p in active})
    first = fields[0][3]
    profiles, faces = {}, {}
    for member in first["source_inputs"]["timber_rows"]:
        name = member["name"]
        profiles[name] = outer.outer_profile(member["raw_profile_source"])
        body_ref = geometry["profiles"][name]["finished"]
        require(sha(body_ref["path"]) == body_ref["sha256"], "cached finished body changed")
        pins[body_ref["path"]] = body_ref["sha256"]
        body = cq.Shape.importBrep(str(ROOT / body_ref["path"]))
        faces[name] = outer.confirm_faces(body, profiles[name])
    cases = []
    for _, case, binding, field in fields:
        shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
        require(len(shafts) == 96, "all 96 current physical shafts required")
        actions = {(r["axis_id"], r["host"]): r for r in field["common_shaft_wood_bearing_actions"]}
        require(len(actions) == 112, "all 112 current analytical wood occurrences required")
        rows = []
        groups = {}
        for identity, shaft in shafts.items():
            key = tuple(sorted((s["kind"], s["host"]) for s in shaft["surfaces"]))
            groups.setdefault(key, []).append(identity)
            for surface in shaft["surfaces"]:
                if surface["kind"] != "wood":
                    continue
                host = surface["host"]
                # A cross-grain projection from the old screen is not an
                # authenticated distance between load-aligned NDS rows.
                rows.append(occurrence(profiles[host], shaft, surface, actions[(identity, host)], None))
        require(len(rows) == 112, "complete current wood occurrence census required")
        keyed = {(r["axis_id"], r["host"]): r for r in rows}
        pairs = []
        for receivers, ids in groups.items():
            require(len(ids) in (1, 2), "current complete receiver groups are at most two shafts")
            if len(ids) == 1:
                continue
            for kind, host in receivers:
                if kind != "wood":
                    continue
                a, b = [shafts[i] for i in ids]
                frame = np.asarray(profiles[host]["basis_grain_u_v_xyz"])
                own = [keyed[(i, host)] for i in ids]
                edge_dimension = own[0]["placement"]["edge_transverse_dimension"]
                delta = frame @ (np.asarray(b["point"]) - a["point"])
                gv = [float(delta[0]), float(delta[edge_dimension])]
                load = group_load(own)
                # Row status is established only for a collinear pair aligned
                # with the resolved principal load. A diagonal projection is
                # not declared to be an NDS row or between-row arrangement.
                row_classification = None
                if ((load["direction"] == "parallel" and abs(gv[1]) < 1e-6)
                        or (load["direction"] == "perpendicular" and abs(gv[0]) < 1e-6)):
                    row_classification = "same_row"
                wood_lengths = [s["interval_mm"][1] - s["interval_mm"][0] for s in a["surfaces"] if s["kind"] == "wood"]
                result = rules.pair_rule(gv, max(a["diameter_mm"], b["diameter_mm"]), min(wood_lengths), load,
                                         row_classification=row_classification)
                pairs.append({"host": host, "axes": ids, "rule": result, "load_classification": load,
                              "row_classification": row_classification, "complete_Cdelta": None})
        axis_results = []
        for identity in shafts:
            own = [r for r in rows if r["axis_id"] == identity]
            pair_rules = [p for p in pairs if identity in p["axes"]]
            statuses = [r["edge_rule"]["status"] for r in own]
            statuses += [e["rule"]["status"] for r in own for e in r["end_rules"]]
            statuses += [p["rule"]["status"] for p in pair_rules]
            if any(not faces[r["host"]]["all_profile_planes_present_on_cached_finished_faces"] for r in own):
                statuses.append("unresolved")
            status = rules.rollup_status(statuses)
            axis_results.append({"axis_id": identity, "component_status": status,
                                 "complete_Cdelta": None, "complete_joint_qualified": False})
        cases.append({"case_id": case, "field": binding, "wood_occurrences": rows, "receiver_pairs": pairs,
                      "axes": axis_results, "axis_status_counts": dict(Counter(r["component_status"] for r in axis_results)),
                      "load_class_counts": dict(Counter(r["load_classification"]["direction"] for r in rows))})
    require(len(cases) == 6, "all six independently replayed current cases required")
    for p, digest in pins.items():
        require(sha(p) == digest, "active source changed: " + p)
    result = {"schema": "eoere_current96_bolt_geometry_review/v1", "geometry_revision": original["geometry_revision"],
              "status": "RULE_APPLICABILITY_CORRECTED_COMPLETE_JOINT_UNRESOLVED",
              "physical_geometry": original["physical_geometry"], "analysis_geometry": ref(analysis.GEOMETRY),
              "base_review": ref(ORIGINAL), "load_contract": original["load_contract"],
              "inventory": {"shafts": 96, "wood_occurrences_per_case": 112, "cases": 6, "panels": 6, "screws": 66},
              "source_evidence": ref(SOURCE), "NDS_source": source["source"], "source_sha256": pins,
              "profile_face_confirmations": faces, "cases": cases,
              "legacy_screen_adjusted_indices_unchanged": original["metric_maxima"]["shafts_Cdelta_adjusted"],
              "formal_geometry_Cdelta": None, "complete_joint_qualified": False, "structural_acceptance": False,
              "fabrication_released": False, "climbing_released": False,
              "frame_CAD_or_mechanics_recomputed": False, "historical_pass_transferred": False,
              "qualification_limits": [
                  "The pinned 2024 NDS file contains specification text only, despite its filename; current commentary was not authenticated from that file.",
                  "Principal-direction table checks are components. Oblique-to-grain loading, reversals, sloped ends and unclassified diagonal row arrangements do not receive invented placement rules or a complete Cdelta.",
                  "Actual center separation and principal projections are different measurements. Passing a Euclidean clearance marker does not establish row-rule eligibility.",
                  "Whole-depth outer-profile distances use both bearing endpoints and each hull plane; intervening bores, channels, splitting and complete finished ligaments remain separate.",
                  "The old adjusted bolt indices are retained as conservative screen diagnostics. No capacity, acceptance, or force change follows from correcting their applicability labels.",
                  "All six panels and66 screw springs participate in the frozen response. Actual Hillman stiffness/strength and physical panel-brace qualification remain unresolved."]}
    write_new(out / "full-review.json", result)
    return result


def public_summary(result, full_path):
    value = {k: copy.deepcopy(v) for k, v in result.items() if k not in ("source_sha256", "profile_face_confirmations", "cases")}
    value["full_review"] = ref(full_path)
    value["producer"] = ref(OWN)
    value["rules_producer"] = ref(Path(rules.__file__))
    value["case_summaries"] = [{k: c[k] for k in ("case_id", "field", "axis_status_counts", "load_class_counts")} for c in result["cases"]]
    value["affected_pair_measurements"] = []
    targets = [{"eoere_bolt_067", "eoere_bolt_071"}, {"eoere_bolt_070", "eoere_bolt_074"},
               {"eoere_bolt_068", "eoere_bolt_072"}, {"eoere_bolt_069", "eoere_bolt_073"}]
    for pair in result["cases"][0]["receiver_pairs"]:
        if any(set(pair["axes"]) == target for target in targets):
            value["affected_pair_measurements"].append(pair)
    value["component_findings"] = [
        {"case_id": c["case_id"], "axis_id": r["axis_id"], "host": r["host"],
         "load_classification": r["load_classification"], "edge_rule": r["edge_rule"], "end_rules": r["end_rules"]}
        for c in result["cases"] for r in c["wood_occurrences"] if r["component_status"] != "PASS_COMPONENTS_ONLY"]
    # Keep the repetitive complete occurrences in ignored raw storage; the
    # public record retains every established component failure and the exact
    # affected eight-axis classification, with full source recovery above.
    value["component_findings"] = [r for r in value["component_findings"]
                                   if r["edge_rule"]["status"] == "fail" or any(e["rule"]["status"] == "fail" for e in r["end_rules"])]
    value["upper_pair_statuses"] = [{"case_id": c["case_id"], **r} for c in result["cases"] for r in c["axes"]
                                    if r["axis_id"] in {f"eoere_bolt_{i:03d}" for i in range(67, 75)}]
    value["all_complete_geometry_factors_unresolved"] = True
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--publish", action="store_true", help="write the fresh compact repository review")
    args = parser.parse_args()
    require(not args.publish or not PUBLIC.exists(), "fresh public review required")
    result = compare(args.out.resolve())
    if args.publish:
        write_new(PUBLIC, public_summary(result, args.out.resolve() / "full-review.json"))
    print(json.dumps({"cases": [{"case": c["case_id"], **c["axis_status_counts"]} for c in result["cases"]],
                      "full_review": ref(args.out.resolve() / "full-review.json"),
                      "formal_geometry_Cdelta": None, "complete_joint_qualified": False}))


if __name__ == "__main__":
    main()
