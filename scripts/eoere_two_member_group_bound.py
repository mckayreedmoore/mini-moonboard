"""Bound NDS group-action adjustment for all current ordinary two-member pairs.

For at most two fasteners per row, Eq.11.3-1 has Cg >= 0.5 for every
positive EA/slip input. This is a conservative factor bound on the existing
lateral components, not a complete adjusted resistance or physical demand bound.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from scripts import eoere_current_washer_lands as intake_source
from scripts import eoere_front_bolt_row_factor as front

current = intake_source.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
FRONT = {"path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/current-front-bolt-row-factor-attempt01.json",
         "sha256": "8c0fa0e0f2f307741b9d21d4a221211fec32af6065b02304e2f49d5c69ee7dca"}
EQUATION = {"path": "fea/reinforced_timber_resistance.py",
            "sha256": "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc"}


def ordinary_groups(shafts):
    """Exact two-member pairs; refuse additional common shafts or mixed members."""
    groups = defaultdict(list)
    for shaft in shafts:
        surfaces = shaft["surfaces"]
        if len(surfaces) != 2:
            continue
        key = tuple(sorted((s["kind"], s["host"]) for s in surfaces))
        current.require(len(set(key)) == 2 and tuple(k for k, _ in key) in (("wood", "wood"), ("steel", "wood")),
                        "two distinct ordinary wood/wood or wood/steel bearing members required")
        current.require(all(len(s["interval_mm"]) == 2 and np.isfinite(s["interval_mm"]).all()
                            and s["interval_mm"][1] > s["interval_mm"][0] for s in surfaces),
                        "positive finite own bearing intervals required")
        groups[key].append(shaft)
    output = []
    for members, pair in sorted(groups.items()):
        ids = [s["axis_id"] for s in pair]
        shared = [s["axis_id"] for s in shafts
                  if set(members) <= {(v["kind"], v["host"]) for v in s["surfaces"]}]
        current.require(len(pair) == len(set(ids)) == 2 and len(shared) == 2 and set(shared) == set(ids),
                        "complete isolated pair must contain exactly two physical shafts")
        d = pair[0]["diameter_mm"]
        axis = front.prior.unit(pair[0]["basis"][0])
        current.require(math.isfinite(d) and 6.35 <= d <= 25.4 and d == pair[1]["diameter_mm"]
                        and abs(abs(axis @ front.prior.unit(pair[1]["basis"][0]))-1.) < 1e-9,
                        "same NDS-scope diameter and parallel physical axes required")
        delta = front.vector(pair[1]["point"])-front.vector(pair[0]["point"])
        current.require(np.linalg.norm(delta-(delta @ axis)*axis) > 1e-8,
                        "duplicate physical bore centerlines cannot be counted as two fasteners")
        output.append({"bearing_members": [{"kind": kind, "host": host} for kind, host in members],
                       "physical_axis_ids": sorted(ids), "maximum_fasteners_in_any_Cg_row": 2,
                       "nominal_diameter_mm": d, "Cg_equation_lower_bound": .5,
                       "actual_Cg": None, "complete_joint_resistance": None})
    return output


def component_comparison(record, cg_floor):
    """Compare unchanged lateral demand with a guaranteed group-factor floor."""
    demand, reference = record["lateral_demand_n"], record["unadjusted_component_Z_n"]
    current.require(all(math.isfinite(v) for v in (demand, reference, cg_floor))
                    and demand >= 0. and reference > 0. and 0. < cg_floor <= 1.,
                    "finite nonnegative demand and positive reference/factor required")
    current.require(abs(demand/reference-record["V_over_unadjusted_component_Z"]) < 1e-12,
                    "original lateral component ratio differs")
    ratio = demand/(reference*cg_floor)
    return {"lateral_demand_n": demand, "unadjusted_component_reference_n": reference,
            "Cg_lower_bound_used": cg_floor, "Cg_bound_only_reference_n": reference*cg_floor,
            "Cg_bound_only_reference_index": ratio, "Cg_bound_only_reference_exceeded": ratio > 1.,
            "complete_Cdelta": None, "complete_adjusted_joint_reference_n": None}


def run():
    cases, pins = intake_source.intake()
    qualified_front = current.read(FRONT)
    refs = [FRONT, EQUATION, current.ref(OWN), current.ref(current.ROOT/"tests/test_eoere_two_member_group_bound.py")]
    pins = current.join(pins, qualified_front["source_sha256"], {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    require = current.require
    require(qualified_front["producer"] == current.ref(Path(front.__file__))
            and qualified_front["geometry_revision"] == "eoere-raised-kicker-screws-v1"
            and qualified_front["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
            and qualified_front["extra_grid"] is False
            and qualified_front["all_24_isolated_lateral_row_factors_one"] is True,
            "exact source-qualified current front component factors required")
    equation = intake_source.component.load(EQUATION, "current_two_fastener_group_bound")
    known = [equation.group_factor(2, pitch, main, side, steel_side=steel)
             for pitch in (.25, 2., 10.) for main, side in ((1e5, 1e9), (1e7, 1e7), (1e9, 1e5))
             for steel in (False, True)]
    require(all(.5-1e-9 <= factor <= 1.+1e-9 for factor in known), "existing NDS two-fastener fixtures violate bound")
    first = cases[0][1]
    require(len(first["source_inputs"]["shafts"]) == 100, "current 100-shaft census required")
    groups = ordinary_groups(first["source_inputs"]["shafts"])
    require(len(groups) == 46, "all 46 current ordinary physical pairs required")
    by_axis = {axis: i for i, group in enumerate(groups) for axis in group["physical_axis_ids"]}
    require(len(by_axis) == 92, "92 unique ordinary axes required")
    front_cases = {c["case_id"]: c for c in qualified_front["cases"]}
    result = []
    for binding, field, data in cases:
        require(field["source_inputs"]["shafts"] == first["source_inputs"]["shafts"]
                and len(field["panel_screw_actions"]) == 66, "same 100-bolt geometry and 66-screw policy required")
        fc = front_cases[binding["case_id"]]
        require(fc["state_id"] == binding["state_id"] and fc["field"] == binding["field"], "front own-case join differs")
        front_refs = {r["axis_id"]: r for r in fc["existing_lateral_component_references"]}
        require(len(front_refs) == 4, "four independently classified front components required")
        source = data["findings"]["timber"]["shaft_components"]
        ordinary = [r for r in source if r["component"] is not None]
        excluded = sorted(r["axis_id"] for r in source if r["component"] is None)
        require(len(source) == 100 and len(ordinary) == 92 and len(excluded) == 8
                and {r["axis_id"] for r in ordinary} == set(by_axis), "ordinary versus mixed-stack scope differs")
        rows = []
        for source_row in ordinary:
            axis, raw = source_row["axis_id"], source_row["component"]
            floor = .5
            if axis in front_refs:
                fr = front_refs[axis]
                require(fr["isolated_lateral_component_Cg"] == 1.
                        and fr["lateral_demand_n"] == raw["lateral_demand_n"]
                        and fr["unadjusted_component_reference_n"] == raw["unadjusted_component_Z_n"], "front factor/reference changed")
                floor = 1.
            rows.append({"axis_id": axis, "physical_group_index": by_axis[axis],
                         "factor_role": "source-qualified isolated front component factor" if floor == 1.
                         else "universal NDS n<=2 factor lower bound; actual Cg not assigned",
                         **component_comparison(raw, floor)})
        result.append({"case_id": binding["case_id"], "state_id": binding["state_id"], "field": binding["field"],
                       "ordinary_lateral_components": rows, "excluded_mixed_stack_axis_ids": excluded})
    current.verify(pins)
    require(current.sha(OWN) == LOADED_SHA, "loaded bound adapter changed")
    rows = [{"case_id": c["case_id"], **r} for c in result for r in c["ordinary_lateral_components"]]
    return {"schema": "eoere_two_member_group_bound/v1", "producer": current.ref(OWN),
            "source_sha256": pins, "all_sources_unchanged": True, "reused_front_factor": FRONT,
            "NDS_equation_helper": EQUATION, "primary_sources": qualified_front["primary_sources"],
            "geometry_revision": qualified_front["geometry_revision"], "hardware_revision": qualified_front["hardware_revision"],
            "extra_grid": False, "current_bolt_count": 100, "current_screw_count": 66,
            "physical_ordinary_groups": groups, "cases": result, "comparison_count": len(rows),
            "known_answer_factor_min_max": [min(known), max(known)],
            "n2_bound_proof": {"domain": "0<m<1, 0<R_EA<=1",
                               "Cg": "(1+R)*(1+m*m)/(2*(1+(R-1)*m+m*m))",
                               "Cg_minus_half_numerator": "R*(1+m*m)+(1-R)*m >= 0",
                               "one_minus_Cg_numerator": "(1-R)*(1-m)*(1-m) >= 0",
                               "common_positive_denominator": "2*(1+(R-1)*m+m*m) > 0",
                               "singleton_factor": 1., "two_fastener_factor_lower_bound": .5},
            "maximum_Cg_bound_only_reference_witness": max(rows, key=lambda r: r["Cg_bound_only_reference_index"]),
            "Cg_bound_only_reference_exceedances": [r for r in rows if r["Cg_bound_only_reference_exceeded"]],
            "complete_Cdelta": None, "complete_joint_resistance": None, "finished_member_capacity": None,
            "physical_demand_bounds_established": False, "structural_acceptance": False,
            "native_or_frame_solve_geometry_change_or_actual_fit": False, "release": qualified_front["release"],
            "limits": ["The NDS11.3-1 n=2 algebraic lower bound covers every positive EA/slip input. At most two physical fasteners belong to each isolated ordinary two-member connection; unmerged singleton rows have Cg=1, and a two-fastener row has Cg>=0.5.",
                       "Only existing ordinary lateral-resultant component references are adjusted. Original source forces, free couples, axial duties and current frame response are unchanged; no physical force-sharing law or complete adjusted joint capacity is supplied.",
                       "The eight three-member mixed stacks are excluded and retain their separate vector-statics and resistance limits. Complete Cdelta, local brittle/group transfer, washer/angle/wood interactions and finished-member/response applicability remain unqualified.",
                       "The 0.5 group-factor floor is distinct from the earlier unadopted Cdelta=0.5 sensitivity. Geometry factors are not assigned by this bound. No new design, actual-fit work or panel/screw remedy occurs."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
