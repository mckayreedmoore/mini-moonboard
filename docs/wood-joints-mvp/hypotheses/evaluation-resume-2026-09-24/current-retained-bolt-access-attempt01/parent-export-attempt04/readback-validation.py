from pathlib import Path
import hashlib,json,time,traceback
import cadquery as cq
_d6_readback_root=Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04")
_d6_readback_manifest_path=_d6_readback_root/"brep-export/manifest.json"
assert hashlib.sha256(_d6_readback_manifest_path.read_bytes()).hexdigest()=="d90a93440575b7871fc429c3f8cec621877f805a068b7ff09a60fddc4b1e538b"
_d6_readback_manifest=json.loads(_d6_readback_manifest_path.read_text())
_d6_readback_shapes={}
_d6_readback_rows=[]
_d6_readback_start=time.monotonic()
_d6_readback_result={"schema":"wj_d6_step_readback/v1","scope":"STEP validity, solid count, and roundtrip geometric summaries only; no motion or fabrication acceptance","manifest_sha256":"d90a93440575b7871fc429c3f8cec621877f805a068b7ff09a60fddc4b1e538b","linear_summary_tolerance_mm":1e-6,"volume_tolerance_rule":"max(1e-5 mm3,1e-9*source volume)","rows":_d6_readback_rows}
try:
    for row in _d6_readback_manifest["files"]:
        path=_d6_readback_root/"brep-export"/row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row["sha256"]
        shape=cq.importers.importStep(str(path)).val()
        bounds=shape.BoundingBox()
        bounds_values=[bounds.xmin,bounds.xmax,bounds.ymin,bounds.ymax,bounds.zmin,bounds.zmax]
        volume_error=abs(shape.Volume()-row["volume_mm3"])
        bounds_error=max(abs(a-b) for a,b in zip(bounds_values,row["bounds_xyz_mm"]))
        center_error=max(abs(a-b) for a,b in zip(shape.Center().toTuple(),row["center_of_mass_xyz_mm"]))
        passed=shape.isValid() and len(shape.Solids())==row["solid_count"] and volume_error<=max(1e-5,1e-9*row["volume_mm3"]) and bounds_error<=1e-6 and center_error<=1e-6
        _d6_readback_rows.append({"path":row["path"],"passed":passed,"volume_error_mm3":volume_error,"max_bounds_error_mm":bounds_error,"max_center_error_mm":center_error,"solid_count":len(shape.Solids())})
        _d6_readback_shapes[(row["category"],row["shape_id"])]=shape
    _d6_readback_result["status"]="PASS" if len(_d6_readback_rows)==211 and all(r["passed"] for r in _d6_readback_rows) else "FAIL"
except Exception:
    _d6_readback_result["status"]="ERROR"
    _d6_readback_result["traceback"]=traceback.format_exc()
finally:
    _d6_readback_result["elapsed_seconds"]=time.monotonic()-_d6_readback_start
    (_d6_readback_root/"readback-validation.json").write_text(json.dumps(_d6_readback_result,indent=2)+"\n")
    print("D6_STEP_READBACK",_d6_readback_result["status"],len(_d6_readback_rows),_d6_readback_result["elapsed_seconds"],flush=True)
