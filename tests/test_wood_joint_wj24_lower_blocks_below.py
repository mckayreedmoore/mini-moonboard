from __future__ import annotations

from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj24_lower_blocks_below as lower


def _box(x: float, y: float, z: float, origin: tuple[float, float, float]) -> cq.Shape:
    return cq.Solid.makeBox(x, y, z, cq.Vector(*origin))


def test_rail_center_plane_comes_from_raw_vertices_and_local_t_frame() -> None:
    rail_id = "base_rail_service_lower_right"
    origin_y = 1353.874134
    geometry = SimpleNamespace(
        source_inventory={
            "parts": [
                {
                    "part_id": rail_id,
                    "local_to_global_transform": [
                        [1, 0, 0, 0],
                        [0, 1, 0, origin_y],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1],
                    ],
                    "local_axes": {"T": [0, 1, 0]},
                }
            ]
        },
        raw_hosts={rail_id: _box(50, 38.1, 20, (0, origin_y - 38.1, 0))},
    )

    normal, point, evidence = lower._rail_center_plane(geometry, rail_id)

    assert normal.toTuple() == pytest.approx((0, 1, 0))
    assert point.toTuple() == pytest.approx((0, origin_y - 19.05, 0))
    assert evidence["raw_t_bounds_local_mm"] == pytest.approx([-38.1, 0])
    assert evidence["center_global_t_mm"] == pytest.approx(1334.824134)


def test_mirror_reflects_block_across_center_t_plane_without_changing_volume() -> None:
    source = _box(2, 3, 4, (10, 20, 30))
    mirrored = lower._mirror_shape(
        source,
        cq.Vector(0, 1, 0),
        cq.Vector(0, 19, 0),
        "test cleat",
    )

    assert mirrored.isValid()
    assert mirrored.Volume() == pytest.approx(source.Volume())
    assert mirrored.BoundingBox().ymin == pytest.approx(15)
    assert mirrored.BoundingBox().ymax == pytest.approx(18)


def test_target_axis_binding_uses_candidate_receiver_when_station_is_absent() -> None:
    bore_map: dict[str, object] = {}
    expected_axis_count = 0
    for part_id, target in lower.TARGETS.items():
        for suffix in target["axis_suffixes"]:
            host_id = target["rail"] if suffix.startswith("lower_rail_") else target["other_receiver"]
            axis_id = f"family/{target['station']}/{suffix}"
            station = None if target["family"] != "left_service" else target["station"]
            bore_map[axis_id] = SimpleNamespace(
                family=target["family"],
                station_id=station,
                receiver_ids=(part_id, host_id),
            )
            expected_axis_count += 1
    geometry = SimpleNamespace(candidate_bores=bore_map)

    by_part = lower._read_target_axes(geometry)

    assert sum(map(len, by_part.values())) == expected_axis_count == 16
    assert len(by_part["wj04_lower_full_stock_cleat"]) == 4
    assert len(by_part["wj06_outer_lower_right_cleat"]) == 4


def test_target_axis_binding_rejects_reversed_receiver_order() -> None:
    part_id, target = next(iter(lower.TARGETS.items()))
    bore_map = {}
    for suffix in target["axis_suffixes"]:
        host_id = target["rail"] if suffix.startswith("lower_rail_") else target["other_receiver"]
        bore_map[f"family/{target['station']}/{suffix}"] = SimpleNamespace(
            family=target["family"],
            station_id=None,
            receiver_ids=(host_id, part_id),
        )

    with pytest.raises(ValueError, match="receiver order/map"):
        lower._read_target_axes(SimpleNamespace(candidate_bores=bore_map))


def test_host_replay_uses_retained_cuts_and_excludes_replaced_source_cutters() -> None:
    target_host = "base_rail_service_lower_right"
    raw_hosts = {host_id: _box(10, 10, 10, (0, 0, 0)) for host_id in lower.HOST_IDS}
    source_maps = {host_id: {} for host_id in lower.HOST_IDS}
    source_maps[target_host] = {
        "retained/native": _box(1, 1, 1, (1, 1, 1)),
        "replaced/old-axis": _box(1, 1, 1, (3, 3, 3)),
    }
    new_bore = _box(1, 1, 1, (5, 5, 5))
    bore = SimpleNamespace(shape=new_bore, receiver_ids=("cleat", target_host))
    geometry = SimpleNamespace(
        raw_hosts=raw_hosts,
        applied_source_cutters_by_host=source_maps,
        replaced_source_cutter_ids=frozenset({"replaced/old-axis"}),
    )

    rebuilt, replay = lower._rebuild_affected_hosts(
        geometry, {"new/axis": bore}
    )

    assert set(rebuilt) == set(lower.HOST_IDS)
    assert replay[target_host]["retained_source_and_purchase_cutter_count"] == 1
    assert replay[target_host]["excluded_replaced_source_cutter_count"] == 1
    assert replay[target_host]["candidate_bore_axis_ids"] == ["new/axis"]
    assert rebuilt[target_host].Volume() == pytest.approx(998)
