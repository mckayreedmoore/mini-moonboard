"""Recover frozen round-frame member and structural-joint demands; conditional references."""
import argparse
import json
from pathlib import Path

import numpy as np

from fea import angle_base_connection_screen as angle_reference
from fea.lumber_leg_resistance import directional_bolt_reference
from fea.panel_screw_sensitivity import authenticated_input, digest

NDS_CH3 = 'https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf'
SIMPSON_CATALOG = 'https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf'


def wrench(points, forces, origin):
    points, forces, origin = np.asarray(points), np.asarray(forces), np.asarray(origin)
    if not np.isfinite(points).all() or not np.isfinite(forces).all():
        raise ValueError('Nonfinite joint demand')
    return forces.sum(axis=0), np.cross(points-origin, forces).sum(axis=0)


def irreducible_couple(force, moment):
    """Separate moment due to an offset force from its origin-invariant couple."""
    force, moment = np.asarray(force), np.asarray(moment)
    norm2 = float(np.dot(force, force))
    couple = force*np.dot(force, moment)/norm2 if norm2 else moment
    offset = np.cross(force, moment)/norm2 if norm2 else None
    return {'parallel_couple_xyz_nmm': couple.tolist(), 'parallel_couple_norm_nmm': float(np.linalg.norm(couple)),
            'equivalent_force_offset_xyz_mm': offset.tolist() if offset is not None else None}


def member_actions(record, report):
    """Recover wood-side reported spring forces and the original nodal gravity.

    Wood attachment MPCs point directly to one member's solid nodes. Rigid
    angle masters and panel nodes must never receive timber ownership.
    """
    owners = {}
    for kind, nodes, name in record['elements'].values():
        if kind == 'C3D20':
            for node in nodes:
                if node in owners and owners[node] != name:
                    raise ValueError('Shared solid nodes across independent members')
                owners[node] = name
    for equation in record['equations']:
        dependent, _, coefficient = equation[0]
        names = {owners.get(node) for node, _, _ in equation[1:]}
        if len(names) == 1 and None not in names:
            if coefficient != 1.:
                raise ValueError('Unexpected wood interpolation equation')
            owners[dependent] = names.pop()
    result = {row['name']: [] for row in record['members']}
    nodes = {int(n): point for n, point in record['nodes'].items()}
    springs = {spring['name']: spring for spring in record['springs']}
    if set(springs) != set(report['connector_forces']):
        raise ValueError('Connector force inventory differs from frozen input')
    seating = {row['name']: row for row in record.get('seating_contacts', [])}
    recovered_seating = {row['name']: row for row in report.get('seating_contacts', [])}
    if set(seating) != set(recovered_seating):
        raise ValueError('Incomplete physical seating-force recovery')
    for name, row in report['connector_forces'].items():
        if name in seating:
            contact, recovered = seating[name], recovered_seating[name]
            force = recovered['compression_n']*np.asarray(contact['inward_xyz'])
            if (not np.isfinite(force).all() or
                    np.linalg.norm(force-row['force_on_first_xyz_n']) > 1.e-8 or
                    np.linalg.norm(force-recovered['physical_force_on_wood_xyz_n']) > 1.e-8):
                raise ValueError('Seating scalar is not mapped to its physical wood normal')
            if contact['member'] not in result or springs[name]['nodes'] != contact['scalar_nodes']:
                raise ValueError('Seating spring/member identity differs')
            result[contact['member']].append({'name': name, 'point': contact['point_xyz_mm'],
                                              'force': force.tolist()})
            continue  # Scalar auxiliary DOFs must not be counted again as XYZ springs.
        first, second = springs[name]['nodes']
        for node, sign in ((first, 1.), (second, -1.)):
            if node in owners:
                result[owners[node]].append({'name': name, 'point': nodes[node],
                    'force': (sign*np.asarray(row['force_on_first_xyz_n'])).tolist()})
    for tag, force in record['loads'].items():
        node = int(tag)
        if node in owners:
            if force[0] != 0. or force[1] != 0. or force[2] > 0.:
                raise ValueError('Expected only gravity applied directly to wood')
            result[owners[node]].append({'name': 'gravity_'+str(node), 'point': nodes[node], 'force': force})
    return result


