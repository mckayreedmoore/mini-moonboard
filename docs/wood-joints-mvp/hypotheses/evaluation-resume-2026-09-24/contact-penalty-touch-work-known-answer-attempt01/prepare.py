#!/usr/bin/env python3
"""Prepare and lineage-check the exact-touch penalty work fixture; no solver."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import tarfile


HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
BASE = EVAL / "contact-energy-known-answer-attempt01"
MECHANICAL_BASE = EVAL / "contact-section-force-known-answer-attempt02"
SOURCE_ARCHIVE = EVAL / "ordinary-external-force-transient-attempt04-diagnostic" / "build-attempt02/source.tar.bz2"
MANUAL = HERE.parents[4] / "fea/generated/ccx_2.23.pdf"

MECHANICAL_BASE_PINS = {
    "input-freeze.json": "0603288af8a4385000d029eca0e31bda57fc63f39e474796033213026b5aa8f7",
    "execution.json": "2736908e0f59c73a43330021c6c3798e46fc3726b22a179ec3dcb1ee07b43435",
    "expected.json": "9298fdce2f9e3e04d5cc12112361a06c6029ecfbbf0f1fa9fa329925d1f42bfd",
    "verifier.py": "c68a9fd998d8ed601d4223118af1699b343cc6688e37818e03131fd84321524b",
    "verifier.json": "4a0fe723f21686ffa6e0d41ca7724b5f901b6234db87a4ac7b3a376dd73da215",
}
MECHANICAL_TOLERANCES = {
    "accepted_state_u3_profile_interface_gap_and_face_warp_mm": 1e-5,
    "force_abs_error_N": 0.001,
    "force_relative_error": 0.01,
    "open_reopen_resultant_support_force_norm_N": 0.001,
    "pressure_compliance_abs_error_mm3_per_N": 1e-10,
    "pressure_compliance_relative_error": 0.01,
    "tangential_reaction_and_top_plus_bottom_force_closure_norm_N":
        "<= 0.001 + 0.01 * current_analytic_compression_force_N",
}

PINNED = {
    "input-freeze.json": "7ca80c4cdfe92b1f8dfcb0d71c9a97884dd7b6bdabb540b50902cf21c16396a0",
    "execution.json": "624c6b2fb3b4a72dff8fab08c4c724444bc46ecb4ad3fccea8af722e224656e1",
    "expected.json": "c49f2bbc020e4db0e38e8fb5973b3f5fbe6af502597c010a886f9e94353b8142",
    "verifier.json": "15ff0827a312df7b5c4e10860ed57f852532b1f5dc718da1a7ec94f260470951",
}
BASE_INPUT = "input/penalty_c3d10.inp"
BASE_INPUT_SHA = "40cdf59c7184f828dac9275ac10a3c04be10e597cf769ec1af332293ee8cb7dc"
BASE_OUTPUT_PINS = {
    "coupon.inp": "40cdf59c7184f828dac9275ac10a3c04be10e597cf769ec1af332293ee8cb7dc",
    "coupon.dat": "37afbec4fc7d2a2b3dc7053f5a66d8e1470262f24f9436833b699a4d817a5a0d",
    "coupon.sta": "30dde235c1f17bb3eab89aea8db856dacb8134f69cf95e84bdec4e7aacb48952",
    "coupon.cvg": "b94d4e2f2057e06a0dbb29feb8ce583820e579817ca3742f27b3b7e2cac52fab",
}
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/contactprints.f":
        "88a2fc1a15caa2ab9b28de6ff6c4566f34e7f24c9db5c2c3ee4ef333439c717d",
    "CalculiX/ccx_2.23/src/elprints.f":
        "15d4ad6001e3ecb4eeaa05cba39333626b6c079cbe9d696879092dc2c73ff7b7",
    "CalculiX/ccx_2.23/src/printout.f":
        "ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32",
    "CalculiX/ccx_2.23/src/printoutelem.f":
        "e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544",
    "CalculiX/ccx_2.23/src/printoutcontact.f":
        "4e1f5452d5fd268d7e4f1ab702de4804bb8f34a429b5e2c14ff9af3df9a9a055",
    "CalculiX/ccx_2.23/src/statics.f":
        "d5add12845e7dc6e7a19043fa6114012b9f36ed0723590308d60f4b09eee4599",
}
PAIR_PRINT = (
    "*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER,FREQUENCY=1\n"
    "CF,CFN,CFS\n"
)
STATES = [
    {"name": "OPEN", "target_U3_mm": 0.001, "target_text": "0.001000",
     "source_step": 0, "total_time": 1.0, "expected_energy_N_mm": 0.0,
     "analytical_segment_work_N_mm": 0.0},
    {"name": "TOUCH_AFTER_OPEN", "target_U3_mm": 0.0, "target_text": "0.000000",
     "source_step": 0, "total_time": 2.0, "expected_energy_N_mm": 0.0,
     "analytical_segment_work_N_mm": 0.0},
    {"name": "COMPRESSION", "target_U3_mm": -0.005, "target_text": "-0.005000",
     "source_step": 1, "total_time": 3.0, "expected_energy_N_mm": 1.0,
     "analytical_segment_work_N_mm": 1.0},
    {"name": "TOUCH_AFTER_COMPRESSION", "target_U3_mm": 0.0, "target_text": "0.000000",
     "source_step": 1, "total_time": 4.0, "expected_energy_N_mm": 0.0,
     "analytical_segment_work_N_mm": -1.0},
    {"name": "REOPEN", "target_U3_mm": 0.001, "target_text": "0.001000",
     "source_step": 2, "total_time": 5.0, "expected_energy_N_mm": 0.0,
     "analytical_segment_work_N_mm": 0.0},
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"Nonstandard JSON number {value} in {path}")))


def save_new(path: Path, value: dict) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify_source() -> dict:
    require(sha(SOURCE_ARCHIVE) == "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7",
            "Pinned CalculiX 2.23 source archive changed")
    require(sha(MANUAL) == "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330",
            "Pinned CalculiX 2.23 manual changed")
    found = {}
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for member_path, digest in SOURCE_MEMBERS.items():
            member = archive.extractfile("./" + member_path)
            require(member is not None, f"Missing pinned source member: {member_path}")
            actual = hashlib.sha256(member.read()).hexdigest()
            require(actual == digest, f"Pinned source member changed: {member_path}")
            found[member_path] = actual
    return {"archive_sha256": sha(SOURCE_ARCHIVE), "manual_sha256": sha(MANUAL),
            "source_members_sha256": found}


def parse_node_blocks(dat_text: str, kind: str) -> dict[float, dict[int, tuple[float, float, float]]]:
    pattern = re.compile(
        rf"^\s*{re.escape(kind)}\s+\([^\n]+\) for set ALLNODES and time\s+(\S+)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    result = {}
    for match in pattern.finditer(dat_text):
        total_time = float(match.group(1))
        rows = {}
        for line in dat_text[match.end():].splitlines():
            fields = line.split()
            if not fields:
                if rows:
                    break
                continue
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                require(node not in rows, f"Duplicate node {node} in {kind} at {total_time}")
                values = tuple(float(value) for value in fields[1:])
                require(all(math.isfinite(value) for value in values),
                        f"Nonfinite {kind} value at node {node}, time {total_time}")
                rows[node] = values
            elif rows:
                break
        require(rows and total_time not in result, f"Missing/duplicate {kind} block at {total_time}")
        result[total_time] = rows
    return result


def parse_energy_blocks(dat_text: str) -> dict[float, dict[str, float]]:
    result: dict[float, dict[str, float]] = {}
    lines = dat_text.splitlines()
    pattern = re.compile(
        r"^total internal energy for set (UPPER|LOWER) and time\s+(\S+)$",
        re.IGNORECASE,
    )
    cels_pattern = re.compile(r"^total contact spring energy for time\s+(\S+)$", re.IGNORECASE)
    for index, line in enumerate(lines):
        header = " ".join(line.split())
        match = pattern.fullmatch(header)
        channel = None
        time_token = None
        if match:
            channel, time_token = match.groups()
            channel = channel.upper()
        else:
            match = cels_pattern.fullmatch(header)
            if match:
                channel, time_token = "CELS", match.group(1)
        if channel is None:
            continue
        total_time = float(time_token)
        value_index = index + 1
        while value_index < len(lines) and not lines[value_index].strip():
            value_index += 1
        require(value_index < len(lines), f"Missing {channel} value at {total_time}")
        fields = lines[value_index].split()
        require(len(fields) == 1, f"Malformed {channel} total at {total_time}")
        value = float(fields[0])
        require(math.isfinite(value), f"Nonfinite {channel} total at {total_time}")
        state = result.setdefault(total_time, {})
        require(channel not in state, f"Duplicate {channel} total at {total_time}")
        state[channel] = value
    for total_time, channels in result.items():
        require(set(channels) == {"UPPER", "LOWER", "CELS"},
                f"Incomplete energy output at {total_time}")
    return result


def format_quantum(token: str) -> float:
    match = re.fullmatch(r"[+-]?\d\.\d{6}E([+-]\d{2,3})", token, re.IGNORECASE)
    require(match is not None, f"Unexpected pinned E13.6 token: {token}")
    exponent = int(match.group(1))
    return 10.0 ** (exponent - 6)


def parse_raw_node_block(dat_text: str, header: re.Match, wanted: set[int]) -> dict[int, str]:
    rows = {}
    for line in dat_text[header.end():].splitlines():
        fields = line.split()
        if not fields:
            if rows:
                break
            continue
        if len(fields) == 4 and fields[0].isdigit():
            node = int(fields[0])
            if node in wanted:
                require(node not in rows, f"Duplicate raw RF node {node}")
                rows[node] = fields[3]
        elif rows:
            break
    require(set(rows) == wanted, "Raw top RF3 block is incomplete")
    return rows


def actual_base_observation() -> dict:
    case = BASE / "output/penalty_c3d10"
    dat_text = (case / "coupon.dat").read_text()
    displacements = parse_node_blocks(dat_text, "displacements")
    forces = parse_node_blocks(dat_text, "forces")
    energies = parse_energy_blocks(dat_text)
    expected_times = [1.0, 2.0, 3.0]
    require(sorted(displacements) == expected_times and sorted(forces) == expected_times
            and sorted(energies) == expected_times, "Pinned penalty state coverage changed")
    top_nodes = {5, 6, 7, 8, 28, 29, 31, 32, 34}
    states = {}
    raw_force_tokens = {}
    force_pattern = re.compile(
        r"^\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$", re.MULTILINE
    )
    force_headers = list(re.finditer(
        r"^\s*forces\s+\([^\n]+\) for set ALLNODES and time\s+(\S+)\s*$",
        dat_text, re.IGNORECASE | re.MULTILINE,
    ))
    for total_time in expected_times:
        require(top_nodes <= set(displacements[total_time])
                and top_nodes <= set(forces[total_time]),
                f"Pinned top-node U/RF coverage changed at {total_time}")
        top_u = [displacements[total_time][node][2] for node in sorted(top_nodes)]
        top_rf = [forces[total_time][node][2] for node in sorted(top_nodes)]
        u_mean = sum(top_u) / len(top_u)
        require(max(abs(value - u_mean) for value in top_u) <= 1e-9,
                f"Pinned top prescribed U3 is not uniform at {total_time}")
        q = sum(top_rf)
        energy = energies[total_time]
        states[total_time] = {
            "top_U3_mm": u_mean,
            "top_RF3_sum_N": q,
            "body_ELSE_upper_N_mm": energy["UPPER"],
            "body_ELSE_lower_N_mm": energy["LOWER"],
            "contact_CELS_N_mm": energy["CELS"],
            "combined_energy_N_mm": sum(energy.values()),
        }
        header = next((item for item in force_headers
                       if abs(float(item.group(1)) - total_time) < 1e-9), None)
        require(header is not None, f"Missing force text block at {total_time}")
        raw_force_tokens[total_time] = parse_raw_node_block(dat_text, header, top_nodes)
    compress_tokens = raw_force_tokens[2.0]
    top_rf_round_bound = 0.5 * sum(format_quantum(value) for value in compress_tokens.values())
    q_open = states[1.0]["top_RF3_sum_N"]
    q_compress = states[2.0]["top_RF3_sum_N"]
    u_open = states[1.0]["top_U3_mm"]
    u_compress = states[2.0]["top_U3_mm"]
    endpoint_chord_work = 0.5 * (q_open + q_compress) * (u_compress - u_open)
    touch_to_compression_work = 0.5 * q_compress * u_compress
    return {
        "states": states,
        "top_RF3_E13_6_rounding_bound_N": top_rf_round_bound,
        "old_open_to_compression_endpoint_chord_work_N_mm": endpoint_chord_work,
        "new_touch_to_compression_endpoint_trapezoid_N_mm": touch_to_compression_work,
        "baseline_compression_energy_N_mm": states[2.0]["combined_energy_N_mm"],
        "top_force_node_ids": sorted(top_nodes),
    }


def analytical_contract(source_pins: dict, observation: dict, deck_sha: str) -> dict:
    mechanical_expected, mechanical_baseline = verify_mechanical_baseline()
    mechanical_tolerances = mechanical_expected["analytical_known_answer"]["predeclared_tolerances"]
    return {
        "schema": "calculix_penalty_exact_touch_work_known_answer/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NO_FREEZE_OR_NATIVE_EXECUTION",
        "native_execution_authorized": False,
        "mechanical_acceptance": False,
        "work_energy_acceptance": False,
        "joint_acceptance": False,
        "release": False,
        "baseline_passing_penalty_fixture": {
            "path": "contact-energy-known-answer-attempt01",
            "input_freeze_sha256": PINNED["input-freeze.json"],
            "execution_sha256": PINNED["execution.json"],
            "expected_sha256": PINNED["expected.json"],
            "verifier_result_sha256": PINNED["verifier.json"],
            "penalty_input_sha256": BASE_INPUT_SHA,
            "penalty_DAT_sha256": BASE_OUTPUT_PINS["coupon.dat"],
            "penalty_STA_sha256": BASE_OUTPUT_PINS["coupon.sta"],
            "penalty_CVG_sha256": BASE_OUTPUT_PINS["coupon.cvg"],
            "baseline_mechanical_status": "PASS_SECTION_STRESS_FIXTURE",
            "baseline_body_ELSE_status": "PASS_KNOWN_ANSWER",
            "baseline_penalty_CELS_status": "PASS_KNOWN_ANSWER",
            "baseline_penalty_combined_energy_N_mm": 0.9991998,
            "baseline_MORTAR_not_reused": True,
        },
        "inherited_mechanical_gates": {
            "baseline_path": "contact-section-force-known-answer-attempt02",
            **mechanical_baseline,
            "predeclared_tolerances": {
                key: mechanical_tolerances[key] for key in MECHANICAL_TOLERANCES
            },
            "section_force_contract": mechanical_expected["section_force_contract"],
            "gate_scope": [
                "full DAT U/RF profile, reaction force, force closure, tangential reactions, and compliance",
                "accepted direct-step history and convergence transcript",
                "full-mesh DISP/FORC/STRESS trace coverage",
                "section force, moment, area, and face-normal checks",
            ],
            "acceptance_authority": "method-fixture output checks only; mechanical and joint acceptance remain false",
        },
        "input": {
            "path": "input/penalty_touch_work.inp",
            "sha256": deck_sha,
            "baseline_source_path": BASE_INPUT,
            "baseline_source_sha256": BASE_INPUT_SHA,
            "only_physical_path_change": "five fixed full steps with prescribed top U3 targets; all material, geometry, contact, and constraint cards preserved",
            "output_only_extension": PAIR_PRINT.strip().replace("\n", " / "),
            "existing_outputs_preserved": ["U", "RF", "ELSE per body", "global CELS"],
        },
        "solver_contract": {
            "version": "CalculiX 2.23",
            "source_archive_sha256": source_pins["archive_sha256"],
            "manual_sha256": source_pins["manual_sha256"],
            "source_members_sha256": source_pins["source_members_sha256"],
            "procedure": "NLGEOM static, *STATIC,DIRECT, fixed full increment 1,1 per step",
            "states": STATES,
            "initial_reference": {"top_U3_mm": 0.0, "top_RF3_sum_N": 0.0,
                                  "stored_energy_N_mm": 0.0},
            "require_exactly_one_accepted_increment_per_step": True,
            "expected_accepted_total_times": [1.0, 2.0, 3.0, 4.0, 5.0],
        },
        "analytical_reference": {
            "units": "mm, N, MPa=N/mm2; work and energy N*mm",
            "youngs_modulus_N_per_mm2": 100000.0,
            "body_area_mm2": 4.0,
            "body_thickness_mm": 2.0,
            "contact_area_mm2": 4.0,
            "linear_contact_slope_N_per_mm3": 100000.0,
            "effective_compliance_formula": "C = L_upper/E + L_lower/E + 1/K",
            "effective_compliance_mm3_per_N": 5e-5,
            "signed_top_reaction_formula": "Q(U3)=A*U3/C for U3<0; Q=0 for U3>=0",
            "compression": {
                "top_U3_mm": -0.005,
                "top_RF3_sum_N": -400.0,
                "each_body_shortening_mm": 0.002,
                "contact_overclosure_mm": 0.001,
                "body_ELSE_each_N_mm": 0.4,
                "body_ELSE_pair_N_mm": 0.8,
                "contact_CELS_N_mm": 0.2,
                "combined_energy_N_mm": 1.0,
                "analytical_trapezoidal_work_touch_to_compression_N_mm": 1.0,
            },
            "open_touch_reopen_energy_N_mm": 0.0,
            "analytical_segment_work_N_mm": [0.0, 0.0, 1.0, -1.0, 0.0],
            "pair_force": {
                "selected_surfaces": {"slave": "SLAVE", "master": "MASTER"},
                "compression_CF_N": [0.0, 0.0, 400.0],
                "compression_CF_origin_moment_N_mm": [400.0, -400.0, 0.0],
                "compression_CFN_N": [0.0, 0.0, 400.0],
                "compression_CFN_origin_moment_N_mm": [400.0, -400.0, 0.0],
                "compression_CFS_N": [0.0, 0.0, 0.0],
                "compression_CFS_origin_moment_N_mm": [0.0, 0.0, 0.0],
                "open_touch_CF_CFN_CFS_origin_moment_N_mm": [0.0, 0.0, 0.0],
                "mean_slave_normal_unit": [0.0, 0.0, -1.0],
                "CFN_projection_on_mean_normal_N_tension_positive": -400.0,
                "open_touch_CF_CFN_CFS_N": [0.0, 0.0, 0.0],
                "force_abs_error_N": 0.001,
                "force_relative_error": 0.01,
                "zero_force_abs_error_N": 0.001,
                "moment_abs_error_N_mm": 0.001,
                "moment_relative_error": 0.01,
                "moment_reference_scale_N_mm": 400.0,
                "moment_acceptance_inequality": "compression norm error <= 0.01*400 + 0.001 = 4.001 N*mm; zero-resultant states <= 0.001 N*mm",
                "finite_force_moment_required": True,
                "area_derived_centroid_and_mean_normal_may_be_undefined_when_area_zero": True,
            },
        },
        "work_energy_contract": {
            "reaction_work_formula": "W_i = sum_TOP 0.5*(RF3_i + RF3_(i+1))*(U3_(i+1)-U3_i); TOP U3 must be uniform",
            "stored_energy_formula": "E_i = ELSE_UPPER_i + ELSE_LOWER_i + CELS_i",
            "incremental_comparison": "abs(W_i-delta_E_i) <= max(abs_floor, relative_tolerance*max(abs(W_i),abs(delta_E_i)))",
            "analytical_work_comparison": "abs(W_i-W_analytic_i) <= max(abs_floor, relative_tolerance*max(abs(W_i),abs(W_analytic_i)))",
            "cumulative_comparison": "compare sum(W_i) from the initial reference with the analytical state energy",
            "relative_tolerance": 0.05,
            "absolute_work_tolerance_N_mm": 3e-6,
            "absolute_floor_rationale": (
                "Deliberately conservative at the 1 N*mm oracle scale: E13.6 has a 1e-6 last-place unit there; "
                "three independent ELSE/ELSE/CELS channels across a two-state difference budget up to six half-units (3e-6). "
                "Actual 0.4/0.2 and near-zero values use finer exponent-scaled units. "
                "Pinned compression TOP RF E13.6 rounding gives a 7e-5 N resultant bound; even applying it at both ends "
                "of the maximum 0.005 mm interval contributes at most 3.5e-7 N*mm work rounding. This is a numerical "
                "readout budget, not physical uncertainty or a current-joint floor."
            ),
            "parent_review_required_before_freeze": True,
        },
        "energy_output_contract": {
            "endpoint_component_relative_tolerance": 0.01,
            "endpoint_component_absolute_tolerance_N_mm": 1e-6,
            "require_all_body_ELSE_and_global_CELS_at_every_state": True,
            "require_CF_CFN_CFS_pair_record_at_every_state": True,
            "MORTAR_scope": "excluded; unsupported CELS is not reused or interpreted as zero",
        },
        "pinned_baseline_observation": observation,
        "no_current_joint_authority": {
            "current_joint_absolute_work_floor_selected": False,
            "current_joint_energy_gate_pass": False,
            "joint_or_release_acceptance": False,
        },
    }


def make_step(template: str, name: str, target: str) -> str:
    matches = list(re.finditer(r"(?m)^\*\* STEP: [^\n]*$", template))
    require(len(matches) == 1, "Expected one step-name comment")
    result = template[:matches[0].start()] + f"** STEP: {name}; prescribed top-face U3={target} mm" + template[matches[0].end():]
    boundary_matches = list(re.finditer(r"(?m)^TOP,3,3,[^\r\n]+$", result))
    require(len(boundary_matches) == 1, "Expected one top U3 target line per step")
    boundary = boundary_matches[0]
    result = result[:boundary.start()] + f"TOP,3,3,{target}" + result[boundary.end():]
    require(result.count("*STATIC,DIRECT\n1,1\n") == 1,
            "Fixed DIRECT full-step control changed")
    require(result.count("*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1\nCELS\n") == 1,
            "Existing global CELS request changed")
    require(result.count(PAIR_PRINT) == 0, "Pair request already present in source template")
    end = result.rfind("*END STEP")
    require(end >= 0 and result.count("*END STEP") == 1, "Malformed source step block")
    return result[:end] + PAIR_PRINT + result[end:]


def normalize_step(step: str) -> str:
    without_pair = step.replace(PAIR_PRINT, "")
    without_comment = re.sub(r"(?m)^\*\* STEP: [^\n]*$", "** STEP", without_pair)
    normalized_target = re.sub(r"(?m)^TOP,3,3,[^\r\n]+$", "TOP,3,3,<TARGET>", without_comment)
    return normalized_target


def build_deck() -> tuple[str, dict]:
    base_path = BASE / BASE_INPUT
    raw = base_path.read_text()
    starts = list(re.finditer(r"(?m)^\*\* STEP: [^\n]*$", raw))
    require(len(starts) == 3, "Expected exactly three baseline full steps")
    prefix = raw[:starts[0].start()]
    source_steps = []
    for index, start in enumerate(starts):
        finish = starts[index + 1].start() if index + 1 < len(starts) else len(raw)
        source_steps.append(raw[start.start():finish])
    require(all(step.count("*STEP,NLGEOM,INC=100") == 1
                and step.count("*END STEP") == 1 for step in source_steps),
            "Baseline state comment is not paired with one fixed full step")
    normalized_templates = [normalize_step(source_steps[i]) for i in range(3)]
    planned = []
    for state in STATES:
        template = source_steps[state["source_step"]]
        step = make_step(template, state["name"], state["target_text"])
        require(normalize_step(step) == normalized_templates[state["source_step"]],
                f"Non-schedule input changed in {state['name']}")
        planned.append(step)
    deck = prefix + "".join(planned)
    require(deck.count("*STEP,NLGEOM,INC=100") == 5
            and deck.count("*STATIC,DIRECT\n1,1\n") == 5,
            "Expected five unchanged fixed DIRECT steps")
    require(deck.count(PAIR_PRINT) == 5
            and deck.count("*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1\nCELS\n") == 5,
            "Pair or global CELS output is not requested at every state")
    for expected_state, step in zip(STATES, planned):
        require(f"** STEP: {expected_state['name']};" in step
                and f"TOP,3,3,{expected_state['target_text']}" in step,
                f"Schedule target mismatch in {expected_state['name']}")
    return deck, {"base_step_sha256": [hashlib.sha256(item.encode()).hexdigest()
                                        for item in source_steps],
                  "normalized_templates_preserved": True,
                  "step_count": len(planned),
                  "pair_request_count": deck.count(PAIR_PRINT)}


def verify_baseline() -> tuple[dict, dict]:
    for name, digest in PINNED.items():
        require(sha(BASE / name) == digest, f"Pinned baseline changed: {name}")
    freeze = read_json(BASE / "input-freeze.json")
    execution = read_json(BASE / "execution.json")
    expected = read_json(BASE / "expected.json")
    result = read_json(BASE / "verifier.json")
    for relative, digest in freeze["files_sha256"].items():
        require(sha(BASE / relative) == digest, f"Frozen baseline file changed: {relative}")
    run = next((item for item in execution["runs"] if item.get("case") == "penalty_c3d10"), None)
    require(run is not None and run.get("status") == "completed"
            and run.get("docker_cli_exit_code") == 0,
            "Pinned penalty run did not complete")
    case_dir = BASE / "output/penalty_c3d10"
    for name, digest in BASE_OUTPUT_PINS.items():
        require(sha(case_dir / name) == digest == run["outputs_sha256"][name],
                f"Pinned penalty output changed: {name}")
    require(sha(BASE / BASE_INPUT) == BASE_INPUT_SHA
            and sha(case_dir / "coupon.inp") == BASE_INPUT_SHA,
            "Pinned penalty input identity changed")
    require(result.get("status") == "PASS_MECHANICAL_FIXTURE_ONLY"
            and result.get("mechanical_status") == "PASS_SECTION_STRESS_FIXTURE"
            and result.get("mechanical_acceptance") is False
            and result.get("joint_acceptance") is False,
            "Attempt01 mechanical method-fixture status changed")
    penalty = result["energy_audit"]["cases"]["penalty_c3d10"]
    require(penalty["body_ELSE"]["status"] == "PASS_KNOWN_ANSWER"
            and penalty["contact_CELS"]["status"] == "PASS_KNOWN_ANSWER"
            and penalty["combined_ELSE_plus_CELS"]["status"] == "PASS_KNOWN_ANSWER",
            "Penalty energy known-answer baseline no longer passes")
    require(result["energy_audit"]["cases"]["mortar_c3d10"]["contact_CELS"]["status"]
            == "OBSERVED_MISMATCH_UNVALIDATED",
            "MORTAR result is not separately preserved as unsupported")
    return expected, result


def verify_mechanical_baseline() -> tuple[dict, dict]:
    """Bind inherited profile, force, compliance, section, and stress gates."""
    for name, digest in MECHANICAL_BASE_PINS.items():
        require(sha(MECHANICAL_BASE / name) == digest,
                f"Pinned attempt02 mechanical baseline changed: {name}")
    freeze = read_json(MECHANICAL_BASE / "input-freeze.json")
    execution = read_json(MECHANICAL_BASE / "execution.json")
    expected = read_json(MECHANICAL_BASE / "expected.json")
    result = read_json(MECHANICAL_BASE / "verifier.json")
    for relative, digest in freeze["files_sha256"].items():
        require(sha(MECHANICAL_BASE / relative) == digest,
                f"Frozen attempt02 mechanical baseline changed: {relative}")
    tolerances = expected["analytical_known_answer"]["predeclared_tolerances"]
    require({key: tolerances[key] for key in MECHANICAL_TOLERANCES}
            == MECHANICAL_TOLERANCES,
            "Inherited attempt02 mechanical tolerance contract changed")
    require(result.get("status") == "PASS_SECTION_STRESS_FIXTURE"
            and result.get("mechanical_acceptance") is False
            and result.get("joint_acceptance") is False,
            "Pinned attempt02 mechanical/stress fixture is not a method-only pass")
    penalty_run = next((item for item in execution.get("runs", [])
                        if item.get("case") == "penalty_c3d10"), None)
    require(penalty_run is not None and penalty_run.get("status") == "completed"
            and penalty_run.get("docker_cli_exit_code") == 0,
            "Pinned attempt02 penalty fixture did not complete")
    case = MECHANICAL_BASE / "output/penalty_c3d10"
    output_pins = {}
    for name in ("coupon.inp", "coupon.dat", "coupon.sta", "coupon.cvg"):
        actual = sha(case / name)
        require(actual == penalty_run["outputs_sha256"][name],
                f"Pinned attempt02 mechanical output differs: {name}")
        output_pins[name] = actual
    return expected, {
        "input_freeze_sha256": MECHANICAL_BASE_PINS["input-freeze.json"],
        "execution_sha256": MECHANICAL_BASE_PINS["execution.json"],
        "expected_sha256": MECHANICAL_BASE_PINS["expected.json"],
        "verifier_source_sha256": MECHANICAL_BASE_PINS["verifier.py"],
        "verifier_result_sha256": MECHANICAL_BASE_PINS["verifier.json"],
        "penalty_output_sha256": output_pins,
        "predeclared_tolerances": {key: tolerances[key] for key in MECHANICAL_TOLERANCES},
    }


def self_check(observation: dict) -> dict:
    area = 4.0
    compliance = 5e-5
    displacement = [0.0, 0.001, 0.0, -0.005, 0.0, 0.001]

    def analytical_reaction(u: float) -> float:
        return area * u / compliance if u < 0 else 0.0

    reactions = [analytical_reaction(u) for u in displacement]
    work = [0.5 * (reactions[i] + reactions[i + 1]) *
            (displacement[i + 1] - displacement[i])
            for i in range(len(displacement) - 1)]
    require(work == [0.0, 0.0, 1.0, -1.0, 0.0],
            f"Analytical exact-touch work oracle failed: {work}")
    energies = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    delta_energy = [energies[i + 1] - energies[i]
                    for i in range(len(energies) - 1)]
    require(work == delta_energy, "Analytical work and energy increments differ")
    old_chord = observation["old_open_to_compression_endpoint_chord_work_N_mm"]
    reference = 1.0
    require(abs(old_chord - reference) > max(3e-6, 0.05 * max(abs(old_chord), abs(reference))),
            "Old force-free-gap chord unexpectedly falls within the proposed gate")
    observed_touch_trapezoid = observation["new_touch_to_compression_endpoint_trapezoid_N_mm"]
    baseline_energy = observation["baseline_compression_energy_N_mm"]
    require(abs(observed_touch_trapezoid - baseline_energy)
            <= max(3e-6, 0.05 * max(abs(observed_touch_trapezoid), abs(baseline_energy))),
            "Pinned endpoint evidence does not support the exact-touch method fixture")
    budget = 0.5 * 0.005 * 2 * observation["top_RF3_E13_6_rounding_bound_N"]
    require(budget < 3e-6, "Reaction work output precision exceeds the proposed floor")
    return {
        "status": "PASS_ANALYTICAL_AND_PINNED_ENDPOINT_PREFLIGHT",
        "native_run_performed": False,
        "input_freeze_created": False,
        "analytical_segment_work_N_mm": work,
        "analytical_energy_increments_N_mm": delta_energy,
        "old_open_to_compression_chord_N_mm": old_chord,
        "pinned_touch_to_compression_endpoint_work_N_mm": observed_touch_trapezoid,
        "pinned_compression_stored_energy_N_mm": baseline_energy,
        "work_output_rounding_bound_N_mm": budget,
        "proposed_absolute_floor_N_mm": 3e-6,
    }


def prepare() -> None:
    for relative in (Path("input/penalty_touch_work.inp"), Path("expected.json"),
                     Path("preparation.json")):
        require(not (HERE / relative).exists(), f"Refusing to replace existing {relative}")
    baseline_expected, baseline_result = verify_baseline()
    mechanical_expected, mechanical_baseline = verify_mechanical_baseline()
    source_pins = verify_source()
    observation = actual_base_observation()
    deck, lineage = build_deck()
    input_dir = HERE / "input"
    input_dir.mkdir(exist_ok=True)
    deck_path = input_dir / "penalty_touch_work.inp"
    with deck_path.open("x") as stream:
        stream.write(deck)
    expected = analytical_contract(source_pins, observation, sha(deck_path))
    save_new(HERE / "expected.json", expected)
    preflight = self_check(observation)
    preparation = {
        "schema": "calculix_penalty_exact_touch_work_preparation/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NO_FREEZE_OR_NATIVE_EXECUTION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "native_run_performed": False,
        "input_freeze_created": False,
        "baseline_penalty_energy_acceptance": {
            "body_ELSE": baseline_result["energy_audit"]["cases"]["penalty_c3d10"]["body_ELSE"]["status"],
            "CELS": baseline_result["energy_audit"]["cases"]["penalty_c3d10"]["contact_CELS"]["status"],
            "combined": baseline_result["energy_audit"]["cases"]["penalty_c3d10"]["combined_ELSE_plus_CELS"]["status"],
            "MORTAR_reused": False,
        },
        "inherited_mechanical_baseline": mechanical_baseline,
        "inherited_mechanical_tolerances": {
            key: mechanical_expected["analytical_known_answer"]["predeclared_tolerances"][key]
            for key in MECHANICAL_TOLERANCES
        },
        "prefreeze_contract_amendment": {
            "note": "prefreeze-amendment.md",
            "note_sha256": sha(HERE / "prefreeze-amendment.md"),
            "original_prepare_sha256": "4fac64dd4225c1a6f55696ae1996f0ead18a173eb0356352073410a27a551cc6",
            "original_readme_sha256": "01d8745da590e2fd974d2502b16a96a0657f36767ca86ba685df31183f89238d",
            "original_expected_sha256": "4f4d73fd829fcb6d3bf0801dc5b2d1c0d3607c3a361630654cdc5df32df2ab7a",
            "original_preparation_sha256": "35c689dfc748fd5b02e474179b8ef627507915cf17254f94e91196823016f939",
            "input_deck_unchanged_sha256": "fffe98b9992ce22a7f9447d423be2fe9f7cf183066ef3f1d9c50b5a295888a0c",
        },
        "input_sha256": sha(deck_path),
        "expected_sha256": sha(HERE / "expected.json"),
        "lineage": lineage,
        "source_pins": source_pins,
        "pinned_baseline_observation": observation,
        "synthetic_and_analytical_preflight": preflight,
        "parent_review_required_before_freeze": True,
    }
    save_new(HERE / "preparation.json", preparation)
    print(json.dumps({"status": preparation["status"],
                      "input_sha256": preparation["input_sha256"],
                      "expected_sha256": preparation["expected_sha256"],
                      "preparation_sha256": sha(HERE / "preparation.json"),
                      "old_chord_work_N_mm": observation["old_open_to_compression_endpoint_chord_work_N_mm"],
                      "touch_compression_work_N_mm": observation["new_touch_to_compression_endpoint_trapezoid_N_mm"],
                      "stored_energy_N_mm": observation["baseline_compression_energy_N_mm"],
                      "preflight": preflight}, sort_keys=True))


if __name__ == "__main__":
    prepare()
