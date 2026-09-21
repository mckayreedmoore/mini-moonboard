"""PB07 may move only the six outer rail-hole rows."""

from dataclasses import replace
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea.floor_flush_run import face_contacts
from scripts import simple_pb05_native as pb05
from scripts import simple_pb06_upper_center_native as pb06
from scripts import simple_pb07_outer_rail_native as pb07
from scripts.simple_center_pb02_native import PB02Native, prepare_case


def test_bore_to_other_block_is_a_blocking_mode():
    first = SimpleNamespace(
        block_name="first_block",
        block=cq.Solid.makeBox(10, 10, 10, cq.Vector(0, 0, 0)),
        bores={
            "first_bore": cq.Solid.makeCylinder(
                1, 8, cq.Vector(21, 5, 5), cq.Vector(1, 0, 0)
            )
        },
    )
    second = SimpleNamespace(
        block_name="second_block",
        block=cq.Solid.makeBox(10, 10, 10, cq.Vector(20, 0, 0)),
        bores={},
    )
    assert pb07._bore_block_hits("first", first, "second", second) == {
        "first/first_bore|second": {
            "second_block": pytest.approx(8 * 3.141592653589793)
        }
    }


@pytest.fixture(scope="module")
def candidates():
    return pb06.PB06Native(), pb07.PB07Native()


def test_revised_native_preserves_pb06_unmoved_axes(candidates):
    source, candidate = candidates
    result = pb07.screen(candidate)
    assert result["source_id"] == pb07.SOURCE_ID != source.KEY
    assert not set(pb06.TARGET_STATIONS) & {part.name for part in candidate.parts()}
    assert (
        result["source_fingerprint_sha256"] != result["pb06_parent_fingerprint_sha256"]
    )
    assert result["inventory"] == {
        "blocks": 10,
        "outer_blocks": 6,
        "original_frame_bolt_axes": 12,
        "panel_kicker_axes": 66,
        "legacy_sds_duties": 12,
        "legacy_sds_axes": 72,
        "new_bolt_axes": 40,
    }
    assert result["geometry_gate"]["detached_six_outer_full_nominal_and_tool"] is True
    assert result["geometry_gate"]["fixed_action_signed_end_edge_sensitivity"] is True
    assert (
        result["geometry_gate"]["new_upper_center_pair_interactions"]["passes"] is True
    )
    assert result["geometry_gate"]["passes"] is True
    assert result["geometry_gate"]["outer_second_rail_far_x_edge_mm"] == 25.25
    assert result["geometry_gate"]["conditional_4d_far_x_margin_mm"] == pytest.approx(
        -0.15
    )
    assert tuple(map(pb05._axis, candidate.panel_connections())) == tuple(
        map(pb05._axis, source.panel_connections())
    )
    for name, original in source.pb03_geometries().items():
        revised = candidate.pb03_geometries()[name]
        if name not in pb07.OUTER_STATIONS:
            assert tuple(map(pb05._axis, revised.bolts)) == tuple(
                map(pb05._axis, original.bolts)
            )
        else:
            assert len(revised.bolts) == 4
            assert revised.report["rail_bore_n_offset_mm"] == (
                45.0
                if name in pb07.upper.TARGET_STATIONS
                else pb07.lower.RAIL_N_OFFSET_MM
            )
            old_rail = [b for b in original.bolts if b.members[0] == original.rail_name]
            new_rail = [b for b in revised.bolts if b.members[0] == revised.rail_name]
            assert len(new_rail) == len(old_rail) == 2
            assert abs(new_rail[0].start.x - old_rail[0].start.x) == pytest.approx(1.0)
            assert abs(
                revised.bores[new_rail[0].name].BoundingBox().xmin
                - original.bores[old_rail[0].name].BoundingBox().xmin
            ) == pytest.approx(1.0)
            assert set(revised.stacks[new_rail[0].name]) == {
                "shaft",
                "head",
                "near_washer",
                "far_washer",
                "nut",
            }
    assert all(
        result[field] is False
        for field in (
            "native_solve",
            "force_transfer",
            "acceptance",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )


def test_preparation_is_pb07_not_pb06(candidates):
    _, candidate = candidates
    _, metadata = prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=700.0,
        bolt_lateral_n_per_mm=1200.0,
        face_normal_total_n_per_mm=2400.0,
        module=candidate,
        expected_candidate=pb07.SOURCE_ID,
        member_contacts=face_contacts(PB02Native()),
        expected_legacy_station_count=12,
        post_prepare=candidate.validate_prepared_case,
    )
    assert metadata["pb07_preparation_validated"] is True
    assert "pb06_candidate" not in metadata
    assert "pb06_preparation_validated" not in metadata
    assert len(metadata["legacy_proxy_stations"]) == 12
    assert all(metadata[field] is False for field in pb07._FALSE_FLAGS)


def test_compact_stock_is_only_a_detached_nominal_screen(candidates):
    _, candidate = candidates
    result = pb07.screen_short_stock(candidate)
    assert result["common_block_length_mm"] == 152.4
    assert {
        key: result["inventory"][key]
        for key in (
            "blocks",
            "bolts",
            "panel_kicker_axes",
            "original_frame_bolt_axes",
            "legacy_duties",
            "legacy_angle_solids",
            "legacy_sds_axes",
        )
    } == {
        "blocks": 10,
        "bolts": 40,
        "panel_kicker_axes": 66,
        "original_frame_bolt_axes": 12,
        "legacy_duties": 12,
        "legacy_angle_solids": 12,
        "legacy_sds_axes": 72,
    }
    assert result["inventory"]["retained_timber_solids"] > 0
    assert result["conditional_4d_far_x_margin_mm"] == pytest.approx(-0.15)
    assert set(result["stations"]) == set(candidate.pb03_geometries())
    for name in pb07.OUTER_STATIONS:
        station = result["stations"][name]
        assert station["rail_x_offsets_mm"] == [26.0, 70.0]
        for bolt, opening in station["end_openings_mm"].items():
            if "_rail_" in bolt and bolt.endswith("/washer"):
                assert opening["near_center_mm"] - opening[
                    "near_net_mm"
                ] == pytest.approx(12.7)
    assert result["decision"] == "ADVANCE_STATIC_GEOMETRY_ONLY", {
        "failed_station_gates": {
            name: {key: passed for key, passed in row["gates"].items() if not passed}
            for name, row in result["stations"].items()
            if not all(row["gates"].values())
        },
        "pair_hits_mm3": result["pair_hits_mm3"],
    }
    assert result["blocking_pair_hits_mm3"] == {}
    assert result["bore_to_other_block_hits_mm3"] == {}
    assert all(result[field] is False for field in pb07._FALSE_FLAGS)


def test_compact_screen_rejects_changed_native_block_and_frame_axis(
    candidates, monkeypatch
):
    _, candidate = candidates
    with monkeypatch.context() as patcher:
        first = candidate._blocks[0]
        patcher.setattr(
            candidate,
            "_blocks",
            (
                replace(first, shape=first.shape.translate((1.0, 0.0, 0.0))),
                *candidate._blocks[1:],
            ),
        )
        with pytest.raises(ValueError, match="short-stock source changed"):
            pb07.screen_short_stock(candidate)
    with monkeypatch.context() as patcher:
        rows = list(candidate._base_connections)
        index = next(i for i, row in enumerate(rows) if row.kind == "bolt")
        rows[index] = replace(rows[index], start=rows[index].start + cq.Vector(1, 0, 0))
        patcher.setattr(candidate, "_base_connections", tuple(rows))
        with pytest.raises(ValueError, match="short-stock source changed"):
            pb07.screen_short_stock(candidate)
