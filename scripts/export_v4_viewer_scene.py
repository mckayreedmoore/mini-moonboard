"""Export source-bound V4 diagnostic primitives for the existing 3D viewer.

This is a partial visual overlay, not a combined V4 assembly or shop output.
"""

import json
from functools import lru_cache
from pathlib import Path

from mini_moonboard.floor_flush_width import (
    KERF_EACH_MM,
    KERF_RIGHT,
    KERF_RIGHT_MM,
    OFFICIAL,
    variant,
)
from scripts import simple_center_current_stack_tip_screen as pb02
from scripts import simple_center_wide_post_probe as wide
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts.simple_center_pb02_geometry import (
    ACTIVE_FINGERPRINT,
    ACTIVE_TRIAL,
    active_geometry,
)
from scripts.simple_pb03_lower_center_pair import (
    BORE_DIAMETER_MM,
    END_ALLOWANCE_MM,
    HEAD_NUT_DIAMETER_MM,
    WASHER_DIAMETER_MM,
)
from scripts.simple_pb04_native import SOURCE_ID, PB04Native
from scripts.simple_pb04_native import screen as screen_pb04_native

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/v4-diagnostic-scene.json"
BASELINE = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"

TRIAL_SHANK_DIAMETER_MM = 6.35
TRIAL_HEAD_LENGTH_MM = 5.0
TRIAL_ENVELOPE_DIAMETER_MM = 20.0


def _axial_component(role, origin, direction, offset, length, diameter):
    return {
        "role": role,
        "start_mm": [
            value + offset * axis for value, axis in zip(origin, direction, strict=True)
        ],
        "axis": direction,
        "length_mm": length,
        "diameter_mm": diameter,
    }


def _trial_stack(name, start, direction, grip_mm):
    """Build a display-only five-role envelope from maintained PB02 bounds."""
    washer_mm = pb02.WASHER_RANGE_IN[1] * pb02.MM_PER_IN
    nut_mm = pb02.NUT_RANGE_IN[1] * pb02.MM_PER_IN
    bolt_mm = pb02.TRIAL_LENGTH_IN[name] * pb02.MM_PER_IN
    return {
        "name": name,
        "station": "PB02",
        "trial_length_in": pb02.TRIAL_LENGTH_IN[name],
        "orientation_selected": False,
        "hardware_selected": False,
        "components": [
            _axial_component(
                "shaft",
                start,
                direction,
                -washer_mm,
                bolt_mm,
                TRIAL_SHANK_DIAMETER_MM,
            ),
            _axial_component(
                "head",
                start,
                direction,
                -(washer_mm + TRIAL_HEAD_LENGTH_MM),
                TRIAL_HEAD_LENGTH_MM,
                TRIAL_ENVELOPE_DIAMETER_MM,
            ),
            _axial_component(
                "near_washer",
                start,
                direction,
                -washer_mm,
                washer_mm,
                TRIAL_ENVELOPE_DIAMETER_MM,
            ),
            _axial_component(
                "far_washer",
                start,
                direction,
                grip_mm,
                washer_mm,
                TRIAL_ENVELOPE_DIAMETER_MM,
            ),
            _axial_component(
                "nut",
                start,
                direction,
                grip_mm + washer_mm,
                nut_mm,
                TRIAL_ENVELOPE_DIAMETER_MM,
            ),
        ],
    }


def _pb04_stack(station, bolt, *, recessed_upright=False):
    """Show the recessed trial seat separately from PB04's gross through-bore."""
    start = list(bolt.start.toTuple())
    direction = list(bolt.direction.normalized().toTuple())
    if recessed_upright:
        near = END_ALLOWANCE_MM
        under_head = near - pocket.WASHER_EACH_SIDE_MM
        far_seat = near + bolt.grip - pocket._required_depth_mm()
        washer = pocket.WASHER_EACH_SIDE_MM
        return {
            "name": bolt.name,
            "station": "PB04",
            "source_station": station,
            "recessed_upright_trial": True,
            "orientation_selected": False,
            "hardware_selected": False,
            "components": [
                _axial_component(
                    "shaft",
                    start,
                    direction,
                    under_head,
                    pocket.BOLT_LENGTH_MM,
                    bolt.diameter,
                ),
                _axial_component(
                    "head", start, direction, under_head - 6, 6, HEAD_NUT_DIAMETER_MM
                ),
                _axial_component(
                    "near_washer",
                    start,
                    direction,
                    under_head,
                    washer,
                    pocket.WASHER_OUTSIDE_DIAMETER_MM,
                ),
                _axial_component(
                    "far_washer",
                    start,
                    direction,
                    far_seat,
                    washer,
                    pocket.WASHER_OUTSIDE_DIAMETER_MM,
                ),
                _axial_component(
                    "nut",
                    start,
                    direction,
                    far_seat + washer,
                    pocket.NUT_HEIGHT_MM,
                    pocket.NUT_MAX_ACROSS_CORNERS_MM,
                ),
            ],
        }
    return {
        "name": bolt.name,
        "station": "PB04",
        "source_station": station,
        "orientation_selected": False,
        "hardware_selected": False,
        "components": [
            _axial_component("shaft", start, direction, 0, bolt.length, bolt.diameter),
            _axial_component(
                "head",
                start,
                direction,
                -5.5,
                6.0,
                HEAD_NUT_DIAMETER_MM,
            ),
            _axial_component(
                "near_washer",
                start,
                direction,
                0.5,
                2.0,
                WASHER_DIAMETER_MM,
            ),
            _axial_component(
                "far_washer",
                start,
                direction,
                bolt.length - 2.5,
                2.0,
                WASHER_DIAMETER_MM,
            ),
            _axial_component(
                "nut",
                start,
                direction,
                bolt.length - 0.5,
                9.0,
                HEAD_NUT_DIAMETER_MM,
            ),
        ],
    }


