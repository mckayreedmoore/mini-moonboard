#!/usr/bin/env python3
"""Focused guard test: a wrong master surface must invalidate deck order."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "audit_terminal_contact.py"
SPEC = importlib.util.spec_from_file_location("audit_terminal_contact", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class HeaderOnlyHelper:
    REPORT_START = AUDIT.STAT_RE
    LABELS: tuple[str, ...] = ()

    @staticmethod
    def parse_record(*_args):
        raise ValueError("intentional header-only test fixture")


def report_record(slave_index: int, master_index: int) -> dict:
    header = (
        f"statistics for slave set WJCP_{slave_index:03d}_S, "
        f"master set WJCP_{master_index:03d}_M and time 0.001\n"
    )
    return AUDIT.parse_complete_or_partial_report([header], HeaderOnlyHelper, 1)


class ContactOutputOrderTest(unittest.TestCase):
    def test_mismatched_master_is_rejected(self):
        record = report_record(1, 2)
        self.assertFalse(record["surface_order_valid"])
        self.assertFalse(AUDIT.output_order_matches_deck(record, 1, "CF"))

    def test_matching_master_and_slot_are_accepted(self):
        record = report_record(1, 1)
        self.assertTrue(record["surface_order_valid"])
        self.assertTrue(AUDIT.output_order_matches_deck(record, 1, "CF"))


if __name__ == "__main__":
    unittest.main()
