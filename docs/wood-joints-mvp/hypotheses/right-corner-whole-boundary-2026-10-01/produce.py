#!/usr/bin/env python3
"""Recover the complete modeled right five-body boundary from frozen responses."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RIGHT = HERE.parent / "right-corner-signed-load-path-2026-10-01/produce.py"
RIGHT_SHA = "13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea"
EXPORT = HERE.parent / "mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py"
EXPORT_SHA = "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8"
MEMBERS = {"base_header", "base_post_outer_right", "base_side_right",
           "knee_outer_right_spine", "knee_outer_right_inner_frame_block"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, expected, name):
    require(sha(path) == expected, "reused method changed")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "method unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(a, b, message, tol=1e-8):
    require(len(a) == len(b) and all(math.isfinite(float(v)) for v in a+b), message)
    require(max(abs(x-y) for x, y in zip(a, b, strict=True)) <= tol, message)


def plus(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def transport(method, force, moment, datum):
    return force + plus(moment, method.cross(datum, force))


def grouped_inventory(model):
    grouped = {}
    for index, raw in enumerate(model["raw_source_carrier_law_inventory_rows"]):
        owner = raw["physical_owner"]
        require(owner["first"] == raw["first_body"]
                and owner["second"] == raw["second_body"], "source owner/body differs")
        if owner["first"] not in MEMBERS and owner["second"] not in MEMBERS:
            continue
        name = raw["name"]
        row = grouped.setdefault(name, {"source_connection_name": name,
                                       "owner": owner, "source_indices": []})
        require(row["owner"] == owner, "scalar group has different endpoint owner")
        row["source_indices"].append(index)
    require(grouped, "empty right boundary")
    return [grouped[name] for name in sorted(grouped)]


def build():
    right = load(RIGHT, RIGHT_SHA, "right_boundary_source")
    # This reviewed join authenticates the case/revision, decks, DATs, responses,
    # terminal records, every all-body gate, geometry and the six selected bolts.
    source = right.produce()
    method = load(EXPORT, EXPORT_SHA, "right_boundary_export_method")
    require((method.BALANCE_FORCE_TOL_N, method.BALANCE_MOMENT_TOL_NMM) == (0.1, 2.0),
            "source body gates changed")
    close(transport(method, [2., 3., 4.], [5., 6., 7.], [10., 20., 30.]),
          [2., 3., 4., -5., 26., -3.], "wrench transport oracle failed")
    cases, states, fingerprints = {}, [], []
    for case, files in source["case_sources"].items():
        model = json.loads((ROOT/files["model"]["path"]).read_text())
        response = json.loads((ROOT/files["response"]["path"]).read_text())
        audit = json.loads((ROOT/files["all_body_audit"]["path"]).read_text())
        require(audit["physical_tolerances_N_Nmm"] == [0.1, 2.0], "all-body limits changed")
        inventory = grouped_inventory(model)
        datums = {body: [(a+b)/2 for a, b in zip(
            model["body_geometry"][body]["geometry_record"]["start"],
            model["body_geometry"][body]["geometry_record"]["end"], strict=True)]
            for body in sorted(MEMBERS)}
        fingerprints.append([(r["source_connection_name"], r["owner"], r["source_indices"])
                             for r in inventory])
        cases[case] = {"source_files": files, "interface_count": len(inventory),
                       "scalar_source_count": sum(len(r["source_indices"]) for r in inventory),
                       "inventory": inventory, "reporting_datums_xyz_mm": datums}
        for index, saved in enumerate(response["increments"]):
            # The reused floor adapter adds source-basis provenance to released
            # zero actions in memory. Preserve all source records on disk.
            inc = copy.deepcopy(saved)
            rows = method.response_interfaces(inc, inventory)
            require(set(rows) == {r["source_connection_name"] for r in inventory},
                    "incomplete or extra interface coverage")
            for binding in inventory:
                method.validate_response_owner(rows[binding["source_connection_name"]],
                                               binding, binding["source_connection_name"])
            balances = method.member_balance(model, {"corner_body_names": sorted(MEMBERS)},
                                             {"descriptor_midpoint_datums_mm": datums},
                                             rows, inc["load_factor"])
            radii = {body: {"force": [0., 0., 0.], "moment": [0., 0., 0.]}
                     for body in MEMBERS}
            internal, boundary, ports = [0.]*6, [0.]*6, defaultdict(lambda: {
                "wrench_about_origin": [0.]*6, "connection_names": []})
            internal_count = boundary_count = 0
            active_floor = released_floor = 0
            for name, row in sorted(rows.items()):
                inside = row["first"] in MEMBERS and row["second"] in MEMBERS
                internal_count += int(inside)
                boundary_count += int(not inside)
                active_floor += int(row.get("floor_tangent_state") == "active_selected_floor_tangent_reaction")
                released_floor += int(row.get("floor_tangent_state") == "released_inactive_floor_tangent_zero_action")
                pair = [0.]*6
                radius = row["force_rounding_radius_xyz_n"]
                require(len(radius) == 3 and all(math.isfinite(v) and v >= 0 for v in radius),
                        "invalid endpoint force radius")
                for side in ("first", "second"):
                    body = row[side]
                    if body not in MEMBERS:
                        continue
                    point = row.get(side+"_point", row["point"])
                    force = row["force_on_"+side+"_xyz_n"]
                    wrench = transport(method, force, [0.]*3, point)
                    pair = plus(pair, wrench)
                    radii[body]["force"] = plus(radii[body]["force"], radius)
                    radii[body]["moment"] = plus(radii[body]["moment"],
                        method.cross_interval_radius(method.sub(point, datums[body]), radius))
                    if not inside:
                        other = row["second" if side == "first" else "first"]
                        port = ports[(body, other, row.get("role", "assumed_no_slip_floor"))]
                        port["wrench_about_origin"] = plus(port["wrench_about_origin"], wrench)
                        port["connection_names"].append(name)
                if inside:
                    close(pair[:3], [0.]*3, "internal force cancellation failed")
                    close(pair[3:], [0.]*3, "internal couple cancellation failed", 1e-6)
                    internal = plus(internal, pair)
                else:
                    boundary = plus(boundary, pair)
            loads, transported_residuals = [0.]*6, [0.]*6
            for body, balance in balances.items():
                original = audit["increments"][index]["body_equilibrium"][body]
                close(datums[body], original["reference_xyz_mm"], "source reporting datum differs")
                require(balance["raw_balance_passed"] and balance["rounding_interval_balance_passed"],
                        "source physical body-balance limits failed")
                for kind, suffix, tolerance in (("force", "xyz_n", 1e-8),
                                                 ("moment", "xyz_nmm", 1e-6)):
                    close(balance["combined_residual_wrench"][kind+"_"+suffix],
                          original[kind+"_residual_"+suffix], "all-body residual differs", tolerance)
                    close(radii[body][kind], original[kind+"_rounding_radius_"+suffix],
                          "all-body force precision differs", tolerance)
                balance["source_force_radius_N"] = radii[body]["force"]
                balance["source_moment_radius_Nmm"] = radii[body]["moment"]
                external = balance["external_load_wrench"]
                residual = balance["combined_residual_wrench"]
                loads = plus(loads, transport(method, external["force_xyz_n"],
                                             external["moment_xyz_nmm"], datums[body]))
                transported_residuals = plus(transported_residuals,
                    transport(method, residual["force_xyz_n"], residual["moment_xyz_nmm"], datums[body]))
            combined = plus(plus(internal, boundary), loads)
            close(combined[:3], transported_residuals[:3], "assembly force reconstruction differs")
            close(combined[3:], transported_residuals[3:], "assembly couple reconstruction differs", 1e-6)
            states.append({"case_id": case, "increment_index": index, "load_factor": inc["load_factor"],
                           "internal_interface_count": internal_count, "boundary_interface_count": boundary_count,
                           "active_floor_tangent_groups": active_floor, "released_floor_tangent_groups": released_floor,
                           "member_balances": balances, "internal_cancellation_wrench": internal,
                           "boundary_wrench": boundary, "external_load_wrench": loads,
                           "combined_residual_wrench": combined,
                           "transported_source_body_residuals": transported_residuals,
                           "boundary_ports": [{"body": k[0], "other_receiver": k[1], "role": k[2], **v}
                                              for k, v in sorted(ports.items())],
                           "interface_actions": rows})
    require(len(states) == 21 and all(f == fingerprints[0] for f in fingerprints),
            "case topology or state coverage differs")
    return {"status": "PASS_RIGHT_FIVE_BODY_BOUNDARY_RECONSTRUCTION_ONLY",
            "candidate": source["candidate"], "revision": source["revision"],
            "producer_sha256": sha(Path(__file__)), "reused_right_join_sha256": RIGHT_SHA,
            "reused_export_helper_sha256": EXPORT_SHA, "cases": cases, "members": sorted(MEMBERS),
            "common_datum_xyz_mm": [0., 0., 0.], "state_count": len(states), "states": states,
            "limits": ["Three frozen conditional rear responses; no new gravity/event history or six-case envelope.",
                       "Modeled endpoint point forces only; transported couples are not bolt internal bending.",
                       "Source body gates stay 0.1 N / 2 Nmm; assembly sums are bookkeeping, not new physical gates.",
                       "Arithmetic matching limits are 1e-8 N / 1e-6 Nmm, not expanded response tolerances.",
                       "Complete source interface coverage does not establish local stress, finished-section strength or stiffness.",
                       "No resistance, criterion pass, native solve, geometry edit, joint acceptance or fabrication release."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(build(), indent=2, allow_nan=False))
