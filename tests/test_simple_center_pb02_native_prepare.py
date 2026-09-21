"""PB02 native preparation preserves geometry and an unsolved claim boundary."""

import math

import pytest

from scripts.simple_center_connected_kinematics import CONTACT_PARTITION
from scripts.simple_center_pb02_native import (
    PB02Native,
    native_contact_partition,
    native_row_inventory,
    prepare_case,
)

AXIAL_STIFFNESS = 700.0
LATERAL_STIFFNESS = 1200.0
FACE_STIFFNESS = 2400.0


@pytest.fixture(scope="module")
def prepared():
    return prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=AXIAL_STIFFNESS,
        bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
        face_normal_total_n_per_mm=FACE_STIFFNESS,
    )


@pytest.fixture(scope="module")
def refined_prepared():
    return prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=AXIAL_STIFFNESS,
        bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
        face_normal_total_n_per_mm=FACE_STIFFNESS,
        contact_grid_resolution=4,
    )


def test_prepare_requires_explicit_trial_stiffnesses():
    with pytest.raises(TypeError, match="required keyword-only argument"):
        prepare_case("a12-forward")


def test_prepare_rejects_unknown_case():
    with pytest.raises(ValueError, match="Unknown unchanged load case"):
        prepare_case(
            "not-a-case",
            bolt_axial_n_per_mm=AXIAL_STIFFNESS,
            bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
            face_normal_total_n_per_mm=FACE_STIFFNESS,
        )


@pytest.mark.parametrize("invalid", [0.0, -1.0, math.inf, math.nan])
@pytest.mark.parametrize(
    "field",
    [
        "bolt_axial_n_per_mm",
        "bolt_lateral_n_per_mm",
        "face_normal_total_n_per_mm",
    ],
)
def test_prepare_rejects_nonpositive_or_nonfinite_stiffness(field, invalid):
    values = {
        "bolt_axial_n_per_mm": AXIAL_STIFFNESS,
        "bolt_lateral_n_per_mm": LATERAL_STIFFNESS,
        "face_normal_total_n_per_mm": FACE_STIFFNESS,
    }
    values[field] = invalid
    with pytest.raises(ValueError, match="positive and finite"):
        prepare_case("a12-forward", **values)


def test_prepare_preserves_kerf_panel_bounds_and_all_66_fastener_axes(prepared):
    structure, metadata = prepared
    module = PB02Native()
    raw = {part.name: part.shape for part in module.uncut_wood_parts()}
    panel_names = {name for name in raw if name.startswith(("main_", "kicker_"))}

    assert set(structure.panels) == panel_names
    assert set(metadata["kerf_panel_bounds_mm"]) == panel_names
    for name, panel in structure.panels.items():
        bounds = raw[name].BoundingBox()
        xs = [structure.nodes[node][0] for node in panel["nodes"]]
        assert (min(xs), max(xs)) == pytest.approx((bounds.xmin, bounds.xmax))
        assert metadata["kerf_panel_bounds_mm"][name] == pytest.approx(
            [bounds.xmin, bounds.xmax]
        )

    panel_connections = module.panel_connections()
    assert len(panel_connections) == 66
    assert {row.name for row in panel_connections} <= set(
        metadata["connection_ownership"]
    )


def test_prepare_keeps_22_proxies_and_exact_floor_members(prepared):
    _, metadata = prepared
    module = PB02Native()

    assert metadata["legacy_proxy_stations"] == sorted(module.legacy_proxy_stations())
    assert len(metadata["legacy_proxy_stations"]) == 22
    assert metadata["extra_floor_bearing_members"] == [
        "shifted_right_post",
        "backer",
    ]
    assert metadata["pb02_rear_cleat_floor_clearance_mm"] == 5.0


