"""Current v8 conventional reference worksheets, with strict candidate intake.

Reuse the issued v6 formula adapters and frozen methods. Change only the
candidate paths/intake and the audited full side-rail core breadth. A separate
vector-bound worksheet refines peak addition within the same rectangular
construction; the original scalar worksheet remains recorded. Complete bolt
geometry factors belong to the independent current checker and remain null
where applicability is unresolved.
"""

from __future__ import annotations

import argparse
import fcntl
import inspect
import json
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from scripts import eoere_v6_checks as issued
from scripts import eoere_v6_report as reducer
from scripts import eoere_v8_analysis as analysis
from scripts import timber_vector_shear_bound as vector
from scripts.eoere_paired_frame_basis import ROOT, ref, sha
from scripts.eoere_v8_bracing_review import Intake, require

OWN = Path(__file__).resolve()
ISSUED = Path(issued.__file__).resolve()
ISSUED_SHA = "c7d0eeaa15be9a8eac450fdcb6c1d594169fc188c5e808c9738837cafe0e2a6f"
FROZEN_WORKSHEETS = {
    "up15_timber_cores.py": "8d45fa0ebba249bf2f36b8addc0bcb0f30f07e877c5e7f149ef51c8376f58a7f",
    "up15_timber_sections.py": "7f9ca56675fbc129b3d179c06aec74a1696164d5fda1e5142f1ea8aa25441b65",
    "shaft_local_review.py": "a487395dd3419c859b846a8dfe1458177eb044963e2ca64c98d358ea910cc9af",
    "shaft_group_factor.py": "59620e87941521d7945ffa25655a17d82b19763f5e2bf99ca50a1ce44418d34a",
    "shaft_bearing_blocks.py": "4a7165af639ac1cf0c8035510a0069b54b946a4b6868b6b3d34b02e4e7a5e612",
    "owner_frame_reviews.py": "73f00a99b10935cc6d60c2e15ad6cbc7eb11a2a043525fee9ea7d8115ddf35ab",
    "owner_roundoff_closure.py": "791ae31ca24e4d8fa56a24cdc632d8d924807cf7622b711da715d0a1383fa382",
}
GEOMETRY = analysis.BASE / "geometry/geometry.json"
RUN = analysis.BASE / "four-hosts"
REVIEW = analysis.BASE / "reference-review-v1"
OUT = REVIEW / "complete-v1"
VECTOR_OUT = REVIEW / "vector-bound-v1"
KINDS = ("preflight", "local", "group", "bearing", "geometry", "sections", "vector", "rows", "report")


