"""Explicit product-frame collision diagnostic; not an auto-collected test.

Run from repo root: PYTHONPATH=. uv run python tests/product_frame_screen.py
No passing structural/fit claim is produced, even when findings are empty.
"""
import argparse
import hashlib
import json
from itertools import combinations
from math import isfinite
from pathlib import Path

import cadquery as cq

from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.selected_hardware import BoltSpec, spec_for

THRESHOLD_MM3 = .01


def screen(parts, connections):
    parts, connections = tuple(parts), tuple(connections)
    if len({p.name for p in parts}) != len(parts) or len({c.name for c in connections}) != len(connections):
        raise ValueError("Duplicate part or connection names")
    bodies = {p.name: p.shape for p in parts}
    for c in connections:
        if not set(c.members) <= bodies.keys():
            raise ValueError(f"Missing receiving members: {c.name}")
    components = {c.name: c.components() for c in connections}
    hardware = {name: cq.Compound.makeCompound(shapes) for name, shapes in components.items()}
    # Exact bounds are cached by object identity for this one diagnostic only.
    bounds = {}
    findings, errors = [], []

    def intersect(category, a, shape_a, b, shape_b, **extra):
        try:
            boxes = []
            for shape in (shape_a, shape_b):
                if id(shape) not in bounds:
                    bounds[id(shape)] = exact_bounds(shape)
                boxes.append(bounds[id(shape)])
            aa, bb = boxes
            if any(min(getattr(aa, k+"max"), getattr(bb, k+"max"))
                   - max(getattr(aa, k+"min"), getattr(bb, k+"min")) <= 1e-5 for k in "xyz"):
                return
            volume = shape_a.intersect(shape_b).Volume()
            if not isfinite(volume):
                raise ValueError("Nonfinite intersection volume")
            if volume > THRESHOLD_MM3:
                findings.append({"category": category, "a": a, "b": b, "volume_mm3": volume, **extra})
        except Exception as error:  # noqa: BLE001 -- retain failures instead of silently skipping pairs
            errors.append({"category": category, "a": a, "b": b,
                           "error": f"{type(error).__name__}: {error}", **extra})

    for (a, sa), (b, sb) in combinations(bodies.items(), 2):
        intersect("body_body", a, sa, b, sb)
    for c in connections:
        shapes = components[c.name]
        roles = ("washer_head", "washer_nut", "head", "nut") if c.kind == "bolt" else ("head_seat_allowance",)
        for role, shape in zip(roles, shapes[1:], strict=True):
            for name, body in bodies.items():
                intersect("hardware_body", c.name, shape, name, body, component=role,
                          declared_member=name in c.members)
        for name, body in bodies.items():
            # Thread/wood overlap within declared screw members is intentional;
            # a bolt shaft is required to clear its receiver bores as well.
            if c.kind == "bolt" or name not in c.members:
                intersect("shaft_body", c.name, shapes[0], name, body,
                          declared_member=name in c.members)
    for (a, sa), (b, sb) in combinations(hardware.items(), 2):
        intersect("hardware_hardware", a, sa, b, sb)

    tools = []  # Retain shapes so object-identity bound-cache keys cannot be reused.
    for c in connections:
        spec, d = spec_for(c), c.direction.normalized()
        if isinstance(spec, BoltSpec):
            entries = (("head", c.start-d*spec.head_height_max_mm, -d),
                       ("nut", c.start+d*(2*spec.washer_thickness_nominal_mm+c.grip+spec.nut_height_max_mm), d))
            diameter, length = 36., 25.  # Existing conservative project socket withdrawal allowance.
        else:
            origin = c.start if spec.seating == "flush" else c.start-d*spec.head_allowance_height_mm
            entries = (("head", origin, -d),)
            diameter, length = spec.tool_allowance_diameter_mm, spec.tool_allowance_length_mm
        for role, start, direction in entries:
            tool = cq.Solid.makeCylinder(diameter/2, length, start, direction)
            tools.append(tool)
            for name, body in bodies.items():
                hidden_front = c.name.startswith("rib_") and c.name.endswith("_front") and name.startswith("main_")
                intersect("tool_body", c.name, tool, name, body, component=role,
                          installation_note="Requires panel removal / before-panel installation" if hidden_front else "Assembled blocker")
            for name, other in hardware.items():
                if name != c.name:
                    intersect("tool_hardware", c.name, tool, name, other, component=role)
    return {"status": "DIAGNOSTIC ONLY; ALL FINDINGS RETAINED; NOT A PASS OR DESIGN QUALIFICATION",
            "qualified_for_design": False, "part_count": len(parts), "connection_count": len(connections),
            "threshold_mm3": THRESHOLD_MM3, "findings": findings, "errors": errors,
            "limits": "Nominal candidate and selected envelopes only. Own hardware components excluded; screw threads may intersect declared members. "
                      "No head/body exemption. Tool corridors start outside heads/nuts and do not prove wrench engagement, curved access, "
                      "manufacturing tolerance, LED/wire clearance, bearing capacity or assembly stability."}


def source_hashes(paths):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_names = ("product_frame", "product_connections", "selected_hardware", "transition_frame",
                    "clip_frame", "spacing_frame", "independent_leg_frame", "joint_frame",
                    "footprint_frame", "shallow_frame", "hybrid_frame", "hybrid", "box_frame",
                    "model", "panel_grid", "box_exports")
    sources = [Path("mini_moonboard")/(name+".py") for name in source_names]
    sources.append(Path("tests/product_frame_screen.py"))
    before = source_hashes(sources)
    from mini_moonboard import product_frame
    report = screen(product_frame.parts(), product_frame.connections())
    if source_hashes(sources) != before:
        raise RuntimeError("Source files changed during product-frame screen; report not published")
    report["source_sha256"] = before
    report["cadquery_version"] = cq.__version__
    payload = json.dumps(report, indent=2, allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(payload)
        from collections import Counter
        print(json.dumps({"output": str(args.output), "errors": len(report["errors"]),
                          "findings": dict(Counter(item["category"] for item in report["findings"]))}))
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
