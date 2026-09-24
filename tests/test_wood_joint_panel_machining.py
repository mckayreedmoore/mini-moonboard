"""Candidate-only kerf-right panel remachining regression."""

from dataclasses import replace
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard import base_frame, box_frame, insert_frame, panel_grid_v2
from mini_moonboard import wood_joint_panel_machining as panel_machining


class _Frame:
    HALF = 10.0
    V1_KICKER_HEIGHT_MM = 10.0

    @staticmethod
    def point(x, s, n):
        return cq.Vector(x, s, n)


class _CandidateFrame:
    HALF = 10.0
    V1_KICKER_HEIGHT_MM = 62.0

    @staticmethod
    def point(x, s, n):
        return cq.Vector(x, s, n + 48.0)


class _PanelConnection:
    def __init__(self, name, panel, start, direction):
        self.name = name
        self.members = (panel, "synthetic_receiver")
        self.start = start
        self.direction = direction
        self.length = 2.0
        self.diameter = 0.5

    def components(self):
        shaft = cq.Solid.makeCylinder(0.25, self.length, self.start, self.direction)
        head = cq.Solid.makeCone(0.5, 0.25, 0.25, self.start, self.direction)
        return shaft, head


class _Candidate:
    option = "kerf-right"
    KEY = "synthetic-kerf-right"
    b = _CandidateFrame()
    base = SimpleNamespace(HEADER_FRONT_Y=base_frame.HEADER_FRONT_Y + 2.0)

    def __init__(self, connections):
        self._connections = tuple(connections)

    def panel_connections(self):
        return self._connections


def _part(name, shape, description="source description"):
    return box_frame.Part(name, shape, (8.4125, 10.0, 1.0), description, 1)


def _source_parts(drilled):
    """Tiny synthetic producer geometry with one grid feature per right panel."""
    result = {
        "main_lower_right": _part(
            "main_lower_right",
            cq.Solid.makeBox(10.0, 10.0, 1.0, cq.Vector(0.0, 0.0, -1.0)),
        ),
        "main_upper_right": _part(
            "main_upper_right",
            cq.Solid.makeBox(10.0, 10.0, 1.0, cq.Vector(0.0, 10.0, -1.0)),
        ),
        "kicker_right": _part(
            "kicker_right",
            cq.Solid.makeBox(
                10.0, 1.0, 10.0, cq.Vector(0.0, base_frame.HEADER_FRONT_Y, 0.0)
            ),
        ),
    }
    if not drilled:
        return tuple(result.values())

    main_half = base_frame.b.HALF
    for datums, diameter in (
        (panel_grid_v2.main_tnut_datums(), 4.0),
        (panel_grid_v2.main_led_datums(), 5.0),
    ):
        for x, s in datums.values():
            panel = (
                f"main_{'lower' if s < main_half else 'upper'}_"
                f"{'left' if x < main_half else 'right'}"
            )
            if panel not in result:
                continue
            start = base_frame.b.point(x - main_half, s, -1.0)
            tool = cq.Solid.makeCylinder(
                diameter / 2.0, 3.0, start, cq.Vector(0.0, 0.0, 1.0)
            )
            part = result[panel]
            result[panel] = replace(part, shape=part.shape.cut(tool))

    for x, z in panel_grid_v2.kicker_foothold_datums().values():
        if x < main_half:
            continue
        start = cq.Vector(
            x - main_half,
            base_frame.HEADER_FRONT_Y - 1.0,
            base_frame.b.V1_KICKER_HEIGHT_MM + z,
        )
        tool = cq.Solid.makeCylinder(3.5 / 2.0, 3.0, start, cq.Vector(0.0, 1.0, 0.0))
        part = result["kicker_right"]
        result["kicker_right"] = replace(part, shape=part.shape.cut(tool))
    return tuple(result.values())


@pytest.fixture
def synthetic_source(monkeypatch):
    monkeypatch.setattr(base_frame, "b", _Frame())
    monkeypatch.setattr(
        panel_grid_v2,
        "main_tnut_datums",
        lambda: {"G1": (15.0, 5.0), "G7": (15.0, 15.0)},
    )
    monkeypatch.setattr(
        panel_grid_v2,
        "main_led_datums",
        lambda: {"G1": (15.0, 4.0), "G7": (15.0, 14.0)},
    )
    monkeypatch.setattr(
        panel_grid_v2,
        "kicker_foothold_datums",
        lambda: {"1": (15.0, -1.0)},
    )
    monkeypatch.setattr(base_frame, "parts", _source_parts)
    monkeypatch.setattr(
        insert_frame,
        "ASSUMPTIONS",
        {**insert_frame.ASSUMPTIONS, "panel_clearance_bore_diameter": 0.5},
    )
    monkeypatch.setattr(insert_frame, "PANEL", 0.1)
    panel_machining._base_grid_cut_volumes.cache_clear()
    yield
    panel_machining._base_grid_cut_volumes.cache_clear()


