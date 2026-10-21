"""Reject a wrong connector graph before spending time on frame mechanics."""

import json

import pytest

from scripts.eoere_leg_header_revision import DOC, ROOT, verify_attachment_axes


@pytest.fixture
def axes():
    # The published nominal assembly is tracked; no ignored CAD or solve is needed.
    return json.loads((ROOT / DOC / 'leg-header-v3/geometry.json').read_bytes())['axes']


def test_published_steel_ports_match_all_installed_shaft_lines(axes):
    assert len(axes) == 96
    verify_attachment_axes(axes)


def test_mirrored_right_post_holes_cannot_be_assigned_to_opposite_bolts(axes):
    pair = [next(a for a in axes if a['id'] == f'cleat_post_bolt_right_{i}') for i in (1, 2)]
    first, second = (a['attachments'][0] for a in pair)
    first['point'][1], second['point'][1] = second['point'][1], first['point'][1]
    with pytest.raises(ValueError, match='off its installed axis: cleat_post_bolt_right_'):
        verify_attachment_axes(axes)


def test_collinear_port_still_needs_its_own_installed_axis_identity(axes):
    axis = next(a for a in axes if a['id'] == 'cleat_post_bolt_right_1')
    axis['attachments'][0]['installed_bolt_axis_id'] = 'cleat_post_bolt_right_2'
    with pytest.raises(ValueError, match='installed axis identity differs'):
        verify_attachment_axes(axes)
