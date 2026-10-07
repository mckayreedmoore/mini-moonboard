"""Correct panel-method references and adapt cached width-grain panel deltas.

This module only reads authenticated saved artifacts and performs small array
maps or scalar reference calculations. It never assembles a frame, calls a
frame solver, launches a native solver, or changes geometry.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]

BASE_OPERATORS = HERE / "operators-attempt02"
WIDTH_OPERATORS = HERE / "panel-width-operators-attempt01"
JOINT_PREPARATION = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/prepare-attempt03"
ROW_MAP = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json"
NDS_SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf"
APA_LEGACY_SOURCE = HERE / "rawlocal/panel-local-net-completion/source-cache/apa-D510C-2012.pdf"

PINS = {
    BASE_OPERATORS / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    BASE_OPERATORS / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    WIDTH_OPERATORS / "operator-assessment.json": "47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0",
    WIDTH_OPERATORS / "operators.npz": "bf7cfd24800a0c551fa136465d8d92172ec9dd9b619d86d43930ab7f17b87387",
    WIDTH_OPERATORS / "model.json": "fe24dcab49f98b9669a4345ff41ea9a566fc95ede07c68ed31745b681768b40f",
    JOINT_PREPARATION / "joint-operators.npz": "10d3e0ca12e6ed3b98280ee343391f7eb4e02996e6dc837e699c6b2a317fbb4b",
    ROW_MAP: "f9ae9865e80ea95db9dccd6e6cd484ce60c6bb3aa6f617ec4387e346c55a5b8d",
    NDS_SOURCE: "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    APA_LEGACY_SOURCE: "6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca",
}

# The current catalog and indexed APA-authored Table 10 were inspected online.
# The 2020 PDF bytes were not obtained; other values retain their frozen 2012
# source rather than being represented as a verified 2020 table match.
APA_D510F = {
    "document": "APA Panel Design Specification, Form D510F",
    "revision": "2020-09-01",
    "official_catalog_url": "https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/",
    "publication_pdf_url": "https://wood.tcaup.umich.edu/lectures/2021/D510.pdf",
    "table_10_page": 29,
    "verification_scope": "Current catalog and web-indexed Table 10; 2020 PDF binary not retrieved or SHA-pinned",
    "group_1_23_32_in_AA_AC_planar_shear_lbf_per_ft": {
        "parallel_to_strength_axis": 350.0,
        "perpendicular_to_strength_axis": 350.0,
    },
    "group_1_23_32_in_marine_planar_shear_lbf_per_ft": {
        "parallel_to_strength_axis": 455.0,
        "perpendicular_to_strength_axis": 455.0,
    },
    "group_1_23_32_in_other_planar_shear_lbf_per_ft": {
        "parallel_to_strength_axis": 350.0,
        "perpendicular_to_strength_axis": 350.0,
    },
    "limits": [
        "D510F Table 10 is a conditional Group 1 / sanded / 23/32-in table fit; the purchased sheet mark and layup are not observed.",
        "Table 10 Fs(Ib/Q) is in-plane interlaminar/rolling shear (ASTM D2718), not a screw-head punching or edge-out resistance.",
        "Table 10 Fv tv is through-thickness shear (ASTM D2719), a different mode.",
    ],
}

APA_D510C = {
    "document": "APA Panel Design Specification, Form D510C (2012)",
    "local_source": str(APA_LEGACY_SOURCE.relative_to(ROOT)),
    "sha256": PINS[APA_LEGACY_SOURCE],
    "publication_pdf_url": "https://design.medeek.com/resources/structural/D510C_2012.pdf",
    "table_12_page": 27,
    "table_12_23_32_in_Ib_over_Q_in2_per_ft": 5.75,
    "face_bearing_section": "4.4.7",
    "face_bearing_psi_at_0_04_in_deformation": 360.0,
    "face_bearing_psi_at_0_02_in_deformation": 210.0,
    "verification_scope": "Frozen source PDF and online text; current-edition Table 13 and face-bearing text not independently verified",
}

NDS_2024 = {
    "document": "ANSI/AWC NDS-2024 with Commentary, Chapter 12",
    "local_source": str(NDS_SOURCE.relative_to(ROOT)),
    "sha256": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    "official_edition_url": "https://awc.org/resources/2024-nds/",
    "sections": ["12.1.5.3", "12.1.5.7", "C12.1.5.7", "12.2.5"],
    "wood_screw_detail_rule": "NDS 12.1.5.7 requires edge distances, end distances, and spacings sufficient to prevent splitting; it gives no numeric placement rule for this #10 (<1/4-in) screw.",
    "commentary_scope": "NDS Commentary C12.1.5.7 provides recommendations for sub-1/4-in screws; these are not bolt-table requirements or screw capacities.",
    "prebored_wood_side_member_recommendation_multipliers_D": {
        "edge": 2.5,
        "end_tension_parallel": 10.0,
        "end_compression_parallel": 5.0,
        "row_spacing_parallel": 10.0,
        "row_spacing_perpendicular": 5.0,
        "in_line_row_spacing": 3.0,
        "staggered_row_spacing": 2.5,
    },
}

N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
CAT_23_32_MM = 23.0 / 32.0 * MM_PER_IN
OWNER_REPORTED_3_4IN_MM = 19.05
LBF_PER_FT_TO_N_PER_MM = N_PER_LBF / (12.0 * MM_PER_IN)
PSI_TO_MPA = 0.006894757293168
PANEL_SCREW_ROLES = {
    "panel_screw_lateral_plane",
    "non_qualifying_parametric_screw_withdrawal",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_pins() -> None:
    for path, expected in PINS.items():
        require(path.is_file(), f"missing pinned source: {path}")
        require(sha256(path) == expected, f"source hash differs: {path}")


def _cached_orientation_delta() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read the cached strong-X minus slope H/e change, with source checks."""
    _check_pins()
    assessment = json.loads((WIDTH_OPERATORS / "operator-assessment.json").read_text())
    require(assessment.get("status") == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
            "cached width-grain packet is not a completed operator comparison")
    require(assessment.get("native_launch") is False,
            "cached orientation packet has an unexpected native launch flag")
    require(assessment.get("output_sha256", {}).get("operators.npz") == PINS[WIDTH_OPERATORS / "operators.npz"],
            "cached width-grain output is not receipt-bound")
    require(assessment.get("source_sha256", {}).get(
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02/operators.npz"
    ) == PINS[BASE_OPERATORS / "operators.npz"], "cached baseline operators differ")
    width_model = json.loads((WIDTH_OPERATORS / "model.json").read_text())
    orientation = width_model.get("panel_orientation_comparison", {})
    require(orientation.get("main_face_grain_global_xyz") == [1.0, 0.0, 0.0]
            and orientation.get("physical_geometry_changed_by_this_comparison") is False,
            "cached width-grain model is not the unchanged strong-X orientation")
    with np.load(BASE_OPERATORS / "operators.npz", allow_pickle=False) as base, \
            np.load(WIDTH_OPERATORS / "operators.npz", allow_pickle=False) as width:
        require(set(base.files) == set(width.files) == {"H", "D", "e", "W", "F"},
                "orientation operator array inventory differs")
        require(base["H"].shape == width["H"].shape == (1888, 1888)
                and base["e"].shape == width["e"].shape == (1888, 12),
                "orientation operator basis dimensions differ")
        for key in ("D", "W", "F"):
            require(np.array_equal(base[key], width[key]),
                    f"orientation comparison unexpectedly changed {key}")
        d_h = width["H"].copy() - base["H"].copy()
        d_e = width["e"].copy() - base["e"].copy()
        h_slope = base["H"].copy()
        e_slope = base["e"].copy()
    return d_h, d_e, h_slope, e_slope


