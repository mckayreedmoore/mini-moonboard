"""Check the purchase override against the retained axes without rebuilding CAD."""
import csv
import io
import json

import pytest

from scripts.eoere_selected_hardware import DOC, ROOT, canonical, selected_rows

SHOP = DOC / "shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1"


def sources():
    parent = json.loads((ROOT / DOC / "occupied-kicker-clearance-v1.json").read_bytes())
    raw = (ROOT / SHOP / "hardware-selection.csv").read_bytes()
    return raw, {row["id"]: row for row in parent["axes"]}, parent


def test_applied_overrides_preserve_axes_and_use_exact_issued_selection():
    raw, axes, parent = sources()
    applied = json.loads((ROOT / DOC / "occupied-selected-hardware-v1.json").read_bytes())
    selected = selected_rows(raw, axes)
    assert list(selected.values()) == applied["selected_stacks"]
    assert canonical(parent["axes"]) == applied["axes_canonical_sha256"]
    assert canonical(parent["screw_axes"]) == applied["screw_axes_canonical_sha256"]
    assert applied["selected_hardware_overrides_parent_lengths"] is True
    assert applied["analysis_pass_transferred"] is False
    assert all(value is False for value in applied["release"].values())
    for name, row in selected.items():
        # Metal extends along the original unit axis; no hole or timber moves.
        assert sum(v * v for v in axes[name]["direction_xyz"]) == pytest.approx(1)
        assert row["selected_underhead_length_mm"] - axes[name]["nominal_under_head_length_mm"] == pytest.approx(row["selected_tip_delta_mm"])
    assert len(applied["changed_finished_solids"]) == 48
    assert len(applied["template_solids"]) == 6


@pytest.mark.parametrize("change", [
    lambda rows: rows.pop(),
    lambda rows: rows.__setitem__(1, rows[0].copy()),
    lambda rows: rows[0].update(selected_diameter_mm="12.7"),
    lambda rows: rows[0].update(selected_underhead_length_mm="65"),
    lambda rows: rows[0].update(minimum_two_pitch_margin_mm="0"),
    lambda rows: rows[0].update(minimum_nut_seating_margin_mm="-1"),
    lambda rows: rows[0].update(minimum_body_to_nominated_target_margin_mm="nan"),
    lambda rows: rows[0].update(nut_side_spacer_mm="6.35"),
])
def test_reject_incompatible_stack_overrides(change):
    raw, axes, _ = sources()
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    fields = list(rows[0])
    change(rows)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    with pytest.raises(ValueError):
        selected_rows(stream.getvalue().encode(), axes)
