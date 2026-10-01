"""Extract corner carrier identities only; never read response forces/states."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE.parent / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
PIN = "d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0"
BODY = {
    "base_post_outer_left", "knee_outer_left_spine", "base_side_left",
    "knee_outer_left_inner_frame_block", "base_header",
}
AXES = {f"knee_outer_left_{part}_{i}" for part in ("post", "side", "inner_header") for i in (1, 2)}
FIELDS = {
    "first", "second", "role", "axis_id", "source_area_mm2", "point",
    "first_point", "second_point", "axis", "scalar_normal", "force_basis",
}


def build():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError("Frozen input changed; stop rather than repin automatically")
    model = json.loads(raw)
    owners = [
        {"name": name, "internal": row["first"] in BODY and row["second"] in BODY,
         **{key: val for key, val in row.items() if key in FIELDS}}
        for name, row in sorted(model["connection_ownership"].items())
        if row["first"] in BODY or row["second"] in BODY
    ]
    cells = [row for row in model["contact_cell_ownership"]
             if row["first"] in BODY or row["second"] in BODY]
    pairs = defaultdict(list)
    for cell in cells:
        pairs[(cell["first"], cell["second"], cell["kind"])].append(cell)
    groups = []
    for (first, second, kind), rows in sorted(pairs.items()):
        groups.append({
            "first": first, "second": second, "kind": kind,
            "internal": first in BODY and second in BODY,
            "cell_count": len(rows), "modeled_area_mm2": sum(r["area_mm2"] for r in rows),
            "cells": rows,
        })
    target = [r for r in owners if r.get("axis_id") in AXES]
    target_counts = Counter(r["role"] for r in target)
    assert target_counts == {"candidate_bolt_lateral_plane": 8, "physical_bolt_outer_seat_tension": 6}
    for axis in AXES:
        expected_planes = 2 if "_side_" in axis else 1
        assert Counter(r["role"] for r in target if r["axis_id"] == axis) == {
            "candidate_bolt_lateral_plane": expected_planes,
            "physical_bolt_outer_seat_tension": 1,
        }
    assert sum(g["internal"] for g in groups) == 7
    assert sum(g["cell_count"] for g in groups if g["internal"]) == 28
    floor_tangents = [r for r in owners if r["role"] == "assumed_no_slip_floor"]
    assert len(floor_tangents) == 4
    assert all(r["first"] == "base_post_outer_left" and r["second"] == "floor" for r in floor_tangents)
    by_name = {r["name"]: r for r in owners}
    for tangent in floor_tangents:
        normal = by_name[tangent["name"].removesuffix("_friction")]
        assert normal["role"] == "floor_normal" and normal["point"] == tangent["point"]
    datums = {}
    for name in sorted(BODY):
        geom = model["body_geometry"][name]["geometry_record"]
        datums[name] = [(a+b)/2 for a, b in zip(geom["start"], geom["end"], strict=True)]
    return {
        "schema": "current-corner-interface-recovery-map-v1",
        "candidate": model["candidate"], "geometry_revision_id": model["geometry_revision_id"],
        "source_path": str(SOURCE.relative_to(ROOT)), "source_sha256": PIN,
        "scope": "Frozen input carrier inventory only; no forces, active states, solve or acceptance",
        "units": {"point": "mm", "area": "mm2", "future_force": "N", "future_moment": "N mm"},
        "bodies": sorted(BODY), "new_corner_axes": sorted(AXES),
        "descriptor_midpoint_datums_mm": datums,
        "datum_scope": "Moment-reporting reference only; not a support, physical cut, or mass centroid",
        "counts": {
            "contact_pairs": len(groups), "contact_cells": len(cells),
            "internal_contact_pairs": 7, "internal_contact_cells": 28,
            "ownership_roles": dict(sorted(Counter(r["role"] for r in owners).items())),
            "new_corner_ownership_roles": dict(sorted(target_counts.items())),
        },
        "contact_groups": groups, "connection_ownership": owners,
        "future_recovery_contract": {
            "member_moment": "Sum (physical_application_point - explicit_datum) cross force_on_member, plus explicit couples",
            "opposite_action": "Use opposite force at the other body's physical application point, not the first seat by default",
            "axial_tie": "Collinear outer-seat forces preserve equal/opposite wrench; no middle-member axial tie",
            "contact": "Use actual normal force vector/sign at the stored point; area alone is not force or resistance",
            "aggregate": "Internal carrier actions cancel; aggregate balance cannot establish individual member or bolt demand",
            "boundary": "Keep all boundary carriers, source-bound external loads and actual member-cut actions; boundary inventory is not resistance requalification",
        },
        "acceptance_guard": [
            "No C11 response force or active flag is used; its rejected sign branch remains rejected",
            "A future response must match its independently frozen geometry/ownership/load/scenario sources",
            "Require simultaneous per-case signs, body/global equilibrium, engagement/contact consistency and declared sensitivity",
            "Separate conditional model actions from accepted physical/product resistance; no historical pass transfers",
            "The present map neither executes nor authorizes a native run, geometry change or fabrication",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = build()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = HERE / "interface-map.json"
    if args.verify:
        if output.read_text() != encoded:
            raise SystemExit("Saved map differs from pinned input extraction")
    else:
        output.write_text(encoded)
    print(json.dumps(result["counts"], sort_keys=True))
