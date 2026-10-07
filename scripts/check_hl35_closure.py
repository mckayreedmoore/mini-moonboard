"""Check remaining bolt/angle and unrelated-timber coverage at the v7 pose.

Raw unrelated timber is conservative here: all proposed machining subtracts
material. Intended receiving members are excluded from the shaft/wood query.
This is occupied geometry, not delivered hardware or strength qualification.
"""

from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as base
from scripts import hl35_candidate_finalize as final
from scripts import hl35_candidate_finish as v5
from scripts import hl35_fit_revision as v3


def main() -> None:
    report_path = final.PACKET / "fit-assessment.json"
    report = json.loads(report_path.read_text())
    manifest_path = final.PACKET / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, digest in {**manifest["source_sha256"], **manifest["outputs"]}.items():
        if base.sha(base.ROOT / name) != digest:
            raise ValueError(f"final geometry binding differs: {name}")
    snapshot, _, _ = base.load_sources()
    source, _ = base.reconstructed_wood(snapshot)
    wood, dims = v5.geometry(source)
    angles = v3.angles(wood, dims)
    axes = []
    for row in report["installed_axes"]:
        row = dict(row)
        row["point"], row["direction"] = cq.Vector(*row["point"]), cq.Vector(*row["direction"])
        row["attachments"] = [r for r in report["flange_attachments"] if r["physical_axis_id"] == row["id"]]
        axes.append(row)
    metal = v5.hardware(axes)
    axis_to_receivers = {row["id"]: set(row["receivers"]) for row in axes}
    angle_bodies = [(row.id, row.shape, row.shape.BoundingBox()) for row in angles]
    wood_bodies = [(name, shape, shape.BoundingBox()) for name, shape in wood.items()]
    steel_hits, shaft_hits = [], []
    def overlap(shape: cq.Shape, bounds, other: cq.Shape, other_bounds) -> float:
        if any(min(getattr(bounds, x + "max"), getattr(other_bounds, x + "max")) -
               max(getattr(bounds, x + "min"), getattr(other_bounds, x + "min")) < 1e-6 for x in "xyz"):
            return 0
        return max(0.0, shape.intersect(other).Volume())
    for axis, role, shape in metal:
        bounds = shape.BoundingBox()
        for angle, body, other_bounds in angle_bodies:
            if (volume := overlap(shape, bounds, body, other_bounds)) > .01:
                steel_hits.append({"axis_id": axis, "role": role, "angle_id": angle,
                                   "intersection_mm3": round(volume, 5)})
        if role == "shaft":
            for member, body, other_bounds in wood_bodies:
                if member not in axis_to_receivers[axis] and (volume := overlap(shape, bounds, body, other_bounds)) > .01:
                    shaft_hits.append({"axis_id": axis, "member": member, "intersection_mm3": round(volume, 5)})
    result = {"schema": "hl35_final_hardware_coverage/v1", "candidate": base.CANDIDATE, "revision": final.REVISION,
        "question": "Do any conditional metal roles intersect ideal angles, or shafts intersect unrelated raw timber/panels?",
        "counts": {"angle_bodies": len(angles), "structural_axes": len(axes), "metal_roles": len(metal),
                   "metal_angle_intersections": len(steel_hits), "shaft_unrelated_raw_timber_intersections": len(shaft_hits)},
        "metal_angle_intersections": steel_hits, "shaft_unrelated_raw_timber_intersections": shaft_hits,
        "conditional_coverage_passed": not steel_hits and not shaft_hits,
        "limits": "Exact conditional occupied solids only. Intended receiver bores are excluded; actual products, access and strength are unqualified.",
        "release": base.RELEASE}
    output = final.PACKET / "hardware-closure.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    manifest["hardware_closure"] = {"command": ".venv/bin/python -m scripts.check_hl35_closure",
        "versions": {"cadquery": cq.__version__},
        "source_sha256": {str(Path(__file__).relative_to(base.ROOT)): base.sha(Path(__file__)),
                          str(report_path.relative_to(base.ROOT)): base.sha(report_path)},
        "outputs": {str(output.relative_to(base.ROOT)): base.sha(output)},
        "passed": result["conditional_coverage_passed"]}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result["counts"], sort_keys=True))
    if not result["conditional_coverage_passed"]:
        raise SystemExit("Nominal geometry requires revision; see hardware-closure.json")


if __name__ == "__main__":
    main()
