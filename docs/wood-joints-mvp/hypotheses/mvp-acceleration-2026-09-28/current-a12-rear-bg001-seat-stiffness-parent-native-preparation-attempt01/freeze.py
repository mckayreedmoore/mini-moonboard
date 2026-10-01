"""Parent exact-byte sensitivity freeze; no native launch."""
import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from fea.wood_joint_reduced_native import digest, verify, write_json, validate_numeric_fields

BASE = Path(__file__).resolve().parent.parent
PREP = BASE/'current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01'
DEST = BASE/'current-a12-rear-bg001-seat-stiffness-native-attempt01'

def main():
    contract = json.loads((PREP/'readiness-contract.json').read_text())
    manifest = json.loads((PREP/'source-snapshot-manifest.json').read_text())
    assert contract['parent_native_readiness'] is False
    sources = dict(manifest['source_snapshots'])
    item = manifest['readiness_contract_snapshot']
    sources[item['repository_relative_path']] = item['sha256']
    assert contract['frozen_source_snapshot_sha256'] == manifest['source_snapshots']
    for name,sha in sources.items():
        assert digest(ROOT/name) == sha and digest(PREP/'sources'/name) == sha,name
    inputs = contract['prepared_inputs']
    model = ROOT/inputs['model_json_path']; deck = ROOT/inputs['deck_path']
    assert digest(model)==inputs['model_json_sha256'] and digest(deck)==inputs['deck_sha256']
    validate_numeric_fields(deck.read_text())
    profile = json.loads((ROOT/'fea/calculix_223/solver-profile.json').read_text())
    assert digest(ROOT/profile['manual']['local_path']) == profile['manual']['sha256']
    # Method review and exact input mutation/negative-response checks were
    # independently executed by parent before this concrete freeze.
    review = json.loads((BASE/'current-sensitivity-response-core-parent-review-attempt01/final-method-review.json').read_text())
    assert review['status']=='PASS_PARENT_FINAL_SENSITIVITY_METHOD_REVIEW'
    DEST.mkdir(exist_ok=False)
    shutil.copyfile(model,DEST/'model.json');shutil.copyfile(deck,DEST/'model.inp')
    shutil.copytree(PREP/'sources',DEST/'sources')
    shutil.copyfile(PREP/'source-snapshot-manifest.json',DEST/'readiness-source-snapshot-manifest.json')
    own = str(Path(__file__).resolve().relative_to(ROOT))
    own_snapshot = DEST/'sources'/own;own_snapshot.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path(__file__),own_snapshot);sources[own]=digest(Path(__file__))
    packet={'schema':'wood_joint_reduced_native_freeze/v1',
            'scope':'One conditional A12-rear BG001 two-tie stiffness sensitivity; provisional floor25 mask; no acceptance',
            'candidate':'compact-floor-flush-wood-joints-development',
            'geometry_revision_id':'led-clearance-2x6-runner-seated-blocks-v1','case_id':'a12-rear',
            'solver_profile':profile,'source_sha256':sources,
            'files_sha256':{name:digest(DEST/name) for name in ['model.json','model.inp','readiness-source-snapshot-manifest.json']},
            'native_solve_executed':False,'mechanical_acceptance':False}
    write_json(DEST/'freeze.json',packet);verify(DEST)
    write_json(DEST/'parent-readiness-review.json',{
        'input_freeze_sha256':digest(DEST/'freeze.json'),'ready_for_scoped_native_run':True,
        'scope':packet['scope'],'max_launches':1,'no_automatic_mask_iteration':True,
        'all_unchanged_physical_gates_required':True,'independent_all50_audit_required':True,
        'standard_711_case_context_claimed':False,'mechanical_acceptance':False,
        'method_review_sha256':digest(BASE/'current-sensitivity-response-core-parent-review-attempt01/final-method-review.json')})
    print('Parent froze exact sensitivity bytes:',DEST)

if __name__=='__main__':
    main()
