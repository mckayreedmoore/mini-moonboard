"""Aggregate flush-top evidence stays complete, authenticated and conservative."""
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from scripts.compact_spliced_flush_top_evidence import CASES, ROOT, build, digest


def copy_authenticated_archives(tmp_path):
    copied = {}
    for label, archive_name in CASES.items():
        archive = tmp_path / archive_name
        shutil.copytree(ROOT / archive_name, archive)
        manifest_path = archive / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for name in ('checks.json', 'splice-checks.json'):
            manifest['files'][name] = digest(archive / name)
        manifest_path.write_text(json.dumps(manifest))
        copied[label] = str(archive)
    return copied


def rewrite_sources(archive, transform):
    sources_path = archive / 'sources.zip'
    with ZipFile(sources_path) as sources:
        retained = {name: sources.read(name) for name in sources.namelist()}
    retained = transform(retained)
    with ZipFile(sources_path, 'w', compression=ZIP_DEFLATED) as sources:
        for name, payload in retained.items():
            sources.writestr(name, payload)
    manifest_path = archive / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['sources.zip'] = digest(sources_path)
    manifest_path.write_text(json.dumps(manifest))


def test_five_file_archives_can_be_aggregated(tmp_path):
    cases = copy_authenticated_archives(tmp_path)
    result = build(root=ROOT, cases=cases)
    assert set(result['cases']) == set(CASES)


def test_aggregate_uses_authenticated_splice_embedded_first_stage(tmp_path):
    cases = copy_authenticated_archives(tmp_path)
    archive = Path(cases['a12-left'])
    checks_path = archive / 'checks.json'
    checks = json.loads(checks_path.read_text())
    checks['metrics']['steel_direct'] = 99.
    checks_path.write_text(json.dumps(checks))
    manifest_path = archive / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['checks.json'] = digest(checks_path)
    manifest_path.write_text(json.dumps(manifest))
    embedded = json.loads((archive / 'splice-checks.json').read_text())['stage_one']

    result = build(root=ROOT, cases=cases)

    assert result['cases']['a12-left']['metrics']['steel_direct'] == embedded['metrics']['steel_direct']
    assert result['cases']['a12-left']['metrics']['steel_direct'] != 99.


def test_all_six_current_archives_form_one_deterministic_evidence_record():
    result = build()
    assert result['candidate'] == 'compact-spliced-flush-top-development'
    assert result['status'] == 'ALL_SIX_LISTED_SPLICE_MEMBER_CRITERIA_MET_WITH_OPEN_ANGLE_GATE'
    assert result['open_completion_gates']
    assert list(result['cases']) == list(CASES)
    assert len({case['geometry_sha256'] for case in result['cases'].values()}) == 1
    assert result['cases']['a12-left']['load'] == {
        'hold': 'A12', 'horizontal_force_xy_n': [-300., 0.],
        'vertical_force_n': -2224.11080763025,
    }
    assert set(result['source_sha256']) == {
        'scripts/compact_spliced_flush_top_evidence.py',
        'scripts/compact_spliced_flush_top_study.py',
    }
    assert all(case['criteria_met'] == case['criteria_total'] == 21
               for case in result['cases'].values())
    assert result['governing_adopted']['actual_angle_lateral_CD_1']['case'] == 'a12-rear'
    assert result['governing_adopted']['actual_angle_lateral_CD_1']['value'] == pytest.approx(
        .7124102546870746)
    root = result['non_adopted_full_root_sensitivity']
    assert root['adopted_as_design_basis'] is False
    assert root['actual_Ktheta']['case'] == 'a12-rear'
    assert root['actual_Ktheta']['value'] == pytest.approx(1.031684172637303)
    assert root['fixed_maximum_Ktheta']['value'] == pytest.approx(1.0805968844786396)
    assert build() == result


def test_archive_manifest_or_case_failure_cannot_be_aggregated(tmp_path):
    cases = copy_authenticated_archives(tmp_path)
    archive = Path(cases['a12-left'])
    (archive / 'splice-checks.json').write_text('{}\n')
    with pytest.raises(ValueError, match=r'Archive manifest hash differs: .*splice-checks.json'):
        build(root=ROOT, cases=cases)


def test_tampered_archived_source_cannot_be_aggregated(tmp_path):
    cases = copy_authenticated_archives(tmp_path)
    archive = Path(cases['a12-left'])

    def tamper(sources):
        sources['fea/reinforced_frame_demand.py'] += b'\n# tampered\n'
        return sources

    rewrite_sources(archive, tamper)

    with pytest.raises(
            ValueError,
            match=r'Archived source hash differs: .*reinforced_frame_demand.py'):
        build(root=ROOT, cases=cases)


def test_missing_archived_source_cannot_be_aggregated(tmp_path):
    cases = copy_authenticated_archives(tmp_path)
    archive = Path(cases['a12-left'])

    def omit(sources):
        del sources['fea/reinforced_frame_demand.py']
        return sources

    rewrite_sources(archive, omit)

    with pytest.raises(ValueError, match=r'Archived source inventory differs: .*a12-left-07'):
        build(root=ROOT, cases=cases)
