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


def _contact_area(moving, stationary, inward_axis, epsilon=0.1):
    """Measure a touching face through a bounded inward CAD perturbation."""
    offset = tuple(component * epsilon for component in inward_axis)
    return moving.translate(offset).intersect(stationary).Volume() / epsilon


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
    """Report trial bore, face-seated washers, and diagnostic tool envelopes."""
    bore = _cylinder(point, axis, grip, DIAMETER)
    end = tuple(point[i] + axis[i] * grip for i in range(3))
    reverse = tuple(-a for a in axis)
    head_face = tuple(point[i] + axis[i] * 2.5 for i in range(3))
    nut_face = tuple(end[i] - axis[i] * 2.5 for i in range(3))
    washers = {
        "head": _cylinder(head_face, reverse, 2.5, WASHER_DIAMETER),
        "nut": _cylinder(nut_face, axis, 2.5, WASHER_DIAMETER),
    }
    tools = {
        "head": _cylinder(point, reverse, TOOL_DEPTH, TOOL_DIAMETER),
        "nut": _cylinder(end, axis, TOOL_DEPTH, TOOL_DIAMETER),
    }
    measured = {k: bore.intersect(v).Volume() for k, v in members.items()}
    expected = {
        k: math.pi * (DIAMETER / 2) ** 2 * length
        for k, length in required_lengths.items()
    }
    missing = {k: max(0.0, volume - measured[k]) for k, volume in expected.items()}
    excess = {k: max(0.0, measured[k] - volume) for k, volume in expected.items()}
    contained = {
        k: missing[k] <= 1.0 and excess[k] <= 1.0 and volume > 0
        for k, volume in expected.items()
    }
    return (
        {
            "name": name,
            "start_xyz_mm": [round(v, 3) for v in point],
            "axis_xyz": [round(v, 6) for v in axis],
            "grip_mm": grip,
            "washer_wood_face_xyz_mm": {
                "head": [round(v, 3) for v in head_face],
                "nut": [round(v, 3) for v in nut_face],
            },
            "washer_seat_offset_from_bore_end_mm": 2.5,
            "actual_head_nut_socket_stack_verified": False,
            "clearance_diameter_mm_trial_not_shop_instruction": DIAMETER,
            "required_wood_bore_mm3": {k: round(v, 3) for k, v in measured.items()},
            "expected_full_bore_wood_mm3": {
                k: round(v, 3) for k, v in expected.items()
            },
            "missing_wood_bore_mm3": {k: round(v, 6) for k, v in missing.items()},
            "excess_wood_bore_mm3": {k: round(v, 6) for k, v in excess.items()},
            "full_bore_tolerance_mm3": 1.0,
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


def _screen_grain_n_cleat(upright, rail, neighbors, panel, panel_axis_solids):
    """One full-section cleat pose with grain along the local N axis."""
    ub, rb = upright.BoundingBox(), rail.BoundingBox()
    rail_t = [v.Y * T[0] + v.Z * T[1] for v in rail.Vertices()]
    rail_n = [v.Y * N[0] + v.Z * N[1] for v in rail.Vertices()]
    upright_t = [v.Y * T[0] + v.Z * T[1] for v in upright.Vertices()]
    upright_n_bounds = [v.Y * N[0] + v.Z * N[1] for v in upright.Vertices()]
    t_near, n_near = max(rail_t), min(rail_n)
    x_width, t_width, n_length = 88.9, 57.15, 200.0
    base_y, base_z = _yz(t_near, n_near)
    cleat = (
        box(ub.xmax, 0, 0, x_width, t_width, n_length)
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, base_y, base_z))
    )
    cleat_t = [v.Y * T[0] + v.Z * T[1] for v in cleat.Vertices()]
    cleat_n = [v.Y * N[0] + v.Z * N[1] for v in cleat.Vertices()]
    upright_n, rail_bolt_n = 260.0, 315.0
    uy, uz = _yz(t_near + t_width / 2, upright_n)
    upright_bolt, upright_bore, uw, ut = _bolt_report(
        "upright_to_grain_n_cleat",
        (ub.xmin - 2.5, uy, uz),
        (1, 0, 0),
        ub.xlen + x_width + 5,
        {"upright": upright, "cleat": cleat},
        {"upright": ub.xlen, "cleat": x_width},
        {"rail": rail, **neighbors, **panel},
    )
    ry, rz = _yz(min(rail_t) - 2.5, rail_bolt_n)
    rail_bolt, rail_bore, rw, rt = _bolt_report(
        "rail_to_grain_n_cleat",
        (ub.xmax + x_width / 2, ry, rz),
        (0, T[0], T[1]),
        38.1 + t_width + 5,
        {"rail": rail, "cleat": cleat},
        {"rail": 38.1, "cleat": t_width},
        {"upright": upright, **neighbors, **panel},
    )
    u_faces = upright_bolt["washer_wood_face_xyz_mm"]
    r_faces = rail_bolt["washer_wood_face_xyz_mm"]
    r_head_t = r_faces["head"][1] * T[0] + r_faces["head"][2] * T[1]
    r_nut_t = r_faces["nut"][1] * T[0] + r_faces["nut"][2] * T[1]
    washer_face_gaps = {
        "upright_head_x": abs(u_faces["head"][0] - ub.xmin),
        "upright_nut_x": abs(u_faces["nut"][0] - ub.xmax - x_width),
        "rail_head_t": abs(r_head_t - min(rail_t)),
        "rail_nut_t": abs(r_nut_t - t_near - t_width),
    }
    washers_seated = all(gap <= 0.01 for gap in washer_face_gaps.values())
    all_envelopes = {
        "cleat": cleat,
        "upright_bore": upright_bore,
        "rail_bore": rail_bore,
        **{f"upright_washer_{end}": solid for end, solid in uw.items()},
        **{f"rail_washer_{end}": solid for end, solid in rw.items()},
        **{f"upright_tool_{end}": solid for end, solid in ut.items()},
        **{f"rail_tool_{end}": solid for end, solid in rt.items()},
    }
    upper_t_near = min(v.Y * T[0] + v.Z * T[1] for v in neighbors[NEIGHBOR].Vertices())
    rail_tool_t_end = t_near + t_width + 2.5 + TOOL_DEPTH
    nominal_contact = {
        "rail_to_cleat": x_width * (max(rail_n) - n_near),
        "upright_to_cleat": t_width * (max(rail_n) - n_near),
    }
    measured_contact = {
        "rail_to_cleat": _contact_area(cleat, rail, (0, -T[0], -T[1])),
        "upright_to_cleat": _contact_area(cleat, upright, (-1, 0, 0)),
    }
    contact_verified = {
        name: measured_contact[name] > 0
        and abs(measured_contact[name] - nominal_contact[name])
        <= max(1.0, nominal_contact[name] * 0.01)
        for name in nominal_contact
    }
    report = {
        "size_local_x_t_n_mm": [x_width, t_width, n_length],
        "grain_direction_xyz": [0, round(N[0], 6), round(N[1], 6)],
        "grain_axis": "N",
        "bolt_axis_dot_cleat_grain": {"upright": 0, "rail": 0},
        "actual_local_bounds_mm": {
            "x": [
                round(cleat.BoundingBox().xmin, 3),
                round(cleat.BoundingBox().xmax, 3),
            ],
            "t": [round(min(cleat_t), 3), round(max(cleat_t), 3)],
            "n": [round(min(cleat_n), 3), round(max(cleat_n), 3)],
        },
        "rail_tangent_face_mm": round(t_near, 3),
        "rail_butt_x_mm": round(rb.xmin, 3),
        "upright_butt_x_mm": round(ub.xmax, 3),
        "nominal_face_contact_area_mm2": {
            name: round(value, 3) for name, value in nominal_contact.items()
        },
        "measured_face_contact_area_mm2": {
            name: round(value, 3) for name, value in measured_contact.items()
        },
        "face_contact_perturbation_mm": 0.1,
        "face_contact_geometry_verified": contact_verified,
        "trial_bolt_n_centers_mm": {"upright": upright_n, "rail": rail_bolt_n},
        "trial_bolt_n_center_separation_mm": rail_bolt_n - upright_n,
        "center_to_edges_mm": {
            "upright_bolt_in_cleat_t": [t_width / 2, t_width / 2],
            "upright_bolt_in_cleat_n": [
                round(upright_n - n_near, 3),
                round(n_near + n_length - upright_n, 3),
            ],
            "upright_bolt_in_host_t": [
                round(t_near + t_width / 2 - min(upright_t), 3),
                round(max(upright_t) - t_near - t_width / 2, 3),
            ],
            "upright_bolt_in_host_n": [
                round(upright_n - min(upright_n_bounds), 3),
                round(max(upright_n_bounds) - upright_n, 3),
            ],
            "rail_bolt_in_cleat_x": [x_width / 2, x_width / 2],
            "rail_bolt_in_cleat_n": [
                round(rail_bolt_n - n_near, 3),
                round(n_near + n_length - rail_bolt_n, 3),
            ],
            "rail_bolt_in_host_x": [
                round(ub.xmax + x_width / 2 - rb.xmin, 3),
                round(rb.xmax - ub.xmax - x_width / 2, 3),
            ],
            "rail_bolt_in_host_n": [
                round(rail_bolt_n - n_near, 3),
                round(max(rail_n) - rail_bolt_n, 3),
            ],
        },
        "edge_distance_structurally_qualified": False,
        "rail_first_bolt_end_distance_mm": round(x_width / 2, 3),
        "nominal_7d_mm": round(7 * 9.525, 3),
        "rail_end_distance_shortfall_if_7d_applies_mm": round(
            7 * 9.525 - x_width / 2, 3
        ),
        "conditional_edge_caution": (
            "rail trial bore is 34.541 mm from its rear N edge; if that edge "
            "is loaded under a 4D screen for a 9.525-mm bolt, 38.1 mm would "
            "be needed. Load direction and applicable NDS rule remain open"
        ),
        "conditional_end_caution": (
            "rail trial bore is 44.45 mm from its grain-X end; this is "
            "22.225 mm short of nominal 7D=66.675 mm for a 9.525-mm bolt "
            "if that NDS full-value end-distance condition applies. "
            "Same-case load direction and applicable rule remain open"
        ),
        "fixed_panel_axes_checked": len(panel_axis_solids),
        "washer_wood_face_gap_mm": {
            name: round(value, 6) for name, value in washer_face_gaps.items()
        },
        "washer_faces_geometry_verified": washers_seated,
        "protected_axis_envelope_clashes_mm3": {
            name: _volume_hits(solid, panel_axis_solids)
            for name, solid in all_envelopes.items()
        },
        "cleat_host_clashes_mm3": _volume_hits(
            cleat, {"upright": upright, "rail": rail}
        ),
        "cleat_parent_clashes_mm3": _volume_hits(cleat, neighbors),
        "cleat_panel_clashes_mm3": _volume_hits(cleat, panel),
        "bolt_groups": {"upright": [upright_bolt], "rail": [rail_bolt]},
        "bolt_intersections_mm3": round(upright_bore.intersect(rail_bore).Volume(), 3),
        "washer_cross_clashes_mm3": {
            "upright_against_rail_bore": _volume_hits(
                uw["nut"], {"rail_bore": rail_bore}
            ),
            "rail_against_upright_bore": _volume_hits(
                rw["nut"], {"upright_bore": upright_bore}
            ),
        },
        "upper_rail_tangent_near_mm": round(upper_t_near, 3),
        "rail_nut_tool_tangent_clearance_mm": round(upper_t_near - rail_tool_t_end, 3),
        "real_stock_and_cost_caveats": [
            "nominal 4x4 cross-section is only a dimensional source; grade and delivered dimensions unverified",
            "57.15-mm tangent rip, saw kerf, tolerances, usable offcut, and fabrication effort unverified",
            "full through-bolt, washer, nut, tool, timber, and purchase-pack costs unknown",
        ],
        "trial_stack_count_not_selected": 2,
        "trial_envelope_grips_mm_not_purchased_lengths": {
            "upright": upright_bolt["grip_mm"],
            "rail": rail_bolt["grip_mm"],
        },
        "installed_cost_usd": None,
        "remaining_open_checks": [
            "one trial bolt per side is not a complete reversible joint or load path",
            "grain-N cleat, edge/end distances, group action, splitting, and net section require 2024 NDS checks",
            "simultaneous force/moment demand, cleat equilibrium, deformation, and contact-only compression open",
            "delivered stock, hardware tolerances, access during assembly, and installed cost open",
        ],
        "load_rating_adopted": False,
        "drilling_released": False,
        "installed_access_verified": False,
        "actual_head_nut_socket_stack_verified": False,
        "tool_clearance_interpretation": (
            "40-mm straight cylinders are diagnostic clearance envelopes only; "
            "real bolt heads, nuts, washer dimensions, sockets, and assembly sequence unverified"
        ),
    }
    clear = (
        all(contact_verified.values())
        and washers_seated
        and all(upright_bolt["full_bore_containment"].values())
        and all(rail_bolt["full_bore_containment"].values())
        and not any(
            _has_hits(report[key])
            for key in (
                "protected_axis_envelope_clashes_mm3",
                "cleat_host_clashes_mm3",
                "cleat_parent_clashes_mm3",
                "cleat_panel_clashes_mm3",
                "washer_cross_clashes_mm3",
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
        and report["bolt_intersections_mm3"] == 0
        and report["rail_nut_tool_tangent_clearance_mm"] > 0
    )
    report["status"] = "diagnostic_pose_only" if clear else "reject_this_pose"
    return report


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
        "installed_access_verified": False,
        "actual_head_nut_socket_stack_verified": False,
        "tool_clearance_interpretation": (
            "40-mm straight cylinders are diagnostic only; installed head, nut, "
            "socket, and assembly access remain unverified"
        ),
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
        "diagnostic_pose_only" if geometry_clear else "reject_this_pose"
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
        "cleat_grain_n": _screen_grain_n_cleat(
            upright, rail, neighbors, panel, panel_axis_solids
        ),
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
