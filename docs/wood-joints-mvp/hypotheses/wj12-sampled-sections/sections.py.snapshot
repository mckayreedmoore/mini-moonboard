"""Sample capacity-independent sections of an existing WJ-12 composition.

The caller supplies an already materialized ``WJ12ComposedGeometry``. This
module samples exact zero-thickness planes and compares each section with its
matching stock and family-input section. It does not materialize WJ-12, infer
capacity, or establish a minimum section over a member.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj03_compact_outer_access as compact_access
from scripts import wood_joint_wj03_compact_outer_probe as outer_probe
from scripts import wood_joint_wj04_probe as wj04_probe
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj05_center_node_probe as center_probe
from scripts import wood_joints_wj05_center_backer_transfer_probe as backer_probe

SCHEMA = "wood_joint_wj12_sections/v1"
AREA_TOLERANCE_MM2 = 1e-7
ROUND_DIGITS = 6
ROOT = Path(__file__).resolve().parents[1]

DEPENDENCY_PATHS = (
    "mini_moonboard/wood_joint_wj04_config.py",
    "scripts/wood_joint_wj03_compact_outer_access.py",
    "scripts/wood_joint_wj03_compact_outer_probe.py",
    "scripts/wood_joint_wj04_probe.py",
    "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
    "scripts/wood_joint_right_rail_integration.py",
    "scripts/wood_joint_wj05_center_node_probe.py",
    "scripts/wood_joint_wj05_center_post_x190_probe.py",
    "scripts/wood_joint_wj05_center_tools.py",
    "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
    "scripts/wood_joint_wj12_compositor.py",
)

OUTER_BRIDGE = "knee_outer_right_rear_bridge"
G7_UPPER = g7_probe.UPPER_CLEAT
CENTER_UPPER = "center_principal_cleat_right"


def _vec(value: Any, name: str) -> cq.Vector:
    try:
        vector = cq.Vector(*value) if not isinstance(value, cq.Vector) else value
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a three-component vector") from error
    if vector.Length <= 1e-12:
        raise ValueError(f"{name} must be nonzero")
    return vector.normalized()


def _rounded(value: float) -> float:
    result = round(float(value), ROUND_DIGITS)
    return 0.0 if abs(result) < 10 ** (-ROUND_DIGITS) else result


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _composition_binding(geometry: Any) -> dict[str, Any]:
    inventory = _shape_map(geometry, "source_inventory")
    binding = getattr(geometry, "source_binding", None)
    binding_row = {}
    for name in (
        "inventory_sha256",
        "runtime_module_sha256",
        "uncut_part_shapes_sha256",
        "uncut_host_shape_sha256",
        "fixed_screw_axes_sha256",
        "frame_bolt_axes_sha256",
    ):
        value = getattr(binding, name, None)
        if isinstance(value, Mapping):
            binding_row[name] = dict(sorted(value.items()))
        elif isinstance(value, str):
            binding_row[name] = value
    family_fingerprints = _shape_map(geometry, "family_source_fingerprints")
    family_trial_ids = _shape_map(geometry, "family_trial_ids")
    return {
        "compositor_trial_id": str(getattr(geometry, "trial_id", "unknown")),
        "source_candidate": inventory.get("candidate"),
        "source_commit": inventory.get("source_commit"),
        "source_inventory_sha256": getattr(
            geometry, "source_inventory_sha256", None
        ),
        "source_binding": binding_row,
        "family_trial_ids": dict(sorted(family_trial_ids.items())),
        "family_source_fingerprints_sha256": {
            family: dict(sorted(rows.items()))
            for family, rows in sorted(family_fingerprints.items())
        },
        "raw_candidate_part_ids": sorted(_shape_map(geometry, "raw_candidate_parts")),
        "finished_candidate_part_ids": sorted(
            _shape_map(geometry, "finished_candidate_parts")
        ),
        "candidate_bore_ids": sorted(_shape_map(geometry, "candidate_bores")),
        "compositor_report_sha256": None,
        "compositor_report_hash_note": (
            "The in-memory geometry object does not retain its JSON artifact hash; "
            "the parent must bind the exact compositor report artifact separately."
        ),
    }


def _producer_fingerprints() -> dict[str, Any]:
    dependencies = {}
    missing = []
    for relative in DEPENDENCY_PATHS:
        path = ROOT / relative
        if path.is_file():
            dependencies[relative] = _sha256_file(path)
        else:
            missing.append(relative)
    return {
        "section_producer_sha256": _sha256_file(Path(__file__)),
        "dependency_files_sha256": dependencies,
        "missing_dependency_paths": missing,
    }


def _plane_face(origin: cq.Vector, normal: cq.Vector) -> cq.Face:
    return cq.Face.makePlane(basePnt=origin, dir=normal)


def _basis_matrix(
    origin: cq.Vector, u_axis: cq.Vector, v_axis: cq.Vector, normal: cq.Vector
) -> cq.Matrix:
    axes = (u_axis, v_axis, normal)
    return cq.Matrix(
        [
            [*axis.toTuple(), -origin.dot(axis)]
            for axis in axes
        ]
        + [[0.0, 0.0, 0.0, 1.0]]
    )


def _section_measure(
    shape: cq.Shape | None,
    *,
    origin: cq.Vector,
    normal: cq.Vector,
    u_axis: cq.Vector,
    v_axis: cq.Vector,
) -> dict[str, Any]:
    """Measure exact section area and local bounds at one plane."""
    if shape is None:
        return {
            "status": "missing_shape",
            "area_mm2": None,
            "bounds_uv_mm": None,
        }
    face = _plane_face(origin, normal)
    section = shape.intersect(face)
    area = max(0.0, float(section.Area()))
    if area <= AREA_TOLERANCE_MM2:
        return {
            "status": "no_material_on_sample_plane",
            "area_mm2": 0.0,
            "bounds_uv_mm": None,
        }
    local = section.transformGeometry(_basis_matrix(origin, u_axis, v_axis, normal))
    box = local.BoundingBox()
    return {
        "status": "section_present",
        "area_mm2": _rounded(area),
        "bounds_uv_mm": {
            "u": [_rounded(box.xmin), _rounded(box.xmax)],
            "v": [_rounded(box.ymin), _rounded(box.ymax)],
        },
    }


def _shape_map(value: Any, name: str) -> Mapping[str, cq.Shape]:
    shapes = getattr(value, name, None)
    if not isinstance(shapes, Mapping):
        return {}
    return shapes


def _candidate_bores_for_part(
    geometry: Any, part_id: str
) -> dict[str, cq.Shape]:
    result = {}
    for axis_id, bore in _shape_map(geometry, "candidate_bores").items():
        receiver_ids = getattr(bore, "receiver_ids", ())
        shape = getattr(bore, "shape", None)
        if part_id in receiver_ids and isinstance(shape, cq.Shape):
            result[axis_id] = shape
    return result


def _purchase_cutters_for_part(geometry: Any, part_id: str) -> dict[str, cq.Shape]:
    cutters = _shape_map(geometry, "purchased_panel_cutters_by_candidate_part")
    return {
        axis_id: shape
        for axis_id, shape in cutters.get(part_id, {}).items()
        if isinstance(shape, cq.Shape)
    }


def _cut_ids_on_plane(
    cutters: Mapping[str, cq.Shape], plane: cq.Face
) -> list[str]:
    return sorted(
        cutter_id
        for cutter_id, cutter in cutters.items()
        if float(cutter.intersect(plane).Area()) > AREA_TOLERANCE_MM2
    )


def _bounds_delta(
    first: dict[str, Any], second: dict[str, Any]
) -> dict[str, list[float]] | None:
    first_bounds = first.get("bounds_uv_mm")
    second_bounds = second.get("bounds_uv_mm")
    if first_bounds is None or second_bounds is None:
        return None
    return {
        axis: [
            _rounded(first_bounds[axis][index] - second_bounds[axis][index])
            for index in (0, 1)
        ]
        for axis in ("u", "v")
    }


def _measurements(
    *,
    geometry: Any,
    part_id: str,
    raw_stock: cq.Shape | None,
    family_input: cq.Shape | None,
    finished: cq.Shape | None,
    origin: cq.Vector,
    normal: cq.Vector,
    u_axis: cq.Vector,
    v_axis: cq.Vector,
    sample_id: str,
    purpose: str,
    cut_feature_ids: tuple[str, ...],
    feature_specific_cut_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    normal = _vec(normal, "section normal")
    u_axis = _vec(u_axis, "section U axis")
    v_axis = _vec(v_axis, "section V axis")
    if abs(normal.dot(u_axis)) > 1e-8 or abs(normal.dot(v_axis)) > 1e-8:
        raise ValueError("section U/V axes must lie in the sample plane")
    if abs(u_axis.dot(v_axis)) > 1e-8:
        raise ValueError("section U/V axes must be perpendicular")
    if u_axis.cross(v_axis).dot(normal) < 1.0 - 1e-8:
        raise ValueError("section U/V/normal axes must be right-handed")

    plane = _plane_face(origin, normal)
    candidate_bores = _candidate_bores_for_part(geometry, part_id)
    panel_cutters = _purchase_cutters_for_part(geometry, part_id)
    crossing_bores = _cut_ids_on_plane(candidate_bores, plane)
    crossing_panel_cutters = _cut_ids_on_plane(panel_cutters, plane)

    stock_section = _section_measure(
        raw_stock,
        origin=origin,
        normal=normal,
        u_axis=u_axis,
        v_axis=v_axis,
    )
    input_section = _section_measure(
        family_input,
        origin=origin,
        normal=normal,
        u_axis=u_axis,
        v_axis=v_axis,
    )
    finished_section = _section_measure(
        finished,
        origin=origin,
        normal=normal,
        u_axis=u_axis,
        v_axis=v_axis,
    )
    stock_area = stock_section["area_mm2"]
    input_area = input_section["area_mm2"]
    finished_area = finished_section["area_mm2"]
    return {
        "sample_id": sample_id,
        "purpose": purpose,
        "sample_basis": "exact zero-thickness plane; no finite probe thickness",
        "plane_origin_global_xyz_mm": [
            _rounded(value) for value in origin.toTuple()
        ],
        "plane_normal_global_xyz": [
            _rounded(value) for value in normal.toTuple()
        ],
        "plane_u_axis_global_xyz": [_rounded(value) for value in u_axis.toTuple()],
        "plane_v_axis_global_xyz": [_rounded(value) for value in v_axis.toTuple()],
        "stock_section": stock_section,
        "family_input_section": input_section,
        "finished_section": finished_section,
        "family_input_minus_stock_area_mm2": (
            _rounded(input_area - stock_area)
            if input_area is not None and stock_area is not None
            else None
        ),
        "finished_minus_stock_area_mm2": (
            _rounded(finished_area - stock_area)
            if finished_area is not None and stock_area is not None
            else None
        ),
        "finished_minus_family_input_area_mm2": (
            _rounded(finished_area - input_area)
            if finished_area is not None and input_area is not None
            else None
        ),
        "family_input_bounds_delta_from_stock_uv_mm": _bounds_delta(
            input_section, stock_section
        ),
        "finished_bounds_delta_from_stock_uv_mm": _bounds_delta(
            finished_section, stock_section
        ),
        "finished_to_stock_area_fraction": (
            _rounded(finished_area / stock_area)
            if finished_area is not None
            and stock_area is not None
            and stock_area > AREA_TOLERANCE_MM2
            else None
        ),
        "feature_cut_ids": list(cut_feature_ids),
        "feature_specific_cut_ids": list(feature_specific_cut_ids),
        "candidate_bore_ids_intersecting_plane": crossing_bores,
        "panel_purchase_cut_ids_intersecting_plane": crossing_panel_cutters,
        "section_bounds_are_sample_local_only": True,
    }


def _axis_plane_samples(
    *,
    geometry: Any,
    part_id: str,
    raw_stock: cq.Shape | None,
    family_input: cq.Shape | None,
    finished: cq.Shape | None,
    grain_axis: cq.Vector,
    u_axis: cq.Vector,
    cut_feature_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Sample one plane through each unique candidate-bore grain station."""
    bores = _candidate_bores_for_part(geometry, part_id)
    stations: dict[float, list[str]] = {}
    for axis_id, bore in bores.items():
        center = bore.Center()
        station = _rounded(center.dot(grain_axis))
        stations.setdefault(station, []).append(axis_id)

    records = []
    for index, (station, axis_ids) in enumerate(sorted(stations.items()), 1):
        origin = grain_axis.multiply(station)
        v_axis = grain_axis.cross(u_axis).normalized()
        records.append(
            _measurements(
                geometry=geometry,
                part_id=part_id,
                raw_stock=raw_stock,
                family_input=family_input,
                finished=finished,
                origin=origin,
                normal=grain_axis,
                u_axis=u_axis,
                v_axis=v_axis,
                sample_id=f"candidate_bore_station_{index}",
                purpose=(
                    "candidate bolt-hole section at the projected centroid station "
                    f"for axis IDs {sorted(axis_ids)}"
                ),
                cut_feature_ids=cut_feature_ids,
            )
        )
    return records


