"""Known-answer balanced force input with free whole-body axial translation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fea.wood_joint_port_reaction_coupon import IMAGE, BINARY, deck, run, sha


def prepare(folder):
    folder.mkdir(parents=True,exist_ok=True)
    if any(p.name!='README.md' for p in folder.iterdir()):
        raise FileExistsError('preserve existing attempt')
    for case in ('force_direct','force_mpc'):
        source=deck('dynamic_'+case.split('_')[1])
        source=source.replace('LEFT,1,1,0\n','')
        old='*BOUNDARY,AMPLITUDE=CUBIC_KNOTS\n'+('9' if case.endswith('mpc') else 'RIGHT')+',1,1,0.01'
        force='9,1,0.01' if case.endswith('mpc') else 'RIGHT,1,0.0025'
        source=source.replace(old,'*CLOAD,AMPLITUDE=CUBIC_KNOTS\nLEFT,1,-0.0025\n'+force)
        if '*BOUNDARY,AMPLITUDE' in source or 'LEFT,1,1' in source:
            raise ValueError('unexpected retained motion boundary')
        (folder/(case+'.inp')).write_text(source)
    (folder/'force-producer.py.snapshot').write_bytes(Path(__file__).read_bytes())
    (folder/'native-runner.py.snapshot').write_bytes(Path(__file__).with_name('wood_joint_port_reaction_coupon.py').read_bytes())
    freeze={'schema':'wood_joint_force_port_coupon/v1','solver_image':IMAGE,
            'solver_binary_sha256':BINARY,'cases':['force_direct','force_mpc'],
            'timeout_per_case_seconds':60,'relative_axial_stiffness_N_per_mm':1.,
            'relative_consistent_mass_tonne':2.5e-10,'force_target_N':.01,
            'ramp_duration_s':1e-4,'dt_s':1e-6,'alpha':0,
            'axial_restraint':False,'mechanical_acceptance':False,
            'artifacts_sha256':{p.name:sha(p) for p in folder.iterdir() if p.is_file()}}
    (folder/'input-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('folder',type=Path)
    args=parser.parse_args()
    (prepare if args.action=='prepare' else run)(args.folder.resolve())
