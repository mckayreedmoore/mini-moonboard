"""Conservative continuous +N enclosure screen for the WJ16 upper-right rail.

The report consumes an already composed WJ16 object. It moves the upper-right
rail, its two cleats, and the four rail-side bolt stacks together through a
nominal 200 mm +N translation. Per-shape X/T/N oriented bounding prisms cover
the full translation, so a clear screen is limited to this modeled,
initial-unwired state; it says nothing about physical support, tools,
tolerance, capacity, or a post-wiring route.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint
from mini_moonboard.wood_joint_panel_machining import PANEL_NAMES, RIGHT_PANEL_NAMES
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj06_outer_pair_probe as outer_probe
from scripts import wood_joint_wj12_diagnostic as shared_diagnostic
from scripts import wood_joint_wj16_compositor as compositor
from scripts import wood_joint_wj16_diagnostic as wj16_diagnostic

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj16_unwired_upper_right_rail_sweep/v1"
EXTENSION_MM = 200.0
HIT_TOLERANCE_MM3 = 1e-6
DISTANCE_TOLERANCE_MM = 1e-8

MOVING_MEMBER_IDS = (
    g7_probe.UPPER_RAIL,
    g7_probe.UPPER_CLEAT,
    outer_probe.UPPER_CLEAT,
)
MOVING_HARDWARE_ROLES = frozenset(
    {"shaft", "head", "head_washer", "nut_washer", "nut"}
)
MOVING_STACK_SUFFIXES = {
    "wj04_g7": frozenset({"upper_rail_1", "upper_rail_2"}),
    "wj06_outer_pair": frozenset({"upper_rail_1", "upper_rail_2"}),
}
ABSENT_UPRIGHT_STACK_SUFFIXES = {
    "wj04_g7": frozenset({"upper_principal_1", "upper_principal_2"}),
    "wj06_outer_pair": frozenset({"upper_side_1", "upper_side_2"}),
}
ABSENT_PANEL_AXIS_IDS = frozenset(
    {
        "round_panel_upper_right_service_1",
        "round_panel_upper_right_service_2",
    }
)

EXPECTED_SOURCE_WOOD_IDS = frozenset(
    {
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
        "kicker_left",
        "kicker_right",
        "base_side_left",
        "base_side_right",
        "base_rail_top",
        "base_header",
        "base_post_outer_left",
        "base_post_outer_right",
        "lumber_leg_left",
        "lumber_leg_right",
        "base_principal_center_left",
        "base_post_center_left",
        "base_principal_center_right",
        "base_post_center_right",
        "base_rail_bottom_left",
        "base_rail_service_lower_left",
        "base_rail_service_upper_left",
        "base_rail_bottom_right",
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
        "base_floor_left",
        "base_floor_right",
    }
)
EXPECTED_PROTECTED_COUNTS = {
    "fixed_66_hillman_axes_63p5mm": 66,
    "retained_12_frame_bolt_components": 60,
    "retained_12_frame_bolt_tools_withdrawals": 36,
    "tnuts": 142,
    "hold_hole_and_provisional_projection": 142,
    "lights": 132,
    "wires": 131,
    "retained_legacy_clips": 8,
    "retained_legacy_sds_axes": 48,
}
ALIAS_PROTECTED_FAMILIES = frozenset(
    {"fixed_66_hillman_axes_63p5mm", "retained_12_frame_bolt_components"}
)
ACCESS_ONLY_PROTECTED_FAMILIES = frozenset(
    {"retained_12_frame_bolt_tools_withdrawals"}
)
OMITTED_HARNESS_FAMILIES = frozenset({"lights", "wires"})
EXPECTED_COMPOSITION_COUNTS = {
    "target_duties": 16,
    "source_hosts": 13,
    "replaced_source_sds_axes": 96,
    "candidate_bores": 72,
    "candidate_installed_hardware_axes": 72,
    "candidate_installed_hardware_components": 360,
    "candidate_parts": 20,
    "panel_replacements": 3,
    "fixed_panel_axes": 66,
    "retained_frame_bolts": 12,
    "retained_frame_bolt_shapes": 72,
    "retained_legacy_clips": 8,
    "retained_legacy_sds_axes": 48,
}
EXPECTED_STATIONARY_CATEGORY_COUNTS = {
    "finished_timber_geometry": 43,
    "candidate_installed_bolt_component": 320,
    "fixed_panel_screw_axis_envelope": 64,
    "frame_bolt_installed_component": 60,
    "frame_bolt_source_occupied_axis_envelope": 12,
    "retained_tnut_geometry": 142,
    "provisional_hold_keepout": 142,
    "retained_source_clip": 8,
    "retained_source_sds_axis_envelope": 48,
}

X_AXIS = cq.Vector(*WJ04_TRIAL.frame.x_global)
T_AXIS = cq.Vector(*WJ04_TRIAL.frame.t_global)
N_AXIS = cq.Vector(*WJ04_TRIAL.frame.n_global)
FRAME_PLANE = cq.Plane(origin=(0, 0, 0), xDir=X_AXIS, normal=N_AXIS)


@dataclass(frozen=True)
class SweepScene:
    moving_shapes: Any
    moving_categories: Any
    stationary_shapes: Any
    stationary_categories: Any
    enclosures: Any
    enclosure_evidence: Any
    source_evidence: Any
    omitted_upright_stack_ids: tuple[str, ...]
    omitted_upright_component_ids: tuple[str, ...]
    absent_panel_axis_ids: tuple[str, ...]
    omitted_harness_shape_ids: tuple[str, ...]
    omitted_access_shape_ids: tuple[str, ...]


def _sha256_file(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _require_shape_map(value: Any, *, context: str) -> dict[str, cq.Shape]:
    if not hasattr(value, "items"):
        raise TypeError(f"{context} must be a shape mapping")
    result = dict(value)
    invalid = [
        name
        for name, shape in result.items()
        if not isinstance(name, str)
        or not name
        or not isinstance(shape, cq.Shape)
        or not shape.isValid()
        or not shape.Solids()
    ]
    if invalid:
        raise ValueError(f"{context} contains invalid shape IDs or solids: {invalid}")
    return result


def _source_part_shapes(source: Any, method_name: str) -> dict[str, cq.Shape]:
    method = getattr(source, method_name, None)
    if not callable(method):
        raise TypeError(f"composed source must provide {method_name}()")
    parts = tuple(method())
    result = {part.name: part.shape for part in parts}
    if len(result) != len(parts):
        raise ValueError(f"source {method_name}() has duplicate member names")
    return _require_shape_map(result, context=f"source/{method_name}")


def _validate_overlay_reconstruction(
    *,
    overlay_reconstruction: dict[str, dict[str, Any]],
    source_finished: dict[str, cq.Shape],
    overlays: dict[str, cq.Shape],
    cutters_by_host: dict[str, dict[str, cq.Shape]],
    expected_cut_ids_by_host: dict[str, set[str]],
    expected_cutters_by_host: dict[str, dict[str, cq.Shape]],
) -> None:
    """Bind the three extra receiver overlays to canonical source and cuts."""
    expected_hosts = set(compositor.EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
    maps = {
        "overlay evidence": set(overlay_reconstruction),
        "finished source overlays": set(overlays),
        "purchased panel cutter hosts": set(cutters_by_host),
        "canonical purchased panel cutter hosts": set(expected_cutters_by_host),
        "expected panel receiver hosts": set(expected_cut_ids_by_host),
    }
    if any(value != expected_hosts for value in maps.values()):
        raise ValueError(f"WJ16 additional source overlay host sets differ: {maps}")

    observed_counts = {
        host_id: len(expected_cut_ids_by_host[host_id]) for host_id in expected_hosts
    }
    if observed_counts != compositor.EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS:
        raise ValueError("WJ16 source overlays do not retain the exact 8-axis map")

    for host_id in sorted(expected_hosts):
        source_shape = source_finished.get(host_id)
        overlay_shape = overlays[host_id]
        if source_shape is None:
            raise ValueError(f"canonical finished source member is missing: {host_id}")
        cut_ids = expected_cut_ids_by_host[host_id]
        cutters = _require_shape_map(
            cutters_by_host[host_id],
            context=f"additional_purchased_panel_cutters_by_host/{host_id}",
        )
        expected_cutters = _require_shape_map(
            expected_cutters_by_host[host_id],
            context=f"canonical_purchased_panel_cutters_by_host/{host_id}",
        )
        if set(cutters) != cut_ids or set(expected_cutters) != cut_ids:
            raise ValueError(f"{host_id} purchased panel cut IDs differ from inventory")
        if any(
            _source_shape_fingerprint(cutters[cut_id])
            != _source_shape_fingerprint(expected_cutters[cut_id])
            for cut_id in cut_ids
        ):
            raise ValueError(f"{host_id} purchased panel cutter geometry differs")

        evidence = overlay_reconstruction[host_id]
        evidence_cut_ids = set(evidence.get("purchase_cut_ids", ()))
        intersections = evidence.get("purchase_cut_intersection_mm3_by_id", {})
        if (
            evidence.get("source_finished_shape_sha256")
            != _source_shape_fingerprint(source_shape)
            or evidence.get("overlaid_finished_shape_sha256")
            != _source_shape_fingerprint(overlay_shape)
            or evidence_cut_ids != cut_ids
            or set(intersections) != cut_ids
            or evidence.get("matches_source_plus_purchase_cuts") is not True
        ):
            raise ValueError(f"{host_id} source overlay reconstruction evidence changed")
        try:
            if any(
                not math.isfinite(float(intersections[cut_id]))
                or float(intersections[cut_id]) <= 0
                for cut_id in cut_ids
            ):
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError(
                f"{host_id} purchase-cut intersection evidence is invalid"
            ) from None


def _validate_protected_counts(protected: Any) -> dict[str, dict[str, cq.Shape]]:
    if not hasattr(protected, "items") or set(protected) != set(
        EXPECTED_PROTECTED_COUNTS
    ):
        raise ValueError("WJ16 protected geometry families differ from the fixed map")
    result = {
        name: _require_shape_map(shapes, context=f"protected/{name}")
        for name, shapes in protected.items()
    }
    counts = {name: len(shapes) for name, shapes in result.items()}
    if counts != EXPECTED_PROTECTED_COUNTS:
        raise ValueError(f"WJ16 protected geometry counts differ: {counts}")
    return result


def _expected_stack_ids(family_trials: Any) -> tuple[set[str], set[str]]:
    moving: set[str] = set()
    absent: set[str] = set()
    for family in sorted(MOVING_STACK_SUFFIXES):
        trial_id = family_trials.get(family)
        expected_trial = (
            g7_probe.TRIAL_ID if family == "wj04_g7" else outer_probe.TRIAL_ID
        )
        if trial_id != expected_trial:
            raise ValueError(f"WJ16 upper-right family trial changed: {family}")
        prefix = f"{family}/{trial_id}/"
        moving.update(prefix + suffix for suffix in MOVING_STACK_SUFFIXES[family])
        absent.update(
            prefix + suffix for suffix in ABSENT_UPRIGHT_STACK_SUFFIXES[family]
        )
    if len(moving) != 4 or len(absent) != 4 or moving & absent:
        raise ValueError("upper-right rail stack partition must be exactly 4 + 4")
    return moving, absent


def _validate_upper_stacks(geometry: Any) -> tuple[set[str], set[str]]:
    moving_ids, absent_ids = _expected_stack_ids(geometry.family_trial_ids)
    _require_shape_map(
        {axis_id: bore.shape for axis_id, bore in geometry.candidate_bores.items()},
        context="candidate_bores",
    )
    hardware = geometry.candidate_installed_hardware
    all_axis_ids = set(geometry.candidate_bores)
    if all_axis_ids != set(geometry.candidate_installed_hardware) or len(all_axis_ids) != 72:
        raise ValueError("WJ16 candidate bore and hardware IDs must match all 72 axes")
    if not (moving_ids | absent_ids) <= all_axis_ids:
        raise ValueError("upper-right candidate stacks are missing from WJ16")

    expected_receivers = {
        f"wj04_g7/{geometry.family_trial_ids['wj04_g7']}/upper_rail_1": {
            g7_probe.UPPER_RAIL,
            g7_probe.UPPER_CLEAT,
        },
        f"wj04_g7/{geometry.family_trial_ids['wj04_g7']}/upper_rail_2": {
            g7_probe.UPPER_RAIL,
            g7_probe.UPPER_CLEAT,
        },
        f"wj04_g7/{geometry.family_trial_ids['wj04_g7']}/upper_principal_1": {
            g7_probe.UPPER_CLEAT,
            g7_probe.PRINCIPAL,
        },
        f"wj04_g7/{geometry.family_trial_ids['wj04_g7']}/upper_principal_2": {
            g7_probe.UPPER_CLEAT,
            g7_probe.PRINCIPAL,
        },
        f"wj06_outer_pair/{geometry.family_trial_ids['wj06_outer_pair']}/upper_rail_1": {
            outer_probe.UPPER_RAIL,
            outer_probe.UPPER_CLEAT,
        },
        f"wj06_outer_pair/{geometry.family_trial_ids['wj06_outer_pair']}/upper_rail_2": {
            outer_probe.UPPER_RAIL,
            outer_probe.UPPER_CLEAT,
        },
        f"wj06_outer_pair/{geometry.family_trial_ids['wj06_outer_pair']}/upper_side_1": {
            outer_probe.UPPER_CLEAT,
            outer_probe.SIDE_HOST,
        },
        f"wj06_outer_pair/{geometry.family_trial_ids['wj06_outer_pair']}/upper_side_2": {
            outer_probe.UPPER_CLEAT,
            outer_probe.SIDE_HOST,
        },
    }
    expected_stations = {
        "wj04_g7": g7_probe.UPPER_STATION,
        "wj06_outer_pair": outer_probe.UPPER_STATION,
    }
    if set(expected_receivers) != moving_ids | absent_ids:
        raise ValueError("upper-right rail stack receiver contract is inconsistent")

    for axis_id, receivers in expected_receivers.items():
        bore = geometry.candidate_bores[axis_id]
        if set(bore.receiver_ids) != receivers:
            raise ValueError(f"{axis_id} candidate receiver identities changed")
        family = axis_id.split("/", 1)[0]
        if bore.station_id is not None and bore.station_id != expected_stations[family]:
            raise ValueError(f"{axis_id} optional station tag contradicts producer")
        components = _require_shape_map(
            hardware[axis_id], context=f"candidate_installed_hardware/{axis_id}"
        )
        if set(components) != MOVING_HARDWARE_ROLES:
            raise ValueError(f"{axis_id} installed bolt component roles changed")
    return moving_ids, absent_ids


def _validate_hardware_map_sizes(
    hardware: Any, expected_axis_ids: set[str]
) -> dict[str, dict[str, cq.Shape]]:
    if not hasattr(hardware, "items") or set(hardware) != expected_axis_ids:
        raise ValueError("candidate installed hardware axis IDs differ from WJ16")
    result = {}
    for axis_id, components in hardware.items():
        checked = _require_shape_map(
            components, context=f"candidate_installed_hardware/{axis_id}"
        )
        if len(checked) != 5:
            raise ValueError(f"{axis_id} must contain five installed shape roles")
        result[axis_id] = checked
    return result


def _validate_protected_aliases(geometry: Any, protected: Any) -> None:
    fixed_axes = _require_shape_map(geometry.fixed_axes, context="fixed_axes")
    fixed_aliases = protected["fixed_66_hillman_axes_63p5mm"]
    if set(fixed_axes) != set(fixed_aliases) or any(
        _source_shape_fingerprint(fixed_axes[axis_id])
        != _source_shape_fingerprint(fixed_aliases[axis_id])
        for axis_id in fixed_axes
    ):
        raise ValueError("protected fixed-axis aliases differ from composed axes")

    frame_aliases = protected["retained_12_frame_bolt_components"]
    frame_shapes = _require_shape_map(
        geometry.frame_bolt_shapes, context="frame_bolt_shapes"
    )
    frame_ids = {
        row["axis_id"] for row in geometry.source_inventory["starting_frame_bolts"]
    }
    alias_roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    expected_alias_ids = {
        f"{axis_id}/{role}" for axis_id in frame_ids for role in alias_roles
    }
    expected_indexed_ids = {
        f"{axis_id}/installed_component_{index}"
        for axis_id in frame_ids
        for index in range(1, 6)
    }
    indexed = {
        name: shape
        for name, shape in frame_shapes.items()
        if name.endswith(tuple(f"/installed_component_{index}" for index in range(1, 6)))
    }
    if set(frame_aliases) != expected_alias_ids or set(indexed) != expected_indexed_ids:
        raise ValueError("protected frame-bolt component IDs differ from WJ16")
    for axis_id in sorted(frame_ids):
        named_multiset = Counter(
            _source_shape_fingerprint(frame_aliases[f"{axis_id}/{role}"])
            for role in alias_roles
        )
        indexed_multiset = Counter(
            _source_shape_fingerprint(indexed[f"{axis_id}/installed_component_{index}"])
            for index in range(1, 6)
        )
        if named_multiset != indexed_multiset:
            raise ValueError(
                f"{axis_id}: named protected components differ from installed shapes"
            )


def _source_evidence(geometry: Any) -> dict[str, Any]:
    inventory_path = ROOT / "docs/wood-joints-mvp/source-inventory.json"
    inventory_bytes = inventory_path.read_bytes()
    inventory_digest = hashlib.sha256(inventory_bytes).hexdigest()
    canonical_inventory = json.loads(inventory_bytes)
    if inventory_digest != geometry.source_inventory_sha256:
        raise ValueError("WJ16 source inventory hash changed after composition")
    if dict(geometry.source_inventory) != canonical_inventory:
        raise ValueError("WJ16 source inventory differs from canonical inventory")
    binding = geometry.source_binding
    if getattr(binding, "inventory_sha256", None) != inventory_digest:
        raise ValueError("WJ16 composition source binding differs from inventory")
    expected_runtime_hashes = canonical_inventory.get(
        "source_runtime_module_hashes_sha256"
    )
    bound_runtime_hashes = dict(getattr(binding, "runtime_module_sha256", {}) or {})
    if bound_runtime_hashes != expected_runtime_hashes:
        raise ValueError("WJ16 runtime module binding differs from source inventory")
    if getattr(binding, "uncut_part_shapes_sha256", None) != canonical_inventory.get(
        "source_part_shapes_sha256"
    ):
        raise ValueError("WJ16 bound raw-shape fingerprint differs from inventory")
    for relative_path, expected_hash in expected_runtime_hashes.items():
        if _sha256_file(relative_path) != expected_hash:
            raise ValueError(f"canonical source runtime module changed: {relative_path}")

    family_fingerprints = {
        family: dict(sorted(rows.items()))
        for family, rows in sorted(geometry.family_source_fingerprints.items())
    }
    for family, rows in family_fingerprints.items():
        for relative_path, expected_hash in rows.items():
            if _sha256_file(relative_path) != expected_hash:
                raise ValueError(
                    f"WJ16 {family} source fingerprint changed: {relative_path}"
                )
    reconstruction = {
        host_id: dict(row)
        for host_id, row in geometry.source_reconstruction.items()
    }
    overlay_reconstruction = {
        host_id: dict(row)
        for host_id, row in geometry.additional_source_reconstruction.items()
    }
    expected_overlay_ids = set(compositor.EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
    if set(reconstruction) != set(compositor.EXPECTED_SOURCE_HOST_IDS) or any(
        not row.get("matches_source_finished_member", False)
        or float(row.get("symmetric_difference_mm3", math.inf)) > 1e-3
        for row in reconstruction.values()
    ):
        raise ValueError("WJ16 native host reconstruction evidence is incomplete")
    overlay_hosts = {
        row["candidate_finished_receiver_member"]
        for row in canonical_inventory.get("fixed_panel_kicker_screws", ())
        if row.get("source_finished_receiver_member")
        == row.get("candidate_finished_receiver_member")
        and row.get("candidate_finished_receiver_member") in expected_overlay_ids
    }
    expected_cut_ids_by_host = {
        host_id: {
            f"panel_purchase/{row['axis_id']}"
            for row in canonical_inventory.get("fixed_panel_kicker_screws", ())
            if row.get("source_finished_receiver_member") == host_id
            and row.get("candidate_finished_receiver_member") == host_id
        }
        for host_id in overlay_hosts
    }
    source_finished = _source_part_shapes(geometry.source, "parts")
    overlay_parts = _require_shape_map(
        geometry.additional_finished_source_parts,
        context="additional_finished_source_parts",
    )
    cutter_hosts = {
        host_id: dict(cutters)
        for host_id, cutters in geometry.additional_purchased_panel_cutters_by_host.items()
    }
    expected_cutters_by_host = compositor._panel_cutters_by_host(
        geometry.source, canonical_inventory, frozenset(expected_overlay_ids)
    )
    if overlay_hosts != expected_overlay_ids:
        raise ValueError("WJ16 source overlay hosts differ from the pinned inventory")
    _validate_overlay_reconstruction(
        overlay_reconstruction=overlay_reconstruction,
        source_finished=source_finished,
        overlays=overlay_parts,
        cutters_by_host=cutter_hosts,
        expected_cut_ids_by_host=expected_cut_ids_by_host,
        expected_cutters_by_host=expected_cutters_by_host,
    )
    producer_paths = {
        "wj16_compositor": "scripts/wood_joint_wj16_compositor.py",
        "wj16_diagnostic": "scripts/wood_joint_wj16_diagnostic.py",
        "wj12_diagnostic": "scripts/wood_joint_wj12_diagnostic.py",
        "wj04_g7": "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
        "wj06_outer_pair": "scripts/wood_joint_wj06_outer_pair_probe.py",
        "unwired_sweep": "scripts/wood_joint_wj16_unwired_rail_sweep.py",
    }
    wiring_reference_paths = {
        "round_service_routing": "docs/round-service-wiring-reference.json",
        "manufacturer_led_routing": "docs/led-wiring-reference.json",
    }
    round_wiring_reference = json.loads(
        (ROOT / wiring_reference_paths["round_service_routing"]).read_text()
    )
    return {
        "source_inventory_sha256": inventory_digest,
        "source_commit": canonical_inventory.get("source_commit"),
        "source_runtime_module_hashes_sha256": dict(sorted(bound_runtime_hashes.items())),
        "family_trial_ids": dict(sorted(geometry.family_trial_ids.items())),
        "family_source_fingerprints_sha256": family_fingerprints,
        "native_host_reconstruction": reconstruction,
        "additional_source_overlay_reconstruction": overlay_reconstruction,
        "producer_hashes_sha256": {
            name: _sha256_file(path) for name, path in sorted(producer_paths.items())
        },
        "wiring_reference_sha256": {
            name: _sha256_file(path)
            for name, path in sorted(wiring_reference_paths.items())
        },
        "wiring_installation_sequence": round_wiring_reference["installation"][
            "sequence"
        ],
    }


def _frame_point(x: float, t: float, n: float) -> cq.Vector:
    return X_AXIS.multiply(x).add(T_AXIS.multiply(t)).add(N_AXIS.multiply(n))


def _frame_bounds(shape: cq.Shape) -> tuple[float, float, float, float, float, float]:
    """Return the OCC bounding box after exact rigid transform to X/T/N."""
    local_shape = shape.moved(FRAME_PLANE.location.inverse)
    bounds = local_shape.BoundingBox()
    return (
        bounds.xmin,
        bounds.xmax,
        bounds.ymin,
        bounds.ymax,
        bounds.zmin,
        bounds.zmax,
    )


def _make_oriented_box(
    bounds: tuple[float, float, float, float, float, float],
    *,
    extra_n_mm: float = 0.0,
) -> cq.Shape:
    if not math.isfinite(extra_n_mm) or extra_n_mm < 0:
        raise ValueError("extra_n_mm must be finite and nonnegative")
    xmin, xmax, tmin, tmax, nmin, nmax = bounds
    lengths = (xmax - xmin, tmax - tmin, nmax - nmin + extra_n_mm)
    if any(not math.isfinite(value) or value <= 0 for value in lengths):
        raise ValueError("oriented enclosure must have finite positive dimensions")
    plane = cq.Plane(
        origin=_frame_point(xmin, tmin, nmin),
        xDir=X_AXIS,
        normal=N_AXIS,
    )
    return cq.Workplane(plane).box(*lengths, centered=(False, False, False)).val()


def _volume_outside(shape: cq.Shape, enclosure: cq.Shape) -> float:
    return max(0.0, float(shape.cut(enclosure).Volume()))


def _build_sweep_enclosure(
    shape: cq.Shape,
    *,
    extension_mm: float = EXTENSION_MM,
    tolerance_mm3: float = HIT_TOLERANCE_MM3,
) -> tuple[cq.Shape, dict[str, Any]]:
    if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
        raise ValueError("moving source must be a valid solid CAD shape")
    if not math.isfinite(tolerance_mm3) or tolerance_mm3 < 0:
        raise ValueError("tolerance_mm3 must be finite and nonnegative")
    bounds = _frame_bounds(shape)
    enclosure = _make_oriented_box(bounds, extra_n_mm=extension_mm)
    endpoint = shape.translate(N_AXIS.multiply(extension_mm))
    start_outside = _volume_outside(shape, enclosure)
    end_outside = _volume_outside(endpoint, enclosure)
    containment_ok = (
        start_outside <= tolerance_mm3 and end_outside <= tolerance_mm3
    )
    if not containment_ok:
        raise ValueError("oriented +N enclosure does not contain moving endpoints")
    return enclosure, {
        "local_x_t_n_bounds_mm": [round(value, 9) for value in bounds],
        "extension_n_mm": extension_mm,
        "start_shape_outside_enclosure_mm3": round(start_outside, 9),
        "end_shape_outside_enclosure_mm3": round(end_outside, 9),
        "start_and_end_containment_verified": containment_ok,
        "intermediate_translation_contained_by_prism": True,
        "containment_basis": (
            "The validated start solid and its +N endpoint lie inside an X/T/N prism; "
            "the prism spans every intermediate rigid translation along N."
        ),
    }


def _bbox_disjoint(first: cq.Shape, second: cq.Shape) -> bool:
    a, b = first.BoundingBox(), second.BoundingBox()
    return (
        a.xmax < b.xmin - DISTANCE_TOLERANCE_MM
        or b.xmax < a.xmin - DISTANCE_TOLERANCE_MM
        or a.ymax < b.ymin - DISTANCE_TOLERANCE_MM
        or b.ymax < a.ymin - DISTANCE_TOLERANCE_MM
        or a.zmax < b.zmin - DISTANCE_TOLERANCE_MM
        or b.zmax < a.zmin - DISTANCE_TOLERANCE_MM
    )


def _add_shapes(
    destination: dict[str, cq.Shape],
    categories: dict[str, str],
    namespace: str,
    rows: dict[str, cq.Shape],
    *,
    category: str,
    omit: set[str] | frozenset[str] = frozenset(),
) -> None:
    for name, shape in sorted(rows.items()):
        if name in omit:
            continue
        shape_id = f"{namespace}/{name}"
        if shape_id in destination:
            raise ValueError(f"duplicate scene shape ID: {shape_id}")
        destination[shape_id] = shape
        categories[shape_id] = category


def _build_scene(geometry: Any) -> SweepScene:
    if not isinstance(geometry, compositor.WJ16ComposedGeometry):
        raise TypeError("sweep requires an already composed WJ16ComposedGeometry")
    if geometry.layout_id != compositor.LAYOUT_ID or geometry.trial_id != compositor.TRIAL_ID:
        raise ValueError("sweep requires the fixed current WJ16 composition")
    if geometry.status != "unaccepted_integrated_hypothesis":
        raise ValueError("sweep requires the unaccepted WJ16 hypothesis status")

    identity = shared_diagnostic._layout_identity_checks(
        geometry, wj16_diagnostic.WJ16_LAYOUT
    )
    if not identity.get("all_exact_sets_match", False):
        raise ValueError("WJ16 exact identity/count contract failed before sweep")
    counts = dict(geometry.counts)
    if any(counts.get(name) != expected for name, expected in EXPECTED_COMPOSITION_COUNTS.items()):
        raise ValueError("WJ16 composed counts differ from the fixed contract")
    source_evidence = _source_evidence(geometry)
    moving_stack_ids, absent_stack_ids = _validate_upper_stacks(geometry)
    hardware_maps = _validate_hardware_map_sizes(
        geometry.candidate_installed_hardware,
        set(geometry.candidate_bores),
    )

    _, finished_wood = shared_diagnostic._composed_wood(geometry)
    if set(finished_wood) != EXPECTED_SOURCE_WOOD_IDS | set(
        compositor.EXPECTED_CANDIDATE_PART_IDS
    ):
        raise ValueError("complete WJ16 finished wood inventory changed")
    if set(geometry.panel_replacements) != RIGHT_PANEL_NAMES:
        raise ValueError("WJ16 panel replacement IDs differ from the three right panels")
    if not PANEL_NAMES <= set(finished_wood):
        raise ValueError("complete WJ16 finished wood map omits one or more of six panels")
    if not set(MOVING_MEMBER_IDS) <= set(finished_wood):
        raise ValueError("upper-right rail or either cleat is absent from finished wood")

    protected = _validate_protected_counts(geometry.protected)
    _validate_protected_aliases(geometry, protected)
    if set(geometry.fixed_axes) != {
        row["axis_id"] for row in geometry.source_inventory["fixed_panel_kicker_screws"]
    }:
        raise ValueError("fixed screw axis IDs differ from the 66-entry inventory")
    if not ABSENT_PANEL_AXIS_IDS <= set(geometry.fixed_axes):
        raise ValueError("the two upper-right panel receiver screw axes are missing")
    if not ABSENT_PANEL_AXIS_IDS <= {
        row["axis_id"]
        for row in geometry.source_inventory["fixed_panel_kicker_screws"]
    }:
        raise ValueError("inventory lacks the two declared absent receiver screw IDs")

    moving_shapes: dict[str, cq.Shape] = {}
    moving_categories: dict[str, str] = {}
    for member_id in MOVING_MEMBER_IDS:
        shape_id = f"finished_wood/{member_id}"
        moving_shapes[shape_id] = finished_wood[member_id]
        moving_categories[shape_id] = (
            "source_timber" if member_id == g7_probe.UPPER_RAIL else "candidate_timber"
        )
    for axis_id in sorted(moving_stack_ids):
        for role, shape in sorted(hardware_maps[axis_id].items()):
            shape_id = f"candidate_installed_hardware/{axis_id}/{role}"
            moving_shapes[shape_id] = shape
            moving_categories[shape_id] = "candidate_installed_bolt_component"
    if len(moving_shapes) != 23:
        raise ValueError("the upper-right rigid subassembly must contain 23 shapes")

    stationary_shapes: dict[str, cq.Shape] = {}
    stationary_categories: dict[str, str] = {}
    _add_shapes(
        stationary_shapes,
        stationary_categories,
        "finished_wood",
        finished_wood,
        category="finished_timber_geometry",
        omit=set(MOVING_MEMBER_IDS),
    )

    for axis_id, components in sorted(hardware_maps.items()):
        if axis_id in moving_stack_ids or axis_id in absent_stack_ids:
            continue
        _add_shapes(
            stationary_shapes,
            stationary_categories,
            f"candidate_installed_hardware/{axis_id}",
            _require_shape_map(components, context=f"hardware/{axis_id}"),
            category="candidate_installed_bolt_component",
        )

    fixed_axes = _require_shape_map(geometry.fixed_axes, context="fixed_axes")
    _add_shapes(
        stationary_shapes,
        stationary_categories,
        "fixed_axes",
        fixed_axes,
        category="fixed_panel_screw_axis_envelope",
        omit=ABSENT_PANEL_AXIS_IDS,
    )
    frame_shapes = _require_shape_map(
        geometry.frame_bolt_shapes, context="frame_bolt_shapes"
    )
    expected_frame_axis_ids = {
        row["axis_id"] for row in geometry.source_inventory["starting_frame_bolts"]
    }
    expected_frame_shape_ids = {
        f"{axis_id}/installed_component_{index}"
        for axis_id in expected_frame_axis_ids
        for index in range(1, 6)
    } | {f"{axis_id}/source_occupied_axis" for axis_id in expected_frame_axis_ids}
    if set(frame_shapes) != expected_frame_shape_ids or len(frame_shapes) != 72:
        raise ValueError("WJ16 frame-bolt shape inventory differs from 12 × (5 + 1)")
    for shape_id, shape in sorted(frame_shapes.items()):
        key = f"frame_bolt_shapes/{shape_id}"
        stationary_shapes[key] = shape
        stationary_categories[key] = (
            "frame_bolt_source_occupied_axis_envelope"
            if shape_id.endswith("/source_occupied_axis")
            else "frame_bolt_installed_component"
        )

    for family, rows in sorted(protected.items()):
        if family in ALIAS_PROTECTED_FAMILIES | ACCESS_ONLY_PROTECTED_FAMILIES | OMITTED_HARNESS_FAMILIES:
            continue
        category = {
            "tnuts": "retained_tnut_geometry",
            "hold_hole_and_provisional_projection": "provisional_hold_keepout",
            "retained_legacy_clips": "retained_source_clip",
            "retained_legacy_sds_axes": "retained_source_sds_axis_envelope",
        }.get(family)
        if category is None:
            raise ValueError(f"unclassified WJ16 protected family: {family}")
        _add_shapes(
            stationary_shapes,
            stationary_categories,
            f"protected/{family}",
            rows,
            category=category,
        )

    category_counts = dict(Counter(stationary_categories.values()))
    if len(stationary_shapes) != 839 or category_counts != EXPECTED_STATIONARY_CATEGORY_COUNTS:
        raise ValueError(
            f"WJ16 initial-unwired stationary shape count must be 839; "
            f"observed {len(stationary_shapes)} with categories {category_counts}"
        )

    enclosure_map: dict[str, cq.Shape] = {}
    enclosure_evidence: dict[str, dict[str, Any]] = {}
    for shape_id, shape in sorted(moving_shapes.items()):
        enclosure, evidence = _build_sweep_enclosure(shape)
        enclosure_map[shape_id] = enclosure
        enclosure_evidence[shape_id] = evidence

    absent_components = tuple(
        sorted(
            f"candidate_installed_hardware/{axis_id}/{role}"
            for axis_id in absent_stack_ids
            for role in MOVING_HARDWARE_ROLES
        )
    )
    harness_shape_ids = tuple(
        sorted(
            f"protected/{family}/{shape_id}"
            for family in OMITTED_HARNESS_FAMILIES
            for shape_id in protected[family]
        )
    )
    access_shape_ids = tuple(
        sorted(
            f"protected/{family}/{shape_id}"
            for family in ACCESS_ONLY_PROTECTED_FAMILIES
            for shape_id in protected[family]
        )
    )
    return SweepScene(
        moving_shapes=MappingProxyType(dict(sorted(moving_shapes.items()))),
        moving_categories=MappingProxyType(dict(sorted(moving_categories.items()))),
        stationary_shapes=MappingProxyType(dict(sorted(stationary_shapes.items()))),
        stationary_categories=MappingProxyType(dict(sorted(stationary_categories.items()))),
        enclosures=MappingProxyType(dict(sorted(enclosure_map.items()))),
        enclosure_evidence=MappingProxyType(
            {name: MappingProxyType(row) for name, row in sorted(enclosure_evidence.items())}
        ),
        source_evidence=MappingProxyType(source_evidence),
        omitted_upright_stack_ids=tuple(sorted(absent_stack_ids)),
        omitted_upright_component_ids=absent_components,
        absent_panel_axis_ids=tuple(sorted(ABSENT_PANEL_AXIS_IDS)),
        omitted_harness_shape_ids=harness_shape_ids,
        omitted_access_shape_ids=access_shape_ids,
    )


def _screen_enclosures(scene: SweepScene) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    contacts: list[dict[str, Any]] = []
    boolean_pair_count = 0
    for moving_id, enclosure in scene.enclosures.items():
        for obstacle_id, obstacle in scene.stationary_shapes.items():
            if _bbox_disjoint(enclosure, obstacle):
                continue
            boolean_pair_count += 1
            try:
                volume = max(0.0, float(enclosure.intersect(obstacle).Volume()))
            except Exception as exc:  # pragma: no cover - exact CAD failure path
                raise RuntimeError(
                    f"CAD intersection failed for {moving_id} vs {obstacle_id}"
                ) from exc
            if volume > HIT_TOLERANCE_MM3:
                hits.append(
                    {
                        "sweep_enclosure_id": moving_id,
                        "moving_category": scene.moving_categories[moving_id],
                        "obstacle_id": obstacle_id,
                        "obstacle_category": scene.stationary_categories[obstacle_id],
                        "intersection_volume_mm3": round(volume, 9),
                    }
                )
                continue
            distance = max(0.0, float(enclosure.distance(obstacle)))
            if distance <= DISTANCE_TOLERANCE_MM:
                contacts.append(
                    {
                        "sweep_enclosure_id": moving_id,
                        "obstacle_id": obstacle_id,
                        "obstacle_category": scene.stationary_categories[obstacle_id],
                    }
                )
    hits.sort(key=lambda row: (row["sweep_enclosure_id"], row["obstacle_id"]))
    contacts.sort(key=lambda row: (row["sweep_enclosure_id"], row["obstacle_id"]))
    by_category: dict[str, dict[str, Any]] = {}
    for row in hits:
        category = row["obstacle_category"]
        summary = by_category.setdefault(
            category, {"positive_volume_hit_count": 0, "intersection_volume_mm3": 0.0}
        )
        summary["positive_volume_hit_count"] += 1
        summary["intersection_volume_mm3"] += row["intersection_volume_mm3"]
    for summary in by_category.values():
        summary["intersection_volume_mm3"] = round(
            summary["intersection_volume_mm3"], 9
        )
    return {
        "sweep_enclosure_count": len(scene.enclosures),
        "stationary_shape_count": len(scene.stationary_shapes),
        "potential_pair_count": len(scene.enclosures) * len(scene.stationary_shapes),
        "exact_boolean_pair_count_after_bbox_pruning": boolean_pair_count,
        "positive_volume_overlap_count": len(hits),
        "positive_volume_overlap_total_mm3": round(
            sum(row["intersection_volume_mm3"] for row in hits), 9
        ),
        "positive_volume_overlaps_by_obstacle_category": dict(sorted(by_category.items())),
        "positive_volume_overlaps": hits,
        "zero_gap_contact_count": len(contacts),
        "zero_gap_contacts": contacts,
        "conservative_enclosures_clear_of_stationary_shapes": not hits and not contacts,
        "positive_volume_only_clearance_is_insufficient_for_tolerance_claim": True,
    }


def build_wj16_unwired_rail_sweep_report(geometry: Any) -> dict[str, Any]:
    """Build a source-bound enclosure screen from retained WJ16 geometry."""
    scene = _build_scene(geometry)
    screen = _screen_enclosures(scene)
    n_axis = tuple(float(value) for value in WJ04_TRIAL.frame.n_global)
    total_shapes = len(scene.moving_shapes) + len(scene.stationary_shapes)
    return {
        "schema": SCHEMA,
        "layout_id": geometry.layout_id,
        "trial_id": geometry.trial_id,
        "status": "continuous_nominal_initial_unwired_motion_enclosure_diagnostic",
        "claim_boundary": (
            "A conservative CAD enclosure screen for one nominal +N translation of the "
            "WJ16 upper-right rail subassembly in an initial-unwired scene. It does not "
            "establish support, tools, tolerance, capacity, fabrication, or movement after wiring."
        ),
        "source": dict(scene.source_evidence),
        "assembly_state": {
            "motion_direction": "+N",
            "N_global_xyz": list(n_axis),
            "translation_interval_mm": [0.0, EXTENSION_MM],
            "moving_member_ids": list(MOVING_MEMBER_IDS),
            "moving_shape_ids": sorted(scene.moving_shapes),
            "moving_shape_count": len(scene.moving_shapes),
            "moving_candidate_rail_stack_ids": sorted(
                _expected_stack_ids(geometry.family_trial_ids)[0]
            ),
            "moving_candidate_rail_stack_component_ids": [
                shape_id
                for shape_id in sorted(scene.moving_shapes)
                if shape_id.startswith("candidate_installed_hardware/")
            ],
            "not_yet_installed_upright_stack_ids_omitted": list(
                scene.omitted_upright_stack_ids
            ),
            "not_yet_installed_upright_component_ids_omitted": list(
                scene.omitted_upright_component_ids
            ),
            "temporarily_absent_upper_right_panel_screw_axis_ids": list(
                scene.absent_panel_axis_ids
            ),
            "panel_shapes_retained_stationary": True,
            "panel_screw_removal_support_or_reinstallation_proven": False,
            "complete_led_wire_harness_omitted": True,
            "omitted_complete_harness_shape_count": len(scene.omitted_harness_shape_ids),
            "omitted_light_shape_count": EXPECTED_PROTECTED_COUNTS["lights"],
            "omitted_wire_shape_count": EXPECTED_PROTECTED_COUNTS["wires"],
            "retained_tnut_shape_count": EXPECTED_PROTECTED_COUNTS["tnuts"],
            "retained_hold_keepout_shape_count": EXPECTED_PROTECTED_COUNTS[
                "hold_hole_and_provisional_projection"
            ],
            "omitted_complete_harness_shape_ids": list(scene.omitted_harness_shape_ids),
            "stationary_shape_count_if_harness_retained": 1102,
            "initial_unwired_state_basis": {
                "installation_sequence": scene.source_evidence[
                    "wiring_installation_sequence"
                ],
                "source_path": "docs/round-service-wiring-reference.json",
                "source_sha256": scene.source_evidence["wiring_reference_sha256"][
                    "round_service_routing"
                ],
                "manufacturer_routing_source_path": "docs/led-wiring-reference.json",
                "manufacturer_routing_source_sha256": scene.source_evidence[
                    "wiring_reference_sha256"
                ]["manufacturer_led_routing"],
                "scope": "models only the earlier frame-and-panels-installed, harness-not-yet-fed state",
            },
            "canonical_source_wood_member_count": len(EXPECTED_SOURCE_WOOD_IDS),
            "complete_finished_wood_member_count": len(EXPECTED_SOURCE_WOOD_IDS)
            + len(compositor.EXPECTED_CANDIDATE_PART_IDS),
            "all_six_panel_member_ids": sorted(PANEL_NAMES),
            "candidate_panel_replacement_ids": sorted(geometry.panel_replacements),
            "protected_alias_families_not_duplicated": sorted(ALIAS_PROTECTED_FAMILIES),
            "nonphysical_tool_access_envelopes_excluded": list(
                scene.omitted_access_shape_ids
            ),
            "all_other_wj16_physical_obstacles_retained": True,
            "moving_plus_stationary_shape_count": total_shapes,
            "stationary_shape_ids": sorted(scene.stationary_shapes),
            "stationary_shape_categories": dict(
                sorted(Counter(scene.stationary_categories.values()).items())
            ),
        },
        "enclosure_method": {
            "frame_axes": {
                "X_global_xyz": list(WJ04_TRIAL.frame.x_global),
                "T_global_xyz": list(WJ04_TRIAL.frame.t_global),
                "N_global_xyz": list(WJ04_TRIAL.frame.n_global),
            },
            "construction": (
                "Rigid-transform each moving solid into the source X/T/N frame, take "
                "its OCC bounding box there, and extend only its N interval by 200 mm. "
                "Each oriented prism contains the start solid and its translated "
                "endpoint, and spans every intermediate rigid translation."
            ),
            "per_shape_containment": {
                shape_id: dict(row)
                for shape_id, row in sorted(scene.enclosure_evidence.items())
            },
            "all_start_and_endpoint_containment_verified": all(
                row["start_and_end_containment_verified"]
                for row in scene.enclosure_evidence.values()
            ),
        },
        "screen": screen,
        "release": {
            "nominal_continuous_enclosure_clearance": screen[
                "conservative_enclosures_clear_of_stationary_shapes"
            ],
            "physical_assembly_or_support_proven": False,
            "tool_or_hand_access_claimed": False,
            "tolerance_clearance_proven": False,
            "post_wiring_transport_proven": False,
            "capacity_established": False,
            "fabrication_released": False,
            "structural_accepted": False,
        },
        "limitations": [
            "The motion is one rigid +N translation from 0 to 200 mm; no reverse, rotation, or alternative pose is tested.",
            "The LED lights and wire runs are omitted in full, while all six panels, all T-nuts, and all provisional hold keepouts remain obstacles.",
            "Four upright candidate bolt stacks and two upper-right Hillman screw envelopes are absent for this modeled stage; their installation and panel support are not demonstrated.",
            "An empty enclosure-intersection result applies only to these source-bound nominal solids and this initial-unwired state; it is not a tolerance, tool-access, handling, support, capacity, or post-wiring claim.",
        ],
    }


__all__ = ["build_wj16_unwired_rail_sweep_report"]