def bore_section(width, depth, diameter, center):
    """Exact isolated transverse-passage projection, excluding fastener holes.

    At the bore center plane perpendicular to grain the removed material is
    a full-width rectangle, not a circle. These are geometry properties only;
    plane-section stresses do not resolve stress concentrations at the hole.
    """
    front, rear_start = center-diameter/2, center+diameter/2
    if not 0 < front < rear_start < depth or width <= 0:
        raise ValueError('Require enclosed transverse bore')
    rectangles = [(front, front/2), (depth-rear_start, (depth+rear_start)/2)]
    area = width*sum(height for height, _ in rectangles)
    centroid = sum(width*height*y for height, y in rectangles)/area
    iu = sum(width*height**3/12+width*height*(y-centroid)**2 for height, y in rectangles)
    iv = sum(height*width**3/12 for height, _ in rectangles)
    return {'gross_area_mm2': width*depth, 'net_area_mm2': area,
            'net_area_fraction': area/(width*depth), 'centroid_n_mm': centroid,
            'front_ligament_mm': front, 'rear_ligament_mm': depth-rear_start,
            'I_u_mm4': iu, 'I_v_mm4': iv, 'width_mm': width, 'depth_mm': depth,
            'scope': 'Isolated service-bore center section only; fastener holes and oblique ends excluded',
            'qualified_for_design': False}


def cut_demand(actions, origin, grain, section_u, section_v, section):
    """Upper-grain free body of the frozen native model; cut is away from supports."""
    origin, grain, u, v = map(np.asarray, (origin, grain, section_u, section_v))
    selected = [a for a in actions if np.dot(np.asarray(a['point'])-origin, grain) > 1.e-6]
    at_cut = [a['name'] for a in actions if abs(np.dot(np.asarray(a['point'])-origin, grain)) <= 1.e-6]
    if at_cut:
        raise ValueError('Discrete attachment/gravity at the requested bore cut: '+str(at_cut))
    if not selected:
        raise ValueError('Empty member free body')
    force, moment = wrench([a['point'] for a in selected], [a['force'] for a in selected], origin)
    # Upper-body external resultant is the internal tensile-positive section
    # resultant. The actual cut traction on that body has the opposite sign.
    axial, vu, vv = np.dot(force, grain), np.dot(force, u), np.dot(force, v)
    torque, mu, mv = np.dot(moment, grain), np.dot(moment, u), np.dot(moment, v)
    normal = [axial/section['net_area_mm2']+mu*y/section['I_u_mm4']-mv*x/section['I_v_mm4']
              for x in (-section['width_mm']/2, section['width_mm']/2)
              for y in (-section['centroid_n_mm'], section['depth_mm']-section['centroid_n_mm'])]
    return {'origin_xyz_mm': origin.tolist(), 'upper_free_body_actions': [a['name'] for a in selected],
            'upper_external_force_xyz_n': force.tolist(), 'upper_external_moment_xyz_nmm': moment.tolist(),
            'axial_n_tension_positive': float(axial), 'shear_u_v_n': [float(vu), float(vv)],
            'bending_u_v_nmm': [float(mu), float(mv)], 'torsion_nmm': float(torque),
            'nominal_net_normal_min_max_mpa': [float(min(normal)), float(max(normal))],
            'limits': 'Section-equilibrium and plane-section diagnostic of frozen clamp/spring model; '
                      'printed-displacement spring recovery is not an independent element-force output; '
                      'local bore stress concentration, shear flow, torsion, instability and wood strength not qualified.'}


