"""Single-centered principal/header barrel candidate for the integrated posts.

This is a source-built viewer producer, not a drilling or structural release.
The candidate electrical service void comes from owner_barrel_candidate_service;
the maintained 38.1 mm source bore and wiring are not changed here.
"""

from itertools import combinations

import cadquery as cq

from mini_moonboard.box_frame import Connection
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_candidate_service as service
from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_center_margin_options as margin
from scripts import owner_barrel_center_post_joint_replan as integrated
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly

PRINCIPAL_Z_MM = 257.7
PRINCIPAL_BOLT_LENGTH_MM = 4.5 * 25.4
PRINCIPAL_BORE_LENGTH_MM = 5 * 25.4
POST_BOLT_LENGTH_MM = 3.5 * 25.4
BOTTOM_BOLT_LENGTH_MM = 4.5 * 25.4
ANGLE_DEG = 50.0
SEAT_DEPTH_MM = 13.1
THREAD_DEPTH_MM = 100.0
POCKET_LEAD_MM = 13.0
VOLUME_TOL_MM3 = 1.0
RELEASE_FLAGS = {
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, other in targets.items()
        if (volume := protected._volume(shape, other)) > VOLUME_TOL_MM3
    }


def _all_role_hits(roles, targets):
    return {
        role: hits for role, shape in roles.items() if (hits := _hits(shape, targets))
    }


def _candidate_service_voids(wood):
    cutters = service.candidate_service_cutters(variant(KERF_RIGHT), wood)
    voids = {}
    for member, name, cutter in cutters:
        if member not in wood:
            continue
        key = f"{member}/{name}"
        if key in voids:
            raise ValueError(f"Duplicate service cutter: {key}")
        voids[key] = (member, cutter.intersect(wood[member]))
    target = "base_principal_center_right/bore_base_principal_center_right_072"
    if target not in voids or voids[target][1].Volume() <= VOLUME_TOL_MM3:
        raise ValueError("Candidate right F1-G1 service void is missing")
    return voids


