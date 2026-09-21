"""PB03 lower-service corner-block core; geometry only, no release."""

import math
from dataclasses import dataclass
from itertools import combinations

import cadquery as cq

from mini_moonboard.box_frame import Connection
from scripts import simple_rail_joint_comparison as pb01
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT

EXPECTED_PB02_FINGERPRINT = (
    "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
)
TARGET_STATIONS = (
    "clip_horizontal_lower_left_2",
    "clip_horizontal_lower_right_1",
)
LOWER_OUTER_STATIONS = (
    "clip_horizontal_lower_left_1",
    "clip_horizontal_lower_right_2",
)
ALL_TARGET_STATIONS = (*TARGET_STATIONS, *LOWER_OUTER_STATIONS)
BLOCK_NAMES = {
    TARGET_STATIONS[0]: "pb03_lower_center_left_block",
    TARGET_STATIONS[1]: "pb03_lower_center_right_block",
}
ALL_BLOCK_NAMES = {
    **BLOCK_NAMES,
    LOWER_OUTER_STATIONS[0]: "pb03_lower_outer_left_block",
    LOWER_OUTER_STATIONS[1]: "pb03_lower_outer_right_block",
}
BLOCK_X_MM = 139.7
BLOCK_T_MM = 57.15
BLOCK_LENGTH_MM = 300.0
BOLT_DIAMETER_MM = 6.35
BORE_DIAMETER_MM = 7.5
WASHER_DIAMETER_MM = 25.4
HEAD_NUT_DIAMETER_MM = 18.0
TOOL_DIAMETER_MM = 40.0
TOOL_DEPTH_MM = 40.0
END_ALLOWANCE_MM = 2.5
TOL_MM3 = 1.0
UPRIGHT_N_OFFSETS_MM = (55.159, 100.159)
RAIL_N_OFFSET_MM = 80.159
RAIL_X_OFFSETS_MM = (70.0, 110.0)


@dataclass(frozen=True)
class StationSpec:
    """Declarative identity and orientation for one actual kerf-right station."""

    station: str
    frame_side: str
    rail_extension_direction: str
    physical_rail_end: str
    upright_name: str
    rail_name: str
    block_name: str
    bolt_prefix: str


STATION_SPECS = {
    TARGET_STATIONS[0]: StationSpec(
        TARGET_STATIONS[0],
        "left",
        "left",
        "right",
        "base_principal_center_left",
        "base_rail_service_lower_left",
        BLOCK_NAMES[TARGET_STATIONS[0]],
        "pb03_left",
    ),
    TARGET_STATIONS[1]: StationSpec(
        TARGET_STATIONS[1],
        "right",
        "right",
        "left",
        "base_principal_center_right",
        "base_rail_service_lower_right",
        BLOCK_NAMES[TARGET_STATIONS[1]],
        "pb03_right",
    ),
    LOWER_OUTER_STATIONS[0]: StationSpec(
        LOWER_OUTER_STATIONS[0],
        "left",
        "right",
        "left",
        "base_side_left",
        "base_rail_service_lower_left",
        ALL_BLOCK_NAMES[LOWER_OUTER_STATIONS[0]],
        "pb03_lower_outer_left",
    ),
    LOWER_OUTER_STATIONS[1]: StationSpec(
        LOWER_OUTER_STATIONS[1],
        "right",
        "left",
        "right",
        "base_side_right",
        "base_rail_service_lower_right",
        ALL_BLOCK_NAMES[LOWER_OUTER_STATIONS[1]],
        "pb03_lower_outer_right",
    ),
}
# Backward-compatible view used by the first-slice tests and downstream readers.
STATION_MEMBERS = {
    name: (spec.rail_extension_direction, spec.upright_name, spec.rail_name)
    for name, spec in STATION_SPECS.items()
}


@dataclass(frozen=True)
class StationGeometry:
    """One independently derived station and its unselected stack envelopes."""

    station: str
    frame_side: str
    rail_extension_direction: str
    physical_rail_end: str
    upright_name: str
    rail_name: str
    block_name: str
    block: cq.Shape
    block_length_mm: float
    source_rail_length_mm: float
    bolts: tuple[Connection, ...]
    stacks: dict[str, dict[str, cq.Shape]]
    bores: dict[str, cq.Shape]
    tools: dict[str, dict[str, cq.Shape]]
    report: dict

    @property
    def side(self):
        """Backward-compatible physical frame-side label for existing viewers."""
        return self.frame_side


