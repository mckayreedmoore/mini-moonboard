"""Authenticate complete common-shaft exports before the frozen body audit.

The issued shaft producer exports the full own-end geometry dictionary. The
earlier audit fixture used its end label. This adapter checks the complete
dictionary against frozen source geometry, then presents only that label to
the unchanged arithmetic audit. No force, datum or state identity is changed.
"""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft_audit as frozen

FROZEN_AUDIT_SHA = "a236900e59a3d5984598df56d4243408ce12801d4ab6fcc7f765f6a420de01ba"
PANEL_PRODUCER_SHA = "472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa"
ACCEPTANCE_KEY = "independent_common_shaft_support_load_and_equilibrium_checks_pass"


def normalized_capture_state(demand: dict, shafts: list[dict]) -> dict:
    """Validate the actual full export; adapt only the already checked label."""
    expected = {(shaft["axis_id"], end["end"]): end
                for shaft in shafts for end in shaft["ends"]}
    adapted = copy.deepcopy(demand)
    used = set()
    for row in adapted["shaft_end_capture_actions"]:
        end = row.get("end")
        if not isinstance(end, dict):
            raise TypeError("complete authenticated shaft end geometry export required")
        key = (row["axis_id"], end.get("end"))
        if key in used or key not in expected or end != expected[key]:
            raise ValueError("shaft end geometry differs from its own source-bound washer support")
        used.add(key)
        row["end"] = end["end"]
    if used != set(expected):
        raise ValueError("all unique own-end geometry exports required")
    return adapted


def verify_panel_screw_datums(demand: dict, layout: dict) -> None:
    """Authenticate the unchanged common midplane point and zero free couple."""
    from scripts.thin_bolted_panel_mechanics import CAT

    axes = {row["axis_id"]: row for row in layout["screw_axes"]}
    for row in demand["panel_screw_actions"]:
        source = axes[row["axis_id"]]
        inward = frozen.arithmetic.vector(source["direction_xyz"])
        inward /= np.linalg.norm(inward)
        point = frozen.arithmetic.vector(source["origin_xyz_mm"]) + CAT / 2. * inward
        if np.linalg.norm(frozen.arithmetic.vector(row["point_xyz_mm"]) - point) > 1e-5:
            raise ValueError("panel screw action differs from its source-bound common midplane datum")
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm",
                    "moment_on_second_at_point_xyz_nmm"):
            if key in row and np.linalg.norm(frozen.arithmetic.vector(row[key])) > 1e-7:
                raise ValueError("current panel screw point law supplies no free couple")
        if "host_support_point_xyz_mm" in row and np.linalg.norm(
                frozen.arithmetic.vector(row["host_support_point_xyz_mm"]) - point) > 1e-5:
            raise ValueError("panel screw paired body datums differ")


def audit_common_shaft_state(demand: dict) -> dict:
    """Reuse the frozen 132-body audit after exact export-geometry checks."""
    audit_path = Path(frozen.__file__)
    panel_path = frozen.ROOT / "scripts/thin_bolted_panel_mechanics.py"
    if (frozen.support.digest(audit_path) != FROZEN_AUDIT_SHA
            or frozen.support.digest(panel_path) != PANEL_PRODUCER_SHA):
        raise ValueError("preserve frozen common-shaft arithmetic and panel datum producers")
    from scripts.thin_bolted_common_shaft import shaft_inputs

    _, cache, unit, layout, _, _, _ = frozen.read_sources()
    adapted = normalized_capture_state(demand, shaft_inputs(layout, unit, cache))
    verify_panel_screw_datums(demand, layout)
    result = frozen.audit_common_shaft_state(adapted)
    result["complete_end_geometry_export_checks_pass"] = True
    result["panel_screw_midplane_datum_checks_pass"] = True
    result["frozen_arithmetic_end_label_adapter"] = {
        "only_complete_authenticated_end_dictionary_replaced_by_its_label": True,
        "input_actions_forces_datums_and_state_identity_unchanged": True,
        "frozen_helper_bytes_preserved": True,
    }
    result["source_sha256"].update({
        str(audit_path.relative_to(frozen.ROOT)): FROZEN_AUDIT_SHA,
        str(panel_path.relative_to(frozen.ROOT)): PANEL_PRODUCER_SHA,
        str(Path(__file__).relative_to(frozen.ROOT)): frozen.support.digest(Path(__file__)),
    })
    if frozen.support.digest(audit_path) != FROZEN_AUDIT_SHA:
        raise ValueError("frozen arithmetic producer changed during export audit")
    return result
