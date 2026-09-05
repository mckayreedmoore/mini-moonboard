"""Actual extended-leg CAD mass/support sweep; no contact or joint-capacity FEA."""
import hashlib
import json
import math
from pathlib import Path

from fea.user_load_envelope import GRAVITY, envelope, hold_locations, hull
from mini_moonboard.stability import evaluate_load, load_cases, row_point

EXTENSIONS_MM = (0, 50, 100, 150, 200)
WEIGHTS_LB = (150, 200, 250, 300)
OUTPUT = Path("fea/results/hybrid/physical_footprint.json")
SOURCES = (
    "fea/physical_footprint.py", "fea/user_load_envelope.py",
    "mini_moonboard/footprint_frame.py", "mini_moonboard/shallow_frame.py",
    "mini_moonboard/hybrid_frame.py", "mini_moonboard/hybrid.py",
    "mini_moonboard/box_frame.py", "mini_moonboard/model.py",
    "mini_moonboard/panel_grid.py", "mini_moonboard/stability.py",
)


def cad_state(extension_mm):
    from mini_moonboard.footprint_frame import parts

    items = parts(extension_mm, drilled=True)
    masses = [p.shape.Volume()/1e9*(7850 if p.name.startswith("angle_") else 600)
              for p in items]
    mass = sum(masses)
    centre = [sum(m*p.shape.centerOfMass(p.shape).toTuple()[axis]
                  for m, p in zip(masses, items, strict=True))/mass for axis in range(3)]
    points = [v.Center().toTuple()[:2] for p in items for face in p.shape.Faces()
              if abs(face.BoundingBox().zmin) < 1e-5 and abs(face.BoundingBox().zmax) < 1e-5
              for v in face.Vertices()]
    return {"extension_mm": extension_mm, "mass_kg": mass,
            "centre_xy_mm": centre[:2], "centre_xyz_mm": centre,
            "support_polygon_mm": hull(points), "part_count": len(items)}


def evaluate(state):
    cases = envelope(state, hold_locations(), WEIGHTS_LB)
    for case in cases:
        vertical = state["mass_kg"]*case["mass_scale"]*GRAVITY+case["downward_n"]
        direction = case["governing"]["horizontal_direction_xy"]
        case["global_floor_force_n"] = [-case["horizontal_n"]*d for d in direction]+[vertical]
        case["global_floor_resultant_n"] = math.hypot(vertical, case["horizontal_n"])
    legacy = []
    y, z = row_point(12)
    for load in load_cases():
        result = evaluate_load(mass_kg=state["mass_kg"], centre_y_mm=state["centre_xy_mm"][1],
            kicker_toe_y_mm=min(p[1] for p in state["support_polygon_mm"]),
            leg_toe_y_mm=max(p[1] for p in state["support_polygon_mm"]),
            load_y_mm=y, load_z_mm=z, load=load)
        legacy.append({"name": load.name, "basis": load.basis, "force_yz_n": [load.force_y_n, load.force_z_n],
            "load_yz_mm": [y, z], "kicker_reaction_n": result.kicker_reaction_n,
            "leg_reaction_n": result.leg_reaction_n, "status": result.status,
            "overturning_factor": result.overturning_factor if math.isfinite(result.overturning_factor) else None,
            "friction_required": result.friction_required})
    return {"state": state, "cases": cases, "legacy_2d_cases": legacy,
            "minimum_factor": min(c["governing"]["factor"] for c in cases if c["governing"]["factor"] is not None),
            "below_screen_count": sum(c["status"] != "MEETS MOMENT SCREEN ONLY" for c in cases),
            "maximum_global_floor_resultant_n": max(c["global_floor_resultant_n"] for c in cases)}


def build_report():
    candidates = {str(extension): evaluate(cad_state(extension)) for extension in EXTENSIONS_MM}
    passing = [extension for extension in EXTENSIONS_MM if not candidates[str(extension)]["below_screen_count"]]
    return {
        "assumptions": "One climber: 250 lb intended maximum; 150/200 lb comparisons and 300 lb sensitivity, not a rating. Actual drilled CAD wood at 600 kg/m3 and custom steel angles at 7850 kg/m3; fasteners, holds, glue, LEDs omitted. Recompute mass, CG and level floor contact hull for each physical leg geometry; 0.8 mass sensitivity freezes each candidate CG. 1x/2x gravity, 0/300 N horizontal all azimuths, 0/50/100 mm hold standoff are illustrative, not validated governing loads. Rigid-body edge moment screen target 1.5; no measured friction, contact deformation, yaw balance, strengths or approval. Legacy six loads are separately retained at row 12 and full modelled mass.",
        "joint_demand_proxy_warning": "Global floor force/resultant is total external support demand only, not an individual joint, leg, bolt or screw force, nor a capacity check. Its horizontal direction is the governing edge direction for that row; vertical reaction sum is independent of direction. Negative legacy toe reactions mean uplift, not tensile floor restraint. Actual support-force distribution requires contact/joint analysis.",
        "source_sha256": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
        "climber_weights_lb": WEIGHTS_LB, "extensions_mm": EXTENSIONS_MM,
        "minimum_tested_extension_meeting_all_96_cases_mm": min(passing) if passing else None,
        "candidates": candidates,
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build_report(), indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
