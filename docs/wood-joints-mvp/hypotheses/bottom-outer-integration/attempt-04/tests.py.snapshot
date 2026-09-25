from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_bottom_outer_integration as bottom_outer

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / bottom_outer.INVENTORY_PATH).read_text(encoding="utf-8"))


def _context_stub(variant: str) -> SimpleNamespace:
    contract = bottom_outer.CONTRACTS[variant]
    duties = bottom_outer._inventory_duties(INVENTORY)
    replaced_axes = {
        axis["axis_id"]
        for duty_id in contract.target_duty_ids
        for axis in duties[duty_id]["legacy_sds_axes"]
        if axis["shop_opening_kind"] == "sds_wood"
    }
    shape = cq.Solid.makeBox(1, 1, 1)
    family_trials = bottom_outer._expected_context_family_trials(variant)
    bore_families = bottom_outer._expected_context_bore_families(variant, contract)
    bores = {
        axis_id: SimpleNamespace(
            axis_id=axis_id,
            family=family,
            trial_id=family_trials[
                "center_x190" if family == "wj05_center_x190" else family
            ],
            receiver_ids=("receiver_a", "receiver_b"),
            shape=shape,
        )
        for axis_id, family in bore_families.items()
    }
    hardware = {
        axis_id: {
            role: shape
            for role in (
                bottom_outer.BACKER_COMPONENT_ROLES
                if axis_id in bottom_outer.BACKER_AXIS_IDS
                else bottom_outer.ORDINARY_COMPONENT_ROLES
            )
        }
        for axis_id in contract.candidate_axis_ids
    }
    overlay_ids = set(contract.additional_overlay_axis_counts)
    panel_replacements = set(bottom_outer.RIGHT_PANEL_NAMES)
    return SimpleNamespace(
        layout_id=contract.layout_id,
        trial_id=contract.trial_id,
        source_inventory=INVENTORY,
        family_trial_ids=family_trials,
        target_station_ids=contract.target_duty_ids,
        raw_hosts={name: shape for name in contract.host_ids},
        finished_hosts={name: shape for name in contract.host_ids},
        candidate_bores=bores,
        candidate_installed_hardware=hardware,
        raw_candidate_parts={name: shape for name in contract.candidate_part_ids},
        finished_candidate_parts={name: shape for name in contract.candidate_part_ids},
        replaced_source_axis_ids=frozenset(replaced_axes),
        additional_finished_source_parts={name: shape for name in overlay_ids},
        additional_purchased_panel_cutters_by_host={
            name: {f"cut_{index}": shape for index in range(count)}
            for name, count in contract.additional_overlay_axis_counts.items()
        },
        additional_source_reconstruction={name: {} for name in overlay_ids},
        panel_replacements={name: shape for name in panel_replacements},
    )


@pytest.mark.parametrize("variant", ["wj16", "wj18"])
def test_context_identity_requires_an_exact_known_layout(variant: str) -> None:
    contract = bottom_outer.validate_context_identity(
        _context_stub(variant), INVENTORY, variant
    )

    assert contract is bottom_outer.CONTRACTS[variant]


