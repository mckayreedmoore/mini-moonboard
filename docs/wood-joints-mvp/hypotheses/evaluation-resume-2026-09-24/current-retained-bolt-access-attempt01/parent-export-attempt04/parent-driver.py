from pathlib import Path
import hashlib,json,runpy,time,traceback
_d6_parent=Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04")
_d6_source=_d6_parent/"producer.py.snapshot"
assert hashlib.sha256(_d6_source.read_bytes()).hexdigest()=="12b77a1e53f1a24db9b72f04e2c06b0933dfcfd8574a5eac3abb6986b6b93fd2"
_d6_freeze_path=Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json")
assert hashlib.sha256(_d6_freeze_path.read_bytes()).hexdigest()=="0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187"
_d6_freeze=json.loads(_d6_freeze_path.read_text())
_d6_start=time.monotonic()
_d6_record={"schema":"wj_d6_parent_export_execution/v1","producer_sha256":"12b77a1e53f1a24db9b72f04e2c06b0933dfcfd8574a5eac3abb6986b6b93fd2","status":"running","native_solve_run":False,"geometry_mutation_authorized":False,"live_session":37771}
try:
    _d6_exporter=runpy.run_path(str(_d6_source))["export_d6_member_breps"]
    _d6_manifest=_d6_exporter(g24_outer_2x6,_d6_freeze,_d6_parent/"brep-export")
    assert _d6_manifest["exported_counts"]=={"original_timber_member_shapes":20,"retained_frame_bolt_stacks":12,"retained_frame_bolt_physical_roles":60,"modeled_wire_shapes":131,"step_files":211}
    _d6_record["status"]="completed"
    _d6_record["counts"]=_d6_manifest["exported_counts"]
    _d6_record["manifest_sha256"]=hashlib.sha256((_d6_parent/"brep-export/manifest.json").read_bytes()).hexdigest()
except Exception:
    _d6_record["status"]="failed"
    _d6_record["traceback"]=traceback.format_exc()
finally:
    _d6_record["elapsed_seconds"]=time.monotonic()-_d6_start
    (_d6_parent/"execution.json").write_text(json.dumps(_d6_record,indent=2)+"\n")
    print("D6_EXPORT_RESULT",json.dumps(_d6_record),flush=True)
