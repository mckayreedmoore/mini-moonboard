"""Freeze current square-cut CAD for separate stiffness and stability screens."""
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from fea.user_load_envelope import envelope, hull

ROOT = Path("fea/generated/square-cut")
KEYS = ("square-cut-bracket", "square-cut-wood-blocks")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")


def locations():
    from mini_moonboard import box_frame as b
    from mini_moonboard import product_frame as product
    from mini_moonboard.panel_grid import kicker_foothold_datums, main_tnut_datums

    result = [(label, b.point(x-b.HALF, s, -product.FACE_THICKNESS_MM).toTuple(),
               (-b.normal()).toTuple()) for label, (x, s) in main_tnut_datums().items()]
    result += [("kicker_"+label, (x-b.HALF,
                product.KICKER_BACK_Y_MM+product.FACE_THICKNESS_MM,
                b.V1_KICKER_HEIGHT_MM+s), (0., 1., 0.))
               for label, (x, s) in kicker_foothold_datums().items()]
    return result


def mass_state(parts):
    from mini_moonboard.box_exports import exact_bounds

    masses = [p.shape.Volume()/1e9*(7850 if p.name.startswith("clip_mvp_") else 600)
              for p in parts]
    total = sum(masses)
    centre = [sum(m*p.shape.Center().toTuple()[i] for m, p in zip(masses, parts, strict=True))/total
              for i in range(3)]
    floor = [v.Center().toTuple()[:2] for p in parts for f in p.shape.Faces()
             if abs(exact_bounds(f).zmin) < 1e-5 and abs(exact_bounds(f).zmax) < 1e-5
             for v in f.Vertices()]
    return {"mass_kg": total, "centre_xy_mm": centre[:2], "centre_xyz_mm": centre,
            "support_polygon_mm": hull(floor), "part_count": len(parts)}


def summarize(cases):
    return {"case_count": len(cases), "status_counts": dict(Counter(c["status"] for c in cases)),
            "minimum_factor": min(c["governing"]["factor"] for c in cases
                                  if c["governing"]["factor"] is not None),
            "maximum_translational_friction_demand": max(c["translational_friction_demand"] for c in cases)}


def main():
    import cadquery as cq

    from mini_moonboard import easy_blocks, easy_frame
    from mini_moonboard.stability import load_cases

    points = locations()
    for module in (easy_frame, easy_blocks):
        directory = ROOT/module.KEY
        directory.mkdir(parents=True, exist_ok=False)
        manifest_path = Path("exports")/module.KEY/"manifest.json"
        manifest = json.loads(manifest_path.read_text())
        if any(digest(p) != h for p, h in manifest["sources"].items()):
            raise ValueError("Published source closure differs from current CAD")
        # Independent actual drilled inventory for mass/contact, not FE bulk mass.
        state = mass_state(module.parts(True))
        cases = envelope(state, points, (150, 200, 250, 300))
        save(directory/"stability.json", {
            "candidate": module.KEY, "state": state, "cases": cases,
            "summaries": {str(w): summarize([c for c in cases if c["climber_lb"] == w])
                          for w in (150, 200, 250, 300)},
            "assumptions": "Actual drilled wood at assumed600kg/m3; A connector proxies7850kg/m3. Fasteners, holds, LEDs and glue omitted. 0.8/1 mass freezes CG; 1x/2x climber gravity,0/300N horizontal all azimuths,0/50/100mm standoff. Illustrative1.5 edge-moment screen, not governing certified loads. No joint compliance, yaw/friction distribution, uneven floor, strength or approval.",
            "source_sha256": {**manifest["sources"],
                **{p: digest(p) for p in ("fea/prepare_easy_structural.py", "fea/user_load_envelope.py")}},
            "manifest_sha256": digest(manifest_path)})
        # Deliberately optimistic bulk: no mechanical-connection or ply slip.
        items = [p for p in module.parts(False) if not p.name.startswith("clip_mvp_")]
        step = directory/"box_frame_bulk.step"
        cq.exporters.export(cq.Compound.makeCompound([p.shape for p in items]), str(step))
        save(directory/"box_frame_bulk.json", {
            "candidate": module.KEY, "parts": [p.name for p in items],
            "geometry_source_sha256": manifest["sources"], "step_sha256": digest(step),
            "geometry_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "audited_load_targets_mm": [p for label, p, _ in points if label in ("A12", "C12", "F12", "H12", "K12")],
            "audited_cases": [{"name": c.name, "basis": c.basis,
                               "force_n": [0, c.force_y_n, c.force_z_n]} for c in load_cases()],
            "assumptions": "OPTIMISTIC BULK DIAGNOSTIC ONLY: current parts(False), retaining preexisting service reliefs but omitting face/connection drilling; all touching timber including four independent leg plies IDEALLY BONDED; A steel clips and all fasteners omitted and butt interfaces bonded. B blocks bonded, not actual bolted stiffness. Fixed floor XYZ, no self-weight, isotropic E=7000MPa nu=.3, five equal row12 point loads. No joint resistance, orthotropy, net-section, buckling, unanchored contact, dynamic or capacity validation. B/A difference cannot rank real joint strength."})
        print(module.KEY, json.dumps(summarize(cases)), flush=True)


if __name__ == "__main__":
    main()
