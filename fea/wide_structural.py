"""Source-bound wide-principal moment and optimistic bulk-stiffness diagnostics.

This wrapper reuses the validated numerical solver without changing its frozen
bearing-frame inputs or code. It does not perform connection/contact capacity FEA.
"""
import argparse
import json
import subprocess
from dataclasses import replace
from pathlib import Path

from fea import prepare_easy_structural as common
from fea import solve_bearing_frame as solver
from fea.user_load_envelope import envelope

KEY = "wide-principal-development"
DIRECTORY = Path("fea/generated/wide-principal")
STABILITY = Path("fea/results/wide-principal/stability.json")
LIMITS = (
    "Optimistic isotropic bulk stiffness diagnostic only; NOT full connection FEA. "
    "Service pockets, housings and plywood gussets retained; face bores and all "
    "fastener bores omitted. Touching timber interfaces and separate leg plies "
    "ideally bonded, including leg-to-upper-panel edge contact; steel clips and "
    "fasteners omitted. All floor nodes fixed XYZ; "
    "no gravity, separation, slip, actual connector compliance, material strength, "
    "buckling, unanchored contact or approval. Five equally loaded corrected-grid "
    "row-12 nodes; reported displacement is their maximum, not whole-frame or "
    "single-hold displacement. Straight-sided quadratic elements facet curved "
    "boundaries; gross volume agreement is not local stress or convergence proof."
)


def locations():
    """Use the versioned panel-edge policy, never inherited historical datums."""
    from mini_moonboard import box_frame as b
    from mini_moonboard import panel_grid_v2 as grid
    from mini_moonboard import product_frame as product

    points = [(label, b.point(x-b.HALF, s, -product.FACE_THICKNESS_MM).toTuple(),
               (-b.normal()).toTuple()) for label, (x, s) in grid.main_tnut_datums().items()]
    points += [("kicker_"+label, (x-b.HALF,
                product.KICKER_BACK_Y_MM+product.FACE_THICKNESS_MM,
                b.V1_KICKER_HEIGHT_MM+s), (0., 1., 0.))
               for label, (x, s) in grid.kicker_foothold_datums().items()]
    return points


def mass_state(parts):
    """Reuse exact mass/contact math with explicit current steel-name mapping."""
    # The legacy helper classifies clip_mvp_ as steel. Rename only its temporary
    # inputs, never CAD identities or exports. Inserts are explicitly excluded.
    return common.mass_state([replace(p, name="clip_mvp_"+p.name)
                              if p.name.startswith("clip_timber_") else p for p in parts
                              if not p.name.startswith("insert_")])


def bulk_parts(frame):
    """Omit face/fastener drilling, not the newly designed timber service pockets."""
    undrilled = {p.name: p for p in frame.wood_parts(False)}
    parts = {p.name: replace(p, shape=undrilled[p.name].shape)
             if p.name.startswith(("main_", "kicker_")) else p
             for p in frame.wood_parts(True)}
    # The already ideal-bonded pair is one rectangular section. Constructing
    # that same section directly avoids duplicate coincident imported faces at
    # the seam; generic OCC deduplication did not heal them. Physical CAD stays
    # two pieces, and no connection strength is implied by this FE-only union.
    if any(name.startswith("base_rail_mid_") for name in parts):
        import cadquery as cq

        from mini_moonboard import box_frame as b
        from mini_moonboard import panel_grid_v2 as grid

        for side in ("left", "right"):
            lower = parts.pop(f"base_rail_mid_lower_{side}")
            upper = parts.pop(f"base_rail_mid_upper_{side}")
            bounds = lower.shape.BoundingBox()
            x0, x1 = bounds.xmin, bounds.xmax
            shape = b.block(x0, x1, b.HALF-38.1, b.HALF+38.1, 0., 139.7)
            for x, s in grid.main_led_datums().values():
                if abs(s-b.HALF) < 40 and x0-20 < x-b.HALF < x1+20:
                    shape = shape.cut(cq.Solid.makeCylinder(20., 45., b.point(x-b.HALF, s, 0), b.normal()))
            if abs(shape.Volume()-lower.shape.Volume()-upper.shape.Volume()) > .01:
                raise ValueError("Canonical midpoint pair changes material volume")
            name = f"bulk_mid_pair_{side}"
            parts[name] = replace(lower, name=name, shape=shape.clean())
    return tuple(parts.values())


