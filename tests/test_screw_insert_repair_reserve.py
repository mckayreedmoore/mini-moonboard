"""Full solid insert reserve, including a negative control missed by an annulus."""
import json
from dataclasses import replace
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import screw_insert_repair_reserve as repair


@pytest.fixture(scope='module')
def baseline():
    return repair.build()


def test_all_56_baseline_reserves(baseline):
    assert baseline['reserve_count'] == 56
    assert baseline['passes_nominal_reserves']
    assert baseline['installed_threaded_inserts'] == 0
    assert not baseline['qualified_for_design'] and not baseline['qualified_repair']
    rows = baseline['schedule']
    assert len({r['connection'] for r in rows}) == 56
    assert sum(r['panel'].startswith('kicker_') for r in rows) == 8
    assert all(r['reserve_depth_mm'] == 17. and r['reserve_diameter_mm'] == pytest.approx(12.1412)
               for r in rows)
    assert all(r['missing_receiver_volume_mm3'] <= repair.VOLUME_TOLERANCE
               and not r['intersecting_other_fasteners'] for r in rows)


def test_solid_reserve_detects_missing_core(monkeypatch):
    c = next(c for c in repair.screen.connections() if isinstance(c, repair.wide.timber.PanelScrew))
    entry, solid = repair.reserve(c)
    assert entry.toTuple() == pytest.approx((c.start + c.direction * repair.wide.PANEL).toTuple())
    core = cq.Solid.makeCylinder(1., repair.DEPTH, entry, c.direction)
    annulus = solid.cut(core)
    assert solid.cut(annulus).Volume() > repair.VOLUME_TOLERANCE
    assert repair.overlaps(solid, core)
    assert not repair.overlaps(solid, core.translate((100., 100., 100.)))
    # A receiver with only an insert-shaped annulus must fail the full reserve.
    screws = [replace(c, name=f'panel_{i}') for i in range(56)]
    monkeypatch.setattr(repair.wide.timber.PanelScrew, 'components', lambda _: ())
    result = repair.assess({c.members[1]: SimpleNamespace(shape=annulus)}, screws)
    assert not result['passes_nominal_reserves']
    assert all(not row['passes_nominal_reserve'] for row in result['schedule'])


def test_output_is_exclusive_and_retains_limits(tmp_path, baseline):
    output = tmp_path / 'reserve'
    repair.write(baseline, output)
    saved = json.loads((output / 'report.json').read_text())
    assert saved == baseline
    assert len((output / 'schedule.csv').read_text().splitlines()) == 57
    with pytest.raises(FileExistsError):
        repair.write(baseline, output)
