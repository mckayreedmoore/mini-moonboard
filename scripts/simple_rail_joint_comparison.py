"""PB-01: two nominal timber-joint poses at one actual kerf-right rail station.

This is a reject/diagnostic screen, never a bolt schedule or drilling plan.
"""

import argparse
import csv
import json
import math

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hybrid import AXES, ROOT, box

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/simple_rail_joint_comparison.json"
UPRIGHT = "base_principal_center_right"
RAIL = "base_rail_service_lower_right"
NEIGHBOR = "base_rail_service_upper_right"
TOL = 0.01
DIAMETER = 10.3  # Trial clearance envelope around 3/8-in bolt, not a drill size.
WASHER_DIAMETER = 25.4  # Diagnostic round envelope, not a product specification.
TOOL_DIAMETER = 40.0  # Diagnostic straight approach envelope.
TOOL_DEPTH = 40.0
OVERLAP_LENGTH = 76.2
OFFSET = 139.7
ANGLE = math.radians(50)
T = (math.cos(ANGLE), math.sin(ANGLE))
N = (-math.sin(ANGLE), math.cos(ANGLE))


def _volume_hits(shape, others):
    return {
        name: round(shape.intersect(other).Volume(), 3)
        for name, other in others.items()
        if shape.intersect(other).Volume() > TOL
    }


def _has_hits(result):
    """Detect any nested occupied-volume clash without trusting a status label."""
    return any(
        _has_hits(value) if isinstance(value, dict) else value > 0
        for value in result.values()
    )


def _cylinder(point, axis, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(*point), cq.Vector(*axis)
    )


def _yz(t, n):
    return (t * T[0] + n * N[0], t * T[1] + n * N[1])


def _read_panel_axes():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    if len(panel) != 66 or len({r["name"] for r in panel}) != 66:
        raise ValueError("expected 66 unique protected panel/kicker axes")
    return panel


def _axis_solid(row):
    point = tuple(float(row[f"start_{a}_mm"]) for a in "xyz")
    direction = tuple(float(row[f"direction_{a}"]) for a in "xyz")
    return _cylinder(
        point,
        direction,
        float(row["occupied_length_mm"]),
        float(row["occupied_diameter_mm"]),
    )


def _bolt_report(name, point, axis, grip, members, required_lengths, parent):
    """Report complete trial bore and external washer/straight-tool envelopes."""
    bore = _cylinder(point, axis, grip, DIAMETER)
    end = tuple(point[i] + axis[i] * grip for i in range(3))
    reverse = tuple(-a for a in axis)
    washers = {
        "head": _cylinder(point, reverse, 2.5, WASHER_DIAMETER),
        "nut": _cylinder(end, axis, 2.5, WASHER_DIAMETER),
    }
    tools = {
        "head": _cylinder(point, reverse, TOOL_DEPTH, TOOL_DIAMETER),
        "nut": _cylinder(end, axis, TOOL_DEPTH, TOOL_DIAMETER),
    }
    required = {k: round(bore.intersect(v).Volume(), 3) for k, v in members.items()}
    expected = {
        k: round(math.pi * (DIAMETER / 2) ** 2 * length, 3)
        for k, length in required_lengths.items()
    }
    contained = {
        k: required[k] >= 0.99 * volume and volume > 0 for k, volume in expected.items()
    }
    return (
        {
            "name": name,
            "start_xyz_mm": [round(v, 3) for v in point],
            "axis_xyz": [round(v, 6) for v in axis],
            "grip_mm": grip,
            "clearance_diameter_mm_trial_not_shop_instruction": DIAMETER,
            "required_wood_bore_mm3": required,
            "expected_full_bore_wood_mm3": expected,
            "full_bore_containment": contained,
            "parent_bore_clashes_mm3": _volume_hits(bore, parent),
            "washer_clashes_mm3": {
                k: _volume_hits(v, parent) for k, v in washers.items()
            },
            "tool_clashes_mm3": {k: _volume_hits(v, parent) for k, v in tools.items()},
        },
        bore,
        washers,
        tools,
    )