def prepare():
    if DIRECTORY.exists() or STABILITY.exists():
        raise FileExistsError("Refusing to overwrite frozen wide-principal evidence")
    import cadquery as cq

    from mini_moonboard import wide_frame as frame
    from mini_moonboard.stability import load_cases

    manifest_path = Path("exports")/KEY/"manifest.json"
    manifest = json.loads(manifest_path.read_text())
    sources = dict(manifest["sources"])
    if (manifest["design"]["key"] != KEY or frame.KEY != KEY or not sources
            or any(common.digest(p) != sha for p, sha in sources.items())):
        raise ValueError("Published wide-principal geometry/source identity differs")
    sources.update({p: common.digest(p) for p in (
        "fea/wide_structural.py", "fea/prepare_easy_structural.py",
        "fea/user_load_envelope.py", "mini_moonboard/stability.py",
        "mini_moonboard/panel_grid_v2.py", str(manifest_path))})
    points = locations()
    state = mass_state(frame.parts(True))
    cases = envelope(state, points, (150, 200, 250, 300))
    report = {"candidate": KEY, "state": state, "cases": cases,
        "source_sha256": sources,
        "summaries": {str(w): common.summarize([c for c in cases if c["climber_lb"] == w])
                      for w in (150, 200, 250, 300)},
        "assumptions": "Moment screen only, not capacity or approval. Current drilled timber600kg/m3 "
        "and clip_timber_ steel7850kg/m3; insert bodies/fasteners/holds/LED/glue omitted; "
        "drilled wood uses display insert-OD reservations, not installation pilots. Corrected panel_grid_v2 "
        "locations. 80/100% included mass at fixed CG, 1x/2x gravity, 0/300N horizontal all "
        "azimuths, 0/50/100mm standoff. No sliding/contact/yaw/dynamics/joint qualification."}
    items = bulk_parts(frame)
    DIRECTORY.mkdir(parents=True)
    step = DIRECTORY/"box_frame_bulk.step"
    cq.exporters.export(cq.Compound.makeCompound([p.shape for p in items]), str(step))
    info = {"candidate": KEY, "parts": [p.name for p in items],
        "geometry_source_sha256": sources, "step_sha256": common.digest(step),
        "cad_unfragmented_volume_mm3": sum(p.shape.Volume() for p in items),
        "geometry_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "audited_load_targets_mm": [p for label, p, _ in points
                                    if label in ("A12", "C12", "F12", "H12", "K12")],
        "audited_cases": [{"name": c.name, "basis": c.basis,
                           "force_n": [0, c.force_y_n, c.force_z_n]} for c in load_cases()],
        "assumptions": LIMITS}
    if any(common.digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Source changed during wide-principal preparation")
    common.save(DIRECTORY/"box_frame_bulk.json", info)
    STABILITY.parent.mkdir(parents=True, exist_ok=True)
    with STABILITY.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps(report["summaries"]), flush=True)


def run(size, modulus=7000.):
    previous = solver.KEY, solver.DIRECTORY, solver.LIMITS
    try:
        solver.KEY, solver.DIRECTORY, solver.LIMITS = KEY, DIRECTORY, LIMITS
        solver.run(size, modulus)
    finally:
        solver.KEY, solver.DIRECTORY, solver.LIMITS = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    solve = commands.add_parser("solve")
    solve.add_argument("--size", type=float, choices=(60., 40.), required=True)
    solve.add_argument("--modulus", type=float, default=7000.)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        run(args.size, args.modulus)


if __name__ == "__main__":
    main()
