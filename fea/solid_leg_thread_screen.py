"""Solid-leg thread inventory and conditional diameter comparison, not approval."""
import argparse
import hashlib
import json
from pathlib import Path

from fea import lumber_leg_resistance as resistance
from fea.bolt_thread_bearing import exposure
from mini_moonboard import lumber_leg_spread_frame as model
from mini_moonboard.connection_geometry import material_intervals
from mini_moonboard.selected_hardware import BoltSpec

ARCHIVE = Path("fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz")
LIMITS = (
    "Same archived forces; full-body diameter is a conditional reference, not a new FE solve. "
    "Actual thread/runout, bearing lengths and steel bending yield remain unverified. "
    "No axial/group/washer/splitting resistance, slip calibration or construction approval. "
    "The 4in length is an arithmetic trial, not installed CAD or selected procurement. "
    "Length-shortfall scenarios hold nominal thread length fixed, excluding runout; "
    "the separate minimum-body-length comparison includes a generic five-pitch allowance."
)


def full_body_reference(bearing):
    """Same TR12 assumptions; only modeled effective diameter changes."""
    original = resistance.bolt_reference(*bearing)
    inputs = dict(original["inputs"])
    diameter = .375
    inputs.update(main_bearing_lb_in=bearing[0]*diameter,
                  side_bearing_lb_in=bearing[1]*diameter,
                  main_yield_moment_lb_in=45000*diameter**3/6,
                  side_yield_moment_lb_in=45000*diameter**3/6)
    result = resistance.single_shear(**inputs)
    return {"reference_lateral_n": result["reference_lateral_lbf"]*4.4482216152605,
            "governing_mode": result["governing_mode"]}


def build():
    evidence = resistance.screen(ARCHIVE)
    if evidence["stock"] != "2x6" or evidence["geometry"] != "spread-100x50-top150" or evidence["extension_mm"] != 300:
        raise ValueError("Require the unchanged spread2x6/e300 trial")
    parts = {p.name: p for p in model.parts("2x6", 300., False)}
    bolts = [c for c in model.connections("2x6", 300.) if c.name.startswith("lumber_leg_bolt_")]
    if len(bolts) != 8:
        raise ValueError("Require all eight leg bolts")
    stacks = []
    for bolt in bolts:
        spec = BoltSpec("Dimensional family only", bolt.length, bolt.grip, 1.524)
        members = []
        for name in bolt.members:
            intervals = material_intervals(parts[name].shape, bolt.start, bolt.direction, 0., bolt.length)
            if len(intervals) != 1:
                raise ValueError("Require one continuous raw bearing interval")
            entry, end = intervals[0]
            scenarios = []
            for length in (95.25, 101.6):
                for shortfall in (0., spec.length_under_tolerance_mm):
                    value = exposure(entry, end, length-shortfall, spec.thread_length_reference_mm)
                    scenarios.append({"nominal_length_mm": length, "length_shortfall_mm": shortfall,
                        **value, "quarter_margin_mm": (end-entry)/4-value["threaded_bearing_mm"]})
            minimum_body = [{"nominal_length_mm": length,
                "generic_minimum_body_length_mm": length-spec.thread_length_reference_mm-5*spec.pitch_mm,
                "quarter_condition_margin_mm": length-spec.thread_length_reference_mm-5*spec.pitch_mm
                    -(end-(end-entry)/4)} for length in (95.25, 101.6)]
            members.append({"member": name, "raw_interval_mm": [entry, end],
                "minimum_full_body_length_for_quarter_condition_mm": end-(end-entry)/4,
                "generic_runout_screen_not_product_certification": minimum_body,
                "scenarios": scenarios})
        stacks.append({"bolt": bolt.name, "members": members})
    rows = []
    for stiffness in ("k100", "k1000", "k10000"):
        for weight in (150, 200, 250, 300):
            choices = []
            for row in evidence["rows"]:
                if row["stiffness"] != stiffness or row["case"]["climber_lb"] != weight:
                    continue
                for name, bolt in row["bolts"].items():
                    full = full_body_reference(bolt["directional_reference"]["rim_leg_bearing_psi"])
                    choices.append({"case": row["case"], "bolt": name,
                        "force_xyz_n": bolt["force_xyz_n"], "lateral_n": bolt["lateral_n"],
                        "root_reference": bolt["directional_reference"],
                        "conditional_full_body_reference": full,
                        "conditional_full_body_ratio": bolt["lateral_n"]/full["reference_lateral_n"]})
            rows.append({"stiffness": stiffness, "climber_lb": weight,
                "governing_root": max(choices, key=lambda r: r["root_reference"]["lateral_demand_reference_ratio"]),
                "governing_conditional_full_body": max(choices, key=lambda r: r["conditional_full_body_ratio"])})
    sources = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
        "fea/solid_leg_thread_screen.py", "fea/lumber_leg_resistance.py", "fea/dowel_yield.py",
        "fea/bolt_thread_bearing.py", "mini_moonboard/connection_geometry.py",
        "mini_moonboard/selected_hardware.py")}
    return {"archive": str(ARCHIVE), "archive_sha256": evidence["archive_sha256"],
        "source_sha256": sources, "qualified_for_design": False,
        "full_body_exception_verified": False, "limits": LIMITS, "stacks": stacks, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    content = json.dumps(build(), indent=2, allow_nan=False)+"\n"
    if args.output:
        with args.output.open("x") as output:
            output.write(content)
    else:
        print(content, end="")