def _feature_record(
    *,
    feature_id: str,
    description: str,
    part_id: str,
    grain_axis: tuple[float, float, float] | cq.Vector,
    grain_basis: str,
    cut_id_basis: str,
    geometry: Any,
    raw_stock: cq.Shape | None,
    family_input_note: str,
    samples: list[dict[str, Any]],
    limitations: tuple[str, ...],
) -> dict[str, Any]:
    normal = _vec(grain_axis, "grain axis")
    raw_parts = _shape_map(geometry, "raw_candidate_parts")
    finished_parts = _shape_map(geometry, "finished_candidate_parts")
    family_input = raw_parts.get(part_id)
    finished = finished_parts.get(part_id)
    if raw_stock is None:
        status = "missing_matching_raw_stock_section_basis"
    elif family_input is None or finished is None:
        status = "missing_composed_candidate_part"
    else:
        status = "sampled_geometry_only"
    return {
        "feature_id": feature_id,
        "description": description,
        "part_id": part_id,
        "status": status,
        "grain_axis_global_xyz": [_rounded(v) for v in normal.toTuple()],
        "grain_basis": grain_basis,
        "cut_id_basis": cut_id_basis,
        "family_input_geometry_note": family_input_note,
        "samples": samples,
        "limitations": list(limitations),
    }


