"""Current structural-screw diagnostic with sampled unilateral panel seating.

Finite attachment/penalty stiffness, isotropic materials, gross rectangular solid
sections and clamped feet are diagnostic assumptions. Centered routing passages
leave only a 50.8 mm uniform rear-prism surrogate in affected 2x6 members;
the intact front ligament is discarded. This artificial stiffness model is not
a bound on structural response or a resolved bore stress model.
Convergence is not panel-screw, member, joint or floor qualification.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np

from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame
from fea import round_insert_frame as shared

KEY = 'round-structural-development'


class SeatingScrew:
    """Expose the current occupied receiver cut to the shared contact sampler."""

    def __init__(self, connection):
        self.connection = connection
        self.members = connection.members

    def receiver_cut(self):
        import cadquery as cq

        c = self.connection
        # Match mini_moonboard.round_structural_frame.parts exactly. This is
        # occupied CAD volume, not permission to drill a major-diameter pilot.
        return cq.Solid.makeCylinder(c.diameter/2, c.length+2,
                                     c.start-c.direction, c.direction)


class SeatingModule:
    def __init__(self, module):
        self.module = module

    def __getattr__(self, name):
        return getattr(self.module, name)

    def panel_connections(self):
        return tuple(SeatingScrew(c) for c in self.module.panel_connections())


def sources():
    """Authenticate current CAD plus every reused mechanics/replay producer."""
    result = shared.sources()
    result[str(Path(__file__).resolve().relative_to(Path.cwd()))] = hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()
    return result


@lru_cache(maxsize=3)
def base_frame(module, hold, source_identity):
    """Source-bound cache; every contact/stiffness probe receives a deep copy."""
    return frame.current_frame(module, hold=hold, stiffness=1000., mode='coupled',
        pounds=250., load_kind='full', frame_size=100., panel_size=80., patch_size=20.)


def prepare(module, hold='F10', panel_stiffness=1000., samples=3, penalty=100., contact=True):
    if module.KEY != KEY:
        raise ValueError('Require current structural-screw candidate')
    connections = module.panel_connections()
    names = {c.name for c in connections}
    if (len(connections) != 56 or len(names) != 56
            or not all(isinstance(c, module.timber.PanelScrew) for c in connections)
            or any(abs(c.length-50.8) > 1.e-6 or abs(c.diameter-4.1402) > 1.e-6 for c in connections)
            or panel_stiffness <= 0 or not np.isfinite(panel_stiffness)):
        raise ValueError('Require 56 SPAX #8 x 2-inch screws and positive attachment stiffness')
    structure, metadata = copy.deepcopy(base_frame(module, hold, tuple(sorted(sources().items()))))
    for spring in structure.springs:
        if spring['name'] in names:
            spring['stiffness_n_per_mm'] = panel_stiffness
    contacts = shared.seating_contacts(structure, SeatingModule(module), samples, penalty) if contact else []
    rejected = getattr(structure, 'seating_sample_rejections', [])
    for row in rejected:
        row['reason'] = ('Sample lies in modeled structural-screw receiver opening; '
                         'whole tributary omitted, not exact void-area integration')
    metadata.update(seating_rejected_samples=rejected,
        seating_rejected_point_count=len({(r['member'], *r['point_xyz_mm']) for r in rejected}),
        seating_rejected_tributary_area_mm2=sum(r['discarded_tributary_area_mm2'] for r in rejected),
        panel_screw_count=len(names), panel_attachment_names=sorted(names),
        panel_attachment_stiffness_n_per_mm=panel_stiffness,
        seating_contacts=contacts, seating_contact_enabled=contact,
        seating_contact_samples_across_width=samples, seating_penalty_n_per_mm3=penalty,
        panel_screw_connections_qualified=False, round_service_bores=module.bore_records(),
        stress_output={'global': True, 'variables': ['S', 'COORD'],
                       'integration_points': {'C3D20': 27, 'S8': 27}})
    metadata['limits'] += ' '+__doc__
    metadata['limits'] += (' Panel seating excludes current modeled screw openings, '
        'not hypothetical insert reserves. Contact uses normal scalar MPCs at existing '
        'member stations; tributary areas are approximate. Local pressure, preload, '
        'friction and actual panel-screw compliance remain unresolved.')
    return structure, metadata


def assess(record, data, frd, expansion):
    result = shared.assess(record, data, frd, expansion)
    result.pop('insert_connections_qualified', None)
    result['panel_screw_connections_qualified'] = False
    return result


def authenticated_input(directory):
    """Verify native/source receipts, exact expanded-output deck and corrected replay."""
    from fea.panel_screw_sensitivity import restore

    directory = Path(directory)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = json.loads((directory/'report.json').read_text())
    if not report['contact_diagnostic_checks_passed']:
        raise ValueError('Structural-screw diagnostic did not pass')
    for name, sha in report['source_sha256'].items():
        if digest(directory/'source_snapshots'/name) != sha:
            raise ValueError('Structural-screw source snapshot mismatch: '+name)
    for name, sha in report['artifact_sha256'].items():
        if digest(directory/name) != sha:
            raise ValueError('Structural-screw native artifact mismatch: '+name)
    job = directory/report['final_cycle_directory']
    record = json.loads((job/'input.json').read_text())
    if (record['candidate'] != 'round-structural-development' or record['mode'] != 'coupled'
            or record['assumed_modulus_mpa'] != 7000. or record['assumed_poisson_ratio'] != .3):
        raise ValueError('Unsupported current structural-screw mechanics')
    active = {r['name'] for r in record['springs'] if r['bearing_closed_assumption'] and r['active']}
    expected = restore(record).deck(active_bearings=active, stress=True).replace(
        '*END STEP', '*NODE FILE,OUTPUT=3D\nU\n*END STEP')
    if expected != (job/'frame.inp').read_text():
        raise ValueError('Expanded-output structural-screw deck does not reproduce')
    data = (job/'frame.dat').read_text()
    replay = assess(record, data, (job/'frame.frd').read_text(), (job/'frame.12d').read_text())
    for key, value in replay.items():
        if report[key] != value:
            raise ValueError('Corrected structural-screw diagnostic replay differs: '+key)
    if stress.assess(record, data) != report['diagnostic_stress']:
        raise ValueError('Structural-screw stress replay differs')
    return record, {'directory': str(directory), 'report_sha256': digest(directory/'report.json'),
                    'input_sha256': digest(job/'input.json'), 'source_sha256': report['source_sha256']}



def run(output, **parameters):
    from mini_moonboard import round_structural_frame as module

    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    hashes = sources()
    structure, metadata = prepare(module, **parameters)
    for name in hashes:
        target = directory/'source_snapshots'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        content = Path(name).read_bytes()
        if hashlib.sha256(content).hexdigest() != hashes[name]:
            raise ValueError('Source changed while archiving: '+name)
        target.write_bytes(content)
    if hashes != sources():
        raise ValueError('Source changed during structural-screw preparation')
    active = {r['name'] for r in structure.springs if r['bearing_closed_assumption']}
    seen, history = set(), []
    converged = False
    for iteration in range(30):
        signature = tuple(sorted(active))
        if signature in seen:
            break
        seen.add(signature)
        job = directory/f'cycle-{iteration:02d}'
        job.mkdir()
        record = frame.record_structure(structure, metadata, active)
        (job/'input.json').write_text(json.dumps(record, indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active, stress=True).replace(
            '*END STEP', '*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
        command = ['docker', 'run', '--rm', '--network=none', '--cpus=1', '--memory=4g',
            '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1',
            '-v', f'{job.resolve()}:/output', '-w', '/output', frame.panel_kernel.IMAGE,
            'timeout', '180s', 'ccx', '-i', 'frame']
        native = subprocess.run(command, capture_output=True, text=True, timeout=200, check=False)
        log = native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native structural-screw solve failed; inspect cycle log')
        data = (job/'frame.dat').read_text()
        report = assess(record, data, (job/'frame.frd').read_text(), (job/'frame.12d').read_text())
        report['diagnostic_stress'] = stress.assess(record, data)
        report['artifact_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in job.iterdir() if p.is_file()}
        (job/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        history.append({'directory': job.name, 'report_sha256': hashlib.sha256((job/'report.json').read_bytes()).hexdigest()})
        if report['closed_bearing_assumption_passed']:
            converged = True
            break
        active = frame.next_bearing_set(report['bearings'])
    if hashes != sources():
        raise ValueError('Source changed during structural-screw-frame diagnostic')
    report.update(contact_active_set_converged=converged, contact_cycles=history,
        final_cycle_directory=history[-1]['directory'], source_sha256=hashes,
        contact_diagnostic_checks_passed=bool(converged and report['global_equilibrium_passed'] and report['mpc_check_passed']),
        parameters=parameters, solver_image=frame.panel_kernel.IMAGE)
    report['artifact_sha256'] = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in directory.rglob('*') if p.is_file()}
    (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', choices=('F10', 'C6', 'C10'), default='F10')
    parser.add_argument('--panel-stiffness', type=float, default=1000.)
    parser.add_argument('--samples', type=int, default=3)
    parser.add_argument('--penalty', type=float, default=100.)
    parser.add_argument('--no-contact', action='store_true')
    args = parser.parse_args()
    r = run(args.output, hold=args.hold, panel_stiffness=args.panel_stiffness, samples=args.samples,
            penalty=args.penalty, contact=not args.no_contact)
    print({k: r[k] for k in ('contact_diagnostic_checks_passed', 'maximum_panel_displacement_mm', 'panel_screw_connections_qualified')})