def build(root=None, *, native_runs=None):
    """Assess either the preserved three-case batch or distinct current insert runs."""
    if native_runs is None:
        from mini_moonboard import round_service_frame as model

        root = Path(root)
        summary_path = root/'summary.json'
        summary = json.loads(summary_path.read_text())
        if summary['candidate'] != model.KEY or len(summary['cases']) != 3:
            raise ValueError('Require frozen three-case round batch')
        runs = [(root/c['case'], c['case'], c['report_sha256']) for c in summary['cases']]
        input_hashes = {str(summary_path): digest(summary_path)}
        mechanics_scope = 'Preserved three-case ordinary-panel-screw mechanics'
        authenticate = authenticated_input
    else:
        from fea import round_insert_frame as native_model
        from mini_moonboard import round_insert_frame as model

        directories = [Path(p) for p in native_runs]
        if not directories or len({p.resolve() for p in directories}) != len(directories):
            raise ValueError('Require nonempty distinct completed native run directories')
        runs = [(p, str(p), digest(p/'report.json')) for p in directories]
        input_hashes = {}
        mechanics_scope = 'Fresh insert mechanics; only the supplied completed native runs'
        authenticate = native_model.authenticated_input
    sources = {str(Path(__file__).resolve().relative_to(Path.cwd())): digest(__file__),
               'fea/lumber_leg_resistance.py': digest('fea/lumber_leg_resistance.py'),
               'fea/dowel_yield.py': digest('fea/dowel_yield.py'),
               'fea/panel_screw_sensitivity.py': digest('fea/panel_screw_sensitivity.py'),
               'fea/horizontal_panel_frame.py': digest('fea/horizontal_panel_frame.py'),
               'fea/vertical_panel_comparison.py': digest('fea/vertical_panel_comparison.py'),
               'fea/angle_base_connection_screen.py': digest('fea/angle_base_connection_screen.py'),
               'docs/ml24z-reference.json': digest('docs/ml24z-reference.json'),
               'docs/selective-connection-reference.json': digest('docs/selective-connection-reference.json')}
    if native_runs is not None:
        sources.update(native_model.sources())
    connections = {c.name: c for c in model.connections()}
    stations = model.stations()
    cases, holds = [], []
    for directory, case_name, report_hash in runs:
        path = directory/'report.json'
        if digest(path) != report_hash:
            raise ValueError('Batch report hash changed')
        record, provenance = authenticate(directory)
        report = json.loads(path.read_text())
        if (record['candidate'] != model.KEY or record['panel_screw_count'] != 56
                or record['pounds'] != 250. or record['load_kind'] != 'full'
                or record['stiffness_n_per_mm'] != 1000.):
            raise ValueError('Unexpected frozen mechanics basis')
        for name, sha in provenance['source_sha256'].items():
            if (name.startswith(('mini_moonboard/', 'docs/'))
                    and not name.endswith(('_exports.py', '_drilling.py')) and digest(name) != sha):
                raise ValueError('Current producer/reference differs from frozen mechanics: '+name)
        holds.append(record['hold'])
        input_hashes[str(path)] = digest(path)
        input_hashes[str(directory/report['final_cycle_directory']/'input.json')] = provenance['input_sha256']
        actions = member_actions(record, report)
        brackets, bolts, sections = [], [], []
        forces = report['connector_forces']
        for name, origin, u, v, supporting, loaded in stations:
            groups = {}
            for member in (supporting, loaded):
                screws = [c for c in connections.values() if c.members == (name, member)]
                if len(screws) != 3 or any(c.length != 38.1 or c.diameter != 6.35 for c in screws):
                    raise ValueError('Require three exact SDS25112 screws on each flange')
                rows = [forces[c.name] for c in screws]
                for c, row in zip(screws, rows, strict=True):
                    expected = (c.start+c.direction*model.hardware.ML['thickness']).toTuple()
                    if np.linalg.norm(np.asarray(expected)-row['first_point_xyz_mm']) > 1.e-5:
                        raise ValueError('Bracket force endpoint differs from current assembly')
                f, m = wrench([r['first_point_xyz_mm'] for r in rows],
                              [r['force_on_first_xyz_n'] for r in rows], origin.toTuple())
                groups[member] = {'force_on_wood_xyz_n': f.tolist(), 'moment_on_wood_at_bend_xyz_nmm': m.tolist(),
                                 'resultant_n': float(np.linalg.norm(f)), 'moment_norm_nmm': float(np.linalg.norm(m)),
                                 'individual_screw_demands': []}
                for c, demand in zip(screws, rows, strict=True):
                    vector = np.asarray(demand['force_on_first_xyz_n'])
                    axial = float(np.dot(vector, c.direction.toTuple()))
                    groups[member]['individual_screw_demands'].append({
                        'connection': c.name, 'force_on_wood_xyz_n': vector.tolist(),
                        'withdrawal_tension_n': max(0., -axial), 'axial_compression_n': max(0., axial),
                        'lateral_n': float(np.linalg.norm(vector-axial*np.asarray(c.direction.toTuple()))),
                        'individual_sds_capacity_assigned': False})
            balance_f = np.asarray(groups[supporting]['force_on_wood_xyz_n'])+groups[loaded]['force_on_wood_xyz_n']
            balance_m = np.asarray(groups[supporting]['moment_on_wood_at_bend_xyz_nmm'])+groups[loaded]['moment_on_wood_at_bend_xyz_nmm']
            if np.linalg.norm(balance_f) > .1 or np.linalg.norm(balance_m) > 2.:
                raise ValueError('Recovered rigid angle violates force/moment equilibrium')
            row = {'angle': name, 'loaded_member': loaded, 'supporting_member': supporting,
                   'origin_xyz_mm': list(origin.toTuple()), 'flanges': groups,
                   'force_balance_norm_n': float(np.linalg.norm(balance_f)),
                   'moment_balance_norm_nmm': float(np.linalg.norm(balance_m)),
                   'qualified_for_design': False}
            # Only the two previously inspected bearing-installation mappings
            # are assigned manufacturer directions. Other station types retain
            # their physical flange wrenches without inventing table mappings.
            if name.startswith('clip_angle_base_'):
                demand = groups[loaded]
                row['bearing_installation_reference'] = angle_reference.assess(
                    (-np.asarray(demand['force_on_wood_xyz_n'])).tolist(),
                    (-np.asarray(demand['moment_on_wood_at_bend_xyz_nmm'])).tolist(), u.toTuple(), v.toTuple())
                row['reference_sign_convention'] = 'Applied load resisted by the angle = negative of bracket force/moment on loaded wood'
                reference = row['bearing_installation_reference']
                reference['unassessed_reasons'] = [reason for reason in reference['unassessed_reasons']
                    if reason != 'Simultaneous directional interaction not established by the inspected ML letter']
                reference['catalog_unity_equation'] = {'source': SIMPSON_CATALOG, 'page': 289,
                    'sum_of_listed_direction_ratios_only': sum(r['component_ratio'] for r in reference['component_references']),
                    'complete_wrench_check': False,
                    'limits': 'General catalog unity requires an applicable allowable in every participating direction; '
                              'it supplies neither missing bearing F2 nor an independent moment resistance. No 75% rule assigned.'}
                reference.update(irreducible_couple(reference['force_on_rim_xyz_n'], reference['moment_on_rim_xyz_nmm']))
            else:
                row['unassessed_reason'] = 'Loaded/supporting grain and flange direction must be matched to a tested installation; no generic resultant capacity.'
            brackets.append(row)
        for name, c in connections.items():
            if not name.startswith('lumber_leg_bolt_'):
                continue
            if c.diameter != 9.525 or c.grip != 76.2:
                raise ValueError('Conditional bolt reference requires 3/8in bolt and two 38.1mm members')
            force = np.asarray(forces[name]['force_on_first_xyz_n'])
            if c.members[0] not in actions or c.members[1] not in actions:
                raise ValueError('Unknown leg bolt members')
            expected = (c.start+c.direction*(2.032+38.1)).toTuple()
            if np.linalg.norm(np.asarray(expected)-forces[name]['first_point_xyz_mm']) > 1.e-5:
                raise ValueError('Bolt force endpoint differs from current assembly')
            reference = directional_bolt_reference(force.tolist(), model.leg.geometry('2x6', 0.)[2].toTuple())
            bolts.append({'connection': name, 'members': list(c.members),
                          'force_on_first_member_xyz_n': force.tolist(),
                          'axial_component_along_bolt_n': float(np.dot(force, c.direction.toTuple())),
                          'lateral_n': float(np.linalg.norm(force[1:])), **reference,
                          'qualified_for_design': False})
        members = {m['name']: m for m in record['members']}
        for bore in record['round_service_bores']:
            member = members[bore['member']]
            if abs(np.dot(member['axis'], bore['direction'])) > 1.e-8:
                raise ValueError('Only transverse passages supported')
            section = bore_section(member['gross_width_mm'], member['gross_depth_mm'],
                                   bore['diameter_mm'], bore['center_n_mm'])
            origin = model.b.point(bore['center_x_mm'], bore['center_s_mm'], section['centroid_n_mm'])
            cut = cut_demand(actions[bore['member']], origin.toTuple(), member['axis'],
                             member['section_u'], member['section_v'], section)
            sections.append({'bore': bore['name'], 'member': bore['member'], 'section': section,
                             'retained_prism_area_fraction': member['retained_area_fraction'], 'demand': cut})
        cases.append({'case': case_name, 'hold': record['hold'], 'brackets': brackets,
                      'leg_bolts': bolts, 'bore_sections': sections,
                      'seating_contact_enabled': record.get('seating_contact_enabled', False),
                      'seating_contact_count': len(record.get('seating_contacts', [])),
                      'panel_attachment_stiffness_n_per_mm': record.get('panel_attachment_stiffness_n_per_mm', record['stiffness_n_per_mm']),
                      'force_recovery_basis': ('Corrected expanded S8 opposite-surface displacement recovery; '
                          'full native force/MPC/stress replay authenticated by round_insert_frame.authenticated_input'
                          if native_runs is not None else report.get('force_recovery_basis',
                          'Reported kDeltaU spring reconstruction; panel-shell printed displacements may average expanded surface nodes. '
                          'No independent native spring-force output or rigorous recovered-force error bound supplied.')),
                      'native_directional_member_stress': [g for g in report['diagnostic_stress']['groups'] if g['element_type'] == 'C3D20']})
    if native_runs is None and sorted(holds) != ['C10', 'C6', 'F10']:
        raise ValueError('Require one distinct C10, C6 and F10 probe')
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError('Assessment source changed during analysis')
    return {'candidate': model.KEY, 'qualified_for_design': False,
            'member_strength_passed': False, 'structural_connection_strength_passed': False,
            'mechanics_scope': mechanics_scope,
            'new_solver_runs': 0, 'input_sha256': input_hashes, 'source_sha256': sources, 'cases': cases,
            'references': {'simpson_letter': angle_reference.LETTER, 'nds_chapter3': NDS_CH3,
                           'simpson_general_unity_equation_catalog_p289': SIMPSON_CATALOG},
            'primary_download_sha256': {
                angle_reference.LETTER: '88d9051a9eadc08508a1a1c591914217309d6a2c1a281b375149d0cc57e584ff',
                SIMPSON_CATALOG: '26e5ada670aecfdeda1b57e7388ce70d707466ac73e9cec591118964f438d2c2',
                NDS_CH3: '205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644'},
            'limits': 'Signed demands from the explicitly supplied authenticated, clamped-foot, isotropic 7000MPa native cases with '
                      '1000N/mm bilateral structural springs, recorded panel-attachment stiffness and compression-only Z bearings. '
                      'Where enabled, sampled panel contact is recovered at its physical point and normal. '
                      'Force recovery inherits the supplied report; global and whole-angle equilibrium do not establish '
                      'accuracy of every panel spring force or a numerical error bound. '
                      'No transfer between ordinary screws and inserts or between changed stiffness/contact models; no physical build qualification. '
                      'Net-section nominal stresses exclude local hole concentrations and other fastener holes. '
                      'Bolt lateral references assume DF-L SG0.50, .298in effective diameter and 45000psi steel yield; '
                      'axial washer bearing, group/splitting effects and adjustments remain unqualified.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('fea/generated/round-frame-batch-v1'))
    parser.add_argument('--native-run', type=Path, action='append',
                        help='Completed current insert native directory; repeat for multiple runs')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(build(args.directory, native_runs=args.native_run), stream, indent=2, allow_nan=False)
        stream.write('\n')
