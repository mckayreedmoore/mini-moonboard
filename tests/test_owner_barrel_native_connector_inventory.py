"""Source-built connector inventory for the owner barrel viewer pose."""

from copy import copy
from dataclasses import replace

import pytest

from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_native_connector_inventory as native_inventory
from scripts import owner_barrel_outer_top_layout as outer
from scripts import owner_barrel_rail_layout as rail
from scripts.center_posts_outward_owner_layout import build_layout as post_layout
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_layout_assembly import build_assembly
from scripts.owner_barrel_native_connector_inventory import build_inventory
from scripts.simple_owner_duty_ledger import selected_duties


@pytest.fixture(scope="module")
def sources():
    return build_viewer_assembly(), post_layout()


@pytest.fixture(scope="module")
def original_sources():
    return build_assembly(
        producers={
            "rail10": rail.build_revised_layout,
            "center6": center.build_revised_layout,
            "outer_top8": outer.build_recessed_viewer_layout,
        },
        post_placement="original",
    )


@pytest.fixture(scope="module")
def inventory(sources):
    return build_inventory(assembly=sources[0], placement=sources[1])


def test_current_viewer_connector_inventory_is_complete_and_source_bound(
    inventory, sources
):
    assembly, _ = sources
    duties = selected_duties()
    assert inventory["schema"] == "owner_barrel_native_connector_inventory/v1"
    assert inventory["viewer_pose"]["outer_header_forward_y_mm"] == -85.0
    assert inventory["viewer_pose"]["post_placement"] == "outward"
    assert inventory["native_ready"] is False
    assert inventory["native_solve"] is False
    assert inventory["capacities_claimed"] is False
    assert inventory["release_claimed"] is False
    assert set(inventory["stations"]) == set(duties)
    assert len(inventory["bolts"]) == len(inventory["barrels"]) == 48
    assert all(
        len(row["bolt_names"]) == len(row["barrel_names"]) == 2
        for row in inventory["stations"].values()
    )
    assert set(inventory["bolts"]) == set(assembly["bolts"])
    assert set(inventory["barrels"]) == set(assembly["barrels"])
    assert len(inventory["fixed_panel_screws"]) == 66
    assert len(inventory["retained_frame_bolts"]) == 12
    assert len(inventory["backer_attachment_bolts"]) == 4
    assert set(inventory["candidate_connection_names"]) == (
        set(inventory["bolts"])
        | set(inventory["backer_attachment_bolts"])
        | set(inventory["fixed_panel_screws"])
        | set(inventory["retained_frame_bolts"])
    )
    excluded = inventory["excluded_legacy"]
    assert set(excluded["angle_stations"]) == set(duties)
    assert set(excluded["sds_axes"]) == {
        name for duty in duties.values() for name in duty["sds_axes"]
    }
    assert not set(inventory["candidate_connection_names"]) & set(excluded["sds_axes"])
    assert inventory["source_sha256"]
    assert len(inventory["inventory_fingerprint_sha256"]) == 64
    shortfalls = inventory["modeled_shaft_reach_shortfalls_mm"]
    assert shortfalls == {}
    assert (
        sum(
            abs(bolt["length_mm"] - 152.4) < 1e-6
            for bolt in inventory["bolts"].values()
        )
        == 12
    )
    for name, bolt in inventory["bolts"].items():
        assert bolt["barrel_name"] == name.removesuffix("_bolt")
        assert bolt["barrel_name"] in inventory["barrels"]
        assert (
            bolt["provisional_thread_axis_point_mm"]
            == inventory["barrels"][bolt["barrel_name"]][
                "provisional_thread_axis_point_mm"
            ]
        )
        assert bolt["station"] == inventory["barrels"][bolt["barrel_name"]]["station"]
        barrel = inventory["barrels"][bolt["barrel_name"]]
        members = set(inventory["stations"][bolt["station"]]["timber_members"])
        assert {bolt["entry_member"], barrel["receiving_member"]} == members
        assert bolt["entry_member"] != barrel["receiving_member"]
        assert bolt["modeled_shaft_shortfall_mm"] == pytest.approx(
            max(
                0.0,
                bolt["provisional_axis_point_from_bolt_start_mm"] - bolt["length_mm"],
            )
        )
        body = assembly["barrels"][bolt["barrel_name"]]
        assert body.intersect(
            assembly["wood"][barrel["receiving_member"]]
        ).Volume() == pytest.approx(body.Volume(), rel=1e-2)
        assert (
            body.intersect(assembly["wood"][bolt["entry_member"]]).Volume()
            < 1e-5 * body.Volume()
        )


