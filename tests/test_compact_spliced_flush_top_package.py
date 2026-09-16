import json

import cadquery as cq
import pytest

from mini_moonboard import compact_spliced_flush_top as model
from mini_moonboard.connection_geometry import material_intervals
from scripts import clear_space_construction as shared
from scripts import compact_spliced_flush_top_construction as construction
from scripts import compact_spliced_flush_top_exports as exports


def test_package_sources_bind_current_hardware_documents():
    sources = exports.sources()
    for path in (
            'docs/compact-half-inch-hardware.md',
            'docs/compact-splice-hardware.md',
            'docs/current-panel-screw-purchase.md'):
        assert sources[path] == exports.shared.digest(exports.shared.ROOT / path)


def test_hardware_schedule_states_catalog_and_nominal_diameter_acceptance():
    rows = construction.bolt_hardware_rows(model.connections())
    assert len(rows) == 20
    assert all('provisional' not in row for row in rows)
    assert all(all(value not in ('', None) for value in row.values()) for row in rows)
    assert all('washer_thickness_mm' not in row for row in rows)
    assert all('modeled_washer_thickness_mm' in row for row in rows)

    upper = next(row for row in rows if row['name'] == 'lumber_leg_bolt_left_1')
    assert upper['catalog_bolt_part'] == 'Bolt Depot 407'
    assert upper['catalog_bolt_size'] == '1/2-13 x 8 in, partially threaded'
    assert upper['minimum_full_body_through_transition_from_under_head_mm'] == 158.9278
    assert upper['catalog_min_thread_length_mm'] == 38.1

    rim = next(row for row in rows if row['name'] == 'knee_bolt_left_rim_1')
    leg = next(row for row in rows if row['name'] == 'knee_bolt_left_leg_1')
    splice = next(row for row in rows if row['name'] == 'knee_splice_bolt_left_1')
    assert rim['catalog_bolt_part'] == leg['catalog_bolt_part'] == 'Bolt Depot 371'
    assert rim['minimum_full_body_through_transition_from_under_head_mm'] == 120.1166
    assert leg['minimum_full_body_through_transition_from_under_head_mm'] == 107.4166
    assert splice['catalog_bolt_part'] == 'Bolt Depot 367'
    assert splice['minimum_full_body_through_transition_from_under_head_mm'] == 69.3166
    assert {row['nominal_diameter_acceptance'] for row in rows} == {
        'Accept only after delivered bolt passes full-body/transition and nut-seating checks.'}


def test_export_metadata_names_exact_fresh_stock_revision():
    metadata = exports.metadata(model.parts(), model.connections())
    assert metadata['key'] == model.KEY
    assert metadata['build_package'] == 'docs/compact-spliced-flush-top-build-package.md'
    assert metadata['leg_top_projection_mm'] == 0.
    assert metadata['rear_rim_overhang_mm'] == 7.
    assert metadata['upper_bolt_pitch_mm'] == 56.
    assert metadata['upper_bolt_centre_yz_mm'] == [1134.25, 1761.5]
    assert metadata['total_bolt_count'] == 20
    assert metadata['knee_piece_count'] == 4
    assert metadata['floor_runner_count'] == 0
    assert metadata['leg_taper'] is None
    assert metadata['fresh_stock_required'] is True
    panel = metadata['panel_screw_purchase']
    assert panel['product'] == 'Fas-n-Tite/Hillman model 42605'
    assert panel['quantity_required'] == 66
    assert '45.24375 mm' in panel['status']
    assert '94.45625 mm' in panel['status']
    assert 'Six fresh listed assembled cases meet' in metadata['assessment_scope']
    assert 'not transferred from prior cases' in metadata['assessment_scope']


def test_purchased_panel_screws_remain_inside_all_receivers():
    raw = {part.name: part for part in model.uncut_wood_parts()}
    screws = model.panel_connections()
    assert len(screws) == 66
    for screw in screws:
        intervals = material_intervals(
            raw[screw.members[1]].shape, screw.start, screw.direction, 0., 200.)
        assert len(intervals) == 1, screw.name
        assert intervals[0][0] == pytest.approx(18.25625), screw.name
        assert intervals[0][1] == pytest.approx(157.95625), screw.name
        assert 63.5 - intervals[0][0] == pytest.approx(45.24375), screw.name
        assert intervals[0][1] - 63.5 == pytest.approx(94.45625), screw.name


