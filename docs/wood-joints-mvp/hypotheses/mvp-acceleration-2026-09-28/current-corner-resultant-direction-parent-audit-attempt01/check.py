"""Independent resultant-angle/reference arithmetic; no imported yield helpers."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[5]
BASE=Path(__file__).resolve().parent.parent
SOURCE=BASE/'current-corner-resultant-direction-single-shear-attempt01/resultant-direction-screen.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-10),(a,b)
def main():
 d=json.loads(SOURCE.read_text())
 assert not d['mechanical_acceptance'] and not d['design_qualification'] and not d['native_solve_launched']
 for path,want in d['input_provenance']['source_sha256'].items():assert sha(ROOT/path)==want,path
 rows=[]
 for group in ('BG001','BG045'):
  for r in d['results'][group]:
   f=r['reported_lateral_action_on_main_xyz_N'];n=math.sqrt(math.fsum(v*v for v in f));close(n,r['lateral_resultant_demand_N'])
   angles={};fes={}
   for member,g in r['source_proposed_grain_unit_global_xyz'].items():
    close(math.sqrt(math.fsum(v*v for v in g)),1)
    c=min(1,abs(math.fsum(a*b for a,b in zip(f,g)))/n)
    theta=math.degrees(math.acos(c));angles[member]=theta
    fe=5600*4450/(5600*(1-c*c)+4450*c*c);fes[member]=fe
    close(theta,r['load_to_grain_angle_deg'][member]);close(fe,r['bearing_basis']['Fe_by_member_psi'][member])
   m=r['main_member'];s=r['side_member'];ins=r['single_shear_method_inputs'];D=ins['diameter_full_body_smooth_shank_in'];close(D,.25);close(ins['bolt_bending_yield_psi'],45000);close(ins['interface_gap_in'],0)
   K=1+.25*max(angles.values())/90;close(K,ins['theta_factor'])
   iv=D*D/(3.2*K)*math.sqrt(2*fes[m]*45000/(3*(1+fes[m]/fes[s])))
   close(iv,r['six_lateral_yield_modes']['unadjusted_reference_values_lbf']['IV'])
   rawN=iv*4.4482216152605;factor=1 if group=='BG001' else .67;close(factor,r['Ceg_factor']);adjN=rawN*factor
   close(rawN,r['governing_unadjusted_reference_N']);close(adjN,r['conditional_governing_reference_after_Ceg_only_N']);ratio=n/adjN;close(ratio,r['resultant_demand_over_governing_reference_after_Ceg_only'])
   assert r['governing_mode']=='IV' and set(r['six_lateral_yield_modes']['unadjusted_reference_values_lbf'])=={'Im','Is','II','IIIm','IIIs','IV'}
   assert min(r['six_lateral_yield_modes']['unadjusted_reference_values_lbf'],key=r['six_lateral_yield_modes']['unadjusted_reference_values_lbf'].get)=='IV'
   rows.append({'axis_id':r['axis_id'],'independent_resultant_N':n,'independent_angles_deg':angles,'independent_Fe_psi':fes,'independent_Mode_IV_N':rawN,'Ceg_only_reference_N':adjN,'conditional_lateral_resultant_reference_ratio':ratio})
 assert len(rows)==4
 out={'status':'PASS_PARENT_FOUR_RESULTANT_DIRECTION_ARITHMETIC_ONLY','source_screen_sha256':sha(SOURCE),'parent_script_sha256':sha(Path(__file__)),'results':rows,'joint_accepted':False,'axial_group_splitting_checks_completed':False}
 (Path(__file__).parent/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
