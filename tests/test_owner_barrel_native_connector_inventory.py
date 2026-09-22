"""Source-built connector inventory for the owner barrel viewer pose."""

from copy import copy
from dataclasses import replace

import pytest

from scripts.center_posts_outward_owner_layout import build_layout as post_layout
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_native_connector_inventory import build_inventory
from scripts.simple_owner_duty_ledger import selected_duties


@pytest.fixture(scope="module")
def sources():
    return build_viewer_assembly(), post_layout()


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
    assert set(inventory["candidate_connection_names"]) == (
        set(inventory["bolts"])
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
    assert len(shortfalls) == 12
    assert set(shortfalls) == {
        name
        for name, bolt in inventory["bolts"].items()
        if bolt["station"]
        in {
            station
            for station, duty in duties.items()
            if duty["family"] in {"bottom_outer", "lower_outer", "upper_outer"}
        }
    }
    assert all(
        value == pytest.approx(33.55125, abs=0.01) for value in shortfalls.values()
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


def test_backer_landings_and_missing_native_laws_are_explicit(inventory, sources):
    _, placement = sources
    assert set(inventory["backers"]) == {
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    }
    for name, row in inventory["backers"].items():
        assert len(row["screw_names"]) == 2
        assert row["frame_attachment_status"] == "missing"
        for screw in row["screw_names"]:
            assert placement["panel_receiver_map"][screw] == name
            assert inventory["fixed_panel_screws"][screw]["receiver"] == name
    assert set(inventory["backer_screw_landings"]) == set(
        placement["center_kicker_screws"]
    )
    assert inventory["missing_native_inputs"]["backer_frame_attachment"]
    assert inventory["missing_native_inputs"]["bolt_reach_and_engagement"]
    assert inventory["missing_native_inputs"]["contact_laws"]
    assert inventory["missing_native_inputs"]["connector_laws"]


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
