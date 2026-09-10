"""Current selective-member CAD mass and finite rigid-floor feasibility screen."""
import argparse
import gzip
import json
import math
from collections import Counter
from pathlib import Path

import scipy

from fea import prepare_easy_structural as common
from fea.rigid_floor_screen import solve
from fea.timber_floor_screen import cases
from fea.wide_structural import locations

OUTPUT = Path("fea/results/selective-floor-v1.json.gz")
FRICTION = (.1, .2, .4)
LIMITS = (
    "Rigid whole-frame floor feasibility only; no structural acceptance. Actual current "
    "drilled CAD wood/plywood at assumed 600 kg/m3 and steel clips plus unioned fastener "
    "component envelopes at 7850 kg/m3. Fastener envelopes simplify threads and heads; "
    "this is a CAD mass estimate, not measured product mass. Holds, LEDs, wiring and glue "
    "omitted. Level floor; compression-only reactions at actual floor-footprint hull "
    "vertices. Assumed friction, not measured. 16-ray inscribed friction polygon; "
    "infeasibility does not prove circular-cone infeasibility. 80/100% included mass "
    "at fixed CG; one hold takes the prescribed full load at 100 mm standoff; nine "
    "selected holds and finite 45-degree horizontal directions, not an exhaustive "
    "load envelope. No stiffness, contact compatibility, pressure, uneven floor, "
    "dynamics, connection demand/capacity, strength, buckling or native FEA. Feasible "
    "forces are independently checked equilibrium witnesses, not predicted reactions."
)


def current_mass(model):
    """Include each drilled part and each unioned fastener exactly once.

    The shared mass helper recognizes only clip_mvp_ as steel. Temporary names
    adapt that explicit density convention without changing model identities.
    Panel screw heads overlap their shafts, so summing component volumes directly
    would double-count steel. Each fastener is fused before integration.
    """
    from mini_moonboard.box_frame import Part

    parts, inventory = [], []
    names = set()

    def append(name, shape, steel, component_count=1, raw_volume=None):
        if name in names or not shape.isValid():
            raise ValueError("Duplicate identity or invalid mass shape: "+name)
        names.add(name)
        volume = shape.Volume()
        if not math.isfinite(volume) or volume <= 0:
            raise ValueError("Positive finite solid volume required: "+name)
        density = 7850 if steel else 600
        parts.append(Part(("clip_mvp_" if steel else "wood_")+name,
                          shape, (0., 0., 0.), "Temporary mass integration identity", 1))
        inventory.append({"name": name, "material": "steel" if steel else "wood/plywood",
                          "density_kg_m3": density, "volume_mm3": volume,
                          "mass_kg": volume/1e9*density,
                          "centre_xyz_mm": list(shape.Center().toTuple()),
                          "component_count": component_count,
                          "overlap_removed_mm3": 0. if raw_volume is None else raw_volume-volume})

    for part in model.parts():
        if part.name.startswith(("insert_", "fastener_")):
            raise ValueError("Unexpected embedded insert or fastener: "+part.name)
        append(part.name, part.shape, part.name.startswith("clip_"))
    for connection in model.connections():
        components = tuple(connection.components())
        if not components or any(not shape.isValid() for shape in components):
            raise ValueError("Invalid fastener components: "+connection.name)
        shape = components[0].fuse(*components[1:]) if len(components) > 1 else components[0]
        append("fastener_"+connection.name, shape, True, len(components),
               sum(component.Volume() for component in components))
    state = common.mass_state(parts)
    if not math.isclose(state["mass_kg"], sum(row["mass_kg"] for row in inventory), abs_tol=1e-9):
        raise ValueError("Mass inventory does not reconcile")
    return state, inventory


def sources():
    # A deliberately broad local closure also captures deferred imports in the
    # shared CAD and FE helpers. No predecessor report or mass state is inherited.
    paths = {*Path("mini_moonboard").glob("*.py"), *Path("fea").glob("*.py"),
             Path("docs/ml24z-reference.json"), Path("docs/panel-insert-reference.json"),
             Path("docs/selective-stock-reference.json"), Path("uv.lock")}
    return {str(path): common.digest(path) for path in sorted(paths)}


def run(output=OUTPUT):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite published floor-screen evidence")
    hashes = sources()
    from mini_moonboard import selective_2x6_frame as model

    state, inventory = current_mass(model)
    floor = [[x, y, 0.] for x, y in state["support_polygon_mm"]]
    records = [{**case, "friction_results": {
        str(mu): solve(floor, case["wrench_n_nmm"], mu) for mu in FRICTION}}
        for case in cases(state, locations())]
    if len(records) != 1296:
        raise ValueError("Expected 1296 prescribed finite load cases")
    feasible = [result for record in records for result in record["friction_results"].values()
                if result["polygon_feasible"]]
    report = {"candidate": model.KEY, "source_sha256": hashes,
              "scipy_version": scipy.__version__, "state": state,
              "mass_inventory": inventory, "floor_vertices_mm": floor,
              "assumptions": LIMITS, "qualified_for_design": False,
              "structural_analysis_run": False, "case_count": len(records),
              "summary": {str(mu): dict(Counter(record["friction_results"][str(mu)]["status"]
                                              for record in records)) for mu in FRICTION},
              "witness_validation": {
                  "checked_feasible_witnesses": len(feasible),
                  "maximum_force_residual_n": max((max(map(abs, r["residual_wrench"][:3]))
                                                    for r in feasible), default=0.),
                  "maximum_moment_residual_nmm": max((max(map(abs, r["residual_wrench"][3:]))
                                                       for r in feasible), default=0.),
                  "minimum_normal_force_n": min((r["minimum_normal_force_n"]
                                                  for r in feasible), default=None),
                  "maximum_friction_excess_n": max((r["maximum_friction_excess_n"]
                                                    for r in feasible), default=None)},
              "cases": records}
    if sources() != hashes:
        raise ValueError("Source changed during floor screen")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(report, allow_nan=False, sort_keys=True)+"\n").encode()
    with output.open("xb") as stream:
        stream.write(gzip.compress(payload, mtime=0))
    print(json.dumps({"candidate": model.KEY, "mass_kg": state["mass_kg"],
                      "summary": report["summary"], "witness_validation": report["witness_validation"]}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    run(parser.parse_args().output)
