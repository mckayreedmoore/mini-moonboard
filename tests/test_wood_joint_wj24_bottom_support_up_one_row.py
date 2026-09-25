from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
import pytest

from scripts import wood_joint_wj24_bottom_support_up_one_row as revision

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class _PanelAxis:
    name: str
    start: cq.Vector
    members: tuple[str, str] = ("main_lower_left", "base_rail_bottom_left")


class _Source:
    def __init__(self, axes):
        self._axes = tuple(axes)

    def panel_connections(self):
        return self._axes


def test_source_bound_t_row_and_exact_changed_axis_sets():
    inventory = json.loads((ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text())
    delta = revision._translation_from_inventory(inventory)

    assert delta.toTuple() == pytest.approx((0.0, 128.557521937, 153.208888624), abs=1e-8)
    assert len(revision.PANEL_SCREW_IDS) == 4
    assert len(revision.MOVING_PART_IDS) == 4
    assert len(revision.MOVING_AXIS_IDS) == 16
    assert len(revision.MOVED_HOST_IDS) == 6
    assert revision.PANEL_SCREW_VISUAL_NAMES == {
        axis_id: f"fastener_{axis_id}" for axis_id in sorted(revision.PANEL_SCREW_IDS)
    }


def test_exactly_four_inventory_axes_move_and_all_66_ids_remain():
    inventory = json.loads((ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text())
    expected = {row["axis_id"] for row in inventory["fixed_panel_kicker_screws"]}
    ids = sorted(expected)
    axes = [_PanelAxis(axis_id, cq.Vector(float(index), 0.0, 0.0)) for index, axis_id in enumerate(ids)]
    delta = revision._translation_from_inventory(inventory)
    moved = revision._panel_connections(_Source(axes), delta, expected)
    moved_by_id = {axis.name: axis for axis in moved}

    assert set(moved_by_id) == expected
    assert sum((moved_by_id[name].start - axes[ids.index(name)].start).Length > 1e-9 for name in revision.PANEL_SCREW_IDS) == 4
    assert all(
        (moved_by_id[name].start - axes[ids.index(name)].start - delta).Length < 1e-9
        for name in revision.PANEL_SCREW_IDS
    )
    assert all(
        (moved_by_id[name].start - axes[ids.index(name)].start).Length < 1e-9
        for name in expected - revision.PANEL_SCREW_IDS
    )
