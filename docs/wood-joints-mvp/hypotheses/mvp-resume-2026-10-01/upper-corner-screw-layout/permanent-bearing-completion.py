"""One saved nominal permanent bearing comparison; parent alone calls build(output).

Import reads no source data and imports no numerical package. prepare() performs
source/header/identity work only. No solver, geometry generator or test runs.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/permanent-bearing-completion"
PERMANENT = HERE / "rawlocal/knee-bridge-permanent-resolve/attempt02"
CONTACT = HERE / "rawlocal/contact-bearing-completion/attempt02"
N15 = HERE / "rawlocal/kicker-path-completion/parent-attempt01"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
CONTACT_METHOD = HERE / "contact-bearing-completion.py"
RECEIVER_METHOD = HERE / "receiver-bearing-completion.py"
RESPONSE = PERMANENT / "response.npz"
OPERATORS = GRAVITY / "operators.npz"
INVENTORY = CONTACT / "geometry-inventory.json"
MATERIAL = PACKET.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
WRENCH = PACKET / "top_corner_actions.py"
BEARING = ROOT / "scripts/compact_thick_results.py"
RIPPED = frozenset(("center_principal_cleat_left", "center_principal_cleat_right",
                    "knee_outer_left_inner_frame_block", "knee_outer_right_inner_frame_block"))
PSI_MPA = 0.006894757293168361
FC_PERP = 4.309223308230226
LIMITS = [
    "One saved permanent-only nominal solution; rank296/nullity4 and no alternate-seating force envelope or strict stability acceptance.",
    "Represented active-face/cell and uniform-footprint means are not physical pressure peaks, local crushing/plasticity or actual floor-substrate capacities.",
    "Four ripped parallel receiver interfaces retain null supported resistance and separately labeled hypothetical values; delivered material/grade remains unobserved.",
    "Parallel bearing retains the 0.75 Fc_star plate trigger; no plate is inferred or qualified.",
    "Nine panel/panel faces and 214 cells remain excluded; plywood-side/local-panel and complete connection resistances remain separate.",
    "No changed-hole stiffness, four internal static-bolt compatibility, no-slip verification or physical/fabrication release is supplied.",
]
FLAGS = dict.fromkeys(("complete_joint_acceptance", "full_frame_acceptance", "strict_frame_stability",
    "proposal_adopted", "formal_criterion_acceptance", "physical_release", "fabrication_release",
    "actual_pressure_distribution_qualified", "geometry_or_hardware_changed", "loads_or_stiffness_changed",
    "historical_acceptance_transferred", "native_or_CAD_or_frame_execution", "tests_or_review_run"), False)
PINS = {
    CONTACT_METHOD: "4c1240a296f764d2565edf219e2a5aa1b0fae25958840f7cc64a610662bee1ee",
    RECEIVER_METHOD: "767da34553071c946b9f0ea88047bb1dedf83b7034cdb47e4945382cb50de8b4",
    PERMANENT / "comparison.json": "3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a",
    RESPONSE: "605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033",
    INVENTORY: "68b421d5d8b16579fbbd5214167830cc0376163e629fcec7a2f407efcf0d1db3",
    CONTACT / "receipt.json": "7e7fdf6195f1611dcf4b020e75cd6ec9c99b04a09e58bdb7631e9e7d51aae326",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    GRAVITY / "model.json": "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    GRAVITY / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    GRAVITY / "model-inputs.json": "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    OPERATORS: "7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f",
    N15 / "contact-bearing.json": "e6d71fdd4355c001a6dcf8ce6a5288e4b68c6bdfe4975cae46be13c37b322dea",
    N15 / "receipt.json": "c589a8227000b2afe9ac536cbb7b99e4000f7b6e8b1024066a7e8b43109da402",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    BEARING: "3f4f0ec5bfd1535c602c0c00c8017665fd336ca32f9cd6b38ccf9d5813853c1a",
    ROOT / "scripts/floor_flush_checks.py": "8d756c608bef10b8ce6f5141e58cbb0c08df56b0e422b6fd8baa262cec61e9cf",
    PACKET.parent / "mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json":
        "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    PACKET / "top-corner-contact-geometry.json": "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    HERE / "rawlocal/receiver-bearing-completion/attempt01/receiver-bearing-addendum.json":
        "33b908fffb3222f6f7c3ed47e7383627d0a03fe337ff6a26026758959ff90292",
}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def key(path):
    return str(Path(path).resolve().relative_to(ROOT))


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source differs: " + key(path))


def source_pins():
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    authenticate(pins)
    return pins


def write(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def pure(path, names, namespace):
    tree = ast.parse(Path(path).read_text(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(nodes) == len(names) and all(not n.decorator_list for n in nodes), "pure function census differs")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**namespace)


def contact_kernel():
    namespace = {"ast": ast, "math": math, "json": json, "sys": sys, "struct": struct, "ZipFile": ZipFile,
        "SimpleNamespace": SimpleNamespace, "require": require, "write": write, "PSI_MPA": PSI_MPA,
        "LAW_TOL_N": 1e-4, "GAP_TOL_MM": 1e-8, "WRENCH": WRENCH, "BEARING": BEARING,
        "OPERATORS": OPERATORS, "RESPONSE": RESPONSE, "CASES": ("permanent-only",), "LIMITS": LIMITS}
    pure(CONTACT_METHOD, ("functions", "bearing_expressions", "ratios", "headers"), namespace)
    tree = ast.parse(CONTACT_METHOD.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "assess_saved")
    old = ast.dump(ast.parse("len(face_records) == 648 and len(floor_records) == 48", mode="eval").body)
    new = ast.parse("len(face_records) == 108 and len(floor_records) == 8", mode="eval").body
    hits = []

    class Census(ast.NodeTransformer):
        def visit_Compare(self, node):
            return self.generic_visit(node)

        def visit_BoolOp(self, node):
            if ast.dump(node) == old:
                hits.append(1)
                return ast.copy_location(copy.deepcopy(new), node)
            return self.generic_visit(node)

    fn = Census().visit(fn)
    require(len(hits) == 1, "frozen one-state census expression differs")
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    exec(compile(module, str(CONTACT_METHOD), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**namespace)


def inputs(pins):
    """Source-only census, material and exact ownership joins; no array values."""
    kernel = contact_kernel()
    report, inventory, model, rows, assessment, material = map(read, (
        PERMANENT / "comparison.json", INVENTORY, GRAVITY / "model.json",
        GRAVITY / "row-identities.json", GRAVITY / "operator-assessment.json", MATERIAL))
    require(report["load_case"] == "permanent-only" and report["wood_strength_CD"] == 0.9
            and report["dead_load_factor"] == 1.1110134616260479 and report["equipment_multiplier_applied_once"]
            and report["selected_unfactored_gravity_column"] == 0
            and all(report[k] == 0 for k in ("live_gravity_scale", "live_horizontal_scale", "live_moment_scale")),
            "permanent load/material contract differs")
    require(report["output_sha256"]["response.npz"] == pins[RESPONSE], "permanent response binding differs")
    state = next(s for s in report["states"] if s["state"] == "permanent-only_gap")
    cert = state["fixed_force_clearance_certificate"]
    require(state["case_id"] == "permanent-only" and state["gap_scale"] == 1 and state["audit"]["force_bearing_rigid_rank"] == 296
            and cert["bounded"] and cert["nullity"] == 4 and not cert["frame_state_accepted"], "nominal bounded-state scope differs")
    receipt = read(CONTACT / "receipt.json")
    require(receipt["output_sha256"]["geometry-inventory.json"] == pins[INVENTORY]
            and receipt["producer_sha256"] == pins[CONTACT_METHOD], "geometry method binding differs")
    for p in (OPERATORS, GRAVITY / "model.json", GRAVITY / "model-inputs.json", GRAVITY / "row-identities.json"):
        require(report["source_sha256"][key(p)] == receipt["source_sha256"][key(p)] == pins[p], "shared physical source differs")
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "row order differs")
    groups, floors = inventory["contact_faces"], inventory["floor_footprints"]
    cells = [cell for g in [*groups, *floors] for cell in g["cells"]]
    wood = [g for g in groups if g["wood_bodies"]]
    excluded = [g for g in groups if not g["wood_bodies"]]
    require((len(wood), len(cells), len(floors), len(excluded)) == (108, 1170, 8, 9)
            and sum(len(g["cells"]) for g in wood) == 856 and sum(len(g["cells"]) for g in excluded) == 214
            and sum(len(g["cells"]) for g in floors) == 100
            and sum(g["base_header_interface"] for g in wood) == 16, "bearing census differs")
    retained = {r["row"]: i for i, r in enumerate(r for r in rows if r["ownership"]["second_body"] != "floor")}
    require(len(retained) == 1588 and len({c["row"] for c in cells}) == 1170, "contact row census differs")
    for cell in cells:
        row = rows[cell["row"]]
        own = row["ownership"]
        require(row["row_id"] == cell["row_id"] and own["first_body"] == cell["first"]
                and own["second_body"] == cell["second"] and own["point_mm"] == cell["point_mm"]
                and own["role"] == cell["role"] and row["law"]["stiffness_N_per_mm"] == cell["k_n_per_mm"],
                "exact saved cell/row ownership or law differs")
        if cell["role"] != "floor_normal":
            require(cell["q_index"] == retained[cell["row"]], "nonfloor motion join differs")
    headers = {"response": kernel.headers(RESPONSE), "operators": kernel.headers(OPERATORS)}
    for suffix, shape in (("raw_force_n", [1888]), ("lumped_q_mm", [1612]), ("rigid_coordinates", [300])):
        require(headers["response"]["permanent-only_gap_" + suffix]["shape"] == shape, "response shape differs")
    require(headers["operators"]["D"]["shape"] == [1888, 300], "D shape differs")
    templates = {}
    n15_receipt = read(N15 / "receipt.json")
    require(n15_receipt["output_sha256"]["contact-bearing.json"] == pins[N15 / "contact-bearing.json"], "direction metadata receipt differs")
    for saved in read(N15 / "contact-bearing.json"):
        # Deliberately consume no saved live force, area, utilization or pass.
        t = {k: saved[k] for k in ("receiver", "other_body", "face_identity", "raw_rows", "normal_grain_dot_abs")}
        identity = (t["receiver"], t["other_body"], tuple(sorted(t["raw_rows"])))
        require(identity not in templates or templates[identity] == t, "case-dependent direction/row identity")
        templates[identity] = t
    material_map = {m["member_id"]: m for m in material["members"]}
    refs = {r["member"]: r["references_cd0_9"] for r in report["members"]}
    receiver_keys = {(body, next(b for b in (g["first"], g["second"]) if b != body), tuple(sorted(c["row"] for c in g["cells"])))
                     for g in wood for body in g["wood_bodies"]}
    require(set(templates) == receiver_keys and len(templates) == 190, "full receiver-side census differs")
    decisions = Counter()
    for t in templates.values():
        body, c = t["receiver"], t["normal_grain_dot_abs"]
        require(body in refs and refs[body]["Fc_perp_mpa"] == FC_PERP, "permanent material reference unavailable")
        if c < 1e-7:
            decision = "perpendicular"
        else:
            require(c in (1.0, 0.7660444429154699), "unsupported grain angle")
            if body in RIPPED:
                require(material_map[body]["code_Table4A_CF"] is None
                        and material_map[body]["study_only_CF_for_arithmetic"] == 1
                        and not material_map[body]["source_grade_inheritance_from_ripped_4x6"], "ripped study binding differs")
                decision = "S"
            else:
                require(material_map[body]["code_Table4A_CF"] is not None, "unsupported stock reference")
                decision = "P" if c == 1 else "O"
        t["decision"] = decision
        decisions[decision] += 1
    require(decisions == {"perpendicular": 156, "P": 26, "O": 4, "S": 4}, "receiver material/direction census differs")
    authenticate(pins)
    return SimpleNamespace(kernel=kernel, comparison=report, model=model, assessment=assessment, state=state,
        geometry=SimpleNamespace(groups=groups, floors=floors, cells=cells), templates=templates, refs=refs,
        receiver_decisions=dict(decisions), headers=headers, pins=pins)


def prepare():
    data = inputs(source_pins())
    return {"status": "PREPARED_NO_NUMERICAL_BEARING_RUN", "source_sha256": {key(p): h for p, h in sorted(data.pins.items())},
                "expected_counts": {"wood_faces": 108, "wood_cells": 856, "receiver_sides": 190, "floor_footprints": 8,
                                 "floor_cells": 100, "base_header_faces": 16, "excluded_panel_faces": 9, "excluded_panel_cells": 214},
                "receiver_geometry_classes": data.receiver_decisions, "array_headers": data.headers}


def receivers(data, results):
    """Scalar application of existing means/laws to freshly recovered permanent areas."""
    scalar = pure(RECEIVER_METHOD, ("scalar_comparison",), {"math": math, "require": require}).scalar_comparison
    expression = data.kernel.bearing_expressions()
    output = []
    groups = {g["group_id"]: g for g in data.geometry.groups}
    for face in results["wood_faces"]:
        g = groups[face["group_id"]]
        raw_rows = tuple(sorted(c["row"] for c in g["cells"]))
        compression, area = face["signed_normal_resultant_n"], face["active_positive_force_area_mm2"]
        for body in g["wood_bodies"]:
            other = next(b for b in (g["first"], g["second"]) if b != body)
            t = data.templates[(body, other, raw_rows)]
            record = dict(t, case_id="permanent-only", gap_scale=1, group_id=g["group_id"],
                          compression_n=compression, active_area_mm2=area, saved_adjusted_reference=data.refs[body],
                          source_strength_CD=0.9, CD_applied_once=True, Cb=1, CP_excluded_from_Fc_star=True,
                          complete_connection_resistance=None, actual_pressure_distribution_qualified=False)
            if t["decision"] == "perpendicular":
                mean_ratio, _ = data.kernel.ratios(expression, [compression], area)
                record.update(law="EXISTING_PERPENDICULAR_MEAN", mean_stress_mpa=compression/area if area else 0,
                              bearing_reference_mpa=FC_PERP, supported_resistance_ratio=mean_ratio,
                              supported_ratio_exceeds_one=mean_ratio > 1, hypothetical_reference_ratio=None,
                              method_applicability="CONDITIONAL_PERPENDICULAR_MEAN" if area else "NO_ACTIVE_COMPRESSION")
            else:
                state = {"decision": t["decision"], "normal_grain_dot_abs": t["normal_grain_dot_abs"],
                             "saved_compression_n": compression, "saved_active_area_mm2": area}
                record.update(scalar(state, data.refs[body], area > 0))
                if not area:
                    require(compression == 0, "nonzero compression without positive area")
                    record.update(mean_stress_mpa=0, method_applicability="NO_ACTIVE_COMPRESSION")
                else:
                    record["method_applicability"] = "HYPOTHETICAL_RIPPED_REFERENCE" if t["decision"] == "S" else "CONDITIONAL_STOCK_MEAN"
            output.append(record)
    require(len(output) == 190 and sum(r["decision"] == "S" for r in output) == 4
            and all(r["supported_resistance_ratio"] is None for r in output if r["decision"] == "S"), "receiver/null census differs")
    return output


def receiver_summary(records):
    summary = {}
    for decision in ("perpendicular", "P", "O", "S"):
        selected = [r for r in records if r["decision"] == decision]
        field = "hypothetical_reference_ratio" if decision == "S" else "supported_resistance_ratio"
        finite = [r for r in selected if r[field] is not None]
        peak = max(finite, key=lambda r: r[field]) if finite else None
        summary[decision] = {"states": len(selected), "finite_comparisons": len(finite), "no_active_compression": sum(r["active_area_mm2"] == 0 for r in selected),
            "supported_nulls": sum(r["supported_resistance_ratio"] is None for r in selected),
            "exceeded": sum(r[field] > 1 for r in finite), "maximum_ratio": None if peak is None else peak[field],
            "witness": None if peak is None else {k: peak[k] for k in ("receiver", "other_body", "group_id", "raw_rows", "compression_n", "active_area_mm2")},
            "plate_trigger_exceeded": sum(r.get("parallel_plate_trigger_exceeded") is True for r in selected)}
    return summary


def build(output: Path):
    """Parent-only one-state saved-force arithmetic, no equation system solve."""
    output = Path(output)
    require(not output.is_symlink() and not RAW.is_symlink(), "symlink output refused")
    output = output.resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned RAW child required")
    pins = source_pins()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    report = dict(schema="permanent_bearing_completion/v1", status="STOP", limits=LIMITS, **FLAGS)
    error = None
    try:
        require(sha(output / "producer.py.snapshot") == pins[Path(__file__).resolve()], "producer snapshot differs")
        data = inputs(pins)
        write(output / "inputs.json", dict(source_state=data.state, wood_strength_CD=0.9,
              Fc_perp_unchanged_mpa=FC_PERP, receiver_geometry_classes=data.receiver_decisions, array_headers=data.headers,
              load_basis={k: data.comparison[k] for k in ("modeled_mass_kg", "equipment_mass_kg", "dead_load_factor", "selected_unfactored_gravity_column")},
              overrides=["permanent-only nominal case/response", "108/8 final contact census", "stored CD0.9 Fc_star without another multiplier"], **FLAGS))
        contact_result = data.kernel.assess_saved(output, data, data.geometry)
        results = read(output / "bearing-results.json")
        with (output / "cell-actions.jsonl").open() as stream:
            cell_count = sum(1 for _ in stream)
        require(len(results["wood_faces"]) == 108 and len(results["floor_footprints"]) == 8
                and cell_count == 956, "actual permanent face/floor/cell output census differs")
        receiver_records = receivers(data, results)
        write(output / "receiver-bearing.json", receiver_records)
        summary = receiver_summary(receiver_records)
        report.update(status="COMPLETED_PERMANENT_BEARING_COMPARISON_WITH_EXPLICIT_GAPS", contact=contact_result, receivers=summary,
            counts={"wood_faces": 108, "wood_cells": 856, "receiver_sides": 190, "floor_footprints": 8, "floor_cells": 100,
                        "base_header_faces": 16, "cell_records": 956, "excluded_panel_faces": 9, "excluded_panel_cells": 214, "ripped_supported_nulls": 4},
            source_state=data.state, load_case="permanent-only", gap_scale=1, Fc_perp_unchanged_mpa=FC_PERP, wood_strength_CD=0.9,
            supported_reference_exceedances=sum(v["exceeded"] for k,v in summary.items() if k != "S"),
            conditional_parallel_plate_triggers=summary["P"]["plate_trigger_exceeded"], numerical_arithmetic_run=True)
    except Exception as caught:  # noqa: BLE001 -- preserve failed attempt, never retry.
        error = caught
        report.update(status="STOP", terminal_exception=f"{type(caught).__name__}: {caught}")
    after = {}
    try:
        after = {key(p): sha(p) for p in sorted(pins)}
        authenticate(pins)
    except Exception as caught:  # noqa: BLE001 -- guard sources on successful and failed arithmetic.
        error = caught
        report.update(status="STOP", source_guard_exception=f"{type(caught).__name__}: {caught}")
    write(output / "sources.json", {key(p): h for p, h in sorted(pins.items())})
    write(output / "report.json", report)
    artifacts = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    write(output / "receipt.json", dict(schema="permanent_bearing_completion_receipt/v1", status=report["status"],
          producer_sha256=pins[Path(__file__).resolve()], source_sha256={key(p): h for p,h in sorted(pins.items())},
          source_sha256_after=after, output_sha256=artifacts,
          sources_authenticated_before=True,
          sources_authenticated_after=after == {key(p): h for p,h in pins.items()},
          sources_authenticated_before_and_after=after == {key(p): h for p,h in pins.items()}, **FLAGS))
    if error is not None:
        raise error
    return {"status": report["status"], "output": key(output), "producer_sha256": pins[Path(__file__).resolve()],
                "report_sha256": sha(output / "report.json"), "receipt_sha256": sha(output / "receipt.json"), "source_pin_count": len(pins),
                "counts": report["counts"], "supported_reference_exceedances": report["supported_reference_exceedances"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
