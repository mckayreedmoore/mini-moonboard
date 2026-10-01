"""Parent independent exact-input and unchanged-physical-gate review; no solve."""
import ast
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def functions(path):
    return {n.name: n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)}

def dump(node):
    return ast.dump(node, include_attributes=False)

def main():
    old = BASE/'current-springa-selected-floor-k12-rear-attempt03'
    new = BASE/'current-springa-k12-rear-spr489-direct-master-input-attempt02'
    packet = BASE/'current-k12-rear-spr489-direct-response-audit-attempt02'
    baseline = json.loads((old/'model.json').read_text())
    variant = json.loads((new/'model.json').read_text())
    changed = [i for i, (a,b) in enumerate(zip(baseline['equations'], variant['equations'], strict=True)) if a != b]
    assert changed == [19433,19434]
    leaves = []
    def diff(a,b,path=''):
        if a == b: return
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(set(a)|set(b)):
                if key not in a or key not in b: leaves.append(path+'/'+key)
                else: diff(a[key],b[key],path+'/'+key)
        elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
            for i,(x,y) in enumerate(zip(a,b)): diff(x,y,path+'/'+str(i))
        else: leaves.append(path)
    diff({k:v for k,v in baseline.items() if k!='equations'}, {k:v for k,v in variant.items() if k!='equations'})
    assert len(leaves)==17
    assert all(p=='/input_method_variant' or p.startswith(('/nonlinear_native_carrier_bindings/488/','/unilateral_springa_bindings/488/')) for p in leaves)
    original = BASE/'current-springa-zero-u-token-response-audit-attempt01/response_audit.py'
    stable = original.with_name('stable_response_audit.py')
    fork = packet/'response_core.py'
    a,c,s = functions(original),functions(fork),functions(stable)
    same = [name for name in a.keys()&c.keys() if dump(a[name])==dump(c[name])]
    required = ['_strict_normal_branch_check','_audit_selected_floor_rows','_inactive_zero_actions','_validate_execution','_validate_model','_validate_case_context']
    assert set(required)<=set(same)
    # Compare all statements through the physical gates, excluding contract
    # acquisition and report rendering. Only the scoped callback is new.
    old_body = a['audit_record'].body[2:-1]
    new_body = c['_audit_record_with_contract'].body[1:]
    report_index = next(i for i,n in enumerate(new_body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report' for t in n.targets))
    new_body = new_body[:report_index]
    class NormalizeCallback(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id=='recover_springa': node.id='audit_springa'
            return node
        def visit_Assign(self,node):
            if any(isinstance(t,ast.Name) and t.id=='recover_springa' for t in node.targets): return None
            return self.generic_visit(node)
    normalized = NormalizeCallback().visit(ast.Module(body=new_body,type_ignores=[]))
    assert dump(ast.Module(body=old_body,type_ignores=[]))==dump(normalized)
    # SPR489 has precisely a different source scalar/radius read; all geometric,
    # constitutive, interval, action/reaction and physical action statements stay.
    old_spring=s['_audit_springa'].body
    new_spring=c['audit_springa_direct_master'].body
    def mechanics(body):
        out=[]
        for n in body:
            if isinstance(n,ast.Assign):
                names=[t.id for t in n.targets if isinstance(t,ast.Name)]
                if any(x in names for x in ['source_q','source_q_radius','scalar_terms','check']): continue
                if any(isinstance(t,ast.Tuple) and any(isinstance(x,ast.Name) and x.id=='source_q' for x in t.elts) for t in n.targets): continue
            out.append(n)
        return ast.Module(body=out,type_ignores=[])
    assert dump(mechanics(old_spring))==dump(mechanics(new_spring))
    # Independent virtual-work force and first-moment transfer from actual
    # emitted two carrier rows, using original physical master coordinates.
    audit=json.loads((new/'input-audit.json').read_text())
    p=audit['source_map_provenance'];axis=p['physical_owner_axis_global_xyz']
    actual={}
    def cross(x,y): return [x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]]
    components=p['carrier_component_equations']
    qmap={}
    for label,j in [('Qy',1),('Qz',2)]:
        for node,dof,coef in components[label][1:]:
            key=(int(node),int(dof));qmap[key]=qmap.get(key,0)+axis[j]*coef
    for side in ['first','second']:
        nodes={int(r['node']) for r in p['source_interpolation_sides'][side]['master_shape_weights']}
        forces={n:[0.,0.,0.] for n in nodes}
        for (n,d),coef in qmap.items():
            if n in nodes: forces[n][d-1]+=coef
        F=[math.fsum(v[j] for v in forces.values()) for j in range(3)]
        moments=[cross(baseline['nodes'][str(n)],v) for n,v in forces.items()]
        M=[math.fsum(v[j] for v in moments) for j in range(3)]
        target=audit['unit_owner_wrench_from_emitted_component_rows']
        assert max(abs(x-y) for x,y in zip(F,target['target_force_xyz_by_physical_owner_N_per_N'][side]))<1e-9
        assert max(abs(x-y) for x,y in zip(M,target['target_moment_global_origin_xyz_by_physical_owner_Nmm_per_N'][side]))<1e-8
        actual[side]={'force_N_per_N':F,'moment_Nmm_per_N':M}
    files=[original,stable,fork,new/'model.json',new/'model.inp',new/'input-audit.json',packet/'validate_direct_master_input.py',Path(__file__)]
    report={'status':'PASS_PARENT_EXACT_INPUT_AND_UNCHANGED_PHYSICAL_GATES_REVIEW','changed_model_equation_rows':changed,'non_equation_changed_paths':leaves,'unchanged_functions':sorted(same),'all_physical_audit_statements_unchanged_except_scoped_callback':True,'direct_spring_geometric_law_intervals_and_physical_action_statements_unchanged':True,'independent_owner_unit_wrenches':actual,'source_sha256':{str(f):sha(f) for f in files},'native_solve_executed':False,'mechanical_acceptance':False}
    (HERE/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(report['status'])

if __name__=='__main__': main()
