"""Printed-output uncertainty of authenticated reinforced-frame force recovery.

Intervals bound native DAT/FRD print roundoff propagated through linear springs
and member free-body cuts. They do not bound discretization, contact-model,
material, stiffness or physical resistance uncertainty.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fea.reinforced_frame_demand import repository_source_closure
from fea.shell_surface_recovery import recover


def moment_radius(lever, force_radius):
    x,y,z=lever
    return np.abs(np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]]))@np.array(force_radius)


def spring_radii(record, precision):
    result={name:np.zeros(3) for name in record['connection_ownership']}
    for spring in record['springs']:
        if not spring.get('active',True):
            continue
        a,b=spring['nodes']
        component=spring['dof']-1
        result[spring['name']][component]=spring['stiffness_n_per_mm']*(precision[a][component]+precision[b][component])
    for name,owner in record['connection_ownership'].items():
        if 'scalar_normal' in owner:
            result[name]=result[name][0]*np.abs(owner['scalar_normal'])
    return result


def authenticated(path):
    root=Path(path).resolve()
    manifest_path=root/'report.json'
    manifest=json.loads(manifest_path.read_text())
    for relative,digest in manifest['source_sha256'].items():
        path=root/'source_snapshots'/relative
        if Path(relative).is_absolute() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Missing or changed original source snapshot: '+relative)
    job=root/manifest['final_cycle_directory']
    content={}
    for name in ('input.json','frame.dat','frame.frd','frame.12d'):
        path=job/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['artifact_sha256'][str(path.relative_to(root))]:
            raise ValueError('Changed original native artifact: '+name)
        content[name]=path.read_text()
    return manifest,content,hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def build(path):
    sources={str(p.relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in repository_source_closure([Path(__file__)])}
    manifest,content,manifest_digest=authenticated(path)
    record=json.loads(content['input.json'])
    _,_,precision=recover(record,content['frame.dat'],content['frame.frd'],content['frame.12d'])
    radii=spring_radii(record,precision)
    members={}
    for name,member in manifest['member_section_demands'].items():
        geometry=member['member']
        entries=[(np.array(owner['point']),radii[connector])
                 for connector,owner in record['connection_ownership'].items()
                 if owner['first']==name or owner['second']==name]
        start=np.array(geometry['start'])
        axis=np.array(geometry['axis'])
        u=np.array(geometry['section_u'])
        v=np.array(geometry['section_v'])
        force=sum((r for _,r in entries),np.zeros(3))
        moment=sum((moment_radius(p-start,r) for p,r in entries),np.zeros(3))
        sections=[]
        for section in member['sections']:
            station=section['station_along_grain_mm']
            origin=np.array(section['origin_xyz_mm'])
            chosen=[(p,r) for p,r in entries if np.dot(p-start,axis)>station+1.e-7
                    or (section['include_station_loads'] and abs(np.dot(p-start,axis)-station)<=1.e-7)]
            force_bound=sum((r for _,r in chosen),np.zeros(3))
            moment_bound=sum((moment_radius(p-origin,r) for p,r in chosen),np.zeros(3))
            sections.append({'station_along_grain_mm':station,
                'include_station_loads':section['include_station_loads'],
                'axial_n_radius':float(abs(axis)@force_bound),
                'shear_u_n_radius':float(abs(u)@force_bound),
                'shear_v_n_radius':float(abs(v)@force_bound),
                'moment_u_nmm_radius':float(abs(u)@moment_bound),
                'moment_v_nmm_radius':float(abs(v)@moment_bound),
                'torsion_nmm_radius':float(abs(axis)@moment_bound)})
        members[name]={'force_residual_n':member['force_residual_n'],
            'moment_residual_nmm':member['moment_residual_nmm'],
            'force_print_roundoff_radius_n':force.tolist(),
            'moment_print_roundoff_radius_nmm':moment.tolist(),
            'force_residual_within_print_roundoff':bool(np.all(abs(np.array(member['force_residual_n']))<=force)),
            'moment_residual_within_print_roundoff':bool(np.all(abs(np.array(member['moment_residual_nmm']))<=moment)),
            'sections':sections}
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest for p,digest in sources.items()):
        raise ValueError('Postprocessor source changed during calculation')
    return {'original_run':Path(path).name,'original_report_sha256':manifest_digest,
            'postprocessor_source_sha256':sources,'member_print_roundoff':members,
            'physical_connection_force_radius_xyz_n':{n:r.tolist() for n,r in radii.items()},
            'all_member_residuals_explained_by_print_roundoff':all(
                m['force_residual_within_print_roundoff'] and m['moment_residual_within_print_roundoff'] for m in members.values()),
            'qualified_for_design':False,'limits':__doc__}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite saved evidence')
    report=build(args.directory)
    with args.output.open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps({'all_member_residuals_explained_by_print_roundoff':report['all_member_residuals_explained_by_print_roundoff']}))
