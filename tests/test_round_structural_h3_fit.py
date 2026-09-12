import pytest

from fea.round_structural_h3_fit import (
    authenticated_assessment,
    necessary_screen,
    write_report,
)


def test_standard_mount_rejected_when_rear_cannot_reach_and_front_is_covered():
    result = necessary_screen(rear_gap_mm=47., wing_reach_mm=40.,
                             front_layer_mm3=100., front_panel_intersection_mm3=100.)
    assert result['all_standard_vertical_uplift_mounts_rejected']
    assert result['rear_nominal_reach_shortfall_mm'] == 7.
    assert not result['actual_hole_pattern_checked']
    assert not result['qualified_for_design']


@pytest.mark.parametrize('gap,coverage', [(39., 100.), (47., 99.), (40., 0.)])
def test_clearing_either_obstruction_does_not_falsely_reject_all_mounts(gap, coverage):
    result = necessary_screen(rear_gap_mm=gap, wing_reach_mm=40.,
                             front_layer_mm3=100., front_panel_intersection_mm3=coverage)
    assert not result['all_standard_vertical_uplift_mounts_rejected']
    assert not result['qualified_for_design']


@pytest.mark.parametrize('coverage', [float('nan'), float('inf'), -1., 101.])
def test_invalid_or_double_counted_coverage_rejected(coverage):
    with pytest.raises(ValueError):
        necessary_screen(rear_gap_mm=47., wing_reach_mm=40.,
                         front_layer_mm3=100., front_panel_intersection_mm3=coverage)


def test_sources_are_captured_before_geometry_and_changes_rejected():
    sources = {'cad.py': 'original'}

    def changing_producer():
        sources['cad.py'] = 'changed'
        return {'geometry': 'old loaded producer'}

    with pytest.raises(ValueError, match='changed during assessment'):
        authenticated_assessment(changing_producer, lambda: dict(sources))


def test_unchanged_sources_bind_report():
    result = authenticated_assessment(lambda: {'geometry': 42}, lambda: {'cad.py': 'same'})
    assert result == {'geometry': 42, 'source_sha256': {'cad.py': 'same'}}


def test_existing_evidence_is_preserved_without_running_producer(tmp_path):
    path = tmp_path/'report.json'
    path.write_text('original')

    def unused_producer():
        pytest.fail('Existing evidence must be rejected before geometry runs')

    with pytest.raises(FileExistsError):
        write_report(path, unused_producer)
    assert path.read_text() == 'original'


def test_evidence_created_during_run_is_also_preserved(tmp_path):
    path = tmp_path/'report.json'

    def racing_producer():
        path.write_text('other result')
        return {'geometry': 42}

    with pytest.raises(FileExistsError):
        write_report(path, racing_producer)
    assert path.read_text() == 'other result'
