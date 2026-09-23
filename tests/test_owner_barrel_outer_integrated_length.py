"""Integrated-only outer/top bolt lengths preserve the historical viewer."""

import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_outer_top_layout as outer
from scripts import simple_owner_duty_ledger as ledger


@pytest.fixture(scope="module")
def wood():
    return {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}


def test_integrated_outer_top_lengths_are_family_specific(wood):
    integrated = outer.build_integrated_recessed_layout(wood)
    historical = outer.build_recessed_viewer_layout(wood)
    revised = {
        "base_outer_side": 114.3,
        "header_outer_post": 114.3,
        "top_center": 114.3,
        "top_outer": 127.0,
    }
    duties = ledger.selected_duties()
    for station, row in integrated["stations"].items():
        expected = revised[duties[station]["family"]]
        assert len(row["bolts"]) == 2
        for name, bolt in row["bolts"].items():
            assert bolt.length == pytest.approx(expected)
            assert row["stacks"][name]["shaft"].Volume() == pytest.approx(
                3.141592653589793 * (bolt.diameter / 2) ** 2 * bolt.length,
                rel=1e-5,
            )
            old = historical["stations"][station]["bolts"][name]
            assert old.length == pytest.approx(127.0)
            assert bolt.start.toTuple() == pytest.approx(old.start.toTuple())
            assert (
                row["drilling_paths"].keys()
                == historical["stations"][station]["drilling_paths"].keys()
            )
    assert integrated["diagnostics"]["integrated_length_revision"] == revised


def test_integrated_top_outer_bores_alone_gain_two_mm_tip_clearance(wood):
    integrated = outer.build_integrated_recessed_layout(wood)
    historical = outer.build_recessed_viewer_layout(wood)
    duties = ledger.selected_duties()
    changed = []
    for station, data in integrated["stations"].items():
        family = duties[station]["family"]
        for bolt_name, bolt in data["bolts"].items():
            bore_name = bolt_name.removesuffix("_bolt") + "/machine_bore"
            bore = data["drilling_paths"][bore_name]
            old_bore = historical["stations"][station]["drilling_paths"][bore_name]
            if family != "top_outer":
                assert bore.Volume() == pytest.approx(old_bore.Volume())
                bounds = bore.BoundingBox()
                old_bounds = old_bore.BoundingBox()
                for coordinate in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"):
                    assert getattr(bounds, coordinate) == pytest.approx(
                        getattr(old_bounds, coordinate)
                    )
                continue
            axis = bolt.direction.normalized()
            bore_end = max(vertex.Center().dot(axis) for vertex in bore.Vertices())
            bolt_tip = (bolt.start + axis * bolt.length).dot(axis)
            assert bore_end - bolt_tip == pytest.approx(2.0)
            assert bore.Volume() - old_bore.Volume() == pytest.approx(
                3.141592653589793 * (outer.MACHINE_BORE_D_MM / 2) ** 2 * 2.0,
                rel=1e-5,
            )
            changed.append(bore_name)
    assert len(changed) == 4
