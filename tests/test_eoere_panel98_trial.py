"""The corrected added-screw rule preserves the current purchased stations."""

import copy
import json

import pytest

from scripts.eoere_98_screw_trial import DOC, PANELS, ROOT, proposed_axes


@pytest.fixture
def source_rows():
    """Tracked frozen stations; no ignored CAD cache or mutable index needed."""
    axes=json.loads((ROOT/DOC/'occupied-kicker-clearance-v1.json').read_bytes())['screw_axes']
    rows=[{'id':r['axis_id'],'first':r['panel'],'second':r['receiver'],
           'source_screw_descriptor':r,'point_xyz_mm':r['origin_xyz_mm']}
          for r in axes]
    names={r[key] for r in axes for key in ('panel','receiver')}
    # Layout tests check station creation/ownership; exact solid backing is
    # exercised by the separate cached-solid evidence, not this broad box.
    sources={name:{'bounds_xyz_mm':[-10000.,10000.]*3} for name in names}
    return {'hillman_rows':rows},sources


def test_layout_adds_32_stations_on_existing_receiver_rows_without_moving_old_axes(source_rows):
    data,sources=source_rows
    before = copy.deepcopy(data['hillman_rows'])
    added = proposed_axes(data,sources)
    assert data['hillman_rows'] == before
    assert len(added) == len({r['axis']['axis_id'] for r in added}) == 32
    assert not {r['axis']['axis_id'] for r in added} & {r['id'] for r in before}
    for panel in PANELS:
        rows = [r for r in added if r['axis']['panel']==panel]
        assert len(rows)==8
        assert all(sum(r['edge_role']==edge for r in rows)==2 for edge in ('rim','center','edge','service'))
    for row in added:
        assert row['axis']['receiver'] == row['mechanical']['second']
        assert row['axis']['installed'] is False
        assert row['axis']['purchased'] is False


def test_missing_original_station_stops_the_trial(source_rows):
    data,sources=source_rows
    data['hillman_rows'].remove(next(r for r in data['hillman_rows']
                                    if r['id']=='round_panel_upper_left_rim_1'))
    with pytest.raises(ValueError,match='expected 12 existing axes'):
        proposed_axes(data,sources)
