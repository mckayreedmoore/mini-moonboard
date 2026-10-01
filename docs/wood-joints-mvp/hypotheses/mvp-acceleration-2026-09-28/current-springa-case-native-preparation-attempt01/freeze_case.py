"""Parent freeze of one source-bound all-bearing diagnostic; never launches."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from fea.wood_joint_reduced_native import freeze
BASE=ROOT/'docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28'
CONTROLS='*CONTROLS,PARAMETERS=TIME INCREMENTATION\n40,40,9,40,10,4,0,0\n0.25,0.5,0.75,0.85,,,1.5\n'
def run(source,target):
 source=Path(source).resolve();target=Path(target).resolve();m=json.loads((source/'model.json').read_text());deck=(source/'model.inp').read_text()
 assert m['schema']=='current_springa_frame_input_model/v1'
 assert deck.count('*STEP,NLGEOM,NLGEOM=NO,INC=40')==1 and '*CONTROLS' not in deck
 original=deck;deck=deck.replace('*STATIC\n',CONTROLS+'*STATIC\n');assert deck.replace(CONTROLS,'')==original
 m['scope']='One case-specific all-bearing support diagnostic only; no mask or historical response transfer.'
 m['conditional_native_numerical_controls']={'source':'Pinned CCX2.23 documentation and prior controls diagnosis','I0':40,'IR':40,'IC':40,'IA':0,'FIELD_tolerances_changed':False,'native_physics_changed':False}
 s=SimpleNamespace(nodes={int(k):v for k,v in m['nodes'].items()},elements={int(k):v for k,v in m['elements'].items()},loads={int(k):v for k,v in m['loads'].items()},fixed=set(m['fixed_nodes']),equations=m['equations'],springs=copy.deepcopy(m['springs']),panels={k:{'nodes':v} for k,v in m['panel_nodes'].items()},rotation_masters=set(m['rotation_master_nodes']))
 extras=[Path(__file__),source.parent/'prepare_six_cases.py',source/'audit.json',source/'source-pins.json',BASE/'current-springa-six-case-parent-input-audit-attempt01/check.py',BASE/'current-springa-frame-response-audit-attempt01/response_audit.py',BASE/'current-six-case-source-load-register-attempt01/register.json',BASE/'current-springa-selected-floor-response-audit-attempt03/method_fixture_check.json',BASE/'current-springa-frame-first-increment-diagnosis-attempt01/README.md']
 for x in extras:assert x.is_file(),x
 result=freeze(target,s,m,extra_sources=extras,deck_text=deck)
 expected=copy.deepcopy(m)
 for row in expected['springs']:row['active']=True
 assert json.loads((target/'model.json').read_text())==expected
 print(json.dumps({'case_id':m['case_id'],'files_sha256':result['files_sha256'],'controls_only':True}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('target');a=p.parse_args();run(a.source,a.target)
