#!/usr/bin/env python3
"""Produce source-pinned, conditional engagement rows for current bolt stacks.

This producer joins saved axes to saved member intervals and catalog envelopes.
It does not run geometry or mechanics software and does not select hardware.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import struct
import sys
import zipfile
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = HERE / "rawlocal" / "hardware-engagement"

PINS = {
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-axes.csv": "2fb010f1b55757e614d90940bfa2a8400df6ee41ab0f950ffa56d30157150b01",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-families.csv": "1787f56e58169426658f266a834286ff9bf0217c5834925c696baf5ffc381f01",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json": "9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a",
    "docs/wood-joints-mvp/current-hardware-coverage.json": "011dcf33c8a99d5072623db06388ffc0e409c8824be15015e68b454c31e7305d",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/proposal.json": "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-hardware/hardware-inputs.json": "a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7",
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fastener-inputs.json": "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv": "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58",
    "docs/floor-flush-construction-kerf-right/bolt-hardware.csv": "a3081ca72f92271ae21967684c5b7a459619dc0cf5c00ac53e7d8cecd748afd8",
    "docs/wood-joints-mvp/wj24-retained-frame-bolt-audit.md": "05f534b8a616e65fd6be1d3d6533b1e59ad16e43db1059a1d92e1334bbca6ff9",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/all-outer-corner-frame-attempt01/comparison.json": "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/all-outer-corner-frame-attempt01/response.npz": "aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01/model.json": "d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01/row-identities.json": "bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/partial-seat-footprint-attempt02/result.json": "ffba33b640e3ae00e61049664a603cdb6fe27cf7561f0068a735878ed8e3bf1b",
}

# Catalog ranges are dimensions transcribed from the pinned local packet and
# the named item records summarized there. Null catalog ends mean unlisted.
STACKS = {
    "qtr_kl": {
        "diameter_mm": 6.35, "tpi": 20, "grade": "SAE J429 Grade 5",
        "bolt_spec": "ASME B18.2.1 partially threaded hex cap screw",
        "nut": {"part": "K.L. Jack 25CNFH5Z", "grade": "SAE J995 Grade 5", "class_scenario": "2B", "height_mm": [5.3848, 5.7404], "across_flats_mm": [10.8712, 11.1252]},
        "washer": {"part": "K.L. Jack 25NWUS", "material": "Type A Wide low-carbon steel; numeric Fy unlisted", "inside_diameter_mm": [7.7978, 8.3058], "outside_diameter_mm": [18.4658, 19.0246], "thickness_mm": [1.2954, 2.0320]},
        "nut_washer_route": "K.L. Jack 25CNFH5Z + 25NWUS; conditional, not selected",
    },
    "qtr_bd": {
        "diameter_mm": 6.35, "tpi": 20, "grade": "SAE J429 Grade 5",
        "bolt_spec": "ASME B18.2.1 partially threaded hex cap screw",
        "nut": {"part": "Bolt Depot 2569", "grade": "SAE J995 Grade 5", "class_scenario": "2B; catalog internal class and chamfers unlisted", "height_mm": [5.3848, 5.7404], "across_flats_mm": [10.8712, 11.1252]},
        "washer": {"part": "Bolt Depot 2994", "material": "low-carbon USS; numeric Fy unlisted", "inside_diameter_mm": [7.7978, 8.3058], "outside_diameter_mm": [18.4658, 19.0246], "thickness_mm": [1.2954, 2.0320]},
        "nut_washer_route": "Bolt Depot 2569 + 2994; conditional, not selected",
    },
    "five16": {
        "diameter_mm": 7.9375, "tpi": 18, "grade": "SAE J429 Grade 8",
        "bolt_spec": "ASME B18.2.1 partially threaded hex cap screw",
        "nut": {"part": "Bolt Depot 2583", "grade": "SAE J995 Grade 8", "class_scenario": "2B; catalog internal class and chamfers unlisted", "height_mm": [6.5532, 6.9342], "across_flats_mm": [12.4206, 12.7000]},
        "washer": {"part": "Bolt Depot 2995", "material": "low-carbon USS; numeric Fy unlisted", "inside_diameter_mm": [9.3980, 9.9060], "outside_diameter_mm": [22.0472, 22.9870], "thickness_mm": [1.6256, 2.6416]},
        "nut_washer_route": "Bolt Depot 2583 + 2995; conditional, not selected",
    },
    "three8": {
        "diameter_mm": 9.525, "tpi": 16, "grade": "SAE J429 Grade 5",
        "bolt_spec": "ASME B18.2.1 partially threaded hex cap screw",
        "nut": {"part": "Bolt Depot 2571", "grade": "SAE J995 Grade 5", "class_scenario": "2B; catalog internal class and chamfers unlisted", "height_mm": [8.1280, 8.5598], "across_flats_mm": [13.9954, 14.3002]},
        "washer": {"part": "Bolt Depot 15023", "material": "Grade 5 USS label; numeric Fy unlisted", "inside_diameter_mm": [10.9982, 11.5062], "outside_diameter_mm": [25.2222, 26.1620], "thickness_mm": [1.6256, 2.6416]},
        "nut_washer_route": "Bolt Depot 2571 + 15023; conditional, not selected",
    },
    "half": {
        "diameter_mm": 12.7, "tpi": 13, "grade": "SAE J429 Grade 5",
        "bolt_spec": "ASME B18.2.1 partially threaded hex cap screw",
        "nut": {"part": "Bolt Depot 2573", "grade": "SAE J995 Grade 5", "class_scenario": "2B; catalog internal class and chamfers unlisted", "height_mm": [10.8458, 11.3792], "across_flats_mm": [18.6944, 19.0500]},
        "washer": {"part": "Bolt Depot 15025", "material": "Grade 5 USS label; numeric Fy unlisted", "inside_diameter_mm": [13.8938, 14.6558], "outside_diameter_mm": [34.7472, 35.0520], "thickness_mm": [2.1844, 3.3528]},
        "nut_washer_route": "Bolt Depot 2573 + 15025; conditional, not selected",
    },
}

ROUTES = {
    "candidate_ordinary_48": ("qtr_kl", 152.4, None, None, "K.L. Jack 25C600HCS5Z; nominal 6 in; listing thread-length field 19.05 mm does not locate LB or full-form start."),
    "candidate_side_16": ("qtr_kl", 203.2, None, None, "Lawson/FalconGrip FA21103; nominal 8 in; also shared with four top-rail and four inner-knee/header stacks; catalog lacks delivered LB/full-form coordinates."),
    "candidate_top_rail_quarter_8in_4": ("qtr_bd", 203.2, None, None, "Lawson/FalconGrip FA21103 or Motion MI 11706127; nominal 8 in; separate Bolt Depot 2569/2994 stack."),
    "candidate_top_side_5_16_4": ("five16", 203.2, 198.628, 203.2, "Bolt Depot 28650; 5/16-18 x 8 in Grade 8; exact listed length range 198.628–203.2 mm; listed 28.575 mm thread-length field does not locate LB/full-form interval."),
    "candidate_outer_post_4": ("qtr_kl", 101.6, None, None, "K.L. Jack 25C400HCS5Z; nominal 4 in; BrightonBest 847030 historical alternate."),
    "candidate_center_post_4": ("qtr_kl", 152.4, None, None, "HiStrength 104-044 / 25C600HCS5P or K.L. Jack 25C600HCS5Z; proposed 6-in alternative to unsourced 5.75-in class."),
    "candidate_center_principal_4": ("qtr_kl", 139.7, None, None, "K.L. Jack 25C550HCS5Z; nominal 5.5 in; request item-specific LB and full-form profile."),
    "candidate_center_post_header_4": ("qtr_kl", 190.5, None, None, "HiStrength 104-049 / 25C750HCS5P; nominal 7.5 in; product thread-length field is not first full-form thread."),
    "candidate_center_principal_header_4": ("qtr_kl", 203.2, None, None, "HiStrength 7.5-in lead plus proposed Lawson FA21103 8-in alternative; alternative nominal endpoint is 13.183 mm beyond frozen CAD cylinder; geometry fit not accepted."),
    "candidate_knee_inner_header_4": ("qtr_kl", 203.2, None, None, "Lawson/FalconGrip FA21103 8-in alternative; one shared 25-pack route with 12 side and four top-rail axes."),
    "candidate_knee_side_4": ("qtr_kl", 241.3, None, None, "Ro-Brand HC5127 nominal 1/4-20 x 9.5 in Grade 5 coarse; supplier must specify J429/B18.2.1, final 2A, LB, full-form window, package and price."),
    "retained_rail_front_4": ("three8", 101.6, 100.076, 101.6, "Bolt Depot 367; listed 3/8-16 x 4 in Grade 5; listed under-head range 100.076–101.6 mm."),
    "retained_rail_rear_4": ("three8", 114.3, 111.760, 114.3, "Bolt Depot 368; listed 3/8-16 x 4.5 in Grade 5; listed under-head range 111.760–114.3 mm."),
    "retained_lumber_leg_4": ("half", 203.2, 198.628, 203.2, "Bolt Depot 407; listed 1/2-13 x 8 in Grade 5; listed under-head range 198.628–203.2 mm."),
}

RETAINED_MEMBER_LENGTHS = {
    "retained_rail_front_4": [38.1, 38.1],
    "retained_rail_rear_4": [38.1, 50.8],
    "retained_lumber_leg_4": [88.9, 88.9],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source(path_text: str) -> Path:
    path = ROOT / path_text
    expected = PINS[path_text]
    if not path.is_file():
        raise ValueError(f"missing pinned source: {path_text}")
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"source hash mismatch: {path_text}: expected {expected}, got {actual}")
    return path


def read_json(path_text: str) -> dict:
    return json.loads(source(path_text).read_text(encoding="utf-8"))


def read_csv(path_text: str) -> list[dict[str, str]]:
    with source(path_text).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def q(value: float) -> float:
    return round(float(value), 6)


def parse_npy_f64_vector(data: bytes) -> list[float]:
    if data[:6] != b"\x93NUMPY" or data[6:8] != b"\x01\x00":
        raise ValueError("saved response array is not NumPy NPY v1")
    header_len = struct.unpack_from("<H", data, 8)[0]
    header = ast.literal_eval(data[10 : 10 + header_len].decode("latin1").strip())
    if header.get("descr") != "<f8" or header.get("fortran_order") or len(header.get("shape", ())) != 1:
        raise ValueError("saved response array does not match expected little-endian f64 vector")
    size = header["shape"][0]
    offset = 10 + header_len
    if len(data) != offset + size * 8:
        raise ValueError("saved response vector length disagrees with NPY header")
    return list(struct.unpack_from(f"<{size}d", data, offset))


def intervals_from_candidate(axis: dict, grip_axis: dict, washer_delta: float) -> list[dict]:
    members = []
    for rec in grip_axis["wood_receiver_intervals"]:
        spans = rec["intersection_solid_intervals_from_underhead_mm"]
        if len(spans) != 1:
            raise ValueError(f"unsupported multi-span receiver: {axis['axis_id']} / {rec['receiver_id']}")
        a, b = spans[0]
        a, b = q(a + washer_delta), q(b + washer_delta)
        members.append({
            "receiver_id": rec["receiver_id"],
            "underhead_interval_mm": [a, b],
            "axis_material_length_mm": q(rec["receiver_wood_axis_length_mm"]),
            "nds_nominal_D_quarter_thread_LB_min_mm": q(b - (b - a) / 4),
            "interval_basis": "saved grip-screen intersection interval, shifted only for published maximum head-washer delta",
        })
    return members


def retained_intervals(axis: dict, bolt_record: dict, washer_delta: float) -> list[dict]:
    family_id = axis["family_id"]
    lengths = RETAINED_MEMBER_LENGTHS[family_id]
    names = [bolt_record["first_member"], bolt_record["second_member"]]
    if abs(sum(lengths) - float(bolt_record["grip_mm"])) > 1e-6:
        raise ValueError(f"retained member lengths do not sum to recorded grip for {axis['axis_id']}")
    cursor = 2.032 + washer_delta
    members = []
    for name, length in zip(names, lengths):
        a, b = q(cursor), q(cursor + length)
        members.append({
            "receiver_id": name,
            "underhead_interval_mm": [a, b],
            "axis_material_length_mm": length,
            "nds_nominal_D_quarter_thread_LB_min_mm": q(b - length / 4),
            "interval_basis": "retained connection axes first_member/second_member order and audited nominal receiver thickness",
        })
        cursor += length
    return members


def central_response() -> dict:
    comparison_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/all-outer-corner-frame-attempt01/comparison.json"
    response_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/all-outer-corner-frame-attempt01/response.npz"
    model_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01/model.json"
    rows_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01/row-identities.json"
    result_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/partial-seat-footprint-attempt02/result.json"
    comparison = read_json(comparison_path)
    model = read_json(model_path)
    row_ids = json.loads(source(rows_path).read_text(encoding="utf-8"))
    footprint = read_json(result_path)
    if comparison.get("response_sha256") != PINS[response_path]:
        raise ValueError("all-outer comparison does not bind expected response hash")
    if comparison.get("source_sha256", {}).get(model_path) != PINS[model_path]:
        raise ValueError("all-outer comparison does not bind the frozen corner model")
    if comparison.get("source_sha256", {}).get(rows_path) != PINS[rows_path]:
        raise ValueError("all-outer comparison does not bind the current corner row identities")
    if model.get("connector_rows_file") != "row-identities.json":
        raise ValueError("current model does not point to expected row identities file")
    indexed = [r for r in row_ids if r.get("row_id") == "center_principal_right_2/outer-seat-axial-tie"]
    if len(indexed) != 1 or indexed[0].get("row") != 1535 or indexed[0].get("ownership", {}).get("role") != "physical_bolt_outer_seat_tension":
        raise ValueError("current all-outer tie row identity is not uniquely bound at index 1535")
    values = []
    with zipfile.ZipFile(source(response_path)) as archive:
        for state in comparison["states"]:
            base_case = state["case_id"]
            suffix = "zero" if float(state["gap_scale"]) == 0.0 else "gap"
            case_id = f"{base_case}_{suffix}"
            name = f"{case_id}_raw_force_n.npy"
            if name not in archive.namelist():
                raise ValueError(f"all-outer response missing vector {name}")
            vector = parse_npy_f64_vector(archive.read(name))
            if len(vector) != 1888:
                raise ValueError(f"unexpected response vector length for {case_id}")
            value = float(vector[1535])
            values.append({"case_id": case_id, "signed_force_N": value, "absolute_force_N": abs(value)})
    if len(values) != 12:
        raise ValueError("all-outer response must contain 12 saved states")
    peak = max(values, key=lambda row: row["absolute_force_N"])
    fc = float(footprint["conditional_base_Fc_perpendicular_mpa"])
    declared_od, wood_id = footprint["declared_outer_inner_diameters_mm"]
    wood_area = float(footprint["central_area_mm2"])
    washer_ids = [7.7978, 8.3058]
    scenarios = []
    for inside in washer_ids:
        area = math.pi / 4 * (float(declared_od) ** 2 - inside**2)
        pressure = peak["absolute_force_N"] / area
        minimum_outer = math.sqrt(inside**2 + 4 * peak["absolute_force_N"] / (math.pi * fc))
        scenarios.append({
            "hypothetical_uniform_annulus_outer_diameter_mm": declared_od,
            "actual_catalog_washer_ID_endpoint_mm": inside,
            "annular_area_mm2": area,
            "pressure_MPa": pressure,
            "ratio_to_conditional_Fc_perp": pressure / fc,
            "uniform_pressure_min_outer_diameter_at_Fc_mm": minimum_outer,
            "status": "arithmetic sensitivity only; actual washer contact, support transfer, tilt and pressure distribution unproved",
        })
    return {
        "source_response": response_path,
        "source_response_sha256": PINS[response_path],
        "source_comparison": comparison_path,
        "source_comparison_sha256": PINS[comparison_path],
        "source_row_identity_file": rows_path,
        "source_row_identity_sha256": PINS[rows_path],
        "source_model": model_path,
        "source_model_sha256": PINS[model_path],
        "row_index": 1535,
        "row_id": indexed[0]["row_id"],
        "row_role": indexed[0]["ownership"]["role"],
        "axis_id": "center_principal_right_2",
        "receiver_body": "base_principal_center_right",
        "all_outer_state_forces": values,
        "current_absolute_peak_N": peak["absolute_force_N"],
        "peak_case_id": peak["case_id"],
        "geometry_only_saved_ring": {
            "source": result_path,
            "source_sha256": PINS[result_path],
            "outer_diameter_mm": declared_od,
            "wood_bore_inner_diameter_mm": wood_id,
            "area_mm2": wood_area,
            "conditional_Fc_perpendicular_MPa": fc,
            "peak_uniform_mean_pressure_MPa": peak["absolute_force_N"] / wood_area,
            "pressure_over_conditional_Fc": peak["absolute_force_N"] / wood_area / fc,
        },
        "actual_washer_ID_annulus_sensitivities": scenarios,
        "limits": [
            "Saved 10 mm OD / 7.3 mm ID ring is geometric support only; catalog washer ID is 7.7978–8.3058 mm.",
            "Uniform annular pressure is an arithmetic sensitivity, not a contact or capacity result.",
            "No washer bearing, nut-to-washer transfer, metal strength, or complete joint capacity is inferred.",
        ],
    }


def build() -> tuple[dict, list[dict]]:
    for pinned_path in PINS:
        source(pinned_path)
    axes_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-axes.csv"
    families_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-families.csv"
    grip_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json"
    coverage_path = "docs/wood-joints-mvp/current-hardware-coverage.json"
    proposal_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/proposal.json"
    top_hw_path = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-hardware/hardware-inputs.json"
    connection_path = "docs/floor-flush-construction-kerf-right/connection-axes.csv"
    bolt_hardware_path = "docs/floor-flush-construction-kerf-right/bolt-hardware.csv"

    axis_rows = read_csv(axes_path)
    family_rows = read_csv(families_path)
    grip = read_json(grip_path)
    coverage = read_json(coverage_path)
    proposal = read_json(proposal_path)
    top_hw = read_json(top_hw_path)
    fastener_inputs = read_json("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fastener-inputs.json")
    connection_axes = read_csv(connection_path)
    bolt_hardware = read_csv(bolt_hardware_path)

    def inch_range(values: list[float]) -> list[float]:
        return [q(float(value) * 25.4) for value in values]

    quarter_dimensions = fastener_inputs["dimension_inputs"]
    if inch_range(quarter_dimensions["nut"]["height_in"]) != STACKS["qtr_kl"]["nut"]["height_mm"]:
        raise ValueError("quarter nut catalog dimensions differ from pinned fastener input")
    for key, field in (("id_in", "inside_diameter_mm"), ("od_in", "outside_diameter_mm"), ("thickness_in", "thickness_mm")):
        if inch_range(quarter_dimensions["washer"][key]) != STACKS["qtr_kl"]["washer"][field]:
            raise ValueError(f"quarter washer {field} differs from pinned fastener input")

    structural = [r for r in axis_rows if r["fastener_type"] == "structural through-bolt"]
    if len(structural) != 104 or len({r["axis_id"] for r in structural}) != 104:
        raise ValueError("structural axis census is not 104 unique IDs")
    if sum(int(r["bolts"]) for r in structural) != 104 or sum(int(r["nuts"]) for r in structural) != 104 or sum(int(r["separate_washers"]) for r in structural) != 208:
        raise ValueError("structural hardware quantity census failed")
    candidate = [r for r in structural if r["system"] == "candidate"]
    retained = [r for r in structural if r["system"] == "retained"]
    if len(candidate) != 92 or len(retained) != 12:
        raise ValueError("expected 92 candidate and 12 retained axes")
    candidate_coverage_ids = {axis_id for family in coverage["candidate_family_coverage"] for axis_id in family["axis_ids"]}
    retained_coverage_ids = {axis_id for family in coverage["retained_family_coverage"] for axis_id in family["axis_ids"]}
    if {r["axis_id"] for r in candidate} != candidate_coverage_ids or {r["axis_id"] for r in retained} != retained_coverage_ids:
        raise ValueError("reconciled structural axes do not preserve frozen coverage axis census")
    grip_map = {r["axis_id"]: r for r in grip["axes"]}
    if set(grip_map) != {r["axis_id"] for r in candidate}:
        raise ValueError("candidate grip-screen axis set differs from current 92-axis census")

    family_map = {}
    for row in family_rows:
        if (
            row["fastener_type"] == "structural through-bolt" if "fastener_type" in row else int(row.get("bolts", 0)) > 0
        ) and row.get("reconciled_family_id"):
            family_map[row["reconciled_family_id"]] = row
    grouped: dict[str, list[dict[str, str]]] = {}
    for axis in structural:
        grouped.setdefault(axis["family_id"], []).append(axis)
    if set(grouped) != set(family_map) or len(grouped) != 14:
        raise ValueError("expected exactly 14 structural family definitions")

    proposal_axis_ids = {axis["axis_id"] for p in proposal["proposals"] for axis in p["axes"]}
    for p in proposal["proposals"]:
        if p["proposed_section_X_T_mm"] != [88.9, 139.7]:
            raise ValueError(f"unexpected reviewed top-cleat section for {p['block']}")
    top_axis_ids = {r["axis_id"] for r in structural if r["family_id"] in {"candidate_top_rail_quarter_8in_4", "candidate_top_side_5_16_4"}}
    if proposal_axis_ids != top_axis_ids or len(proposal_axis_ids) != 8:
        raise ValueError("top proposal axis IDs do not match eight corrected top structural axes")
    if top_hw.get("catalog_parts", {}).get("side_bolt_grade8", {}).get("item") != "28650":
        raise ValueError("top catalog fit source no longer identifies Bolt Depot 28650")

    bolt_hardware_map = {r["name"]: r for r in bolt_hardware}
    connection_map = {r["name"]: r for r in connection_axes}
    output_axes = []
    for axis in structural:
        fid = axis["family_id"]
        family = family_map[fid]
        stack_id, nominal_order, listed_min, listed_max, route = ROUTES[fid]
        stack = STACKS[stack_id]
        max_head_washer = stack["washer"]["thickness_mm"][1]
        model_head_washer = 2.032
        delta = max_head_washer - model_head_washer
        if axis["system"] == "candidate":
            grip_axis = grip_map[axis["axis_id"]]
            if fid == "candidate_top_rail_quarter_8in_4":
                # Proposal replaces 88.9-mm cleat thickness by 139.7 mm.
                receiver_ids = [r["receiver_id"] for r in grip_axis["wood_receiver_intervals"]]
                if receiver_ids != ["base_rail_top", "top_outer_left_cleat"] and receiver_ids != ["base_rail_top", "top_outer_right_cleat"]:
                    raise ValueError(f"unexpected corrected top-rail receivers: {axis['axis_id']}")
                proposal_row = next(a for p in proposal["proposals"] for a in p["axes"] if a["axis_id"] == axis["axis_id"])
                proposal_block = next(p for p in proposal["proposals"] if any(a["axis_id"] == axis["axis_id"] for a in p["axes"]))
                cleat_depth = float(proposal_block["proposed_section_X_T_mm"][1])
                rail_rec = grip_axis["wood_receiver_intervals"][0]
                rail_span = rail_rec["intersection_solid_intervals_from_underhead_mm"][0]
                rail_start, rail_end = q(rail_span[0]), q(rail_span[1])
                if abs(float(proposal_row["wood_grip_mm"]) - (rail_end - rail_start + cleat_depth)) > 0.02:
                    raise ValueError(f"corrected top-rail grip does not reconcile to proposal: {axis['axis_id']}")
                cleat_end = q(rail_end + cleat_depth)
                members = []
                for receiver_id, a, b, length in ((receiver_ids[0], rail_start, rail_end, rail_end - rail_start), (receiver_ids[1], rail_end, cleat_end, cleat_depth)):
                    members.append({
                        "receiver_id": receiver_id,
                        "underhead_interval_mm": [q(a), q(b)],
                        "axis_material_length_mm": q(length),
                        "nds_nominal_D_quarter_thread_LB_min_mm": q(b - length / 4),
                        "interval_basis": "saved rail interval plus reviewed corrected 4x6 top-cleat proposal",
                    })
            else:
                source_head_role = grip_axis["hardware_roles"]["head_washer"]
                source_interval = source_head_role["projection_envelope_from_underhead_mm"]
                source_head_washer = float(source_interval[1]) - float(source_interval[0])
                axis_washer_delta = max_head_washer - source_head_washer
                members = intervals_from_candidate(axis, grip_axis, axis_washer_delta)
        else:
            bolt_record = bolt_hardware_map.get(axis["axis_id"])
            connection_record = connection_map.get(axis["axis_id"])
            if bolt_record is None or connection_record is None:
                raise ValueError(f"retained axis lacks matching current construction hardware records: {axis['axis_id']}")
            if bolt_record["first_member"] != connection_record["first_member"] or bolt_record["second_member"] != connection_record["second_member"]:
                raise ValueError(f"retained member order differs between hardware and connection axes: {axis['axis_id']}")
            members = retained_intervals(axis, bolt_record, delta)

        members.sort(key=lambda r: (r["underhead_interval_mm"][0], r["underhead_interval_mm"][1]))
        shear_planes = []
        for first, second in pairwise(members):
            left = first["underhead_interval_mm"][1]
            right = second["underhead_interval_mm"][0]
            if abs(left - right) > 0.01:
                raise ValueError(f"unjoined member intervals at shear plane for {axis['axis_id']}: {left}, {right}")
            shear_planes.append({
                "between_receivers": [first["receiver_id"], second["receiver_id"]],
                "underhead_coordinate_mm": q((left + right) / 2),
                "smooth_shank_requirement_LB_mm": q((left + right) / 2),
            })
        required_lb = max(m["nds_nominal_D_quarter_thread_LB_min_mm"] for m in members)
        smooth_req = max((p["smooth_shank_requirement_LB_mm"] for p in shear_planes), default=0.0)
        grip_mm = sum(m["axis_material_length_mm"] for m in members)
        # Retained raw series and candidate proposal raw axis table are frozen
        # and retain model grip independently of the revised receiver list.
        if abs(grip_mm - float(axis["grip_mm"])) > 0.02:
            raise ValueError(f"derived wood grip disagrees with hardware axis row for {axis['axis_id']}: {grip_mm} vs {axis['grip_mm']}")

        nut = stack["nut"]
        washer = stack["washer"]
        earliest = washer["thickness_mm"][0] + grip_mm + washer["thickness_mm"][0]
        latest = washer["thickness_mm"][1] + grip_mm + washer["thickness_mm"][1] + nut["height_mm"][1]
        pitch = 25.4 / stack["tpi"]
        three_pitch = latest + 3 * pitch
        legacy_projection = latest + 3.175
        row = {
            "axis_id": axis["axis_id"],
            "family_id": fid,
            "family_name": family["family"],
            "system": axis["system"],
            "diameter_mm": stack["diameter_mm"],
            "thread": f"{stack['diameter_mm']} mm nominal, UNC RH, {stack['tpi']} TPI; external 2A / internal 2B requested scenario",
            "grade": stack["grade"],
            "model_underhead_length_mm": float(axis["model_length_mm"]),
            "proposed_nominal_order_length_mm": nominal_order,
            "listed_product_length_range_mm": [listed_min, listed_max] if listed_min is not None else None,
            "order_minus_model_length_mm": q(nominal_order - float(axis["model_length_mm"])),
            "wood_grip_mm": q(grip_mm),
            "ordered_members_head_to_nut": [m["receiver_id"] for m in members],
            "member_bearing_intervals": members,
            "shear_planes": shear_planes,
            "required_LB_each_member_max_mm": q(required_lb),
            "smooth_shank_LB_through_all_shear_planes_mm": q(smooth_req),
            "full_form_male_thread_required_interval_mm": [q(earliest), q(latest)],
            "physical_three_pitch_length_min_mm": q(three_pitch),
            "legacy_3_175mm_tip_projection_comparator_mm": q(legacy_projection),
            "nut_washer_route": stack["nut_washer_route"],
            "nut_envelope": nut,
            "washer_envelope": washer,
            "conditional_bolt_route": route,
            "product_profile_guarantees": {
                "catalog_LB_guarantee_mm": None,
                "full_form_male_thread_interval_mm": None,
                "nut_active_thread_and_chamfers_mm": None,
                "washer_numeric_yield_minimum": None,
                "selected": False,
            },
        }
        output_axes.append(row)

    if len(output_axes) != 104 or len({r["axis_id"] for r in output_axes}) != 104:
        raise ValueError("output axis records are not 104 unique structural stacks")

    family_outputs = []
    for fid, rows in sorted(grouped.items()):
        rows_out = [r for r in output_axes if r["family_id"] == fid]
        stack_id, nominal_order, listed_min, listed_max, route = ROUTES[fid]
        lbmax = max(r["required_LB_each_member_max_mm"] for r in rows_out)
        shearmax = max((p["smooth_shank_requirement_LB_mm"] for r in rows_out for p in r["shear_planes"]), default=0.0)
        first = rows_out[0]
        order_counts = {}
        for r in rows_out:
            lengths = tuple(q(m["axis_material_length_mm"]) for m in r["member_bearing_intervals"])
            label = " → ".join(f"{x:g}" for x in lengths)
            order_counts[label] = order_counts.get(label, 0) + 1
        family_outputs.append({
            "family_id": fid,
            "family_name": family_map[fid]["family"],
            "system": family_map[fid]["system"],
            "axis_count": len(rows_out),
            "bolts": len(rows_out), "nuts": len(rows_out), "separate_washers": 2 * len(rows_out),
            "diameter_mm": STACKS[stack_id]["diameter_mm"],
            "pitch_tpi": STACKS[stack_id]["tpi"],
            "grade_scenario": STACKS[stack_id]["grade"],
            "nominal_order_length_mm": nominal_order,
            "catalog_listed_length_range_mm": [listed_min, listed_max] if listed_min is not None else None,
            "model_length_mm": float(rows[0]["model_length_mm"]),
            "order_minus_model_length_mm": q(nominal_order - float(rows[0]["model_length_mm"])),
            "wood_grip_mm": first["wood_grip_mm"],
            "receiver_order_length_counts_mm": order_counts,
            "required_LB_each_member_max_mm": q(lbmax),
            "smooth_shank_LB_through_all_shear_planes_max_mm": q(shearmax),
            "full_form_male_thread_required_interval_mm": first["full_form_male_thread_required_interval_mm"],
            "physical_three_pitch_length_min_mm": first["physical_three_pitch_length_min_mm"],
            "legacy_3_175mm_tip_projection_comparator_mm": first["legacy_3_175mm_tip_projection_comparator_mm"],
            "nut_washer_route": first["nut_washer_route"],
            "conditional_bolt_route": route,
            "item_specific_LB_and_full_form_profile_supported": False,
        })

    hardware = {
        "schema": "conditional_structural_bolt_engagement/v1",
        "prepared_on": "2026-10-02",
        "scope": {
            "candidate_structural_axes": 92,
            "retained_starting_axes": 12,
            "total_bolts": 104,
            "matched_nuts": 104,
            "separate_washers": 208,
            "separate_Hillman_42605_screws": 66,
            "families": 14,
            "hardware_selected": False,
            "capacity_assigned": False,
        },
        "source_pins": [{"path": p, "sha256": PINS[p]} for p in PINS],
        "rules": {
            "coordinate": "under-head bearing face, in mm; receiver intervals include published maximum head-washer thickness",
            "nds_each_member": "LB >= b - (b-a)/4 for each wood bearing interval [a,b]; dimensional screen only",
            "smooth_shank_shear_plane": "LB >= each wood interface coordinate; does not replace each-member threaded-bearing check",
            "full_form_window": "first full-form male thread <= earliest washer/nut bearing face; last full-form male thread >= latest far physical nut face",
            "three_pitch_scenario": "latest physical nut face + three nominal thread pitches; declared fit scenario, not universal rule or full-form engagement proof",
            "legacy_comparator": "latest physical nut face + 3.175 mm; comparison only",
            "catalog_lengths": "listed catalog minimum/range kept separate from modeled CAD length and proposed nominal order class",
        },
        "families": family_outputs,
        "axis_records_csv": "hardware-engagement-axes.csv",
        "central_partial_seat_saved_response": central_response(),
        "limits": [
            "No bolt, nut or washer selected; all routes remain conditional supplier/catalog leads.",
            "Catalog nominal length and listed minimum thread length do not establish delivered LB or full-form thread coordinates.",
            "No capacity, strength, washer yield, metal transfer or complete joint acceptance is inferred.",
            "No geometry, CAD, frame response or native mechanics solve was run by this producer.",
        ],
    }
    return hardware, output_axes


def render(hardware: dict, axes: list[dict]) -> dict[str, bytes]:
    json_bytes = (json.dumps(hardware, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    buffer = io.StringIO(newline="")
    fields = [
        "axis_id", "family_id", "family_name", "system", "diameter_mm", "thread", "grade",
        "model_underhead_length_mm", "proposed_nominal_order_length_mm", "listed_product_length_range_mm",
        "order_minus_model_length_mm", "wood_grip_mm", "ordered_members_head_to_nut",
        "member_bearing_intervals", "shear_planes", "required_LB_each_member_max_mm",
        "smooth_shank_LB_through_all_shear_planes_mm", "full_form_male_thread_required_interval_mm",
        "physical_three_pitch_length_min_mm", "legacy_3_175mm_tip_projection_comparator_mm",
        "nut_washer_route", "conditional_bolt_route", "catalog_LB_guarantee_mm",
        "full_form_male_thread_interval_mm", "selected",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in axes:
        flat = {k: row.get(k) for k in fields if k in row}
        flat["listed_product_length_range_mm"] = json.dumps(row["listed_product_length_range_mm"], separators=(",", ":")) if row["listed_product_length_range_mm"] is not None else ""
        flat["ordered_members_head_to_nut"] = json.dumps(row["ordered_members_head_to_nut"], separators=(",", ":"))
        flat["member_bearing_intervals"] = json.dumps(row["member_bearing_intervals"], separators=(",", ":"), sort_keys=True)
        flat["shear_planes"] = json.dumps(row["shear_planes"], separators=(",", ":"), sort_keys=True)
        flat["full_form_male_thread_required_interval_mm"] = json.dumps(row["full_form_male_thread_required_interval_mm"], separators=(",", ":"))
        flat["catalog_LB_guarantee_mm"] = ""
        flat["full_form_male_thread_interval_mm"] = ""
        flat["selected"] = "false"
        writer.writerow(flat)
    return {"hardware-engagement.json": json_bytes, "hardware-engagement-axes.csv": buffer.getvalue().encode()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write ignored JSON/CSV output")
    group.add_argument("--verify", action="store_true", help="verify output bytes against frozen inputs")
    args = parser.parse_args()
    try:
        hardware, axes = build()
        outputs = render(hardware, axes)
        if args.write:
            OUT.mkdir(parents=True, exist_ok=True)
            for name, data in outputs.items():
                (OUT / name).write_bytes(data)
        else:
            for name, data in outputs.items():
                path = OUT / name
                if not path.is_file():
                    raise ValueError(f"missing generated output: {path.relative_to(ROOT)}; run --write")
                if path.read_bytes() != data:
                    raise ValueError(f"generated output differs: {path.relative_to(ROOT)}; run --write")
        for name, data in outputs.items():
            print(f"{name}: sha256={hashlib.sha256(data).hexdigest()} bytes={len(data)}")
        print(f"verified: families={len(hardware['families'])} axes={len(axes)} bolts=104 nuts=104 washers=208 separate_hillman=66")
        peak = hardware["central_partial_seat_saved_response"]
        print(f"central-seat: row={peak['row_index']} axis={peak['axis_id']} peak={peak['current_absolute_peak_N']:.11f} N case={peak['peak_case_id']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"hardware engagement producer: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