def build(*, assembly=None, wood=None):
    """Build two centered principal rows and screen the four center duties."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    base = integrated.build(
        assembly=assembly, wood=wood, post_bolt_length_mm=POST_BOLT_LENGTH_MM
    )
    wood = base["wood"]
    fixed = protected.inventory()
    if fixed["counts"]["panel_screws"] != 66 or fixed["counts"]["frame_bolts"] != 12:
        raise ValueError("Fixed panel/frame axes changed")
    if any(name.startswith("inner_kicker_backer_") for name in wood):
        raise ValueError("Integrated candidate must not contain old backers")

    solids = {
        name: roles
        for name, roles in base["solids"].items()
        if "clip_split_header_center_" in name
    }
    reports = {
        station: {"family": "post_header", "bolts": dict(row["bolts"])}
        for station, row in base["report"]["stations"].items()
        if row["family"] == "post_header"
    }
    tip_extensions = {}
    for side in integrated.SIDES:
        station = f"clip_split_base_center_{side}"
        name, roles, row, tip = margin._pose(
            wood,
            side,
            1,
            x_offset=0.0,
            entry_z=PRINCIPAL_Z_MM,
            bolt_length=PRINCIPAL_BOLT_LENGTH_MM,
            barrel_face="rear",
            seat_depth=SEAT_DEPTH_MM,
            thread_depth=THREAD_DEPTH_MM,
            bolt_angle_deg=ANGLE_DEG,
            pocket_lead_mm=POCKET_LEAD_MM,
            mouth_relief=False,
        )
        # Retain the source bore reach while the nominal shaft is shortened.
        roles["bolt_bore"] = integrated._cylinder(
            row["bolt_seat_xyz_mm"],
            row["bolt_axis_xyz"],
            PRINCIPAL_BORE_LENGTH_MM
            - integrated.WASHER_T
            + margin.BORE_TIP_CLEARANCE_MM,
            center.BORE_DIAMETER_MM,
        )
        row["modeled_bore_depth_past_nominal_tip_mm"] = round(
            PRINCIPAL_BORE_LENGTH_MM
            - PRINCIPAL_BOLT_LENGTH_MM
            + margin.BORE_TIP_CLEARANCE_MM,
            6,
        )
        row["bolt_barrel_intersection_mm3"] = round(
            protected._volume(roles["bolt_bore"], roles["barrel_cross_bore"]), 6
        )
        solids[name] = roles
        reports[station] = {"family": "principal_header", "bolts": {name: row}}
        tip_extensions[name] = tip
    if set(reports) != set(integrated.STATIONS) or len(solids) != 6:
        raise ValueError("Expected four occupied integrated center duties")

    service_voids = _candidate_service_voids(wood)
    retained = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] not in integrated.STATIONS
    }
    retained.update(
        {
            f"stack/{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            if assembly["bolt_station"][name] not in integrated.STATIONS
            for role, shape in stack.items()
        }
    )
    installed = {
        f"{name}/{role}": shape
        for name, roles in solids.items()
        for role, shape in roles.items()
        if role in ("shaft", "barrel", "washer", "head")
    }
    tools = {
        f"{name}/{role}": shape
        for name, roles in solids.items()
        for role, shape in roles.items()
        if role in ("bolt_tool", "barrel_tool")
    }
    pair_hits = {}
    for (first, a), (second, b) in combinations(installed.items(), 2):
        if first.rsplit("/", 1)[0] != second.rsplit("/", 1)[0]:
            volume = protected._volume(a, b)
            if volume > VOLUME_TOL_MM3:
                pair_hits[f"{first}|{second}"] = round(volume, 6)
    tool_hardware_hits = {
        name: hits
        for name, shape in tools.items()
        if (
            hits := _hits(
                shape,
                {
                    other: candidate
                    for other, candidate in installed.items()
                    if other.rsplit("/", 1)[0] != name.rsplit("/", 1)[0]
                },
            )
        )
    }
    tool_pair_hits = {}
    for (first, a), (second, b) in combinations(tools.items(), 2):
        if first.rsplit("/", 1)[0] != second.rsplit("/", 1)[0]:
            volume = protected._volume(a, b)
            if volume > VOLUME_TOL_MM3:
                tool_pair_hits[f"{first}|{second}"] = round(volume, 6)

    role_to_other_hardware = {}
    for station, station_report in reports.items():
        side = station.rsplit("_", 1)[1]
        hosts = {
            "base_header",
            f"base_post_center_{side}"
            if station_report["family"] == "post_header"
            else f"base_principal_center_{side}",
        }
        unrelated = {name: shape for name, shape in wood.items() if name not in hosts}
        local_service = {
            name: shape
            for name, (member, shape) in service_voids.items()
            if member in hosts
        }
        for name, row in station_report["bolts"].items():
            roles = solids[name]
            row["protected_hits_mm3"] = {
                role: hits
                for role, hits in protected.hits(roles, fixed).items()
                if hits
            }
            row["unrelated_wood_hits_mm3"] = _all_role_hits(roles, unrelated)
            row["retained_hardware_hits_mm3"] = _all_role_hits(roles, retained)
            row["candidate_service_void_hits_mm3"] = _all_role_hits(
                roles, local_service
            )
            # The barrel and bolt deliberately meet; only different rows count.
            for role, shape in roles.items():
                other = {
                    key: candidate
                    for key, candidate in installed.items()
                    if key.rsplit("/", 1)[0] != name
                }
                if hits := _hits(shape, other):
                    role_to_other_hardware[f"{name}/{role}"] = hits
            if "head_pocket" in roles:
                row["driver_residual_header_mm3"] = round(
                    protected._volume(
                        roles["bolt_tool"],
                        wood["base_header"].cut(roles["head_pocket"]),
                    ),
                    6,
                )
            if name in tip_extensions:
                tip = tip_extensions[name]
                row["tip_extension_unrelated_wood_hits_mm3"] = _hits(tip, unrelated)
                row["tip_extension_protected_hits_mm3"] = {
                    role: hits
                    for role, hits in protected.hits({"tip": tip}, fixed).items()
                    if hits
                }

    row_clashes = any(
        row["protected_hits_mm3"]
        or row["unrelated_wood_hits_mm3"]
        or row["retained_hardware_hits_mm3"]
        or row["candidate_service_void_hits_mm3"]
        or row["joined_wood_bore_core_fraction"] < 0.999
        or row["tip_extension_in_receiver_fraction"] < 0.999
        or row["barrel_body_in_host_fraction"] < 0.999
        or row.get("barrel_cross_bore_past_entry_1mm_in_host_fraction", 1) < 0.999
        or row.get("tip_extension_unrelated_wood_hits_mm3")
        or row.get("tip_extension_protected_hits_mm3")
        or row.get("driver_residual_header_mm3", 0) > VOLUME_TOL_MM3
        or row.get("head_pocket_in_principal_mm3", 0) > VOLUME_TOL_MM3
        or row.get("external_barrel_tool_mouth_residual_host_mm3", 0) > VOLUME_TOL_MM3
        or (
            row.get("head_washer_inside_header_fraction")
            and min(row["head_washer_inside_header_fraction"].values()) < 0.999
        )
        for station in reports.values()
        for row in station["bolts"].values()
    )
    clash = bool(
        row_clashes
        or pair_hits
        or tool_hardware_hits
        or tool_pair_hits
        or role_to_other_hardware
    )
    return {
        "wood": wood,
        "solids": solids,
        "service_voids": service_voids,
        "report": {
            "schema": "owner_barrel_center_single_layout/v1",
            "stations": reports,
            "protected_counts": fixed["counts"],
            "candidate_service_void": "right_072_same_axis_25.4_mm_provisional",
            "historical_service_diameter_mm": 38.1,
            "candidate_service_diameter_mm": 25.4,
            "installed_hardware_pair_hits_mm3": pair_hits,
            "tool_to_other_hardware_hits_mm3": tool_hardware_hits,
            "tool_pair_hits_mm3": tool_pair_hits,
            "role_to_other_hardware_hits_mm3": role_to_other_hardware,
            "nominal_geometry_disposition": (
                "CLASH" if clash else "CANDIDATE_ONLY_UNVERIFIED"
            ),
            "native_solve": False,
            "structural_capacity_verified": False,
            "assembly_moment_transfer_verified": False,
            "service_feed_qualified": False,
            "release_flags": dict(RELEASE_FLAGS),
            "unverified": {
                "service_feed_and_strength": True,
                "barrel_thread_engagement_and_strength": True,
                "barrel_insertion_orientation": True,
                "single_connector_moment_transfer_and_stiffness": True,
                "header_pocket_edge_and_wood_net_section": True,
            },
            "tool_scope": "Exterior driver and barrel-mouth approach only; recessed barrel insertion and orientation are not screened.",
        },
    }


def build_layout(wood):
    """Assembly-compatible four affected rows; two bottom duties are unchanged."""
    trial = build(wood=wood)
    report, solids = trial["report"], trial["solids"]
    stations = {}
    for station, station_report in report["stations"].items():
        bolts, barrels, stacks, drilling, access = {}, {}, {}, {}, {}
        for name, row in station_report["bolts"].items():
            shapes = solids[name]
            bolt_name = f"{name}_bolt"
            seat, axis = row["bolt_seat_xyz_mm"], row["bolt_axis_xyz"]
            side = station.rsplit("_", 1)[1]
            hosts = (
                "base_header",
                f"base_post_center_{side}"
                if station_report["family"] == "post_header"
                else f"base_principal_center_{side}",
            )
            bolts[bolt_name] = Connection(
                bolt_name,
                cq.Vector(*integrated._add(seat, axis, -integrated.WASHER_T)),
                cq.Vector(*axis),
                row["bolt_length_mm"],
                center.hardware.THREAD_MAJOR_MM,
                hosts,
                "bolt",
            )
            barrels[name] = shapes["barrel"]
            stacks[bolt_name] = {
                role: shapes[role] for role in ("shaft", "washer", "head")
            }
            drilling[f"{name}/bolt_bore"] = shapes["bolt_bore"]
            drilling[f"{name}/barrel_cross_bore"] = shapes["barrel_cross_bore"]
            if "head_pocket" in shapes:
                drilling[f"{name}/head_pocket"] = shapes["head_pocket"]
            access[f"{name}/bolt_tool"] = shapes["bolt_tool"]
            access[f"{name}/barrel_tool"] = shapes["barrel_tool"]
        stations[station] = {
            "mode": "direct",
            "axis_offset_mm": integrated.OFFSET,
            "disposition": "REVISE"
            if report["nominal_geometry_disposition"] == "CLASH"
            else "VIEWER_ONLY_UNVERIFIED",
            "bolts": bolts,
            "barrels": barrels,
            "stacks": stacks,
            "drilling_paths": drilling,
            "access_paths": access,
        }
    return {"stations": stations, "diagnostics": report}


def build_six_layout(wood):
    """Export-wrapper adapter with shorter bottom shafts and unchanged bores."""
    _, former_wood, _ = center._wood()
    former = center.build_revised_layout(former_wood)
    revised = build_layout(wood)
    bottom = {}
    for station, row in former["stations"].items():
        if not station.startswith("clip_horizontal_bottom_"):
            continue
        bolts, stacks = {}, {}
        for name, bolt in row["bolts"].items():
            bolts[name] = Connection(
                name,
                bolt.start,
                bolt.direction,
                BOTTOM_BOLT_LENGTH_MM,
                bolt.diameter,
                bolt.members,
                bolt.kind,
            )
            stacks[name] = {
                **row["stacks"][name],
                "shaft": center._cylinder(
                    bolt.start.toTuple(),
                    bolt.direction.toTuple(),
                    BOTTOM_BOLT_LENGTH_MM,
                    bolt.diameter,
                ),
            }
        bottom[station] = {**row, "bolts": bolts, "stacks": stacks}
    if len(bottom) != 2 or len(revised["stations"]) != 4:
        raise ValueError("Expected six nonempty center duties")
    return {
        "stations": {**bottom, **revised["stations"]},
        "diagnostics": {
            "source_id": "integrated-center-single-candidate",
            "unchanged_bottom": former["diagnostics"],
            "integrated_bottom_bolt_length_mm": BOTTOM_BOLT_LENGTH_MM,
            "revised_center": revised["diagnostics"],
        },
    }