def test_context_identity_rejects_wrong_layout_variant() -> None:
    geometry = _context_stub("wj18")

    with pytest.raises(ValueError, match="pinned WJ16 layout"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj16")


def test_context_identity_rejects_wrong_candidate_bore_family_or_trial() -> None:
    geometry = _context_stub("wj18")
    axis_id = "knee_outer_left_post_1"
    bore = geometry.candidate_bores[axis_id]
    geometry.candidate_bores[axis_id] = SimpleNamespace(
        **{
            **bore.__dict__,
            "trial_id": bottom_outer.CONTRACTS["wj18"].trial_id,
        }
    )

    with pytest.raises(ValueError, match="family/trial provenance"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj18")

    geometry = _context_stub("wj18")
    bore = geometry.candidate_bores[axis_id]
    geometry.candidate_bores[axis_id] = SimpleNamespace(
        **{**bore.__dict__, "family": "wj05_backer"}
    )
    with pytest.raises(ValueError, match="family/trial provenance"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj18")


def test_context_identity_requires_exact_family_trial_map() -> None:
    geometry = _context_stub("wj18")
    geometry.family_trial_ids["wj03_outer"] = "unrecognized_trial"

    with pytest.raises(ValueError, match="exact WJ context producer map"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj18")


def test_both_context_variants_require_exactly_the_three_right_panel_overrides() -> (
    None
):
    geometry = _context_stub("wj18")
    geometry.panel_replacements = {
        name: cq.Solid.makeBox(1, 1, 1) for name in bottom_outer.PANEL_NAMES
    }

    with pytest.raises(ValueError, match="exact three-panel context map"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj18")


def test_full_context_scene_retains_six_panels_with_three_right_overrides() -> None:
    shape = cq.Solid.makeBox(1, 1, 1)
    inventory_part_ids = {row["part_id"] for row in INVENTORY["parts"]}
    non_inventory_source_parts = {
        "clip_horizontal_bottom_left_1",
        "source_screw_legacy",
    }
    source = SimpleNamespace(
        parts=lambda: [
            SimpleNamespace(name=name, shape=shape)
            for name in inventory_part_ids | non_inventory_source_parts
        ]
    )
    geometry = _context_stub("wj18")

    scene = bottom_outer._scene_from_context(geometry, source, {})

    assert set(scene) == inventory_part_ids
    assert set(bottom_outer.PANEL_NAMES) <= set(scene)
    assert not (non_inventory_source_parts & set(scene))


def test_context_identity_rejects_missing_or_extra_candidate_axis() -> None:
    geometry = _context_stub("wj18")
    missing = next(iter(geometry.candidate_bores))
    geometry.candidate_bores.pop(missing)
    geometry.candidate_bores["unexpected_axis"] = SimpleNamespace(
        axis_id="unexpected_axis"
    )

    with pytest.raises(ValueError, match="candidate axis IDs"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj18")


def test_context_identity_rejects_wrong_source_axis_removal_even_at_same_count() -> (
    None
):
    geometry = _context_stub("wj18")
    removed = set(geometry.replaced_source_axis_ids)
    removed.pop()
    removed.add("wrong_legacy_axis")
    geometry.replaced_source_axis_ids = frozenset(removed)

    with pytest.raises(ValueError, match="source-axis IDs"):
        bottom_outer.validate_context_identity(geometry, INVENTORY, "wj18")


def test_canonical_bottom_duty_inventory_is_exactly_three_axes_per_host() -> None:
    duties = bottom_outer._target_duties(INVENTORY)

    assert set(duties) == bottom_outer.TARGET_DUTY_IDS
    assert len(bottom_outer._duty_axis_ids(duties)) == 12
    for duty in duties.values():
        assert len(duty["legacy_sds_axes"]) == 6
        assert {axis["members"][1] for axis in duty["legacy_sds_axes"]} == set(
            duty["legacy_host_members"]
        )


@pytest.mark.parametrize("variant", ["wj16", "wj18"])
def test_context_candidate_axis_families_have_the_exact_pinned_census(
    variant: str,
) -> None:
    contract = bottom_outer.CONTRACTS[variant]
    families = bottom_outer._expected_context_bore_families(variant, contract)

    assert set(families) == contract.candidate_axis_ids
    assert Counter(families.values()) == Counter(
        {
            "wj03_outer": 20,
            "wj05_backer": 4,
            "wj04_g7": 8,
            "wj06_outer_pair": 8,
            "wj05_center_x190": 16,
            "left_service": 16,
            **({"top_outer": 8} if variant == "wj18" else {}),
        }
    )


def test_cleat_and_bolt_datums_use_each_actual_bottom_receiver_frame() -> None:
    datums, frames = bottom_outer.derive_candidate_datums(INVENTORY)
    left = datums["bottom_outer_left_cleat"]
    right = datums["bottom_outer_right_cleat"]

    assert left["cleat_local_intervals_mm"] == {
        "X": [0.0, 88.9],
        "T": [38.1, 127.0],
        "N": [10.0, 129.7],
    }
    assert right["cleat_local_intervals_mm"] == {
        "X": [949.175, 1038.075],
        "T": [38.1, 127.0],
        "N": [10.0, 129.7],
    }
    assert left["rail_top_face"]["normal_global_xyz"] == pytest.approx(
        [0, 0.64278761, 0.76604444]
    )
    assert left["side_inner_face"]["normal_global_xyz"] == pytest.approx([1, 0, 0])
    assert right["side_inner_face"]["normal_global_xyz"] == pytest.approx([-1, 0, 0])
    assert [row["point_local_xyz_mm"][2] for row in left["rail_bolts"]] == [
        55.45,
        84.25,
    ]
    assert [row["point_local_xyz_mm"][2] for row in right["rail_bolts"]] == [
        55.45,
        84.25,
    ]
    assert left["conditional_7D_grain_end_distance_mm"] == [45.45, 45.45]
    assert right["conditional_7D_grain_end_distance_mm"] == [45.45, 45.45]
    assert left["conditional_7D_adverse_margin_after_row_tolerance_mm"] == [
        44.95,
        44.95,
    ]
    assert right["conditional_7D_adverse_margin_after_row_tolerance_mm"] == [
        44.95,
        44.95,
    ]
    assert frames["base_rail_bottom_left"].x.toTuple() == pytest.approx((1, 0, 0))
    assert frames["base_rail_bottom_right"].x.toTuple() == pytest.approx((1, 0, 0))


def test_interface_report_labels_gross_rectangles_and_leaves_net_contact_open() -> None:
    datums, _ = bottom_outer.derive_candidate_datums(INVENTORY)

    for datum in datums.values():
        check = bottom_outer._interface_summary(datum)
        assert check["gross_candidate_face_rectangle_area_rail_mm2"] == pytest.approx(
            88.9 * 119.7
        )
        assert check["gross_candidate_face_rectangle_area_side_mm2"] == pytest.approx(
            88.9 * 119.7
        )
        assert check["finite_finished_paired_contact_area_mm2"] is None
        assert check["finite_finished_paired_contact_area_status"] == "unresolved"
        assert (
            "complete shared-host and cleat bore/cut union"
            in check["finite_finished_paired_contact_area_reason"]
        )


def test_candidate_contains_four_full_through_bolts_per_duty() -> None:
    datums, frames = bottom_outer.derive_candidate_datums(INVENTORY)
    raw_parts, stacks, bores, by_host, installed = (
        bottom_outer._build_candidate_geometry(INVENTORY, datums, frames)
    )

    assert set(raw_parts) == set(bottom_outer.CLEAT_IDS.values())
    assert len(stacks) == len(bores) == 8
    assert sum(len(roles) for roles in installed.values()) == 40
    assert {len(rows) for rows in installed.values()} == {5}
    assert {round(stack.grip_mm, 6) for stack in stacks.values()} == {127.0, 177.8}
    assert {
        axis_id
        for axis_id, bore in bores.items()
        if bore.station_id == "clip_horizontal_bottom_left_1"
    } == {
        "bottom_outer/clip_horizontal_bottom_left_1/rail_1",
        "bottom_outer/clip_horizontal_bottom_left_1/rail_2",
        "bottom_outer/clip_horizontal_bottom_left_1/side_1",
        "bottom_outer/clip_horizontal_bottom_left_1/side_2",
    }
    assert {
        axis_id
        for axis_id, bore in bores.items()
        if bore.station_id == "clip_horizontal_bottom_right_2"
    } == {
        "bottom_outer/clip_horizontal_bottom_right_2/rail_1",
        "bottom_outer/clip_horizontal_bottom_right_2/rail_2",
        "bottom_outer/clip_horizontal_bottom_right_2/side_1",
        "bottom_outer/clip_horizontal_bottom_right_2/side_2",
    }
    assert set(by_host) == bottom_outer.HOST_IDS | set(bottom_outer.CLEAT_IDS.values())
    assert all(shape.isValid() and shape.Volume() > 0 for shape in raw_parts.values())
    assert all(
        shape.isValid() and shape.Volume() > 0
        for axis in bores.values()
        for shape in [axis.shape]
    )


def test_candidate_bolt_stacks_report_only_dimensional_bounds() -> None:
    datums, frames = bottom_outer.derive_candidate_datums(INVENTORY)
    _, stacks, _, _, _ = bottom_outer._build_candidate_geometry(
        INVENTORY, datums, frames
    )
    fit = bottom_outer._fit_summary(stacks)["by_nominal_wood_grip_mm"]

    assert fit["127.0"]["nominal_bolt_length_mm"] == pytest.approx(152.4)
    assert fit["127.0"]["lower_bound_minus_nominal_wood_grip_mm"] == pytest.approx(
        22.86
    )
    assert fit["177.8"]["nominal_bolt_length_mm"] == pytest.approx(203.2)
    assert fit["177.8"]["lower_length_bound_mm"] == pytest.approx(198.628)
    assert fit["177.8"]["lower_bound_minus_nominal_wood_grip_mm"] == pytest.approx(
        20.828
    )
    assert all(not row["length_or_thread_fit_established"] for row in fit.values())
    assert all(
        not row["nominal_shank_treated_as_smooth_length"] for row in fit.values()
    )


def test_wj03_tool_metadata_uses_pinned_trial_and_frame_constants() -> None:
    hypothesis, metadata = bottom_outer._wj03_obstacle_metadata()

    assert hypothesis.id == bottom_outer.wj03_access.TRIAL_ID
    assert metadata["hypothesis_id"] == bottom_outer.wj03_access.TRIAL_ID
    assert metadata["tool_envelope_dimensions_source"] == (
        "mini_moonboard/wood_joint_frame.py"
    )
    assert metadata["tool_envelope_diameter_mm"] == pytest.approx(25.4)
    assert metadata["tool_envelope_length_mm"] == pytest.approx(50.0)
