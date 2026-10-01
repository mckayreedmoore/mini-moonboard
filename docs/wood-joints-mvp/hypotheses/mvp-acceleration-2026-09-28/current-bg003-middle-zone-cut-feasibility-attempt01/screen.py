#!/usr/bin/env python3
"""Reproduce the bounded BG003 middle-zone cut feasibility screen."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DEMAND_REL = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json"
)
GEOMETRY_REL = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-knee-three-member-profile-attempt01/query.json"
)
EXPECTED_DEMAND_SHA256 = "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce"
EXPECTED_GEOMETRY_SHA256 = "5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854"
OUTER_SPINE = "knee_outer_left_spine"
OUTER_BLOCK = "knee_outer_left_inner_frame_block"
MIDDLE = "base_side_left"
EXPECTED_PLANES = {
    "knee_outer_left_side_1": ("plane-37", "plane-38"),
    "knee_outer_left_side_2": ("plane-39", "plane-40"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def angle_deg(a: list[float], b: list[float]) -> float:
    cosine = sum(x * y for x, y in zip(a, b)) / (norm(a) * norm(b))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def find_action(bolt: dict, role: str, suffix: str | None = None) -> dict:
    found = [
        a for a in bolt["actions"]
        if a["role"] == role and (suffix is None or a["source_connection_name"].endswith(suffix))
    ]
    if len(found) != 1:
        raise ValueError(f"expected one {role} {suffix!r} action; got {len(found)}")
    return found[0]


def outer_action_vector(action: dict, expected_body: str) -> list[float]:
    if action["first"] == expected_body:
        return [float(x) for x in action["force_on_first_xyz_n"]]
    if action["second"] == expected_body:
        return [float(x) for x in action["force_on_second_xyz_n"]]
    raise ValueError(f"{expected_body} is not an endpoint of {action['source_connection_name']}")


def member_interval(query: dict, axis_id: str, member_id: str) -> list[float]:
    rows = query["modeled_receiver_intervals_and_source_proposed_grains"][axis_id]
    found = [r for r in rows if r["member_id"] == member_id]
    if len(found) != 1:
        raise ValueError(f"expected one {member_id} interval for {axis_id}; got {len(found)}")
    return [float(x) for x in found[0]["interval_from_underhead_mm"]]


def main() -> None:
    demand_path = ROOT / DEMAND_REL
    geometry_path = ROOT / GEOMETRY_REL
    demand_sha = sha256(demand_path)
    geometry_sha = sha256(geometry_path)
    if demand_sha != EXPECTED_DEMAND_SHA256:
        raise ValueError(f"A1 corner report hash changed: {demand_sha}")
    if geometry_sha != EXPECTED_GEOMETRY_SHA256:
        raise ValueError(f"BG003 geometry query hash changed: {geometry_sha}")

    demand = json.loads(demand_path.read_text())
    geometry = json.loads(geometry_path.read_text())
    if demand["case_id"] != "a1-rear" or demand["status"] != "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY":
        raise ValueError("wrong case or non-passing conditional demand report")
    if demand["response_audit_final_load_factor"] != 1.0:
        raise ValueError("this screen is bound to the final full-load increment")
    if geometry["geometry_revision_id"] != demand["geometry_revision_id"]:
        raise ValueError("geometry revision mismatch")

    increments = [i for i in demand["increments"] if float(i["load_factor"]) == 1.0]
    if len(increments) != 1:
        raise ValueError(f"expected one final full-load increment, got {len(increments)}")
    increment = increments[0]
    group = increment["primary_physical_bolt_groups"]["BG003"]
    bolts_by_id = {b["axis_id"]: b for b in group["bolts"]}
    if set(bolts_by_id) != set(EXPECTED_PLANES):
        raise ValueError("BG003 bolt set changed")

    results = []
    for axis_id, plane_suffixes in EXPECTED_PLANES.items():
        bolt = bolts_by_id[axis_id]
        tie = find_action(bolt, "physical_bolt_outer_seat_tension")
        tie_first = [float(x) for x in tie["force_on_first_xyz_n"]]
        tie_second = [float(x) for x in tie["force_on_second_xyz_n"]]
        if abs(tie_first[0] + tie_second[0]) > 1e-9 or norm(tie_first[1:]) > 1e-9:
            raise ValueError(f"outer-seat tie is not a pure, balanced bolt-axis action: {axis_id}")

        plane_actions = []
        outer_vectors = []
        for suffix, outer_body in zip(plane_suffixes, (OUTER_SPINE, OUTER_BLOCK)):
            action = find_action(bolt, "candidate_bolt_lateral_plane", suffix)
            v = outer_action_vector(action, outer_body)
            if abs(v[0]) > 1e-9:
                raise ValueError(f"lateral action has bolt-axis component: {axis_id}/{suffix}")
            plane_actions.append(action)
            outer_vectors.append(v[1:])

        # The two interface actions and reported middle-body resultant must close.
        expected_middle = [0.0, -(outer_vectors[0][0] + outer_vectors[1][0]), -(outer_vectors[0][1] + outer_vectors[1][1])]
        actual_middle = bolt["physical_member_wrenches_at_axis_datum"][MIDDLE]["force_xyz_n"]
        if max(abs(a - b) for a, b in zip(expected_middle, actual_middle)) > 1e-8:
            raise ValueError(f"middle-member force does not close to the two plane actions: {axis_id}")

        interval = member_interval(geometry, axis_id, MIDDLE)
        thickness = interval[1] - interval[0]
        half = thickness / 2.0
        if abs(thickness - 88.9) > 1e-8:
            raise ValueError(f"unexpected modeled middle thickness for {axis_id}: {thickness}")

        vectors3 = [[0.0, *v] for v in outer_vectors]
        magnitudes = [norm(v) for v in vectors3]
        results.append(
            {
                "axis_id": axis_id,
                "lateral_plane_source_rows": [a["source_connection_name"] for a in plane_actions],
                "outer_member_actions_xyz_N": {
                    OUTER_SPINE: vectors3[0],
                    OUTER_BLOCK: vectors3[1],
                },
                "outer_plane_resultants_N": magnitudes,
                "larger_to_smaller_resultant_ratio": max(magnitudes) / min(magnitudes),
                "angle_between_outer_action_vectors_deg": angle_deg(vectors3[0], vectors3[1]),
                "middle_member_net_force_xyz_N": [float(x) for x in actual_middle],
                "outer_seat_tension_N": abs(tie_first[0]),
                "modeled_middle_interval_from_underhead_mm": interval,
                "modeled_middle_thickness_mm": thickness,
                "hypothetical_nonoverlapping_half_zone_each_mm": half,
                "half_zones_touch_at_center_without_geometric_overlap": True,
                "zero_cut_moment_condition": "for one-sided opposite bearing resultant B=-V distributed at centroid sbar>0 into the half-zone, |M_center|=|V|*sbar; the plane force has no applied couple, so geometry alone cannot make M_center=0",
                "moment_coefficient_Nmm_per_mm_centroid_offset": magnitudes,
            }
        )

    out = {
        "schema": "current_bg003_middle_zone_cut_feasibility_screen/v1",
        "status": "GEOMETRIC_PARTITION_DOES_NOT_ESTABLISH_STATIC_ZERO_CUT_OR_LOWER_BOUND",
        "scope": "A1-rear, final full-load factor 1.0, two BG003 physical bolts; feasibility of assigning the one 88.9 mm continuous middle receiver to two 44.45 mm bearing zones with zero transverse shear and moment at the center cut.",
        "source_pins": {
            DEMAND_REL: demand_sha,
            GEOMETRY_REL: geometry_sha,
        },
        "candidate_case": demand["case_id"],
        "geometry_revision_id": demand["geometry_revision_id"],
        "full_load_factor": 1.0,
        "middle_member": MIDDLE,
        "bolt_axis_global_unit": [1.0, 0.0, 0.0],
        "BG003_bolts": results,
        "method_finding": {
            "geometric_nonoverlap": "the two nominal half-thickness intervals abut at the midplane; they are not separate pieces of wood and do not establish independent dowel-bearing stress zones; the NDS three-member route uses the full 88.9 mm middle-member bearing length as one main member",
            "bearing_zone_overlap": "the modeled bore/profile does not delimit the actual bearing field to either assigned half; nonoverlap is an assumed stress distribution, not a geometry result",
            "bolt_continuity": "one through-bolt crosses both shear planes and the midplane; a zero V/M center boundary is not supplied by the connection geometry",
            "outer_plane_state": "A1 actions are unequal and non-collinear on each bolt; the 2026 TR-12 two-ply simplification is scoped to equal-thickness plies in contact receiving the same load from the same direction through a common element",
            "axial_action": "nonzero axial tie is simultaneous and transmitted through the same bolt; a lateral-only half-zone check would not establish combined bolt tension and bending resistance",
            "lower_bound": "not established; no statically admissible fastener/contact stress field, local yield envelope, or source-authorized interaction rule is provided by the half-thickness geometry or available output",
            "minimum_to_pursue": "a validated three-member model/method that resolves or bounds the dowel bearing distribution and bolt shear/moment along the full 88.9 mm middle length, enforces both actual plane force vectors and axial tie concurrently, and checks the same bolt's combined section resistance; also verify actual bolt/thread section and material bearing/yield properties before design use",
        },
        "source_authority": {
            "nds_2024_chapter_12": "prior source-bound local packet establishes NDS-2024 §§12.3.1, 12.3.5.4, 12.3.8 applicability: symmetric three-member yield path; shorter side length for unequal side geometry; §12.3.8 multiple shear applies to four or more members. It does not furnish this unequal non-collinear three-member load interaction.",
            "nds_2018_commentary_historical_only": "C12.3.8 says the asymmetric three-member method assumes equivalent load to each side; other load distributions may need more complex analysis. It is not substituted for current NDS-2024.",
            "tr12_2026": "§1.2 describes lateral yield equations for single-fastener connection values; §1.6 allows the two-ply simplification only when same-thickness plies in contact receive the same load from the same direction through a common element. Neither passage licenses splitting one continuous middle member into independent half-depth zones under the recorded unequal-vector state.",
        },
        "scope_limits": {
            "capacity_or_dcr": False,
            "independent_plane_capacity_sum": False,
            "actual_bearing_distribution_recovered": False,
            "zero_center_shear_moment_proven": False,
            "native_run_or_geometry_change": False,
            "joint_acceptance": False,
        },
    }
    (HERE / "screen.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": out["status"], "output": str(HERE / "screen.json"), "source_pins": out["source_pins"]}, indent=2))


if __name__ == "__main__":
    main()
