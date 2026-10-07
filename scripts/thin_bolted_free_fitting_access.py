"""Resolve the eight free-angle paths blocked by the first diagonal trial.

Preserves that trial and its producer. No wood, panels, services or bolts
remain in this final named state; each angle still has its complete body.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cadquery as cq

from scripts import thin_bolted_access_takeoff as access

OUT = access.PACKET / "free-fitting-release-v4.json"


def run() -> dict:
    earlier = json.loads(access.OUT.read_text())
    for name, expected in earlier["source_sha256"].items():
        if access.shared.sha(access.shared.ROOT / name) != expected:
            raise ValueError(f"earlier access source changed: {name}")
    frozen = access.model.source_layout()
    _, shapes = access.load_geometry()
    old = earlier["member_release"]
    if old["individual_timbers_released"] != 20 or old["unresolved_timbers"]:
        raise ValueError("the complete prior timber sequence is required")
    stationary = [r for r in shapes if r[0] in old["unresolved_brackets"]]
    rows = []
    for name in old["unresolved_brackets"]:
        row = next(r for r in frozen["raw_fittings"] if r["angle_id"] == name)
        spec = access.model.revision.thin.B103
        plane = cq.Plane(origin=cq.Vector(*row["origin_xyz_mm"]),
                         xDir=cq.Vector(*row["u_xyz"]), normal=cq.Vector(*row["w_xyz"]))
        w, t = spec.width_mm, spec.thickness_mm
        boxes = [cq.Solid.makeBox(spec.u_leg_mm, t, w, cq.Vector(0, 0, -w / 2)).moved(plane.location),
                 cq.Solid.makeBox(t, spec.v_leg_mm, w, cq.Vector(0, 0, -w / 2)).moved(plane.location)]
        actual = next(body for identifier, _, body in stationary if identifier == name)
        if actual.cut(boxes[0].fuse(boxes[1])).Volume() > .01:
            raise ValueError("complete fitting containment failed")
        direction = cq.Vector(*row["w_xyz"])
        corridors = [access.convex_linear_sweep(box, direction, 100.) for box in boxes]
        obstacles = [r for r in stationary if r[0] != name]
        blockers = [{"moving_plate": i, **hit} for i, corridor in enumerate(corridors)
                    for hit in access.hits(corridor, obstacles)]
        blockers.extend({"moving_plate": i, "obstacle": "floor", "role": "floor"}
                        for i, corridor in enumerate(corridors) if corridor.BoundingBox().zmin < -.01)
        rows.append({"id": name, "direction_xyz": access.shared.xyz(direction),
                     "travel_mm": 100., "hits": blockers})
        if not blockers:
            stationary = [r for r in stationary if r[0] != name]
    return {"schema": "thin_bolted_free_fitting_access/v1", "candidate": access.model.CANDIDATE,
            "source_sha256": {str(access.OUT.relative_to(access.shared.ROOT)): access.shared.sha(access.OUT),
                              str(Path(__file__).relative_to(access.shared.ROOT)): access.shared.sha(Path(__file__))},
            "prior_initial_fittings_released": old["brackets_released_before_timbers"],
            "prior_individual_timbers_released": 20, "free_fitting_release_rows": rows,
            "free_fittings_released": len(rows) - len(stationary),
            "total_fittings_released": old["brackets_released_before_timbers"] + len(rows) - len(stationary),
            "unresolved_fittings": [r[0] for r in stationary],
            "sequence": "Release panels/services/screws,70bolt stacks,28initial fittings,20individual timbers,then these8free fittings along their local width axis. Reverse the checked paths for nominal assembly on separately supported members.",
            "method": "Two unperforated rectangular flanges contain every complete fitting. Continuous conservative polyhedral sweeps are checked against all remaining exact fittings and the floor, with100mm initial separation.",
            "limits": "Prior diagonal failures are retained. This final state has no receiving timbers; moving across a seated face was not used while wood was present. Actual tools, tolerances, support stability, loaded removal and free handling remain unverified.",
            "reproduce": ".venv/bin/python -m scripts.thin_bolted_free_fitting_access --out /tmp/thin-free-fitting-reproduced.json",
            "release": access.shared.RELEASE}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve frozen final fitting evidence")
    result = run()
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "total_fittings_released": result["total_fittings_released"],
                      "unresolved": result["unresolved_fittings"]}, indent=2))


if __name__ == "__main__":
    main()
