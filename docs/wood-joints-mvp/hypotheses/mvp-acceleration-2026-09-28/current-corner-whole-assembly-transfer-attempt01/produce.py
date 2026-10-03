#!/usr/bin/env python3
"""Authenticate and sum the five-body corner boundary at one common datum."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCES = {
    "a12-rear": ("current-corner-native-demand-export-attempt03", "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17"),
    "a1-rear": ("current-corner-a1-rear-case-bound-export-attempt01", "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce"),
    "k12-rear": ("current-corner-k12-rear-case-bound-export-attempt01", "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0"),
}
MEMBERS = {"base_header", "base_post_outer_left", "base_side_left", "knee_outer_left_spine", "knee_outer_left_inner_frame_block"}


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def plus(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def shift(force, moment, datum):
    return force + plus(moment, cross(datum, force))


def close(a, b, force=1e-8, moment=1e-6):
    error = [abs(x-y) for x, y in zip(a, b, strict=True)]
    assert max(error[:3]) <= force and max(error[3:]) <= moment, error
    return error


def build():
    # A force/couple transport oracle and an internal collinear tie oracle.
    close(shift([2., 3., 4.], [5., 6., 7.], [10., 20., 30.]), [2., 3., 4., -5., 26., -3.])
    close(plus(shift([2., 0., 0.], [0.]*3, [1., 4., 5.]), shift([-2., 0., 0.], [0.]*3, [8., 4., 5.])), [0.]*6)
    results = []
    pins = {}
    for case, (folder, expected) in SOURCES.items():
        path = BASE/folder/"corner-demand-report.json"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected
        pins[str(path.relative_to(ROOT))] = actual
        report = json.loads(path.read_text())
        assert report["actual_case_demand_usable_for_conditional_joint_checks"] is True
        assert report["case_id"] == case
        assert len(report["increments"]) == 7
        for inc in report["increments"]:
            balances = inc["corner_five_body_balance"]
            assert set(balances) == MEMBERS
            assert inc["all_five_corner_bodies_raw_and_interval_balance_passed"] is True
            assert all(inc["response_audit_gates"].values())
            assert len(inc["all_corner_interfaces"]) == 338
            internal = [0.]*6
            boundary = [0.]*6
            loads = [0.]*6
            reported_residual = [0.]*6
            by_port = {}
            by_member = {m: [0.]*6 for m in MEMBERS}
            internal_count = boundary_count = 0
            for row in inc["all_corner_interfaces"]:
                first_inside = row["first"] in MEMBERS
                second_inside = row["second"] in MEMBERS
                assert first_inside or second_inside
                inside = first_inside and second_inside
                assert (row["relation"] == "internal_corner_transfer") == inside
                if inside:
                    internal_count += 1
                else:
                    boundary_count += 1
                pair = [0.]*6
                for side in ("first", "second"):
                    member = row[side]
                    if member not in MEMBERS:
                        continue
                    force = row[f"force_on_{side}_xyz_n"]
                    point = row[f"{side}_point_global_xyz_mm"]
                    # These exports serialize endpoint point forces, not free couples.
                    # The *_at_owner_datum fields use a connection datum, not body datum.
                    wrench = shift(force, [0.]*3, point)
                    pair = plus(pair, wrench)
                    by_member[member] = plus(by_member[member], wrench)
                    if not inside:
                        other = row["second" if side == "first" else "first"]
                        key = (member, other, row["role"])
                        entry = by_port.setdefault(key, {"wrench": [0.]*6, "connections": []})
                        entry["wrench"] = plus(entry["wrench"], wrench)
                        entry["connections"].append(row["source_connection_name"])
                if inside:
                    close(pair, [0.]*6)
                    internal = plus(internal, pair)
                else:
                    boundary = plus(boundary, pair)
            for member, row in balances.items():
                datum = row["datum_global_xyz_mm"]
                interface = row["interface_action_wrench"]
                close(by_member[member], shift(interface["force_xyz_n"], interface["moment_xyz_nmm"], datum))
                external = row["external_load_wrench"]
                loads = plus(loads, shift(external["force_xyz_n"], external["moment_xyz_nmm"], datum))
                residual = row["combined_residual_wrench"]
                reported_residual = plus(reported_residual, shift(residual["force_xyz_n"], residual["moment_xyz_nmm"], datum))
            combined = plus(plus(internal, boundary), loads)
            errors = close(combined, reported_residual)
            results.append({
                "case_id": case, "load_factor": inc["load_factor"], "time": inc["time"],
                "internal_interface_count": internal_count, "boundary_interface_count": boundary_count,
                "internal_cancellation_wrench": internal,
                "boundary_wrench": boundary, "external_load_wrench": loads,
                "combined_residual_wrench": combined,
                "transported_source_body_residual_wrench": reported_residual,
                "reconstruction_absolute_error": errors,
                "boundary_ports": [{"corner_member": k[0], "external_receiver": k[1], "role": k[2], **v} for k, v in sorted(by_port.items())],
            })
    return {
        "schema": "conditional_five_body_corner_boundary/v1",
        "status": "PASS_AUTHENTICATED_INTERNAL_CANCELLATION_AND_BOUNDARY_RECONSTRUCTION",
        "source_pins": pins,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "common_datum_global_xyz_mm": [0., 0., 0.],
        "vector_order_and_units": "Fx,Fy,Fz [N], Mx,My,Mz [Nmm]",
        "members": sorted(MEMBERS), "state_count": len(results),
        "oracles": "force plus free couple transported to origin; equal/opposite collinear internal tie",
        "states": results,
        "limits": [
            "Only the three authenticated conditional rear cases; no six-case or stiffness envelope.",
            "Assembly residuals are transported sums of existing per-body residuals. Do not compare them to an untransported individual-body moment tolerance or create a new acceptance waiver.",
            "Internal forces cancel at assembly scale but still require individual member and complete-joint resistance checks.",
            "Boundary ports include floor, panel, neighboring block and original frame interfaces; topology is not a single serial path through BG001/BG003/BG045.",
            "No timber/bolt/washer/splitting capacity, physical contact compatibility or accepted fabrication/climber rating is inferred.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    content = json.dumps(build(), indent=2, sort_keys=True, allow_nan=False)+"\n"
    output = HERE/"assembly-transfer.json"
    if args.verify:
        assert output.read_text() == content
        print("PASS_BYTE_IDENTICAL_WHOLE_CORNER_BOUNDARY_RECONSTRUCTION")
    else:
        output.write_text(content)
        print("WROTE", output.relative_to(ROOT))
