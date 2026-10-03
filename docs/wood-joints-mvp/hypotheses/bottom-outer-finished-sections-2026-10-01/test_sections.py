"""Small source-contract and known-answer checks, independent of raw case files."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


producer = load(HERE / "produce.py", "bottom_finished_sections_test")
host = load(producer.HOST_METHOD, "bottom_point_action_method_test")
section = load(producer.SECTION_METHOD, "bottom_section_geometry_method_test")


def fixture():
    frames = {
        member: {
            "host": member,
            "member_start_xyz_mm": [0.0, 0.0, 0.0],
            "member_grain_length_mm": 100.0,
            "grain_axis_global_xyz": [1.0, 0.0, 0.0],
            "section_u_global_xyz": [0.0, 1.0, 0.0],
            "section_v_global_xyz": [0.0, 0.0, 1.0],
        }
        for member in producer.MEMBERS
    }
    axes = {}
    for role in ("rail", "side"):
        for i in (1, 2):
            identity = f"{producer.PREFIX}{role}_{i}"
            memberships = []
            for member in sorted(producer.RECEIVERS[role]):
                feature_id = f"{member}/{role}_{i}"
                station = (
                    (10.0 * i if role == "rail" else 15.0)
                    if member == producer.CLEAT
                    else (30.0 if role == "rail" else 30.0 + 10.0 * i)
                )
                memberships.append(
                    {
                        "receiver_member_id": member,
                        "match_status": "matched_bore_patch",
                        "matched_feature_ids": [feature_id],
                        "cylinder_surface_candidates": [
                            {
                                "feature_id": feature_id,
                                "association_status": "eligible_bore_patch",
                                "patch_interval_projected_from_axis_datum_mm": [
                                    station - 1.0,
                                    station + 1.0,
                                ],
                                "cylinder_radius_mm": 3.75,
                            }
                        ],
                    }
                )
            axes[identity] = {
                "receiver_memberships": memberships,
                "source_axis_fields": {
                    "occupied_diameter_mm": 6.35,
                    "datum_global_xyz_mm": [0.0, 0.0, 0.0],
                    "direction_global_xyz": [1.0, 0.0, 0.0],
                },
            }
    return axes, frames


def test_six_planes_preserve_all_eight_bore_identities():
    axes, frames = fixture()
    planes = producer.plan_planes(host, axes, frames)
    assert len(planes) == 6
    assert sorted(len(p["axis_memberships"]) for p in planes) == [1, 1, 1, 1, 2, 2]
    assert {p["member_id"] for p in planes} == producer.MEMBERS
    assert sorted((p["member_id"], p["cut_station_mm"]) for p in planes) == sorted(
        [
            (producer.CLEAT, 10),
            (producer.CLEAT, 15),
            (producer.CLEAT, 20),
            (producer.RAIL, 30),
            (producer.SIDE, 40),
            (producer.SIDE, 50),
        ]
    )
    assert {
        a["axis_id"] for p in planes for a in p["axis_memberships"]
    } == producer.AXES


@pytest.mark.parametrize(
    "corruption",
    [
        "foreign_receiver",
        "duplicate_receiver",
        "ambiguous_feature",
        "duplicate_patch",
        "wrong_radius",
        "reversed_interval",
        "outside_plane",
        "nonfinite_interval",
        "nonunit_direction",
        "wrong_occupied_diameter",
    ],
)
def test_corrupted_bore_contract_is_rejected(corruption):
    axes, frames = fixture()
    axis = axes[f"{producer.PREFIX}rail_1"]
    receiver = axis["receiver_memberships"][0]
    patch = receiver["cylinder_surface_candidates"][0]
    if corruption == "foreign_receiver":
        receiver["receiver_member_id"] = "unowned_member"
    elif corruption == "duplicate_receiver":
        axis["receiver_memberships"][1] = copy.deepcopy(receiver)
    elif corruption == "ambiguous_feature":
        receiver["matched_feature_ids"].append("another_patch")
    elif corruption == "duplicate_patch":
        receiver["cylinder_surface_candidates"].append(copy.deepcopy(patch))
    elif corruption == "wrong_radius":
        patch["cylinder_radius_mm"] = 3.8
    elif corruption == "reversed_interval":
        patch["patch_interval_projected_from_axis_datum_mm"] = [2, 1]
    elif corruption == "outside_plane":
        patch["patch_interval_projected_from_axis_datum_mm"] = [101, 103]
    elif corruption == "nonfinite_interval":
        patch["patch_interval_projected_from_axis_datum_mm"] = [1, float("nan")]
    elif corruption == "nonunit_direction":
        axis["source_axis_fields"]["direction_global_xyz"] = [2, 0, 0]
    else:
        axis["source_axis_fields"]["occupied_diameter_mm"] = 7.5
    with pytest.raises(ValueError):
        producer.plan_planes(host, axes, frames)


def test_missing_axis_is_rejected():
    axes, frames = fixture()
    axes.pop(next(iter(axes)))
    with pytest.raises(ValueError, match="four bottom axes"):
        producer.plan_planes(host, axes, frames)


def test_changed_source_bytes_are_rejected(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    source.write_text('{"source": 1}')
    monkeypatch.setattr(producer, "PINS", {"fixture": (source, producer.sha(source))})
    producer.verify_sources()
    source.write_text('{"source": 2}')
    with pytest.raises(ValueError, match="source pin changed"):
        producer.verify_sources()


def test_complete_point_action_jump_and_centroid_transport_known_answer():
    _, frames = fixture()
    frame = frames[producer.CLEAT]
    actions = [
        {
            "source_name": f"point-{x}",
            "source_kind": "physical_connection",
            "grain_station_mm": float(x),
            "point_xyz_mm": [float(x), 0.0, 0.0],
            "force_xyz_n": [0.0, float(y_force), 0.0],
            "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
        }
        for x, y_force in ((0, 1), (10, -2), (20, 1))
    ]
    body = {**host.wrench(actions, [0.0, 0.0, 0.0]), "_datum_xyz_mm": [0.0, 0.0, 0.0]}
    left = host.cut_trace(actions, 10, frame, "approached_from_negative_station", body)
    right = host.cut_trace(actions, 10, frame, "approached_from_positive_station", body)
    before = left["internal_cut_wrench_on_positive_side_material"]
    after = right["internal_cut_wrench_on_positive_side_material"]
    assert before["force_xyz_n"] == [0, 1, 0]
    assert after["force_xyz_n"] == [0, -1, 0]
    assert (
        before["moment_about_datum_xyz_nmm"]
        == after["moment_about_datum_xyz_nmm"]
        == [0, 0, -10]
    )
    shifted = host.transport_wrench(before, [10, 0, 0], [10, 0, 2])
    assert shifted["moment_about_datum_xyz_nmm"] == [2, 0, -10]
    assert host.local_wrench(shifted, frame)["moment_T_Mu_Mv_nmm"] == {
        "T": 2,
        "Mu": 0,
        "Mv": -10,
    }


def test_contact_footprint_crossing_is_distinct_from_point_trace():
    actions = [
        {
            "source_name": "crosses",
            "contact_patch": {},
            "finite_footprint_station_bounds_mm": [0, 20],
        },
        {
            "source_name": "touches",
            "contact_patch": {},
            "finite_footprint_station_bounds_mm": [10, 20],
        },
        {
            "source_name": "bolt",
            "contact_patch": None,
            "finite_footprint_station_bounds_mm": [10, 10],
        },
    ]
    assert producer.crossing_contacts(actions, 10, host.STATION_BAND_MM) == ["crosses"]


def test_rectangle_minus_transverse_slot_retains_geometry_only_limits():
    import cadquery as cq

    stock = cq.Solid.makeBox(100, 40, 20)
    bore = cq.Solid.makeCylinder(3.75, 40, cq.Vector(50, 0, 10), cq.Vector(0, 1, 0))
    shape = stock.cut(bore)
    _, frames = fixture()
    frame = frames[producer.CLEAT]
    plane = {"plane_origin_xyz_mm": [50, 0, 0]}
    result = producer.section_at_plane(section, shape, plane, frame)
    assert result["area_mm2"] == pytest.approx(40 * (20 - 7.5), abs=1e-5)
    assert result["component_count"] == 2
    assert result["centroid_global_xyz_mm"] == pytest.approx([50, 20, 10], abs=1e-6)
    for key in (
        "common_strain_or_component_load_sharing_established",
        "actual_integrated_traction_established",
        "section_resistance_accepted",
    ):
        assert result[key] is False
