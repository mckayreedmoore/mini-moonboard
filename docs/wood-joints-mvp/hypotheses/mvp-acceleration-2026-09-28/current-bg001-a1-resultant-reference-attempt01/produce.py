"""Reuse unchanged conditional single-shear resistance for A1's own vectors."""
from pathlib import Path
import hashlib, importlib.util, json
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
METHOD = BASE / 'current-corner-resultant-direction-single-shear-attempt01/produce.py'
REPORT = BASE / 'current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json'
AUDIT = BASE / 'current-corner-a1-parent-export-audit-attempt01/audit.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert sha(METHOD) == 'd14ece8fd0d32e790e4f3de67aa8d860e6881231d6421b650e5b47f699aab57f'
    report = json.loads(REPORT.read_text()); audit = json.loads(AUDIT.read_text())
    assert sha(REPORT) == '2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce'
    assert audit['report_sha256'] == sha(REPORT)
    assert audit['status'] == 'PASS_PARENT_CORNER_INVENTORY_AND_EXACT_SIGNED_FORCE_AUDIT'
    assert report['case_id'] == 'a1-rear' and report['actual_case_demand_usable_for_conditional_joint_checks']
    spec = importlib.util.spec_from_file_location('unchanged_reference_method', METHOD)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    sources = m.validate_and_load_sources()  # Reviewed geometry/basis only, no A12 force adoption.
    nds = m.load_module('a1_reference_nds', m.NDS_PRODUCER)
    fe = m.load_module('a1_reference_fe', m.FE_HELPER)
    basis = sources['bg001_source']['conditional_single_bolt_basis']
    d = float(basis['diameter_in']); lm, ls = map(float, basis['main_and_side_bearing_lengths_in'])
    rows = []
    for bolt in report['increments'][-1]['primary_physical_bolt_groups']['BG001']['bolts']:
        action = m.action_for(bolt, 'candidate_bolt_lateral_plane')
        vectors = {member: m.force_on(action, member) for member in m.MEMBER_ROLES['BG001'].values()}
        main, side = m.MEMBER_ROLES['BG001']['main'], m.MEMBER_ROLES['BG001']['side']
        assert m.vector_close(vectors[main], [-x for x in vectors[side]])
        angles = {member: m.angle_to_grain_deg(v, sources['grain_by_member'][member]) for member,v in vectors.items()}
        bearing = {member: float(fe.dfl_dowel_bearing_psi(d, angles[member])) for member in vectors}
        result = nds.calculate(d, lm, ls, bearing[main], bearing[side], max(angles.values()))
        refs = {k: float(v)*m.N_PER_LBF for k,v in result['reference_values_lbf'].items()}
        mode = min(refs, key=refs.get); demand = m.norm(vectors[main])
        rows.append({'axis_id':bolt['axis_id'], 'force_on_members_xyz_N':vectors,
                     'grain_angles_deg':angles, 'Fe_psi':bearing, 'six_mode_references_N':refs,
                     'governing_mode':mode, 'unadjusted_reference_N':refs[mode],
                     'lateral_resultant_N':demand, 'demand_to_unadjusted_reference':demand/refs[mode]})
    pins = {str(p):sha(p) for p in [METHOD, REPORT, AUDIT, Path(__file__), *m.SOURCE_PATHS.values()]}
    out = {'schema':'current_bg001_a1_resultant_reference/v1','case_id':'a1-rear',
           'status':'CONDITIONAL_UNADJUSTED_SINGLE_SHEAR_REFERENCES_ONLY','source_sha256':pins,'rows':rows,
           'limits':['Recorded conditional Fe/Fyb/quarter-inch smooth-shank basis reused, not product or block qualification.',
                     'Signed loaded end/edge, Cdelta, mixed-direction group/splitting, axial interaction and washers are not covered.',
                     'Full-load A1 vectors only; no six-case envelope or joint acceptance.'], 'joint_accepted':False}
    (HERE/'screen.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(rows))
if __name__ == '__main__': main()