def _missing_feature(
    feature_id: str,
    description: str,
    part_id: str,
    grain_basis: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "feature_id": feature_id,
        "description": description,
        "part_id": part_id,
        "status": "missing_section_basis",
        "grain_axis_global_xyz": None,
        "grain_basis": grain_basis,
        "samples": [],
        "missing_reason": reason,
        "limitations": [
            "No section area, capacity, adequacy, or whole-member minimum is inferred."
        ],
    }


def _outer_bevel(geometry: Any) -> dict[str, Any]:
    raw_parts = _shape_map(geometry, "raw_candidate_parts")
    finished_parts = _shape_map(geometry, "finished_candidate_parts")
    raw_stock = raw_parts.get(OUTER_BRIDGE)
    finished = finished_parts.get(OUTER_BRIDGE)
    if raw_stock is None or finished is None:
        return _missing_feature(
            "wj03_compact_outer_rear_bridge_bevel",
            "Compact outer rear bridge bevel with candidate bolt-hole sections.",
            OUTER_BRIDGE,
            "WJ-03 compact candidate bridge stock record: grain axis +X.",
            "WJ12 raw/finished candidate maps do not contain the representative bridge.",
        )
    bounds = raw_stock.BoundingBox()
    x_station = (bounds.xmin + bounds.xmax) / 2.0
    origin = cq.Vector(x_station, (bounds.ymin + bounds.ymax) / 2, (bounds.zmin + bounds.zmax) / 2)
    grain = cq.Vector(1, 0, 0)
    u_axis = cq.Vector(0, 1, 0)
    v_axis = cq.Vector(0, 0, 1)
    spec = next(
        (row for row in outer_probe.HYPOTHESES if row.id == compact_access.TRIAL_ID),
        None,
    )
    if spec is None or spec.bridge_bevel_n_limit_mm is None:
        bevel_id = f"{OUTER_BRIDGE}/bevel_n_limit_unavailable"
    else:
        bevel_id = f"{OUTER_BRIDGE}/bevel_n_le_{spec.bridge_bevel_n_limit_mm:g}"
    samples = [
        _measurements(
            geometry=geometry,
            part_id=OUTER_BRIDGE,
            raw_stock=raw_stock,
            family_input=raw_stock,
            finished=finished,
            origin=origin,
            normal=grain,
            u_axis=u_axis,
            v_axis=v_axis,
            sample_id="rear_bevel_midgrain_section",
            purpose="Exact transverse section at the midpoint of the bridge stock grain span.",
            cut_feature_ids=(bevel_id,),
            feature_specific_cut_ids=(bevel_id,),
        ),
        *_axis_plane_samples(
            geometry=geometry,
            part_id=OUTER_BRIDGE,
            raw_stock=raw_stock,
            family_input=raw_stock,
            finished=finished,
            grain_axis=grain,
            u_axis=u_axis,
            cut_feature_ids=(bevel_id,),
        ),
    ]
    return _feature_record(
        feature_id="wj03_compact_outer_rear_bridge_bevel",
        description="Representative compact outer rear bridge bevel and bolt-hole sections.",
        part_id=OUTER_BRIDGE,
        grain_axis=grain,
        grain_basis=(
            "scripts/wood_joint_wj03_compact_outer_probe.py candidate stock record "
            "sets rear-bridge grain_axis=(1,0,0)."
        ),
        cut_id_basis=(
            "Exact CutRecord ID emitted by the WJ-03 compact outer producer for "
            "its 137.7 mm local-N rear-bridge bevel."
        ),
        geometry=geometry,
        raw_stock=raw_stock,
        family_input_note=(
            "WJ12 raw_candidate_parts retains this bridge before the compositor's "
            "design bevel and candidate bores."
        ),
        samples=samples,
        limitations=(
            "The sample plane is one exact transverse station, not a scan of every bridge section.",
            "Finished area includes any candidate bores and panel purchase cuts listed on that plane.",
            "No net-section adequacy, resistance, or minimum-over-member result is evaluated.",
        ),
    )