def _shape_mesh(shape):
    """Serialize the actual CAD solid so counterbores remain visible."""
    vertices, triangles = shape.tessellate(0.5)
    return {
        "vertices_mm": [list(vertex.toTuple()) for vertex in vertices],
        "triangles": [list(triangle) for triangle in triangles],
    }


@lru_cache(maxsize=1)
def build_scene():
    baseline = json.loads(BASELINE.read_text())
    names = {part["name"] for part in baseline["parts"]}
    pb04_module = PB04Native()
    pb04_status = screen_pb04_native(pb04_module)
    pb04_core = pb04_module.pb03_geometries()
    replaced_pb04_stations = tuple(pb04_core)
    fixed = [
        name
        for name in names
        if name.startswith(
            (
                "fastener_round_panel_",
                "fastener_round_kicker_",
                "fastener_kicker_header_",
            )
        )
    ]
    if len(fixed) != 66 or baseline["design"]["panel_kicker_screw_count"] != 66:
        raise ValueError("selected baseline no longer contains 66 fixed screw visuals")
    hidden_legacy_visuals = sorted(
        name
        for name in names
        if any(
            name == station or name.startswith(f"fastener_{station}_")
            for station in replaced_pb04_stations
        )
    )
    if len(hidden_legacy_visuals) != 56:
        raise ValueError(
            "PB04 must hide exactly eight angles and forty-eight SDS visuals"
        )

    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    official_wood = {
        part.name: part.shape for part in variant(OFFICIAL).uncut_wood_parts()
    }
    boxes = []
    axes = []
    hardware_stacks = []

    parts, bores, ends = active_geometry()
    block = parts["header_post_side_cleat"].BoundingBox()
    boxes.append(
        {
            "name": "PB02 post/header block",
            "station": "PB02",
            "origin_mm": [block.xmin, block.ymin, block.zmin],
            "size_mm": [block.xlen, block.ylen, block.zlen],
            "rotation_x_deg": 0,
        }
    )
    for part_name, label in (
        ("upright_side_cleat", "PB02 revised upright-side cleat"),
        ("header_side_cleat", "PB02 revised header-side cleat"),
        ("shifted_right_post", "PB02 shifted right center post"),
        ("rear_cleat", "PB02 rear return block"),
        ("backer", "PB02 kicker backer"),
    ):
        bounds = parts[part_name].BoundingBox()
        boxes.append(
            {
                "name": label,
                "station": "PB02",
                "origin_mm": [bounds.xmin, bounds.ymin, bounds.zmin],
                "size_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
                "rotation_x_deg": 0,
            }
        )
    if set(bores) != set(pb02.PAIRS):
        raise ValueError("PB02 ten-bore source inventory changed")
    for name, (start_name, end_name) in pb02.PAIRS.items():
        start = ends[start_name][0]
        finish = ends[end_name][0]
        delta = [b - a for a, b in zip(start, finish)]
        length = sum(value * value for value in delta) ** 0.5
        axes.append(
            {
                "name": name,
                "station": "PB02",
                "start_mm": list(start),
                "axis": [value / length for value in delta],
                "length_mm": length,
                "diameter_mm": 2 * wide.BORE_RADIUS,
            }
        )
        hardware_stacks.append(_trial_stack(name, start, axes[-1]["axis"], length))
    pb02_stack_count = len(hardware_stacks)

    pb04_parts = {part.name: part.shape for part in pb04_module.wood_parts()}
    if not pb04_status["combined_geometry_gates_pass"]:
        raise ValueError("PB04 geometry no longer passes its committed visual source")
    for station, geometry in pb04_core.items():
        block = pb04_parts[geometry.block_name]
        boxes.append(
            {
                "name": geometry.block_name,
                "station": "PB04",
                "source_station": station,
                "center_mm": list(block.Center().toTuple()),
                "size_mm": geometry.report["block_dimensions_mm"],
                "rotation_x_deg": 50,
                "mesh": _shape_mesh(block),
            }
        )
        for bolt in geometry.bolts:
            direction = list(bolt.direction.normalized().toTuple())
            axes.append(
                {
                    "name": bolt.name,
                    "station": "PB04",
                    "source_station": station,
                    "start_mm": list(bolt.start.toTuple()),
                    "axis": direction,
                    "length_mm": bolt.length,
                    "diameter_mm": BORE_DIAMETER_MM,
                }
            )
            hardware_stacks.append(
                _pb04_stack(
                    station,
                    bolt,
                    recessed_upright=(
                        station in pocket.TARGET_STATIONS
                        and bolt.members[0] == geometry.upright_name
                    ),
                )
            )

    kicker_left = wood["kicker_left"].BoundingBox()
    kicker_right = wood["kicker_right"].BoundingBox()
    official_kicker = official_wood["kicker_left"].BoundingBox()
    backer = parts["backer"].BoundingBox()
    shifted = parts["shifted_right_post"].BoundingBox()
    original_right = wood["base_post_center_right"].BoundingBox()

    def edge_supported(edge_x):
        return (
            backer.xmin <= edge_x <= backer.xmax
            and abs(backer.ymax - kicker_left.ymin) < 1e-6
            and backer.zmin <= kicker_left.zmin
            and backer.zmax > kicker_left.zmin
        )

    support = {
        "left": edge_supported(kicker_left.xmax),
        "right": edge_supported(kicker_right.xmin),
    }
    shifted_outward = (shifted.xmin + shifted.xmax) / 2 > (
        original_right.xmin + original_right.xmax
    ) / 2
    if not shifted_outward or not all(support.values()):
        raise ValueError("PB02 center-support or kicker-edge visual contract changed")

    assembly_contract = {
        "width_option": KERF_RIGHT,
        "kerf_total_mm": KERF_RIGHT_MM,
        "kicker_panel_width_mm": kicker_left.xlen,
        "official_kicker_panel_width_mm": official_kicker.xlen,
        "outward_shifted_center_supports": 1,
        "inner_kicker_edges_supported": support,
        "pb02_bore_count": len(bores),
        "pb02_trial_stack_count": pb02_stack_count,
        "pb04_bore_count": sum(len(item.bores) for item in pb04_core.values()),
        "pb04_trial_stack_count": sum(len(item.stacks) for item in pb04_core.values()),
        "pb04_block_count": len(pb04_core),
        "pb04_upper_outer_rail_offset_mm": pb04_status["upper_outer_rail_offset_mm"],
        "pb04_counterbore_count": pb04_status["inventory"]["counterbores"],
        "pb04_counterbore_depth_mm": round(pb04_status["counterbore_depth_mm"], 4),
        "pb04_recessed_trial_stack_count": sum(
            bool(stack.get("recessed_upright_trial")) for stack in hardware_stacks
        ),
        "pb04_recessed_stack_tolerance_pass": (
            pocket.BOLT_LENGTH_MM
            - (pocket.ORIGINAL_GRIP_MM - pocket._required_depth_mm())
            - 2 * pocket.WASHER_EACH_SIDE_MM
            - pocket.NUT_HEIGHT_MM
            - pocket.TWO_THREAD_PROJECTION_MM
            >= 1.0  # Development sensitivity, not an actual product tolerance.
        ),
        "pb04_upright_bolt_product_lead": {
            "retailer": "Home Depot",
            "product": "Everbilt 800696",
            "nominal_size": "1/4-20 x 8 in",
            "url": pocket.HARDWARE_SOURCES["bolt"],
            "selected": False,
        },
        "legacy_station_count": pb04_status["inventory"]["legacy_proxy_stations"],
        "legacy_sds_axis_count": pb04_status["inventory"]["legacy_sds_axes"],
        "replaced_pb04_legacy_stations": list(replaced_pb04_stations),
        "fixed_panel_kicker_screw_axes": len(fixed),
        "total_connection_count": pb04_status["inventory"]["total_connections"],
        "bolt_kind_connection_count": sum(
            row.kind == "bolt" for row in pb04_module.connections()
        ),
        "development_only": not pb04_status["qualified_for_design"],
        "drilling_released": pb04_status["drilling_released"],
        "fabrication_released": pb04_status["fabrication_released"],
        "structural_released": pb04_status["structural_released"],
    }
    if abs(kicker_left.xlen - (official_kicker.xlen - KERF_EACH_MM)) > 1e-6:
        raise ValueError("kerf-right kicker width visual contract changed")
    return {
        "status": "partial_development_visualization",
        "baseline": "compact-floor-flush-kerf-right",
        "fixed_panel_kicker_screw_axes": len(fixed),
        "pb02_variant_id": ACTIVE_TRIAL.variant_id,
        "pb02_source_fingerprint": ACTIVE_FINGERPRINT,
        "pb04_source_id": SOURCE_ID,
        "pb04_source_fingerprint": pb04_status["source_fingerprint_sha256"],
        "hidden_legacy_visual_names": hidden_legacy_visuals,
        "assembly_contract": assembly_contract,
        "hardware_stack_scope": (
            "PB02 trial envelopes, PB04 generic rail/center stacks, and twelve "
            "recessed outer-upright 8-inch nominal stack trials; zero tolerance reserve, "
            "no delivered hardware or construction approval"
        ),
        "fabrication_released": False,
        "boxes": boxes,
        "axes": axes,
        "hardware_stacks": hardware_stacks,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_scene(), indent=2) + "\n")
