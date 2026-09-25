from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj12_compositor as compositor


def _box() -> cq.Shape:
    return cq.Solid.makeBox(12.0, 12.0, 12.0)


def _cylinder(x: float, y: float, *, length: float = 12.0) -> cq.Shape:
    return cq.Solid.makeCylinder(0.5, length, cq.Vector(x, y, 0), cq.Vector(0, 0, 1))


def test_expected_native_cut_ids_keep_separate_screw_head_operations() -> None:
    cutter = _cylinder(1, 1)

    class Source:
        def connections(self):
            return (
                SimpleNamespace(name="screw_host_first", members=("host", "panel"), kind="screw"),
                SimpleNamespace(name="screw_host_second", members=("panel", "host"), kind="screw"),
                SimpleNamespace(name="bolt", members=("host", "mate"), kind="bolt"),
            )

        def service_cutters(self):
            return (("host", "wire_slot", cutter), ("elsewhere", "other", cutter))

        def additional_machining_cutters(self):
            return (("host", "counterbore", "seat", cutter),)

    result = compositor._expected_native_cutter_ids(Source(), frozenset({"host"}))

    assert result == {
        "host": {
            "screw_host_first",
            "screw_host_first/head",
            "screw_host_second",
            "bolt",
            "service/0/wire_slot",
            "additional/0/counterbore/seat",
        }
    }


def test_inventory_must_match_source_binding_pin(tmp_path, monkeypatch) -> None:
    inventory = {"candidate": "development", "fixed_panel_kicker_screws": []}
    inventory_path = tmp_path / "source-inventory.json"
    inventory_path.write_text(json.dumps(inventory))
    monkeypatch.setattr(compositor, "WJ03_SOURCE_INVENTORY", inventory_path)
    binding = SimpleNamespace(
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    )

    compositor._inventory_matches_source_binding(inventory, binding)

    with pytest.raises(ValueError, match="differs from the canonical source inventory"):
        compositor._inventory_matches_source_binding(
            {**inventory, "source_commit": "unbound"}, binding
        )


def _frame_shape_fixture():
    axis_ids = [f"frame_bolt_{index}" for index in range(12)]
    inventory = {"starting_frame_bolts": [{"axis_id": axis_id} for axis_id in axis_ids]}
    records = tuple(
        {"axis_id": axis_id, "installed_component_count": 5}
        for axis_id in axis_ids
    )
    shapes = {
        f"{axis_id}/installed_component_{index}": _box()
        for axis_id in axis_ids
        for index in range(1, 6)
    }
    shapes.update(
        {f"{axis_id}/source_occupied_axis": _box() for axis_id in axis_ids}
    )
    return inventory, records, shapes


def test_frame_bolt_inventory_separates_installed_components_from_source_axes() -> None:
    inventory, records, shapes = _frame_shape_fixture()

    compositor._validate_frame_bolt_shapes(inventory, records, shapes)

    assert len(shapes) == 72
    assert sum(name.endswith("/installed_component_1") for name in shapes) == 12
    assert sum(name.endswith("/source_occupied_axis") for name in shapes) == 12


def test_frame_bolt_inventory_rejects_missing_role_or_wrong_source_axis() -> None:
    inventory, records, shapes = _frame_shape_fixture()
    del shapes["frame_bolt_0/installed_component_5"]
    with pytest.raises(ValueError, match="five installed components and one source occupied axis"):
        compositor._validate_frame_bolt_shapes(inventory, records, shapes)

    with pytest.raises(TypeError, match="starting_frame_bolts must be a list or tuple"):
        compositor._validate_frame_bolt_shapes({}, (), {})


