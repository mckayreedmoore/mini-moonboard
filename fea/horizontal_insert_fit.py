"""Prospective insert fit in current receivers; no installed-hardware change."""
import argparse
import hashlib
import importlib
from pathlib import Path

from fea.screw_insert_repair_reserve import overlaps, write
from fea.vertical_principal_audit import repair_reserves
from mini_moonboard import insert_frame as insert
from mini_moonboard import timber_frame as timber

LIMITS = ('Prospective nominal geometry only. Current panel/kicker wood screws remain; '
          'commercial SDS screws and through-bolts are unchanged. Zero inserts installed. '
          'Receiver reserve includes any modeled grooves/service cuts, but no new pilot cuts. '
          'Insert recess, effective threads, tool access, plywood head seating, damage and '
          'connection resistance remain unresolved; no repair or construction approval.')


def prospective_screw(c):
    return insert.PanelMachineScrew(c.name, c.start, c.direction,
        insert.SCREW['nominal_overall_length'], insert.SCREW['nominal_thread_diameter'], c.members)


def assess(raw, connections):
    screws = [c for c in connections if isinstance(c, timber.PanelScrew)]
    result = repair_reserves(raw, screws, connections)
    neighbors = [(c.name, shape) for c in connections for shape in c.components()]
    for row, c in zip(result['schedule'], screws, strict=True):
        future = prospective_screw(c)
        head = future.components()[1]
        body_hits = sorted(name for name, p in raw.items() if name not in c.members and overlaps(head, p.shape))
        hardware_hits = sorted({name for name, shape in neighbors if name != c.name and overlaps(head, shape)})
        row.update(future_head_other_wood_collisions=body_hits,
                   future_head_other_fastener_collisions=hardware_hits,
                   future_machine_screw_length_mm=future.length,
                   future_machine_screw_diameter_mm=future.diameter,
                   nominal_gross_receiver_reach_mm=future.length-insert.PANEL,
                   minimum_gross_receiver_reach_mm=insert.SCREW['minimum_overall_length']-insert.PANEL,
                   passes_tested_prospective_fit=row['passes_nominal_reserve'] and not body_hits and not hardware_hits)
    result.update(installed_threaded_inserts=0,
        all_tested_prospective_fit_passed=bool(screws) and all(r['passes_tested_prospective_fit'] for r in result['schedule']),
        failure_connections=[r['connection'] for r in result['schedule'] if not r['passes_tested_prospective_fit']],
        limits=LIMITS,
        prospective_products={'insert': 'E-Z LOK 801420-13', 'machine_screw': 'L.H. Dottie FMDD14114',
                              'basis': 'Preserved docs/panel-insert-reference.json; installation not selected'})
    return result


def build(module='mini_moonboard.horizontal_service_frame'):
    model = importlib.import_module(module)
    paths = {*Path('mini_moonboard').glob('*.py'), Path(__file__),
             *map(Path, ('fea/screw_insert_repair_reserve.py', 'fea/vertical_principal_audit.py',
                         'fea/single_2x6_screen.py', 'docs/panel-insert-reference.json',
                         'docs/ml24z-reference.json', 'docs/ml23z-reference.json',
                         'docs/led-wiring-reference.json', 'docs/selective-stock-reference.json'))}
    def hashes():
        return {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(paths)}
    before = hashes()
    report = assess({p.name: p for p in model.wood_parts()}, model.connections())
    if hashes() != before:
        raise ValueError('Sources changed during prospective insert fit')
    return {'candidate': model.KEY, 'source_sha256': before, **report}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='mini_moonboard.horizontal_service_frame')
    parser.add_argument('--output', type=Path, required=True, help='New report/schedule directory')
    args = parser.parse_args()
    write(build(args.model), args.output)
