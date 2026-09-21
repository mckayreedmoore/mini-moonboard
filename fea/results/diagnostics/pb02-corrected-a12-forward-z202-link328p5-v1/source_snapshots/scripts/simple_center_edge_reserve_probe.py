"""PB-02 single 4x4/rear-cleat edge-reserve pose; nominal geometry only."""

import json
from unittest.mock import patch

import cadquery as cq

from scripts import simple_center_wide_post_probe as wide

POST_X = 88.75
BOLT_X = 140.0
LINK_X = 114.45
REAR_X = 89.05
REAR_WIDTH = 88.9  # One ordinary 2x4, wide face along X.


def probe():
    """Screen one outward right-support pose using the prior CAD checks."""
    rear = cq.Solid.makeBox(REAR_WIDTH, 38.1, 460, cq.Vector(REAR_X, -213.8, 0))
    # ponytail: reuse the predecessor's full CAD screen at two exact axes.
    # It ties the separate link bolt to the post-bolt X, so retain each
    # group's own fields and rebuild their mixed bore-pair check below.
    with patch.multiple(wide, POST_X=POST_X, BOLT_X=BOLT_X, REAR=rear):
        trial = wide._trial("nominal solid 4x4 plus one 2x4 rear cleat", 88.9)
    with patch.multiple(wide, POST_X=POST_X, BOLT_X=LINK_X, REAR=rear):
        link_trial = wide._trial("link-bolt check at retained X", 88.9)

    for field, prefix in (
        ("bore_received_fraction", "cleat_link"),
        ("bore_unintended_wood_hits_mm3", "cleat_link/"),
        ("fixed_screw_hits_mm3", "bore/cleat_link/"),
        ("washer_bearing_fraction", "link_"),
        ("trial_20mm_radius_tool_wood_hits_mm3", "link_"),
    ):
        trial[field] = {
            **{k: v for k, v in trial[field].items() if not k.startswith(prefix)},
            **{k: v for k, v in link_trial[field].items() if k.startswith(prefix)},
        }
    trial["actual_edge_end_mm"]["cleat_link_x_edges"] = link_trial[
        "actual_edge_end_mm"
    ]["cleat_link_x_edges"]
    post_front = wide.POST_REAR_Y + 88.9
    bores = {
        **{
            f"post_{name}": cq.Solid.makeCylinder(
                wide.BORE_RADIUS,
                post_front + 213.8,
                cq.Vector(BOLT_X, -213.8, z),
                cq.Vector(0, 1, 0),
            )
            for name, z in zip(("low", "high"), wide.BOLT_Z)
        },
        "upright": cq.Solid.makeCylinder(
            wide.BORE_RADIUS,
            88.9,
            cq.Vector(50.95, -147.3, 350),
            cq.Vector(1, 0, 0),
        ),
        "cleat_link": cq.Solid.makeCylinder(
            wide.BORE_RADIUS,
            94.9,
            cq.Vector(LINK_X, -213.8, 370),
            cq.Vector(0, 1, 0),
        ),
    }
    trial["bore_pair_hits_mm3"] = {
        f"{name}/{other}": round(volume, 5)
        for i, (name, bore) in enumerate(bores.items())
        for other, second in list(bores.items())[i + 1 :]
        if (volume := wide.hit_volume(bore, second)) > wide.TOL
    }
    trial["post_bolt_x_mm"] = BOLT_X
    trial["cleat_link_x_mm"] = LINK_X

    post_min, post_max, *_ = trial["post_bounds_mm"]
    rear_min, rear_max, *_ = trial["cleat_bounds_mm"]["rear"]
    backer = trial["backer_bounds_mm"]
    post = trial["post_bounds_mm"]
    trial["post_to_backer_x_gap_mm"] = round(post[0] - backer[1], 5)
    trial["post_to_backer_x_face_contact_mm2"] = round(
        max(0, min(post[3], backer[3]) - max(post[2], backer[2]))
        * max(0, min(post[5], backer[5]) - max(post[4], backer[4]))
        if abs(post[0] - backer[1]) <= wide.TOL
        else 0,
        5,
    )
    trial["post_to_rear_cleat_contact_mm2"] = round(
        (min(post_max, rear_max) - max(post_min, rear_min)) * wide.POST_TOP, 5
    )
    trial["minimum_post_bolt_x_reserve_mm"] = round(
        min(
            *trial["actual_edge_end_mm"]["post_bolts_x_edges"],
            *trial["actual_edge_end_mm"]["rear_cleat_post_bolts_x_edges"],
        )
        - trial["conditional_4d_mm"],
        5,
    )
    return trial


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
