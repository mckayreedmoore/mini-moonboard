"""Parent-only freeze utility. This never launches a solver."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,json,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from fea.wood_joint_reduced_native import freeze
BASE=ROOT/'docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28'
def main(source,target):
 source=Path(source).resolve();target=Path(target).resolve()
 m=json.loads((source/'model.json').read_text());assert m['schema']=='current_springa_selected_floor_input_model/v1'
 extras=[Path(__file__),BASE/'current-springa-selected-floor-response-audit-attempt03/response_audit.py',BASE/'current-springa-selected-floor-response-audit-attempt03/method_fixture_check.json',BASE/'current-springa-selected-floor-response-audit-attempt03/verify_method_fixtures.py',BASE/'current-springa-frame-response-audit-attempt01/response_audit.py',BASE/'current-springa-selected-floor-parent-response-audit-attempt01/check.py',BASE/'current-springa-selected-floor-parent-input-audit-attempt03/check.py',BASE/'current-springa-selected-floor-parent-input-audit-attempt03/actual-input-audit.json',BASE/'current-springa-parent-input-audit-attempt01/check.py',source.parent/'prepare.py']
 for path in extras:assert path.is_file(),('Missing frozen source/evidence',str(path))
 s=SimpleNamespace(nodes={int(k):v for k,v in m['nodes'].items()},elements={int(k):v for k,v in m['elements'].items()},loads={int(k):v for k,v in m['loads'].items()},fixed=set(m['fixed_nodes']),equations=m['equations'],springs=copy.deepcopy(m['springs']),panels={k:{'nodes':v} for k,v in m['panel_nodes'].items()},rotation_masters=set(m['rotation_master_nodes']))
 meta=copy.deepcopy(m);meta['scope']='One selected-bearing a12-rear support-branch diagnostic of the reviewed frame; no geometry/law/load change, no physical acceptance or automatic mask iteration.'
 expected=copy.deepcopy(meta)
 for row in expected['springs']:row['active']=True
 packet=freeze(target,s,meta,extra_sources=extras,deck_text=(source/'model.inp').read_text())
 assert json.loads((target/'model.json').read_text())==expected
 print(json.dumps({'directory':str(target),'files_sha256':packet['files_sha256'],'model_changes':['diagnostic scope','standard always-active bilateral flags if previously absent']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source_directory');p.add_argument('target_directory');a=p.parse_args();main(a.source_directory,a.target_directory)
