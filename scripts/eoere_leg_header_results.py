"""Summarize fresh fields and conventional leg/post connection-shear checks."""

from __future__ import annotations

import argparse
import json
import math
import runpy
from collections import defaultdict
from pathlib import Path

from scripts.eoere_current_shop_followup import ROOT, encoded, require, sha
from scripts.eoere_leg_header_revision import REVISION, verify_attachment_axes

BASE = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/single-leg-header-integration-v1')
OLD = Path('fea/generated/selected-hardware-followup-v1/engineering-closure-v1')
SEQUENCE = ('a12-forward', 'a12-rear', 'a12-left', 'k12-right', 'k12-rear', 'a1-rear')


def run(out, detail_out=None):
    require(not out.exists(), 'fresh numerical summary required')
    pins = {}

    def read(path, expected=None):
        digest = sha(path)
        require(expected is None or digest == expected, 'source differs: '+str(path))
        pins[str(path)] = digest
        return json.loads(Path(path).read_bytes())

    def ref(path):
        return {'path': str(path), 'sha256': sha(path)}

    helper = OLD/'current-rail-end-connection-shear-v1.py'
    require(sha(helper) == 'f83fe3a96227f5f3d7ca88f98da43ea57ca2735cce3bb76400f5b25c4bc3cba3', 'frozen NDS helper differs')
    h = runpy.run_path(str(helper), run_name='frozen_connection_math')
    pure = h['functions']
    unit = pure(h['UNIT'], ['require', 'vector', 'dot', 'cross'], {'math': math})
    demand = pure(h['DEMAND'], ['add', 'scale', 'free_moment', 'member_cut_wrench'], {'math': math, 'unit': unit})
    own = pure(h['OWN_INPUTS'], ['member_point_inputs'], {'defaultdict': defaultdict, 'unit': unit, 'previous': demand})
    nds = pure(h['PROBE'], ['reduced_depth_shear'], {'math': math, 'parent': unit})
    prior = read(OLD/'current-mitered-prismatic-connection-shear-attempt02.json',
                 '7de3111e718a831b229ec42621548a50886b5af1f9ddbc0f43556ef0a6a90418')
    geometry_path = BASE/'attempt06/geometry.json'
    geometry = read(geometry_path)
    require(geometry['revision'] == REVISION, 'corrected geometry required')
    verify_attachment_axes(geometry['axes'])
    cases, detailed = [], []
    gg, fg, fv = h['GEOMETRY_GUARD'], h['FORCE_GUARD'], h['FV']
    for case in SEQUENCE:
        folder = BASE/'cases-corrected-v3'/case/'attempt01'
        field, replay, laminate = [read(folder/name) for name in ('field.json', 'replay.json', 'replay-plywood.json')]
        require(replay['field'] == ref(folder/'field.json') and laminate['field'] == replay['field']
                and replay['false_screw_force_rejected'] and replay['equilibrium']['physical_body_count'] == 148
                and replay['equilibrium']['gradient_inf_n'] <= 1e-5
                and replay['equilibrium']['maximum_body_force_norm_n'] <= 1e-4
                and replay['equilibrium']['maximum_body_moment_about_reference_norm_nmm'] <= .1,
                'matched complete raw operator/force replay required')
        require(field['trial_parent_geometry'] == ref(geometry_path) and field['response']['converged']
                and field['response']['gradient_inf_n'] <= 1e-5 and not any(field['release'].values()),
                'own corrected conditional field required')
        verify_attachment_axes([r['source_axis'] for r in field['source_inputs']['shafts']])
        actions, gravity = own.member_point_inputs(field)
        members = {m['name']: m for m in field['source_inputs']['timber_rows']}
        shafts = {s['axis_id']: s for s in field['source_inputs']['shafts']}
        rows = []
        for side in ('left', 'right'):
            for kind, prefix, name in (
                ('leg_foot', 'rail_rear_bolt_', 'lumber_leg_'+side),
                ('leg_upper', 'lumber_leg_bolt_', 'lumber_leg_'+side),
                ('post_front', 'rail_front_bolt_', 'base_post_outer_'+side),
                ('post_cleat', 'cleat_post_bolt_', 'base_post_outer_'+side)):
                member = members[name]
                profile = member['raw_profile_source']
                g, _u, v = (member[k] for k in ('axis', 'section_u', 'section_v'))
                origin_s = unit.dot(g, profile['datum_xyz_mm'])
                low, high = (unit.dot(g, member[k]) for k in ('start', 'end'))
                ids = [identity for identity in shafts if identity.startswith(prefix+side+'_')]
                expected = 1 if kind.startswith('leg_') else 2
                require(len(ids) == expected, 'one leg pin/two post bolts required')
                ports = [r for r in field['common_shaft_wood_bearing_actions'] if r['host'] == name and r['axis_id'] in ids]
                require(len(ports) == len(ids), 'one complete own bearing wrench per receiver required')
                require(all(abs(unit.dot(g, shafts[i]['basis'][0])) < 1e-8 and abs(unit.dot(v, shafts[i]['basis'][0])) < 1e-8 for i in ids),
                        'bolt must cross stock width for this NDS comparison')
                centers = [unit.dot(g, shafts[i]['point']) for i in ids]
                radius = max(shafts[i]['bore_diameter_mm']/2 for i in ids)
                band = [min(centers)-radius-gg, max(centers)+radius+gg]
                coords = [unit.dot(v, [a-b for a, b in zip(shafts[i]['point'], profile['datum_xyz_mm'], strict=True)]) for i in ids]
                if kind.startswith('leg_'):
                    old = prior['geometry'][name+('/0' if kind == 'leg_foot' else '/1')]
                    require(old['kind'] == 'new prismatic-band component' and not old['channel_overlap']
                            and old['band_world_grain_mm'][0]-1e-6 <= band[0] < band[1] <= old['band_world_grain_mm'][1]+1e-6,
                            'new band must be contained in the preserved proven prismatic band')
                    section_u, section_v = old['section_uv_mm']
                    core = old['whole_depth_rectangular_core_local_grain_mm']
                    end = min(min(centers)-origin_s-core[0], core[1]+origin_s-max(centers))
                    width, depth = section_u[1]-section_u[0], section_v[1]-section_v[0]
                    de = [section_v[1]-min(coords), max(coords)-section_v[0]]
                    geometry_basis = 'unchanged full-width prismatic band; removed second bore; retained1:12 recess and sole'
                else:
                    # Retained4x6 post has a9.525mm longitudinal bevel. This
                    # full-depth rectangle is the same documented79.375mm core.
                    width, depth = 79.375, 139.7
                    de = [depth-min(coords), max(coords)]
                    end = min(min(centers)-low, high-max(centers))
                    require(0 < band[0] < band[1] < 238.9, 'post band must stay within retained prismatic height')
                    geometry_basis = 'retained4x6 post79.375mm full-depth core; all cut actions assigned to that core'
                references = [nds.reduced_depth_shear(fv, width-gg, depth+gg, x-gg, end)['reference_n'] for x in de]
                require(end > 0 and all(x > 0 for x in references), 'positive applicable component reference required')
                events = [unit.dot(g, point) for point, _, _ in actions[name] if band[0] <= unit.dot(g, point) <= band[1]]
                cuts = sorted({*band, *(math.nextafter(x, direction) for x in events for direction in (-math.inf, math.inf))})
                samples = []
                center, weight = gravity[name]
                for station in cuts:
                    point = [p+(station-low)*q for p, q in zip(member['start'], g, strict=True)]
                    wrench = demand.member_cut_wrench(g, low, high, point, center, weight, actions[name])
                    samples.append({'station_world_grain_mm': station, 'cut_xyz_mm': point,
                                    'force_xyz_n': wrench['force_on_lower_portion_xyz_n'],
                                    'moment_xyz_nmm': wrench['moment_on_lower_portion_about_cut_xyz_nmm'],
                                    'strong_transverse_shear_n': unit.dot(v, wrench['force_on_lower_portion_xyz_n'])})
                worst = max(samples, key=lambda r: abs(r['strong_transverse_shear_n']))
                value = abs(worst['strong_transverse_shear_n'])+fg
                row = {'member': name, 'duty': kind, 'axis_ids': ids, 'geometry_basis': geometry_basis,
                       'section_width_depth_mm': [width, depth], 'de_positive_negative_mm': de,
                       'reference_positive_negative_CD1_N': references, 'demand_N': value,
                       'conservative_reference_index_CD1': value/min(references),
                       'own_bolt_strong_transverse_forces_N': [unit.dot(v, r['force_on_host_xyz_n']) for r in ports],
                       'worst_cut': worst, 'complete_joint_or_member_qualified': False}
                rows.append(row)
                detailed.append({'case_id': case, **row, 'band_mm': band, 'all_event_sided_cuts': samples})
        cases.append({'case_id': case, 'field': ref(folder/'field.json'), 'raw_operator_replay': ref(folder/'replay.json'),
                      'plywood_operator_replay': ref(folder/'replay-plywood.json'), 'counts': field['counts'],
                      'gradient_inf_N': field['response']['gradient_inf_n'],
                      'equilibrium': field['equilibrium_verification'], 'connection_shear_references': rows})
    require(len(detailed) == 48, 'six cases/eight leg-post component comparisons required')
    pins.update({str(p): sha(p) for p in (helper, Path(__file__).relative_to(ROOT))})
    for key in ('UNIT', 'DEMAND', 'OWN_INPUTS', 'PROBE', 'NDS', 'SUPPLEMENT'):
        pins[str(h[key])] = sha(h[key])
    result = {'schema': 'eoere_leg_header_conditional_results/v1', 'revision': REVISION,
              'status': 'SIX_CONDITIONAL_CASES_REPLAYED_STRENGTH_HOLDS_REMAIN', 'geometry': ref(geometry_path),
              'cases': cases, 'maximum_full_gradient_residual_N': max(r['gradient_inf_N'] for r in cases),
              'all_six_raw_operator_and_force_replays_pass': True, 'all96_attachment_axes_checked': True,
              'production_admission_issued': False, 'physical_demand_bound_established': False,
              'NDS_component_basis': 'NDS2024 3.4.4.1/Eqs3.4-6/7; dry DF-LNo2 Fv180psi, CD1; geometry guard.001mm, force guard1e-5N. Event-sided cuts of the current point-action/affine-weight model.',
              'component_comparisons': 48, 'component_reference_exceedances': [r for r in detailed if r['conservative_reference_index_CD1'] > 1],
              'worst_leg_foot': max((r for r in detailed if r['duty'] == 'leg_foot'), key=lambda r: r['conservative_reference_index_CD1']),
              'worst_leg_upper': max((r for r in detailed if r['duty'] == 'leg_upper'), key=lambda r: r['conservative_reference_index_CD1']),
              'worst_front_post': max((r for r in detailed if r['duty'].startswith('post_')), key=lambda r: r['conservative_reference_index_CD1']),
              'source_sha256': pins, 'structural_acceptance': False, 'fabrication_released': False, 'climbing_released': False,
              'actual_observations': None, 'remaining': ['Complete cleat, fitting/common-shaft/axial-seat and timber-interior transfer',
                  'Bolted wood bearing/group/net/end/splitting and finished-member/shear/torsion/stability coverage',
                  'Enclosed-hole and panel/Hillman attachment duties', 'Physical shear/torsion/capture/contact/restraint and no-slip floor assumptions']}
    raw = detail_out or BASE/'current-leg-post-shear-details-v1.json'
    require(not raw.exists(), 'fresh detailed evidence required')
    raw.write_bytes(encoded({'geometry': result['geometry'], 'rows': detailed, 'source_sha256': pins}))
    result['detailed_component_evidence'] = ref(raw)
    # Keep the published packet compact: event cuts remain in the raw companion.
    for row in result['component_reference_exceedances']:
        row.pop('all_event_sided_cuts', None)
    for key in ('worst_leg_foot', 'worst_leg_upper', 'worst_front_post'):
        result[key].pop('all_event_sided_cuts', None)
    out.write_bytes(encoded(result))
    print(json.dumps({'summary': ref(out), 'exceedances': len(result['component_reference_exceedances']),
          'worst_leg_foot': result['worst_leg_foot']['conservative_reference_index_CD1'],
          'worst_leg_upper': result['worst_leg_upper']['conservative_reference_index_CD1'],
          'worst_front_post': result['worst_front_post']['conservative_reference_index_CD1']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    parser.add_argument('--detail-out', type=Path)
    args = parser.parse_args()
    run(args.out, args.detail_out)
