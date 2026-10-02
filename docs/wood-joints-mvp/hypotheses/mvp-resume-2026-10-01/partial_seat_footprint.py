"""Conditional supported central bearing footprint at the partial washer seat.

Do not credit the unsupported outer washer crescent. Check whether a declared
central load footprint is supported by the unchanged finished timber, using
the simultaneous current six-case axial forces. Actual nut/washer contact
and metal transfer remain separate from this conditional wood reference.
"""

import argparse
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
import remaining_joint_screen as screen
import top_corner_local as local

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
RESPONSE = HERE / "top-and-service-frame-attempt02"
BODY, AXIS = "base_principal_center_right", "center_principal_right_2"
SEAT = np.array([50.95, -90.30983137880766, 367.0102220661388])


def run(output, *, frame_dir=FRAME, clearance=RESPONSE, metadata_seed_dir=None,
        inner_diameter_mm=7.3):
    local.require(not output.exists(), "preserve existing footprint output")
    binding = screen.bind_frame_sources(frame_dir, clearance, metadata_seed_dir)
    frame, response_dir = binding["frame_dir"], binding["clearance_dir"]
    case_report = binding["comparison"]
    local.require(math.isfinite(inner_diameter_mm) and 7.3 <= inner_diameter_mm < 10,
                  "central opening must cover the saved 7.3 mm bore and stay below 10 mm")
    inputs = local.read(local.INPUTS)
    geometry = next(
        m["reduced_geometry_descriptor"]
        for m in inputs["members"]
        if m["member_id"] == BODY
    )
    step = ROOT / geometry["step_path"]
    expected = "9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58"
    local.require(local.sha(step) == expected, "changed partial-seat finished timber")
    shape = cq.importers.importStep(str(step)).val()
    local.require(shape.isValid() and len(shape.Solids()) == 1, "invalid timber")
    center = (np.array(geometry["start"]) + geometry["end"]) / 2
    inward = np.array([float(np.sign(center[0] - SEAT[0])), 0.0, 0.0])
    local.require(float((center - SEAT) @ inward) > 0, "wrong inward footprint")
    inner, outer = inner_diameter_mm / 2, 10.0 / 2
    probes = []
    for depth in (0.01, 0.05, 0.1):
        ring = (
            cq.Workplane(cq.Plane(origin=tuple(SEAT), normal=tuple(inward)))
            .circle(outer)
            .circle(inner)
            .extrude(depth)
            .val()
        )
        fraction = ring.intersect(shape).Volume() / ring.Volume()
        local.require(abs(fraction - 1) < 1e-6, "central footprint not supported")
        probes.append({"depth_mm": depth, "supported_fraction": fraction})
    rows = binding["rows"]
    row = rows[1535]
    local.require(
        row["row"] == 1535 and row["row_id"] == AXIS + "/outer-seat-axial-tie",
        "changed axial tie identity",
    )
    material_path = local.actions_method.MATERIALS
    fc = (
        local.read(material_path)["conditional_DF_L_No2_base_row"]["base_properties"][
            "Fc_perpendicular"
        ]
        * local.PSI_MPA
    )
    area = math.pi * (outer**2 - inner**2)
    states = []
    with np.load(response_dir / "response.npz", allow_pickle=False) as data:
        for case in [s for s in case_report["states"] if s["gap_scale"] == 1]:
            tension = float(data[case["case_id"] + "_gap_raw_force_n"][1535])
            pressure = max(tension, 0) / area
            states.append(
                {
                    "case_id": case["case_id"],
                    "signed_tie_n": tension,
                    "declared_central_mean_pressure_mpa": pressure,
                    "central_mean_pressure_over_base_Fc_perp": pressure / fc,
                    "minimum_equal_area_outer_circle_diameter_mm": 2
                    * math.sqrt(inner**2 + max(tension, 0) / (math.pi * fc)),
                }
            )
    pins = dict(binding["pins"])
    for p in [
        Path(__file__),
        local.INPUTS,
        material_path,
        step,
        frame / "row-identities.json",
        response_dir / "comparison.json",
        response_dir / "response.npz",
    ]:
        pins[p] = local.sha(p)
    for p, h in pins.items():
        local.require(local.sha(p) == h, "changed footprint source: " + str(p))
    report = {
        "schema": "partial_seat_supported_central_footprint/v1",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "source_force_state_scope": binding["force_scope"],
        "frame_operator_directory": str(frame.relative_to(ROOT)),
        "clearance_source_directory": str(response_dir.relative_to(ROOT)),
        "metadata_seed_directory": str(binding["metadata_seed_dir"].relative_to(ROOT)),
        "axis_id": AXIS,
        "body": BODY,
        "seat_point_mm": SEAT.tolist(),
        "declared_outer_inner_diameters_mm": [2 * outer, 2 * inner],
        "central_area_mm2": area,
        "geometry_probes": probes,
        "conditional_base_Fc_perpendicular_mpa": fc,
        "states": states,
        "limits": [
            "Only the declared central ring is credited; the original outer washer crescent remains unsupported.",
            "Uniform pressure on this central footprint is an assumed load-transfer scenario, not an actual contact solution.",
            "The actual nut bearing footprint and compatible washer compression/bridging must support this route before it becomes a hardware disposition.",
            "The minimum equivalent circle is an area requirement, not an inspected bearing face or a washer product specification.",
        ],
        "geometry_changed": False,
        "reviewed_geometry_changed": bool(binding["model"].get("owner_authorized_screw_movements")),
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    output.mkdir()
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        "central footprint area",
        area,
        "peak pressure ratio",
        max(s["central_mean_pressure_over_base_Fc_perp"] for s in states),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frame", type=Path, default=FRAME)
    parser.add_argument("--clearance", type=Path, default=RESPONSE)
    parser.add_argument("--metadata-seed", type=Path)
    parser.add_argument("--inner-diameter-mm", type=float, default=7.3)
    args = parser.parse_args()
    run(args.output.resolve(), frame_dir=args.frame, clearance=args.clearance,
        metadata_seed_dir=args.metadata_seed, inner_diameter_mm=args.inner_diameter_mm)
