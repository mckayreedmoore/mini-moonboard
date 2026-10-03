#!/usr/bin/env python3
"""Independently rebuild header cut actions from native response point forces."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
REPORT_PATH = HERE / "section-demands.json"
OUTPUT = HERE / "parent-verification.json"
BODY = "base_header"
X_CUT = -1085.85
PLANE_TOL = 1e-6

SOURCES = {
    "a12-rear": {
        "report": "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "model": "current-springa-selected-floor-a12-rear-attempt03/model.json",
        "response": "current-springa-selected-floor-a12-rear-attempt03/response.json",
    },
    "a1-rear": {
        "report": "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "model": "current-springa-selected-floor-a1-rear-attempt02/model.json",
        "response": "current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
    },
    "k12-rear": {
        "report": "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
        "model": "current-k12-rear-spr489-direct-native-attempt01/model.json",
        "response": "current-k12-rear-spr489-direct-native-attempt01/response.json",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(a, b):
    return [a[i] + b[i] for i in range(3)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def summation(vectors):
    return [math.fsum(v[i] for v in vectors) for i in range(3)] if vectors else [0.0, 0.0, 0.0]


def moment_radius(point, datum, force_radius):
    r = [point[i] - datum[i] for i in range(3)]
    return [
        abs(r[1]) * force_radius[2] + abs(r[2]) * force_radius[1],
        abs(r[2]) * force_radius[0] + abs(r[0]) * force_radius[2],
        abs(r[0]) * force_radius[1] + abs(r[1]) * force_radius[0],
    ]


def wrench(actions, datum):
    force = summation([a["force"] for a in actions])
    moment = summation([
        add(cross([a["point"][i] - datum[i] for i in range(3)], a["force"]), a["couple"])
        for a in actions
    ])
    fr = summation([a["radius"] for a in actions])
    mr = summation([moment_radius(a["point"], datum, a["radius"]) for a in actions])
    return force, moment, fr, mr


def compare(actual, expected, tolerance, label):
    if len(actual) != len(expected) or any(abs(a - b) > tolerance for a, b in zip(actual, expected)):
        raise AssertionError(f"{label}: actual={actual}, expected={expected}, tol={tolerance}")


def collect_native_actions(response_inc, model, load_factor):
    conns = []
    for name, row in response_inc["physical_connection_forces"].items():
        if row.get("first") == BODY or row.get("second") == BODY:
            side = "first" if row["first"] == BODY else "second"
            conns.append({
                "source_type": "physical_connection_force",
                "name": name,
                "role": row.get("role"),
                "point": row.get(side + "_point", row["point"]),
                "force": row["force_on_" + side + "_xyz_n"],
                "radius": row.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0]),
                "couple": [0.0, 0.0, 0.0],
            })
    loads = []
    node_loads = model["physical_body_loads"][BODY]
    if {str(n) for n in node_loads} != {str(n) for n in model["physical_body_nodes"][BODY]}:
        raise AssertionError("base_header physical load/node coverage changed")
    for node, reference in node_loads.items():
        point = model["nodes"].get(str(node), model["nodes"].get(node))
        if point is None:
            raise AssertionError(f"missing node coordinate {node}")
        loads.append({
            "source_type": "source_discrete_body_load",
            "name": f"{BODY}/node/{node}",
            "role": "source_discrete_gravity_and_attached_hardware_load",
            "point": point,
            "force": [load_factor * float(v) for v in reference],
            "radius": [0.0, 0.0, 0.0],
            "couple": [0.0, 0.0, 0.0],
        })
    return conns + loads


def internal(force, moment):
    return {"force_xyz_n": [-v for v in force], "moment_xyz_nmm": [-v for v in moment]}


def build_cut(actions, datum):
    left, plane, right = [], [], []
    for action in actions:
        dx = action["point"][0] - X_CUT
        if dx < -PLANE_TOL:
            left.append(action)
        elif dx > PLANE_TOL:
            right.append(action)
        else:
            plane.append(action)
    states = {}
    for name, (left_actions, right_actions) in {
        "immediately_before_transfer": (left, plane + right),
        "immediately_after_transfer": (left + plane, right),
    }.items():
        lw = wrench(left_actions, datum)
        rw = wrench(right_actions, datum)
        states[name] = {
            "left": internal(lw[0], lw[1]),
            "right": internal(rw[0], rw[1]),
            "left_count": len(left_actions),
            "right_count": len(right_actions),
        }
    pw = wrench(plane, datum)
    return states, plane, pw


def main():
    result = json.loads(REPORT_PATH.read_text())
    if result["status"] != "PASS_SOURCE_PINNED_CONDITIONAL_SIGNED_HEADER_SECTION_ACTIONS":
        raise AssertionError("producer result status changed")
    comparisons = 0
    body_closures = 0
    inventory_checks = 0
    jump_checks = 0
    max_force_diff = 0.0
    max_moment_diff = 0.0
    pins = {str(REPORT_PATH.relative_to(ROOT)): sha(REPORT_PATH)}

    for case, source in SOURCES.items():
        report = json.loads((BASE / source["report"]).read_text())
        model = json.loads((BASE / source["model"]).read_text())
        response = json.loads((BASE / source["response"]).read_text())
        for key, relative in source.items():
            pins[str((BASE / relative).relative_to(ROOT))] = sha(BASE / relative)
        report_rows = report["increments"]
        response_rows = response["increments"]
        output_rows = [r for r in result["per_increment_header_sections"] if r["case_id"] == case]
        if len(output_rows) != 7:
            raise AssertionError(f"expected 7 output increments for {case}")

        for out, rep, resp in zip(output_rows, report_rows, response_rows):
            if out["time"] != rep["time"] or out["load_factor"] != rep["load_factor"]:
                raise AssertionError(f"increment identity mismatch for {case}")
            native = collect_native_actions(resp, model, float(rep["load_factor"]))
            native_conn = [a for a in native if a["source_type"] == "physical_connection_force"]
            exporter_names = {
                row["source_connection_name"] for row in rep["all_corner_interfaces"]
                if row.get("first") == BODY or row.get("second") == BODY
            }
            native_names = {a["name"] for a in native_conn}
            if len(exporter_names) != 160 or len(native_conn) != 160 or exporter_names != native_names:
                raise AssertionError(f"native/export header inventory incomplete for {case}/{rep['time']}")
            inventory_checks += 1

            for reaction_key in ("exact_floor_tangent_reactions", "inactive_floor_tangent_zero_actions"):
                if any(row.get("first") == BODY or row.get("second") == BODY for row in resp.get(reaction_key, [])):
                    raise AssertionError(f"unexpected separate floor tangent action on header: {case}/{reaction_key}")

            origin = wrench(native, [0.0, 0.0, 0.0])
            if any(abs(origin[0][j]) > origin[2][j] + 1e-9 for j in range(3)):
                raise AssertionError(f"native full-header force closure failed {case}/{rep['time']}")
            if any(abs(origin[1][j]) > origin[3][j] + 1e-7 for j in range(3)):
                raise AssertionError(f"native full-header moment closure failed {case}/{rep['time']}")
            body_closures += 1

            datum = [X_CUT, -105.85, 257.95]
            states, plane, plane_wrench = build_cut(native, datum)
            expected = out["section_at_transfer_station"]
            compare(expected["plane_coincident_external_wrench"]["force_xyz_n"], plane_wrench[0], 1e-9, "plane force")
            compare(expected["plane_coincident_external_wrench"]["moment_xyz_nmm_about_cut_datum"], plane_wrench[1], 1e-7, "plane moment")
            expected_plane_names = {row["source_name"] for row in expected["plane_coincident_external_wrench"]["point_actions"]}
            actual_plane_names = {a["name"] for a in plane}
            if expected_plane_names != actual_plane_names or len(plane) != 4:
                raise AssertionError(f"plane-coincident inventory mismatch for {case}/{rep['time']}")
            jump_checks += 1

            for state_name, native_state in states.items():
                written = expected["one_sided_sections"][state_name]
                for side in ("left", "right"):
                    stored = written[side + "_segment_material_action"]
                    direct = native_state[side]
                    fd = max(abs(stored["force_xyz_n"][j] - direct["force_xyz_n"][j]) for j in range(3))
                    md = max(abs(stored["moment_xyz_nmm"][j] - direct["moment_xyz_nmm"][j]) for j in range(3))
                    if fd > 1e-9 or md > 1e-7:
                        raise AssertionError(f"native one-sided section mismatch {case}/{rep['time']}/{state_name}/{side}: {fd}, {md}")
                    max_force_diff = max(max_force_diff, fd)
                    max_moment_diff = max(max_moment_diff, md)
                    comparisons += 1

                # The two material actions together balance the full-body
                # external residual; the jump isolates only plane actions.
                internal_sum_force = add(native_state["left"]["force_xyz_n"], native_state["right"]["force_xyz_n"])
                internal_sum_moment = add(native_state["left"]["moment_xyz_nmm"], native_state["right"]["moment_xyz_nmm"])
                full_at_datum = wrench(native, datum)
                compare(internal_sum_force, [-v for v in full_at_datum[0]], 1e-9, "complementary force sum")
                compare(internal_sum_moment, [-v for v in full_at_datum[1]], 1e-7, "complementary moment sum")

    # Independent hand-answer for force/couple transport and datum translation.
    oracle_force = [0.0, 10.0, 0.0]
    oracle_point = [2.0, 0.0, 0.0]
    oracle_couple = [0.0, 0.0, 3.0]
    m0 = add(cross(oracle_point, oracle_force), oracle_couple)
    m1 = add(cross([1.0, 0.0, 0.0], oracle_force), oracle_couple)
    compare(m0, [0.0, 0.0, 23.0], 1e-12, "known force/couple moment at origin")
    compare(m1, [0.0, 0.0, 13.0], 1e-12, "known force/couple moment at translated datum")

    for path in [HERE / "produce.py", HERE / "parent_verify.py"]:
        pins[str(path.relative_to(ROOT))] = sha(path)
    output_hashes = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (REPORT_PATH, HERE / "produce.py", HERE / "parent_verify.py")
    }
    verification = {
        "status": "PASS_PARENT_NATIVE_POINT_FORCE_HEADER_SECTION_RECONSTRUCTION",
        "case_count": 3,
        "independent_header_body_closure_count": body_closures,
        "independent_native_export_inventory_checks": inventory_checks,
        "independent_plane_jump_checks": jump_checks,
        "one_sided_segment_wrench_comparisons": comparisons,
        "maximum_force_difference_n": max_force_diff,
        "maximum_moment_difference_nmm": max_moment_diff,
        "known_force_couple_transport_oracle": {
            "moment_about_origin_xyz_nmm": m0,
            "moment_about_x1mm_datum_xyz_nmm": m1,
            "passed": True,
        },
        "source_sha256": pins,
        "result_sha256": output_hashes,
        "scope": "Independent native-response endpoint forces plus load-factor-scaled source discrete base_header nodal loads; does not reuse the producer's report-row action collection.",
        "physical_self_weight_distribution_qualified": False,
        "splitting_demand_or_resistance_established": False,
        "joint_accepted": False,
    }
    OUTPUT.write_text(json.dumps(verification, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in verification.items() if k not in ("source_sha256", "result_sha256", "scope")}))


if __name__ == "__main__":
    main()
