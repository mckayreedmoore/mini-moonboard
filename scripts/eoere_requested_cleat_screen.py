"""Conventional first sizing of the owner's trimmed two-3/4in cleats.

Reuse the preceding balanced bore-pressure construction and NDS Appendix E
row helper. Every demand comes from the new frame's own replayed field.
"""

from __future__ import annotations

import ast
import itertools
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts.eoere_paired_frame_basis import RAW, ROOT, ref, sha

BASE = RAW / "frame-completion-v1"
RUN = BASE / "owner-requested-cases-v3"
GEOMETRY = BASE / "owner-requested-geometry-v3/geometry.json"
OUTPUT = Path("docs/bolted-frame-development/owner-frame-v3/cleat-sizing.json")
APA = Path("fea/generated/selected-hardware-followup-v1/engineering-closure-v1/"
           "cleat-senior-review-v1/plywood-gusset-v1/sources/apa-D510F-2020.pdf")


def existing_function(path, name, scope):
    tree = ast.parse((ROOT / path).read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), scope)  # noqa: S102 -- fixed, source-bound local math helpers
    return scope[name]


def evaluate():
    g = json.loads((ROOT / GEOMETRY).read_bytes())
    method = BASE / "shaft_bearing_blocks.py"
    rows_method = RAW / "cleat_group_and_washers.py"
    blocks = existing_function(method, "blocks", {"np": np, "math": math})
    row_tear = existing_function(rows_method, "row_tear", {})
    assert row_tear(191 * 3.125, 3, 7, 4) == 7162.5
    assert abs(blocks(-1, 1, [3, 0, 0], [-3, 0, 0])[0][2][0] - 2) < 1e-12
    profiles = g["profiles"]
    polygons = {}
    for name, p in profiles.items():
        if not name.startswith("eoere_cleat_"):
            continue
        assert sha(p["finished"]["path"]) == p["finished"]["sha256"]
        shape = cq.Shape.importBrep(str(ROOT / p["finished"]["path"]))
        face = next(f for f in shape.Faces() if abs(f.normalAt().x) > .99)
        polygons[name] = [(np.array([e.startPoint().y, e.startPoint().z]),
                           np.array([e.endPoint().y, e.endPoint().z])) for e in face.outerWire().Edges()]

    def span(name, direction, point):
        j, cross = direction - 1, 2 - direction
        values = []
        for a, b in polygons[name]:
            delta = b[cross] - a[cross]
            if abs(delta) < 1e-7:
                continue
            u = (point[cross] - a[cross]) / delta
            if -1e-7 <= u <= 1 + 1e-7:
                values.append(float(a[j] + u * (b[j] - a[j])))
        values = sorted({round(v, 7) for v in values})
        assert len(values) % 2 == 0 and values
        segments = list(zip(values[::2], values[1::2]))
        lo, hi = next((lo, hi) for lo, hi in segments if lo - 1e-6 <= point[j] <= hi + 1e-6)
        return lo, hi

    lbf, inch = 4.4482216152605, 25.4
    shear = 110 * lbf / inch
    tension = {1: 2550 * lbf / 304.8 * .5, 2: 4350 * lbf / 304.8 * .5}
    cases, pins = [], {ref(p)["path"]: sha(p) for p in [Path(__file__), method, rows_method, APA, GEOMETRY]}
    for folder in sorted((ROOT / RUN / "nominal").glob("three-pin-shift-corner-floor-*-v1")):
        if not (folder / "independent-replay-plywood.json").exists():
            continue
        field_ref = ref(folder / "field.json")
        field = json.loads((folder / "field.json").read_bytes())
        replay = json.loads((folder / "independent-replay.json").read_bytes())
        ply = json.loads((folder / "independent-replay-plywood.json").read_bytes())
        assert replay["field"] == ply["field"] == field_ref
        assert replay["false_screw_and_floor_forces_rejected"] and len(ply["raw_operator_checks"]) == 4
        assert field["source_inputs"]["geometry"] == ref(GEOMETRY)
        assert replay["equilibrium"]["gradient_inf_n"] < 1e-5
        for p in [folder / n for n in ("field.json", "independent-replay.json", "independent-replay-plywood.json")]:
            pins[ref(p)["path"]] = sha(p)
        bores, pressures = {}, []
        for name in polygons:
            own = []
            for axis in g["axes"]:
                if name not in axis["receivers"]:
                    continue
                actions = [r for r in field["common_shaft_bearing_actions"]
                           if r["axis_id"] == axis["id"] and r["host"] == name]
                assert len(actions) == 2
                lo, hi = actions[0]["surface_interval_mm"]
                t, center = hi - lo, (hi + lo) / 2
                force = sum((np.asarray(r["force_on_second_xyz_n"]) for r in actions), np.zeros(3))
                first = sum(((r["axis_station_mm"] - center) * np.asarray(r["force_on_second_xyz_n"])
                             for r in actions), np.zeros(3))
                q0, q1 = force / t - 6 * first / t**2, force / t + 6 * first / t**2
                parts = blocks(lo, hi, q0, q1)
                envelope = np.max(np.abs([p[2] for p in parts]), axis=0) * t
                point = np.asarray(axis["point_xyz_mm"])[1:]
                own.append({"axis": axis["id"], "point": point, "demand": envelope,
                            "integrated_force": np.abs(force), "signed_force": force,
                            "first_moment": first, "wall_mm": t})
                pressures.append({"leaf": name, "axis_id": axis["id"], "whole_wall_mm": t,
                                  "force_on_leaf_xyz_N": force.tolist(), "first_moment_xyz_Nmm": first.tolist(),
                                  "balanced_component_envelope_N": envelope.tolist(),
                                  "parts": [{"interval_mm": [a, b], "pressure_xyz_N_per_mm": q.tolist()} for a, b, q in parts]})
            assert len(own) == 3
            bores[name] = own
        groups = []
        for name, own in bores.items():
            for count in (1, 2, 3):
                for subset in itertools.combinations(own, count):
                    references, geometry = {}, {}
                    for direction in (1, 2):
                        cross = 3 - direction
                        rows = {}
                        for b in subset:
                            rows.setdefault(round(b["point"][cross - 1], 5), []).append(b)
                        rr = []
                        for coordinate, row in sorted(rows.items()):
                            coordinates = sorted(b["point"][direction - 1] for b in row)
                            distances = []
                            for b in row:
                                lo, hi = span(name, direction, b["point"])
                                distances.append(min(b["point"][direction - 1] - lo, hi - b["point"][direction - 1]))
                            end = min(distances)
                            pitch = min(b - a for a, b in itertools.pairwise(coordinates)) if len(row) > 1 else None
                            rr.append({"cross_mm": coordinate, "end_mm": end,
                                       "reference_N": row_tear(shear, len(row), end, pitch)})
                        total = sum(r["reference_N"] for r in rr)
                        group = total if len(rr) == 1 else (
                            .5 * (rr[0]["reference_N"] + rr[-1]["reference_N"]) +
                            tension[direction] * (rr[-1]["cross_mm"] - rr[0]["cross_mm"] - (len(rr) - 1) * 10.31875))
                        references[direction] = min(total, group)
                        geometry[direction] = rr
                    index = sum(sum(b["demand"][d] for b in subset) / references[d] for d in (1, 2))
                    resultant_index = sum(sum(b["integrated_force"][d] for b in subset) / references[d] for d in (1, 2))
                    # Project the two-direction reference diamond onto the
                    # signs of the integrated component forces. Even allowing
                    # arbitrary signed pressure, its scalar peak cannot be
                    # below the exact balanced-block L-infinity optimum.
                    moment = sum(sum(np.sign(b["signed_force"][d]) * b["first_moment"][d] /
                                     references[d] for d in (1, 2)) for b in subset)
                    t = subset[0]["wall_mm"]
                    assert all(abs(b["wall_mm"] - t) < 1e-6 for b in subset)
                    a = 2 * abs(moment) / t
                    necessary = a + math.hypot(a, resultant_index)
                    groups.append({"leaf": name, "axes": [b["axis"] for b in subset],
                                   "references_N": references, "row_geometry": geometry,
                                   "signed_weighted_first_moment_mm": moment, "whole_wall_mm": t,
                                   "balanced_pressure_reference_index": index,
                                   "minimum_scalar_pressure_reference_index": necessary,
                                   "integrated_force_only_reference_index": resultant_index})
        assert len(groups) == 28
        cases.append({"case_id": field["case_id"], "field": field_ref,
                      "gradient_inf_N": replay["equilibrium"]["gradient_inf_n"],
                      "balanced_pressures": pressures, "groups": groups,
                      "maximum_balanced_pressure_reference_index": max(r["balanced_pressure_reference_index"] for r in groups),
                      "maximum_minimum_scalar_pressure_reference_index": max(r["minimum_scalar_pressure_reference_index"] for r in groups),
                      "maximum_integrated_force_only_reference_index": max(r["integrated_force_only_reference_index"] for r in groups)})
    assert cases
    result = {"schema": "eoere_requested_three_quarter_cleat_sizing/v1", "geometry": ref(GEOMETRY),
              "producer": ref(Path(__file__)), "source_sha256": pins, "cases": cases,
              "APA_basis": "D510F2020 Table9,24ocPS1 plywood >=5plies/Group1; Fvtv110lbf/in, FtA4350/2550lbf/ft. Narrow-width tension multiplier0.5. Actual stamp unobserved.",
              "minimum_pressure_formula": "I=sum(abs(F_component)/row_reference); J=sum(sign(F_component)*first_moment_component/row_reference). Umin=2abs(J)/t+hypot(2abs(J)/t,I), the exact scalar pressure optimum on a wall of thickness t. This is a lower bound for the two-direction row envelope at these fixed actions.",
              "maximum_balanced_pressure_reference_index": max(c["maximum_balanced_pressure_reference_index"] for c in cases),
              "maximum_minimum_scalar_pressure_reference_index": max(c["maximum_minimum_scalar_pressure_reference_index"] for c in cases),
              "maximum_integrated_force_only_reference_index": max(c["maximum_integrated_force_only_reference_index"] for c in cases),
              "complete_conditional_frame_evaluation": False, "fabrication_released": False, "climbing_released": False,
              "limits": ["Initial sizing only. Full-width nominal plywood beam stiffness remains an approximation for the trimmed perimeter, not a physical demand bound.",
                         "Reuses the prior conventional balanced-pressure/NDS-style group construction, not an APA-tested complete joint capacity.",
                         "Integrated force plus first moment supplies an exact scalar L-infinity lower bound within the stated pointwise row-reference hypothesis. A value above1 cannot be repaired by changing only its pressure construction at the same actions. It is not a universal plywood-fracture or physical-demand bound.",
                         "Whole-frame, hardware, panel/Hillman, finite motion, delivered material/installation and floor qualifications are not supplied by this sheet."]}
    (ROOT / OUTPUT).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(cases), "balanced": result["maximum_balanced_pressure_reference_index"],
                      "integrated_force_only": result["maximum_integrated_force_only_reference_index"]}))


if __name__ == "__main__":
    evaluate()
