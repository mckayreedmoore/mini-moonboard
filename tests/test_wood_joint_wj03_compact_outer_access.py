import json
from types import SimpleNamespace

import cadquery as cq

from scripts import wood_joint_wj03_compact_outer_probe as outer_probe
from scripts.wood_joint_wj03_compact_outer_access import (
    SOURCE_INVENTORY,
    SequenceHostObstacle,
    _combined_header_shape,
    _frame_component_obstacles,
    _motion_for_body,
    _panel_staging,
    _part_extent_along,
    _sequence_host_adapter_map,
)


def test_combined_header_keeps_restored_legacy_hole_and_adds_only_new_bores():
    raw = cq.Solid.makeBox(10, 10, 10)
    legacy_sds = cq.Solid.makeCylinder(0.8, 12, cq.Vector(2, 5, -1))
    retained_source = cq.Solid.makeCylinder(0.8, 12, cq.Vector(8, 5, -1))
    wj05_bore = cq.Solid.makeCylinder(0.8, 12, cq.Vector(5, 5, -1))
    old_source_header = raw.cut(legacy_sds).cut(retained_source)
    wj03_finished_header = old_source_header.fuse(legacy_sds.intersect(raw)).clean()

    combined = _combined_header_shape(
        wj03_finished_header, {"new_wj05_bore": wj05_bore}
    )

    assert old_source_header.intersect(legacy_sds).Volume() < 1e-6
    assert wj03_finished_header.intersect(legacy_sds).Volume() > 0
    assert combined.intersect(legacy_sds).Volume() > 0
    assert combined.intersect(retained_source).Volume() < 1e-6
    assert combined.intersect(wj05_bore).Volume() < 1e-6
    assert abs(raw.Volume() - 1000) < 1e-6


def test_sequence_host_adapter_preserves_combined_candidate_header_shape():
    source_host = cq.Solid.makeBox(10, 10, 10)
    new_wj05_bore = cq.Solid.makeCylinder(0.8, 12, cq.Vector(5, 5, -1))
    combined = _combined_header_shape(source_host, {"new_wj05_bore": new_wj05_bore})
    geometry = SimpleNamespace(host_wood={"base_header": combined})

    adapted = _sequence_host_adapter_map(geometry, {"base_header"})["base_header"]

    assert isinstance(adapted, SequenceHostObstacle)
    assert adapted.finished_shape is combined
    assert adapted.finished_shape.intersect(new_wj05_bore).Volume() < 1e-6
    assert abs(adapted.finished_shape.Volume() - combined.Volume()) < 1e-9


def test_body_motion_vectors_follow_installed_bolt_layer_order():
    side = "left"
    spine = "knee_outer_left_spine"
    link = "knee_outer_left_under_header_link"
    bridge = "knee_outer_left_rear_bridge"
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    spec = next(
        row
        for row in outer_probe.HYPOTHESES
        if row.id == "compact_bridge_rear_bevel_4x6_spine_137_7"
    )
    ids = {
        "spine": spine,
        "bridge": bridge,
        "under": link,
    }
    source_wood = {
        "base_post_outer_left": cq.Solid.makeBox(
            38.1, 38.1, 800, cq.Vector(-1300, -200, 0)
        )
    }
    stacks = outer_probe._stacks(
        side,
        source_wood,
        spec,
        ids,
        outer_probe._source_frame(inventory, "base_side_left"),
    )

    assert len(stacks) == 10
    assert stacks["knee_outer_left_header_1"].layers[0].body_id == "base_header"
    assert stacks["knee_outer_left_header_1"].layers[1].body_id == link
    assert stacks["knee_outer_left_header_1"].direction.toTuple() == (0.0, 0.0, -1.0)

    spine_insert, spine_remove, _ = _motion_for_body(side, spine, stacks)
    link_insert, link_remove, _ = _motion_for_body(side, link, stacks)
    bridge_insert, bridge_remove, _ = _motion_for_body(side, bridge, stacks)

    assert spine_insert.toTuple() == (1.0, 0.0, 0.0)
    assert spine_remove.toTuple() == (-1.0, 0.0, 0.0)
    assert link_insert.toTuple() == (0.0, 0.0, 1.0)
    assert link_remove.toTuple() == (0.0, 0.0, -1.0)
    assert bridge_insert.toTuple() == (0.0, 1.0, 0.0)
    assert bridge_remove.toTuple() == (0.0, -1.0, 0.0)


def test_frame_bolt_components_are_added_as_retained_access_obstacles():
    protected = {
        "solids": {
            "frame_bolt_components": {
                f"frame-bolt-1/{role}": cq.Solid.makeBox(1, 1, 1)
                for role in ("shaft", "head_washer", "nut_washer", "head", "nut")
            }
        }
    }

    obstacles = _frame_component_obstacles(protected)

    assert set(obstacles) == {
        f"frame_bolt_component/frame-bolt-1/{role}"
        for role in ("shaft", "head_washer", "nut_washer", "head", "nut")
    }


def test_panel_staging_carries_only_source_assigned_tnuts_and_keeps_lights_fixed():
    panels = {
        name: cq.Solid.makeBox(5, 5, 5, cq.Vector(x, 0, 100))
        for name, x in (
            ("main_lower_left", 0),
            ("main_lower_right", 10),
            ("kicker_left", 20),
            ("kicker_right", 30),
        )
    }
    protected = {
        "solids": {
            "tnuts": {
                "tnut-lower": cq.Solid.makeBox(1, 1, 1, cq.Vector(1, 1, 101)),
                "tnut-upper": cq.Solid.makeBox(1, 1, 1, cq.Vector(11, 1, 101)),
            },
            "lights": {"light-1": cq.Solid.makeBox(1, 1, 1)},
        }
    }
    owners = {
        "tnut-lower": "main_lower_left",
        "tnut-upper": "main_upper_left",
    }

    staged = _panel_staging(panels, protected, owners)

    assert set(staged) == {
        "staged/main_lower_left/panel",
        "staged/main_lower_left/tnut/tnut-lower",
        "staged/main_lower_right/panel",
        "staged/kicker_left/panel",
        "staged/kicker_right/panel",
    }
    lower_start = panels["main_lower_left"].BoundingBox()
    lower_staged = staged["staged/main_lower_left/panel"].BoundingBox()
    kicker_start = panels["kicker_left"].BoundingBox()
    kicker_staged = staged["staged/kicker_left/panel"].BoundingBox()
    assert lower_staged.ymin > lower_start.ymin
    assert lower_staged.zmin < lower_start.zmin
    assert kicker_staged.ymin == kicker_start.ymin + 100
    assert kicker_staged.zmin == kicker_start.zmin
    assert all("light" not in name for name in staged)


def test_part_motion_extent_uses_installed_shape_bounds():
    part = cq.Solid.makeBox(10, 20, 30)

    assert _part_extent_along(part, cq.Vector(1, 0, 0)) == 10
    assert _part_extent_along(part, cq.Vector(0, 1, 0)) == 20
    assert _part_extent_along(part, cq.Vector(0, 0, 1)) == 30