def _cylinder(point, direction, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2,
        length,
        cq.Vector(*point),
        cq.Vector(*direction),
    )


def _shift(point, direction, distance):
    return tuple(point[index] + direction[index] * distance for index in range(3))


def _contact_area(moving, stationary, inward, epsilon=0.1):
    offset = tuple(axis * epsilon for axis in inward)
    return moving.translate(offset).intersect(stationary).Volume() / epsilon


def _hits(shape, solids):
    return {
        name: round(volume, 6)
        for name, other in solids.items()
        if (volume := shape.intersect(other).Volume()) > TOL_MM3
    }


def _intersection_volume(first, second):
    """Return exact common volume after a conservative bounding-box rejection."""
    left, right = first.BoundingBox(), second.BoundingBox()
    if (
        left.xmax < right.xmin
        or right.xmax < left.xmin
        or left.ymax < right.ymin
        or right.ymax < left.ymin
        or left.zmax < right.zmin
        or right.zmax < left.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def _stack(
    name,
    wood_start,
    direction,
    wood_grip,
    members,
    *,
    bolt_diameter_mm=BOLT_DIAMETER_MM,
    bore_diameter_mm=BORE_DIAMETER_MM,
):
    """Create a complete display/check stack with deliberately generic hardware."""
    if (
        not math.isfinite(bolt_diameter_mm)
        or not math.isfinite(bore_diameter_mm)
        or bolt_diameter_mm <= 0
        or bore_diameter_mm <= bolt_diameter_mm
    ):
        raise ValueError("PB03 requires a positive bore larger than the bolt shaft")
    reverse = tuple(-value for value in direction)
    bore_start = _shift(wood_start, reverse, END_ALLOWANCE_MM)
    bore_length = wood_grip + 2 * END_ALLOWANCE_MM
    wood_end = _shift(wood_start, direction, wood_grip)
    shaft = _cylinder(bore_start, direction, bore_length, bolt_diameter_mm)
    bore = _cylinder(bore_start, direction, bore_length, bore_diameter_mm)
    near_washer = _cylinder(
        _shift(wood_start, reverse, 2.0), direction, 2.0, WASHER_DIAMETER_MM
    )
    far_washer = _cylinder(wood_end, direction, 2.0, WASHER_DIAMETER_MM)
    head = _cylinder(
        _shift(wood_start, reverse, 8.0), direction, 6.0, HEAD_NUT_DIAMETER_MM
    )
    nut = _cylinder(
        _shift(wood_end, direction, 2.0), direction, 9.0, HEAD_NUT_DIAMETER_MM
    )
    tools = {
        "near": _cylinder(wood_start, reverse, TOOL_DEPTH_MM, TOOL_DIAMETER_MM),
        "far": _cylinder(
            _shift(wood_end, direction, 2.0),
            direction,
            TOOL_DEPTH_MM,
            TOOL_DIAMETER_MM,
        ),
    }
    connection = Connection(
        name,
        cq.Vector(*bore_start),
        cq.Vector(*direction),
        bore_length,
        bolt_diameter_mm,
        members,
        "bolt",
        wood_grip,
    )
    return (
        connection,
        {
            "shaft": shaft,
            "head": head,
            "near_washer": near_washer,
            "far_washer": far_washer,
            "nut": nut,
        },
        bore,
        tools,
    )


def _fixed_axis_solids(panel_connections):
    if (
        len(panel_connections) != 66
        or len({row.name for row in panel_connections}) != 66
    ):
        raise ValueError("PB03 requires exactly 66 unique fixed panel/kicker axes")
    return {
        row.name: cq.Solid.makeCylinder(
            row.diameter / 2,
            row.length,
            row.start,
            row.direction,
        )
        for row in panel_connections
    }


def _bore_pair_hits(bores):
    hits = {}
    names = list(bores)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            volume = bores[first].intersect(bores[second]).Volume()
            if volume > TOL_MM3:
                hits[f"{first}|{second}"] = round(volume, 6)
    return hits


def _build_station(
    spec,
    parts,
    finished_parts,
    fixed_axes,
    *,
    rail_n_offset_mm=RAIL_N_OFFSET_MM,
    bolt_diameter_mm=BOLT_DIAMETER_MM,
    bore_diameter_mm=BORE_DIAMETER_MM,
    block_length_mm=BLOCK_LENGTH_MM,
):
    if not math.isfinite(block_length_mm) or block_length_mm <= 0:
        raise ValueError("PB03 block length must be positive and finite")
    station = spec.station
    extension = spec.rail_extension_direction
    upright_name, rail_name = spec.upright_name, spec.rail_name
    upright, rail = parts[upright_name], parts[rail_name]
    ub, rb = upright.BoundingBox(), rail.BoundingBox()
    rail_t = [vertex.Y * pb01.T[0] + vertex.Z * pb01.T[1] for vertex in rail.Vertices()]
    rail_n = [vertex.Y * pb01.N[0] + vertex.Z * pb01.N[1] for vertex in rail.Vertices()]
    t_face, n_front = max(rail_t), min(rail_n)
    if extension == "right":
        butt = ub.xmax
        rail_butt = rb.xmin
        if spec.physical_rail_end != "left" or not math.isclose(
            rail_butt, butt, abs_tol=1e-6
        ):
            raise ValueError(f"{station}: actual right butt faces changed")
        block_x, outward = butt, 1.0
    else:
        butt = ub.xmin
        rail_butt = rb.xmax
        if spec.physical_rail_end != "right" or not math.isclose(
            rail_butt, butt, abs_tol=1e-6
        ):
            raise ValueError(f"{station}: actual left butt faces changed")
        block_x, outward = butt - BLOCK_X_MM, -1.0
    base_y, base_z = pb01._yz(t_face, n_front)
    block = (
        cq.Solid.makeBox(
            BLOCK_X_MM,
            BLOCK_T_MM,
            block_length_mm,
            cq.Vector(block_x, 0, 0),
        )
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, base_y, base_z))
    )

    bolts = []
    stacks = {}
    bores = {}
    tools = {}
    specs = []
    for index, offset in enumerate(UPRIGHT_N_OFFSETS_MM, 1):
        n_center = n_front + offset
        y, z = pb01._yz(t_face + BLOCK_T_MM / 2, n_center)
        if extension == "right":
            wood_start = (ub.xmin, y, z)
            direction = (1.0, 0.0, 0.0)
        else:
            wood_start = (ub.xmax, y, z)
            direction = (-1.0, 0.0, 0.0)
        specs.append(
            (
                f"{spec.bolt_prefix}_upright_{index}",
                wood_start,
                direction,
                ub.xlen + BLOCK_X_MM,
                (upright_name, spec.block_name),
            )
        )
    for index, x_offset in enumerate(RAIL_X_OFFSETS_MM, 1):
        n_center = n_front + rail_n_offset_mm
        y, z = pb01._yz(min(rail_t), n_center)
        x = rb.xmin + x_offset if extension == "right" else rb.xmax - x_offset
        specs.append(
            (
                f"{spec.bolt_prefix}_rail_{index}",
                (x, y, z),
                (0.0, *pb01.T),
                38.1 + BLOCK_T_MM,
                (rail_name, spec.block_name),
            )
        )
    for name, start, direction, grip, members in specs:
        bolt, stack, bore, access = _stack(
            name,
            start,
            direction,
            grip,
            members,
            bolt_diameter_mm=bolt_diameter_mm,
            bore_diameter_mm=bore_diameter_mm,
        )
        bolts.append(bolt)
        stacks[name] = stack
        bores[name] = bore
        tools[name] = access

    hosts = {upright_name: upright, rail_name: rail, spec.block_name: block}
    panel_parts = {
        name: shape
        for name, shape in finished_parts.items()
        if name.startswith(("main_", "kicker_"))
    }
    timber_parts = {
        name: shape for name, shape in finished_parts.items() if name not in panel_parts
    }
    unrelated_timber = {
        name: shape
        for name, shape in timber_parts.items()
        if name not in {upright_name, rail_name}
    }
    block_timber_hits = _hits(block, unrelated_timber)
    block_panel_hits = _hits(block, panel_parts)
    block_fixed_axis_hits = _hits(block, fixed_axes)
    complete_bores = {}
    bore_timber_hits = {}
    bore_panel_hits = {}
    bore_fixed_axis_hits = {}
    stack_timber_hits = {}
    stack_panel_hits = {}
    stack_fixed_axis_hits = {}
    tool_timber_hits = {}
    tool_panel_hits = {}
    tool_fixed_axis_hits = {}
    tool_host_intrusions = {}
    for bolt in bolts:
        bore = bores[bolt.name]
        expected = {
            bolt.members[0]: (ub.xlen if bolt.members[0] == upright_name else 38.1),
            bolt.members[1]: (
                BLOCK_X_MM if bolt.members[0] == upright_name else BLOCK_T_MM
            ),
        }
        complete_bores[bolt.name] = all(
            abs(
                bore.intersect(hosts[member]).Volume()
                - math.pi * (bore_diameter_mm / 2) ** 2 * length
            )
            <= TOL_MM3
            for member, length in expected.items()
        )
        bolt_unrelated_timber = {
            name: shape
            for name, shape in timber_parts.items()
            if name not in bolt.members
        }
        bore_timber_hits[bolt.name] = _hits(bore, bolt_unrelated_timber)
        bore_panel_hits[bolt.name] = _hits(bore, panel_parts)
        bore_fixed_axis_hits[bolt.name] = _hits(bore, fixed_axes)
        stack_timber_hits[bolt.name] = {
            role: _hits(shape, bolt_unrelated_timber)
            for role, shape in stacks[bolt.name].items()
        }
        stack_panel_hits[bolt.name] = {
            role: _hits(shape, panel_parts) for role, shape in stacks[bolt.name].items()
        }
        stack_fixed_axis_hits[bolt.name] = {
            role: _hits(shape, fixed_axes) for role, shape in stacks[bolt.name].items()
        }
        tool_timber_hits[bolt.name] = {
            end: _hits(shape, bolt_unrelated_timber)
            for end, shape in tools[bolt.name].items()
        }
        tool_panel_hits[bolt.name] = {
            end: _hits(shape, panel_parts) for end, shape in tools[bolt.name].items()
        }
        tool_fixed_axis_hits[bolt.name] = {
            end: _hits(shape, fixed_axes) for end, shape in tools[bolt.name].items()
        }
        intended_hosts = {
            name: (block if name == spec.block_name else finished_parts[name])
            for name in bolt.members
        }
        tool_host_intrusions[bolt.name] = {
            end: _hits(shape, intended_hosts) for end, shape in tools[bolt.name].items()
        }
    same_bore_hits = _bore_pair_hits(bores)
    pair_hits = {}
    bolt_names = [bolt.name for bolt in bolts]
    for index, first in enumerate(bolt_names):
        for second in bolt_names[index + 1 :]:
            hits = {}
            for first_role, first_shape in stacks[first].items():
                for second_role, second_shape in stacks[second].items():
                    volume = first_shape.intersect(second_shape).Volume()
                    if volume > TOL_MM3:
                        hits[f"{first_role}|{second_role}"] = round(volume, 6)
            pair_hits[f"{first}|{second}"] = hits
    contact = {
        "rail": _contact_area(block, rail, (0, -pb01.T[0], -pb01.T[1])),
        "upright": _contact_area(block, upright, (-outward, 0, 0)),
    }
    report = {
        "station": station,
        "side": spec.frame_side,
        "frame_side": spec.frame_side,
        "rail_extension_direction": spec.rail_extension_direction,
        "physical_rail_end": spec.physical_rail_end,
        "butt_faces_x_mm": {
            "upright": round(butt, 6),
            "rail": round(rail_butt, 6),
        },
        "butt_faces_coincident": math.isclose(rail_butt, butt, abs_tol=1e-6),
        "actual_member_names": [upright_name, rail_name],
        "source_rail_length_mm": rb.xlen,
        "rail_bore_n_offset_mm": rail_n_offset_mm,
        "bolt_diameter_mm": bolt_diameter_mm,
        "bore_diameter_mm": bore_diameter_mm,
        "block_dimensions_mm": [BLOCK_X_MM, BLOCK_T_MM, block_length_mm],
        "contact_area_mm2": contact,
        "contact_verified": all(value > 0 for value in contact.values()),
        "complete_bores_by_bolt": complete_bores,
        "complete_bores": all(complete_bores.values()),
        "block_unrelated_timber_hits_mm3": block_timber_hits,
        "block_finished_panel_hits_mm3": block_panel_hits,
        "block_fixed_axis_hits_mm3": block_fixed_axis_hits,
        "bore_unrelated_timber_hits_mm3": bore_timber_hits,
        "bore_finished_panel_hits_mm3": bore_panel_hits,
        "bore_fixed_axis_hits_mm3": bore_fixed_axis_hits,
        "same_station_bore_hits_mm3": same_bore_hits,
        "stack_unrelated_timber_hits_mm3": stack_timber_hits,
        "stack_finished_panel_hits_mm3": stack_panel_hits,
        "stack_fixed_axis_hits_mm3": stack_fixed_axis_hits,
        "tool_unrelated_timber_hits_mm3": tool_timber_hits,
        "tool_finished_panel_hits_mm3": tool_panel_hits,
        "tool_fixed_axis_hits_mm3": tool_fixed_axis_hits,
        "tool_intended_host_intrusion_mm3": tool_host_intrusions,
        "tool_seat_path_basis": (
            "Each 40-mm tool cylinder begins at its modeled exterior seat and "
            "extends only outward; any volume in either intended host fails."
        ),
        "tool_seat_paths_clear": not any(
            any(hits.values()) for hits in tool_host_intrusions.values()
        ),
        "cross_stack_hits_mm3": pair_hits,
        "collision_clear": not block_timber_hits
        and not block_panel_hits
        and not block_fixed_axis_hits
        and not any(bore_timber_hits.values())
        and not any(bore_panel_hits.values())
        and not any(bore_fixed_axis_hits.values())
        and not same_bore_hits
        and not any(any(hits.values()) for hits in stack_timber_hits.values())
        and not any(any(hits.values()) for hits in stack_panel_hits.values())
        and not any(any(hits.values()) for hits in stack_fixed_axis_hits.values())
        and not any(pair_hits.values()),
        "access_clear": not any(
            any(hits.values()) for hits in tool_timber_hits.values()
        )
        and not any(any(hits.values()) for hits in tool_panel_hits.values())
        and not any(any(hits.values()) for hits in tool_fixed_axis_hits.values())
        and not any(any(hits.values()) for hits in tool_host_intrusions.values()),
        "exact_retail_hardware_selected": False,
        "drilling_released": False,
    }
    return StationGeometry(
        station,
        spec.frame_side,
        spec.rail_extension_direction,
        spec.physical_rail_end,
        upright_name,
        rail_name,
        spec.block_name,
        block,
        block_length_mm,
        rb.xlen,
        tuple(bolts),
        stacks,
        bores,
        tools,
        report,
    )


