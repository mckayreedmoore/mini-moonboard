from pathlib import Path
from types import SimpleNamespace
import copy, json
from fea.wood_joint_reduced_native import freeze
ROOT=Path(__file__).resolve().parents[5]
BASE=ROOT/"docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
SOURCE=BASE/"current-springa-frame-a12-rear-attempt01"
TARGET=BASE/"current-springa-frame-a12-rear-controls-attempt01"
CONTROL="*CONTROLS,PARAMETERS=TIME INCREMENTATION\n40,40,9,40,10,4,0,0\n0.25,0.5,0.75,0.85,,,1.5\n"
def main():
    model=json.loads((SOURCE/"model.json").read_text())
    old=(SOURCE/"model.inp").read_text()
    marker="*STEP,NLGEOM,NLGEOM=NO,INC=40\n"
    assert old.count(marker)==1 and "*CONTROLS" not in old
    deck=old.replace(marker,marker+CONTROL)
    assert deck.replace(CONTROL,"")==old
    structure=SimpleNamespace(nodes={int(k):v for k,v in model["nodes"].items()},elements={int(k):v for k,v in model["elements"].items()},loads={int(k):v for k,v in model["loads"].items()},fixed=set(model["fixed_nodes"]),equations=model["equations"],springs=copy.deepcopy(model["springs"]),panels={k:{"nodes":v} for k,v in model["panel_nodes"].items()},rotation_masters=set(model["rotation_master_nodes"]))
    metadata=copy.deepcopy(model)
    metadata["scope"]="One current a12-rear diagnostic with identical physical input and delayed divergence controls; at most40 Newton iterations per increment, zero cutbacks, no acceptance transfer."
    extras=[Path(__file__),BASE/"current-springa-frame-response-audit-attempt01/response_audit.py",BASE/"current-springa-frame-response-audit-attempt01/method_fixture_check.json",BASE/"current-springa-parent-input-audit-attempt01/check.py",BASE/"current-springa-parent-cutback-pattern-attempt01/pattern.json"]
    packet=freeze(TARGET,structure,metadata,extra_sources=extras,deck_text=deck)
    actual=json.loads((TARGET/"model.json").read_text())
    expected=copy.deepcopy(model);expected["scope"]=metadata["scope"]
    assert actual==expected
    print(json.dumps({"files_sha256":packet["files_sha256"],"only_model_change":"diagnostic scope","only_deck_change":CONTROL}))
if __name__=="__main__":main()
