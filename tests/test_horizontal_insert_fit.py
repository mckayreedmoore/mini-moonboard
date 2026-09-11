"""Prospective geometry must reject a groove through otherwise sufficient stock."""
import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import horizontal_insert_fit as fit


def test_groove_crossing_full_insert_reserve_fails_without_installing_inserts():
    thickness = fit.insert.PANEL
    screw = fit.timber.PanelScrew('panel', cq.Vector(0, 0, -thickness), cq.Vector(0, 0, 1),
                                 50.8, 4.1402, ('face', 'receiver'))
    stock = cq.Solid.makeBox(38.1, 100., 139.7, cq.Vector(-19.05, -50., 0.))
    raw = {'receiver': SimpleNamespace(shape=stock)}
    report = fit.assess(raw, (screw,))
    assert report['reserve_count'] == 1 and report['all_tested_prospective_fit_passed']
    assert report['installed_threaded_inserts'] == 0
    assert not report['qualified_for_design'] and not report['qualified_repair']
    row = report['schedule'][0]
    assert row['nominal_gross_receiver_reach_mm'] == pytest.approx(13.49375)
    assert row['minimum_gross_receiver_reach_mm'] == pytest.approx(11.96975)
    groove = cq.Solid.makeBox(38.1, 3., 2., cq.Vector(-19.05, -1.5, 0.))
    raw['receiver'] = SimpleNamespace(shape=stock.cut(groove))
    rejected = fit.assess(raw, (screw,))
    assert not rejected['all_tested_prospective_fit_passed']
    assert rejected['failure_connections'] == ['panel']
    assert rejected['schedule'][0]['missing_receiver_volume_mm3'] > .01


def test_larger_future_head_must_clear_neighboring_wood():
    c = fit.timber.PanelScrew('panel', cq.Vector(0, 0, -fit.insert.PANEL), cq.Vector(0, 0, 1),
                              50.8, 4.1402, ('face', 'receiver'))
    raw = {'receiver': SimpleNamespace(shape=cq.Solid.makeBox(38.1, 100., 139.7, cq.Vector(-19.05, -50., 0.))),
           'obstruction': SimpleNamespace(shape=cq.Solid.makeBox(1., 1., 1., cq.Vector(4.5, -.5, -fit.insert.PANEL)))}
    result = fit.assess(raw, (c,))
    assert result['passes_nominal_reserves']
    assert result['schedule'][0]['future_head_other_wood_collisions'] == ['obstruction']
    assert not result['all_tested_prospective_fit_passed']


@pytest.mark.parametrize('reference', ['docs/led-wiring-reference.json', 'docs/ml23z-reference.json'])
def test_runtime_geometry_references_are_hashed_and_changes_rejected(monkeypatch, reference):
    model = SimpleNamespace(KEY='provenance-test', wood_parts=lambda: (), connections=lambda: ())
    monkeypatch.setattr(fit.importlib, 'import_module', lambda _: model)
    monkeypatch.setattr(fit, 'assess', lambda *_: {})
    report = fit.build()
    target = Path(reference).resolve()
    assert report['source_sha256'][reference] == hashlib.sha256(target.read_bytes()).hexdigest()
    original = Path.read_bytes
    reads = 0

    def changed_after_initial_hash(path):
        nonlocal reads
        data = original(path)
        if path.resolve() == target:
            reads += 1
            if reads > 1:
                return data+b' '
        return data

    monkeypatch.setattr(Path, 'read_bytes', changed_after_initial_hash)
    with pytest.raises(ValueError, match='Sources changed'):
        fit.build()


def test_published_v2_sources_schedule_and_fit_flags_replay_without_cad():
    root = Path('fea/results/horizontal-insert-fit-v2')
    report = json.loads((root/'report.json').read_text())
    assert report['candidate'] == 'horizontal-service-development'
    references = {'docs/led-wiring-reference.json', 'docs/ml23z-reference.json',
                  'docs/ml24z-reference.json', 'docs/panel-insert-reference.json'}
    assert references <= report['source_sha256'].keys()
    for name, sha in report['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    rows = report['schedule']
    assert report['reserve_count'] == len(rows) == 87
    assert len({row['connection'] for row in rows}) == 87
    with (root/'schedule.csv').open(newline='') as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == len(rows)
    for row, csv_row in zip(rows, csv_rows, strict=True):
        assert csv_row == {key: ';'.join(value) if key == 'intersecting_other_fasteners'
                           else str(value) for key, value in row.items()}
        assert row['reserve_diameter_mm'] == 12.1412
        assert row['reserve_depth_mm'] == 17.
        assert row['missing_receiver_volume_mm3'] == pytest.approx(0., abs=.01)
        assert not row['intersecting_other_fasteners']
        assert not row['future_head_other_wood_collisions']
        assert not row['future_head_other_fastener_collisions']
        assert row['passes_nominal_reserve'] and row['passes_tested_prospective_fit']
    assert report['passes_nominal_reserves'] and report['all_tested_prospective_fit_passed']
    assert report['failure_connections'] == []
    assert report['installed_threaded_inserts'] == 0
    assert not report['qualified_for_design'] and not report['qualified_repair']
