"""New minimum cap-head face scenario using the frozen washer plate method."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
METHODS = PACKET / "steel-resistance-methods-v4.json"
METHODS_SHA = "d00ff10eb875c0d093f6c0e811a7b1e2ef850f6d3ec846b6b910eb2c4cdabf19"
ASME = "https://www.wanhong-fastener.com/wp-content/uploads/2025/04/ASME-B18.2.1-2012.pdf"
BEARING_DIAMETER_MM = 17.145


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate() -> dict:
    if sha(METHODS) != METHODS_SHA:
        raise ValueError("issued washer method evidence changed")
    methods = json.loads(METHODS.read_text())
    for relative, expected in methods["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"frozen method dependency changed: {relative}")
    from scripts.thin_bolted_steel_resistance import LAYOUT, washer_axisymmetric_bending

    layout = json.loads(LAYOUT.read_text())
    seats = {(r["axis_id"], r["role"]): r for r in layout["washer_seats"]}
    selected = [r for r in methods["washer_reference_inputs"]
                if r["small_washer_product"] and r["role"] == "head_washer"]
    profiles = {}
    ends = []
    for row in selected:
        seat = seats[(row["axis_id"], row["role"])]
        if seat["support_material"] != "steel":
            raise ValueError("new cap-head reference is restricted to the steel-supported head ends")
        opening, thickness = seat["planned_support_opening_mm"], row["minimum_published_thickness_mm"]
        identity = f"cap-half-face17.145-opening{opening}-thickness{thickness}"
        if identity not in profiles:
            old = methods["washer_bending_profiles"][row["bearing_circle_sensitivity_profile_ids"][0]]
            corners = []
            for corner in old["small_washer_tolerance_corner_comparisons"]:
                inside, outside = corner["id_mm"], corner["od_mm"]
                corners.append(washer_axisymmetric_bending(axial_n=1., inner_radius_mm=inside / 2.,
                    outer_radius_mm=outside / 2., bearing_radius_mm=BEARING_DIAMETER_MM / 2.,
                    support_opening_radius_mm=opening / 2., thickness_mm=thickness)
                    | {"id_mm": inside, "od_mm": outside})
            profiles[identity] = {"assumed_circular_bearing_diameter_mm": BEARING_DIAMETER_MM,
                                  "support_opening_mm": opening, "minimum_washer_thickness_mm": thickness,
                                  "tolerance_corner_comparisons": corners,
                                  "unit_axial_two_face_bending": max(corners,
                                      key=lambda r: r["required_fy_mpa_at_sampled_bending_first_yield"])}
        ends.append({"axis_id": row["axis_id"], "role": row["role"], "support_material": "steel",
                     "profile_id": identity})
    if len(ends) != 12:
        raise ValueError("expected twelve small steel-supported cap-head ends")
    return {"schema": "thin_bolted_cap_head_unit_reference/v1", "candidate": methods["candidate"],
            "status": "CONDITIONAL_CHANGED_HEAD_FACE_INPUT_UNIT_REFERENCE",
            "source_sha256": {str(METHODS.relative_to(ROOT)): METHODS_SHA,
                              "scripts/thin_bolted_steel_resistance.py": methods["source_sha256"]["scripts/thin_bolted_steel_resistance.py"],
                              str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
            "standard_source": {"url": ASME, "edition": "ASME B18.2.1-2012",
                                "clause": "4.3, printed page9/PDF page18; Table6 and Table10",
                                "maximum_half_inch_cap_AF_in": .750, "face_min_factor": .9,
                                "derived_minimum_face_diameter_mm": BEARING_DIAMETER_MM,
                                "diameter_gaging_offset_toward_head_mm": .004 * 25.4,
                                "maximum_underhead_fillet_diameter_mm": .550 * 25.4,
                                "source_pdf_byte_hash_available": False,
                                "actual_product_conformance_or_contact_circle_verified": False},
            "ends": ends, "profiles": profiles,
            "limits": ["This is a new assumed circular head footprint; the standard's gaged diameter does not establish actual contact pressure.",
                       "The small washer ID13.3604..13.8684mm is below the allowed maximum fillet diameter13.97mm; actual seating/chamfer/fillet requires reconciliation.",
                       "The two small nut washers retain unresolved nut-face geometry and are outside this head-only scenario.",
                       "Same-end moments, unilateral contact, thick-washer/local bearing and numeric washer yield remain unresolved."],
            "native_or_CAD_execution": False, "prior_unit_responses_recomputed": False,
            "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET / "cap-head-face-reference-v4.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued head-face reference")
    result = evaluate()
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "head_ends": len(result["ends"]),
                      "unit_required_fy_mpa_per_n": [p["unit_axial_two_face_bending"]["required_fy_mpa_at_sampled_bending_first_yield"]
                                                     for p in result["profiles"].values()]}, indent=2))


if __name__ == "__main__":
    main()
