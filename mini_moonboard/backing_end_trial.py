"""Unselected ML23Z backing-end screw-axis trial; does not change current CAD."""
import json
from pathlib import Path

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from .timber_connections import SDS, ConnectorScrew

REFERENCE = json.loads((Path(__file__).resolve().parents[1]/"docs/ml23z-reference.json").read_text())


def screws():
    for side, sign in (("left", 1), ("right", -1)):
        origin = b.point(-sign*base.INNER_EDGE, 44.45, 38.1)
        u, v = cq.Vector(sign, 0, 0), b.normal()
        w = u.cross(v)
        for flange, along, inward, offsets, member in (
            ("backing", u, v, REFERENCE["front_flange_offsets_mm"], "timber_bottom_backing"),
            ("rim", v, u, REFERENCE["opposite_flange_offsets_mm"], f"base_side_{side}"),
        ):
            for i, (station, offset) in enumerate(zip(REFERENCE["width_stations_mm"], offsets, strict=True), 1):
                yield ConnectorScrew(f"trial_end_{side}_{flange}_{i}",
                    origin+w*station+along*offset+inward*REFERENCE["thickness_mm"],
                    -inward, SDS["underhead_length"], 6.35,
                    (f"trial_ml23_{side}", member))
