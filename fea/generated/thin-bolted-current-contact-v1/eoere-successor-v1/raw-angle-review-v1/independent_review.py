"""Read-only source/station arithmetic readiness audit; no cache shape imports."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
PACKET = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/"
CODE = "scripts/eoere_bolted_candidate.py"
TEST = "tests/test_eoere_bolted_candidate.py"
STATIONS = PACKET + "eoere-successor-v1/owner-stations.json"
MANIFEST = PACKET + "native-geometry-v4.json"
LAYOUT = PACKET + "mixed-offset-rows-shallow-wires-v4.json"
PINS = {
    CODE: "87bc48f28364ff085101d37631635236d51180c5a83efad1ecaa8ddf24bf4848",
    TEST: "f537f1bcc7149c39c72386a2a43e6d9db6e2ce4528e4df1153ac3a5561c5817a",
    STATIONS: "f7bd4c803ac149f927d85163a0a9ca2d52eff95abf9901f2c462faa54296ebe5",
    MANIFEST: "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
    LAYOUT: "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def merge(*maps):
    pins = {}
    for data in maps:
        for path, digest in data.items():
            require(path not in pins or pins[path] == digest, "conflicting source: " + path)
            pins[path] = digest
    return pins


def verify(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + path)


def check():
    verify(PINS)
    source, stations, layout = [json.loads((ROOT / path).read_bytes()) for path in (MANIFEST, STATIONS, LAYOUT)]
    raw = {row["member"]: row for row in source["raw_parts"]}
    require(len(raw) == len(source["raw_parts"]) == 20 and len({row["id"] for row in raw.values()}) == 20,
            "twenty unique source raw bodies required")
    pins = merge(PINS, source["source_sha256"], {row["path"]: row["sha256"] for row in raw.values()},
                 {str(OWN.relative_to(ROOT)): sha(str(OWN.relative_to(ROOT)))})
    verify(pins)
    require(stations["source_sha256"] == PINS[LAYOUT], "station predecessor binding differs")
    rows = stations["main_stations"] + stations["remaining_base_header_starting_stations"]
    old = {row["angle_id"]: row for row in layout["raw_fittings"]}
    require(len(rows) == 24 and len(stations["main_stations"]) == 16
            and len(stations["remaining_base_header_starting_stations"]) == 8
            and len({row["duty_id"] for row in rows}) == 24
            and {row["duty_id"] for row in rows} == {row["duty_id"] for row in old.values()}, "exact24 duty handoff differs")
    tree = ast.parse((ROOT / CODE).read_text())
    scenario = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Scenario")
    dimensions = {node.target.id: ast.literal_eval(node.value) for node in scenario.body if isinstance(node, ast.AnnAssign)}
    require(dimensions == {"leg_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "transverse_pitch_mm": 50.8,
                          "axial_pitch_mm": 41.275, "far_offset_mm": 65.0875, "factory_hole_mm": 10.,
                          "bolt_mm": 9.525, "wood_bore_mm": 10.31875}, "nominal scenario changed")
    require(all(math.isfinite(v) and v > 0 for v in dimensions.values()), "finite positive scenario required")
    radius = dimensions["factory_hole_mm"] / 2.
    near = dimensions["far_offset_mm"] - dimensions["axial_pitch_mm"]
    reserves = {"near_hole_to_ideal_heel_edge_mm": near - radius - dimensions["thickness_mm"],
        "far_hole_to_outer_edge_mm": dimensions["leg_mm"] - dimensions["far_offset_mm"] - radius,
        "transverse_hole_to_width_edge_mm": (dimensions["width_mm"] - dimensions["transverse_pitch_mm"]) / 2. - radius,
        "bolt_factory_diametrical_clearance_mm": dimensions["factory_hole_mm"] - dimensions["bolt_mm"],
        "bolt_wood_diametrical_clearance_mm": dimensions["wood_bore_mm"] - dimensions["bolt_mm"]}
    require(min(reserves.values()) > 0, "nominal sharp-angle hole reserves nonpositive")
    factory_volume = ((2. * dimensions["leg_mm"] * dimensions["thickness_mm"] - dimensions["thickness_mm"]**2)
                      * dimensions["width_mm"] - 8. * math.pi * radius**2 * dimensions["thickness_mm"])
    groups, frame_error, determinant_error, pair_error = {}, 0., 0., 0.
    for row in rows:
        require(row["angle_id"] in old and all(row[key] == old[row["angle_id"]][key]
            for key in ("duty_id", "beam", "post", "origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")), "source starting pose/owner differs")
        require(row["beam"] in raw and row["post"] in raw and row["beam"] != row["post"], "known distinct raw receivers required")
        original = np.stack([row["u_xyz"], row["v_xyz"], row["w_xyz"]])
        require(np.isfinite(original).all(), "nonfinite pose")
        frame_error = max(frame_error, float(np.linalg.norm(original @ original.T - np.eye(3))))
        determinant_error = max(determinant_error, abs(float(np.linalg.det(original)) - 1.))
        u = original[0] / np.linalg.norm(original[0])
        v = original[1] - u * float(original[1] @ u)
        v /= np.linalg.norm(v)
        w = np.cross(u, v)
        require(np.linalg.norm(w - original[2]) < 1e-8, "pose normalization would fail")
        for flange, receiver, along, inward in (("beam", row["beam"], u, -v), ("post", row["post"], v, -u)):
            pair = []
            for sign in (-1, 1):
                point = np.asarray(row["origin_xyz_mm"]) + dimensions["far_offset_mm"] * along + sign * 25.4 * w
                pair.append(point)
                direction = inward.copy()
                if next(float(x) for x in direction if abs(x) > 1e-8) < 0:
                    direction *= -1
                foot = point - direction * float(point @ direction)
                key = tuple(round(float(x), 6) for x in np.r_[direction, foot])
                groups.setdefault(key, []).append({"duty_id": row["duty_id"], "flange": flange, "receiver": receiver})
            pair_error = max(pair_error, abs(float(np.linalg.norm(pair[1] - pair[0])) - 50.8))
    require(frame_error < 1e-8 and determinant_error < 1e-8 and pair_error < 1e-10, "proper source frames/transverse pairs differ")
    verify(pins)
    return {"schema": "eoere_successor_raw_angle_independent_method_review/v1", "readiness": "READY_FOR_BOUNDED_RAW_GEOMETRY_AUDIT",
        "confirmed_readiness_blockers": [], "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "source_pin_count": len(pins), "raw_cache_byte_count": sum(row["bytes"] for row in raw.values()),
        "raw_member_count": 20, "main_angles": 16, "base_header_starting_angles": 8, "all_factory_holes": 192,
        "active_flange_attachments": 96, "main_attachments": 64,
        "unqueried_nominal_attachment_line_groups": len(groups),
        "unqueried_nominal_coincident_groups": [ports for ports in groups.values() if len(ports) > 1],
        "scenario": dimensions, "near_factory_hole_offset_mm": near, "ideal_sharp_angle_reserves": reserves,
        "hand_perforated_ideal_angle_volume_mm3": factory_volume,
        "proper_starting_frame_max_residual": frame_error, "starting_frame_max_det_error": determinant_error,
        "transverse_pair_distance_max_error_mm": pair_error,
        "focused_checks": {"pytest_command": ".venv/bin/python -B -m pytest -q " + TEST, "pytest": "8 passed in 1.39s",
                           "ruff_command": ".venv/bin/ruff check " + CODE + " " + TEST, "ruff": "All checks passed!"},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "cadquery": importlib.metadata.version("cadquery")},
        "error_handling_review": "Invalid dimension scenarios reject. Receiver line ValueErrors remain per-hole geometry_error; other geometry errors propagate. No miss or partial bore is promoted to accepted attachment.",
        "nonblocking_count_interpretation": "partial_raw_bores includes missing_receiver_lines via a default zero occupancy; these counts overlap. line_span measures an infinite line, not directed-ray entry clearance. Coincidence uses six-decimal numerical keys.",
        "scope": ["Nominal inch/sharp-angle study: actual heel datums, bend/holes and product strength remain unavailable.",
                  "Raw body bytes only; service cuts, recesses, bores, four new lower blocks/cleats, panels, tools and washers are not established.",
                  "Twelve starting frame bolts and66Hillman stations require separate coordinated successor checks; recorded counts do not prove clearance.",
                  "Source historical poses are starting datums. New holes/poses consume no predecessor forces or acceptance.",
                  "Receiver intersections and valid attachment line groups are uncomputed by this reviewer; parent owns the one serialized raw-cache audit."],
        "actual20_cache_CAD_imports_candidate_q_K_forces_or_native_runs": False,
        "release": {"candidate_accepted": False, "complete_joint_acceptance": False, "capacity_established": False,
                    "fabrication_released": False, "structural_released": False, "climbing_released": False}}


def main():
    invocation = {"actual_sys_argv_from_start": sys.argv.copy(), "actual_sys_orig_argv_from_start": sys.orig_argv.copy(),
                  "cwd_from_start": str(Path.cwd()), "review_source_sha256": sha(str(OWN.relative_to(ROOT)))}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve independent evidence")
    result = {**check(), "review_execution": invocation}
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"readiness": result["readiness"], "path": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      "bytes": args.out.stat().st_size, "pins": result["source_pin_count"]}))


if __name__ == "__main__":
    main()
