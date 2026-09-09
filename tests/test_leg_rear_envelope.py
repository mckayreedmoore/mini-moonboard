"""Owner's preferred rear envelope; historical wider trials remain comparisons."""
import pytest

from mini_moonboard import lumber_leg_spread_frame as model
from mini_moonboard.box_exports import exact_bounds


@pytest.mark.parametrize("side", ["left", "right"])
def test_compact_leg_fits_top_frame_projection(side):
    parts = {p.name: p for p in model.parts("2x6", 0., False)}
    # Use the rear projection of the top frame, slightly tighter than the
    # climbing panel's upper edge. This is not a fall-zone clearance check.
    limit = exact_bounds(parts["base_rail_top"].shape).ymax
    rear = exact_bounds(parts[f"lumber_leg_{side}"].shape).ymax
    assert limit == pytest.approx(1535.584507483516)
    assert rear == pytest.approx(1476.3393621974553)
    assert limit-rear > 59.
    for extension in (150., 300.):
        assert exact_bounds(model.leg("2x6", extension, side).shape).ymax > limit