def test_profile_coordinates_reconstruct_exact_joined_member_corners(tmp_path):
    with construction.sheet_context(tmp_path):
        datums = shared.bolt_member_datums(model.connections())
        corners = construction.profile_corner_rows(datums)
    assert len(datums) == 40
    assert len({row['member'] for row in corners}) == 8
    for row in corners:
        datum = next(item for item in datums if item['member'] == row['member'])
        origin = cq.Vector(*(row[f'origin_{axis}_mm'] for axis in 'xyz'))
        along = cq.Vector(0., datum['along_y'], datum['along_z'])
        cross = cq.Vector(0., datum['cross_y'], datum['cross_z'])
        point = (origin + along * row['along_from_corner_mm']
                 + cross * row['signed_cross_from_corner_mm'])
        assert point.toTuple() == pytest.approx(
            tuple(row[f'world_{axis}_mm'] for axis in 'xyz'), abs=1.e-7)


def test_sheet_context_suppresses_stale_leg_trim_and_restores_globals(tmp_path):
    old = (shared.model, shared.OUT, shared.PACKAGE, shared.HARDWARE)
    with pytest.raises(RuntimeError, match='stop'), construction.sheet_context(tmp_path):
        assert shared.model.KEY == model.KEY
        assert shared.model.trim_planes() == {}
        assert shared.OUT == tmp_path
        raise RuntimeError('stop')
    assert (shared.model, shared.OUT, shared.PACKAGE, shared.HARDWARE) == old


def test_published_manifests_match_exact_candidate_when_present():
    paths = [
        exports.shared.ROOT / 'site/hybrid' / model.KEY / 'manifest.json',
        construction.OUT / 'manifest.json',
    ]
    if not all(path.exists() for path in paths):
        pytest.skip('generated packages not present in this checkout')
    viewer, packet = (json.loads(path.read_text()) for path in paths)
    assert viewer['design']['key'] == model.KEY
    assert viewer['design']['leg_top_projection_mm'] == 0.
    assert viewer['design']['rear_rim_overhang_mm'] == 7.
    assert packet['candidate'] == model.KEY
    assert 'No transferred historical or unconditional qualification' in packet['scope']
    for manifest in (viewer, packet):
        assert set(exports.HARDWARE_SOURCES) <= manifest['source_sha256'].keys()

    inventory = json.loads(paths[0].with_name('parts.json').read_text())
    descriptions = [item['fabrication']['description'] for item in inventory['parts']]
    assert all('Single 2x6 support legs' not in value for value in descriptions)
    assert all('225mm kicker' not in value for value in descriptions)
    assert all('three bolts per leg' not in value for value in descriptions)
    assert all('changed frame response and build qualification remain unresolved' not in value
               for value in descriptions)
    assert all('Whole-frame response and connection resistance not assessed' not in value
               for value in descriptions)
    assert all('Retained ML24Z/SDS connection gate open' in value
               for value in descriptions)
    bolt_parts = [item['fabrication'] for item in inventory['parts']
                  if item['fabrication']['kind'] == 'bolt']
    assert bolt_parts
    assert all(item['catalog_bolt_part'].startswith('Bolt Depot ') for item in bolt_parts)
    assert all(item['minimum_full_body_through_transition_from_under_head_mm'] > 0
               for item in bolt_parts)
    panel_screws = [item['fabrication'] for item in inventory['parts']
                    if item['name'].startswith(
                        ('fastener_round_panel_', 'fastener_round_kicker_',
                         'fastener_kicker_header_'))]
    assert len(panel_screws) == 66
    assert all('Historical SPAX occupied-geometry proxy' in item['description']
               for item in panel_screws)
    assert all('Fas-n-Tite/Hillman model 42605' in item['description']
               for item in panel_screws)
