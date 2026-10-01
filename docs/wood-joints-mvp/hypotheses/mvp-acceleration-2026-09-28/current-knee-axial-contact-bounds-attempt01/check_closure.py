#!/usr/bin/env python3
"""Independent matrix and vector closure check for the BG001 packet."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKET = json.loads((HERE / "axial-contact-bounds.json").read_text())
TOL = 1e-10


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def minus(a, b):
    return [a[i] - b[i] for i in range(3)]


def add(a, b):
    return [a[i] + b[i] for i in range(3)]


def check_close(got, expected):
    return len(got) == len(expected) and all(abs(x - y) <= TOL for x, y in zip(got, expected))


def main():
    eq = PACKET["conditional_equilibrium_map"]
    geom = PACKET["contact_support_geometry"]
    datum = PACKET["datum_transform"]["contact_datum_global_xyz_mm"]
    ids = eq["vertex_column_order"][:2]
    bolt_points = eq["axis_centers_global_xyz_mm"]
    corner_points = geom["outer_contact_convex_hull_corners_global_xyz_mm"]
    worst = 0.0

    for label, witness in eq["signed_unit_wrench_witnesses"].items():
        tensions = witness["bolt_tensions_N"]
        pressures = witness["contact_compression_resultants_N_at_outer_corners"]
        if any(value < -TOL for value in [*tensions.values(), *pressures.values()]):
            raise SystemExit(f"{label}: a tension or compression resultant is negative")

        # First reconstruct from the published scalar equilibrium equations.
        fx = sum(tensions.values()) - sum(pressures.values())
        my = sum((bolt_points[key][2] - datum[2]) * tensions[key] for key in ids)
        mz = 0.0
        for corner_id, force in pressures.items():
            dy = corner_points[corner_id][1] - datum[1]
            dz = corner_points[corner_id][2] - datum[2]
            my -= dz * force
            mz += dy * force
        scalar = [fx, my, mz]
        target = witness["wrench_at_contact_datum_Fx_My_Mz"]
        if not check_close(scalar, target):
            raise SystemExit(f"{label}: scalar map gives {scalar}, expected {target}")

        # Independently sum global force vectors and r cross F moments.
        force_sum = [0.0, 0.0, 0.0]
        moment_sum = [0.0, 0.0, 0.0]
        loads = [
            (bolt_points[ids[0]], [tensions[ids[0]], 0.0, 0.0]),
            (bolt_points[ids[1]], [tensions[ids[1]], 0.0, 0.0]),
        ]
        loads.extend((corner_points[key], [-value, 0.0, 0.0]) for key, value in pressures.items())
        for point, force in loads:
            force_sum = add(force_sum, force)
            moment_sum = add(moment_sum, cross(minus(point, datum), force))
        vector_result = [force_sum[0], moment_sum[1], moment_sum[2]]
        if not check_close(vector_result, target):
            raise SystemExit(f"{label}: vector sum gives {vector_result}, expected {target}")
        worst = max(worst, *(abs(x - y) for x, y in zip(vector_result, target)))

    # Check that the recorded null mode is truly self-equilibrated by the same
    # independent vector summation. Its coefficient t is set to one here.
    null = eq["self_equilibrated_tension_contact_mode"]
    force_sum = [0.0, 0.0, 0.0]
    moment_sum = [0.0, 0.0, 0.0]
    for axis_id in ids:
        force = [null["bolt_tension_N_per_t"][axis_id], 0.0, 0.0]
        force_sum = add(force_sum, force)
        moment_sum = add(moment_sum, cross(minus(bolt_points[axis_id], datum), force))
    for corner_id, reaction in null["contact_compression_resultants_N_per_t"].items():
        force = [-reaction, 0.0, 0.0]
        force_sum = add(force_sum, force)
        moment_sum = add(moment_sum, cross(minus(corner_points[corner_id], datum), force))
    if not check_close(force_sum, [0.0, 0.0, 0.0]) or not check_close(moment_sum, [0.0, 0.0, 0.0]):
        raise SystemExit(f"self-equilibrated mode failed: force {force_sum}, moment {moment_sum}")

    # Independently check the shaft-centroid to face-datum wrench shift.
    transform = PACKET["datum_transform"]
    fixture = transform["synthetic_round_trip_fixture_not_a_frame_demand"]
    r = transform["shaft_centroid_minus_contact_datum_xyz_mm"]
    f = fixture["force_xyz_N"]
    m = fixture["moment_at_shaft_centroid_xyz_N_mm"]
    shifted = [m[0], m[1] + r[2] * f[0] - r[0] * f[2], m[2] + r[0] * f[1] - r[1] * f[0]]
    if not check_close(shifted, fixture["moment_at_contact_datum_xyz_N_mm"]):
        raise SystemExit(f"datum transform failed: got {shifted}")

    print(f"independent closure passed for {len(eq['signed_unit_wrench_witnesses'])} unit witnesses and the null mode; max wrench residual {worst:.3g}; datum shift passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
