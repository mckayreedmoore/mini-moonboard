"""Consolidate frozen joint duties by metadata joins; perform no mechanics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/remaining-block-duties"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
FROZEN = {
    "assessment": (HERE / "operators-attempt02/operator-assessment.json", "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a"),
    "model": (HERE / "operators-attempt02/model.json", "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626"),
    "rows": (HERE / "operators-attempt02/row-identities.json", "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27"),
    "comparison": (HERE / "frame-250-attempt02/comparison.json", "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca"),
    "response": (HERE / "frame-250-attempt02/response.npz", "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7"),
    "register": (HERE / "rawlocal/joint-register/attempt01/register.json", "79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca"),
    "left": (HERE / "rawlocal/upper-left-block/attempt01/checks.json", "5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0"),
    "left_components": (HERE / "rawlocal/upper-left-block-components/attempt01/checks.json", "25f0bb27a752f68d28ededb97017b1675d47751f44922d95d021d1b91e096420"),
    "right": (HERE / "rawlocal/upper-right-block/attempt01/checks.json", "0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b"),
    "assembly": (PACKET / "assembly-package/rawlocal/reconciled-assembly.json", "2bb4e95fbd2a7ec158d24bc12860e0961000fdb9f9af7ffd8504ef966b2aee87"),
    "engagement": (PACKET / "assembly-package/rawlocal/hardware-engagement/hardware-engagement.json", "93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a"),
    "hardware_axes": (PACKET / "assembly-package/rawlocal/hardware-engagement/hardware-engagement-axes.csv", "9fd9f2f70dbaf347bf174925f21cc3d589c2640a7b42501e3b81f4533ab42cac"),
    "length_fit": (PACKET / "assembly-package/rawlocal/hardware-length-fit/saved-source-attempt02/result.json", "df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5"),
    "retained_support": (PACKET / "retained-washer-support-attempt02/support.json", "72ecad11051f7a72695f83561bb12503bfd79a44d3c3f6eeac2de476e3bc3448"),
    "remaining_support": (Path("/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json"), "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3"),
    "upper_support": (ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/seats.json", "4463f581490842095224afefd0b355428f82668f039b2e6035dfe4ec879c96c1"),
    "primary_support": (ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/seat-screen.json", "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0"),
    "primary_offset": (Path("/tmp/mini-moonboard-eccentric-parent-check-2026-10-01.json"), "0ae0af403cd99b323f0deb489e64bdf7cf94e0d32f0b84f0a9344efda2369354"),
    "access": (ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json", "bd2b97c0677b2e0ab5b09898ba7f2227758088744cd93f7e3c9b266bce5c5215"),
    "capture": (ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/captured-nut-motion-attempt02/motion.json", "83c905bec64010695c769a73d7b8923869ef1aef5bda9b8591cdad0d443b21a4"),
    "operations": (ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-closeout-attempt02/evidence-register.json", "dbfe1049d01f936bb034531699ff333d07916240c367851239fb665c1b4f17dc"),
}
METHOD_LABELS = {
    "remaining": "R", "remaining_washer": "WA", "top": "TC", "bottom": "BC",
    "end_grain": "E", "header": "H", "central_seat": "P", "service": "S",
    "knee": "K", "knee_bearing": "KB", "knee_fit": "KF",
}
REQUIREMENTS = {
    "W": {
        "kind": "recorded_missing_local_load_transfer_and_resistance",
        "requirement": "Use the named finished bore/passage intervals and current signed cuts to resolve local ligament transfer, opening concentrations and short-block shear/torque. Bore-free member references supply no result at those intervals.",
        "source": "member-screen-attempt02/four-screw-layout01/member-results.json#/open_checks_by_member",
    },
    "H": {
        "kind": "recorded_resistance_applicability_limit",
        "requirement": "Resolve header local splitting/torque interaction and oblique group applicability using the existing 72 states, 36 interfaces and 1,260 section states. The finite section/contact, Ceg and Cg scenarios are complete; F90 is characteristic, not adopted resistance.",
        "source": "upper-corner-screw-layout/header-replay.md#result-and-scope",
    },
    "K": {
        "kind": "recorded_missing_loaded_contact_compatibility",
        "requirement": "Join the two lateral planes, one physical tie and receiver bearing fields in a loaded common-shaft state for the four continuous bolts. Reuse the 24 fields, 96 static endpoint witnesses and 96 successful geometric placements; no placement replay is required.",
        "source": "upper-corner-screw-layout/knee-replay.md#preserved-law-and-limits",
    },
    "P": {
        "kind": "known_partial_seat_load_path",
        "requirement": "Resolve nut-to-washer-to-supported-wood transfer at center_principal_right_2 over the passage-side unsupported crescent. The 10 mm central ring is already supported; its current six-state pressure scenario is complete. Do not assign a full-annulus ratio to this seat.",
        "source": "upper-corner-screw-layout/bolted-replay-results/central-seat-attempt01/result.json",
    },
    "C": {
        "kind": "recorded_resistance_applicability_limit",
        "requirement": "Integrate local wood/group/splitting and washer transfer with simultaneous corner states. For the top corners use their own compatible local bolt allocations; original frame-allocation splitting cuts cannot silently qualify redistributed individual bolts. Elastic cleat deformation remains a model limit, not a new blanket solve requirement.",
        "source": "upper-corner-screw-layout/upper-right-block.md#meaning-and-remaining-scope",
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def location(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def encoded(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def build() -> tuple[dict, dict[Path, str]]:
    pins: dict[Path, str] = {}

    def pin(path: Path, expected: str | None = None) -> None:
        path = path.resolve()
        actual = digest(path)
        require(expected is None or actual == expected, f"Frozen source differs: {path}")
        require(path not in pins or pins[path] == actual, f"Source changed during join: {path}")
        pins[path] = actual

    def read(path: Path, expected: str | None = None) -> dict:
        pin(path, expected)
        return json.loads(path.read_text())

    for path, expected in FROZEN.values():
        pin(path, expected)
    pin(Path(__file__))
    sources = {
        key: json.loads(path.read_text())
        for key, (path, _) in FROZEN.items() if path.suffix == ".json"
    }
    register = sources["register"]
    require(register["case_ids"] == CASES, "Register case order differs")
    require(register["accounting"]["connector_block_bodies"] == 24, "Block count differs")
    require(register["same_state_force_source"]["response_sha256"] == FROZEN["response"][1], "Register force source differs")
    require(register["same_state_force_source"]["gap_scale"] == 1.0, "Force gap scale differs")
    require(not register["complete_joint_acceptance"] and not register["physical_release"], "Register authority differs")
    require(sources["comparison"]["response_sha256"] == FROZEN["response"][1], "Comparison binding differs")
    require([s["case_id"] for s in sources["comparison"]["states"] if s["gap_scale"] == 1.0] == CASES, "Comparison case order differs")

    methods = register["methods"]
    reports = {}
    for name, record in methods.items():
        report = read(PACKET / record["source"], record["sha256"])
        reports[name] = report
        for key in ("source_response_sha256", "response_sha256"):
            require(key not in report or report[key] == FROZEN["response"][1], f"Incompatible force source: {name}")
        # Only directly consumed saved artifacts are checked. Inherited source maps
        # remain provenance; this join never reruns an upstream producer.
    geometry_path = PACKET / "member-screen-attempt02/four-screw-layout01/geometry.json"
    geometry = read(geometry_path, reports["members"]["output_sha256"]["geometry.json"])
    hw = list(csv.DictReader(io.StringIO(FROZEN["hardware_axes"][0].read_text())))
    hardware = {row["axis_id"]: (index, row) for index, row in enumerate(hw)}
    axes = {row["axis_id"]: (index, row) for index, row in enumerate(register["axes"])}
    require(len(hw) == len(hardware) == len(axes) == 104, "Hardware axis census differs")
    require(set(hardware) == set(axes), "Hardware/register axis IDs differ")
    for axis_id, (_, axis) in axes.items():
        ordered = json.loads(hardware[axis_id][1]["ordered_members_head_to_nut"])
        require(set(ordered) == set(axis["receivers"]), f"Hardware receiver join differs: {axis_id}")
        require([s["case_id"] for s in axis["per_state"]] == CASES, f"Axis force census differs: {axis_id}")
    block_ids = {b["block_id"] for b in register["blocks"]}
    assembly_blocks = {b["body_id"] for b in sources["assembly"]["bodies"] if b["body_id"] in block_ids}
    require(len(block_ids) == 24 and assembly_blocks == block_ids, "Assembly block join differs")
    require(sources["length_fit"]["target_axes"] and not sources["length_fit"]["overlap_pairs"] and not sources["length_fit"]["undecided_pairs"], "Length-fit completion differs")
    require(len(sources["length_fit"]["target_axes"]) == 12, "Length-fit target census differs")
    require(reports["knee_fit"]["placement_found_count"] == reports["knee_fit"]["placement_count"] == 96, "Knee placements differ")
    for side in ("left", "right"):
        local = sources[side]
        require([s["case_id"] for s in local["states"]] == CASES, f"{side} local cases differ")
        require(not local["complete_joint_acceptance"] and not local["physical_release"], f"{side} local claims release")
        for path, expected in local["source_sha256"].items():
            if Path(path).name in {"comparison.json", "response.npz", "model.json", "row-identities.json"}:
                pin(ROOT / path, expected)
    require(sources["left"]["counts"]["completed_host_models"] == 12 and sources["left"]["failure"] is None, "Left local result incomplete")
    left_components = sources["left_components"]
    require(list(dict.fromkeys(s["case_id"] for s in left_components["states"])) == CASES, "Left component cases differ")
    require(len(left_components["states"]) == len({(s["case_id"], s["axis_id"]) for s in left_components["states"]}) == 24, "Left component state census differs")
    require(all({s["axis_id"] for s in left_components["states"] if s["case_id"] == case} == set(sources["left"]["axis_ids"]) for case in CASES), "Left component axis census differs")
    require(left_components["source_sha256"][location(FROZEN["left"][0])] == FROZEN["left"][1], "Left component source differs")
    require(not left_components["complete_joint_acceptance"] and not left_components["physical_release"], "Left components claim release")

    seats = []

    def seat_records(source: str, collection: str, records: list, member_key: str) -> None:
        for index, record in enumerate(records):
            seats.append({"axis_id": record["axis_id"], "member": record[member_key],
                          "source": source, "pointer": f"/{collection}/{index}"})

    seat_records(location(FROZEN["remaining_support"][0]), "seats", sources["remaining_support"]["seats"], "member")
    seat_records(location(FROZEN["upper_support"][0]), "geometry_seats", sources["upper_support"]["geometry_seats"], "owner_member_id")
    # Top and bottom replays supersede the old geometry at their corrected seats.
    for name, collection, member_key in (("top", "washer_seats", "body"), ("bottom", "washer_geometry", "member")):
        replaced = {r["axis_id"] for r in reports[name][collection]}
        seats = [s for s in seats if s["axis_id"] not in replaced]
        seat_records(location(PACKET / methods[name]["source"]), collection, reports[name][collection], member_key)
    primary_ids = {a["axis_id"] for a in sources["primary_support"]["axes"]}
    for index, axis in enumerate(sources["primary_support"]["axes"]):
        seats.append({"axis_id": axis["axis_id"], "member": None,
                      "source": location(FROZEN["primary_support"][0]), "pointer": f"/axes/{index}",
                      "offset_geometry_source": location(FROZEN["primary_offset"][0]),
                      "scope": "Completed six-axis/12-seat geometry and offset support; historical unit ties are not current demands."})

    members = {m["member"]: (index, m) for index, m in enumerate(reports["member_stability"]["members"])}
    operation_rows = sources["operations"]["axis_operation_status_register"]["rows"]
    operation_index = {r["axis_id"]: i for i, r in enumerate(operation_rows)}
    capture_index = {r["axis_id"]: i for i, r in enumerate(sources["capture"]["axis_operations"])}
    access_index = {r["axis_id"]: i for i, r in enumerate(sources["access"]["axis_operations"])}
    length_ids = {axis["axis_id"] for axis in sources["length_fit"]["target_axes"]}
    blocks = []
    for block_index, block in enumerate(register["blocks"]):
        block_id = block["block_id"]
        ids = block["candidate_axis_ids"]
        hosts = sorted({r for interface in block["receiver_interfaces"] for r in interface["receivers"] if r not in block_ids})
        member_records = []
        for member in [block_id, *hosts]:
            index, result = members[member]
            peak_fields = {"case_id", "member", "cut_array_index", "station_mm", "trace", "section_status", "N_n", "Vu_n", "Vv_n", "T_nmm", "Mu_nmm", "Mv_nmm", "timber_braced_normal_ratio", "shear_face_ratio"}
            member_records.append({
                "member": member, "source": methods["member_stability"]["source"],
                "pointer": f"/members/{index}",
                "normal_peak": None if result["timber_braced_normal_peak"] is None else {k: v for k, v in result["timber_braced_normal_peak"].items() if k in peak_fields},
                "shear_torsion_peak": None if result["shear_face_peak"] is None else {k: v for k, v in result["shear_face_peak"].items() if k in peak_fields},
                "section_status_trace_counts": result["section_status_trace_counts"],
                "finished_geometry_source": location(geometry_path),
                "finished_geometry_pointer": f"/members/{member}",
                "finished_step_sha256": geometry["members"][member]["current_finished_step_sha256"],
                "bore_or_passage_interval_count": len(geometry["members"][member]["bore_or_passage_intervals"]),
                "bore_or_passage_intervals_pointer": f"/members/{member}/bore_or_passage_intervals",
                "recorded_open_scope": reports["members"]["open_checks_by_member"][member],
            })
        applicable_seats = [s for s in seats if s["axis_id"] in ids]
        require({s["axis_id"] for s in applicable_seats} == set(ids), f"Seat evidence missing: {block_id}")
        codes = ["W"]
        if "header" in block["method_ids"]:
            codes.append("H")
        if block["shared_axis_ids"]:
            codes.append("K")
        if "central_seat" in block["method_ids"]:
            codes.append("P")
        if "top" in block["method_ids"] or "bottom" in block["method_ids"]:
            codes.append("C")
        top = block_id in {"top_outer_left_cleat", "top_outer_right_cleat"}
        block_axes = []
        for axis_id in ids:
            index, axis = axes[axis_id]
            hw_index, hw_record = hardware[axis_id]
            block_axes.append({
                "axis_id": axis_id, "force_and_component_pointer": f"/axes/{index}",
                "receiver_interfaces": axis["interfaces"], "outer_tie": axis["outer_tie"],
                "hardware_csv_data_row_zero_based": hw_index,
                "hardware_specification": {k: hw_record[k] for k in ["family_id", "diameter_mm", "model_underhead_length_mm", "proposed_nominal_order_length_mm", "wood_grip_mm", "required_LB_each_member_max_mm", "full_form_male_thread_required_interval_mm", "physical_three_pitch_length_min_mm"]},
                "operation_register_pointer": f"/axis_operation_status_register/rows/{operation_index[axis_id]}",
                "preserved_access_pointer": f"/axis_operations/{access_index[axis_id]}",
                "access_scope": "Historical original top hardware; use corrected top approaches and conditional sequence." if top else "Preserved exact source-envelope route; changed remote hardware/obstacles do not inherit a complete installed-operation pass.",
                "captured_nut_pointer": f"/axis_operations/{capture_index[axis_id]}" if axis_id in capture_index else None,
                "added_length_occupancy_complete": axis_id in length_ids,
                "common_shaft_placement_complete": axis_id in register["accounting"]["shared_physical_axes"],
            })
        local_key = "left" if block_id == "top_outer_left_cleat" else "right" if block_id == "top_outer_right_cleat" else None
        local = sources[local_key] if local_key else None
        blocks.append({
            "block_id": block_id, "hosts": hosts, "register_pointer": f"/blocks/{block_index}",
            "axes": block_axes, "shared_axis_ids": block["shared_axis_ids"],
            "source_force_peak": block["peak_lateral"], "source_tie_peak": block["peak_signed_outer_tie"],
            "completed_component_method_ids": block["method_ids"],
            "source_allocation_component_peaks": block["component_ratio_peaks"],
            "member_checks": member_records, "seat_geometry_records": applicable_seats,
            "seat_scope": "Supported central ring plus separately excluded full-annulus nut crescent." if "P" in codes else "Completed saved support geometry; offset/nominal scopes remain as recorded, not loaded pressure or washer strength.",
            "fit_operation_label": "T" if top else "A+CAP" if any(a["axis_id"] in capture_index for a in block_axes) else "A",
            "length_extension_axis_ids": [axis_id for axis_id in ids if axis_id in length_ids],
            "local_whole_block": None if local is None else {
                "source": location(FROZEN[local_key][0]), "sha256": FROZEN[local_key][1],
                "status": local["status"], "cases": CASES,
                "completed_scope": "6 cases, 12 host models, 4 bolts, 32 faces, one rigid cleat gauge",
                "component_replay": "complete finite same-state component replay",
                "component_source": location(FROZEN["left_components"][0]) if local_key == "left" else location(FROZEN["right"][0]),
                "component_sha256": FROZEN["left_components"][1] if local_key == "left" else FROZEN["right"][1],
                "peak_witnesses": left_components["peak_witnesses"] if local_key == "left" else local["peak_witnesses"],
                "limits": local["limits"],
            },
            "recorded_remaining_requirement_ids": codes,
            "conditional_hardware_and_operation_assumptions_are_new_failures": False,
            "new_adopted_block_criterion_failure_identified": False,
            "complete_joint_acceptance": False,
        })

    for filename in ["joint-register.md", "bolted-replay.md", "header-replay.md", "knee-replay.md", "member-replay.md", "upper-right-block.md", "upper-left-block.md", "upper-left-block-components.md"]:
        pin(HERE / filename)
    for filename in ["README.md", "hardware-length-fit.md", "hardware-engagement.md", "shop-guide.md"]:
        pin(PACKET / "assembly-package" / filename)
    for filename in ["current-access-screen.md", "current-retained-wire-sequence.md"]:
        pin(ROOT / "docs/wood-joints-mvp" / filename)
    retained = []
    for index, pair in enumerate(register["retained_frame_bolt_arrangements"]):
        retained.append({"register_pointer": f"/retained_frame_bolt_arrangements/{index}", "register_record": pair,
                         "completed_method_ids": ["remaining", "retained_group", "retained_washer"],
                         "seat_support_source": location(FROZEN["retained_support"][0]),
                         "support_scope": "All 24 concentric annuli and 72 geometry probes complete. Use fresh retained-washer forces; historical support-report pressures are not current demands.",
                         "residual_scope": "Oblique group applicability, local load transfer, washer/head/nut resistance and declared loaded tilt remain explicit limits. Delivered profiles and intact-wire staging are conditional operation assumptions."})
    result = {
        "schema": "current_remaining_block_duty_consolidation/v1",
        "scope": "Existing engineering duty consolidation by direct frozen metadata joins; no new mechanics or acceptance rules.",
        "candidate": register["candidate"], "case_ids": CASES, "accounting": register["accounting"],
        "force_source": {k: v for k, v in register["same_state_force_source"].items() if k != "nominal_source_states"},
        "nominal_source_state_pointer": "/same_state_force_source/nominal_source_states in the frozen register",
        "methods": {name: {k: record[k] for k in ["source", "sha256", "schema", "counts", "limits", "indexed_nominal_records"] if k in record} for name, record in methods.items()},
        "blocks": blocks, "retained_frame_arrangements": retained,
        "source_path_convention": "Method/member sources are relative to mvp-resume-2026-10-01. Paths beginning docs/ are relative to the repository; /tmp/ paths are absolute. Force/axis/retained pointers without a source refer to the frozen register; hardware row indices refer to the pinned engagement CSV.",
        "requirements": REQUIREMENTS,
        "finite_next_joint_groups": {code: [b["block_id"] for b in blocks if code in b["recorded_remaining_requirement_ids"]] for code in REQUIREMENTS},
        "conditional_assumptions": [
            "Recorded timber/grade, final-piece CF=1 where specified, bolt steel/shank/thread profile and washer/head/nut properties remain hypotheses; no delivered inspection or new resistance is asserted.",
            "No-slip floor, no preload/friction, source rank 296/297, bounded nonunique seating and panel screw laws remain source limits. No floor test or blanket external sign-off is added.",
            "Purchasing specifications and three-pitch projection are already recorded. The projection option is not a universal installation rule or an adopted failure criterion.",
            "A/C/T operation routes retain supported member handling, thread-compatible capture and intact harness assumptions. Generic unobserved physical operation is not a reason to rerun completed fit/seat witnesses.",
        ],
        "parent_frame_and_panel_exceptions": [
            {"member": "base_rail_top", "comparison": 1.021524, "basis": "Recorded compatible intact-prism shear/torsion against unchanged normal-duration reference; an unresolved declared comparison, not a new block failure or physical failure.", "source": "member-stability-attempt01/four-screw-layout01/checks.json", "incident_blocks": [b["block_id"] for b in blocks if "base_rail_top" in b["hosts"]]},
            {"axis_id": "round_panel_upper_left_edge_2", "axial_n": 1871.251, "simultaneous_V_n": 726.611, "basis": "Recorded head/withdrawal comparison and panel sharing remain parent-owned. This consolidation does not adopt a measured Hillman failure.", "source": "upper-corner-screw-layout/joint-register.md#finite-remaining-load-transfer-decisions"},
        ],
        "preserved_finished_work": {"knee_placement_witnesses": 96, "added_length_axes": 12, "retained_supported_seats": 24, "primary_geometry_axes": len(primary_ids), "no_replay_required": True},
        "source_receipt_scope": "Direct consumed artifact hashes are checked. Nested historical dependency maps and inherited metadata-only differences are retained as provenance, not a claim that every mutable producer still has its old bytes.",
        "inherited_receipt_differences": register["inherited_receipt_differences"],
        "native_or_frame_or_CAD_execution": False, "tests_run": False,
        "new_material_or_resistance_claim": False, "complete_joint_acceptance": False, "physical_release": False,
    }
    require(sum(len(b["axes"]) for b in blocks) == 96, "Block incidence count differs")
    return result, pins


def render(result: dict, output: Path) -> str:
    lines = [
        "# Remaining duties for the 24 current connector blocks", "",
        "This is a consolidation of completed engineering checks and their recorded missing load-transfer/resistance scope. It uses the current six nominal-gap 250 lb cases after the four upper screw moves. It changes no geometry, mechanics, material reference, adopted criterion or release flag.", "",
        "The new [left common-block result](upper-left-block.md) is **complete** for six cases, twelve host models, four bolts and 32 faces (`5e8c52e5…`). Parent's [left component replay](upper-left-block-components.md) is also **complete** (`25f0bb27…`): lateral 0.722296, finished parallel path 0.142295, mean washer pressure 0.667024 and smooth-bolt VM/92 ksi 0.275588. The [right integration](upper-right-block.md) is complete (`0b0b392b…`, published at `d1014710`): respective indices 0.813949, 0.160367, 0.770232 and 0.313740. Both use a common rigid cleat gauge; neither qualifies elastic timber or changes the frame force allocation.", "",
        "## Per-block evidence map", "",
        "Each row retains four block-axis incidences. Exact axis IDs, receiver interfaces, simultaneous cases, signed ties, member witnesses, seat pointers, hardware profile specifications and operation pointers are in the machine file. **V/T** means the original frame peak lateral force and its simultaneous signed tie, in N; independent maxima are not combined. **N/ST** gives this block's completed conditional bore-free normal and compatible shear/torsion indices, not a whole-joint capacity; `—` means the rectangular trace is inapplicable, not failed.", "",
        "**M**: current member/body balance and restraint/prism screens, including each host. **R/WA**: individual remaining-bolt/ideal-annulus references. **TC/BC**: top/bottom same-state components and finished paths. **E/H**: end-grain/header method. **S**: separate lower-left service references. **P**: partial central-ring result. **K/KB/KF**: continuous-knee reference/static bearing/common-shaft placement. **Left/Right**: their own complete finite rigid-block response. Seat geometry is already indexed for every incident axis; WA alone is not proof of supported contact.", "",
        "**A**: preserved component extraction records and conditional assembly order; **CAP**: use the already completed captured-nut alternative on that row's `rail_2`; **T**: corrected top straight approaches and side-before-rail installation/rail-before-side removal. `+2` identifies the two axes in that block covered by the completed twelve-axis length extension screen. These are bounded geometric/operation scopes, not observed installation or a new qualification checklist.", "",
        "| Block | Hosts | Frame V / simultaneous T (N) | Completed wood N / ST | Completed bolt / support methods | Fit / operation | Recorded remaining scope |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for block in result["blocks"]:
        member = block["member_checks"][0]
        normal, shear = member["normal_peak"], member["shear_torsion_peak"]
        n = "—" if normal is None else f"{normal['timber_braced_normal_ratio']:.6f}"
        st = "—" if shear is None else f"{shear['shear_face_ratio']:.6f}"
        labels = ["M", *[METHOD_LABELS[m] for m in block["completed_component_method_ids"]]]
        if block["local_whole_block"]:
            labels.append("Left" if block["block_id"] == "top_outer_left_cleat" else "Right")
        force = block["source_force_peak"]
        fit = block["fit_operation_label"] + (f"; +{len(block['length_extension_axis_ids'])}" if block["length_extension_axis_ids"] else "")
        lines.append(f"| `{block['block_id']}` | " + "<br>".join(f"`{h}`" for h in block["hosts"]) + f" | {force['V_n']:.3f} / {force['simultaneous_T_n']:.3f} | {n} / {st} | {', '.join(labels)} | {fit} | {', '.join(block['recorded_remaining_requirement_ids'])} |")
    lines += [
        "", "## Exact finite remaining joint work", "",
        "The identifiers below describe gaps already recorded by the consumed methods. They do not infer work from the register's generic null capacity fields. W is tied to each named block/host's actual opening intervals and signed cuts; it does not request another gross-member screen or a full elastic timber solve.", "",
        "| ID | Existing unresolved requirement | Exact scope |", "| --- | --- | --- |",
    ]
    scopes = {
        "W": "24 blocks and their named hosts; exact interval counts and current geometry pointers are in each `member_checks` record. Header section/contact results and corner finished tangent paths remain completed partial coverage.",
        "H": "Six header duties: two center-post, two center-principal and two inner knee blocks; twelve header axes.",
        "K": "Four continuous knee-side bolts shared by the left/right spine and inner frame blocks; four physical bolts, not eight.",
        "P": "Only `center_principal_right_2` nut seat on `base_principal_center_right`.",
        "C": "Two top and two bottom outer cleats; current component results stay active. Top allocations have finite compatible rigid-block responses; bottom component/body-balance scope remains separate.",
    }
    for code in ("P", "K", "H", "C", "W"):
        lines.append(f"| {code} | {REQUIREMENTS[code]['requirement']} | {scopes[code]} |")
    lines += [
        "", "Both top common-block responses and their component replays are finished. The finite next joint packets are the single central partial-seat transfer, the shared left/right continuous-knee transfer and the six named header duties. Corner resistance and named finished-opening transfer then use their saved simultaneous actions. This is a reuse agenda; it authorizes no mechanics execution or physical work.", "",
        "## Completed geometry and conditional assumptions", "",
        "All **96 knee shaft placements** remain completed, alongside 24 bearing fields and 96 static endpoint witnesses. Their loaded contact-compatibility gap is K, not a reopened placement failure. The 92 ksi endpoint scenario peaks at 0.922843; the alternative 45 ksi sensitivity reaches 1.317816. Neither scenario establishes delivered asymmetric-bolt resistance or a failed adopted criterion.", "",
        "All **twelve bolt-tip/travel extension screens** are complete: four center-post, four principal/header and four inner knee/header axes, with no added overlap or undecided pair. The purchasing profile specification already covers all **104 bolts, 104 nuts and 208 washers**, separately from **66 Hillman screws**. Delivered LB/runout, full-form thread/nut engagement and bearing faces remain conditional product facts. The optional three-pitch projection is not an adopted failure rule. Do not restart the finished length checks from those unknowns.", "",
        "Remaining and upper seat records, corrected top/bottom seats, primary knee offset evidence and **24 retained nominal annuli/72 probes** stay completed within their geometry scopes. Only the central passage-side nut seat has a recorded partial-support exception. Its smaller 10 mm supported ring is already complete (area 24.358092 mm², current pressure scenario 0.942288 MPa, conditional ratio 0.218668); the unsupported crescent has no full-annulus credit. Washer/head/nut metal properties and loaded spreading are separate from supported geometry.", "",
        "The four direct nut-slide collisions already have bounded captured-nut alternatives. Preserve those sequences. For the retained leg stacks, preserve the intact-harness staging assumption at `wire_010_A10_A11` and `wire_130_K10_K11`. Top turning/counterhold and full stroke remain outside the straight-approach scope. These limits do not invalidate completed geometric routes or create another blanket operation gate.", "",
        "The twelve retained axes are six separate pairs, outside the 96 block incidences. Their fresh individual/row-factor maximum is 0.962538; fresh 3/8- and 1/2-inch ideal pressure ratios are 0.208053 and 0.264300. Historical support-report pressures are not reused. The machine file joins all six arrangements to current force/component records and the completed concentric geometry; actual oblique Cg and complete local/washer resistance remain unassigned.", "",
        "Parent retains the top-rail intact-prism comparison **1.021524** against the unchanged duration reference and the upper-left `edge_2` screw comparison (**1,871.251 N** axial with **726.611 N** lateral). These are explicit unresolved declared comparisons, not measured physical failures. Source rank 296/297, nonunique fixed-force seating, timber restraint/material hypotheses, screw laws and no-slip floor stay conditional. No adopted block failure is inferred from them; no floor test, material change or external sign-off is added.", "",
        "## Machine receipt and reproduction", "",
        "Frozen direct inputs:", "", "| Input | SHA-256 |", "| --- | --- |",
    ]
    for key in ("assessment", "model", "rows", "comparison", "response", "register", "left", "left_components", "right"):
        path, sha = FROZEN[key]
        lines.append(f"| `{path.relative_to(HERE)}` | `{sha}` |")
    rel = output.relative_to(HERE)
    lines += [
        "", f"Machine table: [`duties.json`]({rel}/duties.json). Source/output receipt: [`receipt.json`]({rel}/receipt.json). Raw evidence stays ignored. The producer reads JSON/CSV metadata and hashes saved bytes; it opens no force/operator array and imports no CAD/mechanics helper. Each compatible method artifact is authenticated against the frozen register. Direct consumed source hashes are rechecked before writing. Inherited mutable producer differences remain provenance, not a new numerical failure.", "",
        "From the repository root, use a fresh child under the owned raw folder:", "", "```sh",
        "python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/remaining-block-duties.py \\",
        f"  --output {location(output.with_name(output.name + '-replay'))}", "```", "",
        "Only this producer, this table and `rawlocal/remaining-block-duties/` belong to this task. Completed sources remain active and preserved; no archive, pruning, shared-document edit, staging or commit is performed. No frame/native/CAD/heavy run or test is required by this consolidation. Complete joint acceptance and physical release remain false.", "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RAW / "attempt01")
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(RAW) and output != RAW, "Output must be a fresh child of the owned raw folder")
    require(not output.exists(), f"Preserve existing output: {output}")
    result, pins = build()
    summary = render(result, output)
    for path, expected in pins.items():
        require(digest(path) == expected, f"Consumed source changed before write: {path}")
    output.mkdir(parents=True)
    (output / "duties.json").write_text(encoded(result))
    (HERE / "remaining-block-duties.md").write_text(summary)
    receipt = {
        "schema": "remaining_block_duties_direct_source_receipt/v1",
        "source_sha256": {location(path): sha for path, sha in sorted(pins.items())},
        "source_unchanged_before_write": True,
        "output_sha256": {"duties.json": digest(output / "duties.json"), "remaining-block-duties.md": digest(HERE / "remaining-block-duties.md")},
        "accounting": result["accounting"],
        "left_component_replay": "complete 25f0bb27; local common-block response complete 5e8c52e5",
        "source_receipt_scope": result["source_receipt_scope"],
        "native_or_frame_or_CAD_execution": False, "tests_run": False,
        "complete_joint_acceptance": False, "physical_release": False,
    }
    (output / "receipt.json").write_text(encoded(receipt))
    print(f"24 block duties; {len(pins)} direct sources unchanged; receipt={location(output / 'receipt.json')}")


if __name__ == "__main__":
    main()