def _g7_crosscut(geometry: Any) -> dict[str, Any]:
    part_id = G7_UPPER
    family_input = _shape_map(geometry, "raw_candidate_parts").get(part_id)
    finished = _shape_map(geometry, "finished_candidate_parts").get(part_id)
    if family_input is None or finished is None:
        return _missing_feature(
            "wj04_upper_g7_crosscut",
            "WJ-04 upper G7 crosscut and bolt-hole sections.",
            part_id,
            "WJ-04 config binds this cleat's grain axis to frame N.",
            "WJ12 raw/finished candidate maps do not contain the G7 upper cleat.",
        )

    frame = WJ04_TRIAL.frame
    grain = _vec(frame.n_global, "WJ-04 grain axis N")
    u_axis = _vec(frame.x_global, "WJ-04 section U axis X")
    v_axis = grain.cross(u_axis).normalized()
    cut_stock_depth = g7_probe.CLEAT_SIZE_MM[2] - g7_probe.UPPER_CLEAT_SIZE_MM[2]
    full_stock_origin = (
        g7_probe.UPPER_CLEAT_ORIGIN_MM[0],
        g7_probe.UPPER_CLEAT_ORIGIN_MM[1],
        g7_probe.UPPER_CLEAT_ORIGIN_MM[2] - cut_stock_depth,
    )
    raw_stock = wj04_probe._box_in_trial_frame(
        WJ04_TRIAL, full_stock_origin, g7_probe.CLEAT_SIZE_MM
    )
    cut_id = f"{part_id}/upper_n_crosscut_to_{g7_probe.UPPER_CLEAT_ORIGIN_MM[2]:.6f}"
    removed_mid_n = full_stock_origin[2] + cut_stock_depth / 2
    retained_end_n = g7_probe.UPPER_CLEAT_ORIGIN_MM[2]

    def origin_at_n(n_value: float) -> cq.Vector:
        point = (
            g7_probe.UPPER_CLEAT_ORIGIN_MM[0] + g7_probe.UPPER_CLEAT_SIZE_MM[0] / 2,
            g7_probe.UPPER_CLEAT_ORIGIN_MM[1] + g7_probe.UPPER_CLEAT_SIZE_MM[1] / 2,
            n_value,
        )
        return cq.Vector(*frame.to_global(point))

    samples = [
        _measurements(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=family_input,
            finished=finished,
            origin=origin_at_n(removed_mid_n),
            normal=grain,
            u_axis=u_axis,
            v_axis=v_axis,
            sample_id="removed_crosscut_stock_midpoint",
            purpose=(
                "Transverse section at the midpoint of the 32.8 mm stock length "
                "removed by the upper crosscut."
            ),
            cut_feature_ids=(cut_id,),
            feature_specific_cut_ids=(cut_id,),
        ),
        _measurements(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=family_input,
            finished=finished,
            origin=origin_at_n(retained_end_n),
            normal=grain,
            u_axis=u_axis,
            v_axis=v_axis,
            sample_id="retained_crosscut_face",
            purpose="Exact section at the retained end face made by the G7 crosscut.",
            cut_feature_ids=(cut_id,),
            feature_specific_cut_ids=(cut_id,),
        ),
        *_axis_plane_samples(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=family_input,
            finished=finished,
            grain_axis=grain,
            u_axis=u_axis,
            cut_feature_ids=(cut_id,),
        ),
    ]
    record = _feature_record(
        feature_id="wj04_upper_g7_crosscut",
        description="WJ-04 upper G7 stock crosscut and candidate bolt-hole sections.",
        part_id=part_id,
        grain_axis=grain,
        grain_basis=(
            "WJ04_TRIAL member config binds cleat grain to station N; the frame's "
            "n_global vector is used without mirroring or inference."
        ),
        cut_id_basis=(
            "Diagnostic feature ID derived from the producer's upper cut-plane N "
            "coordinate; the crosscut is encoded by stock dimensions, not a CutRecord."
        ),
        geometry=geometry,
        raw_stock=raw_stock,
        family_input_note=(
            "WJ12 raw_candidate_parts already contains the shortened 86.9 mm N "
            "candidate input; raw_stock is the producer's matching full 119.7 mm blank."
        ),
        samples=samples,
        limitations=(
            "The removed-stock and retained-face samples are local witnesses, not a scan of all sections.",
            "Bolt-plane areas include all candidate bores that intersect each exact sample plane.",
            "No net-section adequacy or resistance is inferred from the section areas.",
        ),
    )
    record["crosscut_stock_extent"] = {
        "full_stock_n_mm": [
            _rounded(full_stock_origin[2]),
            _rounded(full_stock_origin[2] + g7_probe.CLEAT_SIZE_MM[2]),
        ],
        "family_input_and_finished_n_mm": [
            _rounded(g7_probe.UPPER_CLEAT_ORIGIN_MM[2]),
            _rounded(
                g7_probe.UPPER_CLEAT_ORIGIN_MM[2]
                + g7_probe.UPPER_CLEAT_SIZE_MM[2]
            ),
        ],
        "removed_stock_length_mm": _rounded(cut_stock_depth),
        "cut_id": cut_id,
        "geometry_basis": "source producer's full-stock and crosscut origins/dimensions",
    }
    return record