def test_original_center_screws_land_in_posts_without_backer_duties(original_sources):
    assembly = original_sources
    inventory = build_inventory(assembly=assembly)
    assert inventory["viewer_pose"]["post_placement"] == "original"
    assert len(inventory["candidate_connection_names"]) == 126
    assert inventory["backer_attachment_bolts"] == {}
    assert inventory["backers"] == {}
    assert inventory["backer_screw_landings"] == {}
    assert "backer_frame_attachment" not in inventory["missing_native_inputs"]
    landings = inventory["center_kicker_screw_landings"]
    assert len(landings) == 4
    for name, row in landings.items():
        source = next(
            item for item in assembly["panel_connections"] if item.name == name
        )
        assert row["receiver"] == source.members[1]
        assert row["receiver"] in {"base_post_center_left", "base_post_center_right"}
        assert inventory["fixed_panel_screws"][name]["receiver"] == row["receiver"]
    assert inventory["missing_native_inputs"]["bolt_reach_and_engagement"]
    assert inventory["missing_native_inputs"]["contact_laws"]
    assert inventory["missing_native_inputs"]["connector_laws"]


def test_active_backer_duties_and_unqualified_laws_are_explicit(inventory, sources):
    assembly, placement = sources
    assert inventory["viewer_pose"]["post_placement"] == "outward"
    assert set(assembly["backer_attachment"]["stations"]) == {
        "backer_attachment_left",
        "backer_attachment_right",
    }
    assert len(inventory["backer_attachment_bolts"]) == 4
    assert len(inventory["backers"]) == 2
    assert len(inventory["backer_screw_landings"]) == 4
    assert len(inventory["candidate_connection_names"]) == 130
    assert inventory["missing_native_inputs"]["backer_frame_attachment"]
    for name, row in inventory["backers"].items():
        assert len(row["screw_names"]) == 2
        assert row["frame_attachment_status"] == "nominal_geometry_defined_unqualified"
        assert len(row["frame_attachment_connections"]) == 2
        assert all(
            inventory["fixed_panel_screws"][screw]["receiver"] == name
            for screw in row["screw_names"]
        )
        assert all(
            placement["panel_receiver_map"][screw] == name
            for screw in row["screw_names"]
        )


def test_default_inventory_uses_active_outward_viewer():
    row = build_inventory()
    assert row["viewer_pose"]["post_placement"] == "outward"
    assert len(row["backer_attachment_bolts"]) == 4
    assert len(row["candidate_connection_names"]) == 130


def test_default_rejects_detached_original_trial(original_sources, monkeypatch):
    monkeypatch.setattr(
        native_inventory, "build_viewer_assembly", lambda: original_sources
    )
    with pytest.raises(ValueError, match="Default inventory"):
        build_inventory()


def test_inventory_rejects_missing_barrel_and_changed_viewer_pose(sources):
    assembly, placement = sources
    missing = {**assembly, "barrels": copy(assembly["barrels"])}
    missing["barrels"].pop(next(iter(missing["barrels"])))
    with pytest.raises(ValueError, match="barrel"):
        build_inventory(assembly=missing, placement=placement)

    moved = {**assembly, "diagnostics": copy(assembly["diagnostics"])}
    moved["diagnostics"]["producer_diagnostics"] = copy(
        assembly["diagnostics"]["producer_diagnostics"]
    )
    moved["diagnostics"]["producer_diagnostics"]["outer_top8"] = {
        **moved["diagnostics"]["producer_diagnostics"]["outer_top8"],
        "viewer_trial_outer_header_forward_y_mm": -75.0,
    }
    with pytest.raises(ValueError, match="-85"):
        build_inventory(assembly=moved, placement=placement)

    mixed = {
        **assembly,
        "wood": {
            name: shape
            for name, shape in assembly["wood"].items()
            if name != "inner_kicker_backer_left"
        },
    }
    with pytest.raises(ValueError, match="viewer pose"):
        build_inventory(assembly=mixed)


def test_original_trial_rejects_shifted_placement(original_sources):
    with pytest.raises(ValueError, match="Original center posts"):
        build_inventory(assembly=original_sources, placement=post_layout())


def test_host_ownership_uses_solids_not_connection_member_order(sources, inventory):
    assembly, placement = sources
    name = next(iter(assembly["bolts"]))
    original = assembly["bolts"][name]
    reversed_members = {
        **assembly,
        "bolts": {
            **assembly["bolts"],
            name: replace(original, members=original.members[::-1]),
        },
    }
    record = build_inventory(assembly=reversed_members, placement=placement)["bolts"][
        name
    ]
    assert record["entry_member"] == inventory["bolts"][name]["entry_member"]
    assert record["receiving_member"] == inventory["bolts"][name]["receiving_member"]
    assert record["receiver"] == inventory["bolts"][name]["receiver"]

    ambiguous = {**assembly, "wood": copy(assembly["wood"])}
    entry, receiver = record["entry_member"], record["receiving_member"]
    ambiguous["wood"][receiver] = ambiguous["wood"][entry]
    with pytest.raises(ValueError, match="receiving wood is ambiguous"):
        build_inventory(assembly=ambiguous, placement=placement)
