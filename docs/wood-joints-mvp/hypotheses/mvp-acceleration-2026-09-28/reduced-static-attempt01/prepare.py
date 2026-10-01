"""Bind current assembly topology and external wrenches for a reduced static model.

This is model preparation, not a stiffness solution or joint-demand prediction.
Ambiguous hardware gravity remains explicit until its mechanical carrier is set.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MANIFEST = ('docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/'
            'current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json')
MANIFEST_SHA = '9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11'


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def add(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def close(a, b, tolerance=1e-6):
    assert len(a) == len(b) and max(abs(x-y) for x, y in zip(a, b)) < tolerance, (a, b)


def prepare():
    pins = {}

    def read(path, expected=None):
        raw = (ROOT/path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if expected is not None:
            assert digest == expected, f'Source changed: {path}'
        pins[path] = digest
        return json.loads(raw)

    manifest = read(MANIFEST, MANIFEST_SHA)
    revision = manifest['geometry_revision_id']
    bindings = manifest['evidence_bindings']
    def bound(key):
        entry = bindings[key]
        return read(entry['path'], entry['file_sha256'])
    masses = bound('source_mass_centroids')
    topology = bound('source_to_mass_topology')
    dead_load = bound('modeled_body_gravity_and_accessory_scenarios')
    graph = read(manifest['contact_graph']['source_path'],
                 topology['source_sha256'][manifest['contact_graph']['source_path']])
    load_source = manifest['applied_load_cases']
    read(load_source['source_path'], load_source['source_file_sha256'])
    assert revision == masses['revision_id'] == topology['revision_id'] == graph['revision_id']
    members = {r['member_id']: r for r in manifest['physical_members']}
    source_rows = {r['name']: r for r in masses['rows']}
    assert len(members) == 50 and len(source_rows) == 778
    body_centers = {name: source_rows[name]['mass_center_global_xyz_mm'] for name in members}
    assigned = {name: [] for name in members}
    deferred = []
    for row in topology['physical_mass_rows']:
        source = source_rows[row['inventory_name']]
        assert row['mass_kg'] == source['mass_kg']
        close(row['mass_center_global_xyz_mm'], source['mass_center_global_xyz_mm'])
        force, point = row['gravity_force_global_xyz_n'], row['mass_center_global_xyz_mm']
        close(force, [0, 0, -row['mass_kg']*9.80665])
        close(cross(point, force), row['gravity_moment_about_global_origin_nmm'])
        entity = row['source_mass_entity']
        references = entity['current_graph_member_references']
        assert references and len(references) == len(set(references)) and set(references) <= members.keys()
        entry = {'source_name': row['inventory_name'], 'mass_kg': row['mass_kg'],
                 'point_xyz_mm': point, 'force_xyz_n': force,
                 'receiver_member_ids': references, 'source_entity_kind': entity['kind']}
        if len(references) == 1:
            # Own timber/panel/block gravity or the same-panel hold T-nut gravity.
            assert entity['kind'] in ('current_physical_member_solid', 'current_physical_tnut_component')
            assigned[references[0]].append(entry)
        else:
            # Co-membership does not authorize nearest-body or equal-share assignment.
            deferred.append(entry)
    assert sum(map(len, assigned.values())) + len(deferred) == 778
    close([sum(r['mass_kg'] for rows in assigned.values() for r in rows)
           + sum(r['mass_kg'] for r in deferred)], [masses['modeled_mass_kg']])

    cases, csv_rows = [], []
    for load in load_source['cases']:
        hold_name = 'hold_tnut_main_' + load['hold_id']
        carriers = [name for name, rows in assigned.items() if any(r['source_name'] == hold_name for r in rows)]
        assert len(carriers) == 1, f'Hold does not map uniquely to a current panel: {hold_name}'
        panel = carriers[0]
        assert members[panel]['member_kind'] == 'panel'
        applied = load['applied_force_global_xyz_n']
        application = load['force_application_point_global_xyz_mm']
        reference = load['wrench_reference_point_global_xyz_mm']
        close(cross([x-y for x, y in zip(application, reference)], applied),
              load['moment_global_xyz_nmm'])
        body_rows = []
        full_force, full_moment = [0., 0., 0.], [0., 0., 0.]
        for name, rows in assigned.items():
            force, moment = [0., 0., 0.], [0., 0., 0.]
            center = body_centers[name]
            loads = [(r['point_xyz_mm'], r['force_xyz_n']) for r in rows]
            if name == panel:
                loads.append((application, applied))
            for point, value in loads:
                force = add(force, value)
                moment = add(moment, cross([x-y for x, y in zip(point, center)], value))
            full_force = add(full_force, force)
            full_moment = add(full_moment, add(moment, cross(center, force)))
            body_rows.append({'member_id': name, 'reference_xyz_mm': center,
                              'assigned_external_force_xyz_n': force,
                              'assigned_external_moment_xyz_nmm': moment})
            csv_rows.append([load['case_id'], name, *center, *force, *moment])
        for row in deferred:
            full_force = add(full_force, row['force_xyz_n'])
            full_moment = add(full_moment, cross(row['point_xyz_mm'], row['force_xyz_n']))
        close(full_force, add(masses['gravity_force_global_xyz_n'], applied))
        close(full_moment, add(masses['gravity_moment_about_global_origin_nmm'], cross(application, applied)))
        cases.append({'case_id': load['case_id'], 'loaded_panel': panel,
                      'source_applied_load': load, 'body_external_wrenches': body_rows,
                      'including_deferred_hardware_force_xyz_n': full_force,
                      'including_deferred_hardware_moment_about_origin_xyz_nmm': full_moment})

    connections = []
    for kind, key in [('candidate_bolt', 'candidate_bolt_axes'),
                      ('retained_bolt', 'retained_frame_bolt_axes'),
                      ('panel_screw', 'panel_kicker_screw_axes')]:
        for row in manifest[key]:
            if kind == 'candidate_bolt':
                receivers = row['receiver_member_ids']
                point = row['geometry']['shaft_center_global_xyz_mm']
                axis = row['geometry']['axis_head_to_nut_global']
            elif kind == 'retained_bolt':
                receivers = row['members_as_recorded']
                point, axis = row['origin_global_xyz_mm'], row['axis_global_xyz']
            else:
                receivers = [row['panel_member'], row['receiver_member']]
                point, axis = row['origin_global_xyz_mm'], row['axis_global_xyz']
            assert set(receivers) <= members.keys()
            close([sum(v*v for v in axis)], [1.0])
            connections.append({'kind': kind, 'axis_id': row['axis_id'],
                                'receiver_member_ids': receivers, 'source_point_xyz_mm': point,
                                'axis_xyz': axis, 'source_record': row,
                                'mechanical_attachment_defined': False})
    assert len(connections) == 170 and len(cases) == 6 and len(csv_rows) == 300
    interfaces = []
    for bolt in manifest['candidate_bolt_axes']:
        geometry = bolt['geometry']
        spans = []
        for receiver in geometry['wood_receiver_intervals']:
            intervals = receiver['intersection_solid_intervals_from_underhead_mm']
            assert len(intervals) == 1, 'Multiple wood intervals require an explicit stack model'
            spans.append((*intervals[0], receiver['receiver_id']))
        spans.sort()
        # The pinned geometry uses one cylindrical shaft starting at the underhead.
        length = geometry['modeled_shaft_occupied_length_mm']
        close([length], [geometry['modeled_underhead_to_tip_mm']])
        direction = geometry['axis_head_to_nut_global']
        underhead = [p-length*a/2 for p, a in
                     zip(geometry['shaft_center_global_xyz_mm'], direction)]
        for first, second in zip(spans, spans[1:]):
            gap = second[0]-first[1]
            assert abs(gap) < 1e-5, 'Noncontiguous raw receiver intervals require an explicit gap model'
            station = (first[1]+second[0])/2
            interfaces.append({'axis_id': bolt['axis_id'],
                               'adjacent_receivers_head_to_nut': [first[2], second[2]],
                               'station_from_underhead_mm': station,
                               'raw_interval_gap_mm': gap,
                               'axis_point_xyz_mm': [p+station*a for p, a in zip(underhead, direction)],
                               'mechanical_shear_plane_verified': False,
                               'limit': 'Adjacent raw-wood interval boundary; finished contact patch and continuous-bolt mechanics still require mapping.'})
    assert len(interfaces) == 96
    contact_geometry = read(str((HERE/'contact-geometry.json').relative_to(ROOT)))
    assert contact_geometry['revision_id'] == revision
    assert contact_geometry['checks']['discrepancy_count'] == 0
    assert contact_geometry['checks']['all_opposed_patch_sums_match_graph_and_helper']
    member_geometry = read(str((HERE/'member-geometry.json').relative_to(ROOT)))
    assert member_geometry['geometry_revision_id'] == revision
    assert member_geometry['candidate'] == manifest['candidate']
    reduced_members = {r['member_id']: r for r in member_geometry['members']}
    reduced_panels = {r['panel_id']: r for r in member_geometry['panels']}
    assert len(reduced_members) == 44 and len(reduced_panels) == 6
    assert not (reduced_members.keys() & reduced_panels.keys())
    assert reduced_members.keys() | reduced_panels.keys() == members.keys()
    clearance = read(str((HERE/'bolt-clearance.json').relative_to(ROOT)))
    assert clearance['geometry_revision_id'] == revision
    assert clearance['candidate'] == manifest['candidate'] and not clearance['exceptions']
    clearance_rows = {(r['axis_id'], r['receiver_id']): r
                      for r in clearance['axis_receiver_clearances']}
    expected_pairs = {(r['axis_id'], receiver) for r in manifest['candidate_bolt_axes']
                      for receiver in r['receiver_member_ids']}
    assert set(clearance_rows) == expected_pairs and len(clearance_rows) == 188
    for connection in connections:
        if connection['kind'] == 'candidate_bolt':
            connection['receiver_clearance_geometry'] = [
                clearance_rows[connection['axis_id'], receiver]
                for receiver in connection['receiver_member_ids']]
    for interface in interfaces:
        pair = set(interface['adjacent_receivers_head_to_nut'])
        point = interface['axis_point_xyz_mm']
        matches = []
        for patch in contact_geometry['contact_patches']:
            if set(patch['member_ids']) != pair:
                continue
            distance = abs(sum((x-y)*n for x, y, n in
                               zip(point, patch['centroid_xyz_mm'], patch['normal_on_first_xyz'])))
            if distance < 1e-5:
                matches.append({'member_ids': patch['member_ids'], 'patch_index': patch['patch_index'],
                                'point_to_plane_distance_mm': distance})
        assert matches, f'Raw bolt interface has no matching finished contact plane: {interface}'
        interface['matching_finished_contact_planes'] = matches
        interface['plane_match_limit'] = 'Plane coincidence only, not inclusion within trimmed patch, active contact or stiffness qualification.'
    finite_contacts = [r for r in graph['edges'] if r['geometry_state'] == 'finite_opposed_planar_touch']
    unresolved_contacts = [r for r in graph['edges'] if r['geometry_state'] == 'zero_area_touch_or_unresolved']
    exceptions = [
        {'id': 'connector_laws', 'detail': '170 physical axes need current directional stiffness, engagement and force recovery; no baseline spring properties inherited.'},
        {'id': 'three_receiver_bolts', 'count': sum(len(r['receiver_member_ids']) == 3 for r in connections),
         'detail': 'Three-member bolts remain single physical axes; pair associations are not independent springs.'},
        {'id': 'hardware_gravity_carriers', 'count': len(deferred),
         'mass_kg': sum(r['mass_kg'] for r in deferred),
         'detail': 'Global gravity is retained exactly; body-level carrier mechanics remains unassigned.'},
        {'id': 'accessory_allowance', 'mass_kg': 25,
         'detail': 'Separate existing placement scenarios are retained below; they are not yet body/DOF mapped and are excluded from the base six-case table.'},
        {'id': 'contact_and_floor', 'detail': 'Finite touch is geometry, not an active contact; contact patches, unilateral support and no-slip engagement need explicit current mappings.'},
        {'id': 'zero_area_contacts', 'member_pairs': [r['member_ids'] for r in unresolved_contacts],
         'detail': 'No finite bearing area is assigned to these six touching/unresolved pairs; alternative load paths still require evaluation.'},
        {'id': 'elements_and_properties', 'detail': 'Current member/panel element representation, material axes and section properties must be bound before solving.'},
    ]
    output = {'schema': 'wood_joint_reduced_static_preparation/v1', 'candidate': manifest['candidate'],
              'revision_id': revision, 'source_sha256': pins, 'mechanical_acceptance': False,
              'native_solve_run': False, 'ready_for_six_case_response': False,
              'members': [{**row, 'reduced_geometry_descriptor':
                           reduced_members.get(name, reduced_panels.get(name))}
                          for name, row in members.items()], 'connections': connections,
              'candidate_bolt_adjacent_interfaces': interfaces,
              'contact_geometry_artifact': str((HERE/'contact-geometry.json').relative_to(ROOT)),
              'member_geometry_artifact': str((HERE/'member-geometry.json').relative_to(ROOT)),
              'bolt_clearance_artifact': str((HERE/'bolt-clearance.json').relative_to(ROOT)),
              'finite_contact_candidates': finite_contacts,
              'zero_area_or_unresolved_contacts': unresolved_contacts,
              'assigned_gravity_by_member': assigned, 'unassigned_hardware_gravity': deferred,
              'accessory_placement_scenarios': dead_load['accessory_allowance'],
              'cases': cases, 'exceptions': exceptions,
              'checks': {'source_pins_match': True, 'all_778_masses_retained_once': True,
                         'all_six_force_and_moment_resultants_match': True,
                         'hold_load_carrier_unique': True, 'physical_axes_retained_once': True},
              'limit': 'External body loads only. No interface load sharing, stiffness solution, joint capacity or criterion pass.'}
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['case_id', 'member_id', 'ref_x_mm', 'ref_y_mm', 'ref_z_mm',
                     'external_Fx_N', 'external_Fy_N', 'external_Fz_N',
                     'external_Mx_Nmm', 'external_My_Nmm', 'external_Mz_Nmm'])
    writer.writerows(csv_rows)
    return {'model-inputs.json': json.dumps(output, indent=2)+'\n',
            'body-external-wrenches.csv': stream.getvalue()}


if __name__ == '__main__':
    # Known-answer moment shift, including sign: F=(0,0,-10), x offset 2 => My=20.
    close(cross([2, 0, 0], [0, 0, -10]), [0, 20, 0])
    outputs = prepare()
    if sys.argv[1:] == ['--write']:
        for name, content in outputs.items():
            (HERE/name).write_text(content)
    elif sys.argv[1:] == ['--verify']:
        for name, content in outputs.items():
            assert (HERE/name).read_text() == content, f'Artifact changed: {name}'
    else:
        raise SystemExit('Use --write or --verify')
    print('Verified 50 bodies, 170 physical axes, 778 mass rows and six global force/moment balances')