def _candidate_connections():
    result = [
        _PanelConnection(
            "right-main-lower-current-axis",
            "main_lower_right",
            cq.Vector(1.0, 8.0, 48.0),
            cq.Vector(0.0, 0.0, -1.0),
        ),
        _PanelConnection(
            "right-main-upper-current-axis",
            "main_upper_right",
            cq.Vector(1.0, 18.0, 48.0),
            cq.Vector(0.0, 0.0, -1.0),
        ),
        _PanelConnection(
            "right-kicker-current-axis",
            "kicker_right",
            cq.Vector(1.0, _Candidate.base.HEADER_FRONT_Y + 1.0, 61.0),
            cq.Vector(0.0, -1.0, 0.0),
        ),
    ]
    left_panels = ("main_lower_left", "main_upper_left", "kicker_left")
    result.extend(
        _PanelConnection(
            f"left-axis-{index}",
            left_panels[index % len(left_panels)],
            cq.Vector(-5.0, float(index), 0.0),
            cq.Vector(0.0, 0.0, -1.0),
        )
        for index in range(63)
    )
    return tuple(result)


def _candidate_parts(model):
    lower = cq.Solid.makeBox(8.4125, 10.0, 1.0, cq.Vector(-1.5875, 0.0, 47.0))
    upper = cq.Solid.makeBox(8.4125, 10.0, 1.0, cq.Vector(-1.5875, 10.0, 47.0))
    kicker = cq.Solid.makeBox(
        8.4125, 1.0, 62.0, cq.Vector(-1.5875, model.base.HEADER_FRONT_Y, 0.0)
    )
    raw = {
        "main_lower_right": _part("main_lower_right", lower),
        "main_upper_right": _part("main_upper_right", upper),
        "kicker_right": _part("kicker_right", kicker),
    }
    # The real candidate's uncut parts still contain inherited grid openings,
    # shifted with the right panel. Recreate them from the shared producer's
    # exact raw-to-drilled volume difference.
    _, inherited_grid_holes, _, _ = panel_machining._base_grid_cut_volumes()
    for name in panel_machining.RIGHT_PANEL_NAMES:
        translation = (
            panel_machining._main_panel_translation(model, name)
            if name.startswith("main_")
            else panel_machining._kicker_panel_translation(model, name)
        )
        raw[name] = replace(
            raw[name],
            shape=raw[name]
            .shape.cut(inherited_grid_holes[name].translate(translation))
            .clean(),
        )
    current = dict(raw)
    # Simulate inherited, translated official-axis bores. The adapter must
    # replace these solids from uncut stock, not retain these wrong openings.
    stale = cq.Solid.makeCylinder(
        0.25, 2.0, cq.Vector(4.0, 8.0, 49.0), cq.Vector(0.0, 0.0, -1.0)
    )
    current["main_lower_right"] = replace(
        current["main_lower_right"],
        shape=current["main_lower_right"].shape.cut(stale),
        description="preserved current metadata",
    )
    current["base_header"] = _part(
        "base_header", cq.Solid.makeBox(1.0, 1.0, 1.0, cq.Vector(0, 0, 0))
    )
    return tuple(current.values()), tuple(raw.values())


def _probe(point):
    return cq.Solid.makeBox(
        0.05,
        0.05,
        0.05,
        cq.Vector(point.x - 0.025, point.y - 0.025, point.z - 0.025),
    )


def _material_volume(part, point):
    return part.shape.intersect(_probe(point)).Volume()


def _bounds(part):
    box = part.shape.BoundingBox()
    return (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)


