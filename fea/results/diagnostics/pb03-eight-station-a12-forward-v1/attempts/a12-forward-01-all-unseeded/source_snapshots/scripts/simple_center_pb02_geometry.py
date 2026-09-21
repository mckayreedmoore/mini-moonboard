"""Single source for PB02 trial coordinates and active ten-bore geometry."""

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from types import MappingProxyType
from unittest.mock import patch

import cadquery as cq

from scripts import simple_center_current_stack_tip_screen as stack
from scripts import simple_center_post_header_two_bolt_probe as post
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_side_depth_y_probe as side


@dataclass(frozen=True)
class CenterTrialSpec:
    variant_id: str
    post_high_z: float
    vertical_x: tuple[float, float]
    vertical_y: tuple[float, float]
    link_z: float = 370


TRIAL_SPECS = MappingProxyType(
    {
        "working_reference": CenterTrialSpec(
            "working_reference", 190, (208.35, 235.85), (-130, -130)
        ),
        "rear_stagger": CenterTrialSpec(
            "rear_stagger", 189, (208.35, 235.85), (-130, -144)
        ),
        "front_stagger": CenterTrialSpec(
            "front_stagger", 189, (208.35, 236), (-130.5, -117.5)
        ),
        "ligament_priority": CenterTrialSpec(
            "ligament_priority",
            202.0,
            (208.35, 236),
            (-130.5, -117.5),
            link_z=328.5,
        ),
    }
)
ACTIVE_TRIAL = TRIAL_SPECS["ligament_priority"]

FRONT_Y = -114.1
UPRIGHT_Y = -144.5
UPRIGHT_Z = 356
HEADER_SIDE_TOP_Z = 344
POST_CLEAT_Z = (145, 176)
BLOCK_BOTTOM_Z = 95
POST_AXIS_Y = -145
REAR_CLEAT_FLOOR_CLEARANCE_MM = 5.0
RECEIVERS = MappingProxyType(
    {
        "header_cleat": ("base_header", "header_side_cleat"),
        "cleat_principal": ("header_side_cleat", "base_principal_center_right"),
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
        "post_cleat_1": ("shifted_right_post", "header_post_side_cleat"),
        "cleat_header_1": ("header_post_side_cleat", "base_header"),
        "post_cleat_2": ("shifted_right_post", "header_post_side_cleat"),
        "cleat_header_2": ("header_post_side_cleat", "base_header"),
    }
)


def trial_fingerprint(spec=ACTIVE_TRIAL):
    """Identify the active coordinates and receiver map consumed downstream."""
    payload = {
        "schema": 1,
        "spec": asdict(spec),
        "fixed": {
            "front_y": FRONT_Y,
            "upright_y": UPRIGHT_Y,
            "upright_z": UPRIGHT_Z,
            "header_side_top_z": HEADER_SIDE_TOP_Z,
            "post_cleat_z": POST_CLEAT_Z,
            "block_bottom_z": BLOCK_BOTTOM_Z,
            "post_axis_y": POST_AXIS_Y,
            "rear_cleat_floor_clearance_mm": REAR_CLEAT_FLOOR_CLEARANCE_MM,
        },
        "receivers": dict(RECEIVERS),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


ACTIVE_FINGERPRINT = trial_fingerprint()


def build_center_geometry(spec=ACTIVE_TRIAL):
    """Build all ten PB02 bores and end planes from one immutable trial spec."""
    source_geometry = prior._geometry
    config = (BLOCK_BOTTOM_Z, POST_AXIS_Y, POST_CLEAT_Z, spec.vertical_x)

    def integrated_geometry():
        return side._change(
            *source_geometry(), FRONT_Y, UPRIGHT_Y, UPRIGHT_Z, spec.link_z
        )

    with (
        patch.object(prior, "POSE", replace(prior.POSE, top_z=HEADER_SIDE_TOP_Z)),
        patch.dict(post.VARIANTS, {"shorter_8in_trial": config}),
        patch.object(prior, "_geometry", integrated_geometry),
    ):
        parts, bores, ends = stack._geometry()

    rear_bounds = parts["rear_cleat"].BoundingBox()
    parts["rear_cleat"] = parts["rear_cleat"].intersect(
        cq.Solid.makeBox(
            rear_bounds.xlen,
            rear_bounds.ylen,
            rear_bounds.zmax - REAR_CLEAT_FLOOR_CLEARANCE_MM,
            cq.Vector(
                rear_bounds.xmin,
                rear_bounds.ymin,
                REAR_CLEAT_FLOOR_CLEARANCE_MM,
            ),
        )
    )

    dz = spec.post_high_z - ends["post_rear_high"][0][2]
    bores["post_high"] = bores["post_high"].translate((0, 0, dz))
    for name in ("post_rear_high", "post_front_high"):
        point, outward, receiver = ends[name]
        ends[name] = ((point[0], point[1], spec.post_high_z), outward, receiver)

    for index, y in enumerate(spec.vertical_y, 1):
        name = f"cleat_header_{index}"
        current_y = ends[f"{name}_bottom"][0][1]
        bores[name] = bores[name].translate((0, y - current_y, 0))
        for suffix in ("bottom", "top"):
            end_name = f"{name}_{suffix}"
            point, outward, receiver = ends[end_name]
            ends[end_name] = ((point[0], y, point[2]), outward, receiver)

    expected_ends = {end for pair in stack.PAIRS.values() for end in pair}
    if set(bores) != set(stack.PAIRS) or set(ends) != expected_ends:
        raise ValueError("active PB02 ten-bore/end inventory changed")
    receivers = {
        bolt: tuple(ends[end][2] for end in pair) for bolt, pair in stack.PAIRS.items()
    }
    if receivers != RECEIVERS:
        raise ValueError("active PB02 receiver identities changed")
    return parts, bores, ends


def active_geometry():
    return build_center_geometry(ACTIVE_TRIAL)