def _source_inventory():
    from scripts.simple_center_pb02_native import PB02Native

    module = PB02Native()
    parts = {part.name: part.shape for part in module.uncut_wood_parts()}
    finished_parts = {part.name: part.shape for part in module.wood_parts()}
    if set(parts) != set(finished_parts):
        raise ValueError("PB02 uncut and finished wood inventories differ")
    finished_panels = {
        name for name in finished_parts if name.startswith(("main_", "kicker_"))
    }
    if len(finished_panels) != 6:
        raise ValueError("PB03 requires six explicit finished panel solids")
    connections = tuple(module.connections())
    stations = tuple(module.stations())
    panel_names = {row.name for row in module.raw.panel_connections()}
    panels = tuple(row for row in connections if row.name in panel_names)
    return parts, finished_parts, panels, stations, connections


def _build_targets(
    target_stations,
    *,
    parts=None,
    finished_parts=None,
    panel_connections=None,
    stations=None,
    connections=None,
    bolt_diameter_mm=BOLT_DIAMETER_MM,
    bore_diameter_mm=BORE_DIAMETER_MM,
):
    """Build declared stations separately and reject changed source inventory."""
    target_stations = tuple(target_stations)
    if (
        not target_stations
        or len(set(target_stations)) != len(target_stations)
        or not set(target_stations) <= set(STATION_SPECS)
    ):
        raise ValueError("PB03 target station declaration changed")
    if ACTIVE_FINGERPRINT != EXPECTED_PB02_FINGERPRINT:
        raise ValueError("PB02 geometry fingerprint changed before PB03")
    if any(
        value is None
        for value in (
            parts,
            finished_parts,
            panel_connections,
            stations,
            connections,
        )
    ):
        if not all(
            value is None
            for value in (
                parts,
                finished_parts,
                panel_connections,
                stations,
                connections,
            )
        ):
            raise ValueError(
                "PB03 source inventory must be supplied as one complete set"
            )
        parts, finished_parts, panel_connections, stations, connections = (
            _source_inventory()
        )
    station_names = {row[0] for row in stations}
    if len(station_names) != 22 or not set(target_stations) <= station_names:
        raise ValueError("PB03 requires the exact 22-station PB02 source inventory")
    target_sds = [
        row
        for row in connections
        if any(row.name.startswith(f"{name}_") for name in target_stations)
    ]
    expected_sds = 6 * len(target_stations)
    if len(target_sds) != expected_sds or any(
        row.kind != "screw" for row in target_sds
    ):
        raise ValueError(
            f"PB03 target stations must own exactly {expected_sds} SDS axes"
        )
    fixed_axes = _fixed_axis_solids(panel_connections)
    required_parts = {
        member
        for station in target_stations
        for member in (
            STATION_SPECS[station].upright_name,
            STATION_SPECS[station].rail_name,
        )
    }
    if not required_parts <= set(parts):
        raise ValueError("PB03 target member inventory changed")
    if set(parts) != set(finished_parts):
        raise ValueError("PB03 finished-part inventory changed")
    if (
        len([name for name in finished_parts if name.startswith(("main_", "kicker_"))])
        != 6
    ):
        raise ValueError("PB03 finished-panel inventory changed")
    return {
        station: _build_station(
            STATION_SPECS[station],
            parts,
            finished_parts,
            fixed_axes,
            bolt_diameter_mm=bolt_diameter_mm,
            bore_diameter_mm=bore_diameter_mm,
        )
        for station in target_stations
    }