def _additional_receiver_fixture():
    receiver_shapes = {
        host_id: cq.Solid.makeBox(20, 20, 20)
        for host_id in compositor.EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS
    }
    native_cut = cq.Solid.makeCylinder(
        1.0, 20.0, cq.Vector(18, 18, 0), cq.Vector(0, 0, 1)
    )
    receiver_shapes["base_rail_top"] = receiver_shapes["base_rail_top"].cut(
        native_cut
    ).clean()
    rows = []
    connections = []
    for host_id, count in compositor.EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS.items():
        for index in range(count):
            axis_id = f"fixed_{host_id}_{index + 1}"
            start = cq.Vector(-5.0, 2.0 + index * 4, 10.0)
            direction = cq.Vector(1, 0, 0)
            members = (f"panel_{host_id}", host_id)
            rows.append(
                {
                    "axis_id": axis_id,
                    "source_finished_receiver_member": host_id,
                    "candidate_finished_receiver_member": host_id,
                    "members": list(members),
                    "origin_global_xyz_mm": list(start.toTuple()),
                    "axis_global_xyz": list(direction.toTuple()),
                    "source_occupied_diameter_mm": 6.35,
                    "shop_purchased_length_mm": 63.5,
                }
            )
            connections.append(
                SimpleNamespace(
                    name=axis_id,
                    kind="screw",
                    members=members,
                    start=start,
                    direction=direction,
                    diameter=6.35,
                )
            )
    for index in range(54):
        axis_id = f"already_composed_host_{index + 1}"
        start = cq.Vector(-5.0, 1.0, 1.0)
        direction = cq.Vector(1, 0, 0)
        members = (f"panel_{index + 1}", "base_header")
        rows.append(
            {
                "axis_id": axis_id,
                "source_finished_receiver_member": "base_header",
                "candidate_finished_receiver_member": "base_header",
                "members": list(members),
                "origin_global_xyz_mm": list(start.toTuple()),
                "axis_global_xyz": list(direction.toTuple()),
                "source_occupied_diameter_mm": 6.35,
                "shop_purchased_length_mm": 63.5,
            }
        )
        connections.append(
            SimpleNamespace(
                name=axis_id,
                kind="screw",
                members=members,
                start=start,
                direction=direction,
                diameter=6.35,
            )
        )
    source = SimpleNamespace(
        panel_connections=lambda: tuple(connections),
        parts=lambda: tuple(
            SimpleNamespace(name=host_id, shape=shape)
            for host_id, shape in receiver_shapes.items()
        ),
    )
    preflight = SimpleNamespace(
        inventory={"fixed_panel_kicker_screws": rows},
        source=source,
        host_ids=frozenset({"base_header"}),
    )
    return preflight, receiver_shapes


def test_additional_receiver_overlay_cuts_purchased_axes_into_finished_source_parts() -> None:
    preflight, original_parts = _additional_receiver_fixture()
    original_volumes = {name: shape.Volume() for name, shape in original_parts.items()}

    finished, cutters, evidence = compositor._additional_panel_receiver_overlays(
        preflight
    )

    assert set(finished) == set(compositor.EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS)
    assert {
        host_id: len(host_cuts) for host_id, host_cuts in cutters.items()
    } == compositor.EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS
    assert sum(map(len, cutters.values())) == 12
    assert all(
        set(host_cuts) == set(evidence[host_id]["purchase_cut_ids"])
        and all(cut_id.startswith("panel_purchase/") for cut_id in host_cuts)
        for host_id, host_cuts in cutters.items()
    )
    for host_id, shape in finished.items():
        expected = original_parts[host_id].cut(*cutters[host_id].values()).clean()
        assert compositor.right_integration._shape_difference_volume(shape, expected) <= 1e-6
        assert shape.Volume() < original_volumes[host_id]
        assert evidence[host_id]["matches_source_plus_purchase_cuts"] is True
        assert evidence[host_id]["purchase_cut_intersection_mm3_by_id"]
        assert shape.isValid()
    assert {name: shape.Volume() for name, shape in original_parts.items()} == original_volumes


def test_additional_receiver_overlay_rejects_inventory_map_drift() -> None:
    preflight, _ = _additional_receiver_fixture()
    preflight.inventory["fixed_panel_kicker_screws"].pop()

    with pytest.raises(ValueError, match="additional receiver map|66 fixed axes"):
        compositor._additional_panel_receiver_overlays(preflight)

    inventory, records, shapes = _frame_shape_fixture()
    shapes["unbound_bolt/source_occupied_axis"] = shapes.pop(
        "frame_bolt_0/source_occupied_axis"
    )
    with pytest.raises(ValueError, match="five installed components and one source occupied axis"):
        compositor._validate_frame_bolt_shapes(inventory, records, shapes)


