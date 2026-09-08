"""Current-CAD rigid-body screen and gross-section geometry; not strength FEA."""
import json
from pathlib import Path

from fea.prepare_easy_structural import digest, locations, mass_state, summarize
from fea.user_load_envelope import envelope

OUTPUT = Path("fea/results/lean-frame/report.json")
WEIGHTS = (150, 200, 250, 300)
SCREEN_SOURCES = (
    "fea/lean_screen.py", "fea/prepare_easy_structural.py", "fea/user_load_envelope.py",
)
ASSUMPTIONS = [
    "Not FEA, connection qualification, a user rating or construction approval.",
    ("Actual drilled CAD wood at assumed 600 kg/m3; clip proxies at 7850 kg/m3. "
    "Fasteners, holds, LEDs, wiring and glue mass omitted; no ballast or anchors."),
    ("One climber; 250 lb intended maximum, 300 lb sensitivity, not established ratings. "
    "150/200/250/300 lb, 1x/2x downward gravity, 0/300 N horizontal force over all azimuths, "
    "0/50/100 mm outward hold standoff, and 80%/100% included mass with fixed centre of mass."),
    ("The 1.5 edge-moment target and selected loads are screening assumptions, not a "
    "complete governing load basis. Opposite board-normal/upward exploratory loads are "
    "not in this downward-force envelope; their historical failures are not superseded."),
    ("Rigid body and convex hull of actual coplanar CAD floor contacts. No flexible "
    "connections, contact opening solution, uneven floor, dynamic response, yaw equilibrium "
    "or distribution of friction among feet. Aggregate friction demand is not a sliding pass."),
    ("Member ratios use equal elastic modulus and gross rectangular dimensions only. "
    "No holes, counterbores, local bearing, orthotropy, grades, splitting, buckling, joint "
    "slip, bolt/screw resistance, panel head pull-through, washer bearing, ply sharing, "
    "kicker splice, cyclic loading or whole-frame displacement/capacity is qualified."),
]


def section_comparison():
    """Same depth, reduced width; local axes are transverse width and rear normal."""
    old_width, new_width, depth = 88.9, 38.1, 139.7

    def section(width):
        return {
            "width_mm": width, "rear_normal_depth_mm": depth,
            "area_mm2": width*depth,
            "I_out_of_plane_mm4": width*depth**3/12,
            "I_in_plane_mm4": depth*width**3/12,
            "Z_out_of_plane_mm3": width*depth**2/6,
            "Z_in_plane_mm3": depth*width**2/6,
        }

    old, new = section(old_width), section(new_width)
    return {
        "old_nominal_4x6": old, "new_nominal_2x6": new,
        "new_over_old_ratios": {key: new[key]/old[key] for key in old
                                if key not in ("width_mm", "rear_normal_depth_mm")},
        "interpretation": "Equal-modulus gross-section geometric ratios only, not resistance "
        "or whole-frame stiffness ratios. Actual spans, support locations and connections differ.",
    }


def candidate_report(state, points):
    cases = envelope(state, points, WEIGHTS)
    return {
        "state": state, "cases": cases,
        "summaries": {str(weight): summarize([c for c in cases if c["climber_lb"] == weight])
                      for weight in WEIGHTS},
    }


def manifest_sources(path):
    sources = json.loads(path.read_text())["sources"]
    if not sources or any(digest(source) != sha for source, sha in sources.items()):
        raise ValueError("Published source closure differs from current CAD")
    return sources


def main():
    from mini_moonboard import lean_frame

    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite frozen evidence: {OUTPUT}")
    report = {
        "scope": "Rigid-body stability sensitivity and gross member geometry only; no FEA pass",
        "assumptions": ASSUMPTIONS, "climber_weights_lb": WEIGHTS,
        "gross_member_sections": section_comparison(), "candidates": {},
        "source_sha256": {source: digest(source) for source in SCREEN_SOURCES},
    }
    points = locations()
    manifests = {}
    for module in (lean_frame,):
        path = Path("exports")/module.KEY/"manifest.json"
        sources = manifest_sources(path)
        manifest_sha = digest(path)
        entry = candidate_report(mass_state(module.parts(True)), points)
        entry["mass_by_part_kg"] = {p.name: p.shape.Volume()/1e9*(7850 if p.name.startswith("clip_mvp_") else 600) for p in module.parts(True)}
        entry.update(source_sha256=sources, manifest_sha256=manifest_sha)
        report["candidates"][module.KEY] = entry
        manifests[str(path)] = manifest_sha
        print(module.KEY, json.dumps(entry["summaries"]), flush=True)
    # Long CAD generation must not silently mix changing inputs from another worker.
    all_sources = dict(report["source_sha256"])
    for entry in report["candidates"].values():
        all_sources.update(entry["source_sha256"])
    if any(digest(path) != sha for path, sha in {**all_sources, **manifests}.items()):
        raise ValueError("Source or manifest changed during screening")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()