def test_replacement_rebores_fixed_grid_and_exact_candidate_axes(synthetic_source):
    model = _Candidate(_candidate_connections())
    current_parts, raw_parts = _candidate_parts(model)
    raw_by_name = {part.name: part for part in raw_parts}
    originals = {part.name: part for part in current_parts}
    original_volume = originals["main_lower_right"].shape.Volume()
    original_axis = tuple(model.panel_connections()[0].start.toTuple())

    replacements = panel_machining.candidate_panel_replacements(
        model, current_parts=current_parts, uncut_parts=raw_parts
    )

    assert set(replacements) == {"main_lower_right", "main_upper_right", "kicker_right"}
    assert replacements["main_lower_right"].description == "preserved current metadata"
    assert replacements["main_lower_right"].blank == originals["main_lower_right"].blank
    assert originals["main_lower_right"].shape.Volume() == pytest.approx(
        original_volume
    )
    assert tuple(model.panel_connections()[0].start.toTuple()) == original_axis
    for name in panel_machining.RIGHT_PANEL_NAMES:
        assert _bounds(replacements[name]) == pytest.approx(_bounds(raw_by_name[name]))

    main_translation = panel_machining._main_panel_translation(
        model, "main_lower_right"
    )
    kicker_translation = panel_machining._kicker_panel_translation(
        model, "kicker_right"
    )
    assert main_translation.z == pytest.approx(48.0)
    assert kicker_translation.z == pytest.approx(52.0)
    assert kicker_translation.y == pytest.approx(2.0)

    # Main-panel grid bores stay on world-X datums despite the right-panel
    # outline shift. Inherited shifted bores are present in the input, then
    # filled; lower and upper panels get their own matching frame datum.
    for y, radius in ((5.0, 2.0), (15.0, 2.0), (4.0, 2.5), (14.0, 2.5)):
        right_name = "main_lower_right" if y < 10 else "main_upper_right"
        assert _material_volume(
            raw_by_name[right_name],
            cq.Vector(3.4125 - radius + 0.1, y, 47.5),
        ) == pytest.approx(0.0, abs=1e-8)
        assert (
            _material_volume(
                replacements[right_name],
                cq.Vector(3.4125 - radius + 0.1, y, 47.5),
            )
            > 0.0
        )
        assert _material_volume(
            replacements[right_name], cq.Vector(5.0, y, 47.5)
        ) == pytest.approx(0.0, abs=1e-8)

    # The selected kicker has a 52 mm lower extension below the shared grid
    # stock, plus its own front-face offset. Its fixed hold stays at the top.
    kicker_y = _Candidate.base.HEADER_FRONT_Y + 0.5
    kicker_crescent = 3.4125 - 1.75 + 0.1
    assert _material_volume(
        raw_by_name["kicker_right"],
        cq.Vector(kicker_crescent, kicker_y, 61.0),
    ) == pytest.approx(0.0, abs=1e-8)
    assert (
        _material_volume(
            replacements["kicker_right"],
            cq.Vector(kicker_crescent, kicker_y, 61.0),
        )
        > 0.0
    )
    assert _material_volume(
        replacements["kicker_right"],
        cq.Vector(5.0, kicker_y, 61.0),
    ) == pytest.approx(0.0, abs=1e-8)

    lower_extension = cq.Solid.makeBox(
        20.0, 10.0, 52.0, cq.Vector(-5.0, kicker_y - 5.0, 0.0)
    )
    raw_lower = raw_by_name["kicker_right"].shape.intersect(lower_extension)
    replacement_lower = replacements["kicker_right"].shape.intersect(lower_extension)
    assert raw_lower.cut(replacement_lower).Volume() == pytest.approx(0.0, abs=1e-8)
    assert replacement_lower.cut(raw_lower).Volume() == pytest.approx(0.0, abs=1e-8)

    # The true kerf-right main-panel axis is machined; the stale inherited
    # official-axis opening is filled by rebuilding from the uncut panel.
    assert _material_volume(
        replacements["main_lower_right"], cq.Vector(1.0, 8.0, 47.5)
    ) == pytest.approx(0.0, abs=1e-8)
    assert (
        _material_volume(replacements["main_lower_right"], cq.Vector(4.0, 8.0, 47.5))
        > 0.0
    )

    # Other candidate parts are deliberately absent from the replacement map.
    assert "base_header" not in replacements


def test_only_kerf_right_model_and_exact_66_panel_axes_are_accepted(synthetic_source):
    model = _Candidate(_candidate_connections())
    current_parts, raw_parts = _candidate_parts(model)
    assert len(model.panel_connections()) == 66

    model.option = "official"
    with pytest.raises(ValueError, match="kerf-right"):
        panel_machining.candidate_panel_replacements(
            model, current_parts=current_parts, uncut_parts=raw_parts
        )

    model.option = "kerf-right"
    model._connections = model._connections[:-1]
    with pytest.raises(ValueError, match="66"):
        panel_machining.candidate_panel_replacements(
            model, current_parts=current_parts, uncut_parts=raw_parts
        )
