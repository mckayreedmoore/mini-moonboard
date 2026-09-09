"""Actual spread-group mass/contact; same conditional rigid-floor load screen."""
import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

import scipy

from fea.prepare_easy_structural import digest
from fea.rigid_floor_screen import solve
from fea.timber_floor_screen import cases
from fea.wide_structural import locations, mass_state


def run(size, extension, output):
    from mini_moonboard import lumber_leg_spread_frame as candidate

    if output.exists():
        raise FileExistsError("Refusing to overwrite prior leg-floor evidence")
    manifest_path = Path("exports/wide-principal-development/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    sources = dict(manifest["sources"])
    for path in (str(manifest_path), "mini_moonboard/lumber_leg_frame.py",
                 "mini_moonboard/lumber_leg_spread_frame.py", "fea/spread_leg_floor.py", "fea/wide_structural.py",
                 "fea/prepare_easy_structural.py", "fea/timber_floor_screen.py",
                 "fea/rigid_floor_screen.py", "fea/user_load_envelope.py", "uv.lock"):
        sources.setdefault(path, digest(path))
    if not sources or any(digest(p) != h for p, h in sources.items()):
        raise ValueError("Current candidate source identity differs")
    parts = candidate.parts(size, extension, True)
    state = mass_state(parts)
    floor = [[x, y, 0.] for x, y in state["support_polygon_mm"]]
    records = []
    for case in cases(state, locations()):
        results = {str(mu): solve(floor, case["wrench_n_nmm"], mu) for mu in (.1, .2, .4)}
        # Preserve independent force/moment/friction witnesses without repeating
        # identical prose for every solver call.
        for value in results.values():
            value.pop("limits", None)
        records.append({**case, "friction_results": results})
    summary = {str(mu): dict(Counter(r["friction_results"][str(mu)]["status"] for r in records))
               for mu in (.1, .2, .4)}
    report = {"geometry": "spread-100x50-top150", "stock": size, "extra_foot_extension_mm": extension,
        "state": state, "source_sha256": sources, "summary": summary, "cases": records,
        "scipy_version": scipy.__version__,
        "qualified_for_design": False,
        "limits": "Rigid compression-only floor equilibrium, not elastic FEA or joint/column capacity. "
                  "Same prescribed 150/200/250/300lb,1x/2x,80/100% mass,nine hold,0/300N horizontal cases. "
                  "Actual drilled CAD volume/CG/floor hull; assumed600kg/m3 for all wood,7850steel; "
                  "fasteners,inserts,holds,LEDs,glue excluded. No selected lumber density/property claim. "
                  "Assumed mu0.1/0.2/0.4 with16-ray inscribed cones; feasibility gives admissible "
                  "forces, not predicted allocation; polygon infeasibility alone cannot prove circular-cone failure. "
                  "No contact compatibility,floor pressure,nonlinear flexibility,dynamics or approval."}
    if any(digest(p) != h for p, h in sources.items()):
        raise ValueError("Source changed during leg-floor comparison")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(gzip.compress((json.dumps(report, allow_nan=False)+"\n").encode(), mtime=0))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", choices=("2x6", "2x8"))
    parser.add_argument("--extension", type=float, choices=(0., 150., 300.), default=300.)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.size, args.extension, args.output)))