def _kept_projection(d_h_raw: np.ndarray, d_e_raw: np.ndarray) -> tuple[np.ndarray, list[int], dict[str, Any]]:
    """Build P[kept, raw] from the authenticated canonical source-row map."""
    mapping = json.loads(ROW_MAP.read_text())
    joint_path = JOINT_PREPARATION / "joint-operators.npz"
    with np.load(joint_path, allow_pickle=False) as joint:
        kept_lumped_rows = joint["old_kept_lumped_rows"].astype(int).tolist()
        unilateral = joint["unilateral"].astype(bool)
    entries = mapping.get("kept_map", [])
    n_kept, n_raw = len(kept_lumped_rows), 1888
    require(n_kept == 1592 and len(entries) == n_kept,
            "current old-kept/raw map census differs")
    require(mapping.get("old_kept_lumped_rows") == kept_lumped_rows,
            "row-map kept order differs from current joint preparation")
    P = np.zeros((n_kept, n_raw), dtype=float)
    seen_positions: set[int] = set()
    raw_usage = np.zeros(n_raw, dtype=np.int8)
    for entry in entries:
        position = int(entry["kept_position"])
        raw_rows = [int(x) for x in entry["raw_rows"]]
        weights = np.asarray(entry["weights"], dtype=float)
        require(position not in seen_positions and 0 <= position < n_kept,
                "duplicate/out-of-range kept row in source map")
        require(len(raw_rows) == len(weights) and raw_rows
                and min(raw_rows) >= 0 and max(raw_rows) < n_raw,
                "invalid canonical raw-row group")
        require(abs(float(weights.sum()) - 1.0) < 1e-10,
                "source lumping weights do not preserve a rigid translation")
        require(np.all(raw_usage[raw_rows] == 0),
                "a canonical raw row is assigned to multiple kept rows")
        P[position, raw_rows] = weights
        raw_usage[raw_rows] = 1
        seen_positions.add(position)
        require(int(entry["lumped_row"]) == kept_lumped_rows[position],
                "source map lumped-row label/order differs")
    require(seen_positions == set(range(n_kept)), "source map misses kept positions")

    rows = json.loads((BASE_OPERATORS / "row-identities.json").read_text())
    require(len(rows) == n_raw, "canonical operator row inventory differs")
    require(all(int(row["row"]) == i for i, row in enumerate(rows)),
            "canonical raw-row identities are not in operator array order")
    raw_to_kept: dict[int, int] = {}
    for pos, raw in enumerate(raw_usage):
        if raw:
            raw_to_kept[int(pos)] = int(np.flatnonzero(P[:, int(pos)])[0])
    panel_raw = [i for i, row in enumerate(rows)
                 if row["ownership"]["role"] in PANEL_SCREW_ROLES]
    require(len(panel_raw) == 198, "panel screw scalar-row census differs")
    require(all(i in raw_to_kept for i in panel_raw),
            "one or more panel screw rows were lost from old-kept map")
    panel_ports = [raw_to_kept[i] for i in panel_raw]
    require(len(set(panel_ports)) == 198 and max(panel_ports) < n_kept,
            "panel screw ports are not 198 distinct old-kept rows")
    active_raw = set(np.flatnonzero(np.any(np.abs(d_h_raw) > 1e-12, axis=0)))
    active_raw.update(np.flatnonzero(np.any(np.abs(d_h_raw) > 1e-12, axis=1)))
    active_raw.update(np.flatnonzero(np.any(np.abs(d_e_raw) > 1e-12, axis=1)))
    require(active_raw and active_raw.issubset(raw_to_kept),
            "one or more changed panel/contact rows are absent from the current old-kept map")
    active_roles: dict[str, int] = defaultdict(int)
    for raw in active_raw:
        active_roles[str(rows[int(raw)]["ownership"]["role"])] += 1
    require(len(unilateral) == 3192 and sum(bool(unilateral[i]) for i in panel_ports) == 66,
            "current appended ports/profile joint map differs at panel screw rows")
    return P, kept_lumped_rows, {
        "canonical_raw_row_count": n_raw,
        "old_kept_lumped_row_count": n_kept,
        "panel_screw_scalar_rows": len(panel_raw),
        "panel_screw_unilateral_axis_count": 66,
        "panel_screw_ports_all_old_kept": True,
        "orientation_delta_active_raw_rows": len(active_raw),
        "orientation_delta_active_rows_by_role": dict(sorted(active_roles.items())),
        "orientation_delta_active_rows_all_mapped": True,
        "new_continuous_ports_untouched": 1600,
        "source_row_map_sha256": PINS[ROW_MAP],
        "joint_preparation_sha256": PINS[joint_path],
        "projection_nonzeros": int(np.count_nonzero(P)),
    }


