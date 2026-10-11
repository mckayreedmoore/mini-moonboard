"""Independent saved-input joins and nominal gravity arithmetic; no solver.

The source producer queries geometry. This checker independently compares its
saved records with the current OFF receipts and integrates the physical loads.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

from scripts import eoere_current_response as current

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)


def loaded_source():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded input checker changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def close(actual, expected, tolerance=1e-7):
    if isinstance(actual, list):
        current.require(len(actual) == len(expected), "arithmetic vector size differs")
        for a, b in zip(actual, expected, strict=True):
            close(a, b, tolerance)
    else:
        current.require(math.isfinite(actual) and abs(actual-expected) <= tolerance,
                        "independent current-input arithmetic differs")


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def verify_load_inventory(case, owners, shafts, auxiliary, source_case):
    """Integrate every authenticated component, including screw/T-nut shares."""
    gravity = 9.80665
    expected = [{"id": "self-weight/"+r["id"], "body": r["id"],
                 "point_xyz_mm": r["center_xyz_mm"], "force_xyz_n": [0., 0., -gravity*r["mass_kg"]]}
                for r in owners if r["kind"] != "shaft"]
    expected += [{"id": "physical-bolt-metal/"+r["id"], "body": "shaft/"+shaft["axis_id"],
                  "point_xyz_mm": r["center_of_mass_xyz_mm"], "force_xyz_n": [0., 0., -gravity*r["mass_kg"]]}
                 for shaft in shafts for r in shaft["metal_roles"]]
    expected += [{"id": "bolt-weight/"+r["id"], "body": r["owner"],
                  "point_xyz_mm": r["center_xyz_mm"], "force_xyz_n": [0., 0., -gravity*r["mass_kg"]]}
                 for r in auxiliary]
    # Climbing surfaces and original accessory/hold scenarios are unchanged.
    expected += [r for r in source_case["loads"] if r["id"].startswith(("accessory/", "climber/"))]
    for key in ("case_id", "accessory_placement", "primary_load_basis", "hold"):
        current.require(case[key] == source_case[key], "original case scenario differs")
    wanted = {r["id"]: r for r in expected}
    observed = {r["id"]: r for r in case["loads"]}
    current.require(len(wanted) == len(expected) and len(observed) == len(case["loads"])
                    and wanted.keys() == observed.keys(), "complete physical load inventory differs")
    for name, row in wanted.items():
        actual = observed[name]
        current.require(actual.keys() == row.keys() and actual["body"] == row["body"],
                        "physical load identity/owner differs: "+name)
        close(actual["point_xyz_mm"], row["point_xyz_mm"])
        close(actual["force_xyz_n"], row["force_xyz_n"])


def check(path, expected_sha):
    loaded_source()
    pointer = {"path": str(path.resolve().relative_to(current.ROOT)), "sha256": expected_sha}
    data = current.read(pointer)
    export = current.require_current_sources(data)
    old, sources, axes, selections, source_pins = current.current_metadata()
    current.require(data["historical_q"] is None and data["old_field"] is None,
                    "historical response cannot supply current loads")
    observed = {r["id"]: r for r in export["finished_body_observations"]}
    current.require(len(observed) == len(sources) == 28, "exact28 current wood/panel observations required")
    for name, source in sources.items():
        current.require(all(observed[name]["source"][k] == source[k] for k in ("id", "path", "sha256", "volume_mm3")),
                        "current OFF finished-solid source differs: " + name)
        close(observed[name]["volume_mm3"], source["volume_mm3"], .01)
    shafts = {r["axis_id"]: r for r in data["shafts"]}
    current.validate_metal_roles(list(shafts.values()), selections)
    prior = {r["axis_id"]: r for r in old["shafts"]}
    spacer_mass = 0.
    for axis in axes:
        name = axis["id"]
        shaft, before, selected = shafts[name], prior[name], selections[name]
        current.require(shaft["source_axis"] == axis, "current selected shaft source differs")
        norm = math.sqrt(sum(x*x for x in axis["direction_xyz"]))
        g = [x/norm for x in axis["direction_xyz"]]
        start = -axis["before_plate_mm"]-axis["hardware_scenario"]["washer_thickness_mm"]
        close(shaft["shaft_interval_mm"], [start, start+selected["selected_underhead_length_mm"]])
        spacer = selected["nut_side_spacer_mm"]
        close(shaft["ends"][0]["pressure_face_s_mm"], before["ends"][0]["pressure_face_s_mm"])
        close(shaft["ends"][1]["pressure_face_s_mm"], before["ends"][1]["pressure_face_s_mm"]+spacer)
        close(shaft["ends"][1]["support_s_mm"], before["ends"][1]["support_s_mm"])
        old_roles = {r["kind"]: r for r in before["metal_roles"]}
        for role in shaft["metal_roles"]:
            kind = role["kind"]
            if kind == "shaft":
                volume = math.pi*axis["diameter_mm"]**2/4*selected["selected_underhead_length_mm"]
                station = start+selected["selected_underhead_length_mm"]/2
                center = [p+v*station for p, v in zip(axis["point_xyz_mm"], g, strict=True)]
            elif kind == "spacer":
                volume = math.pi/4*(19.05**2-10.31875**2)*spacer
                station = axis["grip_mm"]+axis["after_plate_mm"]+axis["hardware_scenario"]["washer_thickness_mm"]+spacer/2
                center = [p+v*station for p, v in zip(axis["point_xyz_mm"], g, strict=True)]
                spacer_mass += volume*7850e-9
            else:
                volume = old_roles[kind]["volume_mm3"]
                center = [p+v*(spacer if kind == "nut" else 0.)
                          for p, v in zip(old_roles[kind]["center_of_mass_xyz_mm"], g, strict=True)]
            close(role["volume_mm3"], volume)
            close(role["mass_kg"], volume*7850e-9)
            close(role["center_of_mass_xyz_mm"], center)
    owner_rows = {r["id"]: r for r in data["physical_owner_gravity_rows"]}
    current.require(len(owner_rows) == 150 and len(data["hillman_rows"]) == 66, "150 owners and66 screws required")
    current.require([r["source_screw_descriptor"] for r in data["hillman_rows"]]
                    == [r["source_screw_descriptor"] for r in old["hillman_rows"]], "current screw descriptors differ")
    current.require(export["auxiliary_metal_gravity_descriptors"] == old["auxiliary_metal_gravity_descriptors"],
                    "current screw/T-nut gravity sources differ")
    prior_cases = {r["case_id"]: r for r in current.read(current.manifest()["references"]["prior_inputs"])["cases"]}
    witnesses = []
    expected_cases = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear", "gravity-only"]
    current.require([r["case_id"] for r in data["cases"]] == expected_cases, "original six-case and gravity roster required")
    for case in data["cases"]:
        verify_load_inventory(case, data["physical_owner_gravity_rows"], data["shafts"],
                              export["auxiliary_metal_gravity_descriptors"], prior_cases[case["case_id"]])
        total_force, total_moment = [0., 0., 0.], [0., 0., 0.]
        current.require(len({r["id"] for r in case["loads"]}) == len(case["loads"]), "duplicate physical load")
        for row in case["loads"]:
            current.require(row["body"] in owner_rows, "foreign current load owner")
            moment = cross(row["point_xyz_mm"], row["force_xyz_n"])
            total_force = [a+b for a, b in zip(total_force, row["force_xyz_n"], strict=True)]
            total_moment = [a+b for a, b in zip(total_moment, moment, strict=True)]
        close(total_force, case["applied_force_xyz_n"])
        close(total_moment, case["applied_moment_about_global_origin_xyz_nmm"], 1e-6)
        current.require(sum(r["body"].startswith("shaft/") for r in case["loads"]) == 508,
                        "each case needs508 separate current own-shaft gravity loads")
        if case["hold"]:
            close(case["hold"]["force_xyz_n"][2], -2*250*.45359237*9.80665)
        selected = copy.deepcopy(data)
        selected["case"] = case
        with current.response_context() as (bridge, _):
            bridge.factory.validate_rows(selected)
        witnesses.append({"case_id": case["case_id"], "physical_loads": len(case["loads"]),
                          "applied_force_xyz_n": total_force, "applied_moment_about_global_origin_xyz_nmm": total_moment})
    pins = current.join(data["source_sha256"], source_pins,
                        {r["path"]: r["sha256"] for r in (pointer, loaded_source())})
    current.verify(pins)
    loaded_source()
    return {"schema": current.REVIEW_SCHEMA, "success": current.REVIEW_SUCCESS,
            "geometry": current.manifest()["references"]["geometry"], "input": pointer,
            "source_sha256": pins, "complete_reference_contact_inventory": True,
            "check_method": "independent saved-source comparison and nominal gravity/load wrench integration; no CAD or solve",
            "source_counts": {"pins": len(pins), "wood_and_panels": 28, "physical_owners": 150,
                              "shafts": 100, "screws": 66, "metal_roles": 508, "spacers": 8},
            "spacer_mass_kg": spacer_mass, "case_witnesses": witnesses,
            "structural_acceptance_established": False, "physical_work_authorized": False,
            "release": current.manifest()["release"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixed = current.load("bridge")
    args.out = current.output_path(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with fixed.reserve(args.out) as output:
        output.write(check(args.inputs, args.inputs_sha256))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
