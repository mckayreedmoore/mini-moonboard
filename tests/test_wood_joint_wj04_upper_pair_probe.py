"""Focused no-report tests for the paired WJ-04 full-stock hypothesis."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_upper_pair_probe as probe


def test_pair_plan_binds_axes_preserves_fixed_duties_and_stays_unaccepted():
    canonical_sha = WJ04_TRIAL.canonical_sha256
    plan = probe.trial_plan()

    assert plan["pair_spacing"]["nominal_clear_gap_mm"] == pytest.approx(55.15)
    assert len(plan["stacks"]) == 8
    assert plan["claim_boundary"]["former_sds_axis_count"] == 12
    assert plan["fixed_obligations"] == {
        "panel_kicker_screw_axes": 66,
        "starting_frame_bolts": 12,
        "preservation_required": True,
        "cad_environment_materialized": False,
    }
    assert plan["claim_boundary"]["accepted_replacement_count"] == 0
    assert plan["claim_boundary"]["physical_replacement_accepted"] is False
    assert plan["claim_boundary"]["structural_accepted"] is False
    assert plan["claim_boundary"]["drilling_released"] is False
    assert plan["candidate_panel_overlay"]["planned_for_local_geometry_map"] is True
    assert plan["candidate_panel_overlay"]["applied_to_local_geometry_map"] is False
    assert plan["candidate_panel_overlay"]["raw_source_binding_mutated"] is False
    assert WJ04_TRIAL.canonical_sha256 == canonical_sha

    upper_beams = plan["stations"][probe.UPPER_STATION]["replaced_source_sds_axes"]
    beam_rows = [row for row in upper_beams if "_beam_" in row["axis_id"]]
    expected_beam_origins = (
        (131.29274, 1500.479374, 260.640968),
        (124.94274, 1500.479374, 298.740968),
        (131.29274, 1500.479374, 336.840968),
    )
    for row, expected in zip(beam_rows, expected_beam_origins, strict=True):
        assert row["origin_x_t_n_mm"] == pytest.approx(expected)
    assert all(
        row["direction_x_t_n"] == pytest.approx([0.0, -1.0, 0.0]) for row in beam_rows
    )

    upper_rail = [
        row for row in plan["stacks"] if row["stack_id"].startswith("upper_rail")
    ]
    assert [row["axis_point_basis_mm"] for row in upper_rail] == [
        [134.5, 1586.824134, 273.190968],
        [134.5, 1586.824134, 306.190968],
    ]
    assert all(row["axis_direction_basis"] == [0.0, -1.0, 0.0] for row in upper_rail)


def test_stack_builder_fails_closed_on_duplicate_missing_or_altered_assignment():
    specs = probe.STACK_SPECS
    duplicate = (*specs[:-1], specs[0])
    with pytest.raises(ValueError, match="eight unique stacks"):
        probe.build_stacks(duplicate)
    with pytest.raises(ValueError, match="eight unique stacks"):
        probe.build_stacks(specs[:-1])

    altered = replace(
        specs[0],
        layers=(
            (specs[0].cleat_id, 88.9),
            ("base_rail_service_lower_right", 39.1),
        ),
    )
    with pytest.raises(ValueError, match=r"88.9 \+ 38.1 mm wood layers"):
        probe.build_stacks((altered, *specs[1:]))

    shifted = replace(
        specs[0],
        axis_point_basis_mm=(
            specs[0].axis_point_basis_mm[0] + 1,
            *specs[0].axis_point_basis_mm[1:],
        ),
    )
    with pytest.raises(ValueError, match="axis or member mapping differs"):
        probe.build_stacks((shifted, *specs[1:]))


class _Connection:
    def __init__(self, name, members, start, direction, length, diameter, kind="sds"):
        self.name = name
        self.members = members
        self.start = start
        self.direction = direction.normalized()
        self.length = length
        self.diameter = diameter
        self.kind = kind


def _host(name, shape):
    return SimpleNamespace(name=name, shape=shape)


class _TinySource:
    def __init__(self, raw, finished, connections):
        self._raw = raw
        self._finished = finished
        self._connections = connections

    def uncut_wood_parts(self):
        return [_host(name, shape) for name, shape in self._raw.items()]

    def parts(self):
        return [_host(name, shape) for name, shape in self._finished.items()]

    def connections(self):
        return tuple(self._connections)

    def bolt_dimensions(self, _connection):
        return {"hole_diameter_mm": 6.35}

    def service_cutters(self):
        return ()

    def additional_machining_cutters(self):
        return ()


def test_host_rebuild_restores_selected_sds_and_reapplies_crossing_retained_axis():
    host_ids = (
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
        "base_principal_center_right",
    )
    raw = {name: cq.Solid.makeBox(30, 30, 30) for name in host_ids}
    selected = _Connection(
        "selected_sds",
        ("base_principal_center_right",),
        cq.Vector(0, 15, 15),
        cq.Vector(1, 0, 0),
        30,
        4,
    )
    retained = _Connection(
        "retained_axis",
        ("base_principal_center_right",),
        cq.Vector(15, 0, 15),
        cq.Vector(0, 1, 0),
        30,
        2,
    )
    source_finished = dict(raw)
    source_finished["base_principal_center_right"] = (
        raw["base_principal_center_right"]
        .cut(
            cq.Solid.makeCylinder(2, 32, cq.Vector(-1, 15, 15), cq.Vector(1, 0, 0)),
            cq.Solid.makeCylinder(1, 32, cq.Vector(15, -1, 15), cq.Vector(0, 1, 0)),
        )
        .clean()
    )
    source = _TinySource(raw, source_finished, (selected, retained))
    inventory = {
        "legacy_duties": [
            {
                "legacy_sds_axes": [
                    {"axis_id": "selected_sds", "shop_opening_kind": "sds_wood"}
                ]
            }
        ],
        "fixed_panel_kicker_screws": [],
    }

    rebuilt = probe._rebuild_hosts_with_removed_stations(
        source, inventory, {"selected_sds"}
    )
    expected = (
        raw["base_principal_center_right"]
        .cut(cq.Solid.makeCylinder(1, 32, cq.Vector(15, -1, 15), cq.Vector(0, 1, 0)))
        .clean()
    )

    assert rebuilt["base_principal_center_right"].Volume() == pytest.approx(
        expected.Volume(), abs=1e-5
    )
    assert rebuilt["base_rail_service_lower_right"].Volume() == pytest.approx(
        raw["base_rail_service_lower_right"].Volume()
    )
    assert rebuilt["base_rail_service_upper_right"].Volume() == pytest.approx(
        raw["base_rail_service_upper_right"].Volume()
    )

    inventory["legacy_duties"][0]["legacy_sds_axes"][0]["shop_opening_kind"] = "bolt"
    with pytest.raises(ValueError, match="only selected former SDS openings"):
        probe._rebuild_hosts_with_removed_stations(source, inventory, {"selected_sds"})
