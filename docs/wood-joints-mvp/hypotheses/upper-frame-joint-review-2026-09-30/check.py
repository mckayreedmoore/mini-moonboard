#!/usr/bin/env python3
"""Independently compare upper lateral exports with frozen native RF tokens."""

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def norm(v):
    return math.sqrt(dot(v, v))


def normalized(v):
    return [x / norm(v) for x in v]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def native_forces(path, wanted_nodes):
    found, time = {}, None
    with path.open() as stream:
        for line in stream:
            if "forces (fx,fy,fz) for set ALLN and time" in line:
                time = float(line.split()[-1])
                assert time not in found
                found[time] = {}
            elif "displacements (vx,vy,vz)" in line:
                time = None
            elif time is not None:
                fields = line.split()
                if len(fields) == 4 and fields[0].isdigit():
                    node = int(fields[0])
                    if node in wanted_nodes:
                        assert node not in found[time]
                        found[time][node] = [float(x) for x in fields[1:]]
    assert len(found) == 7
    assert all(set(nodes) == wanted_nodes for nodes in found.values())
    return found


def check():
    report = json.loads((HERE / "upper-joints.json").read_text())
    freeze = json.loads((HERE / "freeze.json").read_text())
    max_force_error, max_grain_error, max_edge_error = 0.0, 0.0, 0.0
    direct_count, direction_count = 0, 0
    for case, sources in freeze["cases"].items():
        for name in ("model", "native_data"):
            assert sha(ROOT / sources[name]["path"]) == sources[name]["sha256"]
        model = json.loads((ROOT / sources["model"]["path"]).read_text())
        rows = [r for r in report["bolt_actions"] if r["case"] == case]
        axis_ids = {r["axis_id"] for r in rows}
        assert len(axis_ids) == 16
        springs = [
            s
            for s in model["springs"]
            if s["physical_owner"].get("axis_id") in axis_ids
            and s["role"] == "candidate_bolt_lateral_plane"
        ]
        assert len(springs) == 32
        by_axis = {
            axis: [s for s in springs if s["physical_owner"]["axis_id"] == axis]
            for axis in axis_ids
        }
        assert all(len(s) == 2 for s in by_axis.values())
        native = native_forces(
            ROOT / sources["native_data"]["path"],
            {node for s in springs for node in s["nodes"]},
        )
        for row in rows:
            first_forces, source_ids = [], []
            for spring in by_axis[row["axis_id"]]:
                n1, n2 = spring["nodes"]
                dof = spring["dof"] - 1
                rf = native[row["load_factor"]]
                # RF is the force required at a carrier endpoint, so its
                # equal-and-opposite source-body action reverses its sign.
                scalar_on_first = -(rf[n1][dof] - rf[n2][dof]) / 2
                first_forces.append(
                    [
                        scalar_on_first * x
                        for x in spring["physical_owner"]["force_basis"][dof]
                    ]
                )
                source_ids.append(spring["source_row_id"])
            assert set(source_ids) == set(row["lateral_source_row_ids"])
            force = [math.fsum(v[i] for v in first_forces) for i in range(3)]
            owner = by_axis[row["axis_id"]][0]["physical_owner"]
            if owner["first"] != row["block"]:
                assert owner["second"] == row["block"]
                force = [-x for x in force]
            error = max(
                abs(x - y)
                for x, y in zip(force, row["lateral_force_on_block_n"], strict=True)
            )
            max_force_error = max(max_force_error, error)
            assert error < 1e-9
            assert abs(norm(force) - row["lateral_magnitude_n"]) < 1e-9
            direct_count += 1
            for role in ("block", "host"):
                member = row[role]
                g = model["body_geometry"][member]["geometry_record"]
                grain = normalized(g["source_descriptor"]["grain_global_xyz"])
                member_force = force if role == "block" else [-x for x in force]
                grain_force = dot(member_force, grain)
                actual = row["member_directions"][role]
                max_grain_error = max(
                    max_grain_error,
                    abs(grain_force - actual["force_parallel_to_grain_signed_n"]),
                )
                assert (
                    abs(grain_force - actual["force_parallel_to_grain_signed_n"]) < 1e-7
                )
                # Independently project the source interface point to the two
                # geometric endpoints. No use of the producer's classifier.
                axis = normalized(g["axis"])
                center = owner["point"]
                start_to_center = dot(
                    [center[i] - g["start"][i] for i in range(3)], axis
                )
                length = norm([g["end"][i] - g["start"][i] for i in range(3)])
                distance = (
                    length - start_to_center
                    if dot(member_force, axis) > 0
                    else start_to_center
                )
                exported = actual["grain_end_direction"][
                    "distance_to_loaded_outer_boundary_mm"
                ]
                if exported is not None:
                    max_edge_error = max(max_edge_error, abs(distance - exported))
                    assert abs(distance - exported) < 1e-6
                direction_count += 1
    assert direct_count == 336 and direction_count == 672
    return {
        "schema": "upper-frame-native-token-check/v1",
        "status": "PASS_EXPORT_RECONSTRUCTION_ONLY",
        "checker_sha256": sha(Path(__file__)),
        "report_sha256": sha(HERE / "upper-joints.json"),
        "freeze_sha256": sha(HERE / "freeze.json"),
        "direct_native_lateral_records_checked": direct_count,
        "signed_member_directions_checked": direction_count,
        "max_lateral_force_vector_difference_n": max_force_error,
        "max_signed_grain_component_difference_n": max_grain_error,
        "max_loaded_outer_grain_end_difference_mm": max_edge_error,
        "limits": "Independent DAT RF-token extraction and vector/end-direction reconstruction using the frozen source carrier mapping. Does not revalidate the solver/carrier law, bolt distribution, contact applicability or resistance.",
        "complete_joint_accepted": False,
        "six_case_envelope_established": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = check()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.verify:
        assert (HERE / "verification.json").read_text() == text
    else:
        (HERE / "verification.json").write_text(text)
    print(text)
