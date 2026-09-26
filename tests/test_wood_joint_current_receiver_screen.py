import copy
import json
import math
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

from scripts.wood_joint_current_receiver_screen import (
    EXPECTED_KICKER_CENTER_RECEIVERS,
    EXPECTED_MOVED_AXIS_IDS,
    _validate_current_axis_shape,
    build_current_panel_axis_map,
)

ROOT = Path(__file__).resolve().parents[1]


class _Vector:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)

    @property
    def Length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return _Vector(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def normalized(self):
        scale = self.Length
        return _Vector(self.x / scale, self.y / scale, self.z / scale)


class _Box:
    def __init__(self, values):
        self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax = values
        self.xlen = self.xmax - self.xmin
        self.ylen = self.ymax - self.ymin
        self.zlen = self.zmax - self.zmin


class _AxisShape:
    def __init__(self, bounds):
        self.bounds = bounds

    def BoundingBox(self):
        return _Box(self.bounds)


class CurrentReceiverAxisMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(
            (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
        )
        cls.report = json.loads(
            (ROOT / "site/owner-wood-joints-review-report.json").read_text()
        )

    def test_current_map_reconciles_58_retained_and_8_moved_axes(self):
        rows = build_current_panel_axis_map(self.inventory, self.report)
        by_id = {row["axis_id"]: row for row in rows}

        self.assertEqual(len(rows), 66)
        self.assertEqual(
            {row["axis_id"] for row in rows if row["current_location_status"] == "moved"},
            EXPECTED_MOVED_AXIS_IDS,
        )
        self.assertEqual(
            sum(row["current_location_status"] == "source_station_retained" for row in rows),
            58,
        )
        self.assertEqual(
            {
                axis_id: by_id[axis_id]["receiver_member"]
                for axis_id in EXPECTED_KICKER_CENTER_RECEIVERS
            },
            EXPECTED_KICKER_CENTER_RECEIVERS,
        )

    def test_moved_axes_use_current_report_coordinates_and_preserve_direction(self):
        rows = build_current_panel_axis_map(self.inventory, self.report)
        by_id = {row["axis_id"]: row for row in rows}
        moved = {row["axis_id"]: row for row in self.report["moved_panel_axes"]}

        for axis_id in EXPECTED_MOVED_AXIS_IDS:
            self.assertEqual(
                by_id[axis_id]["origin_global_xyz_mm"],
                moved[axis_id]["new_start_global_xyz_mm"],
            )
            self.assertEqual(
                by_id[axis_id]["axis_global_xyz"],
                moved[axis_id]["axis_global_xyz_unchanged"],
            )

    def test_moved_axis_record_must_match_source_origin_translation_and_direction(self):
        moved_axis_id = min(EXPECTED_MOVED_AXIS_IDS)

        stale_old_start = copy.deepcopy(self.report)
        stale_old_start["moved_panel_axes"][0]["old_start_global_xyz_mm"][0] += 0.01
        with self.assertRaisesRegex(ValueError, "old start differs from source origin"):
            build_current_panel_axis_map(self.inventory, stale_old_start)

        incorrect_translation = copy.deepcopy(self.report)
        translation_row = next(
            row for row in incorrect_translation["moved_panel_axes"]
            if row["axis_id"] == moved_axis_id
        )
        translation_row["translation_global_xyz_mm"][1] += 0.01
        with self.assertRaisesRegex(ValueError, "old start plus translation"):
            build_current_panel_axis_map(self.inventory, incorrect_translation)

        changed_direction = copy.deepcopy(self.report)
        direction_row = next(
            row for row in changed_direction["moved_panel_axes"]
            if row["axis_id"] == moved_axis_id
        )
        direction_row["axis_global_xyz_unchanged"][1] *= -1
        with self.assertRaisesRegex(ValueError, "differs from source direction"):
            build_current_panel_axis_map(self.inventory, changed_direction)

    def test_map_rejects_a_stale_revision_or_missing_move(self):
        stale = dict(self.report, revision_id="historical-receiver-audit")
        with self.assertRaisesRegex(ValueError, "expected report"):
            build_current_panel_axis_map(self.inventory, stale)

        missing_move = dict(
            self.report,
            moved_panel_axes=self.report["moved_panel_axes"][:-1],
        )
        with self.assertRaisesRegex(ValueError, "moved-axis set"):
            build_current_panel_axis_map(self.inventory, missing_move)

    def test_current_cad_axis_check_rejects_a_stale_or_double_moved_shape(self):
        fake_cadquery = types.SimpleNamespace(Vector=_Vector)
        row = {
            "axis_id": "example_moved_axis",
            "origin_global_xyz_mm": [100.0, 20.0, 30.0],
            "axis_global_xyz": [1.0, 0.0, 0.0],
        }
        current = _AxisShape([100.0, 163.5, 17.93, 22.07, 27.93, 32.07])
        stale = _AxisShape([100.0, 163.5, 109.64, 113.78, 27.93, 32.07])

        with mock.patch.dict(sys.modules, {"cadquery": fake_cadquery}):
            evidence = _validate_current_axis_shape(current, row)
            self.assertEqual(evidence["axial_bounds_from_reported_origin_mm"], [0.0, 63.5])
            with self.assertRaisesRegex(ValueError, "stale or double-moved"):
                _validate_current_axis_shape(stale, row)


if __name__ == "__main__":
    unittest.main()
