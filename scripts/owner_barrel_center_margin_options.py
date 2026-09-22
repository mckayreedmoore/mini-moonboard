"""Bounded, nominal CAD margin trial for the integrated principal/header barrels.

The maintained joint and fixed frame/panel axes are not changed. This is a
source-built clearance screen, not a drilling schedule or structural release.
"""

import math
from itertools import combinations

import cadquery as cq

from mini_moonboard.floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    TRANSLATE_NAMES,
    variant,
)
from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_center_post_joint_replan as current
from scripts import owner_barrel_coordinates as coordinates
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly

TARGET_RECESS_MM = 3.0
TARGET_TOOL_GAP_MM = 2.0
BORE_TIP_CLEARANCE_MM = 4.0
X_OFFSETS_MM = (-12.0, 12.0)
REAR_ENTRY_Z_MM = (257.3, 258.0)
NOMINAL_BOLT_LENGTHS_MM = (127.0, 114.3)
HEAD_POCKET_DIAMETER_MM = 21.0
HEAD_POCKET_LEAD_MM = 15.0
HEAD_SEAT_DEPTH_MM = 15.5
BARREL_MOUTH_RELIEF_DIAMETER_MM = 21.0
BOLT_ANGLE_DEG = 55.0
SHALLOW_ENTRY_Z_MM = (260.3, 261.0)
SHALLOW_HEAD_SEAT_DEPTH_MM = 7.5
SHALLOW_THREAD_DEPTH_MM = 108.0
VOLUME_TOL_MM3 = 1.0


def _rounded(value):
    return round(value, 6)


def _shape_fraction(shape, host):
    return _rounded(protected._volume(shape, host) / shape.Volume())


def _hits(shape, targets):
    return {
        name: _rounded(volume)
        for name, other in targets.items()
        if (volume := protected._volume(shape, other)) > VOLUME_TOL_MM3
    }