def _center_wire_relief(geometry: Any) -> dict[str, Any]:
    part_id = CENTER_UPPER
    family_input = _shape_map(geometry, "raw_candidate_parts").get(part_id)
    finished = _shape_map(geometry, "finished_candidate_parts").get(part_id)
    if family_input is None or finished is None:
        return _missing_feature(
            "wj05_center_principal_wire_relief",
            "WJ-05 center principal upper-cleat wire-relief and bolt-hole sections.",
            part_id,
            "Center-node producer declares GRAIN_T=(0,cos(50°),sin(50°)).",
            "WJ12 raw/finished candidate maps do not contain the center upper cleat.",
        )

    grain = _vec(center_probe.GRAIN_T, "WJ-05 center principal grain axis")
    u_axis = cq.Vector(1, 0, 0)
    v_axis = grain.cross(u_axis).normalized()
    stock_origin = cq.Vector(
        center_probe.UPPER_CLEAT_X_RIGHT_MM[0],
        *center_probe.UPPER_CLEAT_ORIGIN_YZ_MM,
    )
    raw_stock = center_probe._upper_cleat_right(apply_wire_relief=False)
    station = center_probe.UPPER_WIRE_RELIEF_T_MM + 2.0
    sample_origin = stock_origin + grain.multiply(station)
    cut_id = f"{part_id}/wire_relief_triangle"
    samples = [
        _measurements(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=family_input,
            finished=finished,
            origin=sample_origin,
            normal=grain,
            u_axis=u_axis,
            v_axis=v_axis,
            sample_id="inside_wire_relief_grain_station",
            purpose=(
                "Exact transverse section at local T=32 mm, inside the removed "
                "wire-relief tip; the absent section is local to this plane."
            ),
            cut_feature_ids=(cut_id,),
            feature_specific_cut_ids=(cut_id,),
        ),
        *_axis_plane_samples(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=family_input,
            finished=finished,
            grain_axis=grain,
            u_axis=u_axis,
            cut_feature_ids=(cut_id,),
        ),
    ]
    return _feature_record(
        feature_id="wj05_center_principal_wire_relief",
        description="WJ-05 center principal upper-cleat wire-relief and bolt-hole sections.",
        part_id=part_id,
        grain_axis=grain,
        grain_basis=(
            "scripts/wood_joint_wj05_center_node_probe.py declares the upper-cleat "
            "grain axis GRAIN_T=(0,cos(50°),sin(50°))."
        ),
        cut_id_basis=(
            "Diagnostic feature ID names the triangular cut constructed by "
            "_upper_cleat_wire_relief(); the family input does not expose a CutRecord."
        ),
        geometry=geometry,
        raw_stock=raw_stock,
        family_input_note=(
            "WJ12 raw_candidate_parts already contains the triangular wire relief; "
            "raw_stock is the center-node producer's same candidate primitive with "
            "apply_wire_relief=False, before candidate bores."
        ),
        samples=samples,
        limitations=(
            "The selected T=32 mm plane is one exact local section through the relief, not a scan along grain.",
            "Zero area at T=32 mm identifies material removed at this sample plane; it is not a load-bearing failure or member minimum.",
            "Candidate bores that intersect a reported plane are listed and remain included in finished area.",
            "The sample is not a net-section adequacy or resistance check.",
        ),
    )


