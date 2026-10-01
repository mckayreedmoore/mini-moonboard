"""Independent serialized-input audit. Never authorizes or executes a solve."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
NEW=BASE/'current-springa-frame-input-adapter-attempt01/a12-rear'
OLD=BASE/'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1'
FLOOR=BASE/'current-floor-stick-constraint-audit-attempt01'


def cards(text):
    result=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            result.append([line,[]])
        else:
            assert result
            result[-1][1].append(line)
    return result


def equations(deck):
    answer={}
    for header,lines in cards(deck):
        if header.upper()!='*EQUATION':
            continue
        count=int(lines[0]); cells=','.join(lines[1:]).split(',')
        assert len(cells)==3*count
        terms=[(int(cells[i]),int(cells[i+1]),float(cells[i+2])) for i in range(0,len(cells),3)]
        key=terms[0][:2]
        assert key not in answer, ('duplicate dependent DOF',key)
        answer[key]=terms
    return answer


def run(input_directory=None, output_name="audit.json"):
    inspected=Path(input_directory) if input_directory else NEW
    old=json.loads((OLD/'model.json').read_text())
    new=json.loads((inspected/'model.json').read_text())
    olddeck=(OLD/'model.inp').read_text(); deck=(inspected/'model.inp').read_text()
    assert hashlib.sha256((OLD/'model.json').read_bytes()).hexdigest()=='d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0'
    assert new['candidate']==old['candidate'] and new['geometry_revision_id']==old['geometry_revision_id']
    assert new['schema']!=old['schema'], 'A new response schema is required'
    for key in ['physical_body_nodes','physical_body_elements','body_geometry',
                'connection_ownership','physical_body_loads','physical_external_loads']:
        assert new[key]==old[key], ('changed source field',key)
    kinds=('MATERIAL','ELASTIC','ORIENTATION','SOLID SECTION','SHELL SECTION')
    def material_cards(text):
        return [(h,d) for h,d in cards(text) if h[1:].split(',')[0].upper() in kinds]
    assert material_cards(deck)==material_cards(olddeck), 'Material constants/orientations/sections differ'
    parsed_nodes={}
    boundary=set()
    cloads={}
    for header,lines in cards(deck):
        if header.upper()=='*NODE':
            for line in lines:
                fields=line.split(','); parsed_nodes[int(fields[0])]=list(map(float,fields[1:]))
        if header.upper()=='*CLOAD':
            for line in lines:
                n,d,v=line.split(',')
                key=(int(n),int(d))
                cloads[key]=cloads.get(key,0.)+float(v)
        if header.upper()=='*BOUNDARY':
            for line in lines:
                n,a,b,*v=line.split(',')
                assert not v or float(v[0])==0
                boundary.update((int(n),d) for d in range(int(a),int(b)+1))
    assert set(parsed_nodes)==set(map(int,new['nodes']))
    node_error=max(abs(parsed_nodes[int(n)][d]-xyz[d]) for n,xyz in old['nodes'].items() for d in range(3))
    assert node_error<1e-8
    declared_loads={(int(n),d+1):v for n,f in old['physical_external_loads'].items() for d,v in enumerate(f)}
    assert not set(cloads)-set(declared_loads), 'Unexpected applied source load DOF'
    load_error=max(abs(cloads.get(key,0.)-v) for key,v in declared_loads.items())
    assert load_error<1e-8
    eq=equations(deck)
    assert not set(eq)&boundary
    assert len(eq)==len(new['equations'])
    floor=json.loads((FLOOR/'audit.json').read_text())
    archive=np.load(FLOOR/'constraint-matrices.npz')
    A=archive['original']; selected=archive['selected_rows']; pivots=archive['pivots']
    masters=[tuple(k) for k in floor['physical_master_dofs']]
    references=new['floor_reference_nodes_and_load_map']
    ref_by_node={int(r['node']):int(r['source_row_original_index']) for r in references}
    assert len(ref_by_node)==200
    actual_h=np.zeros_like(A); actual_d=np.zeros((200,200))
    for i,pivot in enumerate(pivots):
        terms=eq[masters[int(pivot)]]
        for n,d,c in terms:
            if (n,d) in masters:
                actual_h[i,masters.index((n,d))]+=c
            else:
                assert n in ref_by_node and d==1
                j=int(np.where(selected==ref_by_node[n])[0][0])
                actual_d[i,j]-=c
    S=A[np.ix_(selected,pivots)]
    matrix_residual=float(np.max(np.abs(S@actual_h-A[selected])))
    ref_residual=float(np.max(np.abs(S@actual_d-np.eye(200))))
    assert matrix_residual<1e-10 and ref_residual<1e-10
    # Virtual work: recover each reference channel's nodal reaction from the
    # ACTUAL serialized H,D, then compare its six-component wrench with its
    # original source floor point and unit tangent. No force result is used.
    physical_map=actual_h.T@np.linalg.inv(actual_d.T)
    wrench_map=np.zeros((6,len(masters)))
    for j,(n,d) in enumerate(masters):
        unit=np.eye(3)[d-1]
        wrench_map[:3,j]=unit
        wrench_map[3:,j]=np.cross(np.array(parsed_nodes[n]),unit)
    emitted_reference_wrenches=wrench_map@physical_map
    expected_reference_wrenches=[]
    for original in selected:
        r=references[int(original)]
        axis=np.array(r['owner_tangent_basis_global_xyz'])
        point=np.array(r['owner_floorpoint_xyz_mm'])
        expected_reference_wrenches.append(np.r_[axis,np.cross(point,axis)])
    difference=emitted_reference_wrenches-np.array(expected_reference_wrenches).T
    wrench_force_error=float(np.max(np.abs(difference[:3])))
    wrench_moment_error=float(np.max(np.abs(difference[3:])))
    assert wrench_force_error<1e-9 and wrench_moment_error<1e-6
    F=np.array([cloads.get((n,d),0.) for n,d in [masters[int(p)] for p in pivots]])
    emitted_correction=actual_d.T@F
    declared=np.array([references[int(j)]['source_load_correction_N'] for j in selected])
    load_residual=float(np.max(np.abs(emitted_correction-declared)))
    assert load_residual<1e-8
    result={'status':'PASS_PARENT_SERIALIZED_INPUT_AUDIT','physical_body_count':len(new['physical_body_nodes']),
            'material_constants_orientations_sections_unchanged':True,
            'original_node_serialization_max_error_mm':node_error,
            'source_CLOAD_serialization_max_error_N':load_error,
            'exact_floor_original_constraint_reconstruction_max_error':matrix_residual,
            'exact_floor_reference_transfer_max_error':ref_residual,
            'floor_reference_channel_unit_force_wrench_max_force_error':wrench_force_error,
            'floor_reference_channel_unit_force_wrench_max_moment_error_mm':wrench_moment_error,
            'emitted_vs_declared_reference_source_load_correction_max_error_N':load_residual,
            'distinct_equation_dependent_dofs':len(eq),'dependent_fixed_collision':False,
            'model_sha256':hashlib.sha256((inspected/'model.json').read_bytes()).hexdigest(),
            'deck_sha256':hashlib.sha256((inspected/'model.inp').read_bytes()).hexdigest(),
            'frame_ready_for_native_run':False,'complete_joint_validated':False,
            'limits':['Serialized input only; no frame forces or contact states',
                      'Does not independently qualify material or hardware properties',
                      'Native matrix reaction method and complete response audit must still pass']}
    result['inspected_input_directory']=str(inspected)
    (HERE/output_name).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--input-directory')
    parser.add_argument('--output-name',default='audit.json')
    args=parser.parse_args()
    run(args.input_directory,args.output_name)