def _pose(
    wood,
    side,
    index,
    *,
    x_offset,
    entry_z,
    bolt_length,
    barrel_face,
    seat_depth,
    thread_depth,
):
    """Cross a YZ bolt with a barrel entering a principal broad N face."""
    header = wood["base_header"]
    principal = wood[f"base_principal_center_{side}"]
    bounds = coordinates.local_bounds(principal)
    center_x = sum(bounds["x"]) / 2
    x = center_x + x_offset
    angle = math.radians(BOLT_ANGLE_DEG)
    bolt_axis = (0.0, math.cos(angle), math.sin(angle))
    if barrel_face not in ("rear", "front"):
        raise ValueError("Unsupported principal barrel entry face")
    outward_sign = 1 if barrel_face == "rear" else -1
    outward = (0.0, -bolt_axis[2], bolt_axis[1])
    barrel_axis = tuple(-outward_sign * v for v in outward)
    header_face = (x, header.BoundingBox().ymin, entry_z)
    seat = current._add(header_face, bolt_axis, seat_depth)
    thread = current._add(seat, bolt_axis, thread_depth)
    thread_n = thread[1] * coordinates.N[0] + thread[2] * coordinates.N[1]
    face_n = bounds["n"][1] if barrel_face == "rear" else bounds["n"][0]
    normal_projection = sum(outward[i] * (0.0, *coordinates.N)[i] for i in range(3))
    axis_depth = abs(face_n - thread_n) / abs(normal_projection)
    entry = current._add(thread, outward, outward_sign * axis_depth)
    recess = axis_depth - current.OFFSET
    if recess < 0 or recess + current.LENGTH > bounds["n"][1] - bounds["n"][0]:
        raise ValueError("Barrel does not fit the principal's N width")
    if abs(sum(a * b for a, b in zip(bolt_axis, barrel_axis, strict=True))) > 1e-9:
        raise ValueError("Bolt and barrel axes are not perpendicular")
    shaft_start = current._add(seat, bolt_axis, -current.WASHER_T)
    tip_start = current._add(seat, bolt_axis, bolt_length - current.WASHER_T)
    first_depth = (header.BoundingBox().zmax - seat[2]) / bolt_axis[2]
    name = f"barrel_center_clip_split_base_center_{side}_{index}"
    cylinder = current._cylinder
    add = current._add
    roles = {
        "bolt_bore": cylinder(
            seat,
            bolt_axis,
            bolt_length - current.WASHER_T + BORE_TIP_CLEARANCE_MM,
            center.BORE_DIAMETER_MM,
        ),
        "barrel_cross_bore": cylinder(
            entry, barrel_axis, recess + current.LENGTH, current.OD
        ),
        "shaft": cylinder(
            shaft_start, bolt_axis, bolt_length, center.hardware.THREAD_MAJOR_MM
        ),
        "barrel": cylinder(
            add(entry, barrel_axis, recess), barrel_axis, current.LENGTH, current.OD
        ),
        "washer": cylinder(shaft_start, bolt_axis, current.WASHER_T, 19.05),
        "head": cylinder(add(shaft_start, bolt_axis, -4), bolt_axis, 4, 11.0),
        "head_pocket": cylinder(
            add(header_face, bolt_axis, -HEAD_POCKET_LEAD_MM),
            bolt_axis,
            seat_depth + HEAD_POCKET_LEAD_MM,
            HEAD_POCKET_DIAMETER_MM,
        ),
        "bolt_tool": cylinder(
            seat,
            tuple(-v for v in bolt_axis),
            center.TOOL_LENGTH_MM,
            center.TOOL_DIAMETER_MM,
        ),
        "barrel_tool": cylinder(
            entry,
            tuple(outward_sign * v for v in outward),
            center.TOOL_LENGTH_MM,
            center.TOOL_DIAMETER_MM,
        ),
        "barrel_mouth_relief": cylinder(
            add(entry, outward, outward_sign * 1.5),
            barrel_axis,
            3.0,
            BARREL_MOUTH_RELIEF_DIAMETER_MM,
        ),
    }
    inner_bore = cylinder(
        add(entry, barrel_axis, 1.0),
        barrel_axis,
        recess + current.LENGTH - 1.0,
        current.OD,
    )
    tip_extension = cylinder(
        tip_start, bolt_axis, BORE_TIP_CLEARANCE_MM, center.BORE_DIAMETER_MM
    )
    core = cylinder(seat, bolt_axis, thread_depth, center.BORE_DIAMETER_MM)
    first_core = cylinder(seat, bolt_axis, first_depth, center.BORE_DIAMETER_MM)
    second_core = cylinder(
        add(seat, bolt_axis, first_depth),
        bolt_axis,
        thread_depth - first_depth,
        center.BORE_DIAMETER_MM,
    )
    row = {
        "name": name,
        "entry_face": f"principal_{barrel_face}_broad_face",
        "bolt_entry_face": "header_rear_recess",
        "bolt_seat_xyz_mm": [_rounded(v) for v in seat],
        "bolt_axis_xyz": list(bolt_axis),
        "bolt_axis_angle_from_y_deg": BOLT_ANGLE_DEG,
        "barrel_entry_xyz_mm": [_rounded(v) for v in entry],
        "barrel_axis_xyz": list(barrel_axis),
        "thread_axis_xyz_mm": [_rounded(v) for v in thread],
        "bolt_length_mm": bolt_length,
        "header_seat_depth_mm": seat_depth,
        "thread_depth_from_seat_mm": thread_depth,
        "barrel_axis_depth_mm": _rounded(axis_depth),
        "barrel_recess_mm": _rounded(recess),
        "barrel_cross_bore_depth_mm": _rounded(recess + current.LENGTH),
        "barrel_body_in_host_fraction": _shape_fraction(roles["barrel"], principal),
        "barrel_cross_bore_in_host_fraction": _shape_fraction(
            roles["barrel_cross_bore"], principal
        ),
        "barrel_cross_bore_past_entry_1mm_in_host_fraction": _shape_fraction(
            inner_bore, principal
        ),
        "tip_extension_in_receiver_fraction": _shape_fraction(tip_extension, principal),
        "joined_wood_bore_core_fraction": _rounded(
            (protected._volume(core, header) + protected._volume(core, principal))
            / core.Volume()
        ),
        "intended_bore_core_fraction": {
            "header": _shape_fraction(first_core, header),
            "principal": _shape_fraction(second_core, principal),
        },
        "head_washer_inside_header_fraction": {
            role: _shape_fraction(roles[role], header) for role in ("head", "washer")
        },
        "bolt_barrel_intersection_mm3": _rounded(
            protected._volume(roles["bolt_bore"], roles["barrel_cross_bore"])
        ),
        "nominal_tip_beyond_thread_axis_mm": _rounded(
            bolt_length - current.WASHER_T - thread_depth
        ),
        "nominal_tip_beyond_barrel_far_wall_mm": _rounded(
            bolt_length - current.WASHER_T - thread_depth - current.OD / 2
        ),
        "modeled_bore_depth_past_nominal_tip_mm": BORE_TIP_CLEARANCE_MM,
        "barrel_radial_x_edge_ligament_mm": _rounded(
            min(x - bounds["x"][0], bounds["x"][1] - x) - current.OD / 2
        ),
        "barrel_mouth_relief_x_side_breakout_mm": _rounded(
            BARREL_MOUTH_RELIEF_DIAMETER_MM / 2
            - min(x - bounds["x"][0], bounds["x"][1] - x)
        ),
        "unrelieved_barrel_tool_host_intrusion_mm3": _rounded(
            protected._volume(roles["barrel_tool"], principal)
        ),
        "barrel_tool_residual_host_mm3": _rounded(
            protected._volume(
                roles["barrel_tool"], principal.cut(roles["barrel_mouth_relief"])
            )
        ),
        "barrel_mouth_relief_in_host_fraction": _shape_fraction(
            roles["barrel_mouth_relief"], principal
        ),
        "screened_roles": sorted(roles),
        "complete_thread_engagement_verified": False,
        "driver_residual_header_mm3": _rounded(
            protected._volume(roles["bolt_tool"], header.cut(roles["head_pocket"]))
        ),
        "head_pocket_in_principal_mm3": _rounded(
            protected._volume(roles["head_pocket"], principal)
        ),
        "head_pocket_header_bottom_margin_mm": _rounded(
            roles["head_pocket"].BoundingBox().zmin - header.BoundingBox().zmin
        ),
        "head_pocket_header_top_margin_mm": _rounded(
            header.BoundingBox().zmax - roles["head_pocket"].BoundingBox().zmax
        ),
    }
    return name, roles, row, tip_extension


