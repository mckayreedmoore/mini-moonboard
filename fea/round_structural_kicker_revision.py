"""Restricted 3D force witnesses for a proposed additional kicker header row."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from fea.round_structural_screw_reference import wood_interaction

PRYING = Path('fea/results/round-structural-kicker-prying-v1.json')
MASS = Path('fea/results/round-structural-global-envelope-v1.json')
WIDTH = 1219.2
THICKNESS = 18.25625


def wrench(point, force):
    return np.r_[force, np.cross(point, force)]


def solve_case(*, screws, backing, floor, live_point, live_force, dead_point,
               dead_n, withdrawal_n, lateral_n, head_n):
    """Find independently assigned axial screws and unilateral contact forces.

    All points use the same millimetre coordinate system. No screw shear,
    contact friction, independent couple, or kinematic sharing is introduced.
    """
    inputs = [*live_point, *live_force, *dead_point, dead_n,
              withdrawal_n, lateral_n, head_n]
    if (not np.isfinite(inputs).all() or dead_n < 0
            or min(withdrawal_n, lateral_n, head_n) <= 0
            or not screws or not backing or not floor):
        raise ValueError('Require finite physical inputs and explicit support points')
    supports = ([{'kind': 'screw', **p, 'unit_force': [0.,-1.,0.]} for p in screws]
                +[{'kind': 'backing', **p, 'unit_force': [0.,1.,0.]} for p in backing]
                +[{'kind': 'floor', **p, 'unit_force': [0.,0.,1.]} for p in floor])
    a = np.array([wrench(p['point_mm'],p['unit_force']) for p in supports]).T
    applied = wrench(live_point,live_force)+wrench(dead_point,[0.,0.,-dead_n])
    scale = np.array([1.,1.,1.,1000.,1000.,1000.])
    n = len(supports)
    inequality = np.zeros((len(screws),n+1))
    for i in range(len(screws)):
        inequality[i,i] = 1.
        inequality[i,-1] = -min(head_n,withdrawal_n)
    fit = linprog([0.]*n+[1.], A_eq=np.c_[a/scale[:,None],np.zeros(6)],
                  b_eq=-applied/scale, A_ub=inequality, b_ub=np.zeros(len(screws)),
                  bounds=[(0.,None)]*(n+1), method='highs')
    if not fit.success:
        raise ValueError('Restricted minimax problem did not resolve: '+fit.message)
    reactions = []
    receiver_wrenches = {}
    for i,p in enumerate(supports):
        force = np.array(p['unit_force'])*fit.x[i]
        row = {**p, 'force_on_panel_n': force.tolist(), 'magnitude_n': float(fit.x[i])}
        if p['kind'] == 'screw':
            row['interaction'] = wood_interaction(float(fit.x[i]),0.,withdrawal_n=withdrawal_n,
                lateral_reference_n=lateral_n,head_reference_n=head_n)
        reactions.append(row)
        # Equal-and-opposite reaction delivered by panel, about the same origin.
        receiver = p['receiver']
        receiver_wrenches[receiver] = receiver_wrenches.get(receiver,np.zeros(6))-wrench(p['point_mm'],force)
    residual = a@fit.x[:-1]+applied
    if max(abs(residual[:3])) > 1e-6 or max(abs(residual[3:])) > 1e-3:
        raise ValueError('Invalid six-component equilibrium residual')
    return {'restricted_reference_witness': bool(fit.x[-1] <= 1.+1e-8),
            'minimum_maximum_tension_reference_ratio': float(fit.x[-1]),
            'reaction_forces': reactions, 'residual_wrench_n_nmm': residual.tolist(),
            'applied_wrench_n_nmm': applied.tolist(),
            'receiver_wrenches_from_panel_n_nmm': {k:v.tolist() for k,v in receiver_wrenches.items()},
            'qualified_for_design': False}


def report(mass_report=MASS):
    from mini_moonboard import kicker_header_reinforcement as proposal
    from mini_moonboard import panel_grid_v2 as grid
    from mini_moonboard import round_structural_frame as current

    mass_report = Path(mass_report)
    prying, mass = json.loads(PRYING.read_text()),json.loads(mass_report.read_text())
    hashes = {**prying['source_sha256'],**mass['source_sha256']}
    for path,sha in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError('Stale predecessor source: '+path)
    for path in (PRYING,mass_report,Path(__file__),Path(proposal.__file__)):
        path = path.resolve().relative_to(Path.cwd())
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    caps = prying['references_n']
    cases = []
    for side,sign in [('left',-1.),('right',1.)]:
        panel = 'kicker_'+side
        part = next(p for p in mass['mass_inventory'] if p['name'] == panel)
        dead_parts = [part]
        if mass_report.resolve() != MASS.resolve():
            nuts = [p for p in mass['mass_inventory']
                    if p['name'].startswith('hold_tnut_kicker_')
                    and (p['centre_xyz_mm'][0] < 0) == (side == 'left')]
            if len(nuts) != 5:
                raise ValueError('Revised mass report must include five kicker T-nuts per panel')
            dead_parts += nuts
        dead_mass = sum(p['mass_kg'] for p in dead_parts)
        # Origin is kicker backplane at x=0,z=0, shared by both panel reports.
        dead_point = [sum(p['mass_kg']*p['centre_xyz_mm'][i] for p in dead_parts)/dead_mass
                      for i in range(3)]
        dead_point[1] -= current.base.HEADER_FRONT_Y
        screws = [{'name':r['name'],'receiver':r['receiver'],
                   'point_mm':[r['x'],THICKNESS,r['s']]} for r in current.attachment_datums()
                  if r['panel'] == panel]
        if sorted(p['point_mm'][2] for p in screws) != [60.,60.,140.,140.]:
            raise ValueError('Reassess changed current kicker row')
        screws += [{'name':r['name'],'receiver':r['receiver'],
                    'point_mm':[r['x'],THICKNESS,r['s']]} for r in proposal.added_datums()
                   if r['panel'] == panel]
        backing = [{'name':f'backing_{role}_{z:g}','receiver':receiver,
                    'point_mm':[sign*x,0.,z]}
                   for role,x,post in [('outer',1200.15,f'base_post_outer_{side}'),
                                       ('center',70.,f'base_post_center_{side}')]
                   for z,receiver in [(25.,post),(200.,'base_header')]]
        floor = [{'name':f'floor_{i}','receiver':'floor','point_mm':[sign*x,THICKNESS/2,0.]}
                 for i,x in enumerate((0.,WIDTH))]
        holds = [(label,x-WIDTH) for label,(x,_) in grid.kicker_foothold_datums().items()
                 if (x < WIDTH) == (side == 'left')]
        for c in prying['cases']:
            for hold,x in holds:
                live_point = [x,THICKNESS+c['hold_standoff_mm'],150.]
                live_force = [0.,c['outward_live_n'],-c['downward_live_n']]
                result = solve_case(screws=screws,backing=backing,floor=floor,
                    live_point=live_point,live_force=live_force,dead_point=dead_point,
                    dead_n=dead_mass*9.80665,withdrawal_n=caps['withdrawal_n'],
                    lateral_n=caps['lateral_n'],head_n=caps['head_n'])
                cases.append({'panel':panel,'hold':'kicker_'+hold,'case':c['case'],
                    'standoff_mm':c['hold_standoff_mm'],'outward_n':c['outward_live_n'],
                    'live_point_mm':live_point,'live_force_n':live_force,
                    'dead_point_mm':dead_point,'dead_n':dead_mass*9.80665,
                    'dead_components':[p['name'] for p in dead_parts],**result})
    for path,sha in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError('Source changed during revision witness: '+path)
    return {'candidate':proposal.KEY,
        'based_on_candidate':current.KEY,'qualified_for_design':False,
        'mass_report':str(mass_report), 'mass_source_candidate':mass['candidate'],
        'predecessor_mass_reused':mass_report.resolve() == MASS.resolve(),
        'actual_head_applicability_resolved':False,'geometry_audited':False,
        'source_sha256':hashes,'references_n':caps,
        'proposal':{'retained_screws_per_kicker':4,'additional_screws_per_kicker':5,
                    'additional_abs_x_mm':proposal.ADDED_X_MAGNITUDES_MM,
                    'additional_z_mm':proposal.ADDED_ROW_Z_MM},
        'case_count':len(cases), 'restricted_reference_witness_count':sum(c['restricted_reference_witness'] for c in cases),
        'maximum_minimax_tension_reference_ratio':max(c['minimum_maximum_tension_reference_ratio'] for c in cases),
        'cases':cases,
        'limits':'Proposed geometry, conditional fixed-reference statics only. Panel dead mass and centroid '
                 'taken from the explicitly named authenticated mass report at its stated density. '
                 'Revised mass includes the drilled panel plus five modeled T-nut envelopes per panel. '
                 'Whole attachment screws span panel/receiver and are excluded from isolated-panel dead load; '
                 'unmodeled holds/electrical mass also excluded. No conservative omission claim. '
                 'If predecessor_mass_reused is true, added-hole and hardware mass differences remain '
                 'omitted without a conservative-dead-load claim. All 45 saved downward/normal load cases at all '
                 '10 kicker holds; no x-direction live force or hold torque. Normal screw forces independently '
                 'assigned by minimax LP; witness is not actual equal sharing or stiffness compatibility. '
                 'Floor normal resultants at bottom edge ends and mid-thickness, backing at explicit post/header '
                 'points. Point resultants do not establish contact area, pressure, panel bending, floor resistance '
                 'or local timber acceptance. Receiver wrenches are simultaneous equal-and-opposite transfers, '
                 'not checks of header, post or bracket capacity. Pure tensile screws still need applicable head, '
                 'withdrawal, group, steel and installation provisions. No free support couples, friction or '
                 'screw vertical shear. Feasible statics is not qualified resistance or construction release.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mass-report',type=Path,default=MASS)
    args = parser.parse_args()
    result = report(args.mass_report)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
