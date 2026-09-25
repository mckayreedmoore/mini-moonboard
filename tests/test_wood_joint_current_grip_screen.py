import unittest
from types import SimpleNamespace

from scripts.wood_joint_current_grip_screen import (
    EXPECTED_SHORTENED_AXIS_IDS,
    EXPECTED_TALL_BLOCK_HEAD_MOVE_IDS,
    _direction_difference,
    _matches_partial_thread_class,
    _json_normalize,
    _perpendicular_offset_mm,
    _receiver_axis_record,
    _scope_rows,
    interval_gaps,
    load_frozen_inputs,
    merge_intervals,
    projected_solid_intervals,
)


class CurrentGripScreenIntervalTests(unittest.TestCase):
    def test_interval_union_keeps_real_projection_gaps(self):
        merged = merge_intervals(
            [[4.0, 10.0], [0.0, 4.0], [10.00000023, 14.0], [18.0, 22.0]]
        )
        self.assertEqual(merged, [[0.0, 14.0], [18.0, 22.0]])
        self.assertEqual(interval_gaps(merged), [[14.0, 18.0]])

    def test_oblique_solid_projection_is_axis_length_not_world_aabb_length(self):
        import cadquery as cq

        direction = cq.Vector(0.0, 0.6, 0.8)
        start = cq.Vector(12.0, -4.0, 30.0)
        shape = cq.Solid.makeCylinder(3.175, 25.4, start, direction)
        world = shape.BoundingBox()
        self.assertNotAlmostEqual(world.ylen, 25.4, places=6)
        self.assertNotAlmostEqual(world.zlen, 25.4, places=6)

        intervals = projected_solid_intervals(
            shape, direction.toTuple(), axis_id="oblique", label="shaft"
        )
        self.assertEqual(len(intervals), 1)
        self.assertAlmostEqual(intervals[0][1] - intervals[0][0], 25.4, places=6)

    def test_long_axis_probe_recovers_grip_beyond_a_short_modeled_shaft(self):
        import cadquery as cq

        receiver = cq.Solid.makeBox(10.0, 10.0, 10.0, cq.Vector(-5.0, -5.0, 0.0))
        short_shaft = cq.Solid.makeCylinder(3.175, 5.0, cq.Vector(0.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0))
        geometry = SimpleNamespace(raw_hosts={"member": receiver}, raw_candidate_parts={})

        row = _receiver_axis_record(
            geometry,
            "member",
            short_shaft,
            (0.0, 0.0, 1.0),
            0.0,
            6.35,
            "short-axis-test",
        )

        self.assertEqual(row["intersection_solid_intervals_from_underhead_mm"], [[0.0, 10.0]])
        self.assertEqual(row["current_shaft_intersection_solid_intervals_from_underhead_mm"], [[0.0, 5.0]])
        self.assertFalse(row["current_shaft_covers_long_axis_raw_receiver_projection"])
        self.assertGreater(row["long_probe_minus_current_shaft_volume_mm3"], 0.0)
        self.assertFalse(row["current_shaft_volume_covers_long_probe_intersection"])

    def test_axis_direction_check_compares_all_three_components(self):
        self.assertLess(_direction_difference((0.0, 0.6, 0.8), (0.0, 0.6, 0.8)), 1e-12)
        self.assertGreater(_direction_difference((0.0, 0.6, 0.8), (0.0, 0.8, 0.6)), 0.2)

    def test_axis_line_offset_ignores_along_axis_distance(self):
        direction = (0.0, 0.6, 0.8)
        line_point = (4.0, -2.0, 7.0)
        along = (4.0, 4.0, 15.0)
        shifted = (4.0, 4.00016, 14.99988)
        self.assertAlmostEqual(
            _perpendicular_offset_mm(along, line_point, direction), 0.0, places=12
        )
        self.assertAlmostEqual(
            _perpendicular_offset_mm(shifted, line_point, direction), 0.0002, places=9
        )

    def test_only_exact_existing_partial_thread_length_classes_are_compared(self):
        six_inch = _matches_partial_thread_class(152.4)
        self.assertEqual(
            six_inch["status"],
            "existing_dimensional_class_matches_modeled_underhead_to_tip",
        )
        self.assertEqual(six_inch["Lb_min_mm"], 127.0)
        self.assertEqual(six_inch["Lg_max_mm"], 133.35)
        self.assertEqual(
            _matches_partial_thread_class(152.401)["status"],
            "no_existing_exact_length_class_applied",
        )


class CurrentGripScreenSourceTests(unittest.TestCase):
    def test_frozen_scope_names_eight_shortened_and_eight_head_moved_axes(self):
        snapshot, report = load_frozen_inputs()
        priority = _scope_rows(snapshot, report)

        self.assertEqual(set(priority["shortened_exterior_axis_ids"]), EXPECTED_SHORTENED_AXIS_IDS)
        self.assertEqual(set(priority["tall_block_head_move_axis_ids"]), EXPECTED_TALL_BLOCK_HEAD_MOVE_IDS)
        self.assertEqual(len(snapshot["axes"]), 92)
        self.assertTrue(set(priority["shortened_exterior_axis_ids"]).isdisjoint(
            priority["tall_block_head_move_axis_ids"]
        ))

    def test_live_tuple_rows_normalize_to_the_frozen_json_report(self):
        _, report = load_frozen_inputs()
        live = dict(report)
        live["reseated_candidate_axis_ids"] = tuple(report["reseated_candidate_axis_ids"])
        live["moved_candidate_axis_ids"] = tuple(report["moved_candidate_axis_ids"])

        self.assertEqual(_json_normalize(live), report)


if __name__ == "__main__":
    unittest.main()