def apply_cached_strong_x_delta(
    H_current: np.ndarray,
    e_current: np.ndarray,
    old_kept_lumped_rows: list[int] | np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Add only the cached main-panel strong-X delta to current 3192 H/e.

    This is a pure array adapter. `P` maps the old 1888 canonical raw rows to
    the 1592 current kept/lumped rows. The current 1600 appended shaft/contact
    rows and any current joint-law/profile update remain byte-for-byte intact.
    """
    d_h_raw, d_e_raw, _h_slope, _e_slope = _cached_orientation_delta()
    P, kept, row_audit = _kept_projection(d_h_raw, d_e_raw)
    if old_kept_lumped_rows is not None:
        supplied = np.asarray(old_kept_lumped_rows, dtype=int).tolist()
        require(supplied == kept, "caller current old-kept order differs from authenticated source map")
    H_current = np.asarray(H_current, dtype=float)
    e_current = np.asarray(e_current, dtype=float)
    require(H_current.shape == (3192, 3192) and e_current.shape == (3192, 12),
            "current profile H/e dimensions differ")
    require(np.isfinite(H_current).all() and np.isfinite(e_current).all(),
            "current profile H/e contains nonfinite values")
    d_h_kept = P @ d_h_raw @ P.T
    d_e_kept = P @ d_e_raw
    reciprocity = float(np.linalg.norm(d_h_kept - d_h_kept.T, ord=np.inf)
                        / max(1.0, np.linalg.norm(d_h_kept, ord=np.inf)))
    require(reciprocity <= 1e-8, "projected orientation delta lost H symmetry")
    H_oriented, e_oriented = H_current.copy(), e_current.copy()
    n_old = len(kept)
    H_oriented[:n_old, :n_old] += d_h_kept
    e_oriented[:n_old, :] += d_e_kept
    require(np.array_equal(H_oriented[n_old:, :], H_current[n_old:, :])
            and np.array_equal(H_oriented[:, n_old:], H_current[:, n_old:])
            and np.array_equal(e_oriented[n_old:, :], e_current[n_old:, :]),
            "orientation adapter modified appended shaft/contact rows")
    audit = {
        "schema": "cached_panel_orientation_delta_on_current_joint_ports/v1",
        "status": "READY_ARRAY_ADAPTER_NO_FRAME_SOLVE",
        "orientation": "owner-reported horizontal 8-ft sheet direction; conditional strong-X grain along global X",
        "cached_width_grain_operator_sha256": PINS[WIDTH_OPERATORS / "operators.npz"],
        "cached_width_grain_assessment_sha256": PINS[WIDTH_OPERATORS / "operator-assessment.json"],
        "cached_slope_operator_sha256": PINS[BASE_OPERATORS / "operators.npz"],
        "source_identity": row_audit,
        "projected_delta": {
            "H_inf_norm": float(np.linalg.norm(d_h_kept, ord=np.inf)),
            "H_max_abs": float(np.max(np.abs(d_h_kept), initial=0.0)),
            "e_inf_norm": float(np.linalg.norm(d_e_kept, ord=np.inf)),
            "H_relative_reciprocity_error": reciprocity,
            "applied_H_rows": [0, n_old - 1],
            "applied_e_rows": [0, n_old - 1],
            "D_W_and_appended_rows_changed": False,
        },
        "limits": [
            "Reuse is limited to unchanged four-main-panel geometry, 66 panel screw axes, and matching original 1888 canonical port basis.",
            "Kicker material axes stay unchanged; the current panel thickness remains the parent model's nominal source thickness.",
            "This returns operators only; parent owns the serialized current-profile response and full physics audit.",
        ],
        "frame_solve_executed": False,
        "native_launch": False,
        "geometry_changed": False,
    }
    return H_oriented, e_oriented, audit


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    require(rows and all(isinstance(row, dict) for row in rows), f"empty/invalid JSONL: {path}")
    return rows


def _nds_head_reference(g: float, diameter_mm: float, thickness_mm: float) -> float:
    """NDS 2024 §12.2.5 generic circular screw-head reference, in N."""
    require(g > 0 and thickness_mm > 0 and 0 < diameter_mm <= 0.5 * MM_PER_IN,
            "head-reference inputs exceed the documented generic equation domain")
    diameter_in, thickness_in = diameter_mm / MM_PER_IN, thickness_mm / MM_PER_IN
    head_lbf = (690.0 * math.pi * diameter_in * thickness_in
                if thickness_in <= 2.5 * diameter_in
                else 1725.0 * math.pi * diameter_in**2)
    return head_lbf * g**2 * N_PER_LBF


def _row_scope(row: dict[str, Any]) -> str:
    """Use the source scope when present; otherwise infer it without mutation."""
    if row.get("scope"):
        return str(row["scope"])
    case = row.get("case_id")
    gap = row.get("gap_scale")
    require(isinstance(case, str) and gap is not None,
            "saved force row lacks scope and case_id/gap_scale")
    require(case in {"a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear", "dead-only"},
            "saved force row has an unrecognized accepted case_id")
    gap = float(gap)
    require(gap in (0.0, 1.0), "saved force row has an unrecognized accepted gap_scale")
    return ("permanent" if case == "dead-only" else "live") + ("/zero" if gap == 0.0 else "/nominal")


def _scope_peaks(rows: list[dict[str, Any]], *, g: float,
                 diameter_mm: float, thickness_scenarios: dict[str, float]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        require("tension_n" in row and "lateral_n" in row,
                "saved screw-state schema lacks force/scope fields")
        grouped[_row_scope(row)].append(row)
    out: dict[str, Any] = {}
    for scope, values in sorted(grouped.items()):
        max_t = max(values, key=lambda r: float(r["tension_n"]))
        max_v = max(values, key=lambda r: float(r["lateral_n"]))
        references = {}
        duration_factors=(0.9,) if scope.startswith("permanent/") else (1.0,1.25,1.6)
        for thickness_name, thickness in thickness_scenarios.items():
            base = _nds_head_reference(g, diameter_mm, thickness)
            references[thickness_name] = {
                "net_thickness_mm": thickness,
                "unadjusted_reference_n": base,
                "duration_references_n": {
                    str(cd): base * cd for cd in duration_factors
                },
                "peak_tension_ratios": {
                    str(cd): float(max_t["tension_n"]) / (base * cd)
                    for cd in duration_factors
                },
            }
        out[scope] = {
            "state_count": len(values),
            "peak_tension_n": float(max_t["tension_n"]),
            "peak_tension_witness": {key: max_t.get(key) for key in ("state_id", "case_id", "gap_scale", "panel", "axis_id")},
            "simultaneous_lateral_at_peak_tension_n": float(max_t["lateral_n"]),
            "peak_lateral_n": float(max_v["lateral_n"]),
            "peak_lateral_witness": {key: max_v.get(key) for key in ("state_id", "case_id", "gap_scale", "panel", "axis_id")},
            f"G_{g:.2f}_NDS_head_sensitivities".replace(".", "_"): references,
        }
    return out


def _panel_cut_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompare saved gross-mean cut shear with the current D510F Table 10."""
    cd1_ref = 350.0 * LBF_PER_FT_TO_N_PER_MM
    applicable = [row for row in rows
                  if row.get("applicable_as_gross_mean_component_diagnostic") is True]
    require(applicable, "no explicitly applicable gross panel-cut rows")
    for row in applicable:
        require(float(row.get("CD", -1)) == 1.0,
                "panel-cut action file is not the expected CD=1.0 current-profile basis")
    worst = max(applicable,
                key=lambda row: abs(float(row["demands"]["transverse_shear_mean_n_per_mm"])) / cd1_ref)
    ratios = [abs(float(row["demands"]["transverse_shear_mean_n_per_mm"])) / cd1_ref
              for row in applicable]
    max_demand = abs(float(worst["demands"]["transverse_shear_mean_n_per_mm"]))
    ib_over_q_mm = APA_D510C["table_12_23_32_in_Ib_over_Q_in2_per_ft"] * MM_PER_IN**2 / (12.0 * MM_PER_IN)
    ref_equivalent_mpa = cd1_ref / ib_over_q_mm
    return {
        "source_cut_rows": len(rows),
        "gross_mean_diagnostic_rows": len(applicable),
        "D510F_2020_table_10_Group1_23_32_AA_AC_Fs_lbf_per_ft": 350.0,
        "D510F_2020_table_10_Group1_23_32_AA_AC_Fs_n_per_mm": cd1_ref,
        "D510C_2012_table_12_23_32_Ib_over_Q_in2_per_ft": APA_D510C["table_12_23_32_in_Ib_over_Q_in2_per_ft"],
        "legacy_table_12_derived_Ib_over_Q_mm": ib_over_q_mm,
        "derived_equivalent_reference_stress_mpa": ref_equivalent_mpa,
        "maximum_saved_gross_mean_shear_ratio_at_CD1": max(ratios),
        "maximum_witness": {key: worst.get(key) for key in ("state_id", "case_id", "panel", "cut_axis", "side", "family", "station_from_panel_datum_mm")},
        "maximum_demand_n_per_mm": max_demand,
        "maximum_demand_equivalent_stress_mpa_from_Ib_over_Q": max_demand / ib_over_q_mm,
        "maximum_demand_equivalent_stress_ratio_to_D510F_Fs": (max_demand / ib_over_q_mm) / ref_equivalent_mpa,
        "limits": [
            "This is the saved gross-width mean-component comparison only; it is not the local net-section peak ratio.",
            "The selected 23/32-in Group 1 A-C table fit is conditional; the owner also reports 3/4 in, retained separately as panel geometry.",
            "No Table 10 shear value is assigned as local head-punching or two-ray edge-out resistance.",
        ],
    }


def correct_panel_sources(
    screw_states_path: str | Path,
    panel_cut_actions_path: str | Path,
    *,
    source_binding: dict[str, Any],
    orientation: str,
    head_diameter_mm: float = 9.0,
    panel_thickness_mm: float = CAT_23_32_MM,
    assumed_seat_depth_mm: float = 3.0,
    expected_screws_per_state: int = 66,
    expected_state_count: int = 12,
    panel_head_esg: float = 0.42,
) -> dict[str, Any]:
    """Recalculate bounded panel references from two receipt-bound JSONL files.

    `source_binding` must contain `orientation`, `force_profile_id`,
    `action_receipt_sha256`, `screw_states_sha256`, and
    `panel_cut_actions_sha256`. The force rows are used as saved; this function
    does not rescale or regenerate them.
    """
    screw_states_path, panel_cut_actions_path = Path(screw_states_path), Path(panel_cut_actions_path)
    require(orientation in {"horizontal_strong_x", "board_slope_strong_t"},
            "orientation label must be horizontal_strong_x or board_slope_strong_t")
    require(panel_head_esg in (0.42, 0.50), "unsupported plywood head-pull-through ESG")
    require(source_binding.get("orientation") == orientation,
            "source binding orientation differs from requested branch")
    for key in ("force_profile_id", "action_receipt_sha256", "screw_states_sha256", "panel_cut_actions_sha256"):
        require(isinstance(source_binding.get(key), str) and source_binding[key],
                f"missing required source binding: {key}")
    screw_sha, cuts_sha = sha256(screw_states_path), sha256(panel_cut_actions_path)
    require(screw_sha == source_binding["screw_states_sha256"], "screw-states JSONL hash does not match binding")
    require(cuts_sha == source_binding["panel_cut_actions_sha256"], "panel-cut-actions JSONL hash does not match binding")
    screw_rows, cut_rows = _read_jsonl(screw_states_path), _read_jsonl(panel_cut_actions_path)
    identities = [(row.get("state_id"), row.get("axis_id")) for row in screw_rows]
    require(len(set(identities)) == len(identities), "duplicate screw-state/axis rows")
    by_state: dict[str, int] = defaultdict(int)
    state_axes: dict[str, set[str]] = defaultdict(set)
    for state_id, _axis in identities:
        require(isinstance(state_id, str), "screw state missing state_id")
        by_state[state_id] += 1
        state_axes[state_id].add(_axis)
    require(expected_screws_per_state in (66, 98), "unsupported owner-authorized screw inventory")
    require(1 <= expected_state_count <= 14, "unsupported declared accepted-state inventory")
    require(all(count == expected_screws_per_state for count in by_state.values())
            and len(by_state) == expected_state_count,
            "screw inventory differs from declared accepted-state count")
    require(all(axes == next(iter(state_axes.values())) for axes in state_axes.values()),
            "screw-axis inventory changes between accepted states")
    thickness_scenarios = {
        "CAT_23_32_primary_assumed_3mm_flush_head": panel_thickness_mm - assumed_seat_depth_mm / 3.0,
        "CAT_23_32_primary_no_seat": panel_thickness_mm,
        "owner_report_19_05mm_assumed_3mm_flush_head": OWNER_REPORTED_3_4IN_MM - assumed_seat_depth_mm / 3.0,
        "owner_report_19_05mm_no_seat": OWNER_REPORTED_3_4IN_MM,
    }
    require(all(value > 0 for value in thickness_scenarios.values()),
            "head-seat sensitivity leaves nonpositive net thickness")
    peak_saved_axial = max(screw_rows, key=lambda row: float(row["tension_n"]))
    max_saved_tension = float(peak_saved_axial["tension_n"])
    max_live_tension = max(float(row["tension_n"]) for row in screw_rows
                           if _row_scope(row).startswith("live/"))
    face_bearing_mpa = 360.0 * PSI_TO_MPA
    pressure = {}
    for bore_name, bore in (("retained_7mm_analysis_cavity_not_a_drill_size", 7.0),
                            ("nominal_10_shaft_4_826mm_envelope_sensitivity", 4.826)):
        area = math.pi * (head_diameter_mm**2 - bore**2) / 4.0
        pressure[bore_name] = {
            "projected_annulus_area_mm2": area,
            "maximum_saved_axial_demand_all_states_n": max_saved_tension,
            "maximum_saved_axial_witness": {key: peak_saved_axial.get(key) for key in ("state_id", "case_id", "gap_scale", "panel", "axis_id")},
            "uniform_projected_pressure_mpa": max_saved_tension / area,
            "ratio_to_frozen_APA_360psi_deformation_reference": max_saved_tension / area / face_bearing_mpa,
            "maximum_saved_live_axial_demand_n": max_live_tension,
        }
    nds_detail = dict(NDS_2024)
    D_mm = 0.190 * MM_PER_IN
    nds_detail["D_mm_used_for_commentary_recommendations"] = D_mm
    nds_detail["recommendation_distances_mm_if_prebored_wood_side_member"] = {
        key: multiplier * D_mm
        for key, multiplier in NDS_2024["prebored_wood_side_member_recommendation_multipliers_D"].items()
    }
    return {
        "schema": "panel_method_correction/v1",
        "orientation": orientation,
        "source_binding": dict(source_binding),
        "sources": {
            "screw_states": {"path": str(screw_states_path), "sha256": screw_sha, "rows": len(screw_rows)},
            "panel_cut_actions": {"path": str(panel_cut_actions_path), "sha256": cuts_sha, "rows": len(cut_rows)},
            "NDS_2024": nds_detail,
            "APA_D510F_2020": APA_D510F,
            "APA_D510C_2012_retained_reference": APA_D510C,
        },
        "saved_force_summary": {
            "accepted_states": len(by_state),
            "screws_per_state": expected_screws_per_state,
            "G": panel_head_esg,
            "G_interpretation": "Head-pull-through equivalent specific gravity, not screw withdrawal ESG or density.",
            "head_diameter_mm_owner_report": head_diameter_mm,
            "panel_thickness_mm_primary_nominal_23_32_category_assumption": panel_thickness_mm,
            "panel_thickness_mm_owner_reported_3_4in_sensitivity": OWNER_REPORTED_3_4IN_MM,
            "head_height_or_finished_seat_depth_mm": assumed_seat_depth_mm,
            "head_height_or_seat_depth_status": "unmeasured_explicit_sensitivity_assumption",
            "flush_countersunk_net_thickness_convention": "Panel thickness minus one third of head depth (AWC head pull-through study, p.2); a deep counterbore would require its full depth to be deducted.",
            "scope_results": _scope_peaks(screw_rows, g=panel_head_esg,
                                          diameter_mm=head_diameter_mm,
                                          thickness_scenarios=thickness_scenarios),
        },
        "shop_bore_instructions": {
            "lead_pilot_mm": 3.175,
            "lead_pilot_extent": "through plywood into receiver",
            "face_countersink_tool_diameter_mm": 9.525,
            "tool_diameter_is_finished_cavity": False,
            "tool_diameter_is_installed_head_contact_diameter": False,
            "retained_analysis_cavity_mm": 7.0,
            "nominal_10_shaft_diameter_mm": 4.826,
            "geometry_changed": False,
            "source": "current shop addendum/checklist; face countersink depth/profile and finished cavity remain unmeasured",
        },
        "face_pressure_sensitivity": {
            "reference_mpa": face_bearing_mpa,
            "reference_interpretation": "Frozen D510C 2012 §4.4.7, 360 psi at 0.04-in deformation; deformation reference only, not rupture capacity. Current-edition text not independently verified.",
            "calculated_bore_branches_are_analysis_sensitivities": True,
            "thread_displacement_and_finished_countersink_profile_unmeasured": True,
            "branches": pressure,
        },
        "APA_D510F_current_table_recomparison": _panel_cut_summary(cut_rows),
        "unsupported_local_resistances": {
            "head_punching": {"status": "NO_SUPPORTED_INDEPENDENT_CAPACITY", "retained": "Demand/local field diagnostics may be retained; APA rolling shear is not a screw-head punching resistance."},
            "two_ray_edge_out": {"status": "NO_SUPPORTED_INDEPENDENT_CAPACITY", "retained": "Saved signed load and edge/void ligament geometry are descriptive; the two-ray sum is not a supported block-shear or screw edge-out capacity."},
        },
        "acceptance": {
            "Hillman_product_capacity_assigned": False,
            "panel_or_joint_acceptance": False,
            "physical_release": False,
            "frame_or_native_solve_executed": False,
            "geometry_changed": False,
        },
    }
