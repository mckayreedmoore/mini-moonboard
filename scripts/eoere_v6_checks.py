"""Apply the existing conventional worksheets to the current 96-bolt fields.

Frozen source formulas stay intact. Explicit adapters bind the current census,
purchase rows, plywood walls, all twelve dedicated shafts and all six fields.
These are conditional reference comparisons, not complete joint acceptance.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import eoere_requested_cleat_screen as rows
from scripts import eoere_v6_analysis as analysis
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
GEOMETRY, RUN = analysis.GEOMETRY, analysis.RUN
REVIEW = analysis.BASE / "review"
OUT = REVIEW / "complete-v1"
DEDICATED = {f"eoere_bolt_{i:03d}" for i in (67, 70, 71, 74, 81, 82, 83, 84)} | {
    f"cleat_post_bolt_{s}_{i}" for s in ("left", "right") for i in (1, 2)}
HARDWARE = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/"
                "eoere-successor-v1/leg-header-v3/hardware-selection.csv")


def load_available():
    pins = {ref(p)["path"]: sha(p) for p in (OWN, analysis.OWN, HARDWARE, analysis.MATERIAL, analysis.INPUTS)}
    g = read(GEOMETRY, pins)
    assert g["revision"] == analysis.REVISION and g["perfect_bond_analysis"] and len(g["axes"]) == 96
    fields = []
    for case in CASES:
        folder = RUN / case
        if not all((folder / n).exists() for n in ("field.json", "independent-replay.json", "independent-replay-plywood.json")):
            continue
        f = read(folder / "field.json", pins)
        r = read(folder / "independent-replay.json", pins)
        p = read(folder / "independent-replay-plywood.json", pins)
        binding = ref(folder / "field.json")
        assert r["field"] == p["field"] == binding and f["trial_parent_geometry"] == ref(GEOMETRY)
        assert r["false_screw_and_floor_forces_rejected"] and r["same_state_declared_fixed_floor_replayed"]
        assert r["all_credited_hosts_in_bearing"] and r["equilibrium"]["gradient_inf_n"] < 1e-5
        assert r["equilibrium"]["physical_body_count"] == f["counts"]["physical_bodies"] == 148
        assert len(p["raw_operator_checks"]) == 2 and f["counts"]["shaft"] == 96 and f["counts"]["fitting"] == 24
        assert len(f["panel_screw_actions"]) == len(g["screw_axes"]) == 66
        parameters = f["source_inputs"]["scenario"]["climber_load_parameters"]
        assert parameters["input_weight"] == 250 and parameters["input_unit"] == "lb"
        assert parameters["downward_multiplier"] == 2. and parameters["horizontal_force_n"] == 300.
        fields.append(("nominal", case, binding, f))
    assert fields
    return g, fields, pins


def load():
    g, fields, pins = load_available()
    assert len(fields) == 6, "six own independently admitted fields required"
    return g, fields, pins


def selections(g):
    with (ROOT / HARDWARE).open() as stream:
        old = {r["axis_id"]: r for r in csv.DictReader(stream)}
    proposed = {r["axis_id"]: r for r in g["selected_stack_overrides"]}
    result = []
    for axis in g["axes"]:
        row = {**old.get(axis["id"], {}), **proposed[axis["id"]]}
        row.update(selected_diameter_mm=axis["diameter_mm"],
                   receiver_member_ids=";".join(axis["receivers"]),
                   model_underhead_length_mm=axis["nominal_under_head_length_mm"],
                   minimum_body_mm=float(row.get("minimum_full_body_mm") or row["minimum_body_mm"]))
        assert row["minimum_body_mm"] > 0 and float(row["selected_underhead_length_mm"]) > 0
        result.append(row)
    assert len(result) == len({r["axis_id"] for r in result}) == 96
    assert sum("A574" in r["selected_bolt_grade"] for r in result) == 12
    assert sum("Grade 5" in r["selected_bolt_grade"] for r in result) == 84
    return result


def methods():
    if str(analysis.WORK) not in sys.path:
        sys.path.insert(0, str(analysis.WORK))
    for name in ("owner_frame_basis", "up15_basis", "resolved_frame_basis", "single_knee_basis", "central_front_basis"):
        sys.modules[name] = sys.modules[__name__]
    import owner_frame_reviews as original
    import owner_roundoff_closure as closure
    return original, closure


def replace(source, before, after):
    assert source.count(before) == 1, (before, source.count(before))
    return source.replace(before, after)


def preflight(original):
    source = inspect.getsource(original.preflight)
    source = re.sub(r"(?<!\d)92(?!\d)", "96", source)
    for before, after in [(" == 146", " == 148"),
                          ("MINIMUM_CREDITED_PLYWOOD_MM = 18.25", "MINIMUM_CREDITED_PLYWOOD_MM = 36.5"),
                          ("owner-requested-cases-v3/material.json", "owner-principal-pairs-v6/analysis-v1/material.json")]:
        source = replace(source, before, after)
    source = source.replace("Nominal19.05mm leaves receive only a central18.25mm bearing interval",
                            "Nominal38.1mm pairs receive only a central36.5mm bearing interval")
    namespace = {**vars(original), "OWN": OWN, "basis": sys.modules[__name__]}
    exec(compile(source, str(OWN), "exec"), namespace)  # noqa: S102 -- source-bound worksheet routing
    for _, case, binding, _ in load()[1]:
        output = OUT / f"nominal-{case}-shafts-preflight-v1.json"
        assert not output.exists()
        try:
            namespace["preflight"]((ROOT / binding["path"]).parent, output)
        except KeyError as error:
            # A frozen print uses a deliberately removed rectangular-row column.
            assert error.args == ("maximum_plywood_center_based_row_tear_index",) and output.exists()
        report = json.loads(output.read_bytes())
        report["source_sha256"].update({ref(p)["path"]: sha(p) for p in (OWN, original.OWN)})
        report["superseded_rectangular_row_print_omitted"] = True
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def worksheet(kind):
    original, closure = methods()
    OUT.mkdir(parents=True, exist_ok=True)
    if kind == "preflight":
        preflight(original)
        return
    old_intake = original.intake
    closed = "closed = {'eoere_bolt_071', 'eoere_bolt_074'} | {f'cleat_post_bolt_{s}_{i}' for s in ('left', 'right') for i in (1, 2)} | {f'eoere_bolt_{i:03d}' for i in range(81, 85)}"

    def intake(path, *args, **kwargs):
        code = old_intake(path, *args, **kwargs)
        if path.name == "shaft_group_factor.py":
            code = replace(code, closed, "closed = DEDICATED")
            code = replace(code, "        if set(identities) & closed:",
                           "        if set(identities) & closed:\n            assert 1 <= len(identities) <= 2, 'universal 0.5 group bound requires n<=2'")
            code = code.replace("completed cleat retains its original conservative factor", "current n<=2 complete-receiver group uses universal 0.5 bound")
            code = code.replace("The completed cleat calculations retain their own Cg/Cdelta and are not superseded by this frame screen.",
                                "All twelve dedicated shafts use only the universal n<=2 Cg lower bound; all current end/edge adjustments follow separately.")
        if path.name == "shaft_local_review.py":
            code = replace(code, "'geometry': ref(RAW/'three-pin-shift-geometry-v1/geometry.json')", "'geometry': ref(GEOMETRY)")
        if path.name == "shaft_bearing_blocks.py":
            code = replace(code, closed, "closed = set()")
            code = replace(code, "assert len(rows) == 82", "assert len(rows) == 96")
            code = replace(code, "parts = blocks(lo, hi, q0, q1) if grain is not None else [(lo, hi, q0, q1)]",
                           "parts = blocks(lo, hi, q0, q1) if grain is not None and (surface['host'].startswith('eoere_cleat_') or identity not in DEDICATED) else [(lo, hi, q0, q1)]")
            code = replace(code, "bearing(q, grain, diameter)/cg[identity]",
                           "bearing(q, grain, diameter, surface['host'].startswith('eoere_cleat_'))/cg[identity]")
            code = replace(code, "assert np.linalg.norm(rf, np.inf) < 1e-5 and np.linalg.norm(rm, np.inf) < 1e-3",
                           "audit_closure(field['case_id'], identity, rf, rm)")
            code = code.replace("eoere_remaining96_frame_balanced_bearing_blocks/v1", "eoere_current96_balanced_bearing_blocks/v1")
            code = code.replace("The ten completed cleat/header shafts retain their frozen evaluation.",
                                "All twelve dedicated shafts use their own current actions, conservative n<=2 Cg and current geometry adjustments; sawn/steel pressures remain affine and plywood alone uses balanced blocks.")
        if path.name == "frame_bolt_geometry.py":
            code = replace(code, " rows={r['axis_id']:r for r in calculation['shafts']};surfaces=[];receivers={};groups={}",
                           " rows={r['axis_id']:r for r in calculation['shafts']};surfaces=[];receivers={};groups={}\n assert set(rows)==set(shafts) and len(rows)==96")
            code = replace(code, "'all12_cases_checked':len(cases)==12", "'all6_cases_checked':len(cases)==6")
            code = code.replace("Dedicated ten cleat/header shafts,", "All twelve dedicated cleat/header shafts are included; remaining")
        if path.name == "up15_timber_cores.py":
            code = replace(code, "Current cached24 sawn solids only; four plywood leaves have their dedicated section evaluation.",
                           "Current cached20 sawn solids only; the two analytical plywood pairs have their dedicated row evaluation.")
        return code

    original.intake = intake
    original.basis = sys.modules[__name__]
    original.OUT = OUT
    # Its dispatcher provides fixed source names; the injected globals contain
    # only the current extra inventory and closure methods the worksheets need.
    mapping = {"geometry": "up15_timber_cores.py", "sections": "up15_timber_sections.py",
               "local": "shaft_local_review.py", "group": "shaft_group_factor.py",
               "bearing": "shaft_bearing_blocks.py", "boltgeometry": "resolved_frame_bolt_geometry.py"}
    names = {"geometry": "timber-net-geometry-v1.json", "sections": "timber-sections-v1.json",
             "local": "shaft-local-review-v1.json", "group": "shaft-group-factor-v1.json",
             "bearing": "shaft-bearing-blocks-v1.json", "boltgeometry": "shaft-geometry-adjustments-v3.json"}
    source, output = analysis.WORK / mapping[kind], OUT / names[kind]
    assert not output.exists()
    load()
    sys.argv = [str(source), "owner_frame_basis", str(OUT)] if kind == "boltgeometry" else [str(source), str(output)]
    namespace = {"__file__": str(source), "__name__": "__main__", "OUT": OUT, "REVIEW_OUT": OUT,
                 "DEDICATED": DEDICATED, "GEOMETRY": GEOMETRY, "audit_closure": closure.audit_closure}
    with patch.object(Path, "read_text", intake):
        exec(compile(intake(source), str(source), "exec"), namespace)  # noqa: S102 -- frozen worksheet with bounded source adapters
    result = json.loads(output.read_bytes())
    if "source_sha256" in result:
        result["source_sha256"].update({ref(p)["path"]: sha(p) for p in (OWN, original.OWN, Path(closure.__file__))})
    result.update(current_case_count=6, current_bolt_count=96, current_dedicated_bolt_count=12,
                  duration_factor_CD=1., old_force_pass_transferred=False, structural_acceptance=False)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    receipt = {"producer": ref(OWN), "parent_adapter": ref(original.OWN), "geometry": ref(GEOMETRY),
               "kind": kind, "source_reads": original.captured, "result": ref(output),
               "shaft_terminal_force_allowance_N": 1e-4, "shaft_terminal_moment_allowance_Nmm": 1e-3,
               "shaft_closure_records": closure.CHECKS, "duration_factor_CD": 1., "release": False}
    (OUT / (kind + ".current96-intake.json")).open("x").write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def plywood(thickness):
    assert thickness in (36.5, 38.1)
    REVIEW.mkdir(parents=True, exist_ok=True)
    code = inspect.getsource(rows.evaluate)
    replacements = {
        "shear = 110 * lbf / inch": f"shear = 2 * 110 * lbf / inch * ({thickness}/38.1)",
        "tension = {1: 2550 * lbf / 304.8 * .5, 2: 4350 * lbf / 304.8 * .5}": f"tension = {{1: 2*2550*lbf/304.8*.5*({thickness}/38.1), 2: 2*4350*lbf/304.8*.5*({thickness}/38.1)}}",
        "t, center = hi - lo, (hi + lo) / 2": f"center=(hi+lo)/2\n                t={thickness}\n                lo,hi=center-t/2,center+t/2",
        "assert len(own) == 3": "assert len(own) == 4",
        "for count in (1, 2, 3)": "for count in range(1, len(own)+1)",
        "assert len(groups) == 28": "assert len(groups) == 30",
        'len(ply["raw_operator_checks"]) == 4': 'len(ply["raw_operator_checks"]) == 2',
    }
    for before, after in replacements.items():
        code = replace(code, before, after)
    output = REVIEW / ("nominal38p1-rows-v1.json" if thickness == 38.1 else "bonded-rows-v1.json")
    assert not output.exists()
    folders = [(ROOT / binding["path"]).parent for _, _, binding, _ in load()[1]]
    old_glob = Path.glob

    def own_glob(path, pattern):
        if path == RUN / "nominal" and pattern == "three-pin-shift-corner-floor-*-v1":
            return iter(folders)
        return old_glob(path, pattern)

    namespace = {**vars(rows), "__file__": str(OWN), "GEOMETRY": GEOMETRY, "RUN": RUN, "OUTPUT": output}
    exec(compile(code, str(OWN), "exec"), namespace)  # noqa: S102 -- existing actual-perimeter row math, current four-bore groups
    with patch.object(Path, "glob", own_glob):
        namespace["evaluate"]()
    data = json.loads(output.read_bytes())
    data.update(credited_combined_wall_mm=thickness, nominal_combined_wall_mm=38.1, duration_factor_CD=1.,
                nominal38p1_perfect_bond_response_recomputed=True,
                credited_wall_response_recomputed=thickness == 38.1, bores_per_host=4, subsets_per_case=30,
                APA_basis="Two aligned24ocPS1 >=5ply/Group1 layers; sum of two110lbf/in shear and4350/2550lbf/ft tension products; narrow-width multiplier0.5; fixed-action wall allowance " + str(thickness) + "/38.1. Actual stamp/bond unobserved.",
                floor_support_scenario="Four-host centroidXY assumption;32 compression-only normals; other feet normal-only; no physical floor qualification.",
                limits=["Own six current fields use a full139.7mm-width bonded beam approximation to the actual trapezoid; no physical demand bound.",
                        "Balanced signed force/first-moment and actual-perimeter row construction; no complete plate, bond or joint qualification.",
                        "The36.5mm wall is a fixed-action strength allowance on nominal38.1mm response, not an actual-thickness stiffness bound."])
    data["source_sha256"].update({ref(p)["path"]: sha(p) for p in (OWN, Path(rows.__file__))})
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print("PLYWOOD", thickness, data["maximum_balanced_pressure_reference_index"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("preflight", "local", "group", "bearing", "boltgeometry", "geometry", "sections", "rows"))
    parser.add_argument("thickness", nargs="?", type=float)
    args = parser.parse_args()
    if args.kind == "rows":
        plywood(args.thickness)
    else:
        worksheet(args.kind)
