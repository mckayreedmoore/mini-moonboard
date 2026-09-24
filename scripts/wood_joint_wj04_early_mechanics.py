"""Project old WJ-04 station actions onto canonical ordinary-joint faces.

This is a demand-preservation diagnostic and fail-closed method contract. It
does not qualify the new joint or replace fresh candidate mechanics and cases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL, validate_wj04_trial

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs' / 'wood-joints-mvp'
DEMAND_PATH = ROOT / 'docs' / 'floor-runner-mvp-angle-demands.json'
INVENTORY_PATH = DOCS / 'source-inventory.json'
PROBE_PATH = DOCS / 'wj04-probe.json'
PROBE_PRODUCER_PATH = ROOT / 'scripts' / 'wood_joint_wj04_probe.py'
CONFIG_PATH = ROOT / 'mini_moonboard' / 'wood_joint_wj04_config.py'
OUTPUT_JSON = DOCS / 'wj04-early-mechanics.json'
OUTPUT_MD = DOCS / 'wj04-early-mechanics.md'
STATION = 'clip_horizontal_lower_right_1'
EXPECTED_CASES = ('a12-left', 'a12-rear', 'a12-forward', 'k12-right', 'k12-rear', 'a1-rear')
TOL = 1.0e-8
STATIC_BALANCE_TOL = 1.0e-4
CONTACT_EDGE_BAND_WIDTH_MM = 10.0
CONTACT_EDGE_RESULTANT_INSET_MM = CONTACT_EDGE_BAND_WIDTH_MM / 2
CONTACT_PROBE_DEPTH_MM = 0.1
CONTACT_AREA_METHOD_ID = 'thin_inward_intersection_volume_divided_by_probe_depth'


def _vec(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f'{label} must contain three components')
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f'{label} must be finite')
    return result


def _dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b, strict=True))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def _scale(scalar, vector):
    return tuple(scalar * x for x in vector)


def _norm(vector):
    return math.sqrt(_dot(vector, vector))


def _unit(vector, label):
    norm = _norm(vector)
    if norm <= TOL:
        raise ValueError(f'{label} has zero length')
    return _scale(1.0 / norm, vector)


def _project(vector, basis):
    return tuple(_dot(vector, axis) for axis in basis)


def _axis_basis(config, axis_name):
    return {
        'X': config.frame.x_global,
        'T': config.frame.t_global,
        'N': config.frame.n_global,
    }[axis_name]


def _member_grain_global(config, member):
    return _axis_basis(config, member.grain_axis)


def _round(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, tuple):
        return [_round(item) for item in value]
    if isinstance(value, list):
        return [_round(item) for item in value]
    if isinstance(value, dict):
        return {key: _round(item) for key, item in value.items()}
    return value


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _compare_hashes(declared):
    result = {}
    for relative_path, expected in sorted(declared.items()):
        path = ROOT / relative_path
        actual = _sha256(path) if path.is_file() else None
        result[relative_path] = {
            'declared_sha256': expected,
            'current_sha256': actual,
            'status': 'match' if actual == expected else ('missing' if actual is None else 'stale_or_mismatched'),
        }
    return result


def _staleness_audit(demand, inventory, probe):
    case_sources = {}
    all_case_paths = {}
    for case_id in EXPECTED_CASES:
        declared = demand['cases'][case_id]['source_sha256']
        compared = _compare_hashes(declared)
        stale = [path for path, item in compared.items() if item['status'] == 'stale_or_mismatched']
        missing = [path for path, item in compared.items() if item['status'] == 'missing']
        matches = sum(item['status'] == 'match' for item in compared.values())
        case_sources[case_id] = {
            'declared_source_count': len(compared),
            'matching_current_files': matches,
            'stale_or_mismatched_paths': stale,
            'missing_paths': missing,
        }
        for path in (*stale, *missing):
            all_case_paths.setdefault(path, compared[path])

    probe_dependencies = dict(probe.get('dependency_sha256', {}))
    probe_dependencies['scripts/wood_joint_wj04_probe.py'] = probe.get('producer_sha256')
    probe_inventory_sha = probe.get('source_inventory_sha256')
    probe_dependency_status = _compare_hashes(probe_dependencies)
    probe_dependency_status['docs/wood-joints-mvp/source-inventory.json'] = {
        'declared_sha256': probe_inventory_sha,
        'current_sha256': _sha256(INVENTORY_PATH),
        'status': 'match' if probe_inventory_sha == _sha256(INVENTORY_PATH) else 'stale_or_mismatched',
    }

    inventory_bindings = dict(inventory.get('source_hashes_sha256', {}))
    inventory_bindings.update(inventory.get('source_runtime_module_hashes_sha256', {}))
    inventory_binding_status = _compare_hashes(inventory_bindings)

    contact_path = 'fea/current_response_run.py'
    contact_current = _sha256(ROOT / contact_path)
    contact_search = {
        case_id: {
            'declared_sha256': demand['contact_search_source_sha256_by_case'][case_id],
            'current_sha256': contact_current,
            'status': 'match' if demand['contact_search_source_sha256_by_case'][case_id] == contact_current
            else 'stale_or_mismatched',
        }
        for case_id in EXPECTED_CASES
    }
    return {
        'status': 'stale_or_unverified_inputs_are_recorded_not_promoted',
        'historical_source_commit': inventory.get('source_commit'),
        'historical_source_commit_note': (
            'Pinned baseline identity only; it does not establish freshness of the current working tree.'
        ),
        'old_case_source_snapshot_by_case': case_sources,
        'old_case_stale_or_missing_source_hashes': all_case_paths,
        'old_case_sources_currently_verified_by_source_ledger': False,
        'old_case_consumer_sources': _compare_hashes(demand.get('consumer_source_sha256', {})),
        'old_case_contact_search_source_by_case': contact_search,
        'wood_joint_source_inventory_bindings': inventory_binding_status,
        'wj04_probe_producer_and_dependencies': probe_dependency_status,
    }


def _close_vectors(actual, expected, label):
    if any(not math.isclose(a, e, rel_tol=1.0e-10, abs_tol=TOL)
           for a, e in zip(actual, expected, strict=True)):
        raise ValueError(f'{label} does not match the source record')


def _require_point_inside_contact_rectangle(
    point, face_center, normal, row, transverse, row_bounds, transverse_bounds, label,
):
    plane_distance = _dot(_sub(point, face_center), normal)
    row_coordinate = _dot(point, row)
    transverse_coordinate = _dot(point, transverse)
    if abs(plane_distance) > STATIC_BALANCE_TOL:
        raise ValueError(f'{label} is outside the actual contact-face plane')
    if not row_bounds[0] - TOL <= row_coordinate <= row_bounds[1] + TOL:
        raise ValueError(f'{label} is outside the canonical bounds contact rectangle along the bolt row')
    if not transverse_bounds[0] - TOL <= transverse_coordinate <= transverse_bounds[1] + TOL:
        raise ValueError(f'{label} is outside the canonical bounds contact rectangle across the bolt row')


def _candidate_contact_group(config, inventory, interface_id, probe):
    """Build WJ-04 geometry from canonical config and its bound probe area."""
    host_by_interface = {
        'rail_to_cleat': 'base_rail_service_lower_right',
        'principal_to_cleat': 'base_principal_center_right',
    }
    if interface_id not in host_by_interface:
        raise ValueError(f'Unknown WJ-04 interface: {interface_id}')
    if probe.get('trial_id') != config.trial_id:
        raise ValueError('Contact-area probe is not bound to the canonical WJ-04 trial ID')
    if probe.get('trial_config_sha256') != config.canonical_sha256:
        raise ValueError('Contact-area probe does not match canonical WJ-04 trial configuration hash')
    if probe.get('source_inventory_sha256') != config.source_inventory_sha256:
        raise ValueError('Contact-area probe does not match canonical source inventory hash')
    probe_producer_sha256 = probe.get('producer_sha256')
    if probe_producer_sha256 != _sha256(PROBE_PRODUCER_PATH):
        raise ValueError('Contact-area probe producer hash does not match current source')
    area_record = probe.get('contact_area_mm2', {}).get(interface_id)
    if not isinstance(area_record, (int, float)) or not math.isfinite(area_record) or area_record <= 0:
        raise ValueError(f'{interface_id} probe contact area must be positive and finite')
    finite_probe_area_mm2 = float(area_record)
    host_id = host_by_interface[interface_id]
    member_by_id = {member.member_id: member for member in config.members}
    if host_id not in member_by_id or 'wj04_cleat' not in member_by_id:
        raise ValueError(f'{interface_id} does not bind both canonical timber members')
    stacks = [stack for stack in config.stacks if stack.interface_id == interface_id]
    if len(stacks) != 2:
        raise ValueError(f'{interface_id} must have two canonical bolt stacks')

    points = tuple(config.axis_point_global(stack.stack_id) for stack in stacks)
    axes = tuple(config.axis_direction_global(stack.stack_id) for stack in stacks)
    if _dot(axes[0], axes[1]) < 1.0 - 1e-8:
        raise ValueError(f'{interface_id} bolt axes are not consistently directed')
    row = _unit(_sub(points[1], points[0]), f'{interface_id} bolt-row axis')
    center = _scale(0.5, _add(points[0], points[1]))

    source_host = next(row for row in inventory['parts'] if row['part_id'] == host_id)
    expected_faces = member_by_id[host_id].source_face_ids
    face_rows = [
        face for face in source_host['actual_planar_faces']
        if face['face_id'] in expected_faces
    ]
    matching_faces = [
        face for face in face_rows
        if abs(_dot(_unit(_vec(face['normal_global_xyz'], 'source face normal'),
                          'source face normal'), axes[0])) >= 1.0 - 1e-7
    ]
    if len(matching_faces) != 1:
        raise ValueError(
            f'{interface_id} requires one configured source face normal to the bolt axis'
        )
    face_record = matching_faces[0]
    normal = _unit(_vec(face_record['normal_global_xyz'], 'source face normal'),
                   'source face normal')
    face_center_source = _vec(face_record['center_global_xyz_mm'], 'source face center')

    cleat = config.cleat
    if cleat.size_x_t_n_mm is None or cleat.origin_x_t_n_mm is None:
        raise ValueError('Canonical WJ-04 cleat needs finite dimensions and origin')
    basis = (
        config.frame.x_global, config.frame.t_global, config.frame.n_global,
    )
    frame_origin = config.frame.origin_global_mm
    local_face_center = tuple(
        _dot(_sub(face_center_source, frame_origin), axis) for axis in basis
    )
    normal_axis_index = max(range(3), key=lambda index: abs(_dot(normal, basis[index])))
    if abs(abs(_dot(normal, basis[normal_axis_index])) - 1.0) > 1e-7:
        raise ValueError(f'{interface_id} contact normal is not a canonical X/T/N axis')
    origin = cleat.origin_x_t_n_mm
    size = cleat.size_x_t_n_mm
    cleat_bounds = tuple((origin[i], origin[i] + size[i]) for i in range(3))
    plane_coordinate = local_face_center[normal_axis_index]
    contact_bound_distances = tuple(
        abs(plane_coordinate - value) for value in cleat_bounds[normal_axis_index]
    )
    contact_bound_index = min(range(2), key=lambda index: contact_bound_distances[index])
    if contact_bound_distances[contact_bound_index] > STATIC_BALANCE_TOL:
        raise ValueError(f'{interface_id} source face and cleat contact plane do not meet')

    local_bounds = list(cleat_bounds)
    local_bounds[normal_axis_index] = (plane_coordinate, plane_coordinate)
    corners = [
        config.frame.to_global((x, t, n))
        for x in local_bounds[0]
        for t in local_bounds[1]
        for n in local_bounds[2]
    ]
    face_center = _scale(1.0 / len(corners), tuple(
        math.fsum(point[axis] for point in corners) for axis in range(3)
    ))
    transverse = _unit(_cross(row, normal), f'{interface_id} face transverse axis')
    center_on_face = _add(center, _scale(_dot(_sub(face_center, center), normal), normal))
    row_coordinates = [_dot(point, row) for point in corners]
    edge_coordinates = [_dot(point, transverse) for point in corners]
    row_bounds = (min(row_coordinates), max(row_coordinates))
    edge_bounds = (min(edge_coordinates), max(edge_coordinates))
    center_row = _dot(center_on_face, row)
    center_edge = _dot(center_on_face, transverse)
    _require_point_inside_contact_rectangle(
        center_on_face, face_center, normal, row, transverse,
        row_bounds, edge_bounds, f'{interface_id} bolt-row centroid projected to contact face',
    )
    edge_distances = {
        'negative': center_edge - edge_bounds[0],
        'positive': edge_bounds[1] - center_edge,
    }
    row_span = row_bounds[1] - row_bounds[0]
    edge_span = edge_bounds[1] - edge_bounds[0]
    bounding_rectangle_area_mm2 = row_span * edge_span
    area_delta_mm2 = finite_probe_area_mm2 - bounding_rectangle_area_mm2
    if min(edge_distances.values()) + TOL < CONTACT_EDGE_BAND_WIDTH_MM:
        raise ValueError(f'{interface_id} 10 mm witness band does not fit both contact edges')

    contact_face = {
        'group_centroid_projected_to_contact_face_global_xyz_mm': center_on_face,
        'face_center_global_xyz_mm': face_center,
        'edge_axis_global_xyz': transverse,
        'row_axis_global_xyz': row,
        'face_normal_global_xyz': normal,
        'edge_axis_coordinate_bounds_mm': edge_bounds,
        'row_axis_coordinate_bounds_mm': row_bounds,
        'bolt_row_centroid_row_axis_coordinate_mm': center_row,
        'bolt_row_centroid_within_canonical_bounds_rectangle': True,
        'edge_distances_from_bolt_row_centroid_mm': edge_distances,
        'row_span_mm': row_span,
        'finite_probe_contact_area_mm2': finite_probe_area_mm2,
        'finite_probe_area_measurement': {
            'source_field': f'active_probe.contact_area_mm2.{interface_id}',
            'method_id': CONTACT_AREA_METHOD_ID,
            'calculation': (
                'intersection volume of cleat translated inward into host, divided by the '
                'translation/probe depth'
            ),
            'probe_depth_mm': CONTACT_PROBE_DEPTH_MM,
            'probe_producer_sha256': probe_producer_sha256,
            'capacity_or_contact_pressure_calculated': False,
        },
        'canonical_bounds_rectangle_area_mm2': bounding_rectangle_area_mm2,
        'finite_probe_minus_rectangle_area_mm2': area_delta_mm2,
        'finite_probe_to_rectangle_area_ratio': finite_probe_area_mm2 / bounding_rectangle_area_mm2,
        'edge_band_width_mm': CONTACT_EDGE_BAND_WIDTH_MM,
        'edge_resultant_inset_mm': CONTACT_EDGE_RESULTANT_INSET_MM,
        'available_finite_band_levers_mm': {
            side: distance - CONTACT_EDGE_RESULTANT_INSET_MM
            for side, distance in edge_distances.items()
        },
        'both_signed_edge_bands_fit': True,
    }
    return {
        'interface_id': interface_id,
        'host_member_id': host_id,
        'cleat_member_id': 'wj04_cleat',
        'stack_ids': tuple(stack.stack_id for stack in stacks),
        'stack_points_global_xyz_mm': points,
        'stack_axes_global_xyz': axes,
        'stack_hardware_candidate_ids': tuple(
            stack.hardware_candidate.candidate_id for stack in stacks
        ),
        'stack_hardware_candidates': tuple({
            'candidate_id': stack.hardware_candidate.candidate_id,
            'manufacturer': stack.hardware_candidate.manufacturer,
            'sku': stack.hardware_candidate.sku,
            'thread': stack.hardware_candidate.thread,
            'grade_label': stack.hardware_candidate.grade,
            'nominal_length_mm': stack.hardware_candidate.nominal_length_mm,
            'minimum_smooth_body_mm': stack.hardware_candidate.minimum_smooth_body_mm,
            'maximum_full_thread_start_mm': stack.hardware_candidate.maximum_full_thread_start_mm,
            'status': stack.hardware_candidate.status,
        } for stack in stacks),
        'stack_nominal_bolt_lengths_mm': tuple(
            stack.hardware_candidate.nominal_length_mm for stack in stacks
        ),
        'stack_layers_head_to_nut': tuple(
            tuple({'member_id': layer.member_id, 'thickness_mm': layer.thickness_mm}
                  for layer in stack.layers)
            for stack in stacks
        ),
        'points_global_xyz_mm': points,
        'centroid_global_xyz_mm': center,
        'row_axis_global_xyz': row,
        'bolt_axis_global_xyz': axes[0],
        'face_normal_global_xyz': normal,
        'face_normal_source_face_id': face_record['face_id'],
        'spacing_mm': _norm(_sub(points[1], points[0])),
        'contact_face_geometry': contact_face,
    }


def _candidate_member_fastener_placement(config, inventory, group, member_id):
    """Report finished-member placement distances, never signed NDS verdicts."""
    member = next(row for row in config.members if row.member_id == member_id)
    grain_axis = _member_grain_global(config, member)
    if member_id == 'wj04_cleat':
        if member.size_x_t_n_mm is None or member.origin_x_t_n_mm is None:
            raise ValueError('Canonical cleat needs finite placement bounds')
        local_axes = {
            'X': config.frame.x_global,
            'T': config.frame.t_global,
            'N': config.frame.n_global,
        }
        lower = dict(zip(('X', 'T', 'N'), member.origin_x_t_n_mm, strict=True))
        upper = {
            name: lower[name] + extent
            for name, extent in zip(('X', 'T', 'N'), member.size_x_t_n_mm, strict=True)
        }
        source_geometry_status = 'canonical proposed cleat bounds; uncut/unbored dimensions'
        frame_origin = config.frame.origin_global_mm

        def point_coordinates(point):
            return {
                name: _dot(_sub(point, frame_origin), axis)
                for name, axis in local_axes.items()
            }

    else:
        part = next(row for row in inventory['parts'] if row['part_id'] == member_id)
        transform = part['local_to_global_transform']
        origin_global = tuple(float(transform[row][3]) for row in range(3))
        local_axes = {
            name: _unit(_vec(axis, f'{member_id} local {name} axis'), f'{member_id} local {name} axis')
            for name, axis in part['local_axes'].items()
        }
        extents = part['actual_shape_extents_local_mm']
        lower = {name: float(extents[name][0]) for name in ('X', 'T', 'N')}
        upper = {name: float(extents[name][1]) for name in ('X', 'T', 'N')}
        source_geometry_status = part['source_geometry_status']

        def point_coordinates(point):
            return {
                name: _dot(_sub(point, origin_global), axis)
                for name, axis in local_axes.items()
            }

    grain_local_candidates = [
        (name, _dot(axis, grain_axis)) for name, axis in local_axes.items()
    ]
    grain_name, grain_alignment = max(grain_local_candidates, key=lambda item: abs(item[1]))
    if abs(grain_alignment) < 1.0 - 1e-7:
        raise ValueError(f'{member_id} grain direction is not one source member axis')
    candidate = config.stack_by_id(group['stack_ids'][0]).hardware_candidate
    diameter_in_text = candidate.thread.split('-', maxsplit=1)[0]
    try:
        nominal_diameter_mm = float(Fraction(diameter_in_text)) * 25.4
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f'Cannot parse nominal bolt diameter from {candidate.thread}') from error

    stack_rows = []
    for stack_id, point in zip(group['stack_ids'], group['stack_points_global_xyz_mm'], strict=True):
        point_local = point_coordinates(point)
        bolt_axis = group['bolt_axis_global_xyz']
        bolt_axis_local = [abs(_dot(local_axes[name], bolt_axis)) for name in ('X', 'T', 'N')]
        normal_name = ('X', 'T', 'N')[max(range(3), key=lambda index: bolt_axis_local[index])]
        if bolt_axis_local[('X', 'T', 'N').index(normal_name)] < 1.0 - 1e-7:
            raise ValueError(f'{stack_id} bolt axis does not align with a finished member axis')
        axes = {}
        for name in ('X', 'T', 'N'):
            if name == normal_name:
                continue
            distance_low = point_local[name] - lower[name]
            distance_high = upper[name] - point_local[name]
            if min(distance_low, distance_high) < -STATIC_BALANCE_TOL:
                raise ValueError(f'{stack_id} centerline falls outside {member_id} {name} bounds')
            distances = {'negative': distance_low, 'positive': distance_high}
            axes[name] = {
                'axis_role': 'grain_end' if name == grain_name else 'lateral_edge',
                'distance_to_negative_boundary_mm': distance_low,
                'distance_to_positive_boundary_mm': distance_high,
                'conditional_4d_reserve_mm': {
                    side: value - 4.0 * nominal_diameter_mm
                    for side, value in distances.items()
                },
                'conditional_7d_reserve_mm': (
                    {
                        side: value - 7.0 * nominal_diameter_mm
                        for side, value in distances.items()
                    }
                    if name == grain_name else None
                ),
            }
        stack_rows.append({
            'stack_id': stack_id,
            'local_centerline_coordinates_mm': point_local,
            'bolt_normal_member_axis': normal_name,
            'grain_member_axis': grain_name,
            'grain_axis_signed_alignment_with_member_axis': grain_alignment,
            'placement_by_local_axis': axes,
        })
    return {
        'member_id': member_id,
        'grain_axis_global_xyz': grain_axis,
        'grain_local_axis': grain_name,
        'nominal_bolt_diameter_mm_from_catalog_thread': nominal_diameter_mm,
        'source_geometry_status': source_geometry_status,
        'stack_placement': stack_rows,
        'distance_status': 'placement_only_conditional_4d_7d_reserves_no_signed_load_or_NDS_classification',
    }


def _member_action_projection(force_global, moment_global, grain_axis, bolt_axis):
    """Signed material-axis components; caller labels old actions diagnostic."""
    grain_component = _dot(force_global, grain_axis)
    bolt_axis_component = _dot(force_global, bolt_axis)
    lateral = _sub(force_global, _scale(bolt_axis_component, bolt_axis))
    cross_grain = _sub(force_global, _scale(grain_component, grain_axis))
    return {
        'force_global_xyz_n': force_global,
        'moment_global_xyz_nmm': moment_global,
        'grain_axis_global_xyz': grain_axis,
        'force_parallel_to_grain_signed_n': grain_component,
        'force_perpendicular_to_grain_global_xyz_n': cross_grain,
        'force_perpendicular_to_grain_magnitude_n': _norm(cross_grain),
        'force_along_bolt_axis_signed_n': bolt_axis_component,
        'bolt_lateral_force_global_xyz_n': lateral,
        'bolt_lateral_force_magnitude_n': _norm(lateral),
        'force_sign_interpretation': 'signed component only; end/edge category needs local per-fastener load direction',
    }


def _candidate_material_axes(config, inventory, groups):
    members = {member.member_id: member for member in config.members}
    output = {}
    for member_id in ('base_rail_service_lower_right', 'base_principal_center_right', 'wj04_cleat'):
        member = members[member_id]
        axis = _member_grain_global(config, member)
        inventory_axis = None
        if member.source_part_id is not None:
            source = next(row for row in inventory['parts'] if row['part_id'] == member.source_part_id)
            inventory_axis = _unit(_vec(source['grain_axis_global_xyz'], 'inventory grain axis'),
                                   'inventory grain axis')
            if _dot(axis, inventory_axis) < 1.0 - 1e-7:
                raise ValueError(f'{member_id} canonical grain axis disagrees with source inventory')
        output[member_id] = {
            'configured_grain_axis_name': member.grain_axis,
            'grain_axis_global_xyz': axis,
            'source_inventory_grain_axis_global_xyz': inventory_axis,
            'grain_axis_matches_source_inventory': None if inventory_axis is None else True,
            'stock_grade_verified': config.stock_grade_verified if member.role == 'cleat' else (
                next(row for row in inventory['parts'] if row['part_id'] == member.source_part_id)
                .get('delivered_stock_observed', False)
            ),
        }
    for group in groups.values():
        group['material_axes'] = {
            side: {
                **output[member_id],
                'bolt_axis_global_xyz': group['bolt_axis_global_xyz'],
                'face_normal_global_xyz': group['face_normal_global_xyz'],
                'bolt_axis_parallel_to_grain': abs(_dot(
                    output[member_id]['grain_axis_global_xyz'], group['bolt_axis_global_xyz'],
                )) >= 1.0 - 1e-7,
            }
            for side, member_id in (('host', group['host_member_id']),
                                    ('cleat', group['cleat_member_id']))
        }
    return output


def _complete_joint_capacity_status(config, groups):
    """Record minimum full-joint gates without turning diagnostic actions into demand."""
    return {
        'status': 'UNRESOLVED_DEMAND',
        'disposition': 'revise_named_constraint',
        'complete_bounded_joint_capacity_feasible_now': False,
        'known_candidate_geometry': {
            'cleat_size_x_t_n_mm': config.cleat.size_x_t_n_mm,
            'cleat_origin_x_t_n_mm': config.cleat.origin_x_t_n_mm,
            'interfaces': {
                name: {
                    'interface_id': group['interface_id'],
                    'stack_ids': group['stack_ids'],
                    'stack_points_global_xyz_mm': group['stack_points_global_xyz_mm'],
                    'stack_axes_global_xyz': group['stack_axes_global_xyz'],
                    'nominal_bolt_length_mm': group['stack_nominal_bolt_lengths_mm'],
                    'stack_layers_head_to_nut': group['stack_layers_head_to_nut'],
                    'hardware_candidate_records': group['stack_hardware_candidates'],
                    'material_axes': group.get('material_axes', {}),
                    'finite_probe_contact_area_mm2': group['contact_face_geometry'][
                        'finite_probe_contact_area_mm2'
                    ],
                    'canonical_bounds_rectangle_area_mm2': group['contact_face_geometry'][
                        'canonical_bounds_rectangle_area_mm2'
                    ],
                    'finite_probe_minus_rectangle_area_mm2': group['contact_face_geometry'][
                        'finite_probe_minus_rectangle_area_mm2'
                    ],
                    'contact_edge_distances_mm': group['contact_face_geometry'][
                        'edge_distances_from_bolt_row_centroid_mm'
                    ],
                    'placement_geometry_by_member': group.get('placement_geometry_by_member', {}),
                }
                for name, group in groups.items()
            },
        },
        'reusable_component_reference_functions': [
            {
                'function': 'mini_moonboard.bolted_wood_wood_yield.wood_wood_single_shear_reference',
                'role': 'six unadjusted one-bolt lateral-yield modes for contacting two-solid-wood single shear',
                'current_use': 'conditional component reference only; WJ-04 Fyb, delivered D/Dr/thread bearing, signed bolt shear, gaps, and adjustments are unresolved',
            },
            {
                'functions': [
                    'mini_moonboard.bolted_timber_checks.dfl_dowel_bearing_psi',
                    'mini_moonboard.bolted_timber_checks.dfl_net_parallel_tension_reference_lbf',
                    'mini_moonboard.bolted_timber_checks.dfl_parallel_row_tear_out_reference_lbf',
                    'mini_moonboard.bolted_timber_checks.dfl_parallel_group_tear_out_reference_lbf',
                    'mini_moonboard.bolted_timber_checks.dfl_axial_wood_bearing_reference_lbf',
                ],
                'role': 'constituent DF-L wood bearing/net/parallel-grain tear-out/ideal washer-annulus references',
                'current_use': 'each needs caller-selected applicability, actual geometry, current signed demand, and adjustments; none is a complete joint capacity',
            },
            {
                'functions': [
                    'mini_moonboard.wood_joint_bolt_resistance.nds_effective_bolt_diameter_in',
                    'mini_moonboard.wood_joint_bolt_resistance.nds_fyb_basis_status',
                    'mini_moonboard.wood_joint_bolt_resistance.bolt_first_yield_reference',
                    'mini_moonboard.wood_joint_bolt_resistance.wood_washer_annulus_reference_lbf',
                    'mini_moonboard.wood_joint_bolt_resistance.washer_steel_resistance_status',
                ],
                'role': 'metal D/Dr, Fyb evidence, separate bolt first-yield references, and conditional washer wood-side reference',
                'current_use': 'Fyb, delivered product properties, per-fastener actions, washer plate/spread, and tension/shear interaction remain unresolved',
            },
            {
                'function': 'scripts.wood_joint_wj04_early_mechanics._contact_supported_group_wrench',
                'role': 'finite contact-band static equilibrium witness',
                'current_use': 'not contact pressure, contact stiffness, or compression resistance',
            },
        ],
        'limit_state_methods': [
            {
                'method_id': 'fresh_same_case_interface_actions',
                'status': 'UNRESOLVED_DEMAND',
                'required_basis': 'new six-case candidate solve with signed member-side wrenches and an evidenced contact/load-sharing model',
                'missing': [
                    'current candidate demands; old selected-candidate angle wrenches are provenance-preserved diagnostics only',
                    'stiffness/contact model to resolve per-fastener lateral and axial actions without assumed equal sharing',
                ],
            },
            {
                'method_id': 'wood_bearing_end_edge_group_net_section_splitting',
                'status': 'UNRESOLVED_GEOMETRY_MATERIAL_DEMAND',
                'reference': 'ANSI/AWC NDS-2024 §§12.3, 12.5, Appendix E.2–E.4; Appendix E is parallel-grain net/tear-out only',
                'missing': [
                    'signed current per-fastener lateral vectors on each member and applicable NDS loaded-edge/end category',
                    'delivered bore diameters, exact bore/cut geometry, neighboring holes, and finished member section boundaries',
                    'cross-grain splitting method and applicability basis separate from Appendix E',
                    'verified delivered species/grade/moisture and NDS design-value adjustment inputs',
                ],
            },
            {
                'method_id': 'bolt_lateral_yield_and_bending',
                'status': 'UNRESOLVED_MATERIAL_DEMAND',
                'reference': 'ANSI/AWC NDS-2024 §§12.3.1, 12.3.3–12.3.7 and applicable Table 12.3.1B errata',
                'missing': [
                    'current per-fastener lateral demand and zero-gap/contact applicability for both wood/wood single-shear interfaces',
                    'delivered full-body and thread-root diameters plus thread-bearing lengths in each wood layer',
                    'delivered-bolt Fyb supported by applicable ASTM F1575/F606 evidence; grade label alone does not set Fyb',
                    'applicable NDS adjustment factors and complete group/spacing checks',
                ],
            },
            {
                'method_id': 'bolt_steel_tension_shear_interaction',
                'status': 'UNRESOLVED_MATERIAL_DEMAND_METHOD',
                'missing': [
                    'certified minimum bolt yield strength and controlling tensile area',
                    'actual shank/thread shear-plane area for each installed stack',
                    'same-bolt signed axial and lateral demand',
                    'adopted tension/shear interaction rule applicable to this joint',
                ],
            },
            {
                'method_id': 'washer_bearing_and_plate_spread',
                'status': 'UNRESOLVED_MATERIAL_GEOMETRY_DEMAND',
                'known_conditional_reference': 'DF-L Fc-perp washer-annulus expression is a wood-side reference only when full stiff washer contact is proven',
                'missing': [
                    'verified washer seat fit on actual finished wood around each delivered bore',
                    'washer plate bending/spread capacity and local wood crushing/pull-through method',
                    'washer/nut/bolt delivered dimensions, material properties, and actual axial demand',
                ],
            },
            {
                'method_id': 'unilateral_contact_pressure_opening',
                'status': 'GEOMETRY_WITNESS_ONLY',
                'known': 'finite face rectangles derive from source host face and canonical cleat dimensions; old 10 mm edge-band equilibrium is statics witness',
                'missing': [
                    'pressure distribution and contact stiffness on both wood sides',
                    'opening extent, fit/gap, local Fc-perp design resistance, and coupled bolt tension',
                ],
            },
            {
                'method_id': 'cleat_internal_transfer_and_section',
                'status': 'UNRESOLVED_GEOMETRY_DEMAND_MATERIAL',
                'missing': [
                    'complete cut/hole/defect geometry and finished-section checks at every critical cleat cut',
                    'same-case coupled force and all moment components at cleat datum',
                    'verified cleat grade/species and adjusted material design values',
                    'cross-grain splitting/block-shear method and applicability',
                ],
            },
            {
                'method_id': 'complete_joint_capacity_envelope',
                'status': 'UNRESOLVED',
                'required_components': [
                    'rail and principal wood bearing/yield, loaded end/edge, net section, tear-out and splitting',
                    'each bolt lateral bending/shear, axial tension, and adopted simultaneous interaction',
                    'washer wood bearing plus washer plate distribution',
                    'unilateral contact pressure/opening and local compression perpendicular to grain',
                    'cleat internal transfer through all finished sections and both interfaces',
                    'governing same-case minimum resistance with matching signed demand',
                ],
                'missing': ['all component dispositions above on one fresh, source-bound candidate demand set'],
            },
        ],
        'source_limits': [
            'Catalog dimensional candidates and source-model stock grades are not delivered-part verification.',
            'The active WJ-04 probe and old selected-candidate action ledger establish neither complete-joint capacity nor fresh same-candidate demand.',
        ],
        'official_sources': [
            'https://awc.org/resources/2024-nds/',
            'https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf',
            'https://awc.org/resources/2024-nds-supplement/',
        ],
    }


def _point_group_resultant(force_on_host, moment_on_host, group):
    """Minimum-norm force-only equilibrium at two rigid point fasteners.

    A two-point force group cannot resist the moment component parallel to its
    bolt row. The returned pair balances the other five wrench components.
    """
    row = group['row_axis_global_xyz']
    distance = group['spacing_mm']
    residual_moment = _scale(_dot(moment_on_host, row), row)
    resolved_moment = _sub(moment_on_host, residual_moment)
    couple_force = _scale(1.0 / distance, _cross(row, resolved_moment))
    half_force = _scale(0.5, force_on_host)
    forces = (_add(half_force, couple_force), _sub(half_force, couple_force))
    points = group['points_global_xyz_mm']
    center = group['centroid_global_xyz_mm']
    actual_force = _add(forces[0], forces[1])
    actual_moment = _add(
        _cross(_sub(points[0], center), forces[0]),
        _cross(_sub(points[1], center), forces[1]),
    )
    if _norm(_sub(actual_force, force_on_host)) > 1.0e-6:
        raise ArithmeticError('Two-point force reconstruction failed force closure')
    if _norm(_sub(actual_moment, resolved_moment)) > 1.0e-6:
        raise ArithmeticError('Two-point force reconstruction failed moment closure')
    bolt_axis = group['bolt_axis_global_xyz']
    axial = tuple(_dot(force, bolt_axis) for force in forces)
    shear = tuple(_sub(force, _scale(_dot(force, bolt_axis), bolt_axis)) for force in forces)
    return {
        'model': 'two rigid point fasteners; minimum-norm 3D force split; no contact or bolt moments',
        'force_on_host_global_xyz_n': force_on_host,
        'moment_on_host_at_group_centroid_global_xyz_nmm': moment_on_host,
        'bolt_force_resultants_on_host_global_xyz_n': forces,
        'bolt_force_resultant_norms_n': tuple(_norm(force) for force in forces),
        'bolt_axis_components_n': axial,
        'bolt_transverse_force_vectors_on_host_global_xyz_n': shear,
        'bolt_transverse_resultant_norms_n': tuple(_norm(force) for force in shear),
        'bolt_row_unresolved_moment_global_xyz_nmm': residual_moment,
        'bolt_row_unresolved_moment_nmm': _norm(residual_moment),
        'full_wrench_balanced_by_two_point_forces': _norm(residual_moment) <= 1.0e-6,
    }


def _contact_supported_group_wrench(force_on_host, moment_on_host, group):
    """Close the rigid two-bolt wrench with bolt tension and face compression.

    This is a statics witness only. It moves any compressive axial point force
    from the bolt to face contact, then balances the row-axis moment with an
    equal tension/contact compression couple across the actual face depth.
    It assigns no stiffness, pressure distribution, or resistance.
    """
    point_group = _point_group_resultant(force_on_host, moment_on_host, group)
    normal = group['face_normal_global_xyz']
    row = group['row_axis_global_xyz']
    face = group['contact_face_geometry']
    transverse = face['edge_axis_global_xyz']
    points = group['points_global_xyz_mm']
    center = group['centroid_global_xyz_mm']
    bolt_axis = group['bolt_axis_global_xyz']

    bolt_forces = []
    bolt_rows = []
    contact_forces = []
    for index, (point, point_force, axial) in enumerate(zip(
        points,
        point_group['bolt_force_resultants_on_host_global_xyz_n'],
        point_group['bolt_axis_components_n'],
        strict=True,
    ), start=1):
        tension_sign = 1.0 if _dot(bolt_axis, normal) > 0 else -1.0
        signed_tension = axial * tension_sign
        tension = max(0.0, signed_tension)
        compression = max(0.0, -signed_tension)
        shear = _sub(point_force, _scale(_dot(point_force, normal), normal))
        bolt_force = _add(shear, _scale(tension, normal))
        bolt_forces.append(bolt_force)
        if compression > TOL:
            contact_forces.append({
                'source': f'bolt_{index}_compression_bearing',
                'point_global_xyz_mm': point,
                'force_global_xyz_n': _scale(-compression, normal),
                'magnitude_n': compression,
            })
        bolt_rows.append({
            'bolt_index': index,
            'raw_axial_resultant_n_along_axis': axial,
            'tension_before_row_moment_couple_n': tension,
            'compression_transferred_to_face_contact_n': compression,
            'transverse_shear_resultant_n': _norm(shear),
        })

    row_moment = _dot(moment_on_host, row)
    if abs(row_moment) > TOL:
        edge_key = 'positive' if row_moment > 0 else 'negative'
        edge_distances = face['edge_distances_from_bolt_row_centroid_mm']
        edge_distance = float(edge_distances[edge_key])
        band_width = CONTACT_EDGE_BAND_WIDTH_MM
        inset = CONTACT_EDGE_RESULTANT_INSET_MM
        if not math.isfinite(edge_distance) or edge_distance + TOL < band_width:
            raise ValueError(
                f'10 mm contact band does not fit selected {edge_key} face edge distance'
            )
        lever = edge_distance - inset
        if not math.isfinite(lever) or lever <= 0:
            raise ValueError('finite contact-band resultant lever must be positive and finite')
        couple_force = abs(row_moment) / lever
        zero_area_edge_force = abs(row_moment) / edge_distance
        for index in range(len(bolt_forces)):
            bolt_forces[index] = _add(
                bolt_forces[index], _scale(couple_force / len(bolt_forces), normal)
            )
        edge_low, edge_high = face['edge_axis_coordinate_bounds_mm']
        face_group_center = face['group_centroid_projected_to_contact_face_global_xyz_mm']
        center_edge_coordinate = _dot(face_group_center, transverse)
        contact_edge_coordinate = edge_high if edge_key == 'positive' else edge_low
        band_bounds = (
            (edge_high - band_width, edge_high)
            if edge_key == 'positive'
            else (edge_low, edge_low + band_width)
        )
        band_resultant_coordinate = (
            edge_high - inset if edge_key == 'positive' else edge_low + inset
        )
        band_resultant_inset = abs(contact_edge_coordinate - band_resultant_coordinate)
        contact_point = _add(
            face_group_center,
            _scale(band_resultant_coordinate - center_edge_coordinate, transverse),
        )
        band_force = _scale(-couple_force, normal)
        couple_moment = _cross(_sub(contact_point, center), band_force)
        row_closure = _dot(couple_moment, row)
        if not math.isclose(row_closure, row_moment, rel_tol=1.0e-10, abs_tol=STATIC_BALANCE_TOL):
            raise ArithmeticError('Finite contact-band couple does not close the signed row moment')
        if not math.isclose(band_resultant_inset, inset, rel_tol=0.0, abs_tol=TOL):
            raise ArithmeticError('Finite contact resultant is not at the specified edge inset')
        if not math.isclose(
            _dot(_sub(contact_point, face['face_center_global_xyz_mm']), normal),
            0.0,
            rel_tol=0.0,
            abs_tol=STATIC_BALANCE_TOL,
        ):
            raise ArithmeticError('Finite contact resultant does not lie on the actual face plane')
        _require_point_inside_contact_rectangle(
            contact_point,
            face['face_center_global_xyz_mm'],
            normal,
            row,
            transverse,
            face['row_axis_coordinate_bounds_mm'],
            face['edge_axis_coordinate_bounds_mm'],
            'Finite contact-band resultant',
        )
        contact_forces.append({
            'source': 'row_axis_moment_face_compression_couple',
            'point_global_xyz_mm': contact_point,
            'force_global_xyz_n': band_force,
            'magnitude_n': couple_force,
            'edge_side': edge_key,
            'edge_band_width_mm': band_width,
            'resultant_inset_from_edge_mm': inset,
            'actual_face_edge_distance_mm': edge_distance,
            'lever_arm_mm': lever,
            'zero_area_edge_resultant_upper_bound_lever_mm': edge_distance,
            'zero_area_edge_resultant_force_n': zero_area_edge_force,
            'finite_band_couple_force_n': couple_force,
            'finite_band_force_increase_n': couple_force - zero_area_edge_force,
            'finite_band_force_increase_ratio': couple_force / zero_area_edge_force,
            'contact_band_area_mm2': band_width * face['row_span_mm'],
            'contact_band_edge_axis_coordinate_bounds_mm': band_bounds,
            'contact_band_resultant_edge_axis_coordinate_mm': band_resultant_coordinate,
            'contact_band_resultant_row_axis_coordinate_mm': _dot(contact_point, row),
            'contact_band_fits_actual_face': True,
            'contact_band_resultant_within_actual_face_rectangle': True,
            'finite_contact_resultant_lies_in_face': True,
            'couple_moment_on_host_global_xyz_nmm': couple_moment,
        })
    else:
        edge_key = None
        lever = None
        couple_force = 0.0

    for row_index, row_result in enumerate(bolt_rows):
        row_result['tension_after_row_moment_couple_n'] = max(
            0.0, _dot(bolt_forces[row_index], normal),
        )

    total_force = (0.0, 0.0, 0.0)
    total_moment = (0.0, 0.0, 0.0)
    for point, force in zip(points, bolt_forces, strict=True):
        total_force = _add(total_force, force)
        total_moment = _add(total_moment, _cross(_sub(point, center), force))
    for item in contact_forces:
        point = item['point_global_xyz_mm']
        force = item['force_global_xyz_n']
        total_force = _add(total_force, force)
        total_moment = _add(total_moment, _cross(_sub(point, center), force))
    force_residual = _sub(total_force, force_on_host)
    moment_residual = _sub(total_moment, moment_on_host)
    row_contact = next(
        (item for item in contact_forces
         if item['source'] == 'row_axis_moment_face_compression_couple'),
        None,
    )
    return {
        'model': 'two tension-capable bolts plus compression-only face-contact resultants; rigid statics witness',
        'raw_two_point_group': point_group,
        'bolt_forces_on_host_global_xyz_n': bolt_forces,
        'bolt_rows': bolt_rows,
        'contact_compression_resultants': contact_forces,
        'row_axis_moment_path': {
            'axis_global_xyz': row,
            'moment_demand_nmm': row_moment,
            'contact_transverse_axis_global_xyz': transverse,
            'contact_edge_side': edge_key,
            'available_edge_lever_arm_mm': lever,
            'equal_bolt_tension_addition_total_n': couple_force,
            'face_contact_compression_for_couple_n': couple_force,
            'edge_band_width_mm': CONTACT_EDGE_BAND_WIDTH_MM if row_contact else None,
            'resultant_inset_from_edge_mm': CONTACT_EDGE_RESULTANT_INSET_MM if row_contact else None,
            'actual_face_edge_distance_mm': (
                row_contact['actual_face_edge_distance_mm'] if row_contact else None
            ),
            'zero_area_edge_resultant_upper_bound_lever_mm': (
                row_contact['zero_area_edge_resultant_upper_bound_lever_mm'] if row_contact else None
            ),
            'zero_area_edge_resultant_force_n': (
                row_contact['zero_area_edge_resultant_force_n'] if row_contact else None
            ),
            'finite_band_couple_force_n': (
                row_contact['finite_band_couple_force_n'] if row_contact else None
            ),
            'finite_band_force_increase_n': (
                row_contact['finite_band_force_increase_n'] if row_contact else None
            ),
            'finite_band_force_increase_ratio': (
                row_contact['finite_band_force_increase_ratio'] if row_contact else None
            ),
            'contact_band_area_mm2': row_contact['contact_band_area_mm2'] if row_contact else None,
            'contact_band_edge_axis_coordinate_bounds_mm': (
                row_contact['contact_band_edge_axis_coordinate_bounds_mm'] if row_contact else None
            ),
            'contact_band_resultant_edge_axis_coordinate_mm': (
                row_contact['contact_band_resultant_edge_axis_coordinate_mm'] if row_contact else None
            ),
            'resolved_by_face_contact_resultant': True,
        },
        'force_residual_global_xyz_n': force_residual,
        'moment_residual_global_xyz_nmm': moment_residual,
        'force_residual_norm_n': _norm(force_residual),
        'moment_residual_norm_nmm': _norm(moment_residual),
        'full_wrench_balanced_by_bolts_and_contact': (
            _norm(force_residual) <= STATIC_BALANCE_TOL
            and _norm(moment_residual) <= STATIC_BALANCE_TOL
        ),
        'capacity_or_contact_pressure_calculated': False,
    }


def build_report():
    demand = _read(DEMAND_PATH)
    inventory = _read(INVENTORY_PATH)
    probe = _read(PROBE_PATH)
    config = WJ04_TRIAL
    validate_wj04_trial(config)
    if demand.get('candidate') != inventory.get('source_candidate'):
        raise ValueError('Old action ledger is not bound to the inventory source candidate')
    if demand.get('status') != 'AUDITED_ANGLE_DEMAND_LEDGER_ONLY':
        raise ValueError('Unexpected old action ledger status')
    if tuple(demand.get('case_order', ())) != EXPECTED_CASES:
        raise ValueError('Old ledger case IDs do not match the frozen six-case order')
    if probe.get('station') != STATION:
        raise ValueError('WJ-04 probe station changed')
    if probe.get('trial_id') != config.trial_id:
        raise ValueError('Active WJ-04 probe is not bound to canonical trial ID')
    if probe.get('trial_config_sha256') != config.canonical_sha256:
        raise ValueError('Active WJ-04 probe does not match canonical trial configuration hash')
    inventory_sha = _sha256(INVENTORY_PATH)
    if inventory_sha != config.source_inventory_sha256:
        raise ValueError('Canonical WJ-04 config does not match current source inventory hash')

    duty = next(row for row in inventory['legacy_duties']
                if row['legacy_station_id'] == STATION)
    if duty['legacy_host_members'] != [
        'base_rail_service_lower_right', 'base_principal_center_right',
    ]:
        raise ValueError('WJ-04 source host identity/order changed')
    if len(duty['legacy_sds_axes']) != 6:
        raise ValueError('Expected the six source SDS axes at the reference station')

    basis = (config.frame.x_global, config.frame.t_global, config.frame.n_global)
    contract = inventory['coordinate_contract']
    axis_names = tuple(contract['basis_order'])
    if axis_names != ('X', 'T', 'N'):
        raise ValueError('Unexpected local action basis')
    inventory_basis = tuple(
        _unit(_vec(axis, 'source basis axis'), 'source basis axis')
        for axis in contract['basis_columns_global_xyz']
    )
    for canonical_axis, source_axis in zip(basis, inventory_basis, strict=True):
        _close_vectors(canonical_axis, source_axis, 'Canonical WJ-04 frame basis')
    groups = {
        'rail': _candidate_contact_group(config, inventory, 'rail_to_cleat', probe),
        'principal': _candidate_contact_group(config, inventory, 'principal_to_cleat', probe),
    }
    for group in groups.values():
        group['placement_geometry_by_member'] = {
            member_id: _candidate_member_fastener_placement(
                config, inventory, group, member_id,
            )
            for member_id in (group['host_member_id'], group['cleat_member_id'])
        }
    material_axes = _candidate_material_axes(config, inventory, groups)
    interfaces = {
        'rail': {
            'member_id': 'base_rail_service_lower_right',
            'old_flange': 'beam',
            'interface_id': 'rail_to_cleat',
            'group': groups['rail'],
        },
        'principal': {
            'member_id': 'base_principal_center_right',
            'old_flange': 'upright',
            'interface_id': 'principal_to_cleat',
            'group': groups['principal'],
        },
    }
    per_case = []
    for case_id in EXPECTED_CASES:
        case = demand['cases'][case_id]
        if case.get('current_sources_checked') is not False or case.get('native_solver_replayed') is not False:
            raise ValueError(f'{case_id} is not marked as a historical diagnostic source')
        station_data = case['angles'][STATION]
        origin = _vec(station_data['origin_mm'], f'{case_id} station origin')
        native_station = case['native_station_geometry'][STATION]
        _close_vectors(origin, _vec(native_station['origin'], f'{case_id} native origin'),
                       f'{case_id} origin')
        if native_station.get('members') != duty['legacy_host_members']:
            raise ValueError(f'{case_id} old action host mapping changed')
        case_interfaces = {}
        for interface_name, interface_config in interfaces.items():
            old = station_data['flanges'][interface_config['old_flange']]
            old_force = _vec(old['force_xyz_n'], f'{case_id}.{interface_config["old_flange"]}.force')
            old_moment = _vec(old['moment_xyz_nmm'], f'{case_id}.{interface_config["old_flange"]}.moment')
            centroid = interface_config['group']['centroid_global_xyz_mm']
            old_moment_at_group = _add(old_moment, _cross(_sub(origin, centroid), old_force))
            replacement_force_on_host = _scale(-1.0, old_force)
            replacement_moment_on_host = _scale(-1.0, old_moment_at_group)
            face_normal = interface_config['group']['face_normal_global_xyz']
            point_group = _point_group_resultant(
                replacement_force_on_host, replacement_moment_on_host, interface_config['group'],
            )
            contact_path = _contact_supported_group_wrench(
                replacement_force_on_host, replacement_moment_on_host, interface_config['group'],
            )
            host_grain = material_axes[interface_config['member_id']]['grain_axis_global_xyz']
            cleat_grain = material_axes['wj04_cleat']['grain_axis_global_xyz']
            host_action = _member_action_projection(
                replacement_force_on_host, replacement_moment_on_host,
                host_grain, interface_config['group']['bolt_axis_global_xyz'],
            )
            cleat_action = _member_action_projection(
                _scale(-1.0, replacement_force_on_host),
                _scale(-1.0, replacement_moment_on_host),
                cleat_grain, interface_config['group']['bolt_axis_global_xyz'],
            )
            host_fastener_lateral = point_group[
                'bolt_transverse_force_vectors_on_host_global_xyz_n'
            ]
            cleat_fastener_lateral = tuple(_scale(-1.0, vector)
                                           for vector in host_fastener_lateral)
            case_interfaces[interface_name] = {
                'interface_id': interface_config['interface_id'],
                'member_id': interface_config['member_id'],
                'legacy_flange': interface_config['old_flange'],
                'group_stack_ids': interface_config['group']['stack_ids'],
                'group_centroid_global_xyz_mm': centroid,
                'source_station_origin_global_xyz_mm': origin,
                'legacy_member_on_bracket_force_global_xyz_n': old_force,
                'legacy_member_on_bracket_moment_at_station_origin_global_xyz_nmm': old_moment,
                'legacy_member_on_bracket_force_local_XTN_n': _project(old_force, basis),
                'legacy_member_on_bracket_moment_at_group_centroid_global_xyz_nmm': old_moment_at_group,
                'legacy_member_on_bracket_moment_at_group_centroid_local_XTN_nmm': _project(
                    old_moment_at_group, basis,
                ),
                'replacement_connector_on_host_force_global_xyz_n': replacement_force_on_host,
                'replacement_connector_on_host_force_local_XTN_n': _project(
                    replacement_force_on_host, basis,
                ),
                'replacement_connector_on_host_moment_at_group_centroid_global_xyz_nmm':
                    replacement_moment_on_host,
                'replacement_connector_on_host_moment_at_group_centroid_local_XTN_nmm':
                    _project(replacement_moment_on_host, basis),
                'legacy_member_on_bracket_face_normal_force_n': _dot(old_force, face_normal),
                'replacement_connector_on_host_face_normal_force_n':
                    _dot(replacement_force_on_host, face_normal),
                'legacy_action_indicates_separation': _dot(old_force, face_normal) < -TOL,
                'two_bolt_point_group': point_group,
                'bolt_tension_and_face_contact_static_path': contact_path,
                'old_action_signed_material_projections': {
                    'status': 'diagnostic_only_not_candidate_demand',
                    'host': host_action,
                    'cleat': cleat_action,
                    'per_fastener_lateral_split': {
                        'status': 'minimum_norm_statics_witness_only_no_load_sharing_basis',
                        'host': [
                            _member_action_projection(
                                vector, (0.0, 0.0, 0.0), host_grain,
                                interface_config['group']['bolt_axis_global_xyz'],
                            )
                            for vector in host_fastener_lateral
                        ],
                        'cleat': [
                            _member_action_projection(
                                vector, (0.0, 0.0, 0.0), cleat_grain,
                                interface_config['group']['bolt_axis_global_xyz'],
                            )
                            for vector in cleat_fastener_lateral
                        ],
                        'NDS_end_edge_applicability': 'UNRESOLVED_DEMAND',
                    },
                },
            }
        per_case.append({
            'case_id': case_id,
            'native_report_sha256': case['native_report_sha256'],
            'assessment_input_sha256': case['assessment_input_sha256'],
            'current_sources_checked': case['current_sources_checked'],
            'native_solver_replayed': case['native_solver_replayed'],
            'assessment_resistance_recomputed': case['assessment_resistance_recomputed'],
            'interfaces': case_interfaces,
        })

    summary = {}
    for name, interface_config in interfaces.items():
        rows = [case['interfaces'][name] for case in per_case]
        normals = [row['legacy_member_on_bracket_face_normal_force_n'] for row in rows]
        point = [row['two_bolt_point_group'] for row in rows]
        contact_paths = [row['bolt_tension_and_face_contact_static_path'] for row in rows]
        summary[name] = {
            'interface_id': interface_config['interface_id'],
            'member_id': interface_config['member_id'],
            'group_stack_ids': interface_config['group']['stack_ids'],
            'centroid_global_xyz_mm': interface_config['group']['centroid_global_xyz_mm'],
            'face_normal_global_xyz': interface_config['group']['face_normal_global_xyz'],
            'bolt_axis_global_xyz': interface_config['group']['bolt_axis_global_xyz'],
            'bolt_row_axis_global_xyz': interface_config['group']['row_axis_global_xyz'],
            'bolt_spacing_mm': interface_config['group']['spacing_mm'],
            'stack_points_global_xyz_mm': interface_config['group']['stack_points_global_xyz_mm'],
            'stack_axes_global_xyz': interface_config['group']['stack_axes_global_xyz'],
            'stack_hardware_candidate_ids': interface_config['group']['stack_hardware_candidate_ids'],
            'stack_hardware_candidates': interface_config['group']['stack_hardware_candidates'],
            'stack_nominal_bolt_lengths_mm': interface_config['group']['stack_nominal_bolt_lengths_mm'],
            'stack_layers_head_to_nut': interface_config['group']['stack_layers_head_to_nut'],
            'material_axes': interface_config['group']['material_axes'],
            'placement_geometry_by_member': interface_config['group']['placement_geometry_by_member'],
            'contact_face_geometry': interface_config['group']['contact_face_geometry'],
            'finite_probe_contact_area_mm2': interface_config['group']['contact_face_geometry'][
                'finite_probe_contact_area_mm2'
            ],
            'canonical_bounds_rectangle_area_mm2': interface_config['group']['contact_face_geometry'][
                'canonical_bounds_rectangle_area_mm2'
            ],
            'finite_probe_minus_rectangle_area_mm2': interface_config['group']['contact_face_geometry'][
                'finite_probe_minus_rectangle_area_mm2'
            ],
            'legacy_member_on_bracket_normal_force_range_n': [min(normals), max(normals)],
            'separation_indicated_case_ids': [
                case['case_id'] for case, row in zip(per_case, rows, strict=True)
                if row['legacy_action_indicates_separation']
            ],
            'max_raw_two_point_bolt_force_resultant_n': max(
                max(group['bolt_force_resultant_norms_n']) for group in point
            ),
            'max_raw_two_point_row_moment_nmm_resolved_by_contact': max(
                group['bolt_row_unresolved_moment_nmm'] for group in point
            ),
            'max_bolt_tension_after_contact_couple_n': max(
                bolt['tension_after_row_moment_couple_n']
                for path in contact_paths
                for bolt in path['bolt_rows']
            ),
            'max_face_contact_compression_resultant_n': max(
                item['magnitude_n']
                for path in contact_paths
                for item in path['contact_compression_resultants']
            ),
            'max_force_equilibrium_residual_n': max(
                path['force_residual_norm_n'] for path in contact_paths
            ),
            'max_moment_equilibrium_residual_nmm': max(
                path['moment_residual_norm_nmm'] for path in contact_paths
            ),
            'all_six_full_wrenches_statically_balanced': all(
                path['full_wrench_balanced_by_bolts_and_contact']
                for path in contact_paths
            ),
        }

    hashes = {
        str(path.relative_to(ROOT)): _sha256(path)
        for path in (
            DEMAND_PATH, INVENTORY_PATH, PROBE_PATH, PROBE_PRODUCER_PATH,
            CONFIG_PATH, Path(__file__).resolve(),
        )
    }
    staleness = _staleness_audit(demand, inventory, probe)
    return _round({
        'schema': 'wood_joint_wj04_early_mechanics/v3',
        'status': 'diagnostic_only_no_acceptance',
        'candidate': inventory['candidate'],
        'source_candidate_for_actions': demand['candidate'],
        'station': STATION,
        'case_ids': list(EXPECTED_CASES),
        'canonical_trial': {
            'trial_id': config.trial_id,
            'trial_config_sha256': config.canonical_sha256,
            'config_source_sha256': hashes['mini_moonboard/wood_joint_wj04_config.py'],
            'source_inventory_sha256': inventory_sha,
            'active_probe_trial_config_sha256': probe.get('trial_config_sha256'),
            'active_probe_config_hash_matches': True,
            'probe_geometry_used_as_coordinate_source': False,
            'canonical_geometry_coordinate_source': 'WJ04_TRIAL stacks and cleat; source faces from hash-bound source inventory',
            'cleat_size_x_t_n_mm': config.cleat.size_x_t_n_mm,
            'cleat_origin_x_t_n_mm': config.cleat.origin_x_t_n_mm,
            'stock_grade_verified': config.stock_grade_verified,
            'purchase_approved': config.purchase_approved,
            'drilling_released': config.drilling_released,
            'fabrication_released': config.fabrication_released,
            'structural_released': config.structural_released,
        },
        'material_axes_by_member': material_axes,
        'method': {
            'source_action': 'old selected-candidate audited member-on-bracket flange wrenches',
            'moment_translation': 'M_at_group = M_at_source + (source_origin - group_centroid) cross F',
            'local_basis': {'order': list(axis_names), 'columns_global_xyz': basis},
            'replacement_reaction': 'equal and opposite to old member-on-bracket action, with no stiffness redistribution',
            'two_bolt_point_group': 'minimum-norm rigid two-point force split retained as an intermediate diagnostic',
            'bolt_tension_and_face_contact_static_path': (
                'replace bolt-axis compression with contact compression at that bearing point; '
                'resolve the moment parallel to the bolt row with equal bolt tension and opposite '
                'compression at a 10 mm signed edge band, with resultant 5 mm inside the actual face edge; rigid statics only'
            ),
            'contact_face_extents': (
                'edge bounds come from source host face planes and canonical cleat dimensions; '
                'reported contact-area estimate comes from the trial-bound finite probe '
                'intersection volume divided by probe depth; no pressure distribution or capacity'
            ),
            'signed_material_axis_method': 'project connector-on-host and equal/opposite cleat action onto canonical global grain and bolt axes; retain signs',
            'fastener_load_sharing': 'minimum-norm split retained as a historical statics diagnostic; not an adopted per-fastener demand',
        },
        'source_status': {
            'old_action_ledger_status': demand['status'],
            'old_candidate_connection_resistance_established': demand['connection_resistance_established'],
            'native_solver_replayed': False,
            'current_sources_checked': False,
            'assessment_resistance_recomputed': False,
            'source_ledger_limited_to_angle_demands': True,
        },
        'staleness_audit': staleness,
        'input_sha256': hashes,
        'source_case_provenance': {
            case['case_id']: {
                'native_report_sha256': case['native_report_sha256'],
                'assessment_input_sha256': case['assessment_input_sha256'],
                'native_solver_replayed': case['native_solver_replayed'],
                'current_sources_checked': case['current_sources_checked'],
            }
            for case in per_case
        },
        'interface_summary': summary,
        'complete_joint_capacity': _complete_joint_capacity_status(config, groups),
        'cases': per_case,
        'two_interface_cleat_free_body_closure': _cleat_free_body_closure(
            per_case, basis,
        ),
        'limits': [
            'Old selected-candidate interface actions are demand-preservation proxies only; no action transfers as a new-candidate demand or pass.',
            'No stiffness-based redistribution is available for the altered member and connector geometry.',
            'A statically balanced wrench uses idealized compression resultants from a 10 mm face-edge band; the 5 mm resultant inset is a statics witness, not a pressure-distribution or resistance model.',
            'Signed grain and bolt-axis projections are retained, but old source forces and minimum-norm per-bolt splits cannot classify an adopted NDS end/edge criterion.',
            'No wood bearing, splitting, net section, end/edge, bolt lateral yield, steel tension/shear interaction, washer plate, contact pressure, or cleat internal-transfer capacity is calculated.',
            'The complete bounded joint capacity is not feasible from current inputs: fresh same-candidate demands, actual hole/cut geometry, verified materials, and adopted interaction/contact methods remain unresolved.',
            'Active probe candidate dimensions are modeling inputs; no delivered stock, hardware, or cut is selected.',
        ],
    })


def _cleat_free_body_closure(per_case, basis):
    """Check historical interface-action closure about one shared datum.

    This verifies arithmetic consistency between the two source flange
    wrenches only. It is not a new-cleat stress or resistance calculation.
    """
    result = []
    for case in per_case:
        rail = case['interfaces']['rail']
        principal = case['interfaces']['principal']
        datum = rail['group_centroid_global_xyz_mm']
        force = _add(
            rail['legacy_member_on_bracket_force_global_xyz_n'],
            principal['legacy_member_on_bracket_force_global_xyz_n'],
        )
        principal_force = principal['legacy_member_on_bracket_force_global_xyz_n']
        principal_lever = _sub(principal['group_centroid_global_xyz_mm'], datum)
        moment = _add(
            rail['legacy_member_on_bracket_moment_at_group_centroid_global_xyz_nmm'],
            _add(
                principal['legacy_member_on_bracket_moment_at_group_centroid_global_xyz_nmm'],
                _cross(principal_lever, principal_force),
            ),
        )
        result.append({
            'case_id': case['case_id'],
            'common_datum_global_xyz_mm': datum,
            'legacy_host_actions_on_bracket_force_sum_global_xyz_n': force,
            'legacy_host_actions_on_bracket_moment_sum_global_xyz_nmm': moment,
            'legacy_host_actions_on_bracket_force_residual_n': _norm(force),
            'legacy_host_actions_on_bracket_moment_residual_nmm': _norm(moment),
            'local_XTN_force_sum_n': _project(force, basis),
            'local_XTN_moment_sum_nmm': _project(moment, basis),
            'source_ledger_closure_only': True,
        })
    return result


def render_markdown(report):
    lines = [
        '# WJ-04 early mechanics screen',
        '',
        'Status: **diagnostic only; revise named mechanical gaps.** This screen preserves the old selected-candidate',
        'member-on-bracket actions at the WJ-04 reference station and maps them to group centroids from canonical trial',
        'geometry. It does not qualify the new cleat or replace fresh full-frame actions.',
        '',
        '## Inputs and transfer',
        '',
        f"- Old action candidate: `{report['source_candidate_for_actions']}`; WJ-04 development candidate: `{report['candidate']}`.",
        f"- Canonical trial: `{report['canonical_trial']['trial_id']}`; config SHA-256 `{report['canonical_trial']['trial_config_sha256']}`.",
        '- Group positions, signed axes, and cleat bounds come from hash-bound `WJ04_TRIAL`; the active probe is checked against its config hash.',
        f"- Station and cases: `{report['station']}`; {', '.join(f'`{case}`' for case in report['case_ids'])}.",
        '- Source actions are the audited `flange_member_on_bracket_wrenches` for the six former SDS groups.',
        '  Their source ledger is angle-demand-only: it did not replay native solves, check current sources, or recompute resistance.',
        '- The old action on the bracket is held unchanged, translated from the old station origin to each proposed bolt-group centroid,',
        '  and reversed to show the equal-and-opposite connector action on its host. No stiffness redistribution is inferred.',
        '- A two-point rigid fastener-only split is retained as an intermediate comparison. A separate rigid statics witness',
        '  transfers bolt-axis compression to contact and closes each row-axis moment with bolt tension and opposite face compression.',
        '  It assigns no stiffness, pressure distribution, preload, or resistance.',
        '',
        'Input hashes:',
        '',
    ]
    for path, digest in report['input_sha256'].items():
        lines.append(f'- `{path}`: `{digest}`')
    audit = report['staleness_audit']
    lines += [
        '',
        '## Source/hash staleness',
        '',
        'The old action ledger marks current sources unchecked. This report re-compares declared hashes with the present working tree',
        'to make that provenance gap explicit; a match does not replay or authenticate an old solve.',
        '',
        'Old six-case producer snapshot:',
        '',
    ]
    for case_id in report['case_ids']:
        row = audit['old_case_source_snapshot_by_case'][case_id]
        lines.append(
            f"- `{case_id}`: {row['matching_current_files']}/{row['declared_source_count']} files match; "
            f"{len(row['stale_or_mismatched_paths'])} mismatched, {len(row['missing_paths'])} missing."
        )
    old_stale = audit['old_case_stale_or_missing_source_hashes']
    if old_stale:
        lines += ['', 'Recorded old hashes that differ from current files:', '']
        for path, item in old_stale.items():
            lines.append(
                f"- `{path}`: recorded `{item['declared_sha256']}`, current "
                f"`{item['current_sha256'] or 'missing'}`."
            )
    else:
        lines += ['', 'All declared old-case source files currently match; native solves remain unreplayed.', '']
    lines += ['', 'Currentness of the other bound producers:', '']
    for path, item in audit['old_case_consumer_sources'].items():
        lines.append(f"- Old ledger consumer `{path}`: **{item['status']}**.")
    contact_items = list(audit['old_case_contact_search_source_by_case'].items())
    contact_statuses = {item['status'] for _, item in contact_items}
    contact_hashes = {item['current_sha256'] for _, item in contact_items}
    lines.append(
        f"- Old contact-search producers versus current `fea/current_response_run.py`: "
        f"**{', '.join(sorted(contact_statuses))}**; current hash `"
        f"{next(iter(contact_hashes)) if len(contact_hashes) == 1 else 'varies'}`."
    )
    for label, name in (
        ('Selected source inventory bindings', 'wood_joint_source_inventory_bindings'),
        ('WJ-04 probe producer/dependencies', 'wj04_probe_producer_and_dependencies'),
    ):
        mismatches = [path for path, item in audit[name].items() if item['status'] != 'match']
        lines.append(
            f"- {label}: {len(mismatches)}/{len(audit[name])} current hash mismatches."
            + (f" Paths: {', '.join(f'`{path}`' for path in mismatches)}." if mismatches else '')
        )
    lines += [
        '',
        '## Candidate interfaces',
        '',
        '| Interface | Host face normal | Bolt axis | Bolt-row axis | Spacing | Finite-probe area estimate | Old normal action range | Separation cases |',
        '|---|---:|---:|---:|---:|---:|---:|---|',
    ]
    for key in ('rail', 'principal'):
        row = report['interface_summary'][key]
        face = ', '.join(f'{v:.6g}' for v in row['face_normal_global_xyz'])
        bolt = ', '.join(f'{v:.6g}' for v in row['bolt_axis_global_xyz'])
        axis = ', '.join(f'{v:.6g}' for v in row['bolt_row_axis_global_xyz'])
        normal_range = row['legacy_member_on_bracket_normal_force_range_n']
        sep = ', '.join(row['separation_indicated_case_ids']) or 'none'
        lines.append(
            f"| `{row['interface_id']}` | `{face}` | `{bolt}` | `{axis}` | "
            f"{row['bolt_spacing_mm']:.3f} mm | "
            f"{row['finite_probe_contact_area_mm2']:.6f} mm² | "
            f"[{normal_range[0]:.3f}, {normal_range[1]:.3f}] N | {sep} |"
        )
    lines += [
        '',
        'The signed normal action is reported as **legacy host on bracket**, using the outward normal from each host face toward',
        'the cleat. A negative value indicates a separation tendency in that interface; its equal-and-opposite connector reaction',
        'on the host is positive. Across these old cases the rail interface indicates separation in all six; the principal interface',
        'is compressive in all six. The new bolt axes are parallel to the corresponding face normals, so the provisional topology has',
        'an axial fastener direction for both signs. That alignment establishes no resistance.',
        '',
        '### Canonical contact-face edge bands',
        '',
        'Coordinate bounds are derived from source-inventory host face planes and canonical cleat dimensions.',
        'The row-axis moment witness uses a finite 10 mm band at the selected face edge, with its resultant 5 mm inside that edge.',
        'Both possible signed edges must fit the full band before the report is generated. The projected bolt-group centroid and each',
        'finite-band resultant must also lie inside the canonical bounds rectangle along both the bolt-row and transverse axes.',
        '',
        '| Interface | Band width / inset | Negative edge distance / lever | Positive edge distance / lever | Face band area |',
        '|---|---:|---:|---:|---:|',
    ]
    for key in ('rail', 'principal'):
        row = report['interface_summary'][key]
        face = row['contact_face_geometry']
        distances = face['edge_distances_from_bolt_row_centroid_mm']
        levers = face['available_finite_band_levers_mm']
        lines.append(
        f"| `{row['interface_id']}` | {face['edge_band_width_mm']:.1f} / "
            f"{face['edge_resultant_inset_mm']:.1f} mm | "
            f"{distances['negative']:.3f} / {levers['negative']:.3f} mm | "
            f"{distances['positive']:.3f} / {levers['positive']:.3f} mm | "
            f"{face['edge_band_width_mm'] * face['row_span_mm']:.1f} mm² |"
        )
    lines += [
        '',
        '### Contact-area measurement and coordinate audit',
        '',
        'The contact-area estimate is read from the active, trial-bound WJ-04 probe. Its hash-bound producer computes the',
        'cleat/host overlap volume after a 0.1 mm inward translation, divided by that probe depth. The separate canonical',
        'bounds rectangle is the product of the row and transverse coordinate spans used for the edge witness. The signed',
        'difference is probe estimate minus rectangle area; the quantities are reported separately without a tolerance-based',
        'equivalence claim. This is geometry provenance only, not pressure or resistance.',
        '',
        '| Interface | Finite-probe estimate | Canonical bounds rectangle | Probe minus rectangle | Ratio | Method |',
        '|---|---:|---:|---:|---:|---|',
    ]
    for key in ('rail', 'principal'):
        row = report['interface_summary'][key]
        face = row['contact_face_geometry']
        method = face['finite_probe_area_measurement']
        lines.append(
            f"| `{row['interface_id']}` | {face['finite_probe_contact_area_mm2']:.6f} mm² | "
            f"{face['canonical_bounds_rectangle_area_mm2']:.6f} mm² | "
            f"{face['finite_probe_minus_rectangle_area_mm2']:.6f} mm² | "
            f"{face['finite_probe_to_rectangle_area_ratio']:.9f} | "
            f"`{method['method_id']}` at {method['probe_depth_mm']:.1f} mm |"
        )
    lines += [
        '',
        '### Canonical signed material axes',
        '',
        '| Member | Grain axis | Rail stack axis | Principal stack axis | Stock basis verified |',
        '|---|---:|---:|---:|---|',
    ]
    for member_id in ('base_rail_service_lower_right', 'base_principal_center_right', 'wj04_cleat'):
        member = report['material_axes_by_member'][member_id]
        grain = ', '.join(f'{v:.6g}' for v in member['grain_axis_global_xyz'])
        rail_axis = report['interface_summary']['rail']['bolt_axis_global_xyz']
        principal_axis = report['interface_summary']['principal']['bolt_axis_global_xyz']
        lines.append(
            f"| `{member_id}` | `{grain}` | `{', '.join(f'{v:.6g}' for v in rail_axis)}` | "
            f"`{', '.join(f'{v:.6g}' for v in principal_axis)}` | {member['stock_grade_verified']} |"
        )
    rail_edge = report['interface_summary']['rail']['material_axes']['cleat']
    principal_edge = report['interface_summary']['principal']['material_axes']['cleat']
    rail_axis_global = report['interface_summary']['rail']['bolt_axis_global_xyz']
    principal_axis_global = report['interface_summary']['principal']['bolt_axis_global_xyz']
    principal_cleat_placement = report['interface_summary']['principal'][
        'placement_geometry_by_member'
    ]['wj04_cleat']
    principal_placement_rows = principal_cleat_placement['stack_placement']
    principal_edge_distance = min(
        row['placement_by_local_axis']['T'][key]
        for row in principal_placement_rows
        for key in ('distance_to_negative_boundary_mm', 'distance_to_positive_boundary_mm')
    )
    principal_end_distance = min(
        row['placement_by_local_axis']['N'][key]
        for row in principal_placement_rows
        for key in ('distance_to_negative_boundary_mm', 'distance_to_positive_boundary_mm')
    )
    principal_edge_4d_reserve = min(
        reserve
        for row in principal_placement_rows
        for reserve in row['placement_by_local_axis']['T']['conditional_4d_reserve_mm'].values()
    )
    principal_end_4d_reserve = min(
        reserve
        for row in principal_placement_rows
        for reserve in row['placement_by_local_axis']['N']['conditional_4d_reserve_mm'].values()
    )
    principal_end_7d_reserve = min(
        reserve
        for row in principal_placement_rows
        for reserve in row['placement_by_local_axis']['N']['conditional_7d_reserve_mm'].values()
    )
    lines += [
        '',
        f"Canonical bolt axes are rail `{', '.join(f'{v:.6g}' for v in rail_axis_global)}` and principal `{', '.join(f'{v:.6g}' for v in principal_axis_global)}` in global XYZ.",
        'Member grain directions use canonical config axis names and hash-bound source transforms; old probe local labels do not set material directions.',
        'Signed old-action projections and minimum-norm bolt splits are diagnostic. They do not establish current NDS loaded-edge or end categories.',
        '',
        f"Cleat bolt-axis/grain parallel flags: rail `{rail_edge['bolt_axis_parallel_to_grain']}`, principal `{principal_edge['bolt_axis_parallel_to_grain']}`.",
        f"Principal cleat minimum T lateral-edge distance is {principal_edge_distance:.3f} mm; conditional 4D reference reserve is {principal_edge_4d_reserve:.3f} mm if current lateral force loads that edge.",
        f"Principal cleat minimum N grain-end distance is {principal_end_distance:.3f} mm; 4D/7D reference reserves are {principal_end_4d_reserve:.3f}/{principal_end_7d_reserve:.3f} mm, subject to signed NDS end-category applicability.",
    ]
    lines += [
        '',
        '## Signed actions at proposed group centroids',
        '',
        'Each row gives the old host-on-bracket force in canonical local X/T/N and its moment about the current canonical group centroid.',
        'The connector-on-host force and moment are equal and opposite. Moments are N·mm.',
        '',
        '| Case | Interface | F X | F T | F N | M X | M T | M N |',
        '|---|---|---:|---:|---:|---:|---:|---:|',
    ]
    for case in report['cases']:
        for key in ('rail', 'principal'):
            row = case['interfaces'][key]
            force = row['legacy_member_on_bracket_force_local_XTN_n']
            moment = row['legacy_member_on_bracket_moment_at_group_centroid_local_XTN_nmm']
            lines.append(
                f"| `{case['case_id']}` | `{row['interface_id']}` | "
                + ' | '.join(f'{value:.3f}' for value in (*force, *moment)) + ' |'
            )
    lines += [
        '',
        '## Bolt tension, face compression, and wrench closure',
        '',
        'For each host interface, the statics witness balances the full historical diagnostic wrench with tension-only axial bolt resultants,',
        'transverse point-bolt resultants, and compression-only face-contact resultants. Row-axis moment uses the signed 10 mm face-edge band.',
        'The finite-band couple force exceeds the zero-area edge-resultant force baseline because the resultant sits 5 mm inboard.',
        'This is idealized rigid statics; it does not calculate pressure distribution, opening, stiffness, slip, or resistance.',
        '',
        '| Case | Interface | Edge | Band / inset | Edge distance | Finite lever | Finite couple force | Zero-area edge force | Peak bolt tension | Peak face compression | Force / moment residual |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for case in report['cases']:
        for key in ('rail', 'principal'):
            row = case['interfaces'][key]
            path = row['bolt_tension_and_face_contact_static_path']
            peak_tension = max(
                bolt['tension_after_row_moment_couple_n']
                for bolt in path['bolt_rows']
            )
            peak_contact = max(
                item['magnitude_n'] for item in path['contact_compression_resultants']
            )
            witness = path['row_axis_moment_path']
            lines.append(
                f"| `{case['case_id']}` | `{row['interface_id']}` | "
                f"{witness['contact_edge_side']} | {witness['edge_band_width_mm']:.1f} / "
                f"{witness['resultant_inset_from_edge_mm']:.1f} mm | "
                f"{witness['actual_face_edge_distance_mm']:.3f} mm | "
                f"{witness['available_edge_lever_arm_mm']:.3f} mm | "
                f"{witness['finite_band_couple_force_n']:.3f} N | "
                f"{witness['zero_area_edge_resultant_force_n']:.3f} N | "
                f"{peak_tension:.3f} N | {peak_contact:.3f} N | "
                f"{path['force_residual_norm_n']:.3g} N / "
                f"{path['moment_residual_norm_nmm']:.3g} N·mm |"
            )
    lines += [
        '',
        '## Complete-joint resistance disposition',
        '',
        f"Disposition: **{report['complete_joint_capacity']['disposition']}**; full bounded capacity feasible from current inputs: **{report['complete_joint_capacity']['complete_bounded_joint_capacity_feasible_now']}**.",
        'Old loads remain stale angle-demand diagnostics. No fresh candidate per-fastener demand or resistance comparison exists.',
        '',
        '| Limit state | Status | Main unresolved inputs |',
        '|---|---|---|',
    ]
    for item in report['complete_joint_capacity']['limit_state_methods']:
        missing = '; '.join(item.get('missing', ()))
        lines.append(f"| `{item['method_id']}` | **{item['status']}** | {missing} |")
    lines += [
        '',
        'Wood checks require actual signed member-side fastener actions, finished holes/cuts, material and adjustment inputs; Appendix E covers parallel-grain net/tear-out modes only.',
        'Bolt checks require measured thread engagement in both bearing layers, product-applicable Fyb and steel areas; tension/shear interaction remains unadopted.',
        'Washer steel spread, unilateral contact pressure/opening, and cleat internal transfer remain unresolved. The finite 10 mm contact band is equilibrium geometry only.',
        '',
        '## Coupled cleat free-body source closure',
        '',
        'Both host-on-bracket interface wrenches are translated to one shared datum and summed. This audits the historical source ledger',
        'balance only; it does not evaluate cleat bending, splitting, fastener interaction, or revised-frame demand.',
        '',
        '| Case | Force residual | Moment residual |',
        '|---|---:|---:|',
    ]
    for row in report['two_interface_cleat_free_body_closure']:
        lines.append(
            f"| `{row['case_id']}` | {row['legacy_host_actions_on_bracket_force_residual_n']:.3g} N | "
            f"{row['legacy_host_actions_on_bracket_moment_residual_nmm']:.3g} N·mm |"
        )
    lines += [
        '',
        '## What this supports',
        '',
        '- Signed legacy interface force and all three moment components can be reconstructed at each proposed group centroid.',
        '- The rail side requires a tie path under every old case; compression contact alone cannot supply its normal action.',
        '- Each interface has a finite-band row-axis contact-couple witness with signed edge choice, in-face lever, and full wrench closure.',
        '  The 5 mm inset increases couple force over the optimistic zero-area edge resultant. Geometry, hardware, NDS resistance,',
        '  joint interaction, and fresh candidate demands remain open.',
        '- Both historical interface actions are summed at one shared datum to expose old-ledger closure residuals before geometry reuse.',
        '- The principal face has a compression-normal component in all six old cases. This does not prove that contact remains closed',
        '  after coupled moments, tolerances, or changed full-frame stiffness.',
        '',
        '## Checks this cannot support',
        '',
        '- No resistance or pass for bolt tension, shear, interaction, withdrawal, washer bearing, wood bearing, splitting, or connector bending.',
        '- No contact-pressure distribution, opening extent, slip, rotational stiffness, bolt preload, group stiffness, or load sharing between faces.',
        '- No cleat internal stress, complete wood/bolt/contact capacity, or fresh six-case demand for the revised frame and cleat.',
        '- No reuse of the old angle rating, selected-candidate case pass, or any legacy screw capacity.',
        '- No drilling, stock selection, fabrication, or structural release.',
        '',
        'The reported local results are sufficient to carry WJ-04 into an explicit mechanics-method step. They do not clear the',
        'tool, tolerance, stock, length, end/edge, or service-obstruction blockers in the geometric probe.',
        '',
    ]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='write the diagnostic JSON and Markdown')
    args = parser.parse_args()
    report = build_report()
    if args.write:
        OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        OUTPUT_MD.write_text(render_markdown(report), encoding='utf-8')
        print(f'Wrote {OUTPUT_JSON.relative_to(ROOT)}')
        print(f'Wrote {OUTPUT_MD.relative_to(ROOT)}')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
