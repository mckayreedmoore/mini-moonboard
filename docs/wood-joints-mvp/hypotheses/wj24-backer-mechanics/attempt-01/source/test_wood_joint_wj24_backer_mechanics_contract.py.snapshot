from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj24_backer_mechanics_contract as contract

ROOT = Path(__file__).resolve().parents[1]


def _sha256(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _cylinder_from_inventory(row, *, length: float | None = None) -> cq.Shape:
    direction = cq.Vector(*row["axis_global_xyz"]).normalized()
    return cq.Solid.makeCylinder(
        float(row["source_occupied_diameter_mm"]) / 2.0,
        float(length if length is not None else row["shop_purchased_length_mm"]),
        cq.Vector(*row["origin_global_xyz_mm"]),
        direction,
    )


def _geometry_fixture():
    inventory = json.loads((ROOT / contract.INVENTORY_PATH).read_text())
    screw_rows = {row["axis_id"]: row for row in inventory["fixed_panel_kicker_screws"]}
    positions = {
        "left": ((-35.0, -97.0), (-35.0, -63.0)),
        "right": ((41.0, -98.0), (25.0, -76.0)),
    }
    backer_bounds = {
        "left": (-90.4875, -1.5875),
        "right": (-1.5875, 87.3125),
    }
    raw_header = cq.Solid.makeBox(
        2435.225,
        139.7,
        38.1,
        cq.Vector(-1219.2, -175.7, 238.9),
    )
    finished_header = raw_header
    for side_stations in positions.values():
        for x, y in side_stations:
            finished_header = finished_header.cut(
                cq.Solid.makeCylinder(3.65, 38.1, cq.Vector(x, y, 238.9), cq.Vector(0, 0, 1))
            )

    raw_backers = {}
    finished_backers = {}
    bores = {}
    installed = {}
    cuts_by_backer = {f"inner_kicker_backer_{side}": {} for side in ("left", "right")}
    for side, x_bounds in backer_bounds.items():
        member_id = f"inner_kicker_backer_{side}"
        raw = cq.Solid.makeBox(
            x_bounds[1] - x_bounds[0],
            88.9,
            238.9,
            cq.Vector(x_bounds[0], -124.9, 0.0),
        )
        raw_backers[member_id] = raw
        finished = raw
        for index, (x, y) in enumerate(positions[side], start=1):
            short_id = f"backer_header_{side}_{index}"
            bore = cq.Solid.makeCylinder(3.65, 277.0, cq.Vector(x, y, 0), cq.Vector(0, 0, 1))
            bores[short_id] = SimpleNamespace(
                axis_id=short_id,
                family=contract.BACKER_FAMILY,
                trial_id=contract.BACKER_TRIAL_ID,
                receiver_ids=(member_id, contract.HEADER_ID),
                station_id=f"wj05_backer_{side}",
                shape=bore,
            )
            finished = finished.cut(
                cq.Solid.makeCylinder(3.65, 231.9, cq.Vector(x, y, 7.0), cq.Vector(0, 0, 1))
            ).cut(cq.Solid.makeCylinder(10.0, 7.0, cq.Vector(x, y, 0), cq.Vector(0, 0, 1)))
            installed[short_id] = {
                role: cq.Solid.makeBox(1.0, 1.0, 1.0, cq.Vector(index * 2.0, 0, 0))
                for role in ("bottom_head", "bottom_washer", "shaft", "top_washer", "top_nut")
            }
        for index in (1, 2):
            axis_id = f"round_kicker_{side}_center_{index}"
            cutter = _cylinder_from_inventory(screw_rows[axis_id])
            cuts_by_backer[member_id][axis_id] = cutter
            finished = finished.cut(cutter)
        finished_backers[member_id] = finished

    fixed_axes = {
        row["axis_id"]: _cylinder_from_inventory(row)
        for row in inventory["fixed_panel_kicker_screws"]
    }
    source_paths = (
        contract.INVENTORY_PATH,
        "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
    )
    family_hashes = {path: _sha256(path) for path in source_paths}
    geometry = SimpleNamespace(
        layout_id=contract.LAYOUT_ID,
        trial_id=contract.COMPOSITION_TRIAL_ID,
        status="unaccepted_integrated_hypothesis",
        source_inventory_sha256=_sha256(contract.INVENTORY_PATH),
        source_inventory=inventory,
        source_inputs_sha256=family_hashes,
        family_source_fingerprints={contract.BACKER_SOURCE_BUNDLE: family_hashes},
        family_trial_ids={contract.BACKER_FAMILY: contract.BACKER_TRIAL_ID},
        raw_hosts={contract.HEADER_ID: raw_header},
        finished_hosts={contract.HEADER_ID: finished_header},
        raw_candidate_parts=raw_backers,
        finished_candidate_parts=finished_backers,
        candidate_bores=bores,
        candidate_installed_hardware=installed,
        fixed_axes=fixed_axes,
        purchased_panel_cutters_by_candidate_part=cuts_by_backer,
    )
    return geometry


def test_contract_binds_two_interfaces_four_bolts_and_four_fixed_load_entries() -> None:
    result = contract.build_mechanics_contract(_geometry_fixture())

    assert result["status"] == "bounded_mechanics_inputs_only"
    assert result["physical_inventory"]["backer_header_interfaces"] == 2
    assert result["physical_inventory"]["ordinary_physical_bolts"] == 4
    assert result["physical_inventory"]["fixed_hillman_load_entry_axes"] == 4
    assert result["physical_inventory"]["fixed_panel_axis_count_in_composition"] == 66
    assert len(result["members"]) == 3
    assert len(result["physical_interfaces"]) == 2
    assert len(result["physical_bolts"]) == 4
    assert len(result["fixed_hillman_load_entry_axes"]) == 4
    assert all(
        row["backer_to_header_contact_normal_global_xyz"] == [0.0, 0.0, 1.0]
        for row in result["physical_interfaces"]
    )
    assert all("active_contact_area_mm2" not in row for row in result["physical_interfaces"])
    assert all(row["active_contact_area_assigned"] is False for row in result["physical_interfaces"])
    assert all(
        row["grain_axis_global_xyz"] == [0.0, 0.0, 1.0]
        for member_id, row in result["members"].items()
        if member_id.startswith("inner_kicker_backer_")
    )
    assert result["members"][contract.HEADER_ID]["grain_axis_global_xyz"] == [1.0, 0.0, 0.0]
    assert all(
        row["raw_receiver_intersection_interval_mm_along_purchase_axis"]
        == pytest.approx([18.25625, 63.5])
        for row in result["fixed_hillman_load_entry_axes"]
    )
    assert all(
        row["hardware_selection"].startswith("unresolved")
        and "thread transition" in row["thread_transition_status"]
        and "unresolved" in row["stack_status"]
        for row in result["physical_bolts"]
    )
    assert all(owner["actions_by_case_id"] is None for owner in result["signed_wrench_owners"]["owners"])
    assert all(not claim for claim in result["claims"].values())


def test_contract_uses_full_backer_axis_identities_and_separate_station_aliases() -> None:
    result = contract.build_mechanics_contract(_geometry_fixture())
    physical_ids = {row["physical_bolt_id"] for row in result["physical_bolts"]}
    assert physical_ids == {
        f"{contract.BACKER_FAMILY}/{contract.BACKER_TRIAL_ID}/{axis_id}"
        for axis_id in contract.EXPECTED_BOLT_AXIS_IDS
    }
    assert {row["short_station_axis_alias"] for row in result["physical_bolts"]} == set(
        contract.EXPECTED_BOLT_AXIS_IDS
    )
    bolt_owners = [
        row for row in result["signed_wrench_owners"]["owners"] if row["owner_kind"] == "physical_bolt_axis"
    ]
    assert {row["canonical_axis_id"] for row in bolt_owners} == physical_ids
    assert all(row["datum_global_xyz_mm"] is not None for row in bolt_owners)


def test_contract_rejects_bolt_receiver_order_or_composed_axis_drift() -> None:
    geometry = _geometry_fixture()
    short_id = contract.EXPECTED_BOLT_AXIS_IDS[0]
    original = geometry.candidate_bores[short_id]
    geometry.candidate_bores[short_id] = SimpleNamespace(
        **{**vars(original), "receiver_ids": tuple(reversed(original.receiver_ids))}
    )
    with pytest.raises(ValueError, match="identity/receivers changed"):
        contract.build_mechanics_contract(geometry)

    geometry = _geometry_fixture()
    original = geometry.candidate_bores[short_id]
    geometry.candidate_bores[short_id] = SimpleNamespace(
        **{**vars(original), "shape": original.shape.translate((1.0, 0.0, 0.0))}
    )
    # Axis geometry is read from the actual composed BRep; a moved valid axis
    # cannot silently retain its old interface datum or bolt identity.
    with pytest.raises(ValueError, match="matching finished-member bore centerline"):
        contract.build_mechanics_contract(geometry)


def test_contract_rejects_missing_composed_hillman_receiver_cut() -> None:
    geometry = _geometry_fixture()
    backer_id = contract.BACKER_IDS["left"]
    raw = geometry.raw_candidate_parts[backer_id]
    finished_without_screw_cuts = raw
    for index, (x, y) in enumerate(((-35.0, -97.0), (-35.0, -63.0)), start=1):
        finished_without_screw_cuts = finished_without_screw_cuts.cut(
            cq.Solid.makeCylinder(3.65, 231.9, cq.Vector(x, y, 7.0), cq.Vector(0, 0, 1))
        ).cut(cq.Solid.makeCylinder(10.0, 7.0, cq.Vector(x, y, 0), cq.Vector(0, 0, 1)))
    geometry.finished_candidate_parts[backer_id] = finished_without_screw_cuts
    with pytest.raises(ValueError, match="retains modeled cutter overlap"):
        contract.build_mechanics_contract(geometry)
