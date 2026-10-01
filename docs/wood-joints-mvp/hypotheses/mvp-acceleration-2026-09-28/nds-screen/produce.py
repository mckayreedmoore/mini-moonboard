"""Explicit single-bolt scenarios; no candidate capacity or acceptance."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.dowel_yield import single_shear


def calculate(diameter, main_length, side_length, main_fe, side_fe, theta):
    moment = 45000 * diameter**3 / 6
    ktheta = 1 + 0.25 * theta / 90
    return single_shear(
        main_length_in=main_length, side_length_in=side_length,
        main_bearing_lb_in=main_fe * diameter,
        side_bearing_lb_in=side_fe * diameter,
        main_yield_moment_lb_in=moment, side_yield_moment_lb_in=moment,
        gap_in=0,
        reduction_terms={key: factor * ktheta for key, factor in
                         {"Im": 4, "Is": 4, "II": 3.6, "IIIm": 3.2,
                          "IIIs": 3.2, "IV": 3.2}.items()},
    )


def produce():
    # Published TR12 Example 3.1: 1/2-inch bolt, two 1.5-inch members,
    # Fe=4800 psi, Fyb=45000 psi. Compare independently published rounded modes.
    benchmark = calculate(0.5, 1.5, 1.5, 4800, 4800, 0)
    expected = {"Im": 900, "Is": 900, "II": 414, "IIIm": 550,
                "IIIs": 550, "IV": 663}
    for mode, value in expected.items():
        assert abs(benchmark["reference_values_lbf"][mode] - value) < 0.6
    assert benchmark["governing_mode"] == "II"

    rows = []
    for main_angle, side_angle in ((0, 0), (0, 90), (90, 0), (90, 90)):
        main_fe = 5600 if main_angle == 0 else 4450
        side_fe = 5600 if side_angle == 0 else 4450
        angle = max(main_angle, side_angle)
        result = calculate(0.25, 3.5, 1.5, main_fe, side_fe, angle)
        # Independent closed-form NDS mode IV, without the TR12 quadratic helper.
        ratio = main_fe / side_fe
        direct_iv = (0.25**2 / (3.2 * (1 + 0.25 * angle / 90))
                     * math.sqrt(2 * main_fe * 45000 / (3 * (1 + ratio))))
        assert math.isclose(result["reference_values_lbf"]["IV"], direct_iv,
                            rel_tol=1e-12)
        rows.append({
            "main_load_to_grain_degrees": main_angle,
            "side_load_to_grain_degrees": side_angle,
            "main_bearing_psi": main_fe, "side_bearing_psi": side_fe,
            **result,
            "reference_lateral_N": result["reference_lateral_lbf"] * 4.4482216152605,
            "independent_mode_IV_lbf": direct_iv,
        })
    return {
        "mechanical_acceptance": False,
        "scope": "Unadjusted individual single-shear lateral reference scenarios only",
        "inputs": {
            "diameter_in": 0.25, "main_bearing_length_in": 3.5,
            "side_bearing_length_in": 1.5, "gap_in": 0,
            "bolt_bending_yield_psi": 45000,
            "wood_specific_gravity_scenario": 0.5,
            "bolt_axis_to_each_grain_degrees": 90,
            "bearing_basis": "Explicit rounded Fe: parallel 5600 psi, perpendicular 4450 psi",
            "shank_basis": "Full-body smooth diameter throughout both bearing lengths",
        },
        "sources": {
            "NDS_2024_chapter_12": {
                "url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
                "downloaded_pdf_sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
                "basis": "Chapter 12 lateral-yield provisions; Table 12A full-body 45000 psi basis",
            },
            "helper": {
                "path": "fea/dowel_yield.py",
                "sha256": hashlib.sha256((ROOT / "fea/dowel_yield.py").read_bytes()).hexdigest(),
            },
        },
        "verification": {
            "TR12_example_3_1_all_six_modes_within_0_6_lbf": True,
            "NDS_mode_IV_independent_closed_form_matches_all_rows": True,
        },
        "rows": rows,
        "exclusions": [
            "End-grain-axis connections and their adjustments",
            "Group action, load sharing, geometry and service adjustments",
            "Threads in bearing, actual bolt conformity and hardware fit",
            "Axial or combined actions, splitting, tear-out, washers and complete joint behavior",
            "Current joint demands or acceptance of any candidate criterion",
        ],
    }


if __name__ == "__main__":
    target = HERE / "single-bolt-scenarios.json"
    content = json.dumps(produce(), indent=2) + "\n"
    if sys.argv[1:] == ["--write"]:
        target.write_text(content)
        print("Wrote four single-bolt scenarios; benchmark and independent mode IV checks passed")
    elif sys.argv[1:] == ["--verify"]:
        assert target.read_text() == content, "Scenario artifact differs from recomputed result"
        print("Verified four scenarios, source-helper hash, benchmark and independent mode IV")
    else:
        raise SystemExit("Use --write or --verify")
