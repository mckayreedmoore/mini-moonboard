"""WJ-03 combined outer-node geometry and topology."""

import json

import cadquery as cq
import pytest

import mini_moonboard.wood_joint_frame as frame_model
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import (
    LEGACY_DUTY_HOSTS,
    SOURCE_HOST_IDS,
    build_outer_nodes,
    detached_hardware_removal_shapes,
)
from mini_moonboard.wood_joint_geometry import (
    bolt_stack_report,
    washer_support_report,
)


@pytest.fixture(scope="module")
def nodes():
    return build_outer_nodes()


def _bounds(shape):
    box = shape.BoundingBox()
    return (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)


def test_each_outer_node_maps_two_duties_three_hosts_and_six_interfaces(nodes):
    assert set(nodes) == {"left", "right"}
    for side, node in nodes.items():
        assert node.owner_id == f"knee_outer_{side}"
        assert set(node.duties) == {
            f"clip_timber_header_outer_{side}",
            f"clip_angle_base_{side}",
        }
        assert set(node.source_hosts) == {
            "base_header",
            f"base_post_outer_{side}",
            f"base_side_{side}",
        }
        assert len(node.parts) == 3
        assert len(node.interfaces) == 6
        assert len(node.stacks) == 10
        assert all(area > 0 for area in node.contact_areas_mm2.values())


def test_live_source_modules_shapes_and_exact_duty_hosts_are_inventory_bound(nodes):
    binding = nodes["left"].source_binding
    assert binding is nodes["right"].source_binding
    assert binding.duty_host_mapping == LEGACY_DUTY_HOSTS
    assert set(binding.uncut_host_shape_sha256) == set(SOURCE_HOST_IDS)
    assert set(binding.runtime_module_sha256) == {
        "mini_moonboard/floor_flush_width.py",
        "mini_moonboard/compact_floor_flush_frame.py",
        "scripts/simple_owner_duty_ledger.py",
    }
    assert all(len(digest) == 64 for digest in binding.uncut_host_shape_sha256.values())
    assert len(binding.fixed_screw_axes_sha256) == 64
    assert len(binding.frame_bolt_axes_sha256) == 64


def test_source_binding_fails_if_owned_duty_host_mapping_drifts(tmp_path, monkeypatch):
    inventory = json.loads(frame_model.SOURCE_INVENTORY.read_text())
    duty = next(
        row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] == "clip_angle_base_left"
    )
    duty["legacy_host_members"] = ["base_header", "base_side_right"]
    changed = tmp_path / "source-inventory.json"
    changed.write_text(json.dumps(inventory))
    monkeypatch.setattr(frame_model, "SOURCE_INVENTORY", changed)
    with pytest.raises(ValueError, match="duty-host mapping drifted"):
        frame_model.validate_source_binding(variant(KERF_RIGHT))


def test_source_binding_fails_if_fixed_or_frame_bolt_axis_drifts(
    tmp_path, monkeypatch
):
    inventory = json.loads(frame_model.SOURCE_INVENTORY.read_text())

    fixed_drift = json.loads(json.dumps(inventory))
    fixed_drift["fixed_panel_kicker_screws"][0]["origin_global_xyz_mm"][0] += 0.001
    fixed_path = tmp_path / "fixed-axis-drift.json"
    fixed_path.write_text(json.dumps(fixed_drift))
    monkeypatch.setattr(frame_model, "SOURCE_INVENTORY", fixed_path)
    with pytest.raises(ValueError, match="fixed panel/kicker axes drifted"):
        frame_model.validate_source_binding(variant(KERF_RIGHT))

    bolt_drift = json.loads(json.dumps(inventory))
    bolt_drift["starting_frame_bolts"][0]["source_grip_mm"] += 0.001
    bolt_path = tmp_path / "frame-bolt-drift.json"
    bolt_path.write_text(json.dumps(bolt_drift))
    monkeypatch.setattr(frame_model, "SOURCE_INVENTORY", bolt_path)
    with pytest.raises(ValueError, match="retained frame-bolt axes drifted"):
        frame_model.validate_source_binding(variant(KERF_RIGHT))


def test_three_realizable_4x4_cut_parts_mirror_kerf_right_geometry(nodes):
    left = nodes["left"].parts
    right = nodes["right"].parts
    assert _bounds(left["knee_outer_left_spine"].uncut_shape) == pytest.approx(
        (-1308.1, -1219.2, -182.05, -93.15, 146.05, 416.0)
    )
    assert _bounds(left["knee_outer_left_rear_bridge"].uncut_shape) == pytest.approx(
        (-1308.1, -924.9, -270.95, -182.05, 150.0, 238.9)
    )
    assert _bounds(
        left["knee_outer_left_under_header_link"].uncut_shape
    ) == pytest.approx((-1110.1, -924.9, -182.05, -93.15, 150.0, 238.9))
    assert _bounds(right["knee_outer_right_spine"].uncut_shape) == pytest.approx(
        (1216.025, 1304.925, -182.05, -93.15, 146.05, 416.0)
    )
    assert _bounds(right["knee_outer_right_rear_bridge"].uncut_shape) == pytest.approx(
        (921.725, 1304.925, -270.95, -182.05, 150.0, 238.9)
    )
    assert _bounds(
        right["knee_outer_right_under_header_link"].uncut_shape
    ) == pytest.approx((921.725, 1106.925, -182.05, -93.15, 150.0, 238.9))
    for node in nodes.values():
        for part in node.parts.values():
            assert part.stock_product.startswith("nominal 4x4")
            assert part.modifications
            assert part.finished_shape.Volume() < part.uncut_shape.Volume()


