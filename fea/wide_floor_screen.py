"""Current-wide rigid floor equilibrium using the existing finite scenario screen."""
import gzip
import json
from collections import Counter
from pathlib import Path

import scipy

from fea.prepare_easy_structural import digest
from fea.rigid_floor_screen import solve
from fea.timber_floor_screen import cases
from fea.wide_structural import locations

SOURCE = Path("fea/results/wide-principal/stability.json")
OUTPUT = Path("fea/results/wide-floor-screen.json.gz")
MUS = (.1, .2, .4)
LIMITS = (
    "Rigid whole frame on level floor; compression-only floor-hull vertex forces; "
    "16-ray inscribed friction cones, with assumed not measured coefficients. "
    "1296 finite cases: 150/200/250/300lb, 1x/2x weight, 80/100% included mass "
    "at fixed CG, nine holds at 100mm outward standoff, zero or 300N horizontal "
    "at eight 45deg directions. Not all hold positions or azimuths. Included mass "
    "and floor hull inherited from authenticated current-wide stability evidence. "
    "No contact compatibility, pressure limits, flexibility, dynamics, connection "
    "capacity or approval. Feasible reactions are witnesses, not predicted joint "
    "loads. Inscribed-polygon infeasibility does not prove circular-cone failure."
)


def run():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite published floor-screen evidence")
    source = json.loads(SOURCE.read_text())
    if source.get("candidate") != "wide-principal-development" or not source.get("source_sha256"):
        raise ValueError("Require source-bound current-wide stability evidence")
    hashes = dict(source["source_sha256"])
    # Authenticate inherited identities before adding this calculation's sources.
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("Wide stability source identity differs")
    for p in (SOURCE, Path(__file__).relative_to(Path.cwd()),
              Path("fea/timber_floor_screen.py"), Path("fea/rigid_floor_screen.py"),
              Path("uv.lock")):
        hashes[str(p)] = digest(p)
    floor = [[x, y, 0.] for x, y in source["state"]["support_polygon_mm"]]
    records = [{**case, "friction_results": {
        str(mu): solve(floor, case["wrench_n_nmm"], mu) for mu in MUS}}
        for case in cases(source["state"], locations())]
    report = {"candidate": source["candidate"], "source_sha256": hashes,
              "scipy_version": scipy.__version__, "floor_vertices_mm": floor,
              "assumptions": LIMITS, "cases": records,
              "summary": {str(mu): dict(Counter(
                  r["friction_results"][str(mu)]["status"] for r in records)) for mu in MUS}}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("Source changed during floor screen")
    with OUTPUT.open("xb") as stream:
        stream.write(gzip.compress((json.dumps(report, allow_nan=False)+"\n").encode(), mtime=0))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    run()
