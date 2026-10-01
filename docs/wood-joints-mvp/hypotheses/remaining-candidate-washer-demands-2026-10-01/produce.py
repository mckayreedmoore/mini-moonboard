#!/usr/bin/env python3
"""Join 54 bolts to three authenticated response families; accept no joint."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
METHODS = {
    "geometry": ("remaining-candidate-washer-seats-2026-10-01/check_support.py",
                 "a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967"),
    "acceptance": (
        "mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/produce.py",
        "3f68d54de9aee14cec66b1d45283a678ef7517b5a0790c0eab9fba267e012565"),
}
FREEZE = PACKETS / "upper-frame-joint-review-2026-09-30/freeze.json"
FREEZE_SHA = "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73"
SUPPORT_SHA = "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3"
GATES = ("mpc_interval_checks_passed", "retained_bilateral_checks_passed",
         "springa_law_checks_passed", "selected_floor_complementarity_passed",
         "inactive_floor_tangent_no_restraint_or_reaction_passed",
         "raw_balance_passed", "rounding_interval_balance_passed")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
SIGN_EPSILON = 1e-9


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_method(name):
    relative, expected = METHODS[name]
    path = PACKETS / relative
    require(sha(path) == expected, f"changed {name} method")
    spec = importlib.util.spec_from_file_location(f"remaining_demand_{name}", path)
    require(spec is not None and spec.loader is not None, "unavailable method")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close_vector(actual, expected, message):
    require(len(actual) == len(expected) == 3, message)
    require(all(math.isfinite(float(a)) and math.isfinite(float(b))
                and math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8)
                for a, b in zip(actual, expected, strict=True)), message)


def checked_tie(tie, binding, component, outer):
    axis_id = outer["head"]["axis_id"]
    name = axis_id + "/outer-seat-axial-tie"
    require(tie["axis_id"] == axis_id
            and tie["role"] == "physical_bolt_outer_seat_tension", "wrong tie identity")
    require(binding["name"] == name and binding["force_law"] == "k * max(q_mm, 0)"
            and binding["physical_owner"] == {k: tie[k] for k in binding["physical_owner"]},
            "wrong source binding/physical ownership")
    require(component["source_row_id"] == binding["source_row_id"]
            and component["source_inventory_row_index"] == binding["source_inventory_row_index"]
            and component["element"] == binding["source_element"]
            and component["intended_source_law"] == "tension_only", "wrong spring component")
    require(tie["source_row_ids"] == [binding["source_row_id"]]
            and len(tie["source_inventory_rows"]) == 1, "wrong tie source inventory")
    inventory = tie["source_inventory_rows"][0]
    require(inventory["source_row_id"] == binding["source_row_id"]
            and inventory["source_inventory_row_index"] == binding["source_inventory_row_index"]
            and inventory["source_connection_name"] == name
            and inventory["intended_law"] == "tension_only", "wrong inventory mapping")
    for gate in ("inside_table_domain_including_rounding", "table_force_interval_intersects_native_rf",
                 "native_endpoint_action_reaction_passed", "numerical_ground_rf_excluded_from_physical_balance"):
        require(component[gate] is True, f"source spring gate failed: {gate}")
    signed = float(tie["axial_along_installation_direction_n"])
    require(math.isfinite(signed) and signed >= -SIGN_EPSILON,
            "negative or nonfinite tension-only tie")
    require(math.isclose(signed, float(component["native_endpoint_internal_force_N"]),
                         rel_tol=1e-10, abs_tol=1e-8), "tie/native source RF scalar differs")
    require(math.isfinite(float(tie["transverse_shear_n"]))
            and abs(float(tie["transverse_shear_n"])) <= 1e-8, "nonaxial tie")
    normal = outer["head"]["axis"].toTuple()
    close_vector(tie["axis"], normal, "tie/head-to-nut axis differs")
    close_vector(tie["scalar_normal"], normal, "tie scalar normal differs")
    close_vector(component["physical_force_on_first_body_xyz_n"],
                 tie["force_on_first_xyz_n"], "component physical action differs")
    for role, side, sign in (("head", "first", 1), ("nut", "second", -1)):
        seat = outer[role]
        require(tie[side] == seat["member"], "outer receiver differs")
        close_vector(tie[side + "_point"], seat["point"].toTuple(), "outer seat point differs")
        close_vector(tie["force_on_" + side + "_xyz_n"],
                     [sign * signed * n for n in normal], "signed physical vector differs")
    radius = tie["force_rounding_radius_xyz_n"]
    require(len(radius) == 3 and all(math.isfinite(float(x)) and x >= 0 for x in radius),
            "invalid source rounding interval")
    return signed


def produce(support_path):
    geometry = load_method("geometry")
    acceptance = load_method("acceptance")
    _, register, _ = acceptance.verify_source_pins()
    base, _ = geometry.methods()
    _, model, _, _, input_pins = base.checked_inputs()
    connections, primary, upper = geometry.partition(base, model)
    seats = {c["axis_id"]: {s["role"]: s for s in geometry.source_seats(c)} for c in connections}
    require(sha(support_path) == SUPPORT_SHA, "geometry report differs from frozen reviewed record")
    support = json.loads(support_path.read_text())
    require(support["input_pins"] == input_pins and support["status"] == "GEOMETRY_EXCEPTIONS"
            and support["counts"] == {"axes": 54, "seats": 108, "members": 26},
            "geometry report identity/coverage differs")
    support_seats = {(r["axis_id"], r["role"]): r for r in support["seats"]}
    require(len(support_seats) == len(support["seats"]) == 108, "duplicate geometry seats")
    for body_pin in support["finished_step_pins"].values():
        require(sha(ROOT / body_pin["path"]) == body_pin["sha256"], "finished STEP changed")
    require(sha(FREEZE) == FREEZE_SHA, "all-body source freeze changed")
    freeze = json.loads(FREEZE.read_text())
    require(set(freeze["cases"]) == set(acceptance.CASE_SPECS), "wrong three-case set")
    rows, endpoints = [], []
    for case, files in freeze["cases"].items():
        acceptance.report_register_row(register, case, acceptance.CASE_SPECS[case])
        for pin in files.values():
            require(sha(ROOT / pin["path"]) == pin["sha256"], f"changed {case} source")
        response = json.loads((ROOT / files["response"]["path"]).read_text())
        native_model = json.loads((ROOT / files["model"]["path"]).read_text())
        audit = json.loads((ROOT / files["all_body_audit"]["path"]).read_text())
        terminal = json.loads((ROOT / files["terminal"]["path"]).read_text())
        require(audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
                and audit["source_model_sha256"] == files["model"]["sha256"]
                and audit["source_response_sha256"] == files["response"]["sha256"], "all-body audit differs")
        require(terminal.get("conditional_case_forces_usable",
                             terminal.get("response_usable_for_conditional_joint_checks")) is True,
                "terminal response unusable")
        for key in ("candidate", "geometry_revision_id"):
            expected = model["candidate"] if key == "candidate" else model["revision_id"]
            require(native_model[key] == response[key] == freeze[key] == expected, "wrong revision/candidate")
        require(native_model["case_id"] == response["case_id"] == case, "wrong case identity")
        for key in ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted",
                    "floor_capacity_established", "friction_qualified"):
            require(response[key] is False, "source acceptance boundary changed")
        for name, key in (("model", "source_input_model_json_sha256"),
                          ("deck", "source_input_deck_sha256"), ("native_data", "native_data_sha256")):
            require(response[key] == files[name]["sha256"], "source response/deck/native pin differs")
        require(tuple(i["load_factor"] for i in response["increments"]) == FACTORS, "wrong increment coverage")
        bindings = {r["name"]: r for r in native_model["unilateral_springa_bindings"]}
        require(len(bindings) == len(native_model["unilateral_springa_bindings"]), "duplicate source bindings")
        for index, increment in enumerate(response["increments"]):
            require(all(increment[g] is True for g in GATES), "source increment gate failed")
            components = {r["source_row_id"]: r for r in increment["springa_components"]}
            require(len(components) == len(increment["springa_components"]), "duplicate spring components")
            for axis_id, outer in sorted(seats.items()):
                name = axis_id + "/outer-seat-axial-tie"
                binding = bindings[name]
                component = components[binding["source_row_id"]]
                tie = increment["physical_connection_forces"][name]
                signed = checked_tie(tie, binding, component, outer)
                identity = {"case_id": case, "increment_index": index,
                            "load_factor": increment["load_factor"], "axis_id": axis_id}
                rows.append({**identity, "signed_tie_N": signed,
                             "state": "tension" if signed > SIGN_EPSILON else "display_zero",
                             "source_tie": tie, "source_spring_component": component})
                for role, side in (("head", "first"), ("nut", "second")):
                    support_row = support_seats[(axis_id, role)]
                    require(support_row["member"] == outer[role]["member"], "geometry receiver differs")
                    close_vector(support_row["point_xyz_mm"], outer[role]["point"].toTuple(), "geometry point differs")
                    endpoints.append({**identity, "seat_role": role, "receiver": tie[side],
                                      "point_xyz_mm": tie[side + "_point"],
                                      "physical_action_xyz_N": tie["force_on_" + side + "_xyz_n"],
                                      "signed_inward_action_N": signed,
                                      "geometry_screen_pass": support_row["geometry_screen_pass"],
                                      "hole_only_applicable": support_row["all_direction_hole_only_applicable"]})
    require(len(rows) == len({(r["case_id"], r["increment_index"], r["axis_id"]) for r in rows}) == 1134,
            "incomplete/duplicate tie coverage")
    require(len(endpoints) == 2268, "incomplete outer-seat coverage")
    exceptions = [r for r in endpoints if not r["geometry_screen_pass"]]
    require(len(exceptions) == 21 and {(r["axis_id"], r["seat_role"]) for r in exceptions}
            == {("center_principal_right_2", "nut")}, "geometry exception coverage differs")
    return {"status": "PASS_THREE_CASE_SIGNED_TIE_JOIN_ONLY", "candidate": model["candidate"],
            "revision": model["revision_id"], "producer_sha256": sha(Path(__file__)),
            "method_pins": METHODS, "freeze_sha256": FREEZE_SHA, "support_report_sha256": SUPPORT_SHA,
            "source_cases": freeze["cases"], "geometry_input_pins": input_pins,
            "excluded_primary_axes": primary, "excluded_upper_axes": upper,
            "counts": {"axes": 54, "cases": 3, "increments_per_case": 7,
                       "tie_states": len(rows), "seat_states": len(endpoints)},
            "states": dict(Counter(r["state"] for r in rows)),
            "maximum_tie": max(rows, key=lambda r: r["signed_tie_N"]),
            "partial_support_seat_states": exceptions, "tie_states": rows, "seat_states": endpoints,
            "claim_limits": {"source_join_only": True, "native_tokens_independently_parsed": False,
                             "native_solve": False, "geometry_changed": False, "physical_inspection": False,
                             "washer_contact_or_resistance": False, "complete_joint": False,
                             "six_case_envelope": False, "criterion_pass": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(produce(args.support_report), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