def compare():
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    panel_axes = _read_panel_axes()
    panel_axis_solids = {row["name"]: _axis_solid(row) for row in panel_axes}
    upright, rail = raw[UPRIGHT], raw[RAIL]
    rb = rail.BoundingBox()
    ub = upright.BoundingBox()
    panel = {k: v for k, v in raw.items() if k.startswith(("main_", "kicker_"))}
    neighbors = {
        k: v for k, v in raw.items() if k not in {UPRIGHT, RAIL} and k not in panel
    }
    values_t = [v.Y * T[0] + v.Z * T[1] for v in rail.Vertices()]
    values_n = [v.Y * N[0] + v.Z * N[1] for v in rail.Vertices()]
    upper_t_near = min(v.Y * T[0] + v.Z * T[1] for v in raw[NEIGHBOR].Vertices())
    tc = (min(values_t) + max(values_t)) / 2
    rear_n = max(values_n)

    # A: extend the intact rail 76.2 mm past the butt plane, then offset its
    # entire section by its full 139.7-mm panel-normal depth. The two full
    # sections then meet across broad faces; this is not a flush half-lap.
    segment = rail.intersect(
        box(
            rb.xmin - 0.01,
            rb.ymin - 1,
            rb.zmin - 1,
            OVERLAP_LENGTH + 0.02,
            rb.ylen + 2,
            rb.zlen + 2,
        )
    ).translate((-OVERLAP_LENGTH, 0, 0))
    moved_rail = rail.fuse(segment).clean().translate((0, N[0] * OFFSET, N[1] * OFFSET))
    lost = {}
    for row in panel_axes:
        if row["name"] not in {
            "round_panel_lower_right_service_1",
            "round_panel_lower_right_service_2",
        }:
            continue
        axis = _axis_solid(row)
        before = axis.intersect(rail).Volume()
        after = axis.intersect(moved_rail).Volume()
        lost[row["name"]] = {
            "original_receiver_intersection_mm3": round(before, 3),
            "offset_receiver_intersection_mm3": round(after, 3),
            "change_mm3": round(after - before, 3),
        }
    oy, oz = _yz(tc, min(values_n) - 2.5)
    overlap_bolt, _, _, _ = _bolt_report(
        "full_section_overlap",
        (70, oy, oz),
        (0, N[0], N[1]),
        2 * 139.7 + 5,
        {"upright": upright, "offset_rail": moved_rail},
        {"upright": 139.7, "offset_rail": 139.7},
        {**neighbors, **panel},
    )
    overlap = {
        "offset_mm": OFFSET,
        "offset_direction_xyz": [0, round(N[0], 6), round(N[1], 6)],
        "extended_end_x_mm": round(rb.xmin - OVERLAP_LENGTH, 3),
        "upright_x_span_mm": [round(ub.xmin, 3), round(ub.xmax, 3)],
        "nominal_rail_upright_intersection_mm3": round(
            moved_rail.intersect(upright).Volume(), 3
        ),
        "protected_receiver_changes": lost,
        "neighbor_clashes_mm3": _volume_hits(moved_rail, neighbors),
        "panel_clashes_mm3": _volume_hits(moved_rail, panel),
        "bolt_groups": {"trial_one_bolt_only_not_a_joint_schedule": [overlap_bolt]},
        "limiting_conditions": [
            "both fixed service-rail screw axes lose their original receiver",
            "trial bolt head/washer/tool intersects the fixed lower panel",
            "one trial bolt is not a demonstrated reversible rail joint",
        ],
        "status": "reject_this_pose",
    }

    # B: rectangular solid block beside the unchanged butt joint. The box's
    # local Y runs along T after rotation, so its near face is exactly the
    # rail's +T face; local Z runs along N. Grain follows X.
    cleat_tangent = 57.15
    cleat_normal = 88.9
    base_y, base_z = _yz(max(values_t), rear_n - 114.3)
    cleat = (
        box(ub.xmax, 0, 0, 200, cleat_tangent, cleat_normal)
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, base_y, base_z))
    )
    # Perpendicular trial bore axes: X for upright, panel-tangent for rail.
    # Their stations are staggered; complete member/cleat penetration is
    # measured, not assumed from centerline placement.
    uy, uz = _yz(max(values_t) + cleat_tangent / 2, rear_n - 100)
    upright_bolt, upright_bore, uw, ut = _bolt_report(
        "upright_to_cleat",
        (ub.xmin - 2.5, uy, uz),
        (1, 0, 0),
        ub.xlen + 200 + 5,
        {"upright": upright, "cleat": cleat},
        {"upright": ub.xlen, "cleat": 200},
        {"rail": rail, **neighbors, **panel},
    )
    ry, rz = _yz(min(values_t) - 2.5, rear_n - 69.85)
    rail_bolt, rail_bore, rw, rt = _bolt_report(
        "rail_to_cleat",
        (ub.xmax + 140, ry, rz),
        (0, T[0], T[1]),
        38.1 + cleat_tangent + 5,
        {"rail": rail, "cleat": cleat},
        {"rail": 38.1, "cleat": cleat_tangent},
        {"upright": upright, **neighbors, **panel},
    )
    # The bolt starts 2.5 mm before the rail face and ends 2.5 mm beyond
    # the cleat. The straight 40-mm nut-side envelope starts at that end.
    rail_tool_t_end = max(values_t) + cleat_tangent + 2.5 + TOOL_DEPTH
    cleat_report = {
        "size_mm": [200, cleat_tangent, cleat_normal],
        "local_tangent_near_far_mm": [
            round(max(values_t), 3),
            round(max(values_t) + cleat_tangent, 3),
        ],
        "upright_bolt_tangent_from_cleat_near_mm": cleat_tangent / 2,
        "rail_tangent_near_far_mm": [round(min(values_t), 3), round(max(values_t), 3)],
        "upper_rail_tangent_near_mm": round(upper_t_near, 3),
        "cleat_to_upper_rail_tangent_gap_mm": round(
            upper_t_near - max(values_t) - cleat_tangent, 3
        ),
        "rail_nut_tool_tangent_end_mm": round(rail_tool_t_end, 3),
        "rail_nut_tool_tangent_clearance_mm": round(upper_t_near - rail_tool_t_end, 3),
        "grain_direction_xyz": [1, 0, 0],
        "priority_architecture_blocker": (
            "upright-side X-axis through-bolt is parallel to the cleat X grain; "
            "ordinary lateral-dowel applicability and end-grain load path are unqualified"
        ),
        "upright_bolt_axis_dot_cleat_grain": 1,
        "cleat_parent_clashes_mm3": _volume_hits(cleat, neighbors),
        "cleat_panel_clashes_mm3": _volume_hits(cleat, panel),
        "protected_screw_axis_clashes_mm3": _volume_hits(cleat, panel_axis_solids),
        "protected_axis_hardware_clashes_mm3": {
            "upright_bore": _volume_hits(upright_bore, panel_axis_solids),
            "rail_bore": _volume_hits(rail_bore, panel_axis_solids),
            "upright_washers": {
                end: _volume_hits(shape, panel_axis_solids) for end, shape in uw.items()
            },
            "rail_washers": {
                end: _volume_hits(shape, panel_axis_solids) for end, shape in rw.items()
            },
            "upright_tools": {
                end: _volume_hits(shape, panel_axis_solids) for end, shape in ut.items()
            },
            "rail_tools": {
                end: _volume_hits(shape, panel_axis_solids) for end, shape in rt.items()
            },
        },
        "cleat_host_clashes_mm3": _volume_hits(
            cleat, {"upright": upright, "rail": rail}
        ),
        "bolt_groups": {"upright": [upright_bolt], "rail": [rail_bolt]},
        "orthogonal_axis_dot": 0,
        "bolt_intersections_mm3": round(upright_bore.intersect(rail_bore).Volume(), 3),
        "washer_cross_clashes_mm3": {
            "upright_against_rail": _volume_hits(uw["nut"], {"rail_bore": rail_bore}),
            "rail_against_upright": _volume_hits(
                rw["nut"], {"upright_bore": upright_bore}
            ),
        },
        "neighbor_clashes_mm3": _volume_hits(cleat, neighbors),
        "tool_clashes_mm3": {
            "upright": {
                k: _volume_hits(v, {"rail": rail, **neighbors, **panel})
                for k, v in ut.items()
            },
            "rail": {
                k: _volume_hits(v, {"upright": upright, **neighbors, **panel})
                for k, v in rt.items()
            },
        },
        "nominal_center_to_tangent_edge_mm": cleat_tangent / 2,
        "edge_distance_structurally_qualified": False,
        "remaining_open_checks": [
            "trial 28.575-mm tangent center-to-edge is not an NDS edge-distance pass",
            "one trial bolt per side is not a demonstrated bolt group",
            "same-case force/moment demand and cleat equilibrium",
            "wood bearing, splitting, net section, washer pressure, and bolt interaction",
            "long upright-to-cleat bore runs parallel to cleat grain; resistance and fabrication open",
            "real hardware dimensions, tolerances, assembly sequence, and cost",
        ],
    }
    geometry_clear = (
        all(upright_bolt["full_bore_containment"].values())
        and all(rail_bolt["full_bore_containment"].values())
        and not any(
            _has_hits(cleat_report[key])
            for key in (
                "cleat_parent_clashes_mm3",
                "cleat_panel_clashes_mm3",
                "cleat_host_clashes_mm3",
                "protected_screw_axis_clashes_mm3",
                "protected_axis_hardware_clashes_mm3",
                "washer_cross_clashes_mm3",
                "tool_clashes_mm3",
            )
        )
        and not any(
            _has_hits(bolt[key])
            for bolt in (upright_bolt, rail_bolt)
            for key in (
                "parent_bore_clashes_mm3",
                "washer_clashes_mm3",
                "tool_clashes_mm3",
            )
        )
        and cleat_report["bolt_intersections_mm3"] == 0
        and cleat_report["rail_nut_tool_tangent_clearance_mm"] > 0
    )
    cleat_report["status"] = (
        "geometry_only_candidate" if geometry_clear else "reject_this_pose"
    )
    return {
        "station": "clip_horizontal_lower_right_1",
        "physical_width": "kerf-right",
        "butt_plane_x_mm": round(rb.xmin, 3),
        "fixed_panel_axes": len(panel_axes),
        "participants": [UPRIGHT, RAIL],
        "nearby_rail": NEIGHBOR,
        "overlap": overlap,
        "cleat": cleat_report,
        "load_rating_adopted": False,
        "drilling_released": False,
        "open": [
            "full bolt-group geometry",
            "wood/bolt resistance",
            "same-case actions",
            "assembly access",
            "cost",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = compare()
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    else:
        print(json.dumps(result, indent=2))
