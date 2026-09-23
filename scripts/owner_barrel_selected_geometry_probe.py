"""Reproduce selected barrel shifts and bolt-tip bore corrections in CAD.

This is a nominal geometry screen.  It cannot qualify delivered tolerances,
thread engagement, wood resistance, joint stiffness, or structural response.
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import cadquery as cq

from scripts import owner_barrel_rail_layout as rail
from scripts import owner_barrel_selected_hardware as selected
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "owner_barrel_selected_geometry_probe/v1"
TARGET_TIP_CLEARANCE_MM = 2.0
HIT_TOL_MM3 = 1.0
CONTAINMENT_TOL_MM3 = 0.01
EXPECTED_BARREL_PAIRS = 46
EXPECTED_RAIL_PAIRS = 12
EXPECTED_TOP_OUTER_PAIRS = 4
TOP_OUTER_STATIONS = frozenset(
    {"clip_single_top_left_1", "clip_single_top_right_2"}
)


def _rounded(value, digits=6):
    return round(float(value), digits)


def _cylinder(start, direction, length, diameter):
    return cq.Solid.makeCylinder(diameter / 2, length, start, direction)


def _far_point(shape, line_point, direction):
    """Return far cap centre along a known cylinder centreline."""
    direction = direction.normalized()
    far = max(vertex.Center().dot(direction) for vertex in shape.Vertices())
    return line_point + direction * (far - line_point.dot(direction))


def _outside_volume(shape, host):
    return max(0.0, shape.Volume() - protected._volume(shape, host))


def _hits(shape, others, *, excluded=frozenset()):
    return {
        name: _rounded(volume)
        for name, other in others.items()
        if name not in excluded
        and (volume := protected._volume(shape, other)) > HIT_TOL_MM3
    }


def _protected_hits(name, shape, inventory):
    return {
        family: rows
        for family, rows in protected.hits({name: shape}, inventory)[name].items()
        if rows
    }


def _host_for(shape, assembly, candidates):
    rows = sorted(
        (
            (protected._volume(shape, assembly["wood"][member]), member)
            for member in candidates
        ),
        reverse=True,
    )
    if not rows or rows[0][0] <= HIT_TOL_MM3:
        raise ValueError("Selected geometry has no intended timber host")
    return rows[0][1]


def _selected_bolt(data, modeled_length_mm):
    product, _ = selected.SELECTED_BOLT_BY_MODELED_LENGTH[
        round(float(modeled_length_mm), 1)
    ]
    return next(row for row in data["bolts"] if row["product"] == product)


def _barrel_changes(assembly, data):
    current_axis = assembly["hardware_basis"]["axis_offset_mm_provisional"]
    chosen = data["barrel"]
    shift = current_axis - chosen["nominal_thread_axis_from_slotted_end_mm"]
    if shift <= 0:
        raise ValueError("Selected barrel shift must remain positive")
    inventory = protected.inventory()
    shifted, prepared = {}, []
    for name, body in sorted(assembly["barrels"].items()):
        bolt_name = f"{name}_bolt"
        bolt = assembly["bolts"][bolt_name]
        access_names = [
            path
            for path in assembly["access_paths"]
            if path.startswith(f"{name}/")
            and path.rsplit("/", 1)[1] in ("barrel_access", "barrel_tool")
        ]
        if len(access_names) != 1:
            raise ValueError(f"{name}: expected one barrel insertion access path")
        access = assembly["access_paths"][access_names[0]]
        direction = (body.Center() - access.Center()).normalized()
        moved = body.translate(direction * shift)
        old_end = body.Center() + direction * (chosen["nominal_body_length_mm"] / 2)
        insertion_entry = _far_point(access, body.Center(), direction)
        tail = _cylinder(
            old_end,
            direction,
            shift,
            chosen["nominal_body_od_mm"],
        )
        host = _host_for(body, assembly, bolt.members)
        unrelated = {
            member: shape
            for member, shape in assembly["wood"].items()
            if member != host
        }
        shifted[name] = moved
        prepared.append(
            {
                "name": name,
                "bolt_name": bolt_name,
                "bolt": bolt,
                "host": host,
                "moved": moved,
                "tail": tail,
                "insertion_depth_mm": (old_end + direction * shift - insertion_entry).dot(
                    direction
                ),
                "axis_error_mm": (
                    body.Center()
                    - (
                        body.Center()
                        - direction * (chosen["nominal_body_length_mm"] / 2)
                        + direction * shift
                        + direction
                        * chosen["nominal_thread_axis_from_slotted_end_mm"]
                    )
                ).Length,
                "unrelated": unrelated,
            }
        )
    rows = []
    for item in prepared:
        name = item["name"]
        bolt_name = item["bolt_name"]
        moved = item["moved"]
        tail = item["tail"]
        host = item["host"]
        own_paths = frozenset(
            path
            for path in assembly["drilling_paths"]
            if path.startswith(f"{name}/")
        )
        peer_stacks = {
            f"{peer}/{role}": shape
            for peer, stack in assembly["stacks"].items()
            if peer != bolt_name
            for role, shape in stack.items()
        }
        row = {
            "pair": name,
            "station": assembly["barrel_station"][name],
            "receiver": host,
            "shift_mm": _rounded(shift),
            "selected_insertion_depth_mm": _rounded(
                item["insertion_depth_mm"], digits=3
            ),
            "thread_axis_preservation_error_mm": _rounded(item["axis_error_mm"]),
            "shifted_body_outside_receiver_mm3": _rounded(
                _outside_volume(moved, assembly["wood"][host])
            ),
            "bore_tail_outside_receiver_mm3": _rounded(
                _outside_volume(tail, assembly["wood"][host])
            ),
            "unrelated_wood_hits_mm3": {
                "shifted_body": _hits(moved, item["unrelated"]),
                "bore_tail": _hits(tail, item["unrelated"]),
            },
            "protected_hits_mm3": {
                "shifted_body": _protected_hits(name, moved, inventory),
                "bore_tail": _protected_hits(
                    f"{name}/barrel_bore_tail", tail, inventory
                ),
            },
            "peer_hits_mm3": {
                "shifted_body": {
                    "barrels": _hits(
                        moved, shifted, excluded=frozenset({name})
                    ),
                    "paths": _hits(
                        moved,
                        assembly["drilling_paths"],
                        excluded=own_paths,
                    ),
                    "stacks": _hits(moved, peer_stacks),
                },
                "bore_tail": {
                    "barrels": _hits(
                        tail, shifted, excluded=frozenset({name})
                    ),
                    "paths": _hits(
                        tail,
                        assembly["drilling_paths"],
                        excluded=own_paths,
                    ),
                    "stacks": _hits(tail, peer_stacks),
                },
            },
        }
        rows.append(row)
    return shift, shifted, rows


def _correction_rows(assembly, data, shifted_barrels, target_stations):
    washer = data["washers"][0]
    modeled_washer = data["stack_screen"]["calculation_inputs"][
        "modeled_washer_thickness_mm"
    ]
    inventory = protected.inventory()
    candidate_bolts = {
        name: bolt
        for name, bolt in assembly["bolts"].items()
        if assembly["bolt_station"][name] in target_stations
    }
    rows = []
    for bolt_name, bolt in sorted(candidate_bolts.items()):
        pair = bolt_name.removesuffix("_bolt")
        direction = bolt.direction.normalized()
        bore = assembly["drilling_paths"][f"{pair}/machine_bore"]
        selected_bolt = _selected_bolt(data, bolt.length)
        maximum_length = (
            selected_bolt["nominal_length_mm"]
            + selected_bolt["length_tolerance_mm"][1]
        )
        wood_seat = bolt.start + direction * modeled_washer
        adverse_start = wood_seat - direction * washer["thickness_min_mm"]
        adverse_tip = adverse_start + direction * maximum_length
        old_cap = _far_point(bore, bolt.start, direction)
        extension = adverse_tip.dot(direction) + TARGET_TIP_CLEARANCE_MM - old_cap.dot(
            direction
        )
        if extension <= 0:
            raise ValueError(f"{pair}: selected bore correction is not positive")
        tail = _cylinder(
            old_cap,
            direction,
            extension,
            rail.MACHINE_BORE_DIAMETER_MM,
        )
        new_cap = old_cap + direction * extension
        receiver = _host_for(tail, assembly, bolt.members)
        unrelated_wood = _hits(
            tail,
            assembly["wood"],
            excluded=frozenset({receiver}),
        )
        selected_washer = _cylinder(
            wood_seat,
            -direction,
            washer["thickness_max_mm"],
            washer["od_max_mm"],
        )
        washer_unrelated = _hits(
            selected_washer,
            assembly["wood"],
            excluded=frozenset(bolt.members),
        )
        peer_barrels = _hits(
            tail,
            shifted_barrels,
            excluded=frozenset({pair}),
        )
        own_paths = frozenset(
            {f"{pair}/machine_bore", f"{pair}/barrel_bore"}
        )
        peer_paths = _hits(
            tail,
            assembly["drilling_paths"],
            excluded=own_paths,
        )
        peer_stacks = {
            f"{peer}/{role}": shape
            for peer, stack in assembly["stacks"].items()
            if peer != bolt_name
            for role, shape in stack.items()
        }
        stack_hits = _hits(tail, peer_stacks)
        washer_peer_barrels = _hits(selected_washer, shifted_barrels)
        washer_peer_paths = _hits(
            selected_washer,
            assembly["drilling_paths"],
            excluded=own_paths,
        )
        washer_peer_stacks = _hits(
            selected_washer,
            peer_stacks,
        )
        row = {
            "pair": pair,
            "station": assembly["bolt_station"][bolt_name],
            "receiver": receiver,
            "selected_bolt": selected_bolt["product"],
            "selected_maximum_length_mm": _rounded(maximum_length),
            "added_bore_depth_mm": _rounded(extension),
            "adverse_tip_clearance_mm": _rounded(
                new_cap.dot(direction) - adverse_tip.dot(direction)
            ),
            "bore_tail_outside_receiver_mm3": _rounded(
                _outside_volume(tail, assembly["wood"][receiver])
            ),
            "bore_tail_unrelated_wood_hits_mm3": unrelated_wood,
            "bore_tail_protected_hits_mm3": _protected_hits(
                f"{pair}/machine_bore_tail", tail, inventory
            ),
            "bore_tail_peer_hits_mm3": {
                "barrels": peer_barrels,
                "paths": peer_paths,
                "stacks": stack_hits,
            },
            "maximum_washer_hits_mm3": {
                "unrelated_wood": washer_unrelated,
                "protected": _protected_hits(
                    f"{pair}/maximum_washer", selected_washer, inventory
                ),
                "peer_barrels": washer_peer_barrels,
                "peer_paths": washer_peer_paths,
                "peer_stacks": washer_peer_stacks,
            },
        }
        rows.append(row)
    return rows


def _sum_hits(value):
    if isinstance(value, dict):
        return sum(_sum_hits(child) for child in value.values())
    return 1 if value else 0


def _correction_summary(rows):
    extensions = {row["added_bore_depth_mm"] for row in rows}
    clearances = [row["adverse_tip_clearance_mm"] for row in rows]
    if len(extensions) != 1:
        raise ValueError("Selected correction rows no longer share one depth")
    return {
        "pair_count": len(rows),
        "added_bore_depth_mm": next(iter(extensions)),
        "minimum_adverse_tip_clearance_mm": min(clearances),
        "outside_receiver_volume_mm3": _rounded(
            sum(row["bore_tail_outside_receiver_mm3"] for row in rows)
        ),
        "unrelated_or_protected_hit_count": sum(
            _sum_hits(row["bore_tail_unrelated_wood_hits_mm3"])
            + _sum_hits(row["bore_tail_protected_hits_mm3"])
            for row in rows
        ),
        "peer_barrel_path_or_stack_hit_count": sum(
            _sum_hits(row["bore_tail_peer_hits_mm3"]) for row in rows
        ),
        "maximum_washer_hit_count": sum(
            _sum_hits(row["maximum_washer_hits_mm3"]) for row in rows
        ),
    }


@lru_cache(maxsize=1)
def build_report():
    data = selected.load_selection()
    assembly = build_integrated_viewer_assembly()
    if (
        assembly["hardware_basis"]["barrel_length_mm"]
        != data["barrel"]["nominal_body_length_mm"]
        or assembly["hardware_basis"]["barrel_od_mm"]
        != data["barrel"]["nominal_body_od_mm"]
    ):
        raise ValueError("Selected STAFAST nominal body no longer matches source CAD")
    shift, shifted, barrel_rows = _barrel_changes(assembly, data)
    rail_rows = _correction_rows(
        assembly,
        data,
        shifted,
        frozenset(rail.VIEWER_OUTER_STATIONS),
    )
    top_rows = _correction_rows(
        assembly,
        data,
        shifted,
        TOP_OUTER_STATIONS,
    )
    if (
        len(barrel_rows) != EXPECTED_BARREL_PAIRS
        or len(rail_rows) != EXPECTED_RAIL_PAIRS
        or len(top_rows) != EXPECTED_TOP_OUTER_PAIRS
    ):
        raise ValueError("Selected geometry inventory changed")
    barrel_summary = {
        "pair_count": len(barrel_rows),
        "body_shift_mm": _rounded(shift),
        "insertion_depth_range_mm": [
            min(row["selected_insertion_depth_mm"] for row in barrel_rows),
            max(row["selected_insertion_depth_mm"] for row in barrel_rows),
        ],
        "maximum_thread_axis_preservation_error_mm": max(
            row["thread_axis_preservation_error_mm"] for row in barrel_rows
        ),
        "shifted_body_outside_receiver_volume_mm3": _rounded(
            sum(row["shifted_body_outside_receiver_mm3"] for row in barrel_rows)
        ),
        "bore_tail_outside_receiver_volume_mm3": _rounded(
            sum(row["bore_tail_outside_receiver_mm3"] for row in barrel_rows)
        ),
        "unrelated_wood_hit_count": sum(
            _sum_hits(row["unrelated_wood_hits_mm3"]) for row in barrel_rows
        ),
        "protected_hit_count": sum(
            _sum_hits(row["protected_hits_mm3"]) for row in barrel_rows
        ),
        "peer_barrel_path_or_stack_hit_count": sum(
            _sum_hits(row["peer_hits_mm3"]) for row in barrel_rows
        ),
    }
    rail_summary = _correction_summary(rail_rows)
    top_summary = _correction_summary(top_rows)
    clear = (
        barrel_summary["shifted_body_outside_receiver_volume_mm3"]
        <= CONTAINMENT_TOL_MM3
        and barrel_summary["bore_tail_outside_receiver_volume_mm3"]
        <= CONTAINMENT_TOL_MM3
        and barrel_summary["maximum_thread_axis_preservation_error_mm"] <= 1e-5
        and barrel_summary["unrelated_wood_hit_count"] == 0
        and barrel_summary["protected_hit_count"] == 0
        and barrel_summary["peer_barrel_path_or_stack_hit_count"] == 0
        and all(
            summary["outside_receiver_volume_mm3"] <= CONTAINMENT_TOL_MM3
            and summary["unrelated_or_protected_hit_count"] == 0
            and summary["peer_barrel_path_or_stack_hit_count"] == 0
            and summary["maximum_washer_hit_count"] == 0
            and summary["minimum_adverse_tip_clearance_mm"]
            >= TARGET_TIP_CLEARANCE_MM - 1e-5
            for summary in (rail_summary, top_summary)
        )
    )
    return {
        "schema": SCHEMA,
        "candidate": data["candidate"],
        "status": "PASS_NOMINAL_GEOMETRY_ONLY" if clear else "FAIL_GEOMETRY_SCREEN",
        "inputs": {
            "selected_barrel": data["barrel"]["product"],
            "selected_washer": data["washers"][0]["product"],
            "target_tip_clearance_mm": TARGET_TIP_CLEARANCE_MM,
        },
        "barrel_shift": barrel_summary,
        "six_and_half_inch_rail_correction": rail_summary,
        "five_inch_top_outer_correction": top_summary,
        "barrel_rows": barrel_rows,
        "six_and_half_inch_rail_rows": rail_rows,
        "five_inch_top_outer_rows": top_rows,
        "nominal_geometry_clear": clear,
        "structural_released": False,
        "fabrication_released": False,
        "diy_ready": False,
        "limits": (
            "Nominal source-built collision screen only. Controlled barrel and "
            "finished-bore tolerances, usable female threads, wood resistance, "
            "joint stiffness, signed response, tools, and physical fit remain open."
        ),
    }


def selection_fields(report=None):
    report = build_report() if report is None else report
    barrel = report["barrel_shift"]
    rail_result = report["six_and_half_inch_rail_correction"]
    top = report["five_inch_top_outer_correction"]
    return {
        "selected_geometry_probe_source": (
            "scripts/owner_barrel_selected_geometry_probe.py"
        ),
        "stafast_shifted_bodies_checked": barrel["pair_count"],
        "stafast_shifted_body_unrelated_collisions": barrel[
            "unrelated_wood_hit_count"
        ],
        "stafast_shifted_body_protected_hardware_collisions": barrel[
            "protected_hit_count"
        ],
        "stafast_shifted_insertion_depth_range_mm": barrel[
            "insertion_depth_range_mm"
        ],
        "stafast_shifted_body_or_bore_tail_peer_hits": barrel[
            "peer_barrel_path_or_stack_hit_count"
        ],
        "six_and_half_corrected_cad_probe_extension_mm": rail_result[
            "added_bore_depth_mm"
        ],
        "six_and_half_corrected_cad_probe_pair_count": rail_result["pair_count"],
        "six_and_half_corrected_cad_probe_outside_receiver_volume_mm3": rail_result[
            "outside_receiver_volume_mm3"
        ],
        "six_and_half_corrected_cad_probe_unrelated_or_protected_hits": rail_result[
            "unrelated_or_protected_hit_count"
        ],
        "six_and_half_corrected_cad_probe_peer_barrel_path_or_stack_hits": rail_result[
            "peer_barrel_path_or_stack_hit_count"
        ],
        "six_and_half_corrected_cad_probe_max_washer_hits": rail_result[
            "maximum_washer_hit_count"
        ],
        "five_in_provisional_2mm_clearance_added_bore_depth_mm": top[
            "added_bore_depth_mm"
        ],
        "five_in_corrected_cad_probe_pair_count": top["pair_count"],
        "five_in_corrected_cad_probe_outside_receiver_volume_mm3": top[
            "outside_receiver_volume_mm3"
        ],
        "five_in_corrected_cad_probe_unrelated_or_protected_hits": top[
            "unrelated_or_protected_hit_count"
        ],
        "five_in_corrected_cad_probe_peer_barrel_path_or_stack_hits": top[
            "peer_barrel_path_or_stack_hit_count"
        ],
        "five_in_corrected_cad_probe_max_washer_hits": top[
            "maximum_washer_hit_count"
        ],
    }


def validate_recorded_fields(report=None, data=None):
    data = selected.load_selection() if data is None else data
    if report is not None and report["nominal_geometry_clear"] is not True:
        raise ValueError("Selected nominal geometry does not clear its gates")
    expected = selection_fields(report)
    actual = data["stack_screen"]
    mismatches = {
        key: {"expected": value, "recorded": actual.get(key)}
        for key, value in expected.items()
        if actual.get(key) != value
    }
    if mismatches:
        raise ValueError(f"Selected geometry fields drifted: {mismatches}")
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-fields", action="store_true")
    parser.add_argument("--check-selection", action="store_true")
    args = parser.parse_args()
    result = build_report()
    if args.check_selection:
        validate_recorded_fields(result)
    output = selection_fields(result) if args.selection_fields else result
    print(json.dumps(output, indent=2, sort_keys=True))
