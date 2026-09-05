"""Keep hypothetical 2x8 timber stiffness distinct from buildable geometry."""
from itertools import combinations

import cadquery as cq
import pytest

from mini_moonboard import hybrid_frame as h
from mini_moonboard.box_exports import overlap
from mini_moonboard.hybrid_exports import viewer_mesh


def test_2x8_undrilled_timber_is_valid_and_nonoverlapping():
    timber = [p for p in h.parts("2x8", False)
              if not p.name.startswith("angle_")]
    assert len(timber) == 45
    assert all(p.shape.isValid() and len(p.shape.Solids()) == 1 for p in timber)
    assert not [(a.name, b.name) for a, b in combinations(timber, 2)
                if overlap(a.shape, b.shape) > .01]


def test_2x8_existing_connections_are_explicitly_not_feasible():
    parts = {p.name: p.shape for p in h.parts("2x8")}
    # A valid individual solid does not mean a valid assembly: the existing
    # 80 mm angle reaches into both the panel and its backing at this depth.
    angle = parts["angle_rib_1_mid_left"]
    assert overlap(angle, parts["main_lower_left"]) > 1000
    assert overlap(angle, parts["mid_lower_left"]) > 19000
    bolt = next(c for c in h.connections("2x8")
                if c.name == "angle_rib_1_mid_left_rib_2")
    receiver_probe = cq.Solid.makeCylinder(5.5, bolt.length, bolt.start, bolt.direction)
    assert overlap(receiver_probe, parts["rib_1_mid_left"]) < .01


def test_2x8_has_no_clearance_screened_complete_viewer(tmp_path):
    with pytest.raises(ValueError, match="clearance-screened"):
        viewer_mesh("2x8", tmp_path)
    assert not list(tmp_path.iterdir())
