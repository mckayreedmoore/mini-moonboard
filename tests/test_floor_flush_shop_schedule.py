"""Occupied CAD envelopes stay distinct from shop finished-opening instructions."""
import csv
from pathlib import Path

from scripts.floor_flush_construction import HILLMAN_LENGTH_MM, INCH_MM, OUT


def rows(name):
    with (OUT / name).open(newline='') as source:
        return list(csv.DictReader(source))


def test_bolt_shop_range_is_nds_clearance_and_cad_is_upper_end():
    hardware = rows('bolt-hardware.csv')
    assert len(hardware) == 12
    for row in hardware:
        diameter = float(row['diameter_mm'])
        occupied = float(row['hole_diameter_mm'])
        assert row['shop_opening_kind'] == 'bolt_clearance'
        assert float(row['shop_finished_opening_min_mm']) == diameter + INCH_MM / 32
        assert float(row['shop_finished_opening_max_mm']) == diameter + INCH_MM / 16
        assert occupied == float(row['shop_finished_opening_max_mm'])
        assert 'not a bit catalog number' in row['shop_instruction']


def test_hillman_purchased_length_is_not_occupied_spax_envelope():
    axes = rows('connection-axes.csv')
    hillman = [row for row in axes if row['shop_opening_kind'] == 'hillman_panel']
    assert len(hillman) == 66
    assert {float(row['shop_purchased_length_mm']) for row in hillman} == {HILLMAN_LENGTH_MM}
    assert {float(row['modeled_length_mm']) for row in hillman} == {50.8}
    assert all('not Hillman' in row['shop_instruction'] for row in hillman)
    assert all('Kobalt 80277' in row['shop_instruction'] for row in hillman)
    assert all('1/8 in' in row['shop_instruction'] for row in hillman)
    assert all('not the pilot' in row['shop_instruction'] for row in hillman)
    attachments = rows('panel-attachment-axes.csv')
    assert len(attachments) == 66
    assert {float(row['shop_purchased_length_mm']) for row in attachments} == {HILLMAN_LENGTH_MM}


def test_sds_shop_instruction_is_not_a_wood_pilot():
    axes = rows('connection-axes.csv')
    sds = [row for row in axes if row['shop_opening_kind'] == 'sds_wood']
    assert len(sds) == 144
    assert all('not a wood pilot' in row['shop_instruction'] for row in sds)
    assert {float(row['shop_finished_opening_min_mm']) for row in sds} == {INCH_MM * 5 / 32}
    assert all('5/32 in' in row['shop_instruction'] for row in sds)


def test_construction_readme_does_not_claim_open_resistance_gates():
    text = Path(OUT / 'README.md').read_text()
    assert 'resistance and fabrication gates remain open' not in text
    assert 'not a factory release' in text.lower()
    assert 'shop_*' in text
