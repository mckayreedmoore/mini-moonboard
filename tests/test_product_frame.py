"""Selected-product integration geometry only; no capacity or real-product fit approval."""
from itertools import product

import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard import model
from mini_moonboard import product_frame as frame
from mini_moonboard import transition_frame as baseline
from mini_moonboard.box_exports import exact_bounds, overlap
from mini_moonboard.panel_grid import (
    kicker_foothold_datums,
    main_led_datums,
    main_tnut_datums,
)
from mini_moonboard.product_connections import ProductConnection, selected_connection
from mini_moonboard.selected_hardware import (
    SD9112,
    SDS25112,
    SPECS_BY_NAME,
    BoltSpec,
    spec_for,
)

FACES = {f"main_{band}_{side}" for band, side in product(("lower", "upper"), ("left", "right"))} | {
    "kicker_left", "kicker_right"}


@pytest.fixture(scope="module")
def parts():
    return {p.name: p for p in frame.parts()}


def test_raw_faces_preserve_backing_and_floor_datums():
    old = {p.name: p for p in baseline.parts(False)}
    raw = {p.name: p for p in frame.parts(False)}
    assert raw.keys() == old.keys() and len(raw) == 87
    assert frame.FACE_THICKNESS_MM == pytest.approx(18.25625)
    for name, part in raw.items():
        if name not in FACES:
            assert part.shape.Volume() == pytest.approx(old[name].shape.Volume(), abs=1e-5)
            assert (part.shape.Center()-old[name].shape.Center()).Length < 1e-7
            assert overlap(part.shape, old[name].shape) == pytest.approx(old[name].shape.Volume(), abs=1e-5)
            continue
        assert part.blank[-1] == pytest.approx(18.25625)
        assert "unqualified" in part.description.lower()
        assert part.shape.isValid()
        if name.startswith("main_"):
            n = [(v.Center()-b.point(0, 0, 0)).dot(b.normal()) for v in part.shape.Vertices()]
            assert (min(n), max(n)) == pytest.approx((-18.25625, 0), abs=1e-6)
        else:
            bounds = exact_bounds(part.shape)
            assert (bounds.ymin, bounds.ymax, bounds.zmin) == pytest.approx((-36, -17.74375, 0), abs=1e-6)
    for side in ("left", "right"):
        assert overlap(raw[f"main_lower_{side}"].shape, raw[f"kicker_{side}"].shape) < 1e-5
        for name in (f"leg_{side}_inner", f"leg_{side}_outer", f"kicker_cheek_{side}"):
            assert exact_bounds(raw[name].shape).zmin == pytest.approx(0, abs=1e-6)


def test_official_hold_and_led_axes_remain_open_through_thicker_faces(parts):
    count = 0
    for datums, diameter in ((main_tnut_datums(), model.V1_SELECTED_TNUT_HOLE_DIAMETER_MM),
                             (main_led_datums(), model.V1_LED_HOLE_DIAMETER_MM)):
        for u, s in datums.values():
            if s < 0:
                continue
            side, band = ("left" if u < b.HALF else "right"), ("lower" if s < b.HALF else "upper")
            shape = parts[f"main_{band}_{side}"].shape
            core = cq.Solid.makeCylinder(diameter/2-.1, 21, b.point(u-b.HALF, s, -20), b.normal())
            assert overlap(core, shape) < 1e-5, (u, s)
            count += 1
    for datums, diameter in ((kicker_foothold_datums(), model.V1_SELECTED_TNUT_HOLE_DIAMETER_MM),
                             ({k: v for k, v in main_led_datums().items() if v[1] < 0}, model.V1_LED_HOLE_DIAMETER_MM)):
        for u, s in datums.values():
            side = "left" if u < b.HALF else "right"
            core = cq.Solid.makeCylinder(diameter/2-.1, 21,
                cq.Vector(u-b.HALF, -37, b.V1_KICKER_HEIGHT_MM+s), cq.Vector(0, 1, 0))
            assert overlap(core, parts[f"kicker_{side}"].shape) < 1e-5, (u, s)
            count += 1
    assert count == 142+132


def test_exact_selected_inventory_and_face_screw_datum_shift():
    old = {c.name: c for c in baseline.connections()}
    current = {c.name: c for c in frame.connections()}
    assert len(current) == len(frame.connections()) == 278
    assert current.keys() == old.keys() == SPECS_BY_NAME.keys()
    moved = 0
    for name, c in current.items():
        reference = selected_connection(old[name])
        assert isinstance(c, ProductConnection)
        assert c.members == reference.members and c.kind == reference.kind
        assert (c.length, c.diameter, c.grip) == (reference.length, reference.diameter, reference.grip)
        assert c.direction.toTuple() == pytest.approx(reference.direction.toTuple())
        delta = -.25625 if c.members[0] in FACES else 0.
        assert (c.start-reference.start-reference.direction*delta).Length < 1e-7, name
        moved += delta != 0
        assert spec_for(c).qualified_for_design is False
        assert "inspection envelope only" in c.product_status
    assert moved == 80


def test_every_connection_has_receiving_material_and_open_core(parts):
    # Single-axis probes only, not expensive all-pairs hardware collision checks.
    for c in frame.connections():
        spec = spec_for(c)
        witness = cq.Solid.makeCylinder(6.5 if isinstance(spec, BoltSpec) else 4,
                                       c.length, c.start, c.direction)
        for index, name in enumerate(c.members):
            if isinstance(spec, BoltSpec):
                diameter = 11.1125
            elif name.startswith("clip_"):
                diameter = 4.3434  # Unchanged UK proxy, not a certified US hole.
            elif spec is SD9112:
                diameter = 3.2
            elif spec is SDS25112:
                diameter = 7 if index == 0 else 4
            else:
                diameter = 5.2 if index < len(c.members)-1 else 3.2
            core = cq.Solid.makeCylinder(diameter/2-.1, c.length, c.start, c.direction)
            assert overlap(core, parts[name].shape) < 1e-5, (c.name, name)
            assert overlap(witness, parts[name].shape) > 1, (c.name, name)


def test_screw_head_allowances_follow_flat_and_flush_datums():
    for c in frame.connections():
        spec = spec_for(c)
        if isinstance(spec, BoltSpec):
            continue
        _, head = c.components()
        center_depth = (head.Center()-c.start).dot(c.direction)
        sign = 1 if spec.seating == "flush" else -1
        assert center_depth == pytest.approx(sign*spec.head_allowance_height_mm/2), c.name
        assert head.Volume() == pytest.approx(3.141592653589793*(spec.head_allowance_diameter_mm/2)**2
                                             *spec.head_allowance_height_mm), c.name
