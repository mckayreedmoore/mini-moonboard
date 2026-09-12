"""Integrate native 27-point shell stresses and check APA panel components."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from fea import reinforced_fastener_checks as fasteners
from fea.horizontal_frame_stress import parse, transform
from fea.reinforced_panel_checks import section_check

GAUSS = (-math.sqrt(3/5),0.,math.sqrt(3/5))
WEIGHTS = (5/9,8/9,5/9)


def integrate_thickness(tensors, thickness_mm):
    """Three through-thickness Gauss points, ordered negative-to-positive z."""
    a=np.asarray(tensors,float)
    if a.shape!=(3,3,3) or not np.isfinite(a).all() or not math.isfinite(thickness_mm) or thickness_mm<=0:
        raise ValueError('Require three finite local stress tensors and physical thickness')
    integral=sum(w*s for w,s in zip(WEIGHTS,a,strict=True))*thickness_mm/2
    first=sum(w*g*s for w,g,s in zip(WEIGHTS,GAUSS,a,strict=True))*thickness_mm**2/4
    return {'nx_n_per_mm':float(integral[0,0]),'ny_n_per_mm':float(integral[1,1]),
            'mx_nmm_per_mm':float(first[0,0]),'my_nmm_per_mm':float(first[1,1]),
            'qx_n_per_mm':float(integral[0,2]),'qy_n_per_mm':float(integral[1,2]),
            'nxy_n_per_mm':float(integral[0,1]),
            'mxy_nmm_per_mm_unchecked':float(first[0,1])}


def assess(record,data,thickness_mm=18.25625):
    elements={int(k):v for k,v in record['elements'].items()}
    physical={k:v for k,v in elements.items() if v[0]!='SPRING2'}
    if any(v[0] not in ('S8','C3D20') for v in physical.values()):
        raise ValueError('Unsupported physical element type')
    expected={(e,ip):r[2].upper() for e,r in physical.items() for ip in range(1,28)}
    parsed=parse(data,expected)
    nodes={int(k):np.asarray(v,float) for k,v in record['nodes'].items()}
    panels={}
    target=np.asarray(record['target_xyz_mm'],float) if 'target_xyz_mm' in record else None
    patch=record.get('panel_patch_mm')
    half_patch=((patch[1]-patch[0])/2,(patch[3]-patch[2])/2) if patch else None
    for e,(kind,ids,panel) in physical.items():
        if kind!='S8':
            continue
        origin=nodes[ids[0]]
        ex=nodes[ids[1]]-origin;ey=nodes[ids[3]]-origin
        lx,ly=np.linalg.norm(ex),np.linalg.norm(ey)
        ex,ey=ex/lx,ey/ly
        axes=np.asarray([ex,ey,np.cross(ex,ey)])
        transform([0.]*6,axes)
        if abs(abs(ex[0])-1)>1e-8:
            raise ValueError('Section axes must follow panel horizontal/upslope directions')
        grid={}
        for ip in range(1,28):
            key=(e,ip)
            xyz=np.asarray(parsed['global coordinates'][key])
            local=axes@(xyz-origin)
            targets=[[(g+1)*lx/2 for g in GAUSS],[(g+1)*ly/2 for g in GAUSS],
                     [g*thickness_mm/2 for g in GAUSS]]
            indices=tuple(int(np.argmin(abs(np.asarray(v)-coord))) for v,coord in zip(targets,local,strict=True))
            # Native DAT prints seven significant digits. At <=3000mm the
            # component rounding <=0.0005mm;0.003mm covers orthogonal projections.
            if max(abs(local[i]-targets[i][j]) for i,j in enumerate(indices))>.003:
                raise ValueError(f'Integration-point geometry inconsistent with rectangular S8: {e}/{ip}')
            if indices in grid:
                raise ValueError('Duplicate physical Gauss location')
            grid[indices]=(ip,transform(parsed['stresses'][key],axes))
        if len(grid)!=27:
            raise ValueError('Require complete3x3x3 physical Gauss tensor product')
        for ix in range(3):
            for iy in range(3):
                points=[grid[(ix,iy,iz)] for iz in range(3)]
                resultants=integrate_thickness([p[1] for p in points],thickness_mm)
                checked={k:v for k,v in resultants.items() if not k.endswith('_unchecked')}
                check=section_check(panel=panel,width_mm=1219.2,
                    height_mm=225. if panel.startswith('kicker_') else 1219.2,
                    deflection_mm=None,deflection_limit_mm=None,**checked)
                group=panels.setdefault(panel,{'section_count':0,'exceeded_section_count':0,'component_extrema':{},
                                               'maximum_unchecked_twisting_moment_nmm_per_mm':0.,
                                               'field_outside_patch':{str(d):{'section_count':0,'component_extrema':{}}
                                                                      for d in (0.,50.,100.)}})
                group['section_count']+=1
                group['exceeded_section_count']+=bool(check['exceeded_components'])
                group['maximum_unchecked_twisting_moment_nmm_per_mm']=max(
                    group['maximum_unchecked_twisting_moment_nmm_per_mm'],abs(resultants['mxy_nmm_per_mm_unchecked']))
                point=origin+ex*(GAUSS[ix]+1)*lx/2+ey*(GAUSS[iy]+1)*ly/2
                offset=None if target is None else [float(np.dot(point-target,ex)),float(np.dot(point-target,ey))]
                distance=None if offset is None or half_patch is None else math.hypot(
                    max(0.,abs(offset[0])-half_patch[0]),max(0.,abs(offset[1])-half_patch[1]))
                witness={'element':e,'integration_points':[p[0] for p in points],
                         'section_xyz_mm':point.tolist(),'resultants':resultants,
                         'in_plane_offset_from_load_center_mm':offset,
                         'distance_from_declared_patch_mm':distance}
                destinations=[group['component_extrema']]
                if distance is not None:
                    for threshold,field in group['field_outside_patch'].items():
                        if distance > float(threshold)+1e-8:
                            field['section_count']+=1
                            destinations.append(field['component_extrema'])
                for destination in destinations:
                    for component,ratio in check['component_ratios'].items():
                        if component not in destination or ratio>destination[component]['ratio']:
                            destination[component]={'ratio':ratio,**witness}
    if len(panels)!=6:
        raise ValueError('Require all six independent physical panels')
    return {'panels':panels,'declared_load_patch_mm':patch,
            'declared_load_patch_type':record.get('panel_patch_load_type'),
            'qualified_for_design':False,
            'combined_panel_strength_accepted':False,
            'integration_method':'Three-point thickness Gauss integration of actual global stress tensors '
                'transformed to each shell element axes; nine sections per full-integration S8.',
            'limits':'Native homogeneous isotropic, unperforated shell demands. Ratios compare APA Group4 '
                'weaker-orthogonal component references; material response is not an orthotropic prediction. '
                'No mesh-convergence, actual hold footprint, net-hole notch stresses, biaxial interaction, '
                'twisting resistance, plate buckling or deflection acceptance is supplied. Contact convergence '
                'and the force model must be accepted independently; failed cycle values are diagnostic only. '
                'Patch stresses are not actual hold-seat stresses. Full-field and outside-patch50/100mm '
                'extrema are separately retained; excluding the patch is interpretation, not a local-strength pass. '
                'Absolute panel displacement includes frame motion. Native sticking-floor forces may exceed '
                'assumed floor friction; contact iteration convergence alone does not establish floor admissibility.'}


def from_directory(directory):
    directory=Path(directory)
    sources=('fea/reinforced_panel_resultants.py','fea/reinforced_panel_checks.py',
             'fea/horizontal_frame_stress.py','fea/reinforced_fastener_checks.py',
             'docs/reinforced-fastener-applicability.json','fea/round_structural_screw_reference.py')
    hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}
    manifest_path=directory/'report.json'
    manifest=json.loads(manifest_path.read_text())
    cycle=directory/manifest['final_cycle_directory']
    paths={name:cycle/name for name in ('input.json','frame.dat','frame.inp','report.json')}
    native_hashes={}
    for name,path in paths.items():
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if manifest['artifact_sha256'].get(str(path.relative_to(directory)))!=digest:
            raise ValueError('Native artifact authentication failed: '+name)
        native_hashes[name]=digest
    for name,sha in manifest['source_sha256'].items():
        relative=Path(name)
        if relative.is_absolute():
            relative=relative.relative_to(Path.cwd())
        if hashlib.sha256((directory/'source_snapshots'/relative).read_bytes()).hexdigest()!=sha:
            raise ValueError('Native source snapshot authentication failed: '+name)
    deck=paths['frame.inp'].read_text().splitlines()
    thickness=[]
    for i,line in enumerate(deck):
        if line.upper().startswith('*SHELL SECTION'):
            thickness.append(float(deck[i+1].split(',')[0]))
    if len(thickness)!=6 or any(not math.isclose(t,18.25625,abs_tol=1e-8) for t in thickness):
        raise ValueError('Reassess changed shell thickness')
    record=json.loads(paths['input.json'].read_text())
    result=assess(record,paths['frame.dat'].read_text(),thickness[0])
    references={'withdrawal_n':fasteners.WITHDRAWAL_N,'lateral_n':fasteners.LATERAL_N,
                'head_n':fasteners.HEAD_N}
    attachments=[]
    for name,row in manifest['physical_connection_forces'].items():
        if not name.startswith(('round_panel_','round_kicker_','kicker_header_')):
            continue
        first_panel=row['first'].startswith(('main_','kicker_'))
        panel=row['first'] if first_panel else row['second']
        if not panel.startswith(('main_','kicker_')):
            raise ValueError('Panel attachment has no panel owner')
        force=np.asarray(row['force_on_first_xyz_n' if first_panel else 'force_on_second_xyz_n'])
        inward=np.array([0.,-1.,0.]) if panel.startswith('kicker_') else np.array(
            [0.,-math.cos(math.radians(40)),math.sin(math.radians(40))])
        signed=float(np.dot(force,inward))
        lateral=float(np.linalg.norm(force-signed*inward))
        attachments.append({'name':name,'panel':panel,'signed_tensile_force_n':signed,
            'lateral_force_n':lateral,'force_on_panel_xyz_n':force.tolist(),
            **fasteners.panel_check(row)})
    if len(attachments)!=66:
        raise ValueError('Require all66 current panel/kicker attachment demands')
    result.update({'individual_attachment_checks':attachments,'attachment_references_n':references,
        'attachment_reference_exceedance_count':sum(r['wood_interaction_ratio']>1 or
            r['head_pull_through_ratio']>1 for r in attachments),
        'candidate':manifest['candidate'],'native_directory':str(directory),
        'native_final_cycle':cycle.name,'native_evidence_sha256':native_hashes,
        'native_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'native_contact_active_set_converged':manifest['contact_active_set_converged'],
        'native_global_equilibrium_passed':manifest['global_equilibrium_passed'],
        'reported_maximum_panel_displacement_mm':manifest['maximum_panel_displacement_mm'],
        'reported_displacement_is_absolute_not_relative_panel_bending':True,
        'native_assumptions':manifest['assumptions'],
        'load_and_response_model':{k:record[k] for k in ('hold','force_xyz_n','standoff_from_front_mm',
            'stiffness_n_per_mm','assumed_modulus_mpa','assumed_poisson_ratio','panel_patch_size_mm')},
        'source_sha256':hashes})
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha for p,sha in hashes.items()):
        raise ValueError('Panel response consumer changed during calculation')
    result['recorded_native_hashes_verified']=True
    result['native_producer_dependency_closure_independently_established']=False
    result['native_source_closure_note']=('Recorded snapshots authenticated; complete producer dependency '
        'closure requires independent replay. Check native manifest for horizontal_frame_stress.py, '
        'which v3 omitted. This postprocessor independently records its actual parser hash.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=from_directory(args.directory)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