def write_new(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def head_to_nut_coordinates(geometry, field):
    """Verify the thread transition is measured in the installation direction."""
    axes = {axis["id"]: axis for axis in geometry["axes"]}
    selections = {row["axis_id"]: row for row in issued.selections(geometry)}
    result = []
    for shaft in field["source_inputs"]["shafts"]:
        identity = shaft["axis_id"]
        axis = axes[identity]
        direction = np.asarray(shaft["basis"][0], dtype=float)
        physical_direction = np.asarray(axis["direction_xyz"], dtype=float)
        physical_direction /= np.linalg.norm(physical_direction)
        require(np.allclose(direction, physical_direction, rtol=0, atol=1e-8),
                "shaft strength coordinates must follow the current installation direction")
        require(np.allclose(shaft["point"], axis["point_xyz_mm"], rtol=0, atol=1e-7),
                "current shaft/physical origin differs")
        ends = {end["end"]: end for end in shaft["ends"]}
        head, nut = ends["head"], ends["nut"]
        require(head["pressure_face_s_mm"] < nut["pressure_face_s_mm"],
                "shaft coordinates must increase from head toward nut")
        require(np.isclose(direction @ head["direction_on_shaft_xyz"], -1., atol=1e-8)
                and np.isclose(direction @ nut["direction_on_shaft_xyz"], 1., atol=1e-8),
                "head/nut force directions differ from installation")
        length = selections[identity]["minimum_body_mm"]
        transition = head["pressure_face_s_mm"] + length
        require(shaft["shaft_interval_mm"][0] <= transition <= shaft["shaft_interval_mm"][1],
                "conditional minimum body transition must lie on the current shaft")
        windows = []
        for surface in shaft["surfaces"]:
            lo, hi = surface["interval_mm"]
            require(hi > lo, "current receiver interval must increase head to nut")
            windows.append({"host": surface["host"], "kind": surface["kind"], "interval_mm": [lo, hi],
                            "length_beyond_minimum_body_mm": max(0., hi - max(lo, transition))})
        result.append({"axis": identity, "direction_xyz": direction.tolist(),
                       "reversed_exterior_stack": axis.get("head_faces") == "exterior",
                       "head_pressure_face_s_mm": head["pressure_face_s_mm"],
                       "nut_pressure_face_s_mm": nut["pressure_face_s_mm"],
                       "conditional_minimum_body_mm": length,
                       "body_to_thread_transition_s_mm": transition, "surfaces": windows})
    require(len(result) == len({row["axis"] for row in result}) == len(axes) == 96,
            "all 96 current installation windows required")
    require(sum(row["reversed_exterior_stack"] for row in result) == 40,
            "all 40 reversed stacks must be represented")
    return result


def source_hook(original_intake, path, *args, vector_bound=False, **kwargs):
    code = original_intake(path, *args, **kwargs)
    if path.name == "up15_timber_cores.py":
        code = issued.replace(code, "elif name.startswith(('base_side_','base_post_outer_')):",
                              "elif name.startswith('base_post_outer_'):")
    if vector_bound and path.name == "up15_timber_sections.py":
        code = issued.replace(code, "BASE=OUT", f"BASE=Path({str(OUT)!r})")
        code = issued.replace(
            code, "s=max(rr['same_state_shear_bound_over_Fv'] for rr in comparison['regions'])",
            "s=__import__('scripts.timber_vector_shear_bound',fromlist=['section_upper']).section_upper(comparison,prop['refs']['Fv_parallel'])")
        code = issued.replace(code, "for p,d in pins.items():assert sha(p)==d,p",
                              f"pins[{ref(Path(vector.__file__))[ 'path']!r}]={sha(Path(vector.__file__))!r}\nfor p,d in pins.items():assert sha(p)==d,p")
    return code


def execute(kind, bindings):
    require(sha(ISSUED) == ISSUED_SHA, "preserve issued conventional worksheet adapter")
    for name, digest in FROZEN_WORKSHEETS.items():
        require(sha(analysis.WORK / name) == digest, "preserve issued worksheet: " + name)
    intake = Intake(bindings)
    geometry, fields, pins = intake.load()
    pins[ref(OWN)["path"]] = sha(OWN)
    pins.update({ref(analysis.WORK / name)["path"]: digest for name, digest in FROZEN_WORKSHEETS.items()})
    windows = head_to_nut_coordinates(geometry, fields[0][3])
    REVIEW.mkdir(parents=True, exist_ok=True)
    for source in (OWN, Path(vector.__file__)):
        snapshot = REVIEW / (source.stem + ".snapshot.py")
        if snapshot.exists():
            require(sha(snapshot) == sha(source), "preserve the source used by this worksheet packet")
        else:
            snapshot.write_bytes(source.read_bytes())

    def load():
        return geometry, fields, dict(pins)

    scenario = SimpleNamespace(OWN=analysis.OWN, WORK=analysis.WORK, BASE=analysis.BASE,
                               GEOMETRY=GEOMETRY, RUN=RUN, MATERIAL=analysis.BASE / "material.json",
                               INPUTS=RUN / "preparation/inputs.json", REVISION=analysis.REVISION)
    output = VECTOR_OUT if kind == "vector" else OUT
    with ExitStack() as stack:
        for name, value in {"OWN": OWN, "analysis": scenario, "GEOMETRY": GEOMETRY, "RUN": RUN,
                            "REVIEW": REVIEW, "OUT": output, "load": load, "load_available": load}.items():
            stack.enter_context(patch.object(issued, name, value))
        original, _ = issued.methods()
        old_intake, old_basis, old_out = original.intake, original.basis, original.OUT

        def hook(path, *args, **kwargs):
            return source_hook(old_intake, path, *args, vector_bound=kind == "vector", **kwargs)

        stack.enter_context(patch.object(original, "intake", hook))
        stack.enter_context(patch.object(original, "basis", old_basis))
        stack.enter_context(patch.object(original, "OUT", old_out))
        source = inspect.getsource(issued.preflight)
        source = issued.replace(source, "owner-principal-pairs-v6/analysis-v1/material.json",
                                "owner-inward-angles-v8/analysis-v1/material.json")
        namespace = dict(vars(issued))
        exec(compile(source, str(OWN), "exec"), namespace)  # noqa: S102 -- bounded issued adapter path routing
        stack.enter_context(patch.object(issued, "preflight", namespace["preflight"]))
        if kind == "rows":
            issued.plywood(38.1)
            issued.plywood(36.5)
        else:
            issued.worksheet("sections" if kind == "vector" else kind)
    receipt = {"schema": "eoere_v8_conventional_reference_intake/v1", "producer": ref(OWN),
               "issued_formula_adapter": {"path": ref(ISSUED)["path"], "sha256": ISSUED_SHA},
               "geometry_revision": analysis.PHYSICAL_REVISION, **bindings, **intake.captured,
               "worksheet": kind, "side_rail_core_uses_full_contained_breadth": True,
               "own_head_to_nut_thread_windows_checked": True,
               "legacy_Cdelta_geometry_screen_run": False, "complete_joint_Cdelta_established": False,
               "vector_bound_is_conditional_rectangular_model_only": kind == "vector",
               "physical_resistance_or_screw_law_qualified": False,
               "loads_reference_resistances_or_duration_factor_changed": False,
               "new_frame_or_native_response_solve": False, "structural_acceptance": False, "release": False}
    destination = REVIEW if kind == "rows" else output
    write_new(destination / (kind + ".v8-intake.json"), receipt)
    if not (REVIEW / "head-to-nut-windows.json").exists():
        write_new(REVIEW / "head-to-nut-windows.json",
                  {"geometry": ref(GEOMETRY), "producer": ref(OWN), "shafts": windows,
                   "basis": "conditional purchased minimum body, measured along each own shaft from head to nut",
                   "delivered_shank_thread_window_or_seat_qualified": False})
    print(ref(destination / (kind + ".v8-intake.json")), flush=True)


def report(bindings, public):
    """Reduce only current own worksheets; do not supply missing Cdelta."""
    intake = Intake(bindings)
    geometry, fields, pins = intake.load()
    fields_by_case = {case: binding for _, case, binding, _ in fields}
    paths = {"shaft_Cg_only": OUT / "shaft-bearing-blocks-v1.json",
             "timber_scalar": OUT / "timber-sections-v1.json",
             "timber_vector": VECTOR_OUT / "timber-sections-v1.json",
             "cleat_nominal": REVIEW / "nominal38p1-rows-v1.json",
             "cleat_wall_allowance": REVIEW / "bonded-rows-v1.json"}
    data = {}
    for name, path in paths.items():
        data[name] = json.loads(path.read_bytes())
        for source, digest in data[name]["source_sha256"].items():
            require(sha(source) == digest, "worksheet source changed: " + source)
            pins[source] = digest
        require(len(data[name]["cases"]) == 6
                and {case["case_id"] for case in data[name]["cases"]} == set(fields_by_case),
                "all six current worksheet cases required")
        for case in data[name]["cases"]:
            require(case["field"] == fields_by_case[case["case_id"]], "worksheet field join differs")
    expected_axes = {axis["id"] for axis in geometry["axes"]}
    for case in data["shaft_Cg_only"]["cases"]:
        require(len(case["shafts"]) == 96 and {row["axis_id"] for row in case["shafts"]} == expected_axes,
                "each shaft worksheet must cover the exact current inventory")
    shaft_metrics = ("maximum_bearing_index_before_Cdelta", "maximum_N_M_index_before_Cdelta",
                     "maximum_N_M_V_index_before_Cdelta")
    shaft_rows = [{"case_id": case["case_id"], "axis": row["axis_id"], "metric": metric,
                   "index": row[metric], "Cg": row["bounded_Cg"], "complete_joint_Cdelta": None}
                  for case in data["shaft_Cg_only"]["cases"] for row in case["shafts"]
                  for metric in shaft_metrics]
    require(len(shaft_rows) == 6 * 96 * 3 and all(np.isfinite(row["index"]) for row in shaft_rows),
            "all current finite shaft comparisons required")
    shaft_maxima = {metric: max((row for row in shaft_rows if row["metric"] == metric),
                                key=lambda row: row["index"]) for metric in shaft_metrics}
    summaries, exceedances = {}, {"shaft_Cg_only": [row for row in shaft_rows if row["index"] > 1.]}
    with patch.object(reducer, "RUN", RUN):
        for name in ("timber_scalar", "timber_vector"):
            summaries[name], exceedances[name] = reducer.summarize_timber(data[name])
    members = {name: {metric: max(
        ({"case_id": case["case_id"], "index": row[metric],
          "worst_interval": row["worst_intervals"][metric.removeprefix("maximum_")]}
         for case in data["timber_vector"]["cases"] for row in case["members"] if row["member"] == name),
        key=lambda row: row["index"]) for metric in reducer.TIMBER_METRICS}
        for name in sorted({row["member"] for row in data["timber_vector"]["cases"][0]["members"]})}
    # A weaker-bound refinement must leave normal/stability and the interval
    # census untouched. No event, hole region or member may disappear.
    for old_case, new_case in zip(data["timber_scalar"]["cases"], data["timber_vector"]["cases"], strict=True):
        require(old_case["case_id"] == new_case["case_id"], "section case ordering differs")
        for old, new in zip(old_case["members"], new_case["members"], strict=True):
            require(old["member"] == new["member"] and old["interval_count"] == new["interval_count"],
                    "vector bound cannot remove an interval/member")
            for a, b in zip(old["intervals"], new["intervals"], strict=True):
                for key in ("world_grain_interval_mm", "net_core_interval_local_L_mm", "normal_reference_upper",
                            "declared_restraint_normal_reference_upper"):
                    require(a[key] == b[key], "unrelated section result changed: " + key)
                require(b["shear_torsion_reference_upper"] <= a["shear_torsion_reference_upper"] + 1e-7,
                        "refined bound exceeds scalar beyond its explicit series-tail allowance")
    cleats = {}
    expected_groups = reducer.expected_cleat_groups(geometry)
    for name in ("cleat_nominal", "cleat_wall_allowance"):
        for case in data[name]["cases"]:
            for host, expected in expected_groups.items():
                own = [frozenset(row["axes"]) for row in case["groups"] if row["leaf"] == host]
                require(len(own) == len(expected) == 15 and set(own) == expected,
                        "every current four-bore subset must appear once")
        records = [{"case_id": case["case_id"], "host": row["leaf"], "axes": row["axes"],
                    "index": row["balanced_pressure_reference_index"]}
                   for case in data[name]["cases"] for row in case["groups"]]
        require(len(records) == 6 * 30, "all current four-bore subsets required")
        cleats[name] = max(records, key=lambda row: row["index"])
        exceedances[name] = [row for row in records if row["index"] > 1.]
    core = json.loads((OUT / "timber-net-geometry-v1.json").read_bytes())
    require(core["all_nominal_core_prisms_contained"] and core["member_count"] == len(members) == 20,
            "all twenty current contained timber cores required")
    for side in ("base_side_left", "base_side_right"):
        row = next(row for row in core["rows"] if row["member"] == side)
        lo, hi = row["minimum_full_depth_core_bounds_LUV_mm"][1]
        require(np.isclose(hi - lo, 88.898, rtol=0, atol=1e-7), "full contained side breadth required")
    result = {"schema": "eoere_v8_conventional_reference_review/v1", "producer": ref(OWN),
              "geometry_revision": analysis.PHYSICAL_REVISION, "physical_geometry": bindings["receipt"],
              "physical_source_geometry": bindings["physical_geometry"],
              "analysis_geometry": ref(GEOMETRY), "prepared_readiness": intake.captured["prepared_readiness"],
              "case_ids": list(fields_by_case), "fields": list(fields_by_case.values()),
              "load_contract": {"weight_lb": 250, "downward_multiplier": 2., "horizontal_force_N": 300.,
                                "accessory_mass_kg": 25., "duration_factor_CD": 1., "self_weight": True},
              "source_bindings": {name: ref(path) for name, path in paths.items()} | {
                  "timber_cores": ref(OUT / "timber-net-geometry-v1.json"),
                  "thread_windows": ref(REVIEW / "head-to-nut-windows.json"),
                  "vector_method": ref(Path(vector.__file__))},
              "shaft_Cg_only_maxima": shaft_maxima, "timber_maxima": summaries,
              "vector_timber_member_maxima": members, "cleat_maxima": cleats,
              "reference_exceedances": exceedances,
              "interval_count": sum(row["interval_count"] for case in data["timber_vector"]["cases"]
                                    for row in case["members"]),
              "physical_geometry_loads_screws_resistances_unchanged_by_review": True,
              "complete_joint_Cdelta_established": False, "physical_failure_inferred": False,
              "limitations": [
                  "Every force field already includes six panels, 66 unqualified Hillman springs and contact sharing. Stiffness ratios cannot be applied again as strength multipliers.",
                  "Shaft references include conditional purchased body/thread intervals and Cg, but no complete applicable end/edge/spacing factor. Below-one raw indices do not clear a joint.",
                  "The vector upper bound preserves all rectangular-ligament wrenches, hole deductions, point-event limits and cubic Bernstein controls. The original scalar result is retained.",
                  "Both section constructions remain prismatic common-strain/common-twist engineering models near short loaded holes. Neither establishes three-dimensional splitting, bond, washer-seat, fitting or joint strength.",
                  "The bonded 139.7 mm uniform cleat operator, nominal metal gravity and four-host no-slip floor retain their recorded unqualified applicability. Actual wood, hardware, adhesive, fits and floor remain unobserved.",
                  "A later bolt/spacer revision must receive an explicit applicability check; this review is tied to the frozen v8 hardware and does not transfer its force or strength result."],
              "method_sources": [{"title": "USDA FPL Wood Handbook, chapter 9, transverse shear and rectangular torsion",
                                  "url": "https://research.fs.usda.gov/download/treesearch/62251.pdf",
                                  "scope": "Eqs 9-14 and 9-24/Fig9-15 support the prismatic reference components; not loaded-hole qualification."}],
              "structural_acceptance": False, "fabrication_released": False, "climbing_released": False}
    write_new(REVIEW / "reference-review.json", result)
    require(public.parent == ROOT / "docs/bolted-frame-development/owner-frame-v8", "own v8 public packet required")
    write_new(public, result)
    print(json.dumps({"review": ref(public), "shaft_maxima": shaft_maxima, "cleat_maxima": cleats,
                      "exceedance_counts": {name: len(rows) for name, rows in exceedances.items()}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=KINDS)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--physical-sha256", required=True)
    parser.add_argument("--public", type=Path,
                        default=ROOT / "docs/bolted-frame-development/owner-frame-v8/reference-review.json")
    args = parser.parse_args()
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        bindings = analysis.context(args.receipt_sha256, args.physical_sha256)
        if args.kind == "report":
            report(bindings, args.public.resolve())
        else:
            execute(args.kind, bindings)


if __name__ == "__main__":
    main()
