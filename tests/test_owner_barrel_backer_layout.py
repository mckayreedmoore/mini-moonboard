"""Current-viewer backer producer contract; geometry is not a drilling release."""

import cadquery as cq
import pytest

from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_backer_layout import build_layout
from scripts.owner_layout_protected import _volume


@pytest.fixture(scope="module")
def built():
    return build_layout(build_viewer_assembly())


def test_four_source_bound_complete_paths(built):
    assert built["source_pose"]["outer_header_forward_y_mm"] == -85.0
    assert built["fixed_inventory_counts"]["panel_screws"] == 66
    assert built["fixed_inventory_counts"]["frame_bolts"] == 12
    assert set(built["stations"]) == {
        "backer_attachment_left",
        "backer_attachment_right",
    }
    for station, row in built["stations"].items():
        assert row["mode"] == "direct"
        assert row["disposition"] == "REVISE"
        assert len(row["bolts"]) == len(row["barrels"]) == 2
        assert len(row["stacks"]) == 2
        assert len(row["drilling_paths"]) == 4
        assert len(row["access_paths"]) == 4
        for name, bolt in row["bolts"].items():
            assert bolt.members == (
                "base_header",
                f"inner_kicker_backer_{station.rsplit('_', 1)[-1]}",
            )
            assert bolt.length == pytest.approx(76.2)
            assert bolt.direction.toTuple() == (0.0, 0.0, -1.0)
            assert set(row["stacks"][name]) == {"shaft", "washer", "head"}
            assert (
                _volume(
                    row["stacks"][name]["shaft"],
                    row["barrels"][name.removesuffix("_bolt")],
                )
                > 0
            )
            assert all(
                isinstance(shape, cq.Shape) for shape in row["stacks"][name].values()
            )


def test_bores_tools_and_collision_screen_are_exposed(built):
    assert built["collision_screen"]["finite_clearance_screen_passed"] is True
    assert built["collision_screen"]["mutual_candidate_hits_mm3"] == {}
    assert built["collision_screen"]["nonempty_existing_obstacles"] == {}
    for row in built["collision_screen"]["candidates"].values():
        assert row["nominal_shaft_reach_past_axis_mm"] == pytest.approx(2.2)
        assert row["nominal_tip_past_modeled_barrel_far_wall_mm"] == pytest.approx(
            -2.8038
        )
        assert row["cross_bore_meets_machine_bore_mm3"] > 0
    for station in built["stations"].values():
        assert all(shape.Volume() > 0 for shape in station["drilling_paths"].values())
        assert all(shape.Volume() > 0 for shape in station["access_paths"].values())


def test_non_geometry_gates_remain_closed(built):
    assert built["source_probe_schema"] == "owner_barrel_backer_attachment_probe/v1"
    assert all(value is False for value in built["release_flags"].values())
    assert built["thread_engagement_verified"] is False
    assert built["capacity_verified"] is False
    assert built["assembly_sequence_verified"] is False


def test_rejects_changed_current_viewer_wood():
    assembly = build_viewer_assembly()
    assembly["wood"] = dict(assembly["wood"])
    name = "inner_kicker_backer_left"
    assembly["wood"][name] = assembly["wood"][name].translate(cq.Vector(0, 1, 0))
    with pytest.raises(ValueError, match="source timber contact changed"):
        build_layout(assembly)
