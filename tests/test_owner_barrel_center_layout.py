"""Six direct cross-dowel center duties, strictly viewer/development only."""

import json

import pytest

from scripts import owner_barrel_center_layout as candidate
from scripts import simple_cross_dowel_continuation as shared


def test_shared_provisional_hardware_basis():
    assert candidate.SOURCE_ID == "owner-barrel-center-six-direct-layout-v1"
    assert candidate.BARREL_LENGTH_MM == shared.BARREL_LENGTH_MM
    assert candidate.BARREL_OD_MM == shared.BARREL_OD_MM
    assert candidate.BOLT_LENGTH_MM == shared.BOLT_LENGTH_MM
    assert candidate.THREAD_AXIS_OFFSET_MM == pytest.approx(8.001)
    assert candidate.AXIS_OFFSET_SENSITIVITY_MM == shared.AXIS_OFFSET_SENSITIVITY_MM
    assert len(candidate.STATIONS) == 6


@pytest.fixture(scope="module")
def assembly():
    wood = candidate._wood()[1]
    assembled = candidate.build_layout(wood)
    print(
        "CENTER_SIX_DIAGNOSTIC="
        + json.dumps(
            {
                station: {
                    "mode": row["mode"],
                    "disposition": row["disposition"],
                    "reasons": assembled["diagnostics"]["stations"][station][
                        "alternate_reasons"
                    ],
                    "protected_hit_features": [
                        name
                        for bolt in assembled["diagnostics"]["stations"][station][
                            "bolts"
                        ].values()
                        for name in bolt["protected_hits_mm3"]
                    ],
                    "alternate_block_screen": assembled["diagnostics"][
                        "compact_alternate_screen"
                    ].get(station),
                }
                for station, row in assembled["stations"].items()
            },
            sort_keys=True,
        )
    )
    return assembled


def test_six_source_duties_and_fixed_axes(assembly):
    report = assembly["diagnostics"]
    assert set(report["stations"]) == set(candidate.STATIONS)
    assert report["source_id"] == candidate.SOURCE_ID
    assert report["inventory"]["candidate_barrels"] == 12
    assert report["inventory"]["candidate_bolts"] == 12
    assert report["inventory"]["replaced_legacy_sds"] == 36
    assert report["inventory"]["fixed_panel_kicker_axes"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert report["approved_post_centers_x_mm"] == [-180.0, 180.0]
    assert not report["retained_pb02_return_chain"]
    assert not report["legacy_brackets_installed"]
    assert report["protected_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert not report["purchased_hillman_fit_verified"]
    assert not report["native_solve"]
    assert not report["drilling_released"]


def test_actual_intersection_and_explicit_alternate_gates(assembly):
    report = assembly["diagnostics"]
    for station in candidate.STATIONS:
        row = report["stations"][station]
        assert len(row["bolts"]) == 2
        assert row["butt_contact_area_mm2"] > 0
        for bolt in row["bolts"].values():
            assert bolt["bolt_barrel_intersection_mm3"] > 0
            assert bolt["barrel_body_cross_bore_fraction"] > 0.999
            assert bolt["thread_axis_offset_assumed_mm"] == pytest.approx(8.001)
            assert not bolt["complete_thread_engagement_verified"]
    for side in ("left", "right"):
        principal = report["stations"][f"clip_split_base_center_{side}"]
        assert principal["alternate_required"]
        assert "backer/washer tolerance" in principal["alternate_reasons"]
    assert report["decision"] == "REVISE_VIEWER_ONLY"


def test_viewer_contract_has_real_geometry_and_explicit_alternates(assembly):
    assert set(assembly["stations"]) == set(candidate.STATIONS)
    for station, row in assembly["stations"].items():
        assert row["axis_offset_mm"] == pytest.approx(8.001)
        assert len(row["bolts"]) == len(row["barrels"]) == len(row["stacks"]) == 2
        assert set(row["bolts"]) == set(row["stacks"])
        assert len(row["drilling_paths"]) == len(row["access_paths"]) == 4
        assert all(shape.Volume() > 0 for shape in row["barrels"].values())
        assert all(
            shape.Volume() > 0
            for roles in row["stacks"].values()
            for shape in roles.values()
        )
        assert row["mode"] in {"direct", "mixed"}
        if row["mode"] == "mixed":
            assert row["disposition"] == "REVISE"
            assert row["compact_alternate_block"].Volume() > 0
            assert not assembly["diagnostics"]["compact_alternate_screen"][station][
                "fastened"
            ]
        else:
            assert row["compact_alternate_block"] is None