def _backer_counterbores(geometry: Any, side: str) -> dict[str, Any]:
    if side not in ("left", "right"):
        raise ValueError(f"unknown WJ-05 backer side: {side!r}")
    part_id = f"inner_kicker_backer_{side}"
    feature_id = f"wj05_backer_{side}_bottom_counterbores"
    raw_parts = _shape_map(geometry, "raw_candidate_parts")
    finished_parts = _shape_map(geometry, "finished_candidate_parts")
    raw_stock = raw_parts.get(part_id)
    finished = finished_parts.get(part_id)
    if raw_stock is None or finished is None:
        return _missing_feature(
            feature_id,
            f"Representative {side} backer bottom counterbores and through-bolt sections.",
            part_id,
            "Backer transfer producer records nominal stock 88.9 x 88.9 x 238.9 mm, grain along +Z.",
            f"WJ12 raw/finished candidate maps do not contain the {side} backer.",
        )

    grain = cq.Vector(0, 0, 1)
    u_axis = cq.Vector(1, 0, 0)
    counterbore_z = backer_probe.BOTTOM_COUNTERBORE_DEPTH_MM / 2
    counterbore_ids = tuple(f"backer_header_{side}_{index}" for index in (1, 2))
    cut_id = feature_id
    samples = [
        _measurements(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=raw_stock,
            finished=finished,
            origin=cq.Vector(0, 0, counterbore_z),
            normal=grain,
            u_axis=u_axis,
            v_axis=cq.Vector(0, 1, 0),
            sample_id="counterbore_depth_midplane",
            purpose="Exact transverse section at the midpoint of the 7 mm bottom counterbore depth.",
            cut_feature_ids=(cut_id, *counterbore_ids),
            feature_specific_cut_ids=counterbore_ids,
        ),
        _measurements(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=raw_stock,
            finished=finished,
            origin=cq.Vector(0, 0, backer_probe.BOTTOM_COUNTERBORE_DEPTH_MM + 3.0),
            normal=grain,
            u_axis=u_axis,
            v_axis=cq.Vector(0, 1, 0),
            sample_id="through_bore_only_section",
            purpose="Exact transverse section 3 mm above the counterbore floor through the 7.3 mm bolt bores.",
            cut_feature_ids=(cut_id, *counterbore_ids),
        ),
        *_axis_plane_samples(
            geometry=geometry,
            part_id=part_id,
            raw_stock=raw_stock,
            family_input=raw_stock,
            finished=finished,
            grain_axis=grain,
            u_axis=u_axis,
            cut_feature_ids=(cut_id, *counterbore_ids),
        ),
    ]
    return _feature_record(
        feature_id=feature_id,
        description=f"Representative {side} backer counterbore and candidate through-bolt sections.",
        part_id=part_id,
        grain_axis=grain,
        grain_basis=(
            "scripts/wood_joints_wj05_center_backer_transfer_probe.py records "
            "the candidate backer stock as 88.9 x 88.9 x 238.9 mm with grain along Z."
        ),
        cut_id_basis=(
            "Counterbore IDs are keys in the producer's wj05_counterbores map; "
            "the shared feature ID names the sampled counterbore operation family."
        ),
        geometry=geometry,
        raw_stock=raw_stock,
        family_input_note=(
            f"The composed {side} raw backer is the plain full-stock candidate before its "
            "counterbores, candidate bolt bores, and redirected panel cuts."
        ),
        samples=samples,
        limitations=(
            "The depth-midplane sample quantifies one location inside the bottom counterbores only.",
            "The through-bore sample is a separate transverse plane and does not represent a stress field.",
            "This side uses only its own composed geometry and axis locations; no mirror or symmetry transfer is assumed.",
            "No bottom-foot adequacy, splitting resistance, bearing, capacity, or whole-member minimum is evaluated.",
        ),
    )


