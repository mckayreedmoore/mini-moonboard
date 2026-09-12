"""Reject penetrations and authenticate the separate candidate's mass evidence."""
import json
from pathlib import Path

import cadquery as cq
import pytest

from fea.reinforcement_review import interference, locations, sources
from fea.round_insert_floor import inventory_state
from fea.user_load_envelope import envelope


def test_interference_distinguishes_contact_and_penetration():
    block = cq.Solid.makeBox(10., 10., 10.)
    touching = cq.Solid.makeBox(10., 10., 10., cq.Vector(10., 0., 0.))
    penetrating = cq.Solid.makeBox(10., 10., 10., cq.Vector(9., 0., 0.))
    assert interference(block, touching) == 0.
    assert interference(block, penetrating) == pytest.approx(100.)


def test_combined_evidence_replays_inventory_and_all_global_cases():
    from mini_moonboard import round_reinforcement_frame as model

    report = json.loads(Path('docs/round-reinforcement-review/review.json').read_text())
    assert report['source_sha256'] == sources()
    rebuilt = inventory_state(report['mass_inventory'])
    assert rebuilt == {key: report['state'][key] for key in rebuilt}
    nuts = [r for r in report['mass_inventory'] if r['name'].startswith('hold_tnut_')]
    assert len(nuts) == 142
    assert all(r['density_kg_m3'] == 7850 for r in nuts)
    assert len(model.panel_connections()) == 66
    assert report['unchanged_leg_bolt_count'] == 8
    assert not report['modified_connections']
    assert report['connection_counts'] == {'screw': 198, 'bolt': 24}
    assert not report['added_hardware_interference_check']['interferences']
    assert report['cases'] == json.loads(json.dumps(envelope(report['state'], locations(model))))
    assert not report['qualified_for_design']
    assert not report['internal_connection_demands_evaluated']
    assert not report['floor_qualification']
