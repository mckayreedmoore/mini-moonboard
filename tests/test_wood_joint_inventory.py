"""WJ-01 binds exact source duties, receivers, contacts, and local datums."""

import json
import math
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.wood_joint_inventory import build_inventory, validate_inventory

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "docs/wood-joints-mvp/source-inventory.json"


@pytest.fixture(scope="module")
def inventory():
    return build_inventory()


def test_exact_source_connection_inventory(inventory):
    assert inventory["candidate"] == "compact-floor-flush-wood-joints-development"
    assert inventory["source_commit"] == (
        "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
    )
    duties = inventory["legacy_duties"]
    sds = [axis for duty in duties for axis in duty["legacy_sds_axes"]]
    panels = inventory["fixed_panel_kicker_screws"]
    bolts = inventory["starting_frame_bolts"]

    assert len(duties) == len({duty["legacy_station_id"] for duty in duties}) == 24
    assert len(sds) == len({axis["axis_id"] for axis in sds}) == 144
    assert len(panels) == len({axis["axis_id"] for axis in panels}) == 66
    assert len(bolts) == len({axis["axis_id"] for axis in bolts}) == 12
    assert all(len(duty["legacy_sds_axes"]) == 6 for duty in duties)
    assert {axis["shop_purchased_length_mm"] for axis in panels} == {63.5}

    by_station = {duty["legacy_station_id"]: duty for duty in duties}
    workhorse = by_station["clip_horizontal_lower_right_1"]
    assert workhorse["legacy_host_members"] == [
        "base_rail_service_lower_right",
        "base_principal_center_right",
    ]
    assert workhorse["legacy_sds_axes"][0]["origin_global_xyz_mm"] == pytest.approx(
        [131.29274, 586.085682077917, 1222.5012367458412]
    )
    assert workhorse["replacement_owner"] is None
    assert workhorse["replacement_path_complete"] is False


def test_every_screw_has_receiver_binding_but_no_unproved_frame_path(inventory):
    screws = {row["axis_id"]: row for row in inventory["fixed_panel_kicker_screws"]}
    assert all(row["source_finished_receiver_member"] for row in screws.values())
    assert all(row["candidate_finished_receiver_member"] for row in screws.values())
    assert not any(row["receiver_to_frame_path_complete"] for row in screws.values())

    obligations = {row["side"]: row for row in inventory["receiver_obligations"]}
    assert set(obligations) == {"left", "right"}
    for side, obligation in obligations.items():
        expected_axes = {
            f"round_kicker_{side}_center_1",
            f"round_kicker_{side}_center_2",
        }
        assert set(obligation["fixed_screw_axis_ids"]) == expected_axes
        assert obligation["required_candidate_receiver_member"] == (
            f"inner_kicker_backer_{side}"
        )
        assert obligation["receiver_attachment_to_frame_status"] == "unresolved"
        assert obligation["edge_support_path_status"] == "unresolved"
        assert obligation["complete"] is False
        assert {
            screws[axis]["candidate_finished_receiver_member"] for axis in expected_axes
        } == {f"inner_kicker_backer_{side}"}


def test_transport_contacts_and_candidate_clusters_are_explicit(inventory):
    transport = inventory["transport_decomposition"]
    assert len(transport["timber"]) == 20
    assert len(transport["panels"]) == 6
    assert len(inventory["existing_contact_interfaces"]) == 6
    assert all(
        row["source_behavior"] == "compression_only_no_tangential_restraint"
        and row["new_candidate_acceptance"] is False
        for row in inventory["existing_contact_interfaces"]
    )

    clusters = {row["cluster_id"]: row for row in inventory["candidate_clusters"]}
    assert set(clusters) == {
        "outer_node_left",
        "outer_node_right",
        "ordinary_workhorse_lower_center_right",
        "center_node",
    }
    assert set(clusters["outer_node_left"]["source_host_members"]) == {
        "base_header",
        "base_post_outer_left",
        "base_side_left",
    }
    assert clusters["center_node"]["owner_starting_post_center_x_mm"] == {
        "left": -180.0,
        "right": 180.0,
    }


