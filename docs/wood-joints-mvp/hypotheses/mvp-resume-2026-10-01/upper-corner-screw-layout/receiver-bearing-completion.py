"""Frozen N15 receiver bearing addendum; only the parent calls build(output).

Import is inert. prepare(output) authenticates and joins saved records with the
standard library. build(output) adds scalar mean bearing comparisons only.
No existing producer is imported and no frame, CAD or native operation runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
HYPOTHESES = HERE.parent.parent
LEAF = HERE / "rawlocal/kicker-path-completion/parent-attempt01"
RAW = HERE / "rawlocal/receiver-bearing-completion"
DOCUMENT = HERE / "receiver-bearing-applicability.md"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
MODEL = GRAVITY / "model.json"
ROWS = GRAVITY / "row-identities.json"
GEOMETRY = HERE.parent / "member-screen-attempt02/knee-bridge-gravity01/geometry.json"
CONTACTS = HYPOTHESES / "mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
MATERIAL = HYPOTHESES / "hardware-material-specification-2026-09-30/material-inputs.json"
NDS_CACHE = HYPOTHESES / "upper-block-strength-2026-10-01/source-cache"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
SCENARIOS = {"cd1": 1.0, "cd1_25": 1.25}
SPINES = {"knee_outer_left_spine", "knee_outer_right_spine"}
RIPPED = {"center_principal_cleat_left", "center_principal_cleat_right",
          "knee_outer_left_inner_frame_block", "knee_outer_right_inner_frame_block"}
OBLIQUE = {"base_principal_center_left", "base_principal_center_right",
           "base_side_left", "base_side_right"}
OBLIQUE_COSINE = 0.7660444429154699
REFERENCE_VALUES = {
    1.1: (10.238714580355017, 12.798393225443771),
    1.15: (10.704110697643879, 13.380138372054848),
    1.0: (9.307922345777287, 11.634902932221609),
}
PINS = {
    DOCUMENT: "7ef58395f7eb5c4e14146a27ea5bfad68e02bee5a8aa918f8fbf5ffc7dc0ca65",
    LEAF / "receipt.json": "c589a8227000b2afe9ac536cbb7b99e4000f7b6e8b1024066a7e8b43109da402",
    LEAF / "report.json": "ed568d974c649e052cdde4c604482c23e611900cea7314f26e9426192a1f03e8",
    LEAF / "contact-bearing.json": "e6d71fdd4355c001a6dcf8ce6a5288e4b68c6bdfe4975cae46be13c37b322dea",
    LEAF / "saved-member-reference-join.json": "35c303a0ae9cc88a1c6bf599ccb7da8f467ed6bfe40cf2651de5c3f420a371e1",
    MODEL: "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    HERE / "rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf":
        "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
    NDS_CACHE / "appendix-2024-awc-20260911.pdf":
        "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
    NDS_CACHE / "chapter2-2024-awc.pdf":
        "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
    NDS_CACHE / "source-bounds.json":
        "91c8c0c33cb7cc35dc31ba332778a80e1c5a972a6134e5e277a473a2adf719c9",
    MATERIAL.parent / "materials-source/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf":
        "1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b",
    ROOT / "fea/reinforced_timber_resistance.py":
        "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
}
FLAGS = {name: False for name in (
    "proposal_adopted", "authority_changed", "geometry_or_hardware_changed",
    "loads_or_stiffness_changed", "historical_acceptance_transferred",
    "native_or_CAD_or_frame_execution", "tests_or_review_run", "N14_resistance_rebuilt",
    "complete_joint_acceptance", "complete_load_path_resistance",
    "formal_criterion_acceptance", "physical_release", "fabrication_release",
    "actual_pressure_distribution_qualified",
)}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                          encoding="utf-8")


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source leaves repository: " + str(path))
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def source_map(pins):
    return {p.relative_to(ROOT).as_posix(): h for p, h in sorted(pins.items())}


def key(state):
    return (state["case_id"], state["receiver"], state["other_body"], state["face_identity"])


def sources():
    """Authenticate frozen leaves before reading any mechanical records."""
    pins = {p.resolve(): h for p, h in PINS.items()}
    bind(pins, Path(__file__), sha(__file__))
    authenticate(pins)
    receipt = read(LEAF / "receipt.json")
    require(receipt["status"] == "COMPLETE_SAVED_PATH_ASSESSMENT_WITH_EXPLICIT_RESISTANCE_LIMITS"
            and len(receipt["source_sha256"]) == 94 and len(receipt["output_sha256"]) == 13,
            "different N15 source/receipt census")
    require(receipt["sources_unchanged_before_and_after"] is True,
            "N15 source authentication was incomplete")
    for name, digest in receipt["source_sha256"].items():
        bind(pins, ROOT / name, digest)
    for name, digest in receipt["output_sha256"].items():
        path = (LEAF / name).resolve()
        require(path.parent == LEAF.resolve(), "N15 artifact leaves frozen leaf")
        bind(pins, path, digest)
    authenticate(pins)
    report = read(LEAF / "report.json")
    require(report["current_screw_axes"] == 66 and report["reviewed_authority_axes"] == 104
            and report["unadopted_proposal_axes"] == 108 and tuple(report["case_ids"]) == CASES,
            "force/model scope differs")
    require(all(report[name] is False for name in FLAGS if name in report),
            "N15 authority or acceptance flags differ")
    references = read(LEAF / "saved-member-reference-join.json")
    require(references["load_hypothesis"]["wood_strength_CD_scenarios"] == SCENARIOS
            and references["load_hypothesis"]["Emin_and_Fcperp_unchanged"] is True,
            "saved adjusted-reference duration basis differs")
    require(references["source_sha256"][MATERIAL.relative_to(ROOT).as_posix()] == pins[MATERIAL],
            "reference worksheet has another material source")
    return pins, report, references


def joined_states(references):
    """Stdlib saved identity joins; never calculate demand, angle or resistance."""
    bearing = read(LEAF / "contact-bearing.json")
    require(len(bearing) == len({key(s) for s in bearing}) == 1140,
            "bearing keys are incomplete or duplicated")
    require(Counter(s["method_applicability"] for s in bearing) == {
        "CONDITIONAL_PERPENDICULAR_MEAN": 813, "NO_ACTIVE_AREA": 219,
        "PARALLEL_OR_OBLIQUE_METHOD_NOT_SUPPLIED": 108}, "bearing applicability census differs")
    lookup = {key(s): s for s in bearing}
    geometry = read(GEOMETRY)["members"]
    contacts = read(CONTACTS)["contact_patches"]
    materials = {m["member_id"]: m for m in read(MATERIAL)["members"]}
    orientations = read(MODEL)["material_binding"]["orientation_overrides"]
    rows = read(ROWS)
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)),
            "canonical contact row inventory differs")
    member_refs = {m["member"]: m for m in references["members"]}
    states, interfaces = [], {}
    for saved in bearing:
        if saved["method_applicability"] != "PARALLEL_OR_OBLIQUE_METHOD_NOT_SUPPLIED":
            continue
        case, body, other, face = key(saved)
        require(case in CASES and saved["timber_perpendicular_mean_ratio"] is None
                and saved["ratio_exceeds_one"] is None, "target case/null differs")
        require(all(math.isfinite(saved[field]) and saved[field] > 0
                    for field in ("compression_n", "active_area_mm2")), "invalid saved active compression")
        c = saved["normal_grain_dot_abs"]
        require(c in (1.0, OBLIQUE_COSINE), "different saved grain/contact direction")
        patch = contacts[int(face)]
        require(set(patch["member_ids"]) == {body, other}, "different exact contact pair")
        side = patch["member_ids"].index(body)
        facet = f"{body}/facet{patch['source_face_indices'][side]:03d}"
        planes = [p for p in geometry[body]["profile_planes"] if p["id"] == facet]
        normal = patch["normal_on_first_xyz"] if side == 0 else patch["normal_on_second_xyz"]
        require(len(planes) == 1 and planes[0]["normal"] == normal,
                "receiver plane recipe and contact normal disagree: " + facet)
        raw = [rows[i] for i in saved["raw_rows"]]
        require(len(raw) == 4 and len(set(saved["raw_rows"])) == 4, "contact cell identity differs")
        require(all(r["family"] == "unilateral_springa"
                    and r["law"]["intended_law"] == "compression_only"
                    and [r["ownership"]["first_body"], r["ownership"]["second_body"]] == patch["member_ids"]
                    and r["ownership"]["role"] == "timber_or_panel_contact"
                    and r["ownership"]["direction_global_xyz"] == patch["normal_on_second_xyz"]
                    for r in raw), "saved signed row/face direction differs")
        counter = lookup[(case, other, body, face)]
        require(counter["raw_rows"] == saved["raw_rows"] and counter["normal_grain_dot_abs"] == 0.0,
                "counterface/canonical row binding differs")
        material = materials[body]
        cf_record = material["code_Table4A_CF"]
        study = body in RIPPED
        if study:
            require(cf_record is None and material["study_only_CF_for_arithmetic"] == 1.0
                    and material["source_grade_inheritance_from_ripped_4x6"] is False,
                    "ripped-block study basis differs")
            decision, cf = "S", 1.0
        else:
            require(cf_record is not None and material["material_scenario"] == "conditional_DF-L_No.2",
                    "missing supported conditional material binding")
            cf = cf_record["Fc_parallel"]
            decision = "P" if c == 1.0 else "O"
        require((decision != "O" or body in OBLIQUE) and (not study or c == 1.0),
                "different oblique/study identity")
        donor = "base_header" if body in SPINES else body
        ref = member_refs[donor]
        require(ref["material_strength_binding"]["CF"]["Fc_parallel"] == cf,
                "reference material size factor differs")
        values = {s: {"Fc_star_mpa": ref["references"][s]["Fc_star_mpa"],
                      "Fc_perp_mpa": ref["references"][s]["Fc_perp_mpa"]} for s in SCENARIOS}
        require(tuple(values[s]["Fc_star_mpa"] for s in SCENARIOS) == REFERENCE_VALUES[cf]
                and all(v["Fc_perp_mpa"] == 4.309223308230226 for v in values.values()),
                "adjusted Fc_star/Fc_perp reference differs")
        interface_id = f"{body}/{other}/contact_{face}"
        interface = {
            "receiver": body, "other_body": other, "face_identity": face,
            "raw_rows": saved["raw_rows"], "exact_saved_contact_patch": patch,
            "receiver_plane_recipe": planes[0], "receiver_geometric_grain_xyz": geometry[body]["geometry"]["axis"],
            "receiver_material_grain_xyz": material["source_proposed_longitudinal_grain_global_xyz"],
            "receiver_frozen_elastic_orientation": orientations[body],
            "other_geometric_grain_xyz": geometry[other]["geometry"]["axis"],
            "saved_row_ownership": [r["ownership"] for r in raw],
            "saved_normal_grain_dot_abs": c, "saved_counterface_normal_grain_dot_abs": 0.0,
            "material_record": material, "decision": decision,
            "reference_source_member": donor, "spine_same_stock_material_reference_join": body in SPINES,
            "saved_adjusted_references": values, "CD_already_applied_once": True,
            "CP_excluded_from_Fc_star": True, "Cb": 1.0,
            "plate_at_bearing_face_established": False, "end_to_end_grain_pair": False,
        }
        require(interface_id not in interfaces or interfaces[interface_id] == interface,
                "case-dependent geometry/reference identity")
        interfaces[interface_id] = interface
        states.append({"source_state_key": list(key(saved)), "raw_rows": saved["raw_rows"],
                       "interface_id": interface_id, "decision": decision,
                       "saved_compression_n": saved["compression_n"],
                       "saved_active_area_mm2": saved["active_area_mm2"],
                       "normal_grain_dot_abs": c, "original_N15_state": saved,
                       "original_counterface_state": counter})
    require(Counter(s["decision"] for s in states) == {"P": 79, "O": 14, "S": 15}
            and len(interfaces) == 30, "93 conditional/15 study state census differs")
    return states, interfaces


def scalar_comparison(state, reference, numerical):
    study, parallel = state["decision"] == "S", state["normal_grain_dot_abs"] == 1.0
    result = {"law": "NDS_3.10.1_parallel" if parallel else "NDS_3.10.3_Hankinson",
              "reference_scope": "HYPOTHETICAL_FINAL_SECTION_DF_L_NO2_CF1" if study else "CONDITIONAL_STANDARD_STOCK_DF_L_NO2",
              "saved_adjusted_reference": reference, "mean_stress_mpa": None,
              "bearing_reference_mpa": None, "supported_resistance_ratio": None,
              "supported_ratio_exceeds_one": None, "hypothetical_reference_ratio": None,
              "hypothetical_ratio_exceeds_one": None,
              "parallel_plate_trigger_ratio": None, "parallel_plate_trigger_exceeded": None,
              "parallel_plate_trigger_scope": ("HYPOTHETICAL_ONLY" if study else "CONDITIONAL_STANDARD_STOCK")
              if parallel else "NOT_PARALLEL_BEARING",
              "plate_disposition": "NOT_EVALUATED" if parallel else "NOT_PARALLEL_BEARING",
              "complete_connection_resistance": None}
    if not numerical:
        return result
    stress = state["saved_compression_n"] / state["saved_active_area_mm2"]
    fc, perpendicular = reference["Fc_star_mpa"], reference["Fc_perp_mpa"]
    c = state["normal_grain_dot_abs"]
    strength = fc if parallel else fc * perpendicular / (fc * (1 - c * c) + perpendicular * c * c)
    ratio = stress / strength
    require(all(math.isfinite(v) and v >= 0 for v in (stress, strength, ratio)) and strength > 0,
            "nonfinite scalar bearing comparison")
    result.update(mean_stress_mpa=stress, bearing_reference_mpa=strength)
    prefix = "hypothetical" if study else "supported"
    result[prefix + ("_reference_ratio" if study else "_resistance_ratio")] = ratio
    result[prefix + "_ratio_exceeds_one"] = ratio > 1
    if parallel:
        trigger = stress / (0.75 * fc)
        result.update(parallel_plate_trigger_ratio=trigger, parallel_plate_trigger_exceeded=trigger > 1)
        result["plate_disposition"] = (
            "HYPOTHETICAL_PLATE_TRIGGER_EXCEEDED" if trigger > 1 else "HYPOTHETICAL_BELOW_OR_AT_PLATE_TRIGGER"
        ) if study else (
            "PLATE_REQUIRED_NOT_ESTABLISHED" if trigger > 1 else "BELOW_OR_AT_PLATE_TRIGGER_IN_SAVED_MEAN"
        )
    return result


def extrema(states, numerical):
    if not numerical:
        return None
    output = {}
    for scenario in SCENARIOS:
        output[scenario] = {}
        for decision in ("P", "O", "S"):
            field = "hypothetical_reference_ratio" if decision == "S" else "supported_resistance_ratio"
            eligible = [s for s in states if s["decision"] == decision]
            witness = max(eligible, key=lambda s: s["scenarios"][scenario][field])
            output[scenario][decision] = {"source_state_key": witness["source_state_key"],
                "raw_rows": witness["raw_rows"], "interface_id": witness["interface_id"],
                "scenario_result": witness["scenarios"][scenario]}
    return output


def execute(output, numerical):
    output = Path(output).absolute()
    require(not RAW.is_symlink() and output.parent == RAW and not output.exists() and not output.is_symlink(),
            "use a fresh immediate child of rawlocal/receiver-bearing-completion")
    require(output.resolve().parent == RAW.resolve(), "output route leaves owned folder")
    pins, source_report, references = sources()
    states, interfaces = joined_states(references)
    for state in states:
        values = interfaces[state["interface_id"]]["saved_adjusted_references"]
        state["scenarios"] = {s: scalar_comparison(state, values[s], numerical) for s in SCENARIOS}
    authenticate(pins)
    status = "COMPLETE_SCALAR_BEARING_ADDENDUM_WITH_EXPLICIT_LIMITS" if numerical else "PREPARED_NOT_NUMERICALLY_RUN"
    report = {"schema": "receiver-bearing-completion/v1", "mode": "build" if numerical else "prepare",
        "status": status, **FLAGS, "numerical_arithmetic_run": numerical,
        "source_sha256": source_map(pins), "producer_sha256": pins[Path(__file__).resolve()],
        "N15_receipt_sha256": pins[LEAF / "receipt.json"], "case_ids": list(CASES),
        "reviewed_authority_axes": 104, "unadopted_proposal_axes": 108, "current_screw_axes": 66,
        "force_scope": source_report["force_scope"], "load_hypothesis": references["load_hypothesis"],
        "counts": {"target_states": 108, "conditional_parallel_states": 79, "conditional_oblique_states": 14,
                   "hypothetical_parallel_states": 15, "interfaces": 30, "duration_scenarios": 2},
        "interfaces": interfaces, "states": states, "same_state_extrema": extrema(states, numerical),
        "API": {"prepare": "prepare(output): stdlib authentication and saved joins; scalar results null",
                "build": "build(output): parent-only saved mean pressure/reference arithmetic",
                "output": "fresh immediate child of rawlocal/receiver-bearing-completion"},
        "limits": ["The 15 ripped-block states retain null supported resistance; their finite values are hypothetical only.",
            "The 0.75 Fc_star plate obligation remains distinct from the Fc_star strength ratio; no plate is established.",
            "C_D is already applied once in saved Fc_star; C_P is excluded and Fc_perp is unchanged with C_b=1.",
            "Each receiver side references its original canonical contact rows; no new load, recovery or double counting.",
            "Mean active-area comparisons do not establish physical peak pressure, local crushing/splitting or complete joints.",
            "N14, member/stability/shared-pose limits, edge probes, alternate cuts and release authority retain their source scopes."],
        "sources_unchanged_before_and_after": True}
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "receiver-bearing-addendum.json", report)
    artifacts = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    require(artifacts["producer.py.snapshot"] == report["producer_sha256"], "producer changed during publication")
    authenticate(pins)
    write(output / "receipt.json", {"schema": "receiver-bearing-completion-receipt/v1", "status": status,
        **FLAGS, "numerical_arithmetic_run": numerical, "source_sha256": source_map(pins),
        "producer_sha256": report["producer_sha256"], "output_sha256": artifacts,
        "sources_unchanged_before_and_after": True})
    authenticate(pins)
    for name, digest in artifacts.items():
        require(sha(output / name) == digest, "output changed after receipt: " + name)
    return {"status": status, "counts": report["counts"], "output": output.relative_to(ROOT).as_posix(),
            "producer_sha256": report["producer_sha256"], "receipt_sha256": sha(output / "receipt.json")}


def prepare(output):
    return execute(output, False)


def build(output):
    """Parent serializes and executes the scalar arithmetic in this entry point."""
    return execute(output, True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--build", action="store_true", help="parent-only scalar arithmetic; default is prepare")
    args = parser.parse_args()
    print(json.dumps(build(args.output) if args.build else prepare(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
