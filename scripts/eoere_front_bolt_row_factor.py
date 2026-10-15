"""Classify the current isolated front pairs under the NDS staggered-row rule.

One bolt per unmerged load-aligned row needs no group-action reduction for
its lateral component. Complete geometry, eccentric joint resistance and
physical force sharing remain separate. No frame or geometry is changed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts import eoere_front_bolt_group_scope as prior

current = prior.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
GROUP = {"path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/current-front-bolt-group-scope-attempt03.json",
         "sha256": "9c8e9a693ba20c93b81b66babd872ed98300a5057091d0647fc967a1498f8c27"}


def vector(value):
    a = np.asarray(value, dtype=float)
    current.require(a.shape == (3,) and np.isfinite(a).all(), "finite three-vector required")
    return a


def row_classification(delta, lateral_force, shaft_axis):
    """NDS11.3.6.2's strict quarter-distance rule for an isolated pair."""
    delta, force, axis = vector(delta), vector(lateral_force), prior.unit(shaft_axis)
    current.require(np.linalg.norm(delta) > 1e-8 and abs(delta @ axis) < 1e-8,
                    "distinct pair in one bearing plane required")
    magnitude = float(np.linalg.norm(force))
    current.require(abs(force @ axis) < 1e-8*max(magnitude, 1.), "lateral force perpendicular to shaft required")
    if magnitude < 1e-10:
        return {"status": "undefined_zero_lateral_resultant", "component_Cg": None,
                "load_direction_xyz": None, "fasteners_per_Cg_row": None}
    direction = force/magnitude
    along = abs(float(delta @ direction))
    across = float(np.linalg.norm(delta-(delta @ direction)*direction))
    threshold = along/4.
    merge = across < threshold
    return {"status": "merged_two_fastener_row_requires_EA" if merge else "two_unmerged_single_fastener_rows",
            "load_direction_xyz": direction.tolist(), "parallel_to_load_offset_mm": along,
            "between_load_aligned_rows_mm": across, "quarter_parallel_offset_mm": threshold,
            "unmerged_row_margin_mm": across-threshold,
            "strict_quarter_rule_merges_rows": merge, "fasteners_per_Cg_row": [2] if merge else [1, 1],
            "component_Cg": None if merge else 1., "complete_joint_resistance": None}


def isolated_pair(shafts, host_names, expected_ids):
    """Refuse omitted shafts that connect these same two wood receivers."""
    common = [s for s in shafts
              if set(host_names) <= {v["host"] for v in s["surfaces"] if v["kind"] == "wood"}]
    found = [s["axis_id"] for s in common]
    current.require(len(host_names) == len(set(host_names)) == 2
                    and len(found) == len(expected_ids) == 2 and set(found) == set(expected_ids)
                    and all(len(s["surfaces"]) == 2 for s in common),
                    "complete isolated two-shaft, two-wood connection required")
    return sorted(found)


def member_row_scope(geometry, saved):
    grain, cross = prior.unit(geometry["grain_axis_xyz"]), prior.unit(geometry["cross_grain_axis_xyz"])
    axis = np.cross(grain, cross)
    delta = np.subtract(geometry["own_bearing_midpoints_xyz_mm"][1], geometry["own_bearing_midpoints_xyz_mm"][0])

    def lateral(force):
        f = vector(force)
        return (f @ grain)*grain+(f @ cross)*cross

    group = row_classification(delta, lateral(saved["complete_group_wrench_scope"]["force_xyz_n"]), axis)
    own = [{"axis_id": a["axis_id"], "classification": row_classification(delta, lateral(a["force_xyz_n"]), axis)}
           for a in saved["own_signed_action_scope"]]
    current.require(len(own) == 2 and {a["axis_id"] for a in own} == set(geometry["axis_ids"]),
                    "both original own action directions required")
    consistent = all(r["component_Cg"] == 1. for r in [group, *[a["classification"] for a in own]])
    return {"member": geometry["member"], "axis_ids": geometry["axis_ids"],
            "group_resultant_row_classification": group, "own_direction_classification_sensitivities": own,
            "isolated_lateral_component_Cg": 1. if consistent else None,
            "complete_group_wrench_retained": saved["complete_group_wrench_scope"],
            "complete_Cdelta": None, "complete_joint_resistance": None}