def test_every_stack_bore_is_contained_and_post_stacks_tie_two_members(nodes):
    source = variant(KERF_RIGHT)
    source_wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    for side, node in nodes.items():
        physical = {
            **source_wood,
            **{key: part.uncut_shape for key, part in node.parts.items()},
        }
        for stack in node.stacks.values():
            position = stack.head_seat.center
            direction = stack.direction
            for layer in stack.layers:
                cutter = cq.Solid.makeCylinder(
                    stack.hardware.drill_diameter_mm / 2,
                    layer.thickness_mm,
                    position,
                    direction,
                )
                fraction = (
                    cutter.intersect(physical[layer.body_id]).Volume() / cutter.Volume()
                )
                assert fraction == pytest.approx(1.0, abs=1e-7), (
                    stack.id,
                    layer.body_id,
                )
                position += direction * layer.thickness_mm
        post_stacks = [stack for name, stack in node.stacks.items() if "_post_" in name]
        assert len(post_stacks) == 2
        for stack in post_stacks:
            assert [layer.body_id for layer in stack.layers] == [
                f"knee_outer_{side}_spine",
                f"base_post_outer_{side}",
            ]
            assert stack.grip_mm == pytest.approx(127.0)
            assert stack.hardware.under_head_length_mm == pytest.approx(152.4)


def test_all_changed_source_hosts_are_finished_with_twelve_candidate_bores(nodes):
    left, right = nodes["left"], nodes["right"]
    assert (
        left.source_host_parts["base_header"] is right.source_host_parts["base_header"]
    )
    unique_hosts = {
        part_id: part
        for node in nodes.values()
        for part_id, part in node.source_host_parts.items()
    }
    assert set(unique_hosts) == set(SOURCE_HOST_IDS)
    assert {
        part_id: len(
            [
                cut
                for cut in part.modifications
                if not cut.id.endswith("retained_source_openings")
            ]
        )
        for part_id, part in unique_hosts.items()
    } == {
        "base_header": 4,
        "base_post_outer_left": 2,
        "base_post_outer_right": 2,
        "base_side_left": 2,
        "base_side_right": 2,
    }
    assert (
        sum(
            len(
                [
                    cut
                    for cut in part.modifications
                    if not cut.id.endswith("retained_source_openings")
                ]
            )
            for part in unique_hosts.values()
        )
        == 12
    )
    assert all(
        any(cut.id.endswith("retained_source_openings") for cut in part.modifications)
        for part in unique_hosts.values()
    )
    for part in unique_hosts.values():
        assert part.finished_shape.Volume() < part.uncut_shape.Volume()
        assert len(part.finished_fingerprint) == 64


def test_interfaces_use_actual_contact_frames_and_force_reference_points(nodes):
    expected_normals = {
        "spine_post": {"left": (1, 0, 0), "right": (-1, 0, 0)},
        "spine_side": {"left": (1, 0, 0), "right": (-1, 0, 0)},
        "bridge_spine": {"left": (0, 1, 0), "right": (0, 1, 0)},
        "bridge_link": {"left": (0, 1, 0), "right": (0, 1, 0)},
        "link_header": {"left": (0, 0, 1), "right": (0, 0, 1)},
        "spine_header_end": {"left": (1, 0, 0), "right": (-1, 0, 0)},
    }
    for side, node in nodes.items():
        for interface in node.interfaces:
            suffix = interface.id.removeprefix(f"knee_outer_{side}_")
            local = interface.frame
            assert local.origin.toTuple() == pytest.approx(
                interface.force_reference_point.toTuple()
            )
            assert local.origin.Length > 100
            assert local.n.toTuple() == pytest.approx(expected_normals[suffix][side])
            assert local.x.cross(local.t).dot(local.n) == pytest.approx(1.0)


def test_all_forty_washer_seats_have_full_annular_support(nodes):
    reports = []
    for node in nodes.values():
        bodies = {
            **{name: part.finished_shape for name, part in node.parts.items()},
            **{
                name: part.finished_shape
                for name, part in node.source_host_parts.items()
            },
        }
        for stack in node.stacks.values():
            assert stack.hardware.washer_id_mm == pytest.approx(8.0)
            reports.extend(
                washer_support_report(seat, bodies[seat.body_id], stack.hardware)
                for seat in (stack.head_seat, stack.nut_seat)
            )
    assert len(reports) == 40
    assert all(report.full_seat for report in reports)
    assert all(report.support_fraction == pytest.approx(1.0) for report in reports)


def test_detached_hardware_has_three_conservative_fifty_mm_outward_sweeps(nodes):
    for node in nodes.values():
        for stack in node.stacks.values():
            shapes = detached_hardware_removal_shapes(stack)
            assert set(shapes) == {
                "head_washer_outward",
                "nut_washer_outward",
                "nut_outward",
            }
            assert all(
                shape.isValid() and shape.Volume() > 0 for shape in shapes.values()
            )


def test_all_provisional_stacks_fit_declared_length_and_thread_envelope(nodes):
    for node in nodes.values():
        reports = [bolt_stack_report(stack) for stack in node.stacks.values()]
        assert all(report.passes for report in reports)
        assert {round(report.length_margin_mm, 3) for report in reports} == {13.818}
        assert sorted(
            stack.hardware.under_head_length_mm for stack in node.stacks.values()
        ) == [
            152.4,
            152.4,
            152.4,
            152.4,
            203.2,
            203.2,
            203.2,
            203.2,
            203.2,
            203.2,
        ]


def test_outer_node_records_exact_envelope_exception_without_release(nodes):
    for node in nodes.values():
        assert node.rear_projection_from_header_front_mm == pytest.approx(234.95)
        assert node.rear_envelope_exception_mm == pytest.approx(95.25)