def test_workhorse_reports_actual_narrow_faces(inventory):
    cluster = next(
        row
        for row in inventory["candidate_clusters"]
        if row["cluster_id"] == "ordinary_workhorse_lower_center_right"
    )
    widths = cluster["source_stock_and_face_widths_mm"]
    assert widths["base_rail_service_lower_right"]["stock_section"] == pytest.approx(
        [38.1, 139.7]
    )
    assert widths["base_principal_center_right"]["stock_section"] == pytest.approx(
        [38.1, 139.7]
    )
    assert widths["base_rail_service_lower_right"][
        "rear_face_local_T_width"
    ] == pytest.approx(38.1)
    assert widths["base_principal_center_right"][
        "rear_face_local_X_width"
    ] == pytest.approx(38.1)
    assert [
        row["width_mm"] for row in inventory["two_narrowest_named_envelope_constraints"]
    ] == pytest.approx([38.1, 38.1])
    parts = {part["part_id"]: part for part in inventory["parts"]}
    for member, face_width_key in (
        ("base_rail_service_lower_right", "rear_face_local_T_width"),
        ("base_principal_center_right", "rear_face_local_X_width"),
    ):
        row = widths[member]
        faces = {face["face_id"]: face for face in parts[member]["actual_planar_faces"]}
        assert row["rear_face_id"] in faces
        assert faces[row["rear_face_id"]]["area_mm2"] > 0
        assert row[face_width_key] == pytest.approx(38.1)


def test_declared_faces_and_panel_axes_come_from_actual_shapes(inventory):
    for part in inventory["parts"]:
        assert "presented_faces" not in part
        assert part["actual_planar_faces"]
        assert all(face["area_mm2"] > 0 for face in part["actual_planar_faces"])
        if part["kind"] != "plywood_panel":
            continue
        normal = part["broad_face_normal_global_xyz"]
        first, second = part["panel_strength_axes_global_xyz"]
        dot = lambda a, b: sum(x * y for x, y in zip(a, b, strict=True))
        assert dot(normal, first) == pytest.approx(0, abs=1e-8)
        assert dot(normal, second) == pytest.approx(0, abs=1e-8)
        assert dot(first, second) == pytest.approx(0, abs=1e-8)
        if part["part_id"].startswith("kicker_"):
            assert abs(second[2]) == pytest.approx(1.0)


def test_local_transforms_are_right_handed_and_mirror_safe(inventory):
    parts = {part["part_id"]: part for part in inventory["parts"]}
    for part in parts.values():
        transform = part["local_to_global_transform"]
        basis = [
            tuple(transform[row][column] for row in range(3)) for column in range(3)
        ]
        assert all(
            math.isclose(sum(value * value for value in axis), 1.0) for axis in basis
        )
        assert all(
            math.isclose(
                sum(a * b for a, b in zip(basis[i], basis[j], strict=True)),
                0.0,
                abs_tol=1e-12,
            )
            for i in range(3)
            for j in range(i + 1, 3)
        )
        cross = (
            basis[1][1] * basis[2][2] - basis[1][2] * basis[2][1],
            basis[1][2] * basis[2][0] - basis[1][0] * basis[2][2],
            basis[1][0] * basis[2][1] - basis[1][1] * basis[2][0],
        )
        assert sum(
            a * b for a, b in zip(basis[0], cross, strict=True)
        ) == pytest.approx(1.0)

    for stem in ("base_side", "lumber_leg", "base_principal_center", "main_lower"):
        left = parts[f"{stem}_left"]
        right = parts[f"{stem}_right"]
        assert [row[:3] for row in left["local_to_global_transform"][:3]] == [
            row[:3] for row in right["local_to_global_transform"][:3]
        ]
        if left["kind"] == "timber":
            assert left["grain_axis_global_xyz"] == right["grain_axis_global_xyz"]


def test_validation_rejects_false_edge_support_completion(inventory):
    invalid = deepcopy(inventory)
    invalid["receiver_obligations"][0]["complete"] = True
    with pytest.raises(ValueError, match="edge support"):
        validate_inventory(invalid)


def test_checked_in_inventory_matches_generator(inventory):
    assert json.loads(GENERATED.read_text()) == json.loads(json.dumps(inventory))
