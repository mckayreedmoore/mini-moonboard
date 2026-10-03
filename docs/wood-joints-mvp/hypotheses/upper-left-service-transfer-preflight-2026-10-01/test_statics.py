"""Known-answer statics checks for the signed transfer preflight."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("transfer_preflight", Path(__file__).with_name("produce.py"))
method = importlib.util.module_from_spec(spec)
spec.loader.exec_module(method)


class KnownAnswerStatics(unittest.TestCase):
    def test_force_line_and_reporting_datum(self):
        # A 2 N y-force at x=3 has Mz=6 at x=0, and Mz=4 at x=1.
        self.assertEqual(method.shifted_moment([0, 2, 0], [0, 0, 6],
                                               [0, 0, 0], [1, 0, 0]), [0, 0, 4])

    def test_two_points_cannot_supply_pair_line_couple(self):
        # Opposite y-forces at x=+/-2 carry a 12 Nmm z-couple but no x-couple.
        moments = [method.cross([-2, 0, 0], [0, -3, 0]),
                   method.cross([2, 0, 0], [0, 3, 0])]
        self.assertEqual(method.summed(moments), [0, 0, 12])
        self.assertEqual(method.dot([1, 0, 0], method.summed(moments)), 0)
        # A normal contact force away from that line supplies the missing x-couple.
        self.assertEqual(method.cross([0, 4, 0], [0, 0, -5]), [-20, 0, 0])

    def test_rounding_bound_uses_translated_force_uncertainty(self):
        # y-force uncertainty +/-0.5 at a 3 mm x-shift adds +/-1.5 to Mz.
        self.assertEqual(method.shifted_radius([0, 0.5, 0], [0, 0, 0.2],
                                               [0, 0, 0], [3, 0, 0]), [0, 0, 1.7])

    def test_modified_source_refused_before_json_is_consumed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            path.write_text("not JSON")
            with self.assertRaisesRegex(ValueError, "Source changed"):
                method.read_pinned(path, method.REPORT_SHA)


if __name__ == "__main__":
    unittest.main()