def _screen(
    wood,
    assembly,
    unchanged,
    service,
    *,
    bolt_lengths,
    barrel_faces,
    entry_zs,
    seat_depth,
    thread_depth,
):
    fixed = protected.inventory()
    rows, solids, extensions = {}, {}, {}
    for side in current.SIDES:
        for index, (offset, z, length) in enumerate(
            zip(X_OFFSETS_MM, entry_zs, bolt_lengths, strict=True), 1
        ):
            name, roles, row, tip = _pose(
                wood,
                side,
                index,
                x_offset=offset,
                entry_z=z,
                bolt_length=length,
                barrel_face=barrel_faces[side][index - 1],
                seat_depth=seat_depth,
                thread_depth=thread_depth,
            )
            rows[name], solids[name], extensions[name] = row, roles, tip

    retired = set(current.STATIONS)
    retained = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] not in retired
    }
    retained.update(
        {
            f"stack/{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            if assembly["bolt_station"][name] not in retired
            for role, shape in stack.items()
        }
    )
    unchanged_solids = {
        name: shapes
        for name, shapes in unchanged.items()
        if "clip_split_header_center_" in name
    }
    all_solids = {**unchanged_solids, **solids}
    installed = {
        f"{name}/{role}": shape
        for name, shapes in all_solids.items()
        for role, shape in shapes.items()
        if role in ("shaft", "barrel", "washer", "head")
    }
    tools = {
        f"{name}/{role}": shape
        for name, shapes in all_solids.items()
        for role, shape in shapes.items()
        if role in ("bolt_tool", "barrel_tool")
    }
    pair_hits, tool_hardware_hits, tool_pair_hits = {}, {}, {}
    tool_gaps = {}
    for (a, sa), (b, sb) in combinations(installed.items(), 2):
        if (
            a.rsplit("/", 1)[0] != b.rsplit("/", 1)[0]
            and (volume := protected._volume(sa, sb)) > VOLUME_TOL_MM3
        ):
            pair_hits[f"{a}|{b}"] = _rounded(volume)
    for name, shape in tools.items():
        other = {
            key: candidate
            for key, candidate in installed.items()
            if key.rsplit("/", 1)[0] != name.rsplit("/", 1)[0]
        }
        if hits := _hits(shape, other):
            tool_hardware_hits[name] = hits
    for (a, sa), (b, sb) in combinations(tools.items(), 2):
        if a.rsplit("/", 1)[0] == b.rsplit("/", 1)[0]:
            continue
        gap = sa.distance(sb)
        tool_gaps[f"{a}|{b}"] = _rounded(gap)
        if (volume := protected._volume(sa, sb)) > VOLUME_TOL_MM3:
            tool_pair_hits[f"{a}|{b}"] = _rounded(volume)

    for name, row in rows.items():
        side = name.rsplit("_", 2)[1]
        allowed = {"base_header", f"base_principal_center_{side}"}
        unrelated = {key: shape for key, shape in wood.items() if key not in allowed}
        roles = solids[name]
        row["protected_hits_mm3"] = {
            role: hit for role, hit in protected.hits(roles, fixed).items() if hit
        }
        row["unrelated_wood_hits_mm3"] = {
            role: hit
            for role, shape in roles.items()
            if (hit := _hits(shape, unrelated))
        }
        row["retained_hardware_hits_mm3"] = {
            role: hit
            for role, shape in roles.items()
            if (hit := _hits(shape, retained))
        }
        row["inherited_service_cutter_hits_mm3"] = {
            role: hit
            for role, shape in roles.items()
            if (
                hit := _hits(
                    shape,
                    {
                        cutter_name: cutter
                        for cutter_name, (member, cutter) in service.items()
                        if member in allowed
                    },
                )
            )
        }
        row["tip_extension_unrelated_wood_hits_mm3"] = _hits(
            extensions[name], unrelated
        )
        row["tip_extension_protected_hits_mm3"] = {
            role: hit
            for role, hit in protected.hits({"tip": extensions[name]}, fixed).items()
            if hit
        }

    min_gap = min(tool_gaps.values())
    min_recess = min(row["barrel_recess_mm"] for row in rows.values())
    shape_failures = {
        name: [
            field
            for field in (
                "barrel_body_in_host_fraction",
                "barrel_cross_bore_past_entry_1mm_in_host_fraction",
                "tip_extension_in_receiver_fraction",
                "joined_wood_bore_core_fraction",
            )
            if row[field] < 0.999
        ]
        for name, row in rows.items()
    }
    clear = (
        min_recess >= TARGET_RECESS_MM
        and min_gap >= TARGET_TOOL_GAP_MM
        and not pair_hits
        and not tool_hardware_hits
        and not tool_pair_hits
        and not any(shape_failures.values())
        and all(
            row["bolt_barrel_intersection_mm3"] > 0
            and row["nominal_tip_beyond_thread_axis_mm"] > 0
            and min(row["head_washer_inside_header_fraction"].values()) >= 0.99999
            and row["driver_residual_header_mm3"] <= VOLUME_TOL_MM3
            and row["barrel_tool_residual_host_mm3"] <= VOLUME_TOL_MM3
            and row["head_pocket_in_principal_mm3"] <= VOLUME_TOL_MM3
            and not row["protected_hits_mm3"]
            and not row["unrelated_wood_hits_mm3"]
            and not row["retained_hardware_hits_mm3"]
            and not row["inherited_service_cutter_hits_mm3"]
            and not row["tip_extension_unrelated_wood_hits_mm3"]
            and not row["tip_extension_protected_hits_mm3"]
            for row in rows.values()
        )
    )
    minimum_pocket_edge = min(
        min(
            row["head_pocket_header_bottom_margin_mm"],
            row["head_pocket_header_top_margin_mm"],
        )
        for row in rows.values()
    )
    maximum_mouth_breakout = max(
        row["barrel_mouth_relief_x_side_breakout_mm"] for row in rows.values()
    )
    minimum_barrel_x_ligament = min(
        row["barrel_radial_x_edge_ligament_mm"] for row in rows.values()
    )
    # There is no source-backed structural acceptance limit for this ligament.
    # Its positive nominal size does not qualify the principal net section.
    barrel_x_ligament_structural_sizing_required = True
    net_section_unqualified = (
        minimum_pocket_edge < 3.0
        or maximum_mouth_breakout > 0
        or barrel_x_ligament_structural_sizing_required
    )
    return {
        "rows": rows,
        "barrel_faces": barrel_faces,
        "entry_zs_mm": entry_zs,
        "header_seat_depth_mm": seat_depth,
        "thread_depth_from_seat_mm": thread_depth,
        "solids": solids,
        "minimum_barrel_recess_mm": min_recess,
        "minimum_head_pocket_header_edge_mm": minimum_pocket_edge,
        "minimum_barrel_radial_x_ligament_mm": minimum_barrel_x_ligament,
        "barrel_x_ligament_structural_sizing_required": (
            barrel_x_ligament_structural_sizing_required
        ),
        "maximum_barrel_mouth_x_side_breakout_mm": maximum_mouth_breakout,
        "net_section_unqualified": net_section_unqualified,
        "minimum_tool_path_gap_mm": min_gap,
        "minimum_principal_pair_tool_gap_mm": min(
            gap
            for key, gap in tool_gaps.items()
            if key.count("clip_split_base_center_") == 2
        ),
        "minimum_head_pocket_pair_gap_mm": min(
            solids[f"barrel_center_clip_split_base_center_{side}_1"][
                "head_pocket"
            ].distance(
                solids[f"barrel_center_clip_split_base_center_{side}_2"]["head_pocket"]
            )
            for side in current.SIDES
        ),
        "tool_path_gaps_mm": tool_gaps,
        "installed_hardware_pair_hits_mm3": pair_hits,
        "tool_to_other_hardware_hits_mm3": tool_hardware_hits,
        "tool_pair_hits_mm3": tool_pair_hits,
        "shape_failures": {k: v for k, v in shape_failures.items() if v},
        "nominal_geometry_disposition": (
            "CLASH"
            if not clear
            else "NOMINAL_TARGETS_ONLY_NET_SECTION_UNQUALIFIED"
            if net_section_unqualified
            else "CLEAR_OCCUPANCY"
        ),
    }