def diagnostic_report(geometry: Any) -> dict[str, Any]:
    """Return bounded sampled sections from an already composed WJ-12 object."""
    if geometry is None:
        raise TypeError("an already materialized WJ12ComposedGeometry is required")
    if not hasattr(geometry, "finished_candidate_parts") or not hasattr(
        geometry, "raw_candidate_parts"
    ):
        raise TypeError("geometry must provide composed raw and finished candidate maps")

    features = [
        _outer_bevel(geometry),
        _g7_crosscut(geometry),
        _center_wire_relief(geometry),
        _backer_counterbores(geometry, "left"),
        _backer_counterbores(geometry, "right"),
    ]
    missing = [row["feature_id"] for row in features if row["status"] != "sampled_geometry_only"]
    return {
        "schema": SCHEMA,
        "trial_id": str(getattr(geometry, "trial_id", "unknown_wj12_trial")),
        "status": (
            "sampled_sections_with_explicit_missing_basis" if missing else "sampled_sections_diagnostic_only"
        ),
        "input_contract": "consumes an existing WJ12ComposedGeometry; no source or family materialization is run",
        "composition_binding": _composition_binding(geometry),
        "producer_fingerprints": _producer_fingerprints(),
        "features": features,
        "missing_feature_ids": missing,
        "claim_boundary": {
            "capacity_established": False,
            "net_section_adequacy_evaluated": False,
            "minimum_over_entire_member_proven": False,
            "strength_or_resistance_inferred": False,
            "native_solve_run": False,
        },
        "method_limitations": [
            "Every area and bound is for an explicitly reported exact sample plane only.",
            "Section planes do not assess stress concentration, splitting, block shear, bearing, or a load path.",
            "No global minimum, tolerance range, capacity, or acceptance is reported.",
        ],
    }
