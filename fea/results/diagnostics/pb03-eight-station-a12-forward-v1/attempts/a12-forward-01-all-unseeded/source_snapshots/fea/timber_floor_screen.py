"""Finite asymmetric rigid-floor sensitivity screen, not contact or joint FEA."""
import gzip
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import scipy

from fea.prepare_easy_structural import digest
from fea.rigid_floor_screen import solve
from fea.timber_structural import locations

SOURCE = Path("fea/results/timber-base/stability.json")
OUTPUT = Path("fea/results/timber-floor-screen.json.gz")
HOLDS = ("A1", "F1", "K1", "A6", "F6", "K6", "A12", "F12", "K12")


def cases(state, points):
    """One hold takes the whole prescribed load; no invented sharing."""
    indexed = {label: (np.array(p), np.array(n)) for label, p, n in points}
    for weight in (150, 200, 250, 300):
        for factor in (1, 2):
            for mass_fraction in (.8, 1.):
                gravity = np.array([0., 0., -state["mass_kg"]*mass_fraction*9.80665])
                for label in HOLDS:
                    point, normal = indexed[label]
                    point = point+100.*normal
                    for direction in range(-1, 8):
                        angle = direction*math.pi/4
                        force = np.array([0., 0., -weight*.45359237*9.80665*factor])
                        if direction >= 0:
                            force[:2] = [300*math.cos(angle), 300*math.sin(angle)]
                        moment = np.cross(point, force)+np.cross(state["centre_xyz_mm"], gravity)
                        yield {"climber_lb": weight, "weight_factor": factor,
                               "mass_fraction": mass_fraction, "hold": label,
                               "horizontal_direction_deg": None if direction < 0 else direction*45,
                               "wrench_n_nmm": np.r_[force+gravity, moment].tolist()}


def run():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite published floor-screen evidence")
    source = json.loads(SOURCE.read_text())
    if source.get("candidate") != "timber-base-development" or not source.get("source_sha256"):
        raise ValueError("Require timber-base evidence with a nonempty source closure")
    hashes = {**source["source_sha256"], **{str(p): digest(p) for p in (
        SOURCE, Path("fea/timber_floor_screen.py"),
        Path("fea/rigid_floor_screen.py"), Path("uv.lock"))}}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("Timber source identity differs")
    floor = [[x, y, 0.] for x, y in source["state"]["support_polygon_mm"]]
    records = []
    for case in cases(source["state"], locations()):
        results = {}
        for mu in (.1, .2, .4):
            result = solve(floor, case["wrench_n_nmm"], mu)
            results[str(mu)] = result
        records.append({**case, "friction_results": results})
    report = {"candidate": source["candidate"], "source_sha256": hashes,
              "scipy_version": scipy.__version__, "floor_vertices_mm": floor,
              "assumptions": "Rigid whole frame; level floor; compression-only vertex reactions; "
              "16-ray inscribed friction cones. Assumed mu, not measured. Single holds at 100mm "
              "standoff; finite 45deg horizontal directions, not all azimuths. Included mass and "
              "fixed CG inherited. No elasticity, floor pressure, support loss, dynamic response, "
              "unique joint demands, bolt forces, strength or approval. Polygon infeasibility "
              "alone does not prove circular Coulomb-cone infeasibility.",
              "summary": {str(mu): dict(Counter(r["friction_results"][str(mu)]["status"]
                                              for r in records)) for mu in (.1, .2, .4)},
              "cases": records}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("Source changed during run")
    payload = (json.dumps(report, allow_nan=False)+"\n").encode()
    with OUTPUT.open("xb") as stream:
        stream.write(gzip.compress(payload, mtime=0))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    run()
