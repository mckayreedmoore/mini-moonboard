"""N16 operation queries from saved inputs; importing this module is inert.

prepare() and the arithmetic/query APIs use only the standard library. The
parent explicitly acknowledges ownership before run()/build() may import
saved BReps. No source scene, member, hole, mesh, frame or solver is rebuilt.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import os
import select
import subprocess
import sys
import time
from collections import Counter
from importlib.metadata import version
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/operation-envelope-completion"
H = "docs/wood-joints-mvp/hypotheses"
A = f"{H}/mvp-resume-2026-10-01/assembly-package"
U = f"{H}/mvp-resume-2026-10-01/upper-corner-screw-layout"
E = f"{H}/evaluation-resume-2026-09-24"
FILES = {
    "envelope": f"{A}/rawlocal/ordinary-n-envelope/attempt01/envelope.json",
    "envelope_receipt": f"{A}/rawlocal/ordinary-n-envelope/attempt01/receipt.json",
    "scene": f"{A}/rawlocal/knee-bridge-fit/prepare-attempt02/setup.json",
    "snapshots": f"{A}/rawlocal/top-washer-fit/prepare-attempt02/snapshot-manifest.json",
    "manifest": f"{U}/rawlocal/knee-bridge-working-package/attempt02/manifest.json",
    "top_correction": f"{H}/mvp-resume-2026-10-01/top-corner-correction/proposal.json",
    "access": f"{E}/access-screen-attempt03-exact-components.json",
    "retained": f"{E}/retained-access-attempt03/access.json",
    "captured": f"{E}/captured-nut-motion-attempt02/motion.json",
    "shop": f"{A}/shop-guide.md",
    "map": f"{A}/joint-hardware-map.md",
    "fit": f"{A}/knee-bridge-fit.md",
    "length_fit": f"{A}/hardware-length-fit.md",
    "wire": "docs/wood-joints-mvp/current-retained-wire-sequence.md",
    "frame": f"{U}/rawlocal/knee-bridge-frame/attempt02/response/comparison.json",
    "gravity": f"{U}/rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json",
    "response": f"{U}/rawlocal/knee-bridge-frame/attempt02/response/response.npz",
    "lock": "uv.lock",
    "project": "pyproject.toml",
}
PINS = {
    "envelope": "278407d84e0061ab845ff73fb31dfc5551300a3afb9aa20327a5cca9e6b86ffc",
    "envelope_receipt": "8cec13103d82b262cdbd9446aefb2227ecc0270ebb241999366bc1be8f690fc2",
    "scene": "794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb",
    "snapshots": "c046e1d5b93a3ea69105171b1ab8958915f2a2ae81450c0fdc1d5b3547de7086",
    "manifest": "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    "top_correction": "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    "access": "bd2b97c0677b2e0ab5b09898ba7f2227758088744cd93f7e3c9b266bce5c5215",
    "retained": "fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97",
    "captured": "83c905bec64010695c769a73d7b8923869ef1aef5bda9b8591cdad0d443b21a4",
    "shop": "b3d13e0b90004f3c150a7d5756173bd203ab41dc27a79ee11420aca5c4ed1bd8",
    "map": "db4c50311caf348752ef54b10957fd594bfea28f1c3a9e46f135f44abbf7097c",
    "fit": "881b4a4c8e3c2dfb5be1f3690de287fb21863817c14f02b3b4484a8e2ff5d867",
    "length_fit": "40ec79f3193c60acb718a351bde8db24f67ccacf83a11f86c6e583b1a51d2e4b",
    "wire": "d4df2519c579c8f5d2865205f7c3e6dc03eb4136d7853530031ef90e56dd0559",
    "frame": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    "gravity": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    "response": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    "lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
    "project": "84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452",
}
EXACT_TOOL_VERSIONS = {"cadquery": "2.8.0", "cadquery-ocp": "7.9.3.1.1"}
ORIGIN_PRODUCER = "fa5d055af3d669e1d1b1f10a94c08744bac20ab6ffceddbcbc565e59fdb3ba86"
ORIGIN_SETUP = f"{A}/rawlocal/operation-envelope-completion/prepare-parent03/setup.json"
AABB_RESULT = f"{A}/rawlocal/operation-envelope-completion/attempt02-aabb/result.json"
CONTINUATION_PINS = {
    ORIGIN_SETUP: "d5b942388150bc174ad999f6c53497989c55bea8bba6ab4566bf68079425494a",
    str(Path(ORIGIN_SETUP).with_name("receipt.json")): "8c7bc4abdac49696149cb332b8074b5a8a29fcf2f5cbc58f9accae9e25bdfd4d",
    str(Path(ORIGIN_SETUP).with_name("producer.py.snapshot")): ORIGIN_PRODUCER,
    AABB_RESULT: "5e6ae7a6dd6bd2184aac6fd80e2aaddf686c8ea5c191e19b19f23c6d65c044e2",
    str(Path(AABB_RESULT).with_name("receipt.json")): "3e01d6b3f56dfab643cdb8495d471bc3a77d050f60963487bdd70818ef513e01",
    str(Path(AABB_RESULT).with_name("producer.py.snapshot")): ORIGIN_PRODUCER,
    f"{A}/rawlocal/operation-envelope-completion/attempt01/execution-stop.json": "c0c66e9fe6f69046dbe9b2faed440951cc146f7f6990cb2fa374d793e056f85c",
}
REFERENCE_JOURNAL = f"{A}/rawlocal/operation-envelope-completion/attempt03-route-first/journal.jsonl"
REFERENCE_RUN_PINS = {
    REFERENCE_JOURNAL: "07fa1d7bd3cfd7399a4aaac07993e487d504f4a3ae33c72013cda7f1d7e0faf6",
    str(Path(REFERENCE_JOURNAL).with_name("receipt.json")): "795c7a617e5e1e0eea756cce88cab029480dcc37caf9473c399cd98723843969",
    str(Path(REFERENCE_JOURNAL).with_name("result.json")): "221cad5172672de43b59b554e49b092d3695d5a8f721e0df250352da2ff7c608",
    str(Path(REFERENCE_JOURNAL).with_name("producer.py.snapshot")): "b20596ca480bedce126ecc97582eb7f038ac7c5f5df11c009be95b728724d8f2",
}
QUERY_METHOD = "saved_enclosure_volume_then_zero_volume_distance/v1"
SEPARATED = {"separated_by_conservative_AABB", "separated_by_exact_enclosure_query"}
REFUSED = "enclosure_overlap_requires_disposition"
INHERITED_EXTERNAL_PINS = {
    "/tmp/nds2024-ch3.pdf": "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
}
ROLES = {"shaft", "head", "head_washer", "nut", "nut_washer"}
PANEL_BODIES = {"main_lower_left", "main_lower_right", "main_upper_left", "main_upper_right", "kicker_left", "kicker_right"}
HEADINGS_DEG = (0, 90, 180, 270)
TERMINAL_MM = 1.0
FALSE = {
    "criterion_closed": False,
    "candidate_adopted": False,
    "complete_joint_acceptance": False,
    "delivered_hardware_verified": False,
    "actual_operation_observed": False,
    "harness_staging_or_refeeding_established": False,
    "physical_release": False,
    "fabrication_release": False,
    "scene_rebuilt": False,
    "native_or_frame_run": False,
    "tests_or_review_run": False,
}
# Explicit ordinary-tool design assumptions, not catalog facts or selected SKUs.
# These are much thicker than the old 3 mm micromechanics wrench proxy.
TOOLS = {
    6.35: {"nominal_hex_af_mm": 11.1125, "head_width_mm": 26.0,
           "thickness_mm": 8.0, "overall_length_mm": 150.0, "handle_width_mm": 12.0},
    7.9375: {"nominal_hex_af_mm": 12.7, "head_width_mm": 30.0,
             "thickness_mm": 9.0, "overall_length_mm": 170.0, "handle_width_mm": 14.0},
    9.525: {"nominal_hex_af_mm": 14.2875, "head_width_mm": 34.0,
            "thickness_mm": 10.0, "overall_length_mm": 180.0, "handle_width_mm": 16.0},
    12.7: {"nominal_hex_af_mm": 19.05, "head_width_mm": 42.0,
           "thickness_mm": 12.0, "overall_length_mm": 230.0, "handle_width_mm": 20.0},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def fresh_path(output):
    """Validate before reading inputs or making directories; never reuse output."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(),
            "Output must be a fresh immediate child of rawlocal/operation-envelope-completion")
    return output


def vector(values):
    out = [float(v) for v in values]
    require(len(out) == 3 and all(math.isfinite(v) for v in out), "Invalid finite vector")
    return out


def unit(values):
    values = vector(values)
    length = math.sqrt(dot(values, values))
    require(abs(length - 1.0) < 1e-8, "Expected recorded unit vector")
    return [v / length for v in values]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def advance(p, d, amount):
    return [p[i] + d[i] * amount for i in range(3)]


def box_gap(a, b):
    """Positive value certifies disjoint boxes; zero never means collision."""
    return max(max(b[2*i] - a[2*i+1], a[2*i] - b[2*i+1]) for i in range(3))