def build_pair(**kwargs):
    """Build the original lower-center pair with its established public behavior."""
    return _build_targets(TARGET_STATIONS, **kwargs)


def build_core_slice(**kwargs):
    """Build both lower-service pairs from the actual kerf-right members."""
    return _build_targets(ALL_TARGET_STATIONS, **kwargs)


def _receiver_support(panel_connections, parts):
    support = {}
    for row in panel_connections:
        receiver = row.members[1]
        if receiver not in parts:
            support[row.name] = False
            continue
        axis = cq.Solid.makeCylinder(
            row.diameter / 2, row.length, row.start, row.direction
        )
        support[row.name] = axis.intersect(parts[receiver]).Volume() > TOL_MM3
    return support


def _screen_targets(geometries, target_stations, schema):
    """Apply every local and cross-station gate to the declared station set."""
    target_stations = tuple(target_stations)
    parts, _, panel_connections, stations, connections = _source_inventory()
    # Finished receivers contain the modeled screw openings, so positive backing
    # is proved against the matching uncut receiver while panel-clearance checks
    # above use the explicit finished panel solids.
    support = _receiver_support(panel_connections, parts)
    rows = {name: geometry.report for name, geometry in geometries.items()}
    cross_station_bore_hits = {}
    ordered = [geometries[name] for name in target_stations]
    station_pairs = tuple(combinations(ordered, 2))
    for first, second in station_pairs:
        for first_name, first_bore in first.bores.items():
            for second_name, second_bore in second.bores.items():
                volume = _intersection_volume(first_bore, second_bore)
                if volume > TOL_MM3:
                    cross_station_bore_hits[f"{first_name}|{second_name}"] = round(
                        volume, 6
                    )
    all_bore_pairs_clear = not cross_station_bore_hits and all(
        not row["same_station_bore_hits_mm3"] for row in rows.values()
    )
    cross_station_block_hits = {}
    cross_station_stack_block_hits = {}
    cross_station_stack_component_hits = {}
    cross_station_tool_opposite_hits = {}
    for first, second in station_pairs:
        block_volume = _intersection_volume(first.block, second.block)
        if block_volume > TOL_MM3:
            key = f"{first.block_name}|{second.block_name}"
            cross_station_block_hits[key] = round(block_volume, 6)
        for source, opposite in ((first, second), (second, first)):
            for stack_name, components in source.stacks.items():
                for role, component in components.items():
                    volume = _intersection_volume(component, opposite.block)
                    if volume > TOL_MM3:
                        key = f"{stack_name}/{role}|{opposite.block_name}"
                        cross_station_stack_block_hits[key] = round(volume, 6)
            for tool_name, ends in source.tools.items():
                for end, tool in ends.items():
                    volume = _intersection_volume(tool, opposite.block)
                    if volume > TOL_MM3:
                        key = f"{tool_name}/{end}|{opposite.block_name}"
                        cross_station_tool_opposite_hits[key] = round(volume, 6)
                    for stack_name, components in opposite.stacks.items():
                        for role, component in components.items():
                            volume = _intersection_volume(tool, component)
                            if volume > TOL_MM3:
                                key = f"{tool_name}/{end}|{stack_name}/{role}"
                                cross_station_tool_opposite_hits[key] = round(volume, 6)
        for first_stack, first_components in first.stacks.items():
            for second_stack, second_components in second.stacks.items():
                for first_role, first_component in first_components.items():
                    for second_role, second_component in second_components.items():
                        volume = _intersection_volume(first_component, second_component)
                        if volume > TOL_MM3:
                            key = (
                                f"{first_stack}/{first_role}|"
                                f"{second_stack}/{second_role}"
                            )
                            cross_station_stack_component_hits[key] = round(volume, 6)
    all_stacks_mutually_clear = (
        not cross_station_block_hits
        and not cross_station_stack_block_hits
        and not cross_station_stack_component_hits
    )
    all_cross_station_access_paths_clear = not cross_station_tool_opposite_hits
    gates = [
        tuple(geometries) == target_stations,
        len(geometries) == len(target_stations),
        sum(len(item.bolts) for item in geometries.values())
        == 4 * len(target_stations),
        len({bolt.name for item in geometries.values() for bolt in item.bolts})
        == 4 * len(target_stations),
        len(panel_connections) == 66,
        all(support.values()),
        all(row["butt_faces_coincident"] for row in rows.values()),
        all(row["contact_verified"] for row in rows.values()),
        all(row["complete_bores"] for row in rows.values()),
        all(row["collision_clear"] for row in rows.values()),
        all(row["access_clear"] for row in rows.values()),
        all_bore_pairs_clear,
        all_stacks_mutually_clear,
        all_cross_station_access_paths_clear,
    ]
    result = {
        "schema": schema,
        "pb02_source_fingerprint": ACTIVE_FINGERPRINT,
        "target_stations": list(target_stations),
        "inventory": {
            "target_legacy_stations": len(target_stations),
            "removed_legacy_sds_axes": 6 * len(target_stations),
            "added_timber_blocks": len(geometries),
            "added_through_bolt_stacks": sum(
                len(item.stacks) for item in geometries.values()
            ),
            "fixed_panel_kicker_axes": len(panel_connections),
        },
        "source_legacy_stations": len(stations),
        "source_connection_count": len(connections),
        "stations": rows,
        "finished_panel_solids": 6,
        "cross_station_bore_hits_mm3": cross_station_bore_hits,
        "all_bore_pairs_clear": all_bore_pairs_clear,
        "cross_station_block_hits_mm3": cross_station_block_hits,
        "cross_station_stack_block_hits_mm3": cross_station_stack_block_hits,
        "cross_station_stack_component_hits_mm3": (cross_station_stack_component_hits),
        "cross_station_tool_opposite_hits_mm3": cross_station_tool_opposite_hits,
        "all_stacks_mutually_clear": all_stacks_mutually_clear,
        "all_cross_station_access_paths_clear": (all_cross_station_access_paths_clear),
        "fixed_axes_unchanged": len(panel_connections) == 66,
        "all_fixed_axes_have_positive_receiver_support": all(support.values()),
        "all_geometry_gates_pass": all(gates),
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    if target_stations == TARGET_STATIONS:
        result["all_eight_stacks_mutually_clear"] = all_stacks_mutually_clear
    return result


def screen(pair=None):
    """Preserve the original lower-center screen and schema."""
    if pair is None:
        pair = build_pair()
    return _screen_targets(pair, TARGET_STATIONS, "simple_pb03_lower_center_pair/v1")


def screen_core_slice(core_slice=None):
    """Screen all four lower-service stations without pairwise shortcuts."""
    if core_slice is None:
        core_slice = build_core_slice()
    return _screen_targets(
        core_slice, ALL_TARGET_STATIONS, "simple_pb03_lower_service_core/v1"
    )
