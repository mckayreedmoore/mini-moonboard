"""Evaluate a complete current cleat cut wrench under declared strength assumptions.

An equilibrium traction construction includes normal bending, two shears and
torque. Exact-rational Bernstein subdivision bounds its pointwise interaction.
This is an intact-section reference, not a connection fracture or elastic-field
qualification. No frame solution, CAD query or design change is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import itertools
import json
import math
from fractions import Fraction as F
from pathlib import Path

from scripts import eoere_cleat_reference_audit as prior

current = prior.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC / "selected-hardware-v1/current-response-v1/joint-closure-v1/conditional-material-assumptions-v1.json"


def rational(value):
    current.require(isinstance(value, (int, float, F)) and not isinstance(value, bool)
                    and math.isfinite(value), "finite real scalar required")
    return value if isinstance(value, F) else F(str(value))


def traction_coefficients(wrench, width, height):
    """Polynomials in u=Z/(height/2), v=X/(width/2), in the saved Y,Z,X basis.

    phi = 9*T/(32*a*b) * (1-u*u)*(1-v*v), a=width/2, b=height/2.
    tau_p=phi_,q; tau_q=-phi_,p. Thus T=2*integral(phi), and side
    normal shear vanishes. Parabolic force terms integrate to Vp and Vq.
    """
    current.require(len(wrench) == 6, "six signed wrench components required")
    n, vp, vq, torque, mp, mq = map(rational, wrench)
    width, height = rational(width), rational(height)
    current.require(width > 0 and height > 0, "positive rectangle required")
    a, b, area = width/2, height/2, width*height
    phi = 9*torque/(32*a*b)
    normal = {(0, 0): n/area, (1, 0): -3*mq/(area*b), (0, 1): 3*mp/(area*a)}
    shear_p = {(0, 0): 3*vp/(2*area), (2, 0): -3*vp/(2*area),
               (0, 1): -2*phi/a, (2, 1): 2*phi/a}
    shear_q = {(0, 0): 3*vq/(2*area), (0, 2): -3*vq/(2*area),
               (1, 0): 2*phi/b, (1, 2): -2*phi/b}
    return normal, shear_p, shear_q


def evaluate(polynomial, u, v):
    return sum(c*u**i*v**j for (i, j), c in polynomial.items())


def interaction_polynomials(fields, strengths):
    """Represent max(sigma/Ft,-sigma/Fc)+abs(tau_p)/Fv+abs(tau_q)/Fr.

    The linear interaction is an explicit engineering hypothesis, not a
    published complete wood-connection interaction equation.
    """
    current.require(set(strengths) == {"tension", "compression", "parallel_shear", "rolling_shear"},
                    "four own positive strength references required")
    ft, fc, fv, fr = (rational(strengths[k]) for k in
                      ("tension", "compression", "parallel_shear", "rolling_shear"))
    current.require(min(ft, fc, fv, fr) > 0, "positive strength references required")
    output = []
    for normal_factor, sp, sq in itertools.product((1/ft, -1/fc), (-1, 1), (-1, 1)):
        polynomial = {}
        for field, factor in zip(fields, (normal_factor, sp/fv, sq/fr), strict=True):
            for key, coefficient in field.items():
                polynomial[key] = polynomial.get(key, F(0))+factor*coefficient
        output.append(polynomial)
    return output


def bernstein(polynomial):
    """Exact tensor degree-(2,2) coefficients on [-1,1]^2."""
    current.require(all(0 <= i <= 2 and 0 <= j <= 2 for i, j in polynomial),
                    "degree at most two in each coordinate required")
    values = [[evaluate(polynomial, F(i-1), F(j-1)) for j in range(3)] for i in range(3)]
    transform = ((F(1), F(0), F(0)), (F(-1, 2), F(2), F(-1, 2)), (F(0), F(0), F(1)))
    return tuple(tuple(sum(transform[i][k]*values[k][l]*transform[j][l]
                           for k in range(3) for l in range(3)) for j in range(3)) for i in range(3))


def split_curve(values):
    a, b, c = values
    ab, bc = (a+b)/2, (b+c)/2
    middle = (ab+bc)/2
    return (a, ab, middle), (middle, bc, c)


def subdivide(matrix, axis):
    current.require(axis in (0, 1), "one normalized coordinate required")
    if axis == 1:
        curves = [split_curve(row) for row in matrix]
        return tuple(c[0] for c in curves), tuple(c[1] for c in curves)
    columns = tuple(zip(*matrix, strict=True))
    left, right = subdivide(columns, 1)
    return tuple(zip(*left, strict=True)), tuple(zip(*right, strict=True))


def enclosure(polynomials, tolerance=1e-5, max_cells=100000):
    """Bound the continuous maximum, with exact arithmetic and a real witness."""
    tolerance = rational(tolerance)
    current.require(tolerance > 0 and isinstance(max_cells, int) and max_cells > 0 and polynomials,
                    "positive tolerance and cell budget required")
    matrices = tuple(bernstein(p) for p in polynomials)
    counter = itertools.count()
    heap, best, witness, visited = [], None, None, 0

    def admit(values, box):
        nonlocal best, witness
        upper = max(c for m in values for row in m for c in row)
        u0, u1, v0, v1 = box
        samples = [(m[i][j], (u0 if i == 0 else u1, v0 if j == 0 else v1))
                   for m in values for i in (0, 2) for j in (0, 2)]
        weights = (1, 2, 1)
        samples.extend((sum(m[i][j]*weights[i]*weights[j] for i in range(3) for j in range(3))/16,
                        ((u0+u1)/2, (v0+v1)/2)) for m in values)
        value, point = max(samples, key=lambda pair: pair[0])
        if best is None or value > best:
            best, witness = value, point
        heapq.heappush(heap, (-upper, next(counter), values, box))

    admit(matrices, (F(-1), F(1), F(-1), F(1)))
    while heap:
        negative_upper, _, matrices, box = heapq.heappop(heap)
        upper = -negative_upper
        if upper <= best:
            continue
        if upper-best <= tolerance:
            break
        current.require(visited < max_cells, "continuous-maximum certificate did not converge")
        visited += 1
        u0, u1, v0, v1 = box
        axis = 0 if u1-u0 >= v1-v0 else 1
        halves = tuple(subdivide(m, axis) for m in matrices)
        if axis == 0:
            middle = (u0+u1)/2
            boxes = ((u0, middle, v0, v1), (middle, u1, v0, v1))
        else:
            middle = (v0+v1)/2
            boxes = ((u0, u1, v0, middle), (u0, u1, middle, v1))
        for side, child_box in enumerate(boxes):
            admit(tuple(h[side] for h in halves), child_box)
    else:
        upper = best
    current.require(best <= upper and upper-best <= tolerance, "invalid continuous-maximum enclosure")
    return {"lower": float(best), "upper": float(upper), "normalized_witness_u_v": list(map(float, witness)),
            "exact_lower_fraction": str(best), "exact_upper_fraction": str(upper),
            "subdivided_cells": visited, "tolerance": float(tolerance)}


def validate_assumptions(inputs):
    current.require(inputs["schema"] == "eoere_conditional_material_assumptions/v1"
                    and inputs["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and inputs["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and inputs["extra_grid"] is False
                    and inputs["actual_observations"] is None
                    and inputs["physical_or_structural_release"] is False,
                    "current declared unobserved material hypothesis required")
    source = inputs["source_characteristic_values_mpa"]
    current.require(source == {"tension_perpendicular": .4, "compression_perpendicular": 2.2,
                               "parallel_shear": 3.2, "rolling_shear_approximation": .8}
                    and inputs["parallel_shear_reference_reduction"] == .67,
                    "this source-qualified C16/reference-reduction scope required")
    expected = {"tension": .4, "compression": 2.2, "parallel_shear": 2.144, "rolling_shear": .8}
    current.require(inputs["intact_section_base_reference_mpa"] == expected,
                    "declared base references must match source values and reduction")
    scenarios = inputs["strength_scaling_scenarios"]
    current.require(len(scenarios) == len({s["id"] for s in scenarios}) == 6
                    and sum(s["working_reference"] is True for s in scenarios) == 1,
                    "six distinct scenarios with exactly one working reference required")
    for scenario in scenarios:
        current.require(rational(scenario["strength_divisor"]) >= 1
                        and rational(scenario["whole_wrench_multiplier"]) >= 1
                        and isinstance(scenario["working_reference"], bool),
                        "references may not increase strengths or reduce original demand")
    working = next(s for s in scenarios if s["working_reference"])
    current.require(working["strength_divisor"] == 2. and working["whole_wrench_multiplier"] == 1.,
                    "declared divisor-two nominal-action working reference required")


def run():
    input_path = INPUT.resolve()
    current.require(input_path.is_relative_to(current.ROOT), "repository assumption input required")
    input_bytes = input_path.read_bytes()
    input_ref = {"path": str(input_path.relative_to(current.ROOT)),
                 "sha256": hashlib.sha256(input_bytes).hexdigest()}
    inputs = json.loads(input_bytes)
    validate_assumptions(inputs)
    cases, pins = prior.intake_source.intake()
    source = current.read(prior.DEMAND)
    refs = [prior.DEMAND, input_ref, current.ref(OWN), current.ref(Path(prior.__file__)),
            current.ref(current.ROOT/"tests/test_eoere_cleat_section_reference.py"), *inputs["cached_sources"]]
    pins = current.join(pins, source["source_sha256"], {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    strengths = inputs["intact_section_base_reference_mpa"]
    bindings = {b["case_id"]: b for b, _, _ in cases}
    result = []
    for saved in source["cases"]:
        binding = bindings[saved["case_id"]]
        current.require(saved["state_id"] == binding["state_id"] and saved["field"] == binding["field"],
                        "own authenticated case/state/field required")
        geometry = source["geometry"][saved["member"]]
        current.require(geometry["basis_normal_p_q_xyz"] == [[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]],
                        "saved right-handed Y,Z,X basis required")
        for trace in saved["traces"]:
            wrench = trace["required_cut_on_low_portion_n_nmm"]
            fields = traction_coefficients(wrench, geometry["width_x_mm"], geometry["height_z_mm"])
            bound = enclosure(interaction_polynomials(fields, strengths), inputs["base_reference_index_tolerance"])
            scenarios = []
            for scenario in inputs["strength_scaling_scenarios"]:
                scale = rational(scenario["strength_divisor"])*rational(scenario["whole_wrench_multiplier"])
                current.require(scale > 0., "positive declared reference scaling required")
                lower = F(bound["exact_lower_fraction"])*scale
                upper = F(bound["exact_upper_fraction"])*scale
                status = "construction_within_reference" if upper <= 1. else (
                    "construction_exceeds_reference" if lower > 1. else "reference_boundary_unresolved")
                scenarios.append({**scenario, "interaction_lower": float(lower), "interaction_upper": float(upper),
                                  "construction_status": status})
            result.append({"case_id": saved["case_id"], "state_id": saved["state_id"], "field": saved["field"],
                           "member": saved["member"], "include_boundary_point_actions": trace["boundary_point_actions_in_high_trace"],
                           "source_wrench_n_nmm": wrench, "continuous_base_reference_interaction": bound,
                           "scenarios": scenarios, "complete_cleat_resistance": None})
    current.require(len(result) == 24 and current.sha(OWN) == LOADED_SHA, "complete unchanged 24-trace producer required")
    current.verify(pins)
    return {"schema": "eoere_cleat_intact_section_reference/v1", "producer": current.ref(OWN),
            "inputs": input_ref, "current_cleat_demand": prior.DEMAND, "source_sha256": pins,
            "all_sources_unchanged": True, "geometry_revision": inputs["geometry_revision"],
            "hardware_revision": inputs["hardware_revision"], "extra_grid": False,
            "current_bolt_count": 100, "current_screw_count": 66, "traces": result,
            "status": "COMPLETE_SIX_COMPONENT_INTACT_SECTION_REFERENCE_CONDITIONAL_ON_DECLARED_MODEL",
            "complete_cleat_resistance": None, "complete_joint_or_member_resistance": None,
            "physical_demand_bounds_established": False, "structural_acceptance": False,
            "native_or_frame_solve_CAD_rebuild_geometry_change_or_actual_fit": False,
            "release": source["release"],
            "limits": ["The strength envelope and uniform divisor are owner-authorized engineering hypotheses, not assigned DF-L No.2 design values or a characteristic-to-NDS conversion. The whole-wrench multiplier is a declared scenario, not an authenticated EC5 load combination.",
                       "The polynomial field exactly carries all six section resultants and has zero normal shear on the rectangle sides. It is not a compatible three-dimensional elastic timber field, local bore stress or a fracture-resistance model.",
                       "The positive linear interaction rule is an explicit material-model assumption. Its continuous maximum is bounded by exact-rational tensor Bernstein subdivision, not a sampled-peak claim.",
                       "A construction exceedance is not a physical failure or a proof that every equilibrated field fails. Connection fracture, complete joints/members and physical response remain distinct subsequent qualifications. No redesign or panel/screw remedy is introduced."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