def build():
    """Source-build one broad-face option and the common-5-in length sensitivity."""
    assembly = build_viewer_assembly()
    baseline = current.build(assembly=assembly)
    wood = baseline["wood"]
    service = {}
    relevant = {
        "base_header",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    for member, name, cutter in variant(KERF_RIGHT).service_cutters():
        if member not in relevant:
            continue
        # WidthAdapter delegates service_cutters to the official source. Match
        # the active timber transform, then retain only the removed wood.
        if member in TRANSLATE_NAMES:
            cutter = cutter.translate(cq.Vector(-KERF_RIGHT_MM, 0, 0))
        service[name] = (member, cutter.intersect(wood[member]))
    principal_width = coordinates.local_bounds(wood["base_principal_center_right"])["x"]
    half_width = (principal_width[1] - principal_width[0]) / 2
    dz = SHALLOW_ENTRY_Z_MM[1] - SHALLOW_ENTRY_Z_MM[0]
    offset_sensitivity = {
        str(offset): {
            "nominal_parallel_bolt_tool_gap_mm": _rounded(
                math.hypot(
                    2 * offset,
                    dz * math.cos(math.radians(BOLT_ANGLE_DEG)),
                )
                - center.TOOL_DIAMETER_MM
            ),
            "barrel_radial_x_ligament_mm": _rounded(
                half_width - offset - current.OD / 2
            ),
            "barrel_mouth_relief_x_side_breakout_mm": _rounded(
                BARREL_MOUTH_RELIEF_DIAMETER_MM / 2 - (half_width - offset)
            ),
            "full_collision_rescreened": offset == 12,
        }
        for offset in (11.0, 12.0, 13.0)
    }
    baseline_rows = {}
    for name, shapes in baseline["solids"].items():
        if "clip_split_base_center_" not in name:
            continue
        side = name.rsplit("_", 2)[1]
        baseline_rows[name] = {
            "driver_residual_header_mm3": _rounded(
                protected._volume(
                    shapes["bolt_tool"], wood["base_header"].cut(shapes["head_pocket"])
                )
            ),
            "inherited_service_cutter_hits_mm3": {
                role: hit
                for role, shape in shapes.items()
                if (
                    hit := _hits(
                        shape,
                        {
                            cutter_name: cutter
                            for cutter_name, (member, cutter) in service.items()
                            if member
                            in {
                                "base_header",
                                f"base_principal_center_{side}",
                            }
                        },
                    )
                )
            },
        }
    faces = {"left": ("rear", "rear"), "right": ("rear", "rear")}
    standard = _screen(
        wood,
        assembly,
        baseline["solids"],
        service,
        bolt_lengths=NOMINAL_BOLT_LENGTHS_MM,
        barrel_faces=faces,
        entry_zs=REAR_ENTRY_Z_MM,
        seat_depth=HEAD_SEAT_DEPTH_MM,
        thread_depth=100.0,
    )
    five_in = _screen(
        wood,
        assembly,
        baseline["solids"],
        service,
        bolt_lengths=(127.0, 127.0),
        barrel_faces=faces,
        entry_zs=REAR_ENTRY_Z_MM,
        seat_depth=HEAD_SEAT_DEPTH_MM,
        thread_depth=100.0,
    )
    shallow = _screen(
        wood,
        assembly,
        baseline["solids"],
        service,
        bolt_lengths=NOMINAL_BOLT_LENGTHS_MM,
        barrel_faces=faces,
        entry_zs=SHALLOW_ENTRY_Z_MM,
        seat_depth=SHALLOW_HEAD_SEAT_DEPTH_MM,
        thread_depth=SHALLOW_THREAD_DEPTH_MM,
    )
    shallow_five_in = _screen(
        wood,
        assembly,
        baseline["solids"],
        service,
        bolt_lengths=(127.0, 127.0),
        barrel_faces=faces,
        entry_zs=SHALLOW_ENTRY_Z_MM,
        seat_depth=SHALLOW_HEAD_SEAT_DEPTH_MM,
        thread_depth=SHALLOW_THREAD_DEPTH_MM,
    )
    return {
        "schema": "owner_barrel_center_margin_options/v1",
        "source": "kerf-right model; integrated 4x6 post proof; maintained barrel assembly",
        "protected_counts": protected.inventory()["counts"],
        "baseline": {
            "barrel_recess_mm": 1.049,
            "entry_face": "principal_opposite_x_sides",
            "rows": baseline_rows,
        },
        "offset_sensitivity": offset_sensitivity,
        "broad_face_option": standard,
        "common_5_in_second_row": five_in,
        "shallow_seat_option": shallow,
        "shallow_common_5_in": shallow_five_in,
        "native_solve": False,
        "release_flags": dict(current.RELEASE_FLAGS),
        "limits": "Nominal CAD only; barrel/thread rating, thread engagement, machining tolerances, tool withdrawal, and structural capacity unverified.",
    }
