"""Check source coordinates and reject misleading builder-table inputs."""

import copy
import re

import pytest

from scripts.eoere_builder_layout import (
    OUTPUT,
    ROOT,
    load_sources,
    read_bound,
    render,
    validate,
)


def test_current_layout_and_rejection_controls(tmp_path):
    data = load_sources()
    validate(data)
    assert len(data['selected']) == 96 and len(data['holes']) == 112
    assert all(not r['axis_id'].endswith('_2') for r in data['selected']
               if r['axis_id'].startswith(('lumber_leg_bolt_', 'rail_rear_bolt_')))
    text = render(data)
    assert (ROOT / OUTPUT).read_text() == text
    for name in ("base_post_outer_left", "base_post_outer_right"):
        assert data["profiles"][name]["blank_mm"] == [238.9, 139.7, 88.9]
        post_holes = [r for r in data["holes"] if r["receiver"] == name]
        assert len(post_holes) == 4
        assert all(float(r["saved_full_wall_length_mm"]) == pytest.approx(88.9) for r in post_holes)
    for row in data["selected"]:
        if row["axis_id"].startswith("cleat_post_bolt_"):
            assert float(row["selected_underhead_length_mm"]) == pytest.approx(177.8)
            assert float(row["nut_side_spacer_mm"]) == 25.4
    # The header turns the section axes: U is depth and V is thickness.
    vertices = data["profiles"]["base_header"]["vertices_luv_mm"]
    assert max(v[1] for v in vertices) - min(v[1] for v in vertices) == pytest.approx(139.7)
    assert max(v[2] for v in vertices) - min(v[2] for v in vertices) == pytest.approx(38.1)
    assert "base_header uses U across its 139.7-mm\ndepth and V across its 38.1-mm thickness" in text
    assert "| `eoere_bolt_066` | `(1065.0625, 95.25, 38.1)` | `(1065.0625, 95.25, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |" in text
    # The recessed rear leg enters at U=50.8, not the raw U=88.9 face.
    rear = next(r for r in data["holes"] if r["axis_id"] == "rail_rear_bolt_left_1"
                and r["receiver"] == "lumber_leg_left")
    assert float(rear["entry_in_receiver_u_mm"]) == pytest.approx(50.8, abs=1e-8)
    assert float(rear["entry_in_receiver_l_mm"]) == pytest.approx(88.269485048, abs=1e-8)
    assert float(rear["exit_in_receiver_u_mm"]) == pytest.approx(0, abs=1e-8)
    right = next(r for r in data["holes"] if r["axis_id"] == "rail_rear_bolt_right_1"
                 and r["receiver"] == "lumber_leg_right")
    assert float(right["entry_in_receiver_u_mm"]) == pytest.approx(38.1, abs=1e-8)
    assert float(right["exit_in_receiver_u_mm"]) == pytest.approx(88.9, abs=1e-8)
    guide = (ROOT / OUTPUT.with_name("builder-plan.md")).read_text()
    assert "left leg enters at U=50.8 and exits at U=0" in re.sub(r'\s+', ' ', guide)
    assert "right leg enters at U=38.1 and exits at U=88.9" in re.sub(r'\s+', ' ', guide)
    # A mirrored cleat retains its installed world orientation and selected spacer.
    cleat = data["profiles"]["eoere_cleat_right"]
    assert cleat["datum_xyz_mm"] == pytest.approx([1216.025, -213.8, 139.7])
    assert cleat["basis_grain_u_v_xyz"] == [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    shared = next(r for r in data["selected"] if r["axis_id"] == "eoere_bolt_065")
    assert float(shared["selected_underhead_length_mm"]) == pytest.approx(88.9, abs=1e-10)
    assert float(shared["nut_side_spacer_mm"]) == 12.7
    assert sum(int(r['spacer_piece_count']) for r in data['selected']) == 24
    wrong = copy.deepcopy(data)
    next(r for r in wrong['selected'] if r['axis_id'] == 'eoere_bolt_065')['spacer_piece_count'] = '0'
    with pytest.raises(ValueError, match='factory spacer inventory differs'):
        validate(wrong)

    wrong = copy.deepcopy(data)
    wrong["holes"][0]["entry_in_receiver_v_mm"] = "95.3"
    with pytest.raises(ValueError, match="coordinate differs"):
        validate(wrong)
    wrong = copy.deepcopy(data)
    wrong["holes"][-1] = wrong["holes"][0].copy()
    with pytest.raises(ValueError, match="occurrences differ or repeat"):
        validate(wrong)
    wrong = copy.deepcopy(data)
    wrong["selected"][0]["receiver_member_ids"] = "base_floor_left"
    with pytest.raises(ValueError, match="receiver identities differ"):
        validate(wrong)
    wrong = copy.deepcopy(data)
    wrong["members"][0]["Actual"] = "observed"
    with pytest.raises(ValueError, match="observation cells"):
        validate(wrong)
    (tmp_path / "issued.csv").write_text("changed bytes\n")
    with pytest.raises(ValueError, match="Source hash differs"):
        read_bound(tmp_path, {"path": "issued.csv", "sha256": "0" * 64})
