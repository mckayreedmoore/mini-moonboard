"""Compare selected-stack geometry; preserve unknown current resistance."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
PACKET = Path(__file__).resolve().parent
DOC = PACKET.parent
SHOP = DOC / "shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1"


def build():
    sources = [DOC / "occupied-selected-hardware-v1.json", SHOP / "hardware-selection.csv",
               SHOP / "mechanical-change-review.json",
               DOC / "bounded-strength-v1/connected-stack-followup-v1/result.json",
               DOC / "bounded-strength-v1/connected-stack-followup-v1/verification.json",
               Path(__file__).resolve()]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    pins = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    layout = json.loads(sources[0].read_bytes())
    rows = {r["axis_id"]: r for r in csv.DictReader(sources[1].open())}
    assert len(rows) == len(layout["selected_stacks"]) == 100
    headers = [f"eoere_bolt_{i:03}" for i in (65, 66, 79, 80)]
    cleats = [f"eoere_bolt_{i:03}" for i in (67, 70, 71, 74)]
    mixed = []
    for name in headers + cleats:
        r = rows[name]
        shortage = max(0., -float(r["body_to_farthest_wood_plate_end_margin_mm"]))
        mixed.append({"axis_id": name,
            "minimum_body_mm": float(r["minimum_body_mm"]),
            "nominal_far_interface_margin_mm": float(r["body_to_farthest_wood_plate_end_margin_mm"]),
            "potential_far_cleat_thread_runout_length_mm": shortage if name in cleats else 0.,
            "potential_far_cleat_fraction": shortage / 38.1 if name in cleats else 0.,
            "delivered_thread_profile_verified": False, "current_complete_resistance": None})
    assert all(r["potential_far_cleat_fraction"] > .25 for r in mixed[4:])
    current = json.loads(sources[2].read_bytes())
    unresolved = [
        {"topic": "raised screw ends", "known": "Z212, post top 26.9 mm, side 19.05 mm; full nominal backing.",
         "missing": "Hillman-specific end/splitting, withdrawal/head resistance and simultaneous current screw actions."},
        {"topic": "eight mixed stacks", "known": "Own old prescribed-action equilibrium trials; four new header bodies cover nominal far interfaces.",
         "missing": "Current simultaneous member wrenches and compatible whole-stack yield/contact law; no summed isolated capacities."},
        {"topic": "spacer/washer contact", "known": "Eight nominal annular spacers are shown between nut washer and nut.",
         "missing": "Actual flatness/chamfers, coating, steel resistance, washer bending, eccentricity and axial seat forces; no torque/preload value assigned."},
        {"topic": "thread bearing", "known": "92 rows do not establish full smooth body through all far wood.",
         "missing": "Delivered axial body/runout/root intervals and applicable connected wood/steel bearing/yield treatment."},
        {"topic": "finished sections", "known": "Restored principal adds wood; optional grid subtracts panel/rail material.",
         "missing": "Current signed section demands, cut-aware strength/stability and panel participation; gross-stock operators do not resolve local cuts."},
        {"topic": "restraint/applicability", "known": "Preceding response uses compression-only floor points and rear-leg XY restraints.",
         "missing": "Justified physical restraint/load path and first-order applicability. No floor-friction test or anchor is introduced."},
        {"topic": "complete joints", "known": "Current geometry, nominal catalog windows and access are separate evidence.",
         "missing": "Compatible connection behavior under simultaneous actions, joint resistance and product-specific formed-angle properties."},
    ]
    result = {"schema": "eoere_selected_hardware_bounded_review/v1", "revision": layout["revision"],
        "source_sha256": pins, "mixed_stack_geometry": mixed,
        "nominal_projection_areas_mm2": {
            "spacer_annulus": math.pi / 4 * (19.05**2 - 10.31875**2),
            "washer_spacer_overlap": math.pi / 4 * (19.05**2 - 11.1125**2),
            "ideal_hex_nut_spacer_overlap": math.sqrt(3) / 2 * 14.2875**2 - math.pi / 4 * 10.31875**2},
        "contact_area_limits": "Ideal planar nominal projections only; chamfers, tolerances, contact pressure and resistance are not established.",
        "current_screw_placement": current["screw_placement"],
        "unresolved": [{**row, "current_resistance": None} for row in unresolved],
        "current_response_computed": False, "historical_pass_transferred": False,
        "reference_exceedances_retained": True, "actual_observations": None,
        "fabrication_released": False, "climbing_released": False}
    assert all(digest(ROOT / name) == expected for name, expected in pins.items())
    return (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.out.open("xb") as handle:
        handle.write(build())
