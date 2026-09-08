"""Freeze bearing-frame CAD for separate moment and optimistic stiffness screens."""
import json
import subprocess
from pathlib import Path

from fea.prepare_easy_structural import digest, locations, mass_state, save, summarize
from fea.user_load_envelope import envelope

DIRECTORY = Path("fea/generated/bearing-frame")
STABILITY = Path("fea/results/bearing-frame/stability.json")


def main():
    import cadquery as cq

    from mini_moonboard import bearing_frame as frame
    from mini_moonboard.stability import load_cases

    if DIRECTORY.exists() or STABILITY.exists():
        raise FileExistsError("Refusing to overwrite frozen bearing-frame evidence")
    manifest_path = Path("exports")/frame.KEY/"manifest.json"
    manifest = json.loads(manifest_path.read_text())
    sources = dict(manifest["sources"])
    if not sources or any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Published geometry sources differ")
    sources.update({p: digest(p) for p in (
        "fea/prepare_bearing_structural.py", "fea/prepare_easy_structural.py",
        "fea/user_load_envelope.py", "mini_moonboard/stability.py", str(manifest_path))})
    points = locations()
    state = mass_state(frame.parts(True))
    cases = envelope(state, points, (150, 200, 250, 300))
    report = {"candidate": frame.KEY, "state": state, "cases": cases,
        "source_sha256": sources,
        "summaries": {str(w): summarize([c for c in cases if c["climber_lb"] == w])
                      for w in (150, 200, 250, 300)},
        "assumptions": "Moment screen only, not capacity or approval. Drilled wood600kg/m3, steel7850kg/m3; holds/fasteners/LED/glue omitted. 80/100% mass at fixed CG, 1x/2x gravity, 0/300N horizontal all azimuths, 0/50/100mm standoff. No sliding/contact/yaw/dynamics/joint qualification."}
    items = [p for p in frame.parts(False) if not p.name.startswith("clip_mvp_")]
    DIRECTORY.mkdir(parents=True)
    step = DIRECTORY/"box_frame_bulk.step"
    cq.exporters.export(cq.Compound.makeCompound([p.shape for p in items]), str(step))
    info = {"candidate": frame.KEY, "parts": [p.name for p in items],
        "geometry_source_sha256": sources, "step_sha256": digest(step),
        "cad_unfragmented_volume_mm3": sum(p.shape.Volume() for p in items),
        "geometry_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "audited_load_targets_mm": [p for label, p, _ in points if label in ("A12", "C12", "F12", "H12", "K12")],
        "audited_cases": [{"name": c.name, "basis": c.basis,
                           "force_n": [0, c.force_y_n, c.force_z_n]} for c in load_cases()],
        "assumptions": "Optimistic undrilled isotropic ideally bonded timber, steel and fasteners omitted; fixed floor XYZ and no gravity. Five equally loaded row12 points. No joint, strength, buckling, unanchored contact or construction approval."}
    if any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Source changed during preparation")
    save(DIRECTORY/"box_frame_bulk.json", info)
    STABILITY.parent.mkdir(parents=True, exist_ok=True)
    save(STABILITY, report)
    print(json.dumps(report["summaries"]), flush=True)


if __name__ == "__main__":
    main()