def geometry_bounds(g):
    """Conservative world AABB; tool sector uses its enclosing cylinder."""
    if g["kind"] == "saved_world_aabb":
        return list(g["bounds_xyz_mm"])
    if g["kind"] == "sweep":
        base = geometry_bounds(g["base"])
        d = vector(g["displacement_xyz_mm"])
        return [v + min(0.0, d[i//2]) if i % 2 == 0 else v + max(0.0, d[i//2])
                for i, v in enumerate(base)]
    axis = unit(g["direction_xyz"])
    start = vector(g["start_xyz_mm"])
    length = float(g["length_mm"])
    radius = float(g.get("radius_mm", g.get("outer_radius_mm", 0.0)))
    require(length > 0 and radius > 0, "Nonpositive enclosure dimension")
    end = advance(start, axis, length)
    radial = [radius * math.sqrt(max(0.0, 1 - v*v)) for v in axis]
    return [value for i in range(3)
            for value in (min(start[i], end[i])-radial[i]-1e-6,
                          max(start[i], end[i])+radial[i]+1e-6)]


def sweep(g, displacement):
    return {"kind": "sweep", "base": copy.deepcopy(g),
            "displacement_xyz_mm": vector(displacement)}


def translated(g, displacement):
    g = copy.deepcopy(g)
    if g["kind"] == "saved_world_aabb":
        g["bounds_xyz_mm"] = [v + displacement[i//2]
                              for i, v in enumerate(g["bounds_xyz_mm"])]
    else:
        g["start_xyz_mm"] = [v + displacement[i]
                             for i, v in enumerate(g["start_xyz_mm"])]
    return g


def operation_arithmetic(components, pitch_mm, *, saved_travel_mm=None,
                         saved_length_mm=None, head_washer_delta_mm=0.0,
                         captured=None, washer_hole_diameters_mm=None):
    """Pure fit/stroke arithmetic for one five-role coaxial planning stack.

    Source travel is corrected for the new shaft and outward head-washer shift.
    Without a saved receiver-extrema travel, the full shaft length is used as
    a conservative extraction bound. Neither route verifies delivered threads.
    """
    require(set(components) == ROLES, "A stack must contain exactly five roles")
    shaft = components["shaft"]
    d = unit(shaft["direction_xyz"])
    p = vector(shaft["start_xyz_mm"])
    length = float(shaft["length_mm"])
    pitch = float(pitch_mm)
    require(length > 0 and pitch > 0 and math.isfinite(pitch), "Invalid length/pitch")
    nut_start = dot([a-b for a, b in zip(components["nut"]["start_xyz_mm"], p)], d)
    washer_start = dot([a-b for a, b in zip(components["nut_washer"]["start_xyz_mm"], p)], d)
    nut_free = max(TERMINAL_MM, length - nut_start + TERMINAL_MM)
    washer_free = max(TERMINAL_MM, length - washer_start + TERMINAL_MM)
    head_washer_t = float(components["head_washer"]["length_mm"])
    if saved_travel_mm is None:
        travel = length + 2*TERMINAL_MM
        basis = "Full shaft length plus 2 mm reserves a 1 mm gap after sliding the head washer off the tip"
    else:
        require(saved_length_mm is not None, "Saved length needed for source travel join")
        travel = (float(saved_travel_mm) + length - float(saved_length_mm)
                  - float(head_washer_delta_mm) + head_washer_t + 2*TERMINAL_MM)
        basis = "Saved receiver-extrema travel + shaft delta - outward washer delta + head washer thickness + 2 mm"
    if captured:
        travel = max(travel, float(captured["headward_travel_mm"]))
    require(travel > 0 and nut_free <= travel, "Thread release exceeds bolt withdrawal")
    hole_margins = None
    if washer_hole_diameters_mm is not None:
        require(set(washer_hole_diameters_mm) == {"head_washer", "nut_washer"}, "Both washer bore diameters required")
        hole_margins = {r: (float(v) - 2*shaft["radius_mm"]) / 2 for r, v in washer_hole_diameters_mm.items()}
        require(all(math.isfinite(v) and v > 0 for v in hole_margins.values()), "Declared washer hole does not enclose nominal shaft")
    return {
        "head_to_nut_xyz": d, "underhead_xyz_mm": p,
        "shaft_length_mm": length, "pitch_mm": pitch,
        "bolt_headward_travel_mm": travel, "bolt_travel_basis": basis,
        "nut_thread_release_travel_mm": nut_free,
        "nut_thread_release_turns": nut_free / pitch,
        "nut_washer_tip_clearance_travel_mm": washer_free,
        "head_washer_slide_over_extracted_bolt_mm": length + TERMINAL_MM,
        "terminal_allowance_mm": TERMINAL_MM,
        "head_washer_tip_staging_allowance_mm": head_washer_t + 2*TERMINAL_MM,
        "captured_nut_route": captured,
        "nominal_washer_hole_radial_margins_mm": hole_margins,
        "thread_compatibility_established": False,
    }


def tool_geometry(point, outward, tool, heading, *, swing_deg=0.0, travel_mm=0.0):
    """Continuous sector enclosure of an ordinary straight box-end tool.

    A circular head plus sector contains the rectangular handle through the
    complete 30-degree stroke and axial advance, including return/reindex.
    This is an outer enclosure, not a detailed wrench or thread simulation.
    """
    outward = unit(outward)
    head_r = tool["head_width_mm"] / 2
    half_handle = tool["handle_width_mm"] / 2
    require(0 < half_handle < head_r, "Handle must fit within head width")
    angular_padding = math.degrees(math.asin(half_handle / head_r))
    return {
        "kind": "tool_sector", "start_xyz_mm": vector(point),
        "direction_xyz": outward,
        "length_mm": tool["thickness_mm"] + abs(travel_mm),
        "head_radius_mm": head_r,
        "outer_radius_mm": tool["overall_length_mm"] + half_handle,
        "heading_deg": float(heading),
        "half_angle_deg": float(swing_deg) + angular_padding,
        "continuous_enclosure": True,
        "target_hex_slot_and_shaft_bore": "intended engagement, checked separately from external fit",
    }


def make_queries(axis):
    """Pure generator: full hardware strokes, approaches, turns, counterholds."""
    identity = axis["axis_id"]
    c, a, tool = axis["components"], axis["arithmetic"], axis["tool"]
    d = a["head_to_nut_xyz"]
    headward = [-v for v in d]
    captured = a["captured_nut_route"]
    queries, pairs = [], []

    def emit(name, geometry, operation, ignore=None, side=None, heading=None):
        q = {"id": identity + "/" + name, "axis_id": identity,
             "geometry": geometry, "bounds_xyz_mm": geometry_bounds(geometry),
             "operation": operation,
             "reverse_installation_uses_same_occupancy": True,
             "own_role_dispositions": ignore or {}, "side": side, "heading_deg": heading}
        queries.append(q)
        return q["id"]

    removed = {r: "active bolt group or prerequisite removal" for r in ROLES}
    for role in ("shaft", "head", "head_washer"):
        exclusions = dict(removed)
        if captured:
            for r in ("nut", "nut_washer"):
                exclusions.pop(r)
            if role == "shaft":
                exclusions.update({"nut": "intended coaxial threaded disengagement, not a fit pass",
                                   "nut_washer": "intended shaft passage through washer bore"})
        emit("bolt_" + role, sweep(c[role], [v*a["bolt_headward_travel_mm"] for v in headward]),
             "full headward bolt withdrawal / reverse insertion", exclusions)
    if captured:
        lateral = captured["lateral_displacement_xyz_mm"]
        following = captured["following_nutward_displacement_xyz_mm"]
        for role in ("nut", "nut_washer"):
            emit(role + "_captured_lateral", sweep(c[role], lateral),
                 "captured pair lateral move after bolt removal", removed)
            emit(role + "_captured_followon", sweep(translated(c[role], lateral), following),
                 "recorded 25 mm nutward follow-on / reverse staging", removed)
    else:
        emit("nut_thread_and_removal", sweep(c["nut"], [v*a["nut_thread_release_travel_mm"] for v in d]),
             "nut turns and slides until its near face clears bolt tip",
             {"nut": "active nut", "shaft": "intended threaded engagement, not a fit pass"})
        emit("nut_washer_removal", sweep(c["nut_washer"], [v*a["nut_washer_tip_clearance_travel_mm"] for v in d]),
             "washer slides over bolt tip after nut removal",
             {"nut_washer": "active washer", "nut": "prerequisite removed nut",
              "shaft": "intended shaft passage through washer bore"})
    extracted = translated(c["head_washer"], [v*a["bolt_headward_travel_mm"] for v in headward])
    emit("head_washer_over_extracted_tip", sweep(extracted, [v*a["head_washer_slide_over_extracted_bolt_mm"] for v in d]),
         "head washer slides nutward over fully extracted bolt / reverse preassembly", removed)

    # The nut is fixed for captured routes; the head turns and translates.
    # Conventional routes keep the head fixed while the nut turns and advances.
    active_side = "head" if captured else "nut"
    tools = {}
    for side, outward in (("head", headward), ("nut", d)):
        washer = c["head_washer" if side == "head" else "nut_washer"]
        point = (c["shaft"]["start_xyz_mm"] if side == "head" else
                 advance(washer["start_xyz_mm"], washer["direction_xyz"], washer["length_mm"]))
        engage = {side: "intended tool-to-hex engagement; no thread or socket conformity pass",
                  "shaft": "intended tool opening around coaxial shaft"}
        release = a["nut_thread_release_travel_mm"] if side == active_side else 0.0
        # Approach from beyond the occupied tip/hex; no 50 mm shortcut for long tails.
        projection = max(0.0, dot([x-y for x, y in zip(advance(a["underhead_xyz_mm"], d, a["shaft_length_mm"]), point)], outward))
        approach = max(projection, release, tool["thickness_mm"]) + 25.0
        for heading in HEADINGS_DEG:
            seated = tool_geometry(point, outward, tool, heading)
            seat_id = emit(f"{side}_tool/{heading}/seated", seated, "stationary counterhold pose", engage, side, heading)
            approach_id = emit(f"{side}_tool/{heading}/approach", sweep(seated, [v*approach for v in outward]),
                               "full axial tool approach and reverse departure", engage, side, heading)
            turn_id = emit(f"{side}_tool/{heading}/turn", tool_geometry(point, outward, tool, heading,
                            swing_deg=30.0, travel_mm=release),
                           "continuous +/-30 degree indexed turn and all axial thread travel", engage, side, heading)
            tools[side, heading] = {"seated": seat_id, "approach": approach_id, "turn": turn_id}
    fixed_side = "nut" if captured else "head"
    for active_heading in HEADINGS_DEG:
        for fixed_heading in HEADINGS_DEG:
            for phase in ("approach", "turn"):
                pairs.append({"axis_id": identity, "active_heading_deg": active_heading,
                              "counterhold_heading_deg": fixed_heading, "phase": phase,
                              "first_query_id": tools[active_side, active_heading][phase],
                              "second_query_id": tools[fixed_side, fixed_heading]["seated"]})
    return queries, pairs


def _merge(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, f"Conflicting source hash: {path}")
        pins[path] = digest


def _verify(pins):
    for relative, digest in pins.items():
        path = (ROOT / relative).resolve()
        approved_external = (
            relative in INHERITED_EXTERNAL_PINS
            and path == Path(relative)
            and digest == INHERITED_EXTERNAL_PINS[relative]
        )
        require((path.is_relative_to(ROOT) or approved_external) and path.is_file() and sha(path) == digest,
                f"Frozen input mismatch: {relative}")


def prepare(output):
    """Authenticate saved inputs and publish executable queries without CAD."""
    output = fresh_path(output)
    pins = {FILES[k]: digest for k, digest in PINS.items()}
    _verify(pins)
    env, scene, manifest = (read(ROOT / FILES[k]) for k in ("envelope", "scene", "manifest"))
    receipt = read(ROOT / FILES["envelope_receipt"])
    require(receipt["output_sha256"]["envelope.json"] == PINS["envelope"], "Envelope receipt mismatch")
    require(receipt["source_pins_unchanged"], "Envelope source closure was not stable")
    _merge(pins, env["source_sha256"])
    _merge(pins, scene["source_sha256"])
    _verify(pins)
    snapshots = read(ROOT / FILES["snapshots"])
    source_paths = {}
    snapshot_root = HERE / "rawlocal/top-washer-fit/prepare-attempt02"
    for relative, entry in snapshots.items():
        path = (snapshot_root / entry["path"]).resolve()
        require(path.is_relative_to(snapshot_root / "input-snapshots"), "Snapshot escapes saved root")
        require(entry["sha256"] == pins[relative] and sha(path) == pins[relative], "Saved snapshot hash mismatch")
        source_paths[relative] = path.relative_to(ROOT).as_posix()
    existing = {row["axis_id"]: row for row in manifest["existing_bolt_axes"]}
    proposed = {row["axis_id"]: row for row in manifest["proposed_internal_bolt_axes"]}
    require(manifest["source_load_identity"] == {
        "source_climber_weight_lb": 250, "source_dynamic_factor": 2,
        "source_hold_lever_mm": 100, "source_horizontal_force_magnitude_n": 300,
    }, "Frozen proposal load identity changed")
    require(len(existing) == 104 and len(proposed) == 4 and not (existing.keys() & proposed.keys()), "104/4 axis census mismatch")
    require(len(env["components"]) == 540 and len(scene["obstacles"]) == 1041, "Saved component/scene census mismatch")
    components = {}
    for row in env["components"]:
        role_map = components.setdefault(row["axis_id"], {})
        require(row["role"] not in role_map, "Duplicate stack role")
        role_map[row["role"]] = row["geometry"]
    require(set(components) == existing.keys() | proposed.keys(), "Installed envelope axis join mismatch")
    access = {row["axis_id"]: row for name in ("access", "retained")
              for row in read(ROOT / FILES[name])["axis_operations"]}
    require(set(access) == set(existing), "104 saved movement rows do not join")
    captured = {}
    for row in read(ROOT / FILES["captured"])["axis_operations"]:
        clear = [v for v in row["lateral_then_axial_options"] if v["two_stage_cad_motion_clear"]]
        require(len(clear) == 1, "Captured route needs exactly one saved clear direction")
        captured[row["axis_id"]] = {"headward_travel_mm": row["headward_travel_mm"],
                                    **{k: clear[0][k] for k in ("lateral_displacement_xyz_mm", "following_nutward_displacement_xyz_mm")}}
    require(len(captured) == 4, "Captured-nut route count mismatch")
    axis_rows, queries, tool_pairs = [], [], []
    env_axes = {r["axis_id"]: r for r in env["axes"]}
    top_parts = read(ROOT / f"{H}/mvp-resume-2026-10-01/top-corner-hardware/hardware-inputs.json")["catalog_parts"]
    correction = read(ROOT / FILES["top_correction"])
    top_axes = {}
    for block_index, block in enumerate(correction["proposals"]):
        for axis_index, row in enumerate(block["axes"]):
            identity = row["axis_id"]
            require(identity not in top_axes and identity in existing, "Corrected top axis must name one existing identity")
            top_axes[identity] = {
                "record": row, "block": block["block"],
                "record_pointer": f"/proposals/{block_index}/axes/{axis_index}",
            }
    top_heads = {r["axis_id"]: (i, r) for i, r in enumerate(correction["straight_tool_approach_scenarios"]) if r["end"] == "head"}
    saved_top = {}
    for row in scene["obstacles"]:
        if row["category"] == "corrected_top_component":
            saved_top.setdefault(row["axis_id"], {})[row["component"]] = row["cylinder"]
    require(len(top_axes) == 8 and set(top_axes) == set(top_heads) == set(saved_top), "Eight current top station authorities must join")
    existing_indices = {r["axis_id"]: i for i, r in enumerate(manifest["existing_bolt_axes"])}
    proposed_indices = {r["axis_id"]: i for i, r in enumerate(manifest["proposed_internal_bolt_axes"])}
    for identity in sorted(components):
        c = components[identity]
        require(set(c) == ROLES, "Five installed roles required")
        shaft = c["shaft"]
        diameter = round(shaft["radius_mm"] * 2, 4)
        require(diameter in TOOLS, f"Unsupported ordinary tool diameter: {identity}")
        info = env_axes[identity]["reconstruction"]
        pitch = 25.4 / ({6.35: 20, 7.9375: 18, 9.525: 16, 12.7: 13}[diameter])
        source = existing.get(identity, proposed.get(identity))
        source_direction = source.get("axis_xyz", source.get("axis_unit_global_xyz"))
        historical_point = source.get("axis_point_xyz_mm", source.get("axis_origin_global_xyz_mm"))
        source_point = historical_point
        station_direction = source_direction
        station_scope = "original_104_station" if identity in existing else "unadopted_four_internal_ties"
        group, index = (("existing_bolt_axes", existing_indices[identity]) if identity in existing else
                        ("proposed_internal_bolt_axes", proposed_indices[identity]))
        station_authority = {"path": FILES["manifest"], "sha256": PINS["manifest"],
                             "record_pointer": f"/{group}/{index}"}
        if identity in top_axes:
            current = top_axes[identity]
            row = current["record"]
            head_index, head = top_heads[identity]
            require(math.dist(historical_point, row["old_axis_point_mm"]) < 0.005,
                    f"Historical top identity does not join correction origin: {identity}")
            require(current["block"] in source["receivers"] and diameter == row["nominal_bolt_diameter_mm"],
                    f"Current top receiver/diameter does not join: {identity}")
            require(set(saved_top[identity]) == ROLES and all(
                c[role] == {"kind": "cylinder", **saved_top[identity][role]} for role in ROLES),
                f"Current top components differ from frozen corrected scene: {identity}")
            # The old contract retains identity/provenance; its point is historical.
            # Use the literal corrected bore station and head-to-nut direction.
            source_point = row["proposed_axis_point_mm"]
            station_direction = [-v for v in head["outward_axis_xyz"]]
            station_scope = "current_top_correction_station"
            station_authority = {"path": FILES["top_correction"], "sha256": PINS["top_correction"],
                                 "record_pointer": current["record_pointer"],
                                 "direction_record_pointer": f"/straight_tool_approach_scenarios/{head_index}/outward_axis_xyz"}
        recorded_direction = unit(station_direction)
        require(abs(abs(dot(recorded_direction, unit(shaft["direction_xyz"]))) - 1.0) < 1e-8,
                f"Axis orientation does not join: {identity}")
        offset = [p - q for p, q in zip(shaft["start_xyz_mm"], source_point)]
        offset = [v - recorded_direction[i] * dot(offset, recorded_direction) for i, v in enumerate(offset)]
        require(math.sqrt(dot(offset, offset)) < 0.005, f"Axis station does not join: {identity}")
        if identity in top_axes:
            source_length, saved_travel, delta = None, None, 0.0
        elif identity in existing:
            motion = access[identity]["operations"]["head_side_bolt"]
            source_length = info.get("source_modeled_underhead_to_tip_mm", info.get("source_recorded_occupied_length_mm"))
            # Eight corrected top stacks have new endpoints, so use full length.
            saved_travel = motion["derived_travel_mm"] if source_length is not None else None
            delta = info.get("catalog_minus_source_head_washer_thickness_mm", 0.0)
            if "source_head_washer_bounds_xyz_mm" in info:
                b = info["source_head_washer_bounds_xyz_mm"]
                delta = c["head_washer"]["length_mm"] - (b[1]-b[0]-0.002)
        else:
            source_length, saved_travel, delta = None, None, 0.0
        if "catalog_stack" in info:
            washer_hole = min(info["catalog_stack"]["washer"]["inside_diameter_mm"])
        elif identity in proposed or "/rail_" in identity:
            washer_hole = 8.3058  # Saved 25.4/8.3058/2.5 mm retail/proposal hypothesis.
        else:
            washer_hole = top_parts["side_washer_uss"]["inside_diameter"]["mm"]["minimum"]
        arithmetic = operation_arithmetic(c, pitch, saved_travel_mm=saved_travel,
                                          saved_length_mm=source_length, head_washer_delta_mm=delta,
                                          captured=captured.get(identity),
                                          washer_hole_diameters_mm={r: washer_hole for r in ("head_washer", "nut_washer")})
        axis = {"axis_id": identity, "source_scope": "reviewed_104_axis" if identity in existing else "unadopted_four_internal_ties",
                "geometry_station_scope": station_scope, "station_authority": station_authority,
                "station_axis_point_xyz_mm": source_point, "station_head_to_nut_xyz": recorded_direction,
                "historical_contract_point_xyz_mm": historical_point,
                "historical_movement_station_used": identity in existing and identity not in top_axes,
                "receivers": source["receivers"], "components": c, "arithmetic": arithmetic,
                "tool": copy.deepcopy(TOOLS[diameter]),
                "tool_bound_basis": "Explicit ordinary-tool design assumption; no thin-tool concession",
                "retained_head_catalog_profile_supported": info.get("catalog_head_dimensions_supported"),
                "removal_sequence": [
                    "Support named receivers; seat counterhold, then active turning tool",
                    "Unthread with full axial travel: head moves for captured routes; nut moves otherwise",
                    "Withdraw both tools using the declared departure/approach occupancy",
                    "Capture nut and nut washer; ordinary routes slide both fully over the bolt tip",
                    "Withdraw shaft, head and head washer headward; reserve washer-tip staging thickness and 1 mm final clearance",
                    "Captured routes move nut/washer by saved lateral displacement, then saved 25 mm follow-on",
                    "Slide head washer nutward over the extracted bolt tip; keep stack identity",
                ],
                "installation_sequence": "Reverse the removal sequence in the same supported, thread-compatible model state",
                "component_limits": [r["geometry_limit"] for r in env["components"] if r["axis_id"] == identity]}
        q, t = make_queries(axis)
        axis["query_ids"] = [r["id"] for r in q]
        axis_rows.append(axis)
        queries.extend(q)
        tool_pairs.extend(t)
    # Keep the complete saved obstacle map, replacing only its hardware planning
    # envelopes with the already frozen working-order component envelopes.
    obstacles = []
    for row in scene["obstacles"]:
        if row["category"] in {"candidate_hardware", "retained_frame_bolt_roles", "corrected_top_component"}:
            continue
        obstacles.append(copy.deepcopy(row))
    for axis in axis_rows:
        for role, g in axis["components"].items():
            obstacles.append({"id": "planning_stack/" + axis["axis_id"] + "/" + role,
                              "category": "planning_hardware", "axis_id": axis["axis_id"],
                              "role": role, "geometry": g, "bounds_xyz_mm": geometry_bounds(g)})
    # STEP substitutions are saved geometry only; 104 retains its original spines.
    overrides = {r["body"]: r for r in manifest["geometry"]["STEP_overrides"]}
    for row in overrides.values():
        _merge(pins, {row["proposal_step"]["path"]: row["proposal_step"]["sha256"]})
    producer = Path(__file__).resolve().relative_to(ROOT).as_posix()
    pins[producer] = sha(__file__)
    _verify(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    data = {
        "schema": "operation_envelope_completion/v1", "status": "PREPARED_NOT_EVALUATED",
        "source_sha256": dict(sorted(pins.items())), "saved_snapshot_paths": source_paths,
        "axes": axis_rows, "queries": queries, "tool_pairs": tool_pairs,
        "obstacles": obstacles, "proposal_STEP_overrides": overrides,
        "counts": {"reviewed_axes": 104, "proposed_internal_axes": 4, "queries": len(queries),
                   "tool_pairs": len(tool_pairs), "planning_components": 540,
                   "original_station_axes": 96, "current_top_correction_axes": 8},
        "station_scope_inventory": {
            "old_104_axis_identities": sorted(existing),
            "current_top_correction_axis_ids": sorted(top_axes),
            "current_moved_top_axis_ids": sorted(k for k, v in top_axes.items() if v["record"]["axis_translation_T_mm"] != 0.0),
            "proposed_internal_tie_axis_ids": sorted(proposed),
            "scope_limit": "104 identifies the original inventory; eight named current top components use corrected planning geometry, not the historical stations/profiles",
        },
        "ordinary_tools": TOOLS, "headings_deg": HEADINGS_DEG,
        "exact_query_tool_versions": EXACT_TOOL_VERSIONS,
        "load_scope": {"250_lb_times_two": True, "signed_horizontal_N": 300,
                       "hold_lever_mm": 100, "equipment_gravity_kg": 25,
                       "force_recalculation": False, "scope_source": FILES["manifest"]},
        "stage_definitions": {
            "route_retained": "All saved panels, hold hardware, lights and harness retained; no route erased",
            "initial_frame_open": "Documented initial assembly before six panels, panel hardware, LEDs and intact harness are installed; reverse requires unobserved support and intact harness/panel staging",
            "two_wire_lower_bound": "Only the two recorded leg-bolt crossing spans omitted; this is a geometry subset, not a demonstrated service state",
        },
        "method": "AABB separation only; overlapping boxes require exact query/STEP intersections or remain undecided",
        "limits": ["Conservative tool sectors and component cylinders are not exact delivered tools or hardware",
                   "Four captured-pair follow-ons end after the saved 25 mm segment, not at a verified human staging position",
                   "Hand/support fixtures, harness flexibility, anchoring, slack and refeeding are not modeled",
                   "A supported numerical operation envelope does not close formal criteria or physical flags"],
        **FALSE,
    }
    dump(output / "setup.json", data)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    _verify(pins)
    dump(output / "receipt.json", {"source_sha256": pins, "source_unchanged": True,
                                   "output_sha256": {name: sha(output / name) for name in ("setup.json", "producer.py.snapshot")}, **FALSE})
    return output / "setup.json"


def _solid(g, cq):
    """Construct only query enclosures; STEP obstacles remain untouched."""
    kind = g["kind"]
    if kind == "saved_world_aabb":
        b = g["bounds_xyz_mm"]
        return cq.Solid.makeBox(b[1]-b[0], b[3]-b[2], b[5]-b[4], cq.Vector(b[0], b[2], b[4]))
    if kind == "sweep":
        base, displacement = g["base"], vector(g["displacement_xyz_mm"])
        if base["kind"] == "saved_world_aabb":
            return _solid({"kind": "saved_world_aabb", "bounds_xyz_mm": geometry_bounds(g)}, cq)
        axis = unit(base["direction_xyz"])
        axial = dot(axis, displacement)
        transverse = [displacement[i]-axis[i]*axial for i in range(3)]
        transverse_length = math.sqrt(dot(transverse, transverse))
        if transverse_length < 1e-8:
            moving = copy.deepcopy(base)
            moving["start_xyz_mm"] = advance(base["start_xyz_mm"], axis, min(0.0, axial))
            moving["length_mm"] += abs(axial)
            return _solid(moving, cq)
        require(kind == "sweep" and base["kind"] == "cylinder" and abs(axial) < 1e-7,
                "Only saved perpendicular captured-pair translation supports a transverse exact enclosure")
        xdir = [v/transverse_length for v in transverse]
        plane = cq.Plane(origin=cq.Vector(*base["start_xyz_mm"]), xDir=cq.Vector(*xdir), normal=cq.Vector(*axis))
        return (cq.Workplane(plane).center(transverse_length/2, 0)
                .slot2D(transverse_length+2*base["radius_mm"], 2*base["radius_mm"])
                .extrude(base["length_mm"]).val())
    axis = unit(g["direction_xyz"])
    if kind == "cylinder":
        return cq.Solid.makeCylinder(g["radius_mm"], g["length_mm"], cq.Vector(*g["start_xyz_mm"]), cq.Vector(*axis))
    require(kind == "tool_sector", "Unknown query geometry")
    seed = min(([1., 0., 0.], [0., 1., 0.], [0., 0., 1.]), key=lambda v: abs(dot(v, axis)))
    base = [seed[i]-axis[i]*dot(seed, axis) for i in range(3)]
    mag = math.sqrt(dot(base, base))
    xdir = [v/mag for v in base]
    plane = cq.Plane(origin=cq.Vector(*g["start_xyz_mm"]), xDir=cq.Vector(*xdir), normal=cq.Vector(*axis))
    angle, half = math.radians(g["heading_deg"]), math.radians(g["half_angle_deg"])
    r = g["outer_radius_mm"]
    points = [(r*math.cos(a), r*math.sin(a)) for a in (angle-half, angle, angle+half)]
    sector = (cq.Workplane(plane).moveTo(0, 0).lineTo(*points[0])
              .threePointArc(points[1], points[2]).close().extrude(g["length_mm"]).val())
    boss = cq.Solid.makeCylinder(g["head_radius_mm"], g["length_mm"], cq.Vector(*g["start_xyz_mm"]), cq.Vector(*axis))
    return sector.fuse(boss)


def run(output, setup, *, parent_owned=False, exact=False):
    """Parent-only finite screen; exact=True lazily imports saved STEP BReps.

    Non-STEP obstacles without a bound query representation remain undecided.
    Only exceptional pairs are saved; disjoint pairs have per-query counts.
    """
    require(parent_owned, "Parent owns serialized operation-envelope execution")
    output = fresh_path(output)
    setup = Path(setup).resolve()
    require(setup.name == "setup.json" and setup.parent.parent == RAW.resolve(), "Setup must be an owned prepared child")
    data = read(setup)
    require(sha(setup) == read(setup.parent / "receipt.json")["output_sha256"]["setup.json"], "Prepared setup changed")
    _verify(data["source_sha256"])
    require(data["source_sha256"][Path(__file__).resolve().relative_to(ROOT).as_posix()] == sha(__file__), "Producer changed since prepare")
    geometry_versions = {name: version(name) for name in EXACT_TOOL_VERSIONS} if exact else {}
    require(not exact or geometry_versions == data["exact_query_tool_versions"], "Saved-BRep query dependency versions differ from shared frozen lock")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    queries = {q["id"]: q for q in data["queries"]}
    axes = {a["axis_id"]: a for a in data["axes"]}
    solids, steps, exact_pairs = {}, {}, {}
    exceptions, summaries, pair_results, stage_records = [], [], [], []

    def solid(g, identity):
        if identity not in solids:
            import cadquery as cq
            solids[identity] = _solid(g, cq)
            require(solids[identity].isValid(), f"Invalid query enclosure: {identity}")
        return solids[identity]

    def compare(q, o):
        gap = box_gap(q["bounds_xyz_mm"], o["bounds_xyz_mm"])
        if gap > 0:
            return {"status": "separated_by_conservative_AABB", "box_gap_mm": gap}
        if not exact:
            return {"status": "undecided_overlapping_AABBs"}
        cache_key = (q["id"], o["id"], o.get("step_path"))
        if cache_key in exact_pairs:
            return dict(exact_pairs[cache_key])
        if "geometry" in o:
            fixed = solid(o["geometry"], o["id"])
        elif "step_path" in o:
            path = o["step_path"]
            if path not in steps:
                source = ROOT / data["saved_snapshot_paths"].get(path, path)
                require(path in data["source_sha256"] and sha(source) == data["source_sha256"][path], "Saved STEP binding changed")
                import cadquery as cq
                steps[path] = cq.importers.importStep(str(source)).val()
                require(steps[path].isValid(), f"Invalid saved STEP: {path}")
            fixed = steps[path]
        else:
            return {"status": "undecided_no_exact_saved_geometry"}
        moving = solid(q["geometry"], q["id"])
        volume, distance = float(moving.intersect(fixed).Volume()), float(moving.distance(fixed))
        require(math.isfinite(volume) and math.isfinite(distance), "Nonfinite exact intersection result")
        result = {"status": "enclosure_overlap_requires_disposition" if volume > 1e-6 else "separated_by_exact_enclosure_query",
                  "intersection_volume_mm3": volume, "distance_mm": distance,
                  "contact_at_zero_distance_is_not_a_clash": volume <= 1e-6 and distance <= 1e-6}
        exact_pairs[cache_key] = result
        return dict(result)

    for scope in ("reviewed_104", "proposal_108"):
        live = copy.deepcopy(data["obstacles"])
        if scope == "reviewed_104":
            live = [o for o in live if o.get("axis_id") not in axes or axes[o["axis_id"]]["source_scope"] == "reviewed_104_axis"]
        else:
            for o in live:
                body = o["id"].removeprefix("wood/")
                if o["category"] == "wood" and body in data["proposal_STEP_overrides"]:
                    o["step_path"] = data["proposal_STEP_overrides"][body]["proposal_step"]["path"]
        stage_removed = {stage: {} for stage in data["stage_definitions"]}
        for o in live:
            body = o["id"].removeprefix("wood/")
            if o["category"] in {"panel_screw_envelope", "tnuts", "lights", "modeled_wires"} or body in PANEL_BODIES:
                stage_removed["initial_frame_open"][o["id"]] = "not yet installed at documented initial frame assembly; reverse staging unobserved"
            if o["id"].endswith(("wire_010_A10_A11", "wire_130_K10_K11")):
                stage_removed["two_wire_lower_bound"][o["id"]] = "recorded two-span lower bound only; no physical staging pass"
        require(len(stage_removed["two_wire_lower_bound"]) == 2, "Two saved wire span IDs must join")
        stage_records.extend({"scope": scope, "stage": stage, "excluded": [
            {"obstacle_id": name, "reason": reason} for name, reason in removed.items()]}
            for stage, removed in stage_removed.items())
        for q in data["queries"]:
            axis = axes[q["axis_id"]]
            if scope == "reviewed_104" and axis["source_scope"] != "reviewed_104_axis":
                continue
            stages = ["route_retained", "initial_frame_open"]
            if axis["axis_id"].startswith("lumber_leg_bolt_"):
                stages.append("two_wire_lower_bound")
            for stage in stages:
                counts, excluded, minimum = Counter(), [], None
                for o in live:
                    if o["id"] in stage_removed[stage]:
                        continue
                    reason = None
                    if o.get("axis_id") == q["axis_id"] and o.get("role") in q["own_role_dispositions"]:
                        reason = q["own_role_dispositions"][o["role"]]
                    if reason:
                        excluded.append({"obstacle_id": o["id"], "reason": reason})
                        continue
                    result = compare(q, o)
                    counts[result["status"]] += 1
                    if "box_gap_mm" in result:
                        minimum = result["box_gap_mm"] if minimum is None else min(minimum, result["box_gap_mm"])
                    else:
                        exceptions.append({"scope": scope, "stage": stage, "query_id": q["id"], "obstacle_id": o["id"], **result})
                summaries.append({"scope": scope, "stage": stage, "query_id": q["id"], "counts": dict(counts),
                                  "minimum_positive_box_gap_mm": minimum, "own_role_dispositions": excluded,
                                  "stage_exclusion_count": len(stage_removed[stage])})
        for pair in data["tool_pairs"]:
            if scope == "reviewed_104" and axes[pair["axis_id"]]["source_scope"] != "reviewed_104_axis":
                continue
            first, second = queries[pair["first_query_id"]], queries[pair["second_query_id"]]
            pair_results.append({"scope": scope, **pair,
                                 **compare(first, {"id": second["id"], "geometry": second["geometry"], "bounds_xyz_mm": second["bounds_xyz_mm"]})})
    _verify(data["source_sha256"])
    dispositions = summarize_operations(data, summaries, pair_results)
    result = {"schema": "operation_envelope_completion_result/v1",
              "status": "FINITE_ENVELOPE_SCREEN_REQUIRES_DISPOSITION",
              "setup_sha256": sha(setup), "query_summaries": summaries,
              "exception_pairs": exceptions, "counterhold_pairs": pair_results,
              "operation_dispositions": dispositions, "stage_exclusions": stage_records,
              "exception_status_counts": dict(Counter(r["status"] for r in exceptions)),
              "exact_saved_BRep_queries_executed": exact,
              "geometry_tool_versions": geometry_versions,
              "CAD_scene_replayed": False, "stage_definitions": data["stage_definitions"], **FALSE}
    result["station_scope_inventory"] = data["station_scope_inventory"]
    dump(output / "result.json", result)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    _verify(data["source_sha256"])
    dump(output / "receipt.json", {"source_sha256": data["source_sha256"], "source_unchanged": True,
                                   "output_sha256": {n: sha(output / n) for n in ("result.json", "producer.py.snapshot")}, **FALSE})
    return output / "result.json"


def summarize_operations(data, summaries, pair_results):
    """Pure same-state join; a tool pair needs scene access and counterhold."""
    supported = {"separated_by_conservative_AABB", "separated_by_exact_enclosure_query"}
    by_query = {(r["scope"], r["stage"], r["query_id"]): r for r in summaries}
    by_pair = {(r["scope"], r["axis_id"], r["active_heading_deg"], r["counterhold_heading_deg"], r["phase"]): r
               for r in pair_results}
    result = []
    for scope in ("reviewed_104", "proposal_108"):
        for axis in data["axes"]:
            identity = axis["axis_id"]
            if scope == "reviewed_104" and axis["source_scope"] != "reviewed_104_axis":
                continue
            for stage in data["stage_definitions"]:
                if (scope, stage, axis["query_ids"][0]) not in by_query:
                    continue

                def clear(qid, scope=scope, stage=stage):
                    row = by_query[scope, stage, qid]
                    return set(row["counts"]) <= supported

                hardware = [q for q in axis["query_ids"] if "_tool/" not in q]
                active = "head" if axis["arithmetic"]["captured_nut_route"] else "nut"
                fixed = "nut" if active == "head" else "head"
                alternatives = []
                for ah in HEADINGS_DEG:
                    for fh in HEADINGS_DEG:
                        needed = [f"{identity}/{side}_tool/{heading}/{phase}" for side, heading, phase in (
                            (fixed, fh, "approach"), (fixed, fh, "seated"),
                            (active, ah, "approach"), (active, ah, "turn"))]
                        pairs = [by_pair[scope, identity, ah, fh, phase] for phase in ("approach", "turn")]
                        alternatives.append({"active_heading_deg": ah, "counterhold_heading_deg": fh,
                                             "scene_queries_separated": all(clear(q) for q in needed),
                                             "tools_separated": all(r["status"] in supported for r in pairs)})
                result.append({"scope": scope, "stage": stage, "axis_id": identity,
                               "geometry_station_scope": axis["geometry_station_scope"],
                               "hardware_stroke_enclosures_separated": all(clear(q) for q in hardware),
                               "counterhold_alternatives": alternatives,
                               "modeled_tool_route_available": any(r["scene_queries_separated"] and r["tools_separated"] for r in alternatives),
                               "comparison_is_qualification": False, **FALSE})
    return result


def build(output, setup, *, parent_owned=False, exact=False):
    """Explicit alias for the parent-owned finite run; never runs on import."""
    return run(output, setup, parent_owned=parent_owned, exact=exact)


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _continuation_inputs():
    """Read authenticated historical output; do not repin its producer path."""
    _verify(CONTINUATION_PINS)
    data, aabb = read(ROOT / ORIGIN_SETUP), read(ROOT / AABB_RESULT)
    origin_receipt = read((ROOT / ORIGIN_SETUP).with_name("receipt.json"))
    aabb_receipt = read((ROOT / AABB_RESULT).with_name("receipt.json"))
    producer_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    require(data["source_sha256"][producer_path] == ORIGIN_PRODUCER, "Unexpected historical producer")
    require(len(data["source_sha256"]) == 622 and
            data["source_sha256"] == origin_receipt["source_sha256"] == aabb_receipt["source_sha256"],
            "Historical source closures differ")
    require(origin_receipt["output_sha256"]["setup.json"] == CONTINUATION_PINS[ORIGIN_SETUP] and
            origin_receipt["output_sha256"]["producer.py.snapshot"] == ORIGIN_PRODUCER and
            aabb_receipt["output_sha256"]["result.json"] == CONTINUATION_PINS[AABB_RESULT] and
            aabb_receipt["output_sha256"]["producer.py.snapshot"] == ORIGIN_PRODUCER,
            "Historical receipt bindings differ")
    require(origin_receipt["source_unchanged"] and aabb_receipt["source_unchanged"] and
            not aabb["exact_saved_BRep_queries_executed"] and
            aabb["setup_sha256"] == CONTINUATION_PINS[ORIGIN_SETUP], "Not the frozen AABB phase")
    _verify({p: h for p, h in data["source_sha256"].items() if p != producer_path})
    return data, aabb


def make_continuation_plan(data, aabb):
    """Pure source join: reuse candidate pairs, without another AABB screen."""
    require((len(aabb["query_summaries"]), len(aabb["exception_pairs"]),
             len(aabb["counterhold_pairs"]), len(aabb["operation_dispositions"])) ==
            (12992, 156204, 6784, 432), "Frozen AABB census differs")
    queries = {q["id"]: q for q in data["queries"]}
    axes = {a["axis_id"]: a for a in data["axes"]}
    obstacles = {o["id"]: o for o in data["obstacles"]}
    exceptions = {}
    for row in aabb["exception_pairs"]:
        require(row["status"] == "undecided_overlapping_AABBs", "Not an AABB candidate")
        exceptions.setdefault((row["scope"], row["stage"], row["query_id"]), []).append(row["obstacle_id"])
    summaries = {(r["scope"], r["stage"], r["query_id"]): r for r in aabb["query_summaries"]}
    tasks, nodes, routes, fixed_geometries = {}, {}, [], {}

    def task(qid, obstacle):
        fixed = ({"geometry": obstacle["geometry"]} if "geometry" in obstacle else
                 {"step_path": obstacle["step_path"], "step_sha256": data["source_sha256"][obstacle["step_path"]]}
                 if "step_path" in obstacle else {"unsupported_obstacle_id": obstacle["id"]})
        key = content_hash({"moving_geometry": queries[qid]["geometry"], "fixed": fixed,
                            "query_method": QUERY_METHOD, "versions": data["exact_query_tool_versions"]})
        if "geometry" in fixed:
            geometry_key = content_hash(fixed["geometry"])
            fixed_geometries.setdefault(geometry_key, fixed["geometry"])
            fixed = {"geometry_key": geometry_key}
        tasks.setdefault(key, {"query_id": qid, "obstacle_id": obstacle["id"], **fixed})
        return key

    def scene_node(scope, stage, qid):
        key = content_hash([scope, stage, qid])
        if key in nodes:
            return key
        summary = summaries[scope, stage, qid]
        candidates = exceptions.get((scope, stage, qid), [])
        require(summary["counts"].get("undecided_overlapping_AABBs", 0) == len(candidates) and
                set(summary["counts"]) <= {"undecided_overlapping_AABBs", "separated_by_conservative_AABB"},
                "Candidate/summary join differs")
        keys = []
        for oid in candidates:
            obstacle = dict(obstacles[oid])
            body = oid.removeprefix("wood/")
            if scope == "proposal_108" and obstacle["category"] == "wood" and body in data["proposal_STEP_overrides"]:
                obstacle["step_path"] = data["proposal_STEP_overrides"][body]["proposal_step"]["path"]
            keys.append(task(qid, obstacle))
        nodes[key] = {"scope": scope, "stage": stage, "query_id": qid,
                      "aabb_summary": {k: summary[k] for k in ("counts", "minimum_positive_box_gap_mm", "stage_exclusion_count")},
                      "own_role_dispositions_source": "same named summary in frozen AABB result",
                      "task_keys": list(dict.fromkeys(keys))}
        return key

    pair_nodes = {}
    for row in aabb["counterhold_pairs"]:
        key = content_hash([row["scope"], row["axis_id"], row["active_heading_deg"], row["counterhold_heading_deg"], row["phase"]])
        keys = []
        if row["status"] not in SEPARATED:
            require(row["status"] == "undecided_overlapping_AABBs", "Unexpected counterhold result")
            fixed = queries[row["second_query_id"]]
            keys.append(task(row["first_query_id"], {"id": fixed["id"], "geometry": fixed["geometry"]}))
        nodes[key] = {"counterhold_record": row, "task_keys": keys}
        pair_nodes[row["scope"], row["axis_id"], row["active_heading_deg"], row["counterhold_heading_deg"], row["phase"]] = key

    def required(nodes_needed):
        return {k for node in nodes_needed for k in nodes[node]["task_keys"]}

    def cost(keys):
        return (sum("unsupported_obstacle_id" in tasks[k] for k in keys), len(keys))

    for disposition in aabb["operation_dispositions"]:
        identity, scope, stage = (disposition[k] for k in ("axis_id", "scope", "stage"))
        axis = axes[identity]
        hardware = [scene_node(scope, stage, q) for q in axis["query_ids"] if "_tool/" not in q]
        active = "head" if axis["arithmetic"]["captured_nut_route"] else "nut"
        fixed = "nut" if active == "head" else "head"
        alternatives = []
        for ah in HEADINGS_DEG:
            for fh in HEADINGS_DEG:
                needed = [scene_node(scope, stage, f"{identity}/{side}_tool/{heading}/{phase}")
                          for side, heading, phase in ((fixed, fh, "approach"), (fixed, fh, "seated"),
                                                     (active, ah, "approach"), (active, ah, "turn"))]
                needed += [pair_nodes[scope, identity, ah, fh, phase] for phase in ("approach", "turn")]
                keys = required(hardware + needed)
                alternatives.append({"active_heading_deg": ah, "counterhold_heading_deg": fh,
                                     "node_ids": needed, "candidate_cost": list(cost(keys))})
        alternatives.sort(key=lambda a: (a["candidate_cost"], a["active_heading_deg"], a["counterhold_heading_deg"]))
        routes.append({"scope": scope, "stage": stage, "axis_id": identity,
                       "geometry_station_scope": axis["geometry_station_scope"],
                       "hardware_node_ids": hardware, "alternatives": alternatives})
    routes.sort(key=lambda r: (r["alternatives"][0]["candidate_cost"], r["stage"] != "initial_frame_open",
                               r["scope"] != "reviewed_104", r["axis_id"], r["stage"]))
    hardware_keys = required([n for r in routes for n in r["hardware_node_ids"]])
    first_keys = required([n for r in routes for n in r["hardware_node_ids"] + r["alternatives"][0]["node_ids"]])
    census = {
        "route_slots": len(routes), "unique_candidate_tasks": len(tasks),
        "unique_hardware_candidate_tasks": len(hardware_keys),
        "first_alternative_unique_candidate_tasks": len(first_keys),
        "unsupported_candidate_tasks": sum("unsupported_obstacle_id" in t for t in tasks.values()),
        "route_slots_with_all_geometry_represented": dict(Counter(r["stage"] for r in routes if r["alternatives"][0]["candidate_cost"][0] == 0)),
        "route_slots_with_unrepresented_geometry_in_every_alternative": dict(Counter(r["stage"] for r in routes if r["alternatives"][0]["candidate_cost"][0] > 0)),
        "first_route": {k: routes[0][k] for k in ("scope", "stage", "axis_id")},
        "first_route_candidate_cost": routes[0]["alternatives"][0]["candidate_cost"],
    }
    return {"tasks": tasks, "nodes": nodes, "routes": routes,
            "fixed_geometries": fixed_geometries, "candidate_census": census}


def prepare_continuation(output, *, reuse_journals=()):
    """Stdlib-only plan publication from the authenticated cheap parent result."""
    output = fresh_path(output)
    data, aabb = _continuation_inputs()
    producer = Path(__file__).resolve().relative_to(ROOT).as_posix()
    pins = {producer: sha(__file__), **CONTINUATION_PINS}
    for journal in reuse_journals:
        journal = Path(journal).resolve()
        require(journal.parent.parent == RAW.resolve() and journal.name == "journal.jsonl" and journal.is_file(),
                "Reuse only a preserved owned continuation journal")
        relative = journal.relative_to(ROOT).as_posix()
        pins[relative] = sha(journal)
        if relative == REFERENCE_JOURNAL:
            _verify(REFERENCE_RUN_PINS)
            _merge(pins, REFERENCE_RUN_PINS)
    plan = {"schema": "operation_envelope_route_first_plan/v1", "origin_setup_path": ORIGIN_SETUP,
            "origin_setup_sha256": CONTINUATION_PINS[ORIGIN_SETUP], "aabb_result_path": AABB_RESULT,
            "aabb_result_sha256": CONTINUATION_PINS[AABB_RESULT], "query_method": QUERY_METHOD,
            "producer_sha256": pins[producer], "source_sha256": pins,
            "inherited_source_sha256": data["source_sha256"],
            "reuse_journals": [Path(p).resolve().relative_to(ROOT).as_posix() for p in reuse_journals],
            "budgets": {"max_seconds": 270.0, "max_exact_pairs": 64, "max_pair_seconds": 15.0},
            "load_scope": data["load_scope"],
            "stage_definitions": data["stage_definitions"], "station_scope_inventory": data["station_scope_inventory"],
            **make_continuation_plan(data, aabb), **FALSE}
    plan["budgets"]["max_exact_pairs_ceiling"] = (plan["candidate_census"]["unique_candidate_tasks"]
                                                - plan["candidate_census"]["unsupported_candidate_tasks"])
    _reused_results(plan)  # Authenticate requested cache compatibility before publication.
    _verify(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    dump(output / "continuation-plan.json", plan)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    _verify(pins)
    dump(output / "receipt.json", {"source_sha256": pins, "source_unchanged": True,
                                   "output_sha256": {n: sha(output / n) for n in ("continuation-plan.json", "producer.py.snapshot")},
                                   "origin_source_pin_count": 622, **FALSE})
    return output / "continuation-plan.json"


def _cache_binding(plan):
    return {k: plan[k] for k in ("producer_sha256", "origin_setup_sha256", "aabb_result_sha256", "query_method")}


def _validate_pair_result(result):
    status = result["status"]
    if status in {REFUSED, "separated_by_exact_enclosure_query"}:
        volume = result["intersection_volume_mm3"]
        require(math.isfinite(volume) and volume >= 0 and (volume > 1e-6) == (status == REFUSED),
                "Exact status/volume differs")
        if status != REFUSED:
            require(math.isfinite(result["distance_mm"]) and result["distance_mm"] >= 0, "Invalid exact distance")
    else:
        require(status.startswith("undecided_"), "Unexpected native/cache status")
    return result


def _exact_method_fingerprint(path):
    """Source identity for the unchanged kernel, geometry recipes and fit helpers."""
    names = {"require", "sha", "read", "vector", "unit", "dot", "advance", "_solid", "content_hash",
             "make_continuation_plan", "_ExactWorker", "_exact_worker", "_validate_pair_result",
             "EXACT_TOOL_VERSIONS", "QUERY_METHOD", "SEPARATED", "REFUSED"}
    selected = []
    for node in ast.parse(Path(path).read_text(encoding="utf-8")).body:
        node_names = ({node.name} if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else
                      {t.id for t in node.targets if isinstance(t, ast.Name)} if isinstance(node, ast.Assign) else set())
        if node_names & names:
            selected.append(node)
    require(len(selected) == len(names), "Incomplete exact-method source fingerprint")
    return content_hash([ast.dump(node, include_attributes=False) for node in selected])


def _reused_results(plan):
    cache = {}
    for relative in plan["reuse_journals"]:
        lines = (ROOT / relative).read_bytes().splitlines(keepends=True)
        begun, finished = set(), set()
        require(lines, "Empty prior journal")
        header = json.loads(lines[0])
        require(header["event"] == "binding", "Prior journal has no binding")
        binding = header["binding"]
        if binding != _cache_binding(plan):
            reference_source = str(Path(REFERENCE_JOURNAL).with_name("producer.py.snapshot"))
            require(relative == REFERENCE_JOURNAL and
                    binding["producer_sha256"] == REFERENCE_RUN_PINS[reference_source] and
                    plan["source_sha256"].get(relative) == REFERENCE_RUN_PINS[relative] and
                    {**binding, "producer_sha256": plan["producer_sha256"]} == _cache_binding(plan),
                    "Prior journal method/source differs")
            _verify(REFERENCE_RUN_PINS)
            require(_exact_method_fingerprint(ROOT / reference_source) == _exact_method_fingerprint(__file__),
                    "Reference journal exact method changed")
        for line in lines[1:]:
            if not line.endswith(b"\n"):
                break  # An interrupted final append remains unknown; preserve its original bytes.
            row = json.loads(line)
            if row["event"] == "pair_begin":
                begun.add(row["key"])
            elif row["event"] == "pair_finish":
                key, result = row["key"], _validate_pair_result(row["result"])
                require(key in begun and key in plan["tasks"], "Prior finish has no bound start/task")
                require(key not in cache or cache[key] == result, "Conflicting prior pair results")
                cache[key] = result
                finished.add(key)
        for key in begun - finished:
            cache.setdefault(key, {"status": "undecided_interrupted_previous_query"})
    return cache


class _ExactWorker:
    """One serialized native process, with reusable shapes and a bounded request."""

    def __init__(self, plan_path, stderr):
        self.process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()),
                                         "--parent-owned", "--exact-worker", "--plan", str(plan_path),
                                         "--worker-plan-sha256", sha(plan_path)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        self.buffer = b""

    def receive(self, seconds):
        deadline = time.monotonic() + seconds
        while b"\n" not in self.buffer:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.process.stdout], [], [], max(0, left))[0]:
                raise TimeoutError("Serialized saved-BRep query exceeded its bounded request")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError(f"Saved-BRep worker exited {self.process.poll()}")
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b"\n", 1)
        return json.loads(line)

    def compare(self, key, seconds):
        self.process.stdin.write((json.dumps({"key": key}) + "\n").encode())
        self.process.stdin.flush()
        row = self.receive(seconds)
        require(row["key"] == key, "Worker response/task differs")
        return _validate_pair_result(row["result"])

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()


def _exact_worker(plan_path, plan_hash, *, parent_owned=False):
    """Private child of parent run_continuation; never creates scene parts."""
    require(parent_owned and sha(plan_path) == plan_hash, "Worker needs a bound parent plan")
    plan = read(plan_path)
    require(plan["producer_sha256"] == sha(__file__), "Worker producer differs")
    data = read(ROOT / plan["origin_setup_path"])
    require(sha(ROOT / plan["origin_setup_path"]) == plan["origin_setup_sha256"], "Worker setup differs")
    require({n: version(n) for n in EXACT_TOOL_VERSIONS} == data["exact_query_tool_versions"], "Worker versions differ")
    import cadquery as cq
    queries = {q["id"]: q for q in data["queries"]}
    shapes, steps = {}, {}

    def solid(g):
        key = content_hash(g)
        if key not in shapes:
            shapes[key] = _solid(g, cq)
            require(shapes[key].isValid(), "Invalid frozen query enclosure")
        return shapes[key]

    print(json.dumps({"ready": True}), flush=True)
    for line in sys.stdin:
        key = json.loads(line)["key"]
        try:
            task = plan["tasks"][key]
            moving = solid(queries[task["query_id"]]["geometry"])
            if "geometry_key" in task:
                fixed = solid(plan["fixed_geometries"][task["geometry_key"]])
            else:
                path = task["step_path"]
                if path not in steps:
                    source = ROOT / data["saved_snapshot_paths"].get(path, path)
                    require(data["source_sha256"][path] == task["step_sha256"] and sha(source) == task["step_sha256"],
                            "Saved STEP binding changed")
                    steps[path] = cq.importers.importStep(str(source)).val()
                    require(steps[path].isValid(), "Invalid saved STEP")
                fixed = steps[path]
            volume = float(moving.intersect(fixed).Volume())
            require(math.isfinite(volume) and volume >= 0, "Nonfinite/negative exact volume")
            result = {"status": REFUSED if volume > 1e-6 else "separated_by_exact_enclosure_query",
                      "intersection_volume_mm3": volume}
            if volume <= 1e-6:
                distance = float(moving.distance(fixed))
                require(math.isfinite(distance) and distance >= 0, "Nonfinite/negative exact distance")
                result.update(distance_mm=distance, contact_at_zero_distance_is_not_a_clash=distance <= 1e-6)
        except Exception as error:  # noqa: BLE001 - Third-party BRep failures remain undecided.
            result = {"status": "undecided_exact_query_error", "error": str(error)[:1000]}
        print(json.dumps({"key": key, "result": result}, allow_nan=False), flush=True)


def run_continuation(output, plan, *, parent_owned=False, max_seconds=270.0,
                     max_exact_pairs=64, max_pair_seconds=15.0):
    """Parent-only route search; native calls journaled and individually bounded."""
    started = time.monotonic()
    require(parent_owned, "Parent owns serialized saved-BRep execution")
    require(0 < max_seconds <= 270 and 0 < max_exact_pairs and int(max_exact_pairs) == max_exact_pairs and
            0 < max_pair_seconds <= 15, "Continuation must stay within the unchanged 300-second parent cap")
    output = fresh_path(output)
    plan_path = Path(plan).resolve()
    require(plan_path.parent.parent == RAW.resolve() and plan_path.name == "continuation-plan.json", "Use an owned continuation plan")
    plan = read(plan_path)
    require(max_exact_pairs <= plan["candidate_census"]["unique_candidate_tasks"]
            - plan["candidate_census"]["unsupported_candidate_tasks"], "Count exceeds the finite prepared exact candidate graph")
    require(sha(plan_path) == read(plan_path.with_name("receipt.json"))["output_sha256"][plan_path.name], "Continuation plan changed")
    require(plan["producer_sha256"] == sha(__file__) and plan["query_method"] == QUERY_METHOD, "Continuation producer/method changed")
    _verify(plan["source_sha256"])
    data, _ = _continuation_inputs()
    require(data["source_sha256"] == plan["inherited_source_sha256"], "Inherited closure changed")
    require({n: version(n) for n in EXACT_TOOL_VERSIONS} == data["exact_query_tool_versions"], "Saved-BRep versions differ")
    cache = _reused_results(plan)
    reused_count = len(cache)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    worker, executed, node_results, dispositions = None, 0, {}, []
    engine_stop = None
    deadline = started + max_seconds
    with (output / "journal.jsonl").open("x", encoding="utf-8") as journal, (output / "worker-stderr.log").open("xb") as stderr:
        def record(event, **fields):
            row = {"event": event, "elapsed_seconds": time.monotonic() - started, **fields}
            journal.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            journal.flush()
            os.fsync(journal.fileno())

        record("binding", binding=_cache_binding(plan), plan_sha256=sha(plan_path),
               budgets={"max_seconds": max_seconds, "max_exact_pairs": max_exact_pairs, "max_pair_seconds": max_pair_seconds})

        def compare(key):
            nonlocal worker, executed, engine_stop
            if key in cache:
                return cache[key]
            task = plan["tasks"][key]
            if "unsupported_obstacle_id" in task:
                return {"status": "undecided_no_exact_saved_geometry"}
            if engine_stop is not None:
                return engine_stop
            if executed >= max_exact_pairs or time.monotonic() >= deadline:
                return {"status": "undecided_execution_budget"}
            if worker is None:
                record("engine_begin")
                worker = _ExactWorker(plan_path, stderr)
                try:
                    require(worker.receive(min(15.0, max(0.001, deadline-time.monotonic()))).get("ready"), "No engine handshake")
                except (OSError, RuntimeError, ValueError, KeyError) as error:
                    worker.close()
                    worker = None
                    # A startup STOP is not retried blindly for every candidate.
                    record("engine_stop", error=str(error)[:1000])
                    engine_stop = {"status": "undecided_exact_engine_start", "error": str(error)[:1000]}
                    return engine_stop
                record("engine_ready")
            if time.monotonic() >= deadline:
                return {"status": "undecided_execution_budget"}
            executed += 1
            record("pair_begin", key=key, query_id=task["query_id"], obstacle_id=task["obstacle_id"])
            pair_start = time.monotonic()
            try:
                result = worker.compare(key, min(max_pair_seconds, max(0.001, deadline-pair_start)))
            except (OSError, RuntimeError, ValueError, KeyError) as error:
                result = {"status": "undecided_exact_query_timeout" if isinstance(error, TimeoutError) else "undecided_exact_worker_stop",
                          "error": str(error)[:1000]}
                worker.close()
                worker = None
            cache[key] = result
            record("pair_finish", key=key, result=result, query_seconds=time.monotonic()-pair_start)
            print(json.dumps({"event": "pair_finish", "count": executed, "status": result["status"],
                              "elapsed_seconds": time.monotonic()-started}), flush=True)
            return result

        def check(node_id):
            if node_id in node_results:
                return node_results[node_id]
            keys = plan["nodes"][node_id]["task_keys"]
            keys = sorted(keys, key=lambda k: ("unsupported_obstacle_id" not in plan["tasks"][k],
                                              k not in cache, "step_path" in plan["tasks"][k], k))
            checked = []
            for key in keys:
                result = compare(key)
                checked.append({"key": key, **result})
                if result["status"] not in SEPARATED:
                    break
            status = REFUSED if any(r["status"] == REFUSED for r in checked) else (
                "separated" if len(checked) == len(keys) and all(r["status"] in SEPARATED for r in checked) else "undecided")
            node_results[node_id] = {"status": status, "checked_pairs": checked,
                                     "unexamined_task_keys": [k for k in keys if k not in {r["key"] for r in checked}]}
            return node_results[node_id]

        def group(node_ids):
            for node_id in sorted(node_ids, key=lambda n: (len(plan["nodes"][n]["task_keys"]), n)):
                result = check(node_id)
                if result["status"] != "separated":
                    return result["status"], node_id
            return "separated", None

        try:
            for route in plan["routes"]:
                alternatives, selected = [], None
                if route["alternatives"][0]["candidate_cost"][0] > 0:
                    state, witness = "undecided", None
                    for alternative in route["alternatives"]:
                        unsupported = [n for n in alternative["node_ids"] if any(
                            "unsupported_obstacle_id" in plan["tasks"][k] for k in plan["nodes"][n]["task_keys"])]
                        outcome, witness = group(unsupported)
                        alternatives.append({"active_heading_deg": alternative["active_heading_deg"],
                                             "counterhold_heading_deg": alternative["counterhold_heading_deg"],
                                             "status": outcome, "witness_node_id": witness})
                else:
                    state, witness = group(route["hardware_node_ids"])
                if state == "separated":
                    for alternative in route["alternatives"]:
                        # Missing exact geometry already defeats proof of this alternative.
                        unsupported = [n for n in alternative["node_ids"] if any(
                            "unsupported_obstacle_id" in plan["tasks"][k] for k in plan["nodes"][n]["task_keys"])]
                        outcome, witness = group(unsupported or alternative["node_ids"])
                        alternatives.append({"active_heading_deg": alternative["active_heading_deg"],
                                             "counterhold_heading_deg": alternative["counterhold_heading_deg"],
                                             "status": outcome, "witness_node_id": witness})
                        if outcome == "separated":
                            selected = alternative
                            break
                    state = "separated" if selected else (REFUSED if all(a["status"] == REFUSED for a in alternatives) else "undecided")
                disposition = {k: route[k] for k in ("scope", "stage", "axis_id", "geometry_station_scope")}
                disposition.update(status="one_complete_modeled_route" if selected else state,
                                   modeled_complete_route_available=selected is not None,
                                   selected_alternative=selected, examined_alternatives=alternatives,
                                   hardware_node_ids=route["hardware_node_ids"], witness_node_id=witness,
                                   unexamined_alternative_count=len(route["alternatives"])-len(alternatives), **FALSE)
                dispositions.append(disposition)
                record("route_disposition", disposition=disposition)
        finally:
            if worker is not None:
                worker.close()
        record("execution_end", exact_pairs_executed=executed)
    _verify(plan["source_sha256"])
    producer_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    _verify({p: h for p, h in plan["inherited_source_sha256"].items() if p != producer_path})
    result = {"schema": "operation_envelope_route_first_result/v1",
              "status": "BOUNDED_ROUTE_FIRST_RESULTS_REQUIRES_DISPOSITION",
              "plan_sha256": sha(plan_path), "binding": _cache_binding(plan),
              "candidate_census": plan["candidate_census"], "operation_dispositions": dispositions,
              "checked_nodes": node_results, "pair_results": cache,
              "route_status_counts": dict(Counter(d["status"] for d in dispositions)),
              "exact_pairs_executed": executed, "reused_pair_results": reused_count,
              "elapsed_seconds": time.monotonic()-started, "budgets": {"max_seconds": max_seconds,
              "max_exact_pairs": max_exact_pairs, "max_pair_seconds": max_pair_seconds},
              "geometry_tool_versions": data["exact_query_tool_versions"],
              "load_scope": data["load_scope"],
              "stage_definitions": plan["stage_definitions"], "station_scope_inventory": plan["station_scope_inventory"],
              "CAD_scene_replayed": False, **FALSE}
    dump(output / "result.json", result)
    dump(output / "receipt.json", {"source_sha256": plan["source_sha256"], "inherited_source_sha256": plan["inherited_source_sha256"],
                                   "source_unchanged": True, "plan_sha256": sha(plan_path),
                                   "output_sha256": {n: sha(output / n) for n in ("result.json", "journal.jsonl", "producer.py.snapshot", "worker-stderr.log")}, **FALSE})
    return output / "result.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--prepare-continuation", action="store_true")
    modes.add_argument("--run-continuation", action="store_true")
    modes.add_argument("--exact-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--setup", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--reuse-journal", action="append", type=Path, default=[])
    parser.add_argument("--max-seconds", type=float, default=270.0)
    parser.add_argument("--max-exact-pairs", type=int, default=64)
    parser.add_argument("--max-pair-seconds", type=float, default=15.0)
    parser.add_argument("--worker-plan-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--parent-owned", action="store_true")
    parser.add_argument("--exact", action="store_true")
    args = parser.parse_args()
    if args.exact_worker:
        require(args.plan is not None and args.worker_plan_sha256 is not None, "Worker needs its bound parent plan")
        _exact_worker(args.plan, args.worker_plan_sha256, parent_owned=args.parent_owned)
        return
    require(args.output is not None, "Publication needs a fresh --output")
    if args.prepare_continuation:
        path = prepare_continuation(args.output, reuse_journals=args.reuse_journal)
    elif args.run_continuation:
        require(args.plan is not None and args.parent_owned and args.exact, "Continuation needs --plan --parent-owned --exact")
        path = run_continuation(args.output, args.plan, parent_owned=args.parent_owned,
                                max_seconds=args.max_seconds, max_exact_pairs=args.max_exact_pairs,
                                max_pair_seconds=args.max_pair_seconds)
    elif args.run:
        require(args.setup is not None, "--run needs --setup")
        path = run(args.output, args.setup, parent_owned=args.parent_owned, exact=args.exact)
    else:
        path = prepare(args.output)
    print(json.dumps({"path": str(path), "sha256": sha(path)}))


if __name__ == "__main__":
    main()