def test_prepare_adds_exact_canonical_spring_inventory(prepared):
    structure, metadata = prepared
    rows = native_row_inventory()
    bolt_names = {
        row["name"].removesuffix("/tension")
        for row in rows
        if row["kind"] == "bolt_tension"
    }
    contact_names = {
        row["name"] for row in rows if row["kind"] == "contact_compression"
    }
    bolt_springs = [
        spring for spring in structure.springs if spring["name"] in bolt_names
    ]
    contact_springs = [
        spring for spring in structure.springs if spring["name"] in contact_names
    ]

    assert metadata["pb02_native_row_counts"] == {
        "bolt_shear": 20,
        "bolt_tension_only": 10,
        "contact_compression": CONTACT_PARTITION["contact_row_count"],
    }
    assert {spring["name"] for spring in bolt_springs} == bolt_names
    assert len([spring for spring in bolt_springs if spring["dof"] == 1]) == 10
    assert len([spring for spring in bolt_springs if spring["dof"] in (2, 3)]) == 20
    assert {spring["name"] for spring in contact_springs} == contact_names
    assert len(contact_springs) == CONTACT_PARTITION["contact_row_count"]

    axial = [spring for spring in bolt_springs if spring["dof"] == 1]
    lateral = [spring for spring in bolt_springs if spring["dof"] in (2, 3)]
    assert all(spring["tension_only_assumption"] for spring in axial)
    assert all(spring["bearing_closed_assumption"] for spring in axial)
    assert all(not spring.get("tension_only_assumption", False) for spring in lateral)
    assert all(
        spring["stiffness_n_per_mm"] == pytest.approx(AXIAL_STIFFNESS)
        for spring in axial
    )
    assert all(
        spring["stiffness_n_per_mm"] == pytest.approx(LATERAL_STIFFNESS)
        for spring in lateral
    )


def test_shifted_post_header_has_four_samples_and_no_backer_contact(prepared):
    structure, metadata = prepared
    summary = metadata["pb02_shifted_post_header_contacts"]
    names = set(summary["names"])
    springs = [spring for spring in structure.springs if spring["name"] in names]
    owners = metadata["connection_ownership"]

    assert summary == {
        "names": sorted(names),
        "sample_count": 4,
        "normal_xyz_into_post": [0.0, 0.0, -1.0],
        "face_normal_total_n_per_mm": FACE_STIFFNESS,
        "backer_post_contact_credited": False,
    }
    assert len(names) == len(springs) == 4
    assert sum(spring["stiffness_n_per_mm"] for spring in springs) == pytest.approx(
        FACE_STIFFNESS
    )
    assert all(
        {owners[name]["first"], owners[name]["second"]}
        == {"shifted_right_post", "base_header"}
        for name in names
    )
    assert not any(
        {owner.get("first"), owner.get("second")} == {"backer", "shifted_right_post"}
        for owner in owners.values()
    )


def test_prepare_is_explicitly_unsolved_and_never_a_release(prepared):
    _, metadata = prepared

    assert metadata["pb02_same_case_demand"] is False
    assert metadata["solved"] is False
    assert metadata["qualified_for_design"] is False
    assert metadata["actual_joint_demands_qualified"] is False
    assert metadata["acceptance"] is False
    assert metadata["drilling_released"] is False
    assert metadata["preparation_only"] is True
    assert metadata["developmental_only"] is True


def test_four_by_four_partition_prepares_with_exact_boundary_cell_coalescing(
    refined_prepared,
):
    structure, metadata = refined_prepared
    cells, partition = native_contact_partition(4)
    contact_names = {
        row["name"]
        for row in native_row_inventory(4)
        if row["kind"] == "contact_compression"
    }

    assert partition["grid_resolution"] == [4, 4]
    assert partition["contact_row_count"] == 104
    assert sum(
        row["native_attachment_coalesced_count"]
        for row in partition["interfaces"].values()
    ) == 6
    assert sum(len(rows) for rows in cells.values()) == 104
    assert metadata["pb02_contact_stiffness"]["partition_fingerprint"] == (
        partition["fingerprint"]
    )
    assert metadata["pb02_native_row_counts"]["contact_compression"] == 104
    assert contact_names <= {spring["name"] for spring in structure.springs}