def _redirect_fixture():
    host_ids = frozenset({"base_post_center_left", "base_post_center_right"})
    receiver_rows = []
    native_cuts = {name: {} for name in host_ids}
    purchased_ids = {name: set() for name in host_ids}
    panel_connections = []
    candidate_cuts = {"inner_kicker_backer_left": {}, "inner_kicker_backer_right": {}}
    for side, x in (("left", -1.0), ("right", 1.0)):
        source_receiver = f"base_post_center_{side}"
        candidate_receiver = f"inner_kicker_backer_{side}"
        for index, z in ((1, 2.0), (2, 8.0)):
            axis_id = f"round_kicker_{side}_center_{index}"
            point = cq.Vector(x, 0, z)
            direction = cq.Vector(0, -1, 0)
            connection = SimpleNamespace(
                name=axis_id,
                members=(f"kicker_{side}", source_receiver),
                kind="screw",
                start=point,
                direction=direction,
                diameter=4.1402,
            )
            panel_connections.append(connection)
            receiver_rows.append(
                {
                    "axis_id": axis_id,
                    "members": list(connection.members),
                    "origin_global_xyz_mm": list(point.toTuple()),
                    "axis_global_xyz": list(direction.toTuple()),
                    "source_occupied_diameter_mm": connection.diameter,
                    "source_finished_receiver_member": source_receiver,
                    "candidate_finished_receiver_member": candidate_receiver,
                    "shop_purchased_length_mm": 63.5,
                }
            )
            native_cuts[source_receiver][axis_id] = _cylinder(x, z)
            purchase_id = f"panel_purchase/{axis_id}"
            purchased_ids[source_receiver].add(purchase_id)
            candidate_cuts[candidate_receiver][axis_id] = _cylinder(x, z, length=63.5)

    panel_connections.extend(
        SimpleNamespace(name=f"unrelated_panel_axis_{index}")
        for index in range(62)
    )
    source = SimpleNamespace(panel_connections=lambda: tuple(panel_connections))
    inventory = {"fixed_panel_kicker_screws": receiver_rows}
    preflight = SimpleNamespace(
        source=source,
        inventory=inventory,
        host_ids=host_ids,
        source_cutters_by_host=native_cuts,
        purchased_panel_cut_ids_by_host={
            name: frozenset(ids) for name, ids in purchased_ids.items()
        },
    )
    purchase_map = {
        name: {axis_id: _cylinder(1, 1, length=63.5) for axis_id in ids}
        for name, ids in purchased_ids.items()
    }
    return preflight, purchase_map, candidate_cuts


def test_redirected_fixed_axes_cut_backers_and_leave_old_posts_unmachined() -> None:
    preflight, purchase_map, expected_backer_cuts = _redirect_fixture()

    candidate_cuts = compositor._candidate_panel_extension_map(
        preflight, set(expected_backer_cuts)
    )
    final, applied_purchase = compositor._final_source_cutters(
        preflight, purchase_map, candidate_cuts
    )

    assert set(candidate_cuts) == {"inner_kicker_backer_left", "inner_kicker_backer_right"}
    assert {
        receiver: set(cuts) for receiver, cuts in candidate_cuts.items()
    } == {receiver: set(cuts) for receiver, cuts in expected_backer_cuts.items()}
    assert all(not cutters for cutters in final.values())
    assert all(not cutters for cutters in applied_purchase.values())


def test_candidate_part_machining_preserves_design_and_purchase_cuts() -> None:
    raw = {"backer": _box()}
    design_cut = cq.Solid.makeBox(1.0, 1.0, 1.0, cq.Vector(0.5, 0.5, 0.5))
    bore = _cylinder(4.0, 4.0)
    purchase = _cylinder(9.0, 9.0, length=12.0)

    finished = compositor._machine_candidate_parts(
        raw,
        {"backer": (design_cut,)},
        {"backer": {"bolt_axis": bore}},
        {"backer": {"panel_axis": purchase}},
    )["backer"]
    expected = raw["backer"].cut(design_cut, bore, purchase).clean()

    assert finished.isValid()
    assert compositor.right_integration._shape_difference_volume(finished, expected) <= 1e-6
    assert finished.Volume() < raw["backer"].Volume()


def test_retained_legacy_map_filters_all_twelve_composed_duties() -> None:
    target_stations = set(compositor.TARGET_STATIONS)
    retained_stations = {f"retained_duty_{index}" for index in range(12)}
    all_stations = sorted(target_stations | retained_stations)
    duties = []
    all_axis_ids = set()
    for station_id in all_stations:
        axes = [
            {"axis_id": f"{station_id}/sds_{index}"}
            for index in range(6)
        ]
        all_axis_ids.update(row["axis_id"] for row in axes)
        duties.append({"legacy_station_id": station_id, "legacy_sds_axes": axes})
    inventory = {"legacy_duties": duties}
    replaced = frozenset(
        axis_id
        for row in duties
        if row["legacy_station_id"] in target_stations
        for axis_id in (axis["axis_id"] for axis in row["legacy_sds_axes"])
    )
    right_clips = {
        station_id: _box()
        for station_id in set(all_stations) - set(compositor.RIGHT_STATIONS)
    }
    right_axes = {
        axis_id: _box()
        for axis_id in all_axis_ids
        if axis_id not in {
            axis["axis_id"]
            for row in duties
            if row["legacy_station_id"] in compositor.RIGHT_STATIONS
            for axis in row["legacy_sds_axes"]
        }
    }
    right = SimpleNamespace(
        retained_legacy_clip_shapes=right_clips,
        retained_source_axis_shapes=right_axes,
    )

    clips, axes = compositor._retained_legacy_parts(inventory, right, replaced)

    assert set(clips) == retained_stations
    assert len(axes) == compositor.EXPECTED_RETAINED_LEGACY_SDS_COUNT
    assert not set(axes) & replaced
