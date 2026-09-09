"""Dimensional and actual nominal CAD checks, not joint qualification."""
from itertools import product

import pytest
from test_lumber_leg_spread_frame import overlap

from mini_moonboard import leg_hardware_trial as model
from mini_moonboard.connection_geometry import material_intervals


@pytest.mark.parametrize("rim,leg", list(product((37.5, 38.5), repeat=2)))
def test_worst_dimensional_window(rim, leg):
    value = model.dimensional_window(rim, leg)
    assert value["body_margin_mm"] >= .8367-1e-8
    assert value["seating_margin_mm"] >= 3.626-1e-8
    assert value["tip_projection_min_mm"] > 3*model.THREAD_PITCH
    assert not value["qualified_for_design"]
    assert not value["complete_thread_projection_verified"]


def test_out_of_window_rejected():
    for rim, leg in ((37.49, 38.1), (38.1, 38.51), (float("nan"), 38.1)):
        with pytest.raises(ValueError):
            model.dimensional_window(rim, leg)


@pytest.mark.parametrize("thickness", [model.WASHER_MIN, model.WASHER_NOMINAL, model.WASHER_MAX])
@pytest.mark.parametrize("extension", [0., 300.])
def test_new_hardware_preserves_bearing_planes_and_clears_assembly(thickness, extension):
    parts = model.parts(extension)
    assert parts is model.base.parts("2x6", extension)
    raw = {p.name: p for p in model.base.parts("2x6", extension, False)}
    connections = model.connections(thickness, extension=extension)
    changed = [c for c in connections if isinstance(c, model.TrialBolt)]
    assert len(changed) == 8 and len(connections) == 182
    retained = {c.name: c for c in model.base.connections("2x6", extension)}
    hardware = {c.name: c.components() for c in connections}
    for c in connections:
        if not isinstance(c, model.TrialBolt):
            assert c is retained[c.name]
    for bolt in changed:
        assert len(hardware[bolt.name]) == 7  # shaft, four washers, head, nut
        for index, member in enumerate(bolt.members):
            intervals = material_intervals(raw[member].shape, bolt.start, bolt.direction, 0., bolt.length)
            start = 2*thickness+index*38.1
            assert len(intervals) == 1 and intervals[0] == pytest.approx([start, start+38.1])
        for component in hardware[bolt.name]:
            assert component.isValid() and component.Volume() > 0
            for part in parts:
                assert overlap(component, part.shape) < .01, (bolt.name, part.name)
            for name, others in hardware.items():
                if name != bolt.name:
                    for other in others:
                        assert overlap(component, other) < .01, (bolt.name, name)


def test_default_remains_extended_and_invalid_extensions_rejected():
    assert model.parts() is model.parts(300.)
    def identity(bolt):
        return (bolt.name, bolt.start.toTuple(), bolt.direction.toTuple(), bolt.length,
                bolt.diameter, bolt.grip, bolt.members, getattr(bolt, "product_status", None))
    assert list(map(identity, model.connections())) == list(map(identity, model.connections(extension=300.)))
    for extension in (-1., 150., float("nan")):
        with pytest.raises(ValueError, match="foot extension"):
            model.parts(extension)
        with pytest.raises(ValueError, match="foot extension"):
            model.connections(extension=extension)
