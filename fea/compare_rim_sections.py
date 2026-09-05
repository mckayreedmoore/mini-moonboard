"""Gross side-rim section comparison, NOT a whole-frame FEA substitute."""
import hashlib
import json
import math
from pathlib import Path

from mini_moonboard.box_frame import DEPTH, THICKNESS
from mini_moonboard.hybrid import WIDTHS
from mini_moonboard.model import PANEL_THICKNESS_MM

DIRECTORY=Path(__file__).resolve().parent/"results"


def section(thickness, depth):
    if any(not math.isfinite(v) or v<=0 for v in (thickness,depth)):
        raise ValueError("Positive finite section dimensions required")
    return {"area_mm2":thickness*depth,
            "I_normal_mm4":thickness*depth**3/12,
            "I_lateral_mm4":depth*thickness**3/12,
            "Z_normal_mm3":thickness*depth**2/6,
            "Z_lateral_mm3":depth*thickness**2/6}


def compare():
    evidence=DIRECTORY/"box_audited_40_7000.json"
    old=json.loads(evidence.read_text())
    modulus=old["modulus_mpa"]
    baseline=section(THICKNESS,DEPTH+PANEL_THICKNESS_MM)
    rows=[]
    for name,depth in {"plywood":DEPTH+PANEL_THICKNESS_MM,**WIDTHS}.items():
        properties=section(THICKNESS,depth)
        rows.append({"name":name,"thickness_mm":THICKNESS,"depth_mm":depth,
            **properties,
            "gross_volume_ratio_same_length":properties["area_mm2"]/baseline["area_mm2"],
            "equal_E_normal_EI_ratio":properties["I_normal_mm4"]/baseline["I_normal_mm4"],
            "equal_E_lateral_EI_ratio":properties["I_lateral_mm4"]/baseline["I_lateral_mm4"],
            "same_normal_moment_stress_ratio":baseline["Z_normal_mm3"]/properties["Z_normal_mm3"],
            "E_to_match_baseline_normal_EI_mpa":modulus*baseline["I_normal_mm4"]/properties["I_normal_mm4"],
            "normal_EI_sensitivity":[{"assumed_E_mpa":modulus*factor,
                "EI_ratio_to_plywood":factor*properties["I_normal_mm4"]/baseline["I_normal_mm4"]}
                for factor in (.5,1,1.5,2)]})
    return {"status":"ANALYTICAL GROSS SECTION SCREEN ONLY; no new FEA solve",
            "baseline_assumed_E_mpa":modulus,
            "baseline_result_file":evidence.name,
            "baseline_result_sha256":hashlib.sha256(evidence.read_bytes()).hexdigest(),
            "scope":"Side rims only, same length and bending axis. Gross homogeneous rectangular sections; perfect plywood lamination. No holes, joints, frame action, shear deflection, torsion or material failure. Sensitivity moduli are assumptions, not selected lumber properties or bounds. Do not scale old whole-frame displacements by these ratios.",
            "sections":rows}


if __name__=="__main__":
    output=DIRECTORY/"hybrid_rim_sections.json"
    output.write_text(json.dumps(compare(),indent=2)+"\n")
    print(output)
