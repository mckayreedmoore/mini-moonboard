"""Native elastic patch checks for the current equivalent layered panel.

Prescribed exterior displacements reproduce exact uniaxial strain or pure
bending with zero Poisson coupling. Interior nodes remain free. Reaction work
checks section stiffness against the independently specified APA EA/EI targets.
This verifies the numerical section implementation, not a plywood product.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from fea.current_response_materials import materials
from fea.current_response_model import CurrentStructure, panel_kernel


def prepare(axis, kind, length=200., amplitude=1.e-5):
    if axis not in (0, 1) or kind not in ('axial', 'bending'):
        raise ValueError('Require an in-plane axis and axial or bending field')
    properties = materials()
    model = CurrentStructure(properties)
    local, elements, _ = panel_kernel.grid([0., length/2, length], [0., length/2, length])
    tags = {n: model.node(p) for n, p in local.items()}
    for ids in elements.values():
        model.element('S8', [tags[n] for n in ids], 'coupon')
    model.panels['coupon'] = {'nodes': list(tags.values()), 'normal': [0., 0., 1.]}
    model.layered_panels()
    half = panel_kernel.THICKNESS/2
    prescribed = {}
    expected = {}
    for n, p in model.nodes.items():
        displacement = np.zeros(3)
        if kind == 'axial':
            displacement[axis] = amplitude*p[axis]
        else:
            displacement[axis] = -amplitude*p[axis]*p[2]
            displacement[2] = amplitude*p[axis]**2/2
        expected[n] = displacement
        if any(abs(p[d]-end) < 1.e-8 for d in (0, 1) for end in (0., length)) or abs(abs(p[2])-half) < 1.e-8:
            prescribed[n] = displacement
    deck = model.deck()
    boundary = '\n'.join(f'{n},{d+1},{d+1},{value:.15g}'
                         for n, u in prescribed.items() for d, value in enumerate(u))
    deck = deck.replace('*BOUNDARY\n', '*BOUNDARY\n'+boundary+'\n').replace('*CLOAD\n', '')
    stiffness = properties['panel_targets']['ea_n_per_mm' if kind == 'axial' else 'ei_nmm'][axis]
    energy = .5*stiffness*length**2*amplitude**2
    return model, deck, prescribed, expected, energy


def run(output):
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    results = []
    for axis in (0, 1):
        for kind in ('axial', 'bending'):
            model, deck, prescribed, expected, energy = prepare(axis, kind)
            job = directory/f'{axis}-{kind}'
            job.mkdir()
            (job/'coupon.inp').write_text(deck)
            command = ['docker', 'run', '--rm', '--network=none', '--cpus=1', '--memory=1g',
                       '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1',
                       '-v', f'{job.resolve()}:/output', '-w', '/output', panel_kernel.IMAGE,
                       'timeout', '60s', 'ccx', '-i', 'coupon']
            native = subprocess.run(command, capture_output=True, text=True, timeout=80, check=False)
            log = native.stdout+native.stderr
            (job/'coupon.log').write_text(log)
            if native.returncode or '*ERROR' in log.upper():
                raise ValueError('Native patch solve failed: '+str(job/'coupon.log'))
            rows = panel_kernel.read_blocks((job/'coupon.dat').read_text())
            recovered = .5*sum(float(np.dot(rows['forces'][n], u)) for n, u in prescribed.items())
            relative = abs(recovered/energy-1.)
            displacement_error = max(float(np.linalg.norm(np.asarray(rows['displacements'][n])-u))
                                     for n, u in expected.items())
            result = {'axis': axis, 'kind': kind, 'expected_energy_nmm': energy,
                      'native_reaction_energy_nmm': recovered, 'relative_energy_error': relative,
                      'maximum_displacement_error_mm': displacement_error,
                      'nodes': len(model.nodes), 'elements': len(model.elements),
                      'passed': relative < 1.e-5 and displacement_error < 1.e-6}
            results.append(result)
    report = {'checks': results, 'passed': all(row['passed'] for row in results),
              'solver_image': panel_kernel.IMAGE, 'scope': __doc__}
    (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output), indent=2))
