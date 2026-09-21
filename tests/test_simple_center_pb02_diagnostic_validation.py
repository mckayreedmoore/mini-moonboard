"""PB02 accepted-report validation uses physical bolt names, not interfaces."""

from scripts.simple_center_pb02_diagnostic_run import _bolt_row_inventory
from scripts.simple_center_pb02_native import native_row_inventory


def test_canonical_rows_group_under_all_ten_physical_bolts():
    groups = _bolt_row_inventory(native_row_inventory())

    assert len(groups) == 10
    assert set(groups) == {
        "post_block/bolt_1",
        "post_block/bolt_2",
        "block_header/bolt_1",
        "block_header/bolt_2",
        "header_principal_block/bolt_1",
        "principal_block_principal/bolt_1",
        "principal_upright_block/bolt_1",
        "upright_rear_block/bolt_1",
        "rear_block_post/bolt_1",
        "rear_block_post/bolt_2",
    }
    assert all(len(rows) == 3 for rows in groups.values())