def run():
    cases, pins = prior.intake_source.intake()
    old = current.read(GROUP)
    refs = [GROUP, current.ref(OWN), current.ref(current.ROOT/"tests/test_eoere_front_bolt_row_factor.py")]
    pins = current.join(pins, old["source_sha256"], {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    require = current.require
    require(old["producer"] == current.ref(Path(prior.__file__))
            and old["geometry_revision"] == "eoere-raised-kicker-screws-v1"
            and old["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
            and old["extra_grid"] is False and old["current_bolt_count"] == 100,
            "exact frozen current group evidence required")
    first = cases[0][1]
    require(len(first["source_inputs"]["shafts"]) == 100 and len(first["panel_screw_actions"]) == 66,
            "retained 100-bolt/66-screw design required")
    connections = []
    for side, ids in prior.PAIRS.items():
        hosts = [f"base_floor_{side}", f"base_post_outer_{side}"]
        connections.append({"wood_receivers": hosts,
                            "complete_physical_axis_ids": isolated_pair(first["source_inputs"]["shafts"], hosts, ids)})
    old_cases = {c["case_id"]: c for c in old["cases"]}
    require(len(old_cases) == len(cases) == 6 and len(old["geometry"]) == 4, "complete current group scope required")
    result = []
    for binding, field, data in cases:
        saved = old_cases[binding["case_id"]]
        require(saved["state_id"] == binding["state_id"] and saved["field"] == binding["field"]
                and field["source_inputs"]["shafts"] == first["source_inputs"]["shafts"]
                and len(field["panel_screw_actions"]) == 66, "exact own case and same geometry required")
        rows = []
        for scope in saved["member_pair_scope"]:
            geometry = old["geometry"][scope["geometry_index"]]
            actions = [a for a in data["findings"]["timber"]["wood_surfaces"]
                       if a["receiver"] == geometry["member"] and a["axis_id"] in geometry["axis_ids"]]
            require(prior.action_scope(geometry, actions) == scope["own_signed_action_scope"]
                    and prior.group_wrench_scope(geometry, actions) == scope["complete_group_wrench_scope"],
                    "original current signed action or complete group wrench changed")
            rows.append(member_row_scope(geometry, scope))
        require(len(rows) == 4, "all four member/pair classifications required")
        references = []
        for component in data["findings"]["timber"]["shaft_components"]:
            axis_id = component["axis_id"]
            if axis_id not in {i for ids in prior.PAIRS.values() for i in ids}:
                continue
            receivers = [r for r in rows if axis_id in r["axis_ids"]]
            require(len(receivers) == 2 and component["component"] is not None,
                    "both own receivers and existing lateral component reference required")
            cg = 1. if all(r["isolated_lateral_component_Cg"] == 1. for r in receivers) else None
            raw = component["component"]
            references.append({"axis_id": axis_id, "isolated_lateral_component_Cg": cg,
                               "lateral_demand_n": raw["lateral_demand_n"],
                               "unadjusted_component_reference_n": raw["unadjusted_component_Z_n"],
                               "Cg_only_component_ratio": None if cg is None else raw["V_over_unadjusted_component_Z"]/cg,
                               "complete_Cdelta": None, "complete_joint_reference_n": None})
        require(len(references) == 4, "four own current front reference bindings required")
        result.append({"case_id": binding["case_id"], "state_id": binding["state_id"], "field": binding["field"],
                       "member_pair_rows": rows, "existing_lateral_component_references": references})
    current.verify(pins)
    require(current.sha(OWN) == LOADED_SHA, "loaded row adapter changed")
    classifications = [r for c in result for r in c["member_pair_rows"]]
    all_directions = [r["group_resultant_row_classification"] for r in classifications]
    all_directions.extend(a["classification"] for r in classifications
                          for a in r["own_direction_classification_sensitivities"])
    require(len(classifications) == 24 and len(all_directions) == 72, "complete same-case row-direction coverage required")
    refs = [r for c in result for r in c["existing_lateral_component_references"]]
    return {"schema": "eoere_front_bolt_row_factor/v1", "producer": current.ref(OWN),
            "source_sha256": pins, "all_sources_unchanged": True, "reused_group_audit": GROUP,
            "primary_sources": old["primary_sources"], "connections": connections, "cases": result,
            "geometry_revision": old["geometry_revision"], "hardware_revision": old["hardware_revision"],
            "extra_grid": False, "current_bolt_count": 100, "current_screw_count": 66,
            "all_24_isolated_lateral_row_factors_one": all(r["isolated_lateral_component_Cg"] == 1. for r in classifications),
            "row_direction_count": len(all_directions),
            "minimum_unmerged_margin_over_72_directions_mm": min((r["unmerged_row_margin_mm"] for r in all_directions
                                                                  if "unmerged_row_margin_mm" in r), default=None),
            "maximum_Cg_only_component_ratio": max((r["Cg_only_component_ratio"] for r in refs
                                                   if r["Cg_only_component_ratio"] is not None), default=None),
            "complete_Cdelta": None, "complete_joint_resistance": None, "physical_force_sharing_qualified": False,
            "structural_acceptance": False, "native_or_frame_solve_geometry_change_or_actual_fit": False,
            "release": old["release"],
            "limits": ["NDS11.3.6.2 uses load-aligned rows and merges staggered adjacent rows only when their separation is strictly less than one quarter of the parallel offset. Each current isolated front pair stays as two single-fastener rows for the group direction and both original individual lateral directions.",
                       "NDS11.3.6.1's n=1 factor is identically one, independent of positive EA/slip inputs. No guessed material compliance or fictitious two-fastener aligned row is used.",
                       "Cg=1 is credited only to the isolated front lateral-resultant component. Original forces, free couples, axial actions and physical force sharing are not changed or qualified. No universal group factor for the other 96 shafts is adopted.",
                       "Complete Cdelta, oblique/eccentric joint resistance, local brittle modes, the recorded cardinal row-marker shortfall, physical response and deferred panel/screw behavior remain separate. No complete adjusted capacity or remedy is introduced."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
